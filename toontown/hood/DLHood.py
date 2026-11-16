from panda3d.core import *
from . import ToonHood
from toontown.town import DLTownLoader
from toontown.safezone import DLSafeZoneLoader
from toontown.toonbase.ToontownGlobals import *
from . import SkyUtil

class DLHood(ToonHood.ToonHood):

    def __init__(self, parentFSM, doneEvent, dnaStore, hoodId):
        ToonHood.ToonHood.__init__(self, parentFSM, doneEvent, dnaStore, hoodId)
        self.id = DonaldsDreamland
        self.townLoaderClass = DLTownLoader.DLTownLoader
        self.safeZoneLoaderClass = DLSafeZoneLoader.DLSafeZoneLoader
        self.storageDNAFile = 'phase_8/dna/ttrm_d_strg_ddl.dna'
        self.holidayStorageDNADict = {WINTER_DECORATIONS: ['phase_8/dna/ttrm_d_strg_ddl_winter.dna'],
         WACKY_WINTER_DECORATIONS: ['phase_8/dna/ttrm_d_strg_ddl_winter.dna'],
         HALLOWEEN_PROPS: ['phase_8/dna/ttrm_d_strg_ddl_halloween.dna'],
         SPOOKY_PROPS: ['phase_8/dna/ttrm_d_strg_ddl_halloween.dna']}
        self.skyFile = 'phase_8/models/props/DL_sky'
        #self.skyFile = 'phase_8/models/props/ttoff_m_ara_DL_skyDawn'
        self.titleColor = (1.0, 0.9, 0.5, 1.0)

    def load(self):
        ToonHood.ToonHood.load(self)
        self.parentFSM.getStateNamed('DLHood').addChild(self.fsm)

    def unload(self):
        self.parentFSM.getStateNamed('DLHood').removeChild(self.fsm)
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
