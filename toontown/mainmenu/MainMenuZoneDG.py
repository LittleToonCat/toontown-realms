from direct.interval.MetaInterval import Sequence
from panda3d.core import PolylightEffect, NodePath, PolylightNode, Vec4, VBase4

from toontown.mainmenu.MainMenuZone import MainMenuZone
from toontown.toonbase import ToontownGlobals


class MainMenuZoneDG(MainMenuZone):
    zone = 'DG'  # type: str
    storages = [
        'phase_8/dna/ttrm_d_strg_dga.dna',
        'phase_8/dna/ttrm_d_strg_dga_sz.dna',
        'phase_8/dna/ttrm_d_strg_dga_town.dna'
    ]  # type: list[str]
    skyModel = 'phase_3.5/models/props/TT_sky'  # type: str
    if loader.loadingScreen.getActiveHoliday() == ToontownGlobals.HolidayHalloween:
        storages.append('phase_8/dna/ttrm_d_strg_dga_halloween.dna')
        storages.append('phase_8/dna/ttrm_d_strg_dga_sz_halloween.dna')
        skyModel = 'phase_14.5/models/props/halloween-skybox'
    if loader.loadingScreen.getActiveHoliday() == ToontownGlobals.HolidayWinter:
        storages.append('phase_8/dna/ttrm_d_strg_dga_winter.dna')
        skyModel = 'phase_3.5/models/props/BR_sky'
    billboardColor = VBase4(0.0, 0.9, 0.7, 1.0)
    char = {
        ToontownGlobals.HolidayNormal:     'dd',
        ToontownGlobals.HolidayHalloween:  'shdd',
        ToontownGlobals.HolidayWinter:     'dd',
        ToontownGlobals.HolidayAprilFools: 'dd'
    }

    def __init__(self):
        MainMenuZone.__init__(self)

    def setupToonAnimation(self):  # type: () -> Sequence
        pass
