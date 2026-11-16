from panda3d.core import *
from . import SafeZoneLoader
from . import DLPlayground
from toontown.toonbase import ToontownGlobals


class DLSafeZoneLoader(SafeZoneLoader.SafeZoneLoader):

    def __init__(self, hood, parentFSM, doneEvent):
        SafeZoneLoader.SafeZoneLoader.__init__(self, hood, parentFSM, doneEvent)
        self.playgroundClass = DLPlayground.DLPlayground
        self.activityMusicFile = 'phase_8/audio/bgm/DL_SZ_activity.ogg'
        if base.cr.newsManager.isHolidayRunning(ToontownGlobals.HALLOWEEN_PROPS):
            self.dnaFile = 'phase_8/dna/ttrm_d_ara_ddl_sz_halloween.dna'
            self.musicFile = 'phase_8/audio/bgm/ttoff_s_ara_ddl_nbrhood_halloween.ogg'
        else:
            self.dnaFile = 'phase_8/dna/ttrm_d_ara_ddl_sz.dna'
            self.musicFile = 'phase_8/audio/bgm/DL_nbrhood.ogg'
        self.safeZoneStorageDNAFile = 'phase_8/dna/ttrm_d_strg_ddl_sz.dna'
