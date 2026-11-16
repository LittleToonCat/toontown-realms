from . import SafeZoneLoader
from . import MMPlayground
from ..toonbase import ToontownGlobals


class MMSafeZoneLoader(SafeZoneLoader.SafeZoneLoader):

    def __init__(self, hood, parentFSM, doneEvent):
        SafeZoneLoader.SafeZoneLoader.__init__(self, hood, parentFSM, doneEvent)
        self.playgroundClass = MMPlayground.MMPlayground
        if base.cr.newsManager.isHolidayRunning(ToontownGlobals.HALLOWEEN_PROPS):
            self.musicFile = 'phase_6/audio/bgm/ttoff_s_ara_mml_nbrhood_halloween.ogg'
        else:
            self.musicFile = 'phase_6/audio/bgm/MM_nbrhood.ogg'
        self.activityMusicFile = 'phase_6/audio/bgm/MM_SZ_activity.ogg'
        if base.cr.newsManager.isHolidayRunning(ToontownGlobals.HALLOWEEN_PROPS):
            self.dnaFile = 'phase_6/dna/ttrm_d_ara_mml_sz_halloween.dna'
        else:
            self.dnaFile = 'phase_6/dna/ttrm_d_ara_mml_sz.dna'
        self.safeZoneStorageDNAFile = 'phase_6/dna/ttrm_d_strg_mml_sz.dna'

    def load(self):
        SafeZoneLoader.SafeZoneLoader.load(self)
        self.piano = self.geom.find('**/g54')
        if not self.piano.isEmpty():
            hq = self.geom.find('**/*toon_landmark_hqMM_DNARoot')
            hq.wrtReparentTo(self.piano)

    def unload(self):
        SafeZoneLoader.SafeZoneLoader.unload(self)
        del self.piano
