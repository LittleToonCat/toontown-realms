import random

from direct.interval.FunctionInterval import Func, Wait
from direct.interval.LerpInterval import LerpPosHprInterval, LerpPosInterval
from direct.interval.MetaInterval import Sequence, Parallel
from panda3d.core import PolylightEffect, NodePath, PolylightNode, Vec4, VBase4, Vec3, Point3
from panda3d.toontown import NametagGroup

from otp.otpbase.PythonUtil import weightedChoice, blendAnimation
from toontown.avatar import ToontownAvatarUtils
from toontown.mainmenu.MainMenuZone import MainMenuZone
from toontown.makeatoon import NameGenerator
from toontown.toon.ToonDNA import ToonDNA
from toontown.toonbase import ToontownGlobals


class MainMenuZoneTT(MainMenuZone):
    zone = 'TT'  # type: str
    storages = [
        'phase_4/dna/ttrm_d_strg_ttc.dna',
        'phase_4/dna/ttrm_d_strg_ttc_sz.dna',
        'phase_5/dna/ttrm_d_strg_ttc_town.dna']  # type: list[str]
    skyModel = 'phase_3.5/models/props/TT_sky'  # type: str
    if loader.loadingScreen.getActiveHoliday() == ToontownGlobals.HolidayHalloween:
        storages.append('phase_4/dna/ttrm_d_strg_ttc_halloween.dna')
        storages.append('phase_4/dna/ttrm_d_strg_ttc_sz_halloween.dna')
        skyModel = 'phase_14.5/models/props/halloween-skybox'
    if loader.loadingScreen.getActiveHoliday() == ToontownGlobals.HolidayWinter:
        storages.append('phase_4/dna/ttrm_d_strg_ttc_winter.dna')
        storages.append('phase_4/dna/ttrm_d_strg_ttc_sz_winter.dna')
        skyModel = 'phase_3.5/models/props/BR_sky'
    billboardColor = VBase4(0.21, 0.73, 0.31, 1.0)
    billboardPos = (
        Vec3(29.5097, 129.512, 14),
        Vec3(-15, 0, 0),
        Vec3(1.88969)
    )
    char = {
        ToontownGlobals.HolidayNormal:     'mk',
        ToontownGlobals.HolidayHalloween:  'vmk',
        ToontownGlobals.HolidayWinter:     'mk',
        ToontownGlobals.HolidayAprilFools: 'mk'
    }

    def __init__(self):
        MainMenuZone.__init__(self)

    def setupToonAnimation(self):  # type: () -> Sequence
        # not ready
        return None
        path1Points = (
            Vec3(50.0, 25.0, -0.5),
            Vec3(30.0, 25.0, -0.5),
            Vec3(4.0, 25.0, -0.5),
            Vec3(-4.0, 25.0, -0.5),
            Vec3(-30.0, 25.0, -0.5),
            Vec3(-50.0, 25.0, -0.5),
        )
        namegen = NameGenerator.NameGenerator()
        for i in range(8):
            dna = ToonDNA(type = 't')
            randName = namegen.randomNameMoreinfo(boy = dna.gender == 'm', girl = dna.gender == 'f')[
                -1]
            # todo: why the hell isnt the nametag style applying?
            nametag = weightedChoice((
                (50, 100), (30, 0), (30, random.randint(1, 13)),
            ))
            toon = ToontownAvatarUtils.createUniqueToon(name = randName, dna = dna, nametagStyle = nametag,
                                                        colorType = NametagGroup.CCSpeedChat)
            toon.addActive()
            toon.hideNametag2d()
            toon.reparentTo(self.geom)
            toon.stop()
            toon.setPos(0, -10, -20)
            toon.setBlend(animBlend = True)
            toon.loop('run')
            toon.loop('neutral')
            toon.loop('walk')
            self.toons.append(toon)
            base.loader.tick()

        seq = Sequence(
                Parallel(
                        Sequence(
                                Func(self.toons[0].setPosHpr, path1Points[0], Point3(90, 0, 0)),
                                blendAnimation(0.5, actor = self.toons[0], fromAnim = 'neutral', toAnim = 'run'),
                                Parallel(
                                        LerpPosInterval(self.toons[0], duration = 5, pos = path1Points[2],
                                                        blendType = 'easeInOut'),
                                        Sequence(Wait(4.5),
                                                 blendAnimation(0.5, actor = self.toons[0], fromAnim = 'run',
                                                                toAnim = 'neutral'))),
                                Wait(3),
                        ),
                        Sequence(
                                Wait(0.5),
                                Func(self.toons[1].setPosHpr, path1Points[5], Point3(-90, 0, 0)),
                                blendAnimation(0.5, actor = self.toons[1], fromAnim = 'neutral', toAnim = 'run'),
                                Parallel(
                                        LerpPosInterval(self.toons[1], duration = 5, pos = path1Points[3],
                                                        blendType = 'easeInOut'),
                                        Sequence(Wait(4.5),
                                                 blendAnimation(0.5, actor = self.toons[1], fromAnim = 'run',
                                                                toAnim = 'neutral'))),
                                Wait(2.5),
                        ),
                )
        )

        return seq
