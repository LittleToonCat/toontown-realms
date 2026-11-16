from panda3d.core import *
from . import SafeZoneLoader
from . import TTBPlayground

class TTBSafeZoneLoader(SafeZoneLoader.SafeZoneLoader):

    def __init__(self, hood, parentFSM, doneEvent):
        SafeZoneLoader.SafeZoneLoader.__init__(self, hood, parentFSM, doneEvent)
        self.playgroundClass = TTBPlayground.TTBPlayground
        self.musicFile = 'phase_4/audio/bgm/TC_nbrhood.ogg'
        self.activityMusicFile = 'phase_3.5/audio/bgm/TC_SZ_activity.ogg'
        self.dnaFile = 'phase_14.5/dna/ttrm_d_ara_ttcb_sz.dna'
        self.safeZoneStorageDNAFile = 'phase_4/dna/ttrm_d_strg_ttc_sz.dna'
