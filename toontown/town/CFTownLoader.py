from . import CFStreet
from . import TownLoader


class CFTownLoader(TownLoader.TownLoader):

    def __init__(self, hood, parentFSM, doneEvent):
        TownLoader.TownLoader.__init__(self, hood, parentFSM, doneEvent)

        # Street class
        self.streetClass = CFStreet.CFStreet
        # Music paths
        self.musicFile = 'phase_14.5/audio/bgm/SP_SZ_activity.ogg'
        self.activityMusicFile = 'phase_14.5/audio/bgm/SP_SZ_activity.ogg'
        self.battleMusicFile = 'phase_4/audio/bgm/TC_battle.ogg'
        # Load the appropriate storage for this theme
        self.townStorageDNAFile = 'phase_14.5/dna/ttrm_d_strg_crf.dna'

    def load(self, zoneId):
        TownLoader.TownLoader.load(self, zoneId)
       # dnaFile = f'phase_14.5/dna/ttrm_d_ara_crf_{self.canonicalBranchZone}.dna'
       # self.createHood(dnaFile)

    def unload(self):
        TownLoader.TownLoader.unload(self)
