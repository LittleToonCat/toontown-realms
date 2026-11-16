from direct.distributed.DistributedObject import DistributedObject
from direct.distributed.ClockDelta import globalClockDelta
from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.fsm.FSM import FSM
from toontown.toonbase.ToontownTimer import ToontownTimer
from toontown.toonbase.ToontownGlobals import NormalGravity, MicroGameTimerOff
from toontown.hood import ZoneUtil
from direct.showbase.InputStateGlobal import inputState


class DistributedMicroGame(DistributedObject, FSM):
    notify = directNotify.newCategory('DistributedMicroGame')
    defaultTransitions = {'Off': ['Start'],
                          'Start': ['Done', 'Off'],
                          'Done': ['Off']}

    def __init__(self, cr):
        DistributedObject.__init__(self, cr)
        FSM.__init__(self, 'DistributedMicroGame')
        self._timer = ToontownTimer()
        self._timer.setBin('gui-popup', 0)

    def announceGenerate(self):
        DistributedObject.announceGenerate(self)
        self._timer.posBelowTopRightCorner()
        self._timer.hide()

    def delete(self):
        self._timer.destroy()
        FSM.cleanup(self)
        DistributedObject.delete(self)

    # Update timer for toons who enter after the game started
    def sendStartTime(self, timestamp):
        # We're storing this field in ram so we need a value to hide the timer
        # (Right now this only applies for Boss Parties because they're the only
        # type of micro game that persists)
        if timestamp == MicroGameTimerOff:
            self._timer.hide()
            self._timer.reset()
        else:
            self._timer.show()
            time = globalClockDelta.localElapsedTime(timestamp)
            self._timer.countdown(self._duration - time)

    def setDuration(self, dur):
        self._duration = dur

    def isActive(self):
        return self.getCurrentOrNextState() == 'Start'

    def setState(self, state):
        self.request(state)

    def enterOff(self):
        self.setupRules(False)

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

    def setupRules(self, flag):
        if flag:
            self.setNeverDisable(True)
            inputState.set('debugRunning', False)
            if ZoneUtil.isBetaPlaygroundZone(self.zoneId):
                base.localAvatar.setWalkSpeedOld()
            else:
                base.localAvatar.setWalkSpeedNormal()
            base.localAvatar.collisionsOn()
            currentControls = base.localAvatar.controlManager.currentControls
            if hasattr(currentControls, 'setGravity'):
                currentControls.setGravity(NormalGravity)
            if base.cr.areCheesyEffectsAllowed():
                base.cr.forbidCheesyEffects(1)
        else:
            self.setNeverDisable(False)
            if not base.cr.areCheesyEffectsAllowed():
                base.cr.forbidCheesyEffects(0)

    def enterStart(self):
        self.setupRules(True)

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
        self._timer.hide()
        self._timer.reset()
        self.setupRules(False)

    def filterDone(self, request, args):
        self.notify.debug("filter%s( '%s', '%s' )" % (self.state, request, args))
        if request == self.state:
            return
        else:
            return self.defaultFilter(request, args)

    def exitDone(self):
        pass
