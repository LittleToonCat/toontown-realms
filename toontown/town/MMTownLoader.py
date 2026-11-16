from . import TownLoader
from . import MMStreet
from toontown.suit import Suit

class MMTownLoader(TownLoader.TownLoader):

    def __init__(self, hood, parentFSM, doneEvent):
        TownLoader.TownLoader.__init__(self, hood, parentFSM, doneEvent)
        self.streetClass = MMStreet.MMStreet
        self.musicFile = 'phase_6/audio/bgm/MM_SZ.ogg'
        self.activityMusicFile = 'phase_6/audio/bgm/MM_SZ_activity.ogg'
        self.battleMusicFile = 'phase_6/audio/bgm/MM_battle.ogg'
        self.townStorageDNAFile = 'phase_6/dna/ttrm_d_strg_mml_town.dna'

    def load(self, zoneId):
        TownLoader.TownLoader.load(self, zoneId)
        Suit.loadSuits()
        dnaFile = 'phase_6/dna/ttrm_d_ara_mml_' + str(self.canonicalBranchZone) + '.dna'
        self.createHood(dnaFile)

    def unload(self):
        Suit.unloadSuits()
        TownLoader.TownLoader.unload(self)
