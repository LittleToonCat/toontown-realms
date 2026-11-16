from direct.distributed.ClockDelta import globalClockDelta
from direct.directnotify.DirectNotifyGlobal import directNotify
from otp.avatar.DistributedPlayerAI import DistributedPlayerAI
from .DistributedMicroGameAI import DistributedMicroGameAI
from toontown.hood.ZoneUtil import getCanonicalBranchZone
from toontown.toonbase import TTLocalizer, ToontownGlobals
import random


class DistributedHideAndSeekAI(DistributedMicroGameAI):
    notify = directNotify.newCategory('DistributedHideAndSeekAI')
    messages = {'start': TTLocalizer.HideAndSeekStartHider,
                'startSeeker': TTLocalizer.HideAndSeekStartSeeker,
                'seek': TTLocalizer.HideAndSeekSeekHider,
                'seekSeeker': TTLocalizer.HideAndSeekSeekSeeker,
                'update': TTLocalizer.HideAndSeekInProgress,
                'newSeeker': TTLocalizer.HideAndSeekNewSeeker,
                'noHidersLeft': TTLocalizer.HideAndSeekEndNoHidersLeft,
                'found': TTLocalizer.HideAndSeekFound,
                'foundSeeker': TTLocalizer.HideAndSeekFoundSeeker,
                'end': TTLocalizer.HideAndSeekEnd}
    defaultTransitions = {'Off': ['Start'],
                          'Start': ['Seek', 'Done', 'Off'],
                          'Seek': ['Done', 'Off'],
                          'Done': ['Off']}

    def __init__(self, air):
        DistributedMicroGameAI.__init__(self, air)
        self._duration = ToontownGlobals.DefaultHideAndSeekHidingDuration
        self._seekingDuration = ToontownGlobals.DefaultHideAndSeekSeekingDuration
        self._hiders = []
        self._seeker = 0

    def _cleanupTasks(self):
        DistributedMicroGameAI._cleanupTasks(self)
        taskMgr.remove(self.uniqueName('finishHiding'))

    def getName(self):
        return TTLocalizer.HideAndSeekTitle

    def isActive(self):
        return self.getCurrentOrNextState() in ('Start', 'Seek')

    def b_setSeeker(self, avId):
        self.setSeeker(avId)
        self.d_setSeeker(avId)

    def d_setSeeker(self, avId):
        seeker = self.air.doId2do.get(avId)
        if seeker:
            self.sendUpdate('setSeeker', [seeker.getName()])
        elif avId == 0:
            self.sendUpdate('setSeeker', [''])

    def setSeeker(self, avId):
        if avId == 0:
            self.ignore(self.air.getAvatarExitEvent(self._seeker))

        self._seeker = avId

        if avId != 0:
            avExitEvent = self.air.getAvatarExitEvent(avId)
            av = self.air.doId2do.get(avId)
            if av:
                self.acceptOnce(avExitEvent, self.handleAvatarExited, extraArgs=[av])

    def __setNewSeeker(self):
        if len(self._hiders) > 0:
            newSeekerId = random.choice(self._hiders)
            self.b_setSeeker(newSeekerId)
            self.removeHider(newSeekerId)
            self._broadcastSystemMessage(self.messages.get('newSeeker'))

            if self.getCurrentOrNextState() == 'Seek':
                self.sendUpdateToAvatarId(newSeekerId, 'sendClearHideEvents', [])
                self.sendUpdateToAvatarId(self._seeker, 'setCollMaskPie', [])
                self.__initializeHiderCollisions()

            self.__checkForHidersGone()

    def getSeeker(self):
        return self._seeker

    def addHider(self, avId):
        # Possible for hider to already be in hiders list
        # if they were in a building in the same branch zone
        # when the game started and came out after seeking
        # state started
        if avId not in self._hiders:
            self._hiders.append(avId)

    def removeHider(self, avId):
        if avId in self._hiders:
            self._hiders.remove(avId)
        self.ignore(self.air.getAvatarExitEvent(avId))

    def __removeAllHiders(self):
        if hasattr(self, '_hiders'):
            for hider in self._hiders:
                self.removeHider(hider)

    def __checkForHidersGone(self):
        if len(self._hiders) == 0:
            self.sendUpdateToAvatarId(self._seeker, 'setCollMaskPie', [])
            self._broadcastSystemMessage(self.messages.get('noHidersLeft'))
            self.d_setState('Done')
            self.requestDelete()

    def delete(self):
        del self._seekingDuration
        self.__removeAllHiders()
        del self._hiders
        DistributedMicroGameAI.delete(self)

    def getSeekingDuration(self):
        return self._seekingDuration

    def setSeekingDuration(self, dur):
        self._seekingDuration = dur

    def handleAvatarEntered(self, av):
        DistributedMicroGameAI.handleAvatarEntered(self, av)
        avId = av.getDoId()
        if avId != self.getSeeker():
            self.addHider(avId)
            if self.getCurrentOrNextState() == 'Seek':
                self.sendUpdateToAvatarId(self._seeker, 'acceptFoundEvent', [avId])
                self.sendUpdateToAvatarId(self._seeker, 'setCollMaskWall', [avId])

    def handleAvatarExited(self, av):
        DistributedMicroGameAI.handleAvatarExited(self, av)
        avId = av.getDoId()
        if avId == self.getSeeker():
            self.__setNewSeeker()
        else:
            self.__handleRemoveHider(av.getDoId())

    def enterOff(self):
        DistributedMicroGameAI.enterOff(self)
        self.__removeAllHiders()
        self.sendUpdate('sendClearHideEvents', [])
        self.sendUpdateToAvatarId(self._seeker, 'setCollMaskPie', [])
        self.b_setSeeker(0)

    def _initializePlayers(self):
        for doId, do in list(self.air.doId2do.items()):
            if doId == self._seeker:
                continue
            elif isinstance(do, DistributedPlayerAI):
                if str(doId)[0] != str(self.air.districtId)[0]:
                    if getCanonicalBranchZone(do.zoneId) != self.zoneId:
                        continue
                    self.addHider(doId)
                    avExitEvent = self.air.getAvatarExitEvent(doId)
                    self.acceptOnce(avExitEvent, self.handleAvatarExited, extraArgs=[do])

    def __initializeHiderCollisions(self):
        for doId, do in list(self.air.doId2do.items()):
            if doId == self._seeker:
                continue
            elif isinstance(do, DistributedPlayerAI):
                if str(doId)[0] != str(self.air.districtId)[0]:
                    if getCanonicalBranchZone(do.zoneId) != self.zoneId:
                        continue
                    self.sendUpdateToAvatarId(self._seeker, 'acceptFoundEvent', [doId])
        self.sendUpdateToAvatarId(self._seeker, 'setCollMaskWall', [0])

    def __handleRemoveHider(self, avId):
        self.removeHider(avId)
        self.__checkForHidersGone()

    def setupRules(self, flag, avId=None):
        DistributedMicroGameAI.setupRules(self, flag, avId)
        if flag:
            if avId:
                self._callFuncOnPlayer(avId, 'requestKart', False)
            else:
                self._callFuncOnPlayers('requestKart', False)

    def enterStart(self):
        self._initializePlayers()
        for hider in self._hiders:
            self._sendSystemMessageToAv(self.messages.get('start').format(self._duration), hider)
        self._sendSystemMessageToAv(self.messages.get('startSeeker').format(self._duration), self._seeker)
        self.setupRules(True)
        self._startTimestamp = globalClockDelta.getRealNetworkTime()
        taskMgr.doMethodLater(self._duration, self.b_setState, self.uniqueName('finishHiding'), extraArgs=['next'])
        self.sendUpdate('sendStartTime', [self._startTimestamp])

    def filterStart(self, request, args):
        self.notify.debug("filter%s( '%s', '%s' )" % (self.state, request, args))
        if request == self.state:
            return
        elif request == 'next':
            return 'Seek'
        else:
            return self.defaultFilter(request, args)

    def enterSeek(self):
        self.__initializeHiderCollisions()
        self.b_setDuration(self._seekingDuration)
        for hider in self._hiders:
            self._sendSystemMessageToAv(self.messages.get('seek').format(self._duration), hider)
        self._sendSystemMessageToAv(self.messages.get('seekSeeker').format(self._duration), self._seeker)
        self._startTimestamp = globalClockDelta.getRealNetworkTime()
        taskMgr.doMethodLater(self._duration, self.b_setState, self.uniqueName('finishGame'), extraArgs=['next'])
        self.sendUpdate('sendStartTime', [self._startTimestamp])

    def filterSeek(self, request, args):
        self.notify.debug("filter%s( '%s', '%s' )" % (self.state, request, args))
        if request == self.state:
            return
        elif request == 'next':
            return 'Done'
        else:
            return self.defaultFilter(request, args)

    def exitSeek(self):
        pass

    def enterDone(self):
        self.__removeAllHiders()
        DistributedMicroGameAI.enterDone(self)

    def found(self, avId):
        self.__checkFound(avId)

    def __checkFound(self, avId):
        if avId in self._hiders:
            self.notify.debug('Found ' + str(avId))
            self.removeHider(avId)
            self._sendSystemMessageToAv(self.messages.get('found'), avId)
            av = self.air.doId2do.get(avId)
            if av:
                self._sendSystemMessageToAv(self.messages.get('foundSeeker') % av.getName(), self._seeker)
            self.__checkForHidersGone()
        else:
            self.notify.debug('Bumped ' + str(avId))
