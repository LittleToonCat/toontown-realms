from direct.interval.MetaInterval import Sequence
from panda3d.core import PolylightEffect, NodePath, PolylightNode, Vec4, VBase4

from toontown.mainmenu.MainMenuZone import MainMenuZone
from toontown.toonbase import ToontownGlobals
from toontown.hood import SkyUtil


class MainMenuZoneBR(MainMenuZone):
    zone = 'BR'  # type: str
    storages = [
        'phase_8/dna/ttrm_d_strg_tbr.dna',
        'phase_8/dna/ttrm_d_strg_tbr_sz.dna',
        'phase_8/dna/ttrm_d_strg_tbr_town.dna'
    ]  # type: list[str]
    skyModel = 'phase_3.5/models/props/BR_sky'  # type: str
    if loader.loadingScreen.getActiveHoliday() == ToontownGlobals.HolidayHalloween:
        storages.append('phase_8/dna/ttrm_d_strg_tbr_halloween.dna')
        storages.append('phase_8/dna/ttrm_d_strg_tbr_sz_halloween.dna')
        skyModel = 'phase_14.5/models/props/halloween-skybox'
    if loader.loadingScreen.getActiveHoliday() == ToontownGlobals.HolidayWinter:
        storages.append('phase_8/dna/ttrm_d_strg_tbr_winter.dna')
    billboardColor = VBase4(0.0, 0.85, 1.0, 1.0)
    char = {
        ToontownGlobals.HolidayNormal:     'p',
        ToontownGlobals.HolidayHalloween:  'wp',
        ToontownGlobals.HolidayWinter:     'p',
        ToontownGlobals.HolidayAprilFools: 'p'
    }

    def setupToonAnimation(self):  # type: () -> Sequence
        pass

    def startCloudSky(self):
        return SkyUtil.startNoCloudSky(self)

    def skyTrackNoClouds(self, task):
        return SkyUtil.noCloudSkyTrack(task)