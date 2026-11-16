from direct.interval.LerpInterval import LerpHprInterval
from direct.interval.MetaInterval import Sequence
from panda3d.core import PolylightEffect, NodePath, PolylightNode, Vec4, VBase4, Vec3

from toontown.mainmenu.MainMenuZone import MainMenuZone
from toontown.toonbase import ToontownGlobals
from toontown.hood import SkyUtil


class MainMenuZoneMM(MainMenuZone):
    zone = 'MM'  # type: str
    storages = [
        'phase_6/dna/ttrm_d_strg_mml.dna',
        'phase_6/dna/ttrm_d_strg_mml_sz.dna',
        'phase_6/dna/ttrm_d_strg_mml_town.dna'
    ]  # type: list[str]
    skyModel = 'phase_6/models/props/MM_sky'  # type: str
    if loader.loadingScreen.getActiveHoliday() == ToontownGlobals.HolidayHalloween:
        storages.append('phase_6/dna/ttrm_d_strg_mml_halloween.dna')
        storages.append('phase_6/dna/ttrm_d_strg_mml_sz_halloween.dna')
        skyModel = 'phase_14.5/models/props/halloween-skybox'
    if loader.loadingScreen.getActiveHoliday() == ToontownGlobals.HolidayWinter:
        storages.append('phase_6/dna/ttrm_d_strg_mml_winter.dna')
        skyModel = 'phase_3.5/models/props/BR_sky'
    billboardColor = VBase4(0.21, 0.73, 0.31, 1.0)
    billboardPos = (
        Vec3(29.5097, 129.512, 14),
        Vec3(-15, 0, 0),
        Vec3(1.88969)
    )
    char = {
        ToontownGlobals.HolidayNormal:     'mn',
        ToontownGlobals.HolidayHalloween:  'wmn',
        ToontownGlobals.HolidayWinter:     'mn',
        ToontownGlobals.HolidayAprilFools: 'mn'
    }

    def __init__(self):
        MainMenuZone.__init__(self)
        horn = self.geom.find('**/prop.horn_DNARoot')
        self.hornRotInterval = LerpHprInterval(horn, duration = 12, startHpr = Vec3(0), hpr = Vec3(360, 0, 0))
        self.hornRotInterval.loop()

    def unload(self):
        self.hornRotInterval.finish()
        super().unload()

    def setupToonAnimation(self):  # type: () -> Sequence
        pass

    def startCloudSky(self):
        return SkyUtil.startSingleCloudSky(self)

    def skyTrackSingle(self, task):
        return SkyUtil.singleCloudSkyTrack(task)