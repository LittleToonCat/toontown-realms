from direct.directnotify import DirectNotifyGlobal
from otp.distributed import DistributedDistrict
from otp.otpbase import OTPGlobals
from toontown.toonbase import ToontownGlobals
from toontown.suit import SuitDNA

import json


class ToontownDistrict(DistributedDistrict.DistributedDistrict):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownDistrict')

    def __init__(self, cr):
        DistributedDistrict.DistributedDistrict.__init__(self, cr)
        self.avatarCount = 0
        self.newAvatarCount = 0
        self.description = ''
        self.iconPath = ''
        self.timestamp = None
        self.legitMode = False
        self.nerfsMode = False
        self.classicFishing = True
        self.whitelist = OTPGlobals.CHAT_FILTER_CENSOR
        self.customWhitelist = []
        self.whiteListMode = 0
        self.wantGlobalChat = True
        self.outskirtsTheme = ''
        self.selfToonUp = True
        self.populationLimit = ToontownGlobals.DEFAULT_POP_LIMIT
        self.classicAnimatedPropFaceoff = False if not self.legitMode else True
        self.experimentalFeatures: bool = False

    def announceGenerate(self):
        DistributedDistrict.DistributedDistrict.announceGenerate(self)
        self.d_requestOnlineAvatars()

    def d_requestOnlineAvatars(self):
        self.sendUpdate('requestOnlineAvatars')

    def onlineAvatarsResponse(self, onlineAvatars):
        self.cr.handleGetOnlineAvatars(onlineAvatars)

    def updateOnlineAvatar(self, onlineAvatar):
        self.cr.updateOnlineAvatar(onlineAvatar)

    def removeOnlineAvatar(self, doId):
        self.cr.removeOnlineAvatar(doId)

    def allowAHNNLog(self, allow):
        self.allowAHNN = allow

    def getAllowAHNNLog(self):
        return self.allowAHNN

    def setName(self, name):
        DistributedDistrict.DistributedDistrict.setName(self, name)
        base.cr.serverName = self.name

    def setDescription(self, description):
        self.description = description
        base.cr.serverDescription = self.description

    def setIconPath(self, path):
        self.iconPath = path
        base.cr.serverIconPath = self.iconPath

    def setTimestamp(self, timestamp):
        timestamp = json.loads(timestamp)
        self.timestamp = timestamp
        base.cr.timestamp = timestamp

    def setLegitMode(self, legitMode):
        self.legitMode = legitMode
        base.cr.legitMode = legitMode

    def setNerfsMode(self, nerfsMode):
        self.nerfsMode = nerfsMode
        base.cr.nerfsMode = nerfsMode

    def setExperimentalFeatures(self, experimental: bool):
        if experimental:
            self.notify.warning("!!!EXPERIMENTAL FEATURES ARE ENABLED!!!")
        self.experimentalFeatures = experimental
        base.cr.experimentalFeatures = experimental

    def setClassicFishing(self, classicFishing):
        self.classicFishing = classicFishing
        base.cr.classicFishing = classicFishing

    def setWhitelist(self, whitelist):
        self.whitelist = whitelist
        base.cr.whiteListChatEnabled = whitelist

    def setCustomWhitelist(self, custom):
        self.customWhitelist = custom
        base.cr.customWhitelist = custom

    def setWhitelistMode(self, mode):
        self.whiteListMode = mode
        base.cr.whiteListMode = mode

    def setGlobalChat(self, wantGlobalChat):
        self.wantGlobalChat = wantGlobalChat
        base.cr.wantGlobalChat = wantGlobalChat

    def setPropFaceoffTime(self, isClassic):
        self.classicAnimatedPropFaceoff = isClassic
        base.cr.classicAnimatedPropFaceoff = isClassic

    def setSelfToonUp(self, selfToonUp):
        self.selfToonUp = selfToonUp
        base.cr.selfToonUp = selfToonUp

    def setPopulationLimit(self, popLimit):
        self.populationLimit = popLimit
        base.cr.populationLimit = popLimit

    def handlePlayerBanned(self, avId):
        messenger.send('playerBanned', [avId])
