from toontown.toonbase import ToontownGlobals
from toontown.chat import ToonChatGarbler
from toontown.social.SocialGlobals import VisibilityTypes

from typing import Tuple

class AvatarHandle:

    def __init__(self, doId, name, style, petId, isAPet = False,
                 accessories = ((0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)),
                 profileBackground = 0, profilePose = 0,
                 visibility = VisibilityTypes.ONLINE
                 ):
        self.doId = doId
        self.style = style
        self.commonChatFlags = 0
        self.whitelistChatFlags = 0
        self.petId = petId
        self.isAPet = isAPet
        self.chatGarbler = ToonChatGarbler.ToonChatGarbler()
        self.name = name
        for emoji in base.emojis:
            self.name = self.name.replace(f':{emoji}:', f'\x01white\x01\5{emoji}\5\x02')
        self.accessories = accessories
        self.profileBackground = profileBackground
        self.profilePose = profilePose
        self.visibility = visibility

    def getDoId(self):
        return self.doId

    def getPetId(self):
        return self.petId

    def hasPet(self):
        return self.getPetId() != 0

    def isPet(self):
        return self.isAPet

    def getName(self):
        if base.cr.getChatFilterMode() >= ToontownGlobals.CHAT_FILTER_CENSOR:
            # todo: handle whitelist
            return base.profanityFilter.censor(self.name)
        return self.name

    def getFont(self):
        return ToontownGlobals.getToonFont()

    def getHat(self) -> Tuple[int, int, int]:
        return self.accessories[0]

    def getGlasses(self) -> Tuple[int, int, int]:
        return self.accessories[1]

    def getBackpack(self) -> Tuple[int, int, int]:
        return self.accessories[2]

    def getShoes(self) -> Tuple[int, int, int]:
        return self.accessories[3]

    def getStyle(self):
        return self.style

    def getDNAString(self) -> str:
        return self.style.makeNetString()

    def getProfileBackground(self) -> int:
        return self.profileBackground

    def getProfilePose(self) -> int:
        return self.profilePose

    def getVisibility(self):
        return self.visibility

    def uniqueName(self, idString):
        return idString + '-' + str(self.getDoId())

    def isUnderstandable(self):
        if self.commonChatFlags & base.localAvatar.commonChatFlags & ToontownGlobals.CommonChat:
            understandable = 1
        elif self.commonChatFlags & ToontownGlobals.SuperChat:
            understandable = 1
        elif base.localAvatar.commonChatFlags & ToontownGlobals.SuperChat:
            understandable = 1
        elif base.cr.getFriendFlags(self.doId) & ToontownGlobals.FriendChat:
            understandable = 1
        elif self.whitelistChatFlags & base.localAvatar.whitelistChatFlags:
            understandable = 1
        else:
            understandable = 0
        return understandable

    def filterChatString(self, chatString, fromId):
        if base.cr.getChatFilterMode() == ToontownGlobals.CHAT_FILTER_WHITELIST:
            if (fromId, 1) in base.localAvatar.friendsList:
                return chatString

            animalType = self.style.getType()

            words = chatString.split(' ')
            newWords = []
            i = 0
            for word in words:
                if word == '' or (word == '.' and len(words) == 1):
                    newWords.append(word)
                elif (word.startswith(".") or word.startswith("!")) and len(word) > 1 and i == 0:
                    if base.whiteList.isWord(word[1:]):
                        newWords.append(word)
                    else:
                        if fromId == base.localAvatar.doId:
                            garbledWord = word
                        else:
                            garbledWord = self.chatGarbler.garbleSingle(animalType, word)
                        newWords.append(word[0] + '\x01WLDisplay\x01' + garbledWord + '\x02')
                elif base.whiteList.isWord(word):
                    newWords.append(word)
                else:
                    if fromId == base.localAvatar.doId:
                        garbledWord = word
                    else:
                        garbledWord = self.chatGarbler.garbleSingle(animalType, word)
                    newWords.append('\x01WLDisplay\x01' + garbledWord + '\x02')
                i += 1

            return ' '.join(newWords)
        elif base.cr.getChatFilterMode() == ToontownGlobals.CHAT_FILTER_CENSOR:
            return base.profanityFilter.censor(chatString)
        else:
            return chatString

    def setCommonAndWhitelistChatFlags(self, commonChatFlags, whitelistChatFlags):
        self.commonChatFlags = commonChatFlags
        self.whitelistChatFlags = whitelistChatFlags
