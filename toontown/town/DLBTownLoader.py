from . import TownLoader
from . import DLBStreet
from toontown.suit import Suit

class DLBTownLoader(TownLoader.TownLoader):

    def __init__(self, hood, parentFSM, doneEvent):
        TownLoader.TownLoader.__init__(self, hood, parentFSM, doneEvent)
        self.streetClass = DLBStreet.DLBStreet
        self.musicFile = 'phase_8/audio/bgm/DL_SZ.ogg'
        self.activityMusicFile = 'phase_8/audio/bgm/DL_SZ_activity.ogg'
        self.battleMusicFile = 'phase_8/audio/bgm/DL_battle.ogg'
        self.townStorageDNAFile = 'phase_8/dna/ttrm_d_strg_ddl_town.dna'

    def load(self, zoneId):
        TownLoader.TownLoader.load(self, zoneId)
        Suit.loadSuits()
        dnaFile = 'phase_8/dna/ttrm_d_ara_ddlb_' + str(self.canonicalBranchZone) + '.dna'
        self.createHood(dnaFile)

    def unload(self):
        Suit.unloadSuits()
        TownLoader.TownLoader.unload(self)
