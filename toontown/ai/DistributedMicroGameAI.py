from direct.distributed.DistributedObjectAI import DistributedObjectAI
from direct.distributed.ClockDelta import globalClockDelta
from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.fsm.FSM import FSM
from panda3d.toontown import WhisperPopup
from otp.avatar.DistributedPlayerAI import DistributedPlayerAI
from toontown.hood.ZoneUtil import getCanonicalBranchZone
from toontown.toonbase import TTLocalizer, ToontownGlobals


class DistributedMicroGameAI(DistributedObjectAI, FSM):
    notify = directNotify.newCategory('DistributedMicroGameAI')
    defaultTransitions = {'Off': ['Start'],
                          'Start': ['Done', 'Off'],
                          'Done': ['Off']}

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)
        FSM.__init__(self, 'DistributedMicroGameAI')
        self._duration = 60
        self._startTimestamp = None

    def announceGenerate(self):
        DistributedObjectAI.announceGenerate(self)

    def delete(self):
        self.setupRules(False)
        self._cleanupTasks()
        del self._duration
        FSM.cleanup(self)
        self.ignoreAll()
        self.air.microGameMgr.microGames[self.zoneId] = None
        DistributedObjectAI.delete(self)

    def _cleanupTasks(self):
        taskMgr.remove(self.uniqueName('enterNextState'))
        taskMgr.remove(self.uniqueName('finishGame'))

    def getName(self):
        return TTLocalizer.MicroGameDefaultTitle

    def getDuration(self):
        return self._duration

    def b_setDuration(self, dur):
        self.setDuration(dur)
        self.d_setDuration(dur)

    def setDuration(self, dur):
        self._duration = dur

    def d_setDuration(self, dur):
        self.sendUpdate('setDuration', [dur])

    def _initializePlayers(self):
        for doId, do in list(self.air.doId2do.items()):
            if isinstance(do, DistributedPlayerAI):
                if str(doId)[0] != str(self.air.districtId)[0]:
                    if getCanonicalBranchZone(do.zoneId) != self.zoneId:
                        continue
                    avExitEvent = self.air.getAvatarExitEvent(doId)
                    self.acceptOnce(avExitEvent, self.handleAvatarExited, extraArgs=[do])

    def _callFuncOnPlayers(self, func, *args):
        for doId, do in list(self.air.doId2do.items()):
            if isinstance(do, DistributedPlayerAI):
                if str(doId)[0] != str(self.air.districtId)[0]:
                    if getCanonicalBranchZone(do.zoneId) != self.zoneId:
                        continue
                    playerFunc = getattr(do, func)
                    if playerFunc:
                        playerFunc(*args)

    def _callFuncOnPlayer(self, avId, func, *args):
        av = self.air.doId2do.get(avId)
        if av:
            if isinstance(av, DistributedPlayerAI):
                if str(avId)[0] != str(self.air.districtId)[0]:
                    if getCanonicalBranchZone(av.zoneId) != self.zoneId:
                        return
                    playerFunc = getattr(av, func)
                    if playerFunc:
                        playerFunc(*args)

    def _callFuncsOnPlayers(self, funcDefs):
        for doId, do in list(self.air.doId2do.items()):
            if isinstance(do, DistributedPlayerAI):
                if str(doId)[0] != str(self.air.districtId)[0]:
                    if getCanonicalBranchZone(do.zoneId) != self.zoneId:
                        continue
                    for funcDef in funcDefs:
                        func = funcDef[0]
                        args = funcDef[1:]
                        playerFunc = getattr(do, func)
                        if playerFunc:
                            playerFunc(*args)

    def _callFuncsOnPlayer(self, funcDefs, avId):
        av = self.air.doId2do.get(avId)
        if av:
            if isinstance(av, DistributedPlayerAI):
                if str(avId)[0] != str(self.air.districtId)[0]:
                    if getCanonicalBranchZone(av.zoneId) != self.zoneId:
                        return
                    for funcDef in funcDefs:
                        func = funcDef[0]
                        args = funcDef[1:]
                        playerFunc = getattr(av, func)
                        if playerFunc:
                            playerFunc(*args)

    def handleAvatarEntered(self, av):
        self.notify.debug('avatar entered %s' % av)
        if hasattr(self, 'messages') and self.messages:
            avId = av.getDoId()
            av.d_setSystemMessage(0, self.messages.get('update'))
            self.setupRules(True, avId)
            avExitEvent = self.air.getAvatarExitEvent(avId)
            self.acceptOnce(avExitEvent, self.handleAvatarExited, extraArgs=[av])

    def handleAvatarExited(self, av):
        self.notify.debug('avatar exited %s' % av)
        self.setupRules(False, av.getDoId())

    def _broadcastSystemMessage(self, msg):
        self._callFuncOnPlayers('d_setSystemMessage', 0, msg, WhisperPopup.WTSystem)

    def _sendSystemMessageToAv(self, msg, avId):
        self._callFuncOnPlayer(avId, 'd_setSystemMessage', 0, msg, WhisperPopup.WTSystem)

    def isActive(self):
        return self.getCurrentOrNextState() == 'Start'

    def b_setState(self, state):
        self.request(state)
        self.d_setState(state)

    def d_setState(self, state):
        self.sendUpdate('setState', [state])

    def enterOff(self):
        self._cleanupTasks()

    def filterOff(self, request, args):
        self.notify.debug("filter%s( '%s', '%s' )" % (self.state, request, args))
        if request == self.state:
            return
        elif request == 'next':
            return 'Start'
        else:
            return self.defaultFilter(request, args)

    def exitOff(self):
        pass

    def setupRules(self, flag, avId=None):
        if flag:
            if avId:
                self._callFuncsOnPlayer((('b_setRun', False, 1.0), ('d_setToonScale', 1.0)), avId)
            else:
                self._callFuncsOnPlayers((('b_setRun', False, 1.0), ('d_setToonScale', 1.0)))

    def enterStart(self):
        self._initializePlayers()
        if hasattr(self, 'messages') and self.messages:
            self._broadcastSystemMessage(self.messages.get('start').format(self._duration))
        self.setupRules(True)
        self._startTimestamp = globalClockDelta.getRealNetworkTime()
        taskMgr.doMethodLater(self._duration, self.b_setState, self.uniqueName('finishGame'), extraArgs=['next'])
        self.sendUpdate('sendStartTime', [self._startTimestamp])

    def filterStart(self, request, args):
        self.notify.debug("filter%s( '%s', '%s' )" % (self.state, request, args))
        if request == self.state:
            return
        elif request == 'next':
            return 'Done'
        else:
            return self.defaultFilter(request, args)

    def exitStart(self):
        pass

    def enterDone(self):
        def deleteTask(task):
            self.d_setState('Done')
            self.requestDelete()
            return task.done

        self._cleanupTasks()
        if hasattr(self, 'messages') and self.messages:
            self._broadcastSystemMessage(self.messages.get('end'))
        self.sendUpdate('sendStartTime', [ToontownGlobals.MicroGameTimerOff])
        self._startTimestamp = None
        taskMgr.doMethodLater(0.1, deleteTask, self.uniqueName('enterNextState'))

    def filterDone(self, request, args):
        self.notify.debug("filter%s( '%s', '%s' )" % (self.state, request, args))
        if request == self.state:
            return
        else:
            return self.defaultFilter(request, args)

    def exitDone(self):
        pass
