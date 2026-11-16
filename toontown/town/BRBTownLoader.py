from . import TownLoader
from . import BRBStreet
from toontown.suit import Suit

class BRBTownLoader(TownLoader.TownLoader):

    def __init__(self, hood, parentFSM, doneEvent):
        TownLoader.TownLoader.__init__(self, hood, parentFSM, doneEvent)
        self.streetClass = BRBStreet.BRBStreet
        self.musicFile = 'phase_8/audio/bgm/TB_SZ.ogg'
        self.activityMusicFile = 'phase_8/audio/bgm/TB_SZ_activity.ogg'
        self.battleMusicFile = 'phase_8/audio/bgm/TB_battle.ogg'
        self.townStorageDNAFile = 'phase_8/dna/ttrm_d_strg_br_town.dna'

    def load(self, zoneId):
        TownLoader.TownLoader.load(self, zoneId)
        Suit.loadSuits()
        dnaFile = 'phase_14.5/dna/ttrm_d_ara_brb_' + str(self.canonicalBranchZone) + '.dna'
        self.createHood(dnaFile)

    def unload(self):
        Suit.unloadSuits()
        TownLoader.TownLoader.unload(self)
