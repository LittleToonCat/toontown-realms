from panda3d.core import *
from . import SafeZoneLoader
from . import TTPlayground
import random
from toontown.launcher import DownloadForceAcknowledge
from toontown.toonbase import ToontownGlobals

class TTSafeZoneLoader(SafeZoneLoader.SafeZoneLoader):

    def __init__(self, hood, parentFSM, doneEvent):
        SafeZoneLoader.SafeZoneLoader.__init__(self, hood, parentFSM, doneEvent)
        self.playgroundClass = TTPlayground.TTPlayground
        if base.cr.newsManager.isHolidayRunning(ToontownGlobals.HALLOWEEN_PROPS):
            self.musicFile = 'phase_4/audio/bgm/ttoff_s_ara_ttc_nbrhood_halloween.ogg'
        elif base.cr.newsManager.isHolidayRunning(ToontownGlobals.WINTER_DECORATIONS):
            self.musicFile = 'phase_4/audio/bgm/ttoff_s_ara_ttc_nbrhood_winter.ogg'
        else:
            self.musicFile = 'phase_4/audio/bgm/TC_nbrhood.ogg'
        self.activityMusicFile = 'phase_3.5/audio/bgm/TC_SZ_activity.ogg'
        if base.cr.newsManager.isHolidayRunning(ToontownGlobals.HALLOWEEN_PROPS):
            self.dnaFile = 'phase_4/dna/ttrm_d_ara_ttc_sz_halloween.dna'
        else:
            self.dnaFile = 'phase_4/dna/ttrm_d_ara_ttc_sz.dna'
        self.safeZoneStorageDNAFile = 'phase_4/dna/ttrm_d_strg_ttc_sz.dna'

    def load(self):
        SafeZoneLoader.SafeZoneLoader.load(self)
        if base.cr.newsManager.isHolidayRunning(ToontownGlobals.HALLOWEEN_PROPS):
            self.birdSound = list(map(base.loader.loadSfx, ['phase_4/audio/sfx/MG_sfx_vine_game_bat_flying_lp.ogg', 'phase_4/audio/sfx/MG_sfx_vine_game_bat_shriek_3.ogg']))
        else:
            self.birdSound = list(map(base.loader.loadSfx, ['phase_4/audio/sfx/SZ_TC_bird1.ogg', 'phase_4/audio/sfx/SZ_TC_bird2.ogg', 'phase_4/audio/sfx/SZ_TC_bird3.ogg'],
                                      ['environment']))

    def unload(self):
        del self.birdSound
        SafeZoneLoader.SafeZoneLoader.unload(self)

    def enter(self, requestStatus):
        SafeZoneLoader.SafeZoneLoader.enter(self, requestStatus)

    def exit(self):
        SafeZoneLoader.SafeZoneLoader.exit(self)
