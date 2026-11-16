from panda3d.core import *
from . import SafeZoneLoader
from . import DGPlayground
from ..toonbase import ToontownGlobals


class DGSafeZoneLoader(SafeZoneLoader.SafeZoneLoader):

    def __init__(self, hood, parentFSM, doneEvent):
        SafeZoneLoader.SafeZoneLoader.__init__(self, hood, parentFSM, doneEvent)
        self.playgroundClass = DGPlayground.DGPlayground
        self.activityMusicFile = 'phase_8/audio/bgm/DG_SZ.ogg'
        if base.cr.newsManager.isHolidayRunning(ToontownGlobals.HALLOWEEN_PROPS):
            self.dnaFile = 'phase_8/dna/ttrm_d_ara_dga_sz_halloween.dna'
            self.musicFile = 'phase_8/audio/bgm/ttoff_s_ara_dga_nbrhood_halloween.ogg'
        else:
            self.dnaFile = 'phase_8/dna/ttrm_d_ara_dga_sz.dna'
            self.musicFile = 'phase_8/audio/bgm/DG_nbrhood.ogg'
        self.safeZoneStorageDNAFile = 'phase_8/dna/ttrm_d_strg_dga_sz.dna'

    def load(self):
        SafeZoneLoader.SafeZoneLoader.load(self)
        self.bird1Sound = base.loader.loadSfx('phase_8/audio/sfx/SZ_DG_bird_01.ogg', manager = 'environment')
        self.bird2Sound = base.loader.loadSfx('phase_8/audio/sfx/SZ_DG_bird_02.ogg', manager = 'environment')
        self.bird3Sound = base.loader.loadSfx('phase_8/audio/sfx/SZ_DG_bird_03.ogg', manager = 'environment')
        self.bird4Sound = base.loader.loadSfx('phase_8/audio/sfx/SZ_DG_bird_04.ogg', manager = 'environment')

    def unload(self):
        SafeZoneLoader.SafeZoneLoader.unload(self)
        del self.bird1Sound
        del self.bird2Sound
        del self.bird3Sound
        del self.bird4Sound

    def enter(self, requestStatus):
        SafeZoneLoader.SafeZoneLoader.enter(self, requestStatus)

    def exit(self):
        SafeZoneLoader.SafeZoneLoader.exit(self)
