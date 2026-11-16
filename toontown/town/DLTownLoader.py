from . import TownLoader
from . import DLStreet
from toontown.hood import ZoneUtil
from toontown.toonbase import ToontownGlobals
from toontown.suit import Suit
import random

class DLTownLoader(TownLoader.TownLoader):

    def __init__(self, hood, parentFSM, doneEvent):
        TownLoader.TownLoader.__init__(self, hood, parentFSM, doneEvent)
        self.streetClass = DLStreet.DLStreet
        self.townStorageDNAFile = 'phase_8/dna/ttrm_d_strg_ddl_town.dna'

    def load(self, zoneId):
        canonicalZoneId = ZoneUtil.getCanonicalBranchZone(zoneId)
        if canonicalZoneId == ToontownGlobals.DreamyDriveOutcove:
            self.musicFile = f'phase_8/audio/bgm/ttrm_s_ara_bgm_ddlo_nbrhood_{random.randint(1, 3)}.ogg'
            self.activityMusicFile = 'phase_8/audio/bgm/ttrm_s_ara_bgm_ddlo_interior.ogg'
        elif canonicalZoneId == ToontownGlobals.DreamyDrive:
            self.musicFile = 'phase_8/audio/bgm/ttrm_s_ara_bgm_ddlo_street.ogg'
            self.activityMusicFile = 'phase_8/audio/bgm/ttrm_s_ara_bgm_ddlo_interior.ogg'
            self.battleMusicFile = 'phase_8/audio/bgm/ttrm_s_ara_bgm_ddlo_battle.ogg'
        else:
            self.musicFile = 'phase_8/audio/bgm/DL_SZ.ogg'
            self.activityMusicFile = 'phase_8/audio/bgm/DL_SZ_activity.ogg'

        TownLoader.TownLoader.load(self, zoneId)
        Suit.loadSuits()
        dnaFile = 'phase_8/dna/ttrm_d_ara_ddl_' + str(self.canonicalBranchZone) + '.dna'
        self.createHood(dnaFile)

    def unload(self):
        Suit.unloadSuits()
        TownLoader.TownLoader.unload(self)
