from direct.interval.MetaInterval import Sequence
from panda3d.core import PolylightEffect, NodePath, PolylightNode, Vec4, VBase4, Vec3

from toontown.mainmenu.MainMenuZone import MainMenuZone
from toontown.toonbase import ToontownGlobals
from toontown.hood import SkyUtil


class MainMenuZoneDL(MainMenuZone):
    zone = 'DL'  # type: str
    storages = [
        'phase_8/dna/ttrm_d_strg_ddl.dna',
        'phase_8/dna/ttrm_d_strg_ddl_sz.dna',
        'phase_8/dna/ttrm_d_strg_ddl_town.dna'
    ]  # type: list[str]
    skyModel = 'phase_8/models/props/DL_sky'  # type: str
    if loader.loadingScreen.getActiveHoliday() == ToontownGlobals.HolidayHalloween:
        storages.append('phase_8/dna/ttrm_d_strg_ddl_halloween.dna')
        storages.append('phase_8/dna/ttrm_d_strg_ddl_sz_halloween.dna')
        skyModel = 'phase_14.5/models/props/halloween-skybox'
    if loader.loadingScreen.getActiveHoliday() == ToontownGlobals.HolidayWinter:
        storages.append('phase_8/dna/ttrm_d_strg_ddl_winter.dna')
        skyModel = 'phase_3.5/models/props/BR_sky'
    billboardColor = VBase4(0.55, 0.16, 0.76, 1.0)
    billboardPos = (
        Vec3(55.2917, 109.956, 11.0),
        Vec3(-15, 0, 0),
        Vec3(1.54797)
    )
    char = {
        ToontownGlobals.HolidayNormal:     'd',
        ToontownGlobals.HolidayHalloween:  'fd',
        ToontownGlobals.HolidayWinter:     'd',
        ToontownGlobals.HolidayAprilFools: 'd'
    }

    def __init__(self):
        MainMenuZone.__init__(self)
        self.geom.setColorScale(0.6, 0.6, 0.64, 1.0)
        self.pe = PolylightEffect.make()  # type: PolylightEffect
        self.pe.setWeight(20)
        self.char.node().setEffect(self.pe)

        oneLights = self.geom.findAllMatches("**/*prop_dl_post_one_light_DNARoot")
        threeLights = self.geom.findAllMatches("**/*prop_dl_post_three_light_DNARoot")
        lamps = oneLights + threeLights  # type: list[NodePath]
        self.discs = []

        # List of NodePaths of PolylightNodes
        self.polylights = []

        for lamp in lamps:
            lamp.setColorScale(Vec4(1), 1)
            disc = loader.loadModel("phase_3.5/models/props/glow")
            # Add PolylightNodes
            plNode = PolylightNode("pl"+str(hash(lamp)))
            plNode.setRadius(35)
            plNode.setColor(1.0, 0.9, 0.8)
            plNode.flickerOff()
            plNodePath = NodePath(plNode)
            self.polylights.append(plNodePath)

            self.pe = self.pe.addLight(plNodePath)
            self.char.node().setEffect(self.pe)

            # A glow around the lamp light bulb

            disc.setBillboardPointEye()
            if 'three' in lamp.getName():
                disc.setPos(0.5, -1, 10)
            else:
                disc.setPos(-.5, -1, 10)
            disc.setScale(8)
            disc.setColorScale(1, 1, 0.8, 0.25, 1)
            disc.setTransparency(1)
            if loader.loadingScreen.getActiveHoliday() in [ToontownGlobals.HolidayHalloween, ToontownGlobals.HolidayWinter]:
                disc.reparentTo(lamp.find('**/*streetlamp*'))
            else:
                disc.reparentTo(lamp.find("**/p*3"))
            # disc.node().setEffect(pe)
            self.discs.append(disc)
            # A glow on the floor
            disc = loader.loadModel("phase_3.5/models/props/glow")
            disc.setPos(0, 0, 0.025)
            disc.setHpr(0, 90, 0)
            disc.setScale(14)
            disc.setColorScale(1, 1, 0.8, 0.25, 1)
            disc.setTransparency(1)
            if loader.loadingScreen.getActiveHoliday() in [ToontownGlobals.HolidayHalloween, ToontownGlobals.HolidayWinter]:
                disc.reparentTo(lamp.find('**/*streetlamp*'))
            else:
                disc.reparentTo(lamp.find("**/p*3"))
            plNodePath.reparentTo(disc)
            disc.node().setEffect(self.pe)
            disc.show()
            self.discs.append(disc)

    def setupToonAnimation(self):  # type: () -> Sequence
        pass

    def startCloudSky(self):
        return SkyUtil.startSingleCloudSky(self)

    def skyTrackSingle(self, task):
        return SkyUtil.singleCloudSkyTrack(task)
