from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.fsm import State
from direct.fsm.ClassicFSM import ClassicFSM
from panda3d.toontown import NametagGlobals

from toontown.hood.Place import Place
from toontown.instancedgames.InstancedGameWalk import InstancedGameWalk
from toontown.toonbase import ToontownGlobals, ClientSettings


class InstancedMinigamePlace(Place):
    notify = directNotify.newCategory('InstancedMinigamePlace')

    def __init__(self, loader, parentFSM, doneEvent):
        super().__init__(loader, doneEvent)
        self.parentFSM = parentFSM
        self.fsm = ClassicFSM(
                'InstancedMinigamePlace',
                [
                    State.State('start', self.enterStart, self.exitStart, ['final', 'teleportIn', 'walk']),
                    State.State('walk', self.enterWalk, self.exitWalk, ['final',
                                                                        'sit',
                                                                        'stopped',
                                                                        'DFA']),
                    State.State('stopped', self.enterStopped, self.exitStopped, ['walk', 'teleportOut']),
                    State.State('sit', self.enterSit, self.exitSit, ['walk']),
                    State.State('teleportIn', self.enterTeleportIn, self.exitTeleportIn, ['walk']),
                    State.State('teleportOut', self.enterTeleportOut, self.exitTeleportOut,
                                ['teleportIn', 'walk', 'final']),
                    State.State('final', self.enterFinal, self.exitFinal, ['teleportIn']),
                    State.State('stopped', self.enterStopped, self.exitStopped, ['walk']),
                    State.State('DFA', self.enterDFA, self.exitDFA, ['DFAReject', 'teleportOut']),
                    State.State('DFAReject', self.enterDFAReject, self.exitDFAReject, ['walk'])
                ], 'start', 'final'
        )
        self.spawnPointPos = (0.0, 0.0, 0.0)
        self.spawnPointH = 0

    def setPlayerSpawnPoint(self, x, y, z, h):
        self.spawnPointPos = (x, y, z)
        self.spawnPointH = h

    def enter(self, requestStatus):
        super().enter()
        self.zoneId = requestStatus['zoneId']
        base.localAvatar.book.hideButton()

    def exit(self):
        super().exit()
        if hasattr(self, 'fsm'):
            self.fsm.requestFinalState()

    def load(self):
        super().load()
        # Don't use PublicWalk
        self.walkStateData.unload()
        del self.walkStateData

        # Use InstancedWalk instead
        self.walkStateData = InstancedGameWalk(self.fsm, self.walkDoneEvent)
        self.walkStateData.load()

    def enterTeleportIn(self, nextState=''):
        base.localAvatar.setTransitioning(True)
        base.localAvatar.setPos(render, *self.spawnPointPos)
        base.localAvatar.setH(render, self.spawnPointH)
        self._tiToken = self.addSetZoneCompleteCallback(Functor(self._placeTeleportInPostZoneComplete, nextState), 100)

    def _placeTeleportInPostZoneComplete(self, nextState):
        NametagGlobals.setMasterArrowsOn(0)
        base.localAvatar.laffMeter.start()
        base.localAvatar.startQuestMap()
        base.localAvatar.reconsiderCheesyEffect()
        base.localAvatar.obscureMoveFurnitureButton(1)
        base.transitions.irisIn()
        self.nextState = nextState
        base.localAvatar.attachCamera()
        base.localAvatar.activateCamera()
        base.localAvatar.startPosHprBroadcast(period = ClientSettings.PositionSendRate.get())
        globalClock.tick()
        base.localAvatar.b_setAnimState('TeleportIn', 1, callback=self.teleportInDone)
        base.localAvatar.d_broadcastPositionNow()
        base.localAvatar.b_setParent(ToontownGlobals.SPRender)

    def teleportInDone(self):
        base.localAvatar.b_setAnimState('neutral')
        if self.nextState and hasattr(self, 'fsm'):
            self.fsm.request(self.nextState, [1])
