##################################################
# The Toontown Realms Magic Word Manager
##################################################
# Co-Authors: John Cote, William Lord, Frank, Nick, Little Cat, Ooowoo, Drew, Leo
# Copyright: Copyright 2022, Toontown Realms
# License: MIT
# Version: 1.0.0
##################################################

from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObject

from panda3d.toontown import WhisperPopup

from toontown.social import AvatarHandle
from toontown.spellbook.MagicWordConfig import *
from toontown.spellbook.MagicWordIndex import *
from toontown.toonbase import ClientSettings
from toontown.toon import Toon

from operator import itemgetter

MagicWordIndex = magicWordIndex.copy()


class ToontownRealmsMagicWordManager(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownRealmsMagicWordManager')
    neverDisable = 1

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        base.cr.magicWordManager = self

        # The default chat prefix we use to determine if said phrase is a Magic Word
        self.chatPrefix = PREFIX_DEFAULT

        # The default name of the "wizard" that returns responses when executing Magic Words
        self.wizardName = WIZARD_DEFAULT

        # Keep track of the last clicked avatar for targeting purposes
        self.lastClickedAvId = 0

        # The 10 most recently used Magic Words used by our player
        self.recentWords = []

        # The top 10 favorite Magic Words used by our player- favorite status is determined by how often the Word is used
        self.favoriteWords = {}

        # Magic Words saved by the player
        self.savedWords = []

        # The most recently used Magic Word (can't rely on recentWords for this, since the player can clear that at any time)
        self.recentWord = None

        # The rank at which Magic Word cooldowns are ignored (this is mostly just to show in the book; the actual value checked against is stored on the server)
        self.bypassLevel = COOLDOWN_BYPASS_DEFAULT

    def announceGenerate(self):
        DistributedObject.DistributedObject.announceGenerate(self)

        # Only use a custom Magic Word activator if the index is allowed
        activatorIndex = ClientSettings.MagicWordActivator.get()
        if 0 <= activatorIndex <= (len(PREFIX_ALLOWED) - 1):
            self.chatPrefix = PREFIX_ALLOWED[activatorIndex]

        # Accept events such as outgoing chat messages and clicking on nametags
        self.accept(OUTGOING_CHAT_MESSAGE_NAME, self.checkMagicWord)
        self.accept(CLICKED_NAMETAG_MESSAGE_NAME, self.__handleClickedNametag)
        self.accept(FOCUS_OUT_MESSAGE_NAME, self.__handleFocusOutNametag)

        # Refresh our Magic Words speedchat menu
        messenger.send('magicWordsChanged')

        # Accept any incoming speedchat messages
        self.accept('TTSCMagicWord', self.checkMagicWord)
        self.accept('TTSCMagicWordAdd', self.addMagicWord)
        self.accept('TTSCMagicWordRemove', self.removeMagicWords)
        self.accept('TTSCMagicWordClearRecent', self.clearRecentWords)
        self.accept('TTSCMagicWordClearFavorites', self.clearFavoriteWords)

    def sendWordData(self, changes):
        for wordData in changes:
            name, accessLevel, cooldown, anyTarget = wordData

            if name == '':
                continue

            if accessLevel not in list(AccessLevelName2Int.keys()):
                break

            if cooldown:
                cooldown = max(0, min(cooldown, 300))

            try:
                wordInfo = MagicWordIndex[str(name.lower())]
                for alias in wordInfo['aliases']:
                    MagicWordIndex[alias]['access'] = accessLevel
                    MagicWordIndex[alias]['cooldown'] = cooldown
                    MagicWordIndex[alias]['anyTarget'] = anyTarget
            except:
                pass

    def sendCooldownBypass(self, cooldownBypass):
        if cooldownBypass:
            self.bypassLevel = cooldownBypass

    def disable(self):
        DistributedObject.DistributedObject.disable(self)

        # Ignore the events we were accepting earlier
        self.ignoreAll()

    @staticmethod
    def getMagicWordPrefix():
        magicWordPrefix = '~'
        magicWordActivatorIndex = ClientSettings.MagicWordActivator.get()
        MW_PREFIX_ALLOWED = ['~', '?', '/', '<', ':', ';']
        if config.GetBool('exec-chat', False):
            MW_PREFIX_ALLOWED.append('>')
        if 0 <= magicWordActivatorIndex <= (len(MW_PREFIX_ALLOWED) - 1):
            magicWordPrefix = MW_PREFIX_ALLOWED[magicWordActivatorIndex]
        return magicWordPrefix

    def setChatPrefix(self, chatPrefix):
        self.chatPrefix = chatPrefix

    def __handleClickedNametag(self, avatar):
        if avatar:
            # Make sure the nametag we clicked on is a Toon
            if isinstance(avatar, Toon.Toon) or isinstance(avatar, AvatarHandle.AvatarHandle):
                # Store the avId of our target
                self.lastClickedAvId = avatar.getDoId()
                return
        # Clear our target avId
        self.lastClickedAvId = 0

    def __handleFocusOutNametag(self):
        # We've clicked off of a nametag, so reset the target avId
        self.lastClickedAvId = 0

    def checkMagicWord(self, magicWord):
        # Well, this obviously isn't a Magic Word if it doesn't begin with our prefix
        if not magicWord.startswith(self.chatPrefix):
            return

        # We don't even have access to be using Magic Words in the first place
        if base.localAvatar.getAccessLevel() < AccessLevelName2Int.get('USER'):
            self.generateResponse(responseType="NoAccess")
            return

        # Using Magic Words while teleporting or going through tunnels is scary
        if base.localAvatar.getTransitioning():
            self.generateResponse(responseType="Teleporting")
            return

        # We're naughty, so no Magic Words for us
        if base.localAvatar.getLocked():
            self.generateResponse(responseType="Locked")
            return

        # We're allowed to use the Magic Word then, so let's proceed
        self.handleMagicWord(magicWord)

    def generateResponse(self, responseType, magicWord='', args=None, returnValue=None, affectRange=None,
                         affectType=None, affectExtra=None, lastClickedAvId=None, extraMessageData=None):
        # Generate and send the response to the use of our Magic Word
        response = self.generateMagicWordResponse(responseType, magicWord, args, returnValue, affectRange, affectType,
                                                  affectExtra, lastClickedAvId, extraMessageData)
        base.localAvatar.setSystemMessage(0, self.wizardName + ': ' + response, WhisperPopup.WTMagicWord)
        self.notify.info(response)

    def generateMagicWordResponse(self, responseType, magicWord, args, returnValue, affectRange, affectType,
                                  affectExtra, lastClickedAvId, extraMessageData):
        # Start out with a blank response
        response = ''

        # We had a successful Magic Word and also got a return value, so let's just use that
        if responseType == "Success":
            response += returnValue
            return response

        # Guess it wasn't a success, so let's grab our response via the given code
        response += MAGIC_WORD_RESPONSES.get(responseType, MAGIC_WORD_NO_RESPONSE)

        # If we want to provide extra info, format the response
        if responseType in MagicWordConfig.HAS_EXTRA_MESSAGE_DATA:
            response = response.format(extraMessageData)

        return response

    def handleMagicWord(self, magicWord):
        # Register our Magic Word for things like the Chat Log & Speedchat Menu
        self.registerMagicWord(magicWord)

        # By default, our Magic Word affects nobody- not even ourself!
        affectRange = AFFECT_NONE

        # A normal affect type-  we aren't trying to target all Toons in the zone, server, or a specific Access Level
        affectType = AFFECT_NORMAL

        # Only used for determining what Access Level will be targeted, if we decide to target a specific one
        affectExtra = -1

        # Used for determining what the affectRange is- it counts the amount of activators uses (ranges 1-3)
        for x in range(3):
            if magicWord.startswith(self.chatPrefix * (3 - x)):
                affectRange = 2 - x
                break

        # If so some reason our affectRange is still none, we can't go any further
        if affectRange == AFFECT_NONE:
            self.generateResponse(responseType="NoEffect")
            return

        # Get how many activators were used in this Magic Word execution
        activatorLength = affectRange + 1

        # The Magic word without the activators
        magicWordNoPrefix = magicWord[activatorLength:]

        # Make sure to encode the string
        magicWordNoPrefix = magicWordNoPrefix

        # Iterate through the affectType strings and see if any of them were used (e.g. zone, server, or rank)
        for affect in AFFECT_TYPES:
            if magicWordNoPrefix.startswith(affect) and magicWordNoPrefix != affect:
                magicWordNoPrefix = magicWordNoPrefix[len(affect):]
                affectType = AFFECT_TYPES.index(affect)
                break

        # Calculate the Access Level to affect if affectType is RANK
        if affectType == AFFECT_RANK:
            # Iterate over all the possible Access Level integers and see if any match with the one provided
            for level in list(OTPGlobals.AccessLevelName2Int.values()):
                # It matches, woohoo!
                if magicWordNoPrefix.startswith(str(level)):
                    # Sorry, I'm commenting this way after the fact, so not even I know why there is a try/except here
                    # My guess is that sometimes this doesn't work for whatever reason, but I'm not too sure
                    # It typically works fine for me but I will keep it here just in-case
                    try:
                        int(magicWordNoPrefix[len(str(level)):][:1])
                        self.generateResponse(responseType="BadTarget")
                        return
                    except:
                        pass

                    # Strip the Access Level integer from the Magic Word string
                    magicWordNoPrefix = magicWordNoPrefix[len(str(level)):]

                    # Store the Access Level integer here instead
                    affectExtra = level
                    break

            # The invoker wanted to target an Access Level but provided an invalid integer, so let them know
            if affectExtra == -1:
                self.generateResponse(responseType="BadTarget")
                return

        # Finally, we can get the name of the Magic Word used
        word = magicWordNoPrefix.split(' ', 1)[0].lower()

        # The Magic Word the invoker used doesn't exist
        if word not in MagicWordIndex:
            # Iterate over all Magic Word names and see if the one provided is close to any of them
            for magicWord in list(MagicWordIndex.keys()):
                # If it is close, suggest to the invoker that they made a typo
                if word in magicWord:
                    self.generateResponse(responseType="CloseWord", extraMessageData=magicWord)
                    return
            # Couldn't find any Magic Word close to what was provided, so let them know the word doesn't exist
            self.generateResponse(responseType="BadWord")
            return

        # Grab the Magic Word info based off of it's name
        magicWordInfo = MagicWordIndex[word]
        execLocation = magicWordInfo['execLocation']

        # Our affectRange is other or both, and affectType is normal, meaning we want to target someone- let's make sure we're allowed to
        if (affectRange in (AFFECT_OTHER, AFFECT_BOTH)) and (affectType == AFFECT_NORMAL) and (execLocation == EXEC_LOC_CLIENT):
            # If they don't exist, why would we want to continue?
            toon = base.cr.doId2do.get(self.lastClickedAvId)
            if not toon:
                self.generateResponse(responseType="DifferentZone")
                return

            # Like earlier, Magic Words are no good if used while moving between zones
            if toon.getTransitioning():
                self.generateResponse(responseType="OtherTeleporting")
                return

        # The location of the Magic Word's execution was not specified, so raise an error
        if execLocation == EXEC_LOC_INVALID:
            raise ValueError("execLocation not set for magic word {}!".format(magicWordInfo['classname']))
        # The execLocation is valid, so let's finally send data over to the server to execute our Magic Word
        elif execLocation in (EXEC_LOC_SERVER, EXEC_LOC_CLIENT):
            self.sendUpdate('requestExecuteMagicWord', [affectRange, affectType, affectExtra, self.lastClickedAvId,
                                                        magicWordNoPrefix])

    def executeMagicWord(self, word, commandName, targetIds, args, affectRange, affectType, affectExtra, lastClickedAvId):
        # We have have a target avId and the affectRange isn't ourself, we want to execute this Magic Word on the target
        # This is alright, but we should only execute it on the target if they are visible on our client
        if self.lastClickedAvId and affectRange != AFFECT_SELF:
            toon = base.cr.doId2do.get(self.lastClickedAvId)
            if not toon:
                self.generateResponse(responseType="NoTarget")
                return

        # Get the Magic Word info based off of it's name
        magicWord = commandName.lower()
        magicWordInfo = MagicWordIndex[magicWord]

        # Load the class tied to the Magic Word
        command = magicWordInfo['class']
        command.loadWord(None, self.cr, base.localAvatar.getDoId(), targetIds, args)

        # Execute the Magic Word and store the return value
        returnValue = command.executeWord()

        # If we have a return value, route it through
        if returnValue:
            self.generateResponse(responseType="Success", returnValue=returnValue)

    def registerMagicWord(self, magicWord):
        # Add our Magic Word usage to the Chat Log
        color = Vec4(0.8, 0.3, 0.6, 0.6)
        messenger.send('addToLog', ['Magic Word', 0, None, None, color, magicWord, WhisperPopup.WTMagicWord])

        self.recentWord = magicWord

        # Add this Magic Word to our "recents" category in Speedchat
        if magicWord not in self.recentWords:
            if len(self.recentWords) >= 10:
                del self.recentWords[-1]

            self.recentWords.insert(0, magicWord)

        # Register it to the favorites dict to keep track of how many times it has been used
        if magicWord not in list(self.favoriteWords.keys()):
            self.favoriteWords[magicWord] = 1
        else:
            count = self.favoriteWords.get(magicWord) + 1
            self.favoriteWords[magicWord] = count

        # Refresh our Magic Words speedchat menu
        messenger.send('magicWordsChanged')

    def getRecentWords(self):
        return self.recentWords

    def getFavoriteWords(self):
        # Grab the Magic Words with the top 10 uses- that have been used at least 5 times so far
        favorites = dict(sorted(self.favoriteWords.items(), key=itemgetter(1), reverse=True))
        words = []
        for word, uses in favorites.items():
            if uses >= 5 and len(words) < 10:
                words.append(word)

        return words

    def getSavedWords(self):
        words = ClientSettings.FavoriteMagicWords.get()
        return words

    def addMagicWord(self):
        if not self.recentWord:
            return

        words = self.getSavedWords()
        if len(words) >= 10:
            del words[-1]

        words.insert(0, self.recentWord)
        ClientSettings.FavoriteMagicWords.set(words)

        # Refresh our Magic Words speedchat menu
        messenger.send('magicWordsChanged')

    def removeMagicWords(self):
        ClientSettings.FavoriteMagicWords.set([])

        # Refresh our Magic Words speedchat menu
        messenger.send('magicWordsChanged')

    def clearRecentWords(self):
        self.recentWords = []

        # Refresh our Magic Words speedchat menu
        messenger.send('magicWordsChanged')

    def clearFavoriteWords(self):
        self.favoriteWords = {}

        # Refresh our Magic Words speedchat menu
        messenger.send('magicWordsChanged')
