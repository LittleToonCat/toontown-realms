from . import SafeZoneLoader
from . import BRPlayground
from ..toonbase import ToontownGlobals


class BRSafeZoneLoader(SafeZoneLoader.SafeZoneLoader):

    def __init__(self, hood, parentFSM, doneEvent):
        SafeZoneLoader.SafeZoneLoader.__init__(self, hood, parentFSM, doneEvent)
        self.playgroundClass = BRPlayground.BRPlayground
        self.musicFile = 'phase_8/audio/bgm/TB_nbrhood.ogg'
        self.activityMusicFile = 'phase_8/audio/bgm/TB_SZ_activity.ogg'
        if base.cr.newsManager.isHolidayRunning(ToontownGlobals.HALLOWEEN_PROPS):
            self.dnaFile = 'phase_8/dna/ttrm_d_ara_tbr_sz_halloween.dna'
            self.musicFile = 'phase_8/audio/bgm/ttoff_s_ara_tbr_nbrhood_halloween.ogg'
        else:
            self.dnaFile = 'phase_8/dna/ttrm_d_ara_tbr_sz.dna'
        self.safeZoneStorageDNAFile = 'phase_8/dna/ttrm_d_strg_tbr_sz.dna'
