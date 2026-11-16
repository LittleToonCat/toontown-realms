import random
import sys
from direct.directnotify import DirectNotifyGlobal
from direct.distributed import ClockDelta
from panda3d.core import *
from subprocess import Popen

from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import SoundInterval, Wait, Sequence, Func
from panda3d.toontown import CFSpeech, CFThought, CFTimeout, CFPageButton, CFNoQuitButton, CFQuitButton, CFExclaim
from panda3d.toontown import Nametag, NametagGroup

from otp.avatar.ShadowCaster import ShadowCaster
from otp.otpbase import OTPGlobals
from otp.otpbase import OTPLocalizer
from otp.otpbase import OTPRender
from toontown.toonbase import ToontownGlobals, ClientSettings

teleportNotify = DirectNotifyGlobal.directNotify.newCategory('Teleport')
teleportNotify.showTime = True
if config.GetBool('want-teleport-debug', 0):
    teleportNotify.setDebug(1)


def reconsiderAllUnderstandable():
    for av in Avatar.ActiveAvatars:
        av.considerUnderstandable()


class Avatar(Actor, ShadowCaster):
    notify = directNotify.newCategory('Avatar')
    ActiveAvatars = []
    ManagesNametagAmbientLightChanged = False

    def __init__(self, other = None):
        self._name = ''
        try:
            self.Avatar_initialized
            return
        except:
            self.Avatar_initialized = 1

        Actor.__init__(self, None, None, other, flattenable=0,
                       setFinal=not ClientSettings.AvatarFrustumCulling.get())
        ShadowCaster.__init__(self)
        self.__font = OTPGlobals.getInterfaceFont()
        self.soundChatBubble = None
        self.avatarType = ''
        self.nametagNodePath = None
        self.__nameVisible = 1
        self.nametag = NametagGroup()
        self.nametag.setAvatar(self)
        self.nametag.setFont(OTPGlobals.getInterfaceFont())
        self.nametag2dContents = Nametag.CName | Nametag.CSpeech | Nametag.CExclaim
        self.nametag2dDist = Nametag.CName | Nametag.CSpeech | Nametag.CExclaim
        self.nametag2dNormalContents = Nametag.CName | Nametag.CSpeech | Nametag.CExclaim
        self.nametag3d = self.attachNewNode('nametag3d')
        self.nametag3d.setTag('cam', 'nametag')
        self.nametag3d.setLightOff()
        if self.ManagesNametagAmbientLightChanged:
            self.acceptNametagAmbientLightChange()
        OTPRender.renderReflection(False, self.nametag3d, 'otp_avatar_nametag', None)
        self.getGeomNode().showThrough(OTPRender.ShadowCameraBitmask)
        self.nametag3d.hide(OTPRender.ShadowCameraBitmask)
        self.collTube = None
        self.battleTube = None
        self.scale = 1.0
        self.nametagScale = 1.0
        self.height = 0.0
        self.battleTubeHeight = 0.0
        self.battleTubeRadius = 0.0
        self.style = None
        self.commonChatFlags = 0
        self.understandable = 1
        self.setPlayerType(NametagGroup.CCNormal)
        self.ghostMode = 0
        self.__chatParagraph = None
        self.__chatMessage = None
        self.__chatFlags = 0
        self.__chatPageNumber = None
        self.__chatAddressee = None
        self.__chatDialogueList = []
        self.__chatSet = 0
        self.__chatLocal = 0
        self.__currentDialogue = None
        self.whitelistChatFlags = 0
        self.soundSequenceList = []
        self.curTTS = None
        return

    def delete(self):
        try:
            self.Avatar_deleted
        except:
            self.deleteNametag3d()
            Actor.cleanup(self)
            if self.ManagesNametagAmbientLightChanged:
                self.ignoreNametagAmbientLightChange()
            self.Avatar_deleted = 1
            for soundSequence in self.soundSequenceList:
                soundSequence.finish()

            self.soundSequenceList = []

            # Cleanup TTS so we're not waiting for
            # a long message to finish upon
            # program exit
            if self.curTTS and not self.curTTS.poll():
                self.curTTS.terminate()

            del self.__font
            del self.style
            del self.soundChatBubble
            del self.nametag
            self.nametag3d.removeNode()
            ShadowCaster.delete(self)
            Actor.delete(self)

    def acceptNametagAmbientLightChange(self):
        self.accept('nametagAmbientLightChanged', self.nametagAmbientLightChanged)

    def ignoreNametagAmbientLightChange(self):
        self.ignore('nametagAmbientLightChanged')

    def isLocal(self):
        return 0

    def isPet(self):
        return False

    def isProxy(self):
        return False

    def setPlayerType(self, playerType, understandable=False):
        self.playerType = playerType
        if not hasattr(self, 'nametag'):
            self.notify.warning('no nametag attributed, but would have been used.')
            return
        if self.isUnderstandable() or understandable:
            self.nametag.setColorCode(self.playerType)
        else:
            self.nametag.setColorCode(NametagGroup.CCNoChat)

    def setCommonChatFlags(self, commonChatFlags):
        self.commonChatFlags = commonChatFlags
        self.considerUnderstandable()
        if self == base.localAvatar:
            reconsiderAllUnderstandable()

    def setWhitelistChatFlags(self, whitelistChatFlags):
        self.whitelistChatFlags = whitelistChatFlags
        self.considerUnderstandable()
        if self == base.localAvatar:
            reconsiderAllUnderstandable()

    def considerUnderstandable(self):
        speed = 0
        if self.playerType in (NametagGroup.CCNormal, NametagGroup.CCFreeChat, NametagGroup.CCSpeedChat):
            self.setPlayerType(NametagGroup.CCSpeedChat)
            speed = 1
        if hasattr(base, 'localAvatar') and self == base.localAvatar:
            self.understandable = 1
            self.setPlayerType(NametagGroup.CCFreeChat)
        elif self.playerType == NametagGroup.CCSuit:
            self.understandable = 1
            self.setPlayerType(NametagGroup.CCSuit)
        elif self.playerType not in (NametagGroup.CCNormal, NametagGroup.CCFreeChat, NametagGroup.CCSpeedChat):
            self.understandable = 1
            self.setPlayerType(NametagGroup.CCNoChat)
        elif hasattr(base, 'localAvatar') and self.commonChatFlags & base.localAvatar.commonChatFlags & OTPGlobals.CommonChat:
            self.understandable = 1
            self.setPlayerType(NametagGroup.CCFreeChat)
        elif self.commonChatFlags & OTPGlobals.SuperChat:
            self.understandable = 1
            self.setPlayerType(NametagGroup.CCFreeChat)
        elif hasattr(base, 'localAvatar') and base.localAvatar.commonChatFlags & OTPGlobals.SuperChat:
            self.understandable = 1
            self.setPlayerType(NametagGroup.CCFreeChat)
        elif base.cr.getFriendFlags(getattr(self, 'doId', 0)) & OTPGlobals.FriendChat:
            self.understandable = 1
            self.setPlayerType(NametagGroup.CCFreeChat)
            retroMode = ClientSettings.ClassicNametags.get()
            if retroMode:
                self.setPlayerType(NametagGroup.CCNormal)
        elif base.cr.playerFriendsManager.findPlayerIdFromAvId(getattr(self, 'doId', 0)) is not None:
            playerInfo = base.cr.playerFriendsManager.findPlayerInfoFromAvId(self.doId)
            if playerInfo.openChatFriendshipYesNo:
                self.understandable = 1
                self.nametag.setColorCode(NametagGroup.CCFreeChat)
            elif playerInfo.isUnderstandable():
                self.understandable = 1
            else:
                self.understandable = 0
        elif hasattr(base, 'localAvatar') and self.whitelistChatFlags & base.localAvatar.whitelistChatFlags:
            self.understandable = 1
        else:
            self.understandable = 0
        if not hasattr(self, 'nametag'):
            self.notify.warning('no nametag attributed, but would have been used')
        else:
            self.nametag.setColorCode(self.playerType)
        return

    def isUnderstandable(self):
        return self.understandable

    def setDNAString(self, dnaString):
        pass

    def setDNA(self, dna):
        pass

    def getAvatarScale(self):
        return self.scale

    def setAvatarScale(self, scale):
        if self.scale != scale:
            self.scale = scale
            self.getGeomNode().setScale(scale)
            self.setHeight(self.height)

    def getNametagScale(self):
        return self.nametagScale

    def setNametagScale(self, scale):
        self.nametagScale = scale
        self.nametag3d.setScale(scale)

    def adjustNametag3d(self):
        if self.nametag3d and not self.nametag3d.isEmpty():
            self.nametag3d.setPos(0, 0, self.height + 0.5)

    def getHeight(self):
        return self.height

    def setHeight(self, height):
        self.height = height
        self.adjustNametag3d()
        if self.collTube:
            self.collTube.setPointB(0, 0, height - self.getRadius())
            if self.collNodePath:
                self.collNodePath.forceRecomputeBounds()
        if self.battleTube:
            self.battleTube.setPointB(0, 0, height - self.getRadius())

    def getRadius(self):
        return OTPGlobals.AvatarDefaultRadius

    def getName(self):
        for emoji in base.emojis:
            self._name = self._name.replace(f':{emoji}:', f'\x01white\x01\5{emoji}\5\x02')
        return self._name

    def getType(self):
        return self.avatarType

    def setName(self, name):
        if hasattr(self, 'transformations'):
            if self.getTransformationsIndex(ToontownGlobals.TransformationCog):
                return
        self._name = name
        if hasattr(self, 'nametag'):
            nametagName = name
            # TODO: emojis don't work on the nametag chat bubble so f
            #for emoji in base.emojis:
                #nametagName = name.replace(f':{emoji}:', f'\x01white\x01\5{emoji}\5\x02')
            if base.cr.getChatFilterMode() >= ToontownGlobals.CHAT_FILTER_CENSOR:
                nametagName = base.profanityFilter.censor(nametagName)
            self.nametag.setName(nametagName)

    def setDisplayName(self, str):
        if hasattr(self, 'transformations'):
            if self.getTransformationsIndex(ToontownGlobals.TransformationCog):
                return
        self.nametag.setDisplayName(str)

    def getFont(self):
        return self.__font

    def setFont(self, font, chat_font_flag=True):
        self.__font = font
        self.nametag.setFont(font, chat_font_flag)

    def getStyle(self):
        return self.style

    def setStyle(self, style):
        self.style = style

    def getDialogueArray(self):
        return None

    def playCurrentDialogue(self, dialogue, chatFlags, interrupt = 1):
        exclaimFlag = False
        if chatFlags & CFExclaim == 512:
            exclaimFlag = True
        if interrupt and self.__currentDialogue is not None:
            self.__currentDialogue.stop()
        self.__currentDialogue = dialogue
        chatString = ''
        if dialogue:
            base.playSfx(dialogue, node=self)
        elif chatFlags & CFSpeech != 0 or exclaimFlag:
            if self.nametag.getNumChatPages() > 0:
                chatString = self.nametag.getChat()
                self.playDialogueForString(chatString, exclaim=exclaimFlag)
                if self.soundChatBubble != None:
                    base.playSfx(self.soundChatBubble, node=self)
            elif self.nametag.getChatStomp() > 0:
                chatString = self.nametag.getStompText()
                self.playDialogueForString(chatString, self.nametag.getStompDelay(), exclaim=exclaimFlag)

            # Add to chat history.
            if chatString and chatString.strip() and chatString != '.':
                if self.isLocal():
                    color = 8
                else:
                    color = self.nametag.getColorCode()
                messenger.send('addToLog', [self.getName().split('\n')[0], getattr(self, 'doId', 0), self.nametag.getNameFont(), self.nametag.getChatFont(), color, chatString.strip()])

    def playDialogueForString(self, chatString, delay=0.0, exclaim=False):
        searchString = chatString.lower()
        if searchString.find(OTPLocalizer.DialogSpecial) >= 0:
            type = 'special'
        elif searchString.find(OTPLocalizer.DialogExclamation) >= 0 or exclaim:
            type = 'exclamation'
        elif searchString.find(OTPLocalizer.DialogQuestion) >= 0:
            type = 'question'
        elif random.randint(0, 1):
            type = 'statementA'
        else:
            type = 'statementB'
        stringLength = len(chatString)
        if stringLength <= OTPLocalizer.DialogLength1:
            length = 1
        elif stringLength <= OTPLocalizer.DialogLength2:
            length = 2
        elif stringLength <= OTPLocalizer.DialogLength3:
            length = 3
        else:
            length = 4
        self.playDialogue(type, length, chatString, delay)

    def playDialogue(self, type, length, chatString='', delay=0.0):
        if ClientSettings.TextToSpeechEnabled.get():
            chatString = chatString.replace('WLDisplay', '')
            soundSequence = Sequence(Wait(delay), Func(self.playTTS, chatString))
            self.soundSequenceList.append(soundSequence)
            soundSequence.start()
            self.cleanUpSoundList()
            return
        dialogueArray = self.getDialogueArray()
        if not dialogueArray:
            return
        sfxIndex = None
        if type == 'statementA' or type == 'statementB':
            if length == 1:
                sfxIndex = 0
            elif length == 2:
                sfxIndex = 1
            elif length >= 3:
                sfxIndex = 2
        elif type == 'question':
            sfxIndex = 3
        elif type == 'exclamation':
            sfxIndex = 4
        elif type == 'special':
            sfxIndex = 5
        else:
            self.notify.error('unrecognized dialogue type: ', type)
        if sfxIndex != None and sfxIndex < len(dialogueArray) and dialogueArray[sfxIndex] != None:
            node = self
            # We won't be able to hear Avatars
            # reparented to aspect2d unless
            # we do this
            if self.getParent() == aspect2d:
                node = None
            if ClientSettings.DistancedDialog.get() and hasattr(base, 'localAvatar'):
                soundSequence = Sequence(Wait(delay), SoundInterval(dialogueArray[sfxIndex], node=node, listenerNode=base.localAvatar, loop=0, volume=1.0))
            else:
                soundSequence = Sequence(Wait(delay), SoundInterval(dialogueArray[sfxIndex], loop=0, volume=1.0))
            self.soundSequenceList.append(soundSequence)
            soundSequence.start()
            self.cleanUpSoundList()

    def playTTS(self, chatString):
        try:
            if self.getTTSVolume() == 0:
                return

            # Prevent TTS voices from stacking cuz it'll
            # get loud
            if self.curTTS and not self.curTTS.poll():
                self.curTTS.terminate()

            if sys.platform == "darwin":
                self.playTTSDarwinVoice(chatString)
            else:
                self.playTTSVoice(chatString)
        except ValueError:
            pass
        except (IOError, OSError):
            base.resetTextToSpeech()
            base.localAvatar.setSystemMessage(0, OTPLocalizer.TextToSpeechWarning)

    def playTTSDarwinVoice(self, chatString):
        voice = self.getTTSDarwinVoice()
        self.curTTS = Popen(['say', voice, chatString])

    def playTTSVoice(self, chatString):
        volume = '-a' + str(self.getTTSVolume())
        pitch = self.getTTSPitch()
        self.curTTS = Popen([base.textToSpeechPath, volume, '-ven', pitch, chatString])

    def getTTSDarwinVoice(self):
        return ToontownGlobals.DefaultVoice

    def getTTSPitch(self):
        return '-p' + str(ToontownGlobals.DefaultPitch)

    def getTTSVolume(self):
        result = int(round(ClientSettings.TextToSpeechVolume.get() * 100))
        if ClientSettings.DistancedDialog.get():
            result *= self.getLocalizedVolume()
        result = max(0, min(result, 100))
        return result

    def getLocalizedVolume(self, cutoff=None):
        # This is a copy of getLocalizedVolume from SfxPlayer in
        # direct.showbase. It's copied here so TTS can use it.
        node = self
        # We won't be able to hear Avatars
        # reparented to aspect2d unless
        # we do this
        if self.getParent() == aspect2d:
            node = None
        listenerNode = base.localAvatar
        if not node:
            return 1
        d = None
        if not node.isEmpty():
            if listenerNode and not listenerNode.isEmpty():
                d = node.getDistance(listenerNode)
            else:
                d = node.getDistance(base.cam)
        if not cutoff:
            cutoff = 120.0
        if d is None or d > cutoff:
            volume = 0
        else:
            volume = 1 - (d / (cutoff or 1))

        return volume

    def getDialogueSfx(self, type, length):
        retval = None
        dialogueArray = self.getDialogueArray()
        if dialogueArray == None:
            return
        sfxIndex = None
        if type == 'statementA' or type == 'statementB':
            if length == 1:
                sfxIndex = 0
            elif length == 2:
                sfxIndex = 1
            elif length >= 3:
                sfxIndex = 2
        elif type == 'question':
            sfxIndex = 3
        elif type == 'exclamation':
            sfxIndex = 4
        elif type == 'special':
            sfxIndex = 5
        else:
            self.notify.error('unrecognized dialogue type: ', type)
        if sfxIndex != None and sfxIndex < len(dialogueArray) and dialogueArray[sfxIndex] != None:
            retval = dialogueArray[sfxIndex]
        return retval

    def setChatAbsolute(self, chatString, chatFlags, dialogue=None, interrupt=1):
        self.nametag.setChat(chatString, chatFlags)
        self.playCurrentDialogue(dialogue, chatFlags, interrupt)

    def displayTalk(self, chatString):
        for chat in base.emojis:
            chatString = chatString.replace(f':{chat}:', f'\x01white\x01\5{chat}\5\x02')
        if not base.cr.avatarFriendsManager.checkIgnored(self.doId):
            if base.talkAssistant.isThought(chatString):
                self.nametag.setChat(base.talkAssistant.removeThoughtPrefix(chatString), CFThought)
            elif base.talkAssistant.isExclaim(chatString):
                self.nametag.setChat(base.talkAssistant.removeExclaimPrefix(chatString), CFExclaim | CFTimeout)
            else:
                self.nametag.setChat(chatString, CFSpeech | CFTimeout)

    def cleanUpSoundList(self):
        removeList = []
        for soundSequence in self.soundSequenceList:
            if soundSequence.isStopped():
                removeList.append(soundSequence)

        for soundSequence in removeList:
            self.soundSequenceList.remove(soundSequence)

    def clearChat(self):
        self.nametag.clearChat()

    def isInView(self):
        pos = self.getPos(camera)
        eyePos = Point3(pos[0], pos[1], pos[2] + self.getHeight())
        return base.camNode.isInView(eyePos)

    def getNameVisible(self):
        return self.__nameVisible

    def setNameVisible(self, bool):
        self.__nameVisible = bool
        if bool:
            self.showName()
        if not bool:
            self.hideName()

    def hideName(self):
        self.nametag.getNametag3d().setContents(Nametag.CSpeech | Nametag.CThought | Nametag.CExclaim)

    def showName(self):
        if self.__nameVisible and not self.ghostMode:
            self.nametag.getNametag3d().setContents(Nametag.CName | Nametag.CSpeech | Nametag.CThought | Nametag.CExclaim)

    def hideNametag2d(self):
        self.nametag2dContents = 0
        self.nametag.getNametag2d().setContents(self.nametag2dContents & self.nametag2dDist)

    def showNametag2d(self):
        self.nametag2dContents = self.nametag2dNormalContents
        if self.ghostMode:
            self.nametag2dContents = Nametag.CSpeech
        self.nametag.getNametag2d().setContents(self.nametag2dContents & self.nametag2dDist)

    def hideNametag3d(self):
        self.nametag.getNametag3d().setContents(0)

    def showNametag3d(self):
        if self.__nameVisible and not self.ghostMode:
            self.nametag.getNametag3d().setContents(Nametag.CName | Nametag.CSpeech | Nametag.CThought | Nametag.CExclaim)
        else:
            self.nametag.getNametag3d().setContents(0)

    def setPickable(self, flag):
        self.nametag.setActive(flag)

    def clickedNametag(self):
        if self.nametag.hasButton():
            self.advancePageNumber()
        elif self.nametag.isActive():
            messenger.send('clickedNametag', [self])

    def setPageChat(self, addressee, paragraph, message, quitButton, extraChatFlags=None, dialogueList=[], pageButton=True):
        self.__chatAddressee = addressee
        self.__chatPageNumber = None
        self.__chatParagraph = paragraph
        self.__chatMessage = message
        if extraChatFlags is None:
            self.__chatFlags = CFSpeech
        else:
            self.__chatFlags = CFSpeech | extraChatFlags
        self.__chatDialogueList = dialogueList
        self.__chatSet = 0
        self.__chatLocal = 0
        self.__updatePageChat()
        if addressee == base.localAvatar.doId:
            if pageButton:
                self.__chatFlags |= CFPageButton
            if quitButton is None:
                self.__chatFlags |= CFNoQuitButton
            elif quitButton:
                self.__chatFlags |= CFQuitButton
            self.b_setPageNumber(self.__chatParagraph, 0)
        return

    def setLocalPageChat(self, message, quitButton, extraChatFlags=None, dialogueList=[]):
        self.__chatAddressee = base.localAvatar.doId
        self.__chatPageNumber = None
        self.__chatParagraph = None
        self.__chatMessage = message
        if extraChatFlags is None:
            self.__chatFlags = CFSpeech
        else:
            self.__chatFlags = CFSpeech | extraChatFlags
        self.__chatDialogueList = dialogueList
        self.__chatSet = 1
        self.__chatLocal = 1
        self.__chatFlags |= CFPageButton
        if quitButton is None:
            self.__chatFlags |= CFNoQuitButton
        elif quitButton:
            self.__chatFlags |= CFQuitButton
        if len(dialogueList) > 0:
            dialogue = dialogueList[0]
        else:
            dialogue = None
        self.clearChat()
        self.setChatAbsolute(message, self.__chatFlags, dialogue)
        self.setPageNumber(None, 0)
        return

    def setPageNumber(self, paragraph, pageNumber, timestamp=None):
        if timestamp is None:
            elapsed = 0.0
        else:
            elapsed = ClockDelta.globalClockDelta.localElapsedTime(timestamp)
        self.__chatPageNumber = [paragraph, pageNumber]
        self.__updatePageChat()
        if hasattr(self, 'uniqueName'):
            if pageNumber >= 0:
                messenger.send(self.uniqueName('nextChatPage'), [pageNumber, elapsed])
            else:
                messenger.send(self.uniqueName('doneChatPage'), [elapsed])
        elif pageNumber >= 0:
            messenger.send('nextChatPage', [pageNumber, elapsed])
        else:
            messenger.send('doneChatPage', [elapsed])
        return

    def advancePageNumber(self):
        if self.__chatAddressee == base.localAvatar.doId and self.__chatPageNumber is not None and self.__chatPageNumber[0] == self.__chatParagraph:
            pageNumber = self.__chatPageNumber[1]
            if pageNumber >= 0:
                pageNumber += 1
                if pageNumber >= self.nametag.getNumChatPages():
                    pageNumber = -1
                if self.__chatLocal:
                    self.setPageNumber(self.__chatParagraph, pageNumber)
                else:
                    self.b_setPageNumber(self.__chatParagraph, pageNumber)
        return

    def __updatePageChat(self):
        if self.__chatPageNumber is not None and self.__chatPageNumber[0] == self.__chatParagraph:
            pageNumber = self.__chatPageNumber[1]
            if pageNumber >= 0:
                if not self.__chatSet:
                    if len(self.__chatDialogueList) > 0:
                        dialogue = self.__chatDialogueList[0]
                    else:
                        dialogue = None
                    self.setChatAbsolute(self.__chatMessage, self.__chatFlags, dialogue)
                    self.__chatSet = 1
                if pageNumber < self.nametag.getNumChatPages():
                    self.nametag.setPageNumber(pageNumber)
                    if pageNumber > 0:
                        if len(self.__chatDialogueList) > pageNumber:
                            dialogue = self.__chatDialogueList[pageNumber]
                        else:
                            dialogue = None
                        self.playCurrentDialogue(dialogue, self.__chatFlags)
                else:
                    self.clearChat()
            else:
                self.clearChat()
        return

    def getAirborneHeight(self):
        height = self.getPos(self.shadowPlacer.shadowNodePath)
        return height.getZ() + 0.025

    def initializeNametag3d(self):
        self.deleteNametag3d()
        nametagNode = self.nametag.getNametag3d()
        self.nametagNodePath = self.nametag3d.attachNewNode(nametagNode)
        for cJoint in self.getNametagJoints():
            cJoint.clearNetTransforms()
            cJoint.addNetTransform(nametagNode)

    def nametagAmbientLightChanged(self, newlight):
        self.nametag3d.setLightOff()
        if newlight:
            self.nametag3d.setLight(newlight)

    def deleteNametag3d(self):
        if self.nametagNodePath:
            self.nametagNodePath.removeNode()
            self.nametagNodePath = None
        return

    def initializeBodyCollisions(self, collIdStr):
        self.collTube = CollisionTube(0, 0, 0.5, 0, 0, self.height - self.getRadius(), self.getRadius())
        self.collNode = CollisionNode(collIdStr)
        self.collNode.addSolid(self.collTube)
        self.collNodePath = self.attachNewNode(self.collNode)
        if self.ghostMode:
            self.collNode.setCollideMask(OTPGlobals.GhostBitmask)
        else:
            self.collNode.setCollideMask(OTPGlobals.WallBitmask)

    def stashBodyCollisions(self):
        if hasattr(self, 'collNodePath'):
            self.collNodePath.stash()

    def unstashBodyCollisions(self):
        if hasattr(self, 'collNodePath'):
            self.collNodePath.unstash()

    def disableBodyCollisions(self):
        if hasattr(self, 'collNodePath'):
            self.collNodePath.removeNode()
            del self.collNodePath
        self.collTube = None
        return

    def addActive(self):
        if base.wantNametags:
            try:
                Avatar.ActiveAvatars.remove(self)
            except ValueError:
                pass

            Avatar.ActiveAvatars.append(self)
            self.nametag.manage(base.marginManager)
            self.accept(self.nametag.getUniqueId(), self.clickedNametag)

    def removeActive(self):
        if base.wantNametags:
            try:
                Avatar.ActiveAvatars.remove(self)
            except ValueError:
                pass

            self.nametag.unmanage(base.marginManager)
            self.ignore(self.nametag.getUniqueId())

    def loop(self, animName, restart = 1, partName = None, fromFrame = None, toFrame = None):
        Actor.loop(self, animName, restart, partName, fromFrame, toFrame)

    # Moved these here for compatibility with non-distributed Avatars
    def showHpText(self, number, bonus = 0, scale = 1):
        if self.HpTextEnabled and not self.ghostMode:
            if number != 0:
                if self.hpText:
                    self.hideHpText()
                self.HpTextGenerator.setFont(OTPGlobals.getSignFont())
                if number < 0:
                    self.HpTextGenerator.setText(str(number))
                else:
                    self.HpTextGenerator.setText('+' + str(number))
                self.HpTextGenerator.clearShadow()
                self.HpTextGenerator.setAlign(TextNode.ACenter)
                if bonus == 1:
                    r = 1.0
                    g = 1.0
                    b = 0
                    a = 1
                elif bonus == 2:
                    r = 1.0
                    g = 0.5
                    b = 0
                    a = 1
                elif number < 0:
                    r = 0.9
                    g = 0
                    b = 0
                    a = 1
                else:
                    r = 0
                    g = 0.9
                    b = 0
                    a = 1
                self.HpTextGenerator.setTextColor(r, g, b, a)
                self.hpTextNode = self.HpTextGenerator.generate()
                self.hpText = self.attachNewNode(self.hpTextNode)
                self.hpText.setScale(scale)
                self.hpText.setBillboardPointEye()
                self.hpText.setBin('fixed', 100)
                self.hpText.setPos(0, 0, self.height / 2)
                self.hpTextSeq = Sequence(
                        self.hpText.posInterval(1.0, Point3(0, 0, self.height + 1.5), blendType='easeOut'),
                        Wait(0.85),
                        self.hpText.colorScaleInterval(0.1, Vec4(r, g, b, 0)),
                        Func(self.hideHpText))
                self.hpTextSeq.start()

    def showHpString(self, text, duration = 0.85, scale = 0.7):
        if self.HpTextEnabled and not self.ghostMode:
            if text != '':
                if self.hpText:
                    self.hideHpText()
                self.HpTextGenerator.setFont(OTPGlobals.getSignFont())
                self.HpTextGenerator.setText(text)
                self.HpTextGenerator.clearShadow()
                self.HpTextGenerator.setAlign(TextNode.ACenter)
                r = a = 1.0
                g = b = 0.0
                self.HpTextGenerator.setTextColor(r, g, b, a)
                self.hpTextNode = self.HpTextGenerator.generate()
                self.hpText = self.attachNewNode(self.hpTextNode)
                self.hpText.setScale(scale)
                self.hpText.setBillboardAxis()
                self.hpText.setPos(0, 0, self.height / 2)
                self.hpTextSeq = Sequence(
                    self.hpText.posInterval(1.0, Point3(0, 0, self.height + 1.5), blendType='easeOut'), 
                    Wait(duration), 
                    self.hpText.colorScaleInterval(0.1, Vec4(r, g, b, 0)), 
                    Func(self.hideHpText)
                    )
                self.hpTextSeq.start()

    def hideHpText(self):
        if self.hpText:
            self.hpText.removeNode()
            self.hpText = None
            if self.hpTextSeq:
                self.hpTextSeq.finish()
                self.hpTextSeq = None
        return

    def tryShowGeom(self) -> bool:
        """Wrapper around Actor.getGeomNode().show() to avoid revealing ghosted avatars."""
        if self.ghostMode:
            return False
        avatarGeom: GeomNode = self.getGeomNode()
        avatarGeom.show()
        return True

    def tryShowDropShadow(self) -> bool:
        """Wrapper around Avatar.dropShadow.show() to avoid revealing ghosted avatars."""
        if self.ghostMode:
            return False
        self.dropShadow.show()
        return True

    def tryShowNametag(self) -> bool:
        """Wrapper around Avatar.nametag3d.show() to avoid revealing ghosted avatars."""
        if self.ghostMode:
            return False
        self.nametag3d.show()
        return True
