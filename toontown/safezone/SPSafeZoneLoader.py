from direct.fsm import State

from toontown.building import SuitInterior
from toontown.cogdominium import CogdoInterior
from toontown.distributed import HoodMgr
from toontown.suit import Suit

from . import SafeZoneLoader
from . import SPPlayground


class SPSafeZoneLoader(SafeZoneLoader.SafeZoneLoader):

    def __init__(self, hood, parentFSM, doneEvent):
        SafeZoneLoader.SafeZoneLoader.__init__(self, hood, parentFSM, doneEvent)

        self.playgroundClass = SPPlayground.SPPlayground

        self.musicFile = 'phase_14.5/audio/bgm/SP_nbrhood_tt.ogg'
        self.activityMusicFile = 'phase_14.5/audio/bgm/SP_SZ_activity.ogg'

        self.battleMusicFile = 'phase_4/audio/bgm/TC_battle.ogg'

        self.dnaFile = 'phase_14.5/dna/ttrm_d_ara_sph_sz.dna'
        self.safeZoneStorageDNAFile = ('phase_4/dna/ttrm_d_strg_ttc_sz.dna',
                                       'phase_14.5/dna/storage_SP_sz.dna')

        self.fsm.addState(State.State('suitInterior', self.enterSuitInterior, self.exitSuitInterior, ['quietZone']))
        self.fsm.addState(State.State('cogdoInterior', self.enterCogdoInterior, self.exitCogdoInterior, ['quietZone']))

        stateNames = ('quietZone',)
        for stateName in stateNames:
            state = self.fsm.getStateNamed(stateName)
            state.addTransition('suitInterior')
            state.addTransition('cogdoInterior')

    def load(self):
        SafeZoneLoader.SafeZoneLoader.load(self)
        Suit.loadSuits()
        self.reparentLandmarkBlockNodes()

    def unload(self):
        SafeZoneLoader.SafeZoneLoader.unload(self)
        Suit.unloadSuits()
        self.landmarkBlocks.removeNode()
        del self.landmarkBlocks

    def reparentLandmarkBlockNodes(self):
        bucket = self.landmarkBlocks = hidden.attachNewNode('landmarkBlocks')
        npc = self.geom.findAllMatches('**/sb*:*_landmark_*_DNARoot')
        for i in range(npc.getNumPaths()):
            nodePath = npc.getPath(i)
            nodePath.wrtReparentTo(bucket)

    def enterSuitInterior(self, requestStatus = None):
        self.placeDoneEvent = 'suit-interior-done'
        self.acceptOnce(self.placeDoneEvent, self.handleSuitInteriorDone)
        self.place = SuitInterior.SuitInterior(self, self.fsm, self.placeDoneEvent)
        self.place.load()
        self.place.enter(requestStatus)
        base.cr.playGame.setPlace(self.place)

    def exitSuitInterior(self):
        self.ignore(self.placeDoneEvent)
        #del self.placeDoneEvent
        self.place.exit()
        self.place.unload()
        self.place = None
        base.cr.playGame.setPlace(self.place)
        return

    def handleSuitInteriorDone(self):
        doneStatus = self.place.getDoneStatus()
        if base.cr.playGame.hood.isSameHood(doneStatus):
            self.fsm.request('quietZone', [doneStatus])
        else:
            self.doneStatus = doneStatus
            messenger.send(self.doneEvent)

    def enterCogdoInterior(self, requestStatus = None):
        self.placeDoneEvent = 'cogdo-interior-done'
        self.acceptOnce(self.placeDoneEvent, self.handleCogdoInteriorDone)
        self.place = CogdoInterior.CogdoInterior(self, self.fsm, self.placeDoneEvent)
        self.place.load()
        self.place.enter(requestStatus)
        base.cr.playGame.setPlace(self.place)

    def exitCogdoInterior(self):
        self.ignore(self.placeDoneEvent)
        #del self.placeDoneEvent
        self.place.exit()
        self.place.unload()
        self.place = None
        base.cr.playGame.setPlace(self.place)
        return

    def handleCogdoInteriorDone(self):
        doneStatus = self.place.getDoneStatus()
        if base.cr.playGame.hood.isSameHood(doneStatus):
            self.fsm.request('quietZone', [doneStatus])
        else:
            self.doneStatus = doneStatus
            messenger.send(self.doneEvent)
