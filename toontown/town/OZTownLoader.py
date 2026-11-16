from . import TownLoader
from . import OZStreet
from toontown.suit import Suit

class OZTownLoader(TownLoader.TownLoader):

    def __init__(self, hood, parentFSM, doneEvent):
        TownLoader.TownLoader.__init__(self, hood, parentFSM, doneEvent)
        self.streetClass = OZStreet.OZStreet
        self.musicFile = 'phase_6/audio/bgm/OZ_nbrhood.ogg'
        self.activityMusicFile = 'phase_6/audio/bgm/OZ_nbrhood.ogg'
        self.battleMusicFile = 'phase_4/audio/bgm/TC_battle.ogg'
        self.townStorageDNAFile = 'phase_6/dna/ttrm_d_strg_cda_town.dna'

    def load(self, zoneId):
        TownLoader.TownLoader.load(self, zoneId)
        Suit.loadSuits()
        dnaFile = 'phase_6/dna/ttrm_d_ara_cda_' + str(self.canonicalBranchZone) + '.dna'
        self.createHood(dnaFile)

    def unload(self):
        Suit.unloadSuits()
        TownLoader.TownLoader.unload(self)
