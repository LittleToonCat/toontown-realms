from panda3d.core import *
from . import SafeZoneLoader
from . import MMBPlayground
from toontown.toonbase import ToontownGlobals


class MMBSafeZoneLoader(SafeZoneLoader.SafeZoneLoader):

    def __init__(self, hood, parentFSM, doneEvent):
        SafeZoneLoader.SafeZoneLoader.__init__(self, hood, parentFSM, doneEvent)
        self.playgroundClass = MMBPlayground.MMBPlayground
        self.musicFile = 'phase_6/audio/bgm/MM_nbrhood.ogg'
        self.activityMusicFile = 'phase_6/audio/bgm/MM_SZ_activity.ogg'
        self.dnaFile = 'phase_14.5/dna/ttrm_d_ara_mmlb_sz.dna'
        self.safeZoneStorageDNAFile = 'phase_6/dna/ttrm_d_strg_mml_sz.dna'
