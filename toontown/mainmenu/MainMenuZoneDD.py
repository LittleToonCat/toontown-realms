from direct.interval.MetaInterval import Sequence
from panda3d.core import PolylightEffect, NodePath, PolylightNode, Vec4, VBase4, Fog

from toontown.mainmenu.MainMenuZone import MainMenuZone
from toontown.toonbase import ToontownGlobals
from toontown.hood import SkyUtil


class MainMenuZoneDD(MainMenuZone):
    zone = 'DD'  # type: str
    storages = [
        'phase_6/dna/ttrm_d_strg_dod.dna',
        'phase_6/dna/ttrm_d_strg_dod_sz.dna',
        'phase_6/dna/ttrm_d_strg_dod_town.dna'
    ]  # type: list[str]
    skyModel = 'phase_3.5/models/props/BR_sky'  # type: str
    if loader.loadingScreen.getActiveHoliday() == ToontownGlobals.HolidayHalloween:
        storages.append('phase_6/dna/ttrm_d_strg_dod_halloween.dna')
        storages.append('phase_6/dna/ttrm_d_strg_dod_sz_halloween.dna')
        skyModel = 'phase_14.5/models/props/halloween-skybox'
    if loader.loadingScreen.getActiveHoliday() == ToontownGlobals.HolidayWinter:
        storages.append('phase_6/dna/ttrm_d_strg_dod_winter.dna')
        skyModel = 'phase_3.5/models/props/BR_sky'
    billboardColor = VBase4(0.65, 0.2, 0.15, 1.0)
    char = {
        ToontownGlobals.HolidayNormal:     'ddl',
        ToontownGlobals.HolidayHalloween:  'ddl',
        ToontownGlobals.HolidayWinter:     'ddl',
        ToontownGlobals.HolidayAprilFools: 'ddl'
    }

    def __init__(self):
        MainMenuZone.__init__(self)
        self.fog = Fog('DODMainMenuFov')
        self.fog.setColor(Vec4(0.8, 0.8, 0.8, 1))
        self.fog.setLinearRange(0.0, 600)
        self.geom.setFog(self.fog)
        self.sky.setFog(self.fog)

    def setupToonAnimation(self):  # type: () -> Sequence
        pass

    def startCloudSky(self):
        return SkyUtil.startNoCloudSky(self)

    def skyTrackNoClouds(self, task):
        return SkyUtil.noCloudSkyTrack(task)