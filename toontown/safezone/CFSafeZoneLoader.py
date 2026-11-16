from direct.fsm import State
from direct.fsm.ClassicFSM import ClassicFSM

from . import CFPlayground
from . import SafeZoneLoader
from ..hood.Place import Place
from ..instancedgames import InstancedMinigamePlace
from ..instancedgames.DistributedPropHuntGame import DistributedPropHuntGame
from ..toonbase import ToontownGlobals


class CFSafeZoneLoader(SafeZoneLoader.SafeZoneLoader):

    def __init__(self, hood, parentFSM, doneEvent):
        SafeZoneLoader.SafeZoneLoader.__init__(self, hood, parentFSM, doneEvent)

        self.playgroundClass = CFPlayground.CFPlayground

        self.musicFile = 'phase_14.5/audio/bgm/SP_SZ_activity.ogg'
        self.activityMusicFile = 'phase_14.5/audio/bgm/SP_SZ_activity.ogg'

        self.dnaFile = 'phase_14.5/dna/ttrm_d_ara_crf_sz.dna'
        self.safeZoneStorageDNAFile = ('phase_14.5/dna/ttrm_d_strg_crf.dna', 'phase_4/dna/ttrm_d_strg_ttc.dna',
                                       'phase_4/dna/ttrm_d_strg_ttc_sz.dna', 'phase_5/dna/ttrm_d_strg_ttc_town.dna')

        self.fsm = ClassicFSM(
                'SafeZoneLoader',
                [
                    State.State('start', self.enterStart, self.exitStart,
                                ['quietZone', 'playground', 'toonInterior', 'propHuntGame']),
                    State.State('playground', self.enterPlayground, self.exitPlayground, ['quietZone', 'propHuntGame']),
                    State.State('toonInterior', self.enterToonInterior, self.exitToonInterior, ['quietZone']),
                    State.State('quietZone', self.enterQuietZone, self.exitQuietZone,
                                ['playground', 'toonInterior', 'propHuntGame']),
                    State.State('propHuntGame', self.enterPropHuntGame, self.exitPropHuntGame,
                                ['quietZone', 'playground']),
                    State.State('final', self.enterFinal, self.exitFinal, ['start'])
                ], 'start', 'final')

    def load(self):
        SafeZoneLoader.SafeZoneLoader.load(self)

    def unload(self):
        SafeZoneLoader.SafeZoneLoader.unload(self)

    def enterPlace(self, requestStatus):
        self.acceptOnce(self.placeDoneEvent, self.placeDone)
        self.place = self.placeClass(self, self.fsm, self.placeDoneEvent)
        base.cr.playGame.setPlace(self.place)
        self.place.load()
        self.place.enter(requestStatus)

    def exitPlace(self):
        self.ignore(self.placeDoneEvent)
        self.place.exit()
        self.place.unload()
        self.place = None
        base.cr.playGame.setPlace(self.place)

    def enterPropHuntGame(self, requestStatus):
        self.placeClass = InstancedMinigamePlace.InstancedMinigamePlace
        self.enterPlace(requestStatus)
        base.transitions.irisIn(t = 0.2)

    def exitPropHuntGame(self):
        self.exitPlace()
        return

    def placeDone(self):
        self.requestStatus = self.place.doneStatus
        status = self.place.doneStatus
        if status.get('shardId') == None:
            zoneId = status['zoneId']
            self.fsm.request('quietZone', [status])
        else:
            self.doneStatus = status
            messenger.send(self.doneEvent)
