from . import DistributedCCharBase
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State
from direct.interval.IntervalGlobal import *
from . import CharStateDatas
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer


class DistributedBetaPluto(DistributedCCharBase.DistributedCCharBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBetaPluto')

    def __init__(self, cr):
        try:
            self.DistributedBetaPluto_initialized
        except:
            self.DistributedBetaPluto_initialized = 1
            DistributedCCharBase.DistributedCCharBase.__init__(self, cr, TTLocalizer.Pluto, 'p')
            self.fsm = ClassicFSM.ClassicFSM(self.getName(), [State.State('Off', self.enterOff, self.exitOff,
                                                                          ['Neutral']),
                                                              State.State('Neutral', self.enterNeutral,
                                                                          self.exitNeutral, ['Walk']),
                                                              State.State('Walk', self.enterWalk, self.exitWalk,
                                                                          ['Neutral'])], 'Off', 'Off')
            self.fsm.enterInitialState()

    def disable(self):
        self.fsm.requestFinalState()
        DistributedCCharBase.DistributedCCharBase.disable(self)
        del self.neutralDoneEvent
        del self.neutral
        del self.walkDoneEvent
        del self.walk
        del self.walkStartTrack
        del self.neutralStartTrack
        self.fsm.requestFinalState()

    def delete(self):
        try:
            self.DistributedBetaPluto_deleted
        except:
            del self.fsm
            self.DistributedBetaPluto_deleted = 1
            DistributedCCharBase.DistributedCCharBase.delete(self)

    def generate(self):
        DistributedCCharBase.DistributedCCharBase.generate(self)
        name = self.getName()
        self.neutralDoneEvent = self.taskName(name + '-neutral-done')
        self.neutral = CharStateDatas.CharNeutralState(self.neutralDoneEvent, self)
        self.walkStartTrack = Sequence(self.actorInterval('stand'), Func(self.stand))
        self.neutralStartTrack = Sequence(self.actorInterval('sit'), Func(self.sit))
        self.walkDoneEvent = self.taskName(name + '-walk-done')
        self.walk = CharStateDatas.CharWalkState(self.walkDoneEvent, self)
        self.fsm.request('Neutral')

    def stand(self):
        self.dropShadow.setScale(0.9, 1.35, 0.9)
        if hasattr(self, 'collNodePath'):
            self.collNodePath.setScale(1.0, 1.5, 1.0)

    def sit(self):
        self.dropShadow.setScale(0.9)
        if hasattr(self, 'collNodePath'):
            self.collNodePath.setScale(1.0)

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    def enterNeutral(self):
        self.notify.debug('Neutral ' + self.getName() + '...')
        self.neutral.enter(startTrack=self.neutralStartTrack, playRate=0.5)
        self.acceptOnce(self.neutralDoneEvent, self.__decideNextState)

    def exitNeutral(self):
        self.ignore(self.neutralDoneEvent)
        self.neutral.exit()

    def enterWalk(self):
        self.notify.debug('Walking ' + self.getName() + '...')
        self.walk.enter(startTrack=self.walkStartTrack)
        self.acceptOnce(self.walkDoneEvent, self.__decideNextState)

    def exitWalk(self):
        self.ignore(self.walkDoneEvent)
        self.walk.exit()

    def __decideNextState(self, doneStatus):
        self.fsm.request('Neutral')

    def setWalk(self, srcNode, destNode, timestamp):
        if destNode and not destNode == srcNode:
            self.walk.setWalk(srcNode, destNode, timestamp)
            self.fsm.request('Walk')

    def walkSpeed(self):
        return ToontownGlobals.PlutoSpeed

    def handleHolidays(self):
        self.CCChatter = 0

    def getCCLocation(self):
        return 1
