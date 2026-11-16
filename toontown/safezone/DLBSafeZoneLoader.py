from panda3d.core import *
from . import SafeZoneLoader
from . import DLBPlayground

class DLBSafeZoneLoader(SafeZoneLoader.SafeZoneLoader):

    def __init__(self, hood, parentFSM, doneEvent):
        SafeZoneLoader.SafeZoneLoader.__init__(self, hood, parentFSM, doneEvent)
        self.playgroundClass = DLBPlayground.DLBPlayground
        self.musicFile = 'phase_8/audio/bgm/DL_nbrhood.ogg'
        self.activityMusicFile = 'phase_8/audio/bgm/DL_SZ_activity.ogg'
        self.dnaFile = 'phase_14.5/dna/ttrm_d_ara_ddlb_sz.dna'
        self.safeZoneStorageDNAFile = 'phase_8/dna/ttrm_d_strg_ddl_sz.dna'
