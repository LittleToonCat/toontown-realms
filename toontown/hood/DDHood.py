from panda3d.core import *
from . import ToonHood
from toontown.town import DDTownLoader
from toontown.safezone import DDSafeZoneLoader
from toontown.toonbase.ToontownGlobals import *
from toontown.toonbase import EnvironmentManager
from . import SkyUtil

BR_SKY = 'phase_3.5/models/props/BR_sky'

class DDHood(ToonHood.ToonHood):

    def __init__(self, parentFSM, doneEvent, dnaStore, hoodId):
        ToonHood.ToonHood.__init__(self, parentFSM, doneEvent, dnaStore, hoodId)
        self.id = DonaldsDock
        self.townLoaderClass = DDTownLoader.DDTownLoader
        self.safeZoneLoaderClass = DDSafeZoneLoader.DDSafeZoneLoader
        self.storageDNAFile = 'phase_6/dna/ttrm_d_strg_dod.dna'
        self.holidayStorageDNADict = {WINTER_DECORATIONS: ['phase_6/dna/ttrm_d_strg_dod_winter.dna'],
         WACKY_WINTER_DECORATIONS: ['phase_6/dna/ttrm_d_strg_dod_winter.dna'],
         HALLOWEEN_PROPS: ['phase_6/dna/ttrm_d_strg_dod_halloween.dna'],
         SPOOKY_PROPS: ['phase_6/dna/ttrm_d_strg_dod_halloween.dna']}
        self.skyFile = BR_SKY
        self.winterSkyFile = BR_SKY
        self.spookySkyFile = 'phase_14.5/models/props/halloween-skybox'
        self.titleColor = (0.8, 0.6, 0.5, 1.0)
        self.whiteFogColor = Vec4(0.8, 0.8, 0.8, 1)
        self.winterFogColor = Vec4(0.501, 0.559, 0.682, 1)
        self.underwaterFogColor = Vec4(0.0, 0.0, 0.6, 1.0)

    def load(self):
        ToonHood.ToonHood.load(self)
        self.parentFSM.getStateNamed('DDHood').addChild(self.fsm)
        self.fog = Fog('DDFog')

    def unload(self):
        self.parentFSM.getStateNamed('DDHood').removeChild(self.fsm)
        ToonHood.ToonHood.unload(self)
        self.fog = None

    def enter(self, *args):
        ToonHood.ToonHood.enter(self, *args)

    def exit(self):
        ToonHood.ToonHood.exit(self)

    def setUnderwaterFog(self):
        if base.wantFog:
            self.fog.setColor(self.underwaterFogColor)
            self.fog.setLinearRange(0.1, 100.0)
            EnvironmentManager.unloadEnvironment()
            EnvironmentManager.setDefaultFog(self.fog)
            EnvironmentManager.setActiveFog(self.fog)
            EnvironmentManager.enableEnvironment()

    def setDDFog(self):
        if base.wantFog:
            if base.cr.newsManager.isHolidayRunning(WINTER_DECORATIONS):
                self.fog.setColor(self.winterFogColor)
                self.fog.setLinearRange(0.0, 515.84)
            else:
                self.fog.setColor(self.whiteFogColor)
                self.fog.setLinearRange(0.0, 400.0)
            EnvironmentManager.unloadEnvironment()
            EnvironmentManager.setDefaultFog(self.fog)
            EnvironmentManager.setActiveFog(self.fog)
            EnvironmentManager.enableEnvironment()

    def setNoFog(self):
        if base.wantFog:
            EnvironmentManager.unloadEnvironment()

    def skyTrackNoClouds(self, task):
        return SkyUtil.noCloudSkyTrack(task)

    def startSky(self):
        self.sky.setTransparency(TransparencyAttrib.MDual, 1)
        self.notify.debug('The sky is: %s' % self.sky)
        if not self.sky.getTag('sky') == 'Regular':
            self.endSpookySky()
        SkyUtil.startNoCloudSky(self)
