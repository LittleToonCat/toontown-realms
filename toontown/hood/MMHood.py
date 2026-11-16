from panda3d.core import *
from . import ToonHood
from toontown.town import MMTownLoader
from toontown.safezone import MMSafeZoneLoader
from toontown.toonbase.ToontownGlobals import *
from . import SkyUtil

class MMHood(ToonHood.ToonHood):

    def __init__(self, parentFSM, doneEvent, dnaStore, hoodId):
        ToonHood.ToonHood.__init__(self, parentFSM, doneEvent, dnaStore, hoodId)
        self.id = MinniesMelodyland
        self.townLoaderClass = MMTownLoader.MMTownLoader
        self.safeZoneLoaderClass = MMSafeZoneLoader.MMSafeZoneLoader
        self.storageDNAFile = 'phase_6/dna/ttrm_d_strg_mml.dna'
        self.holidayStorageDNADict = {WINTER_DECORATIONS: ['phase_6/dna/ttrm_d_strg_mml_winter.dna'],
         WACKY_WINTER_DECORATIONS: ['phase_6/dna/ttrm_d_strg_mml_winter.dna'],
         HALLOWEEN_PROPS: ['phase_6/dna/ttrm_d_strg_mml_halloween.dna'],
         SPOOKY_PROPS: ['phase_6/dna/ttrm_d_strg_mml_halloween.dna']}
        self.skyFile = 'phase_6/models/props/MM_sky'
        self.spookySkyFile = 'phase_14.5/models/props/halloween-skybox'
        self.titleColor = (1.0, 0.5, 0.5, 1.0)

    def load(self):
        ToonHood.ToonHood.load(self)
        self.parentFSM.getStateNamed('MMHood').addChild(self.fsm)

    def unload(self):
        self.parentFSM.getStateNamed('MMHood').removeChild(self.fsm)
        ToonHood.ToonHood.unload(self)

    def enter(self, *args):
        ToonHood.ToonHood.enter(self, *args)

    def exit(self):
        ToonHood.ToonHood.exit(self)

    def skyTrackSingle(self, task):
        return SkyUtil.singleCloudSkyTrack(task)

    def startSky(self):
        self.sky.setTransparency(TransparencyAttrib.MDual, 1)
        self.notify.debug('The sky is: %s' % self.sky)
        if not self.sky.getTag('sky') == 'Regular':
            self.endSpookySky()
        SkyUtil.startSingleCloudSky(self)
