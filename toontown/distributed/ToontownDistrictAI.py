from direct.directnotify import DirectNotifyGlobal

from otp.distributed.DistributedDistrictAI import DistributedDistrictAI

from toontown.toonbase import TTLocalizer, ToontownGlobals


class ToontownDistrictAI(DistributedDistrictAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownDistrictAI')

    def __init__(self, air):
        DistributedDistrictAI.__init__(self, air)
        self.ahnnLog = False
        self.description = ''
        self.iconPath = ''
        self.timestamp = None
        self.legitMode = False
        self.nerfsMode = False
        self.classicFishing = True
        self.whitelist = False
        self.customWhitelist = []
        self.whiteListMode = 0
        self.wantGlobalChat = True
        self.selfToonUp = True
        self.populationLimit = ToontownGlobals.DEFAULT_POP_LIMIT
        self.classicAnimatedPropFaceoff = False if not self.legitMode else True
        self.experimentalFeatures: bool = False

    def allowAHNNLog(self, ahnnLog):
        self.ahnnLog = ahnnLog

    def d_allowAHNNLog(self, ahnnLog):
        self.sendUpdate('allowAHNNLog', [ahnnLog])

    def b_allowAHNNLog(self, ahnnLog):
        self.allowAHNNLog(ahnnLog)
        self.d_allowAHNNLog(ahnnLog)

    def getAllowAHNNLog(self):
        return self.ahnnLog

    def requestOnlineAvatars(self):
        senderId = self.air.getAccountIdFromSender()
        onlineAvatars = list(self.air.onlineAvatars.values())
        self.sendUpdateToAccountId(senderId, 'onlineAvatarsResponse', [onlineAvatars])

    def setDescription(self, description):
        # If we're in Offline Mode, the realm description should say Offline Mode.
        if simbase.air.gamemode:
            self.description = TTLocalizer.DiscordOffline
        # Otherwise, let's provide a default miniserver description if the realm hoster hasn't provided one.
        elif description == TTLocalizer.WordPageNA:
            self.description = TTLocalizer.DistrictMiniserverDefault
        # Guess they did provide one. Okay, custom description it is.
        else:
            self.description = description

    def getDescription(self):
        return self.description

    def setIconPath(self, path):
        self.iconPath = path

    def d_setIconPath(self, path):
        self.sendUpdate('setIconPath', [path])

    def b_setIconPath(self, path):
        self.setIconPath(path)
        self.d_setIconPath(path)

    def getIconPath(self):
        return self.iconPath

    def setTimestamp(self, timestamp):
        self.timestamp = timestamp

    def getTimestamp(self):
        return self.timestamp

    def setLegitMode(self, legitMode):
        self.legitMode = legitMode

    def getLegitMode(self):
        return self.legitMode

    def setNerfsMode(self, nerfsMode):
        self.nerfsMode = nerfsMode

    def getNerfsMode(self):
        return self.nerfsMode

    def setExperimentalFeatures(self, experimental: bool):
        if experimental:
            self.notify.warning("!!!EXPERIMENTAL FEATURES ARE ENABLED!!!")
        self.experimentalFeatures = experimental

    def getExperimentalFeatures(self) -> bool:
        return self.experimentalFeatures

    def setClassicFishing(self, classicFishing):
        self.classicFishing = classicFishing

    def getClassicFishing(self):
        return self.classicFishing

    def setWhitelist(self, whitelist):
        self.whitelist = whitelist

    def getWhitelist(self):
        return self.whitelist

    def setCustomWhitelist(self, custom):
        self.customWhitelist = custom

    def getCustomWhitelist(self):
        return self.customWhitelist

    def setWhitelistMode(self, mode):
        self.whiteListMode = mode

    def getWhitelistMode(self):
        return self.whiteListMode

    def setGlobalChat(self, wantGlobalChat):
        self.wantGlobalChat = wantGlobalChat

    def getGlobalChat(self):
        return self.wantGlobalChat

    def setPropFaceoffTime(self, isClassic):
        self.classicAnimatedPropFaceoff = isClassic

    def getPropFaceoffTime(self):
        return self.classicAnimatedPropFaceoff

    def setSelfToonUp(self, selfToonUp):
        self.selfToonUp = selfToonUp

    def d_setSelfToonUp(self, selfToonUp):
        self.sendUpdate('setSelfToonUp', [selfToonUp])

    def b_setSelfToonUp(self, selfToonUp):
        self.setSelfToonUp(selfToonUp)
        self.d_setSelfToonUp(selfToonUp)

    def getSelfToonUp(self):
        return self.selfToonUp

    def setPopulationLimit(self, popLimit):
        self.populationLimit = popLimit

    def getPopulationLimit(self):
        return self.populationLimit

