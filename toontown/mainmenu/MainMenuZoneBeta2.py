from typing import List

from direct.interval.MetaInterval import Sequence
from panda3d.core import PolylightEffect, NodePath, PolylightNode, Vec4, VBase4, Vec3, CSDefault

from panda3d.toontown import loadDNAFile

from toontown.avatar import ToontownAvatarUtils
from toontown.mainmenu.MainMenuZone import MainMenuZone
from toontown.toonbase import ToontownGlobals
from toontown.hood import SkyUtil


class MainMenuZoneBeta2(MainMenuZone):
    zone = 'DL'
    storages = [
        'phase_8/dna/ttrm_d_strg_ddl.dna',
        'phase_8/dna/ttrm_d_strg_ddl_sz.dna',
        'phase_8/dna/ttrm_d_strg_ddl_town.dna'
    ]
    skyModel = 'phase_8/models/props/DL_sky'
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
        self.pe: PolylightEffect = PolylightEffect.make()
        self.pe.setWeight(20)
        self.char.node().setEffect(self.pe)

        oneLights = self.geom.findAllMatches("**/*prop_dl_post_one_light_DNARoot")
        threeLights = self.geom.findAllMatches("**/*prop_dl_post_three_light_DNARoot")
        lamps: List[NodePath] = oneLights + threeLights
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

    def load(self):
        loadDNAFile(self.DNAStorage, 'phase_4/dna/ttrm_d_strg.dna', CSDefault, 1)

        for storage in self.storages:
            loadDNAFile(self.DNAStorage, storage, CSDefault, 1)
            base.loader.tick()

        np = loadDNAFile(self.DNAStorage, f'phase_8/dna/ttrm_d_ara_ddl_9400.dna', CSDefault,
                         1)  # type: NodePath
        if np.getNumParents() == 1:
            self.geom = NodePath(np.getParent(0))
            self.geom.reparentTo(render)
        else:
            self.geom = render.attachNewNode(np)  # type: NodePath
        base.loader.tick()

        if loader.loadingScreen.getActiveHoliday() == ToontownGlobals.HolidayHalloween:
            self.geom.setColorScale(0.6, 0.6, 0.6, 1.0)

        # Hide the black parts in the doors
        doorHoles = self.geom.findAllMatches('**/doorFrameHole*')
        for hole in doorHoles:
            hole.removeNode()

        self.sky = loader.loadModel(self.skyModel)  # type: NodePath
        self.sky.reparentTo(render)
        if loader.loadingScreen.getActiveHoliday() == 0:
            self.startCloudSky()

        if loader.loadingScreen.getActiveHoliday() in [ToontownGlobals.HolidayHalloween, ToontownGlobals.HolidayWinter]:
            lights = self.geom.findAllMatches('**/*light*')
            lights += self.geom.findAllMatches('**/*lamp*')
            lights += self.geom.findAllMatches('**/prop_snow_tree*')
            for light in lights:
                light.setColorScaleOff(0)
        base.loader.tick()

        self.char = ToontownAvatarUtils.createToon(9428)

        self.char.nametag.getNametag2d().setContents(0)
        self.char.setPosHpr(-.5, -8.4, 0.02, 80, 0, 0)
        self.char.loop('neutral')
        self.char.reparentTo(self.geom)

        base.loader.tick()

        self.loadAnimatedProps()
        base.loader.tick()

        gsg = base.win.getGsg()
        if gsg:
            self.geom.prepareScene(gsg)

        base.camera.setPosHpr(
                Vec3(-10, -8.5, 2.8),
                Vec3(-60, 5, 0.0)
        )

        self.sky.setScale(4)
        base.camLens.setFar(2000)

        self.sequence = self.setupToonAnimation()
        if self.sequence:
            self.sequence.loop()

    def setupToonAnimation(self) -> Sequence:
        pass

    def startCloudSky(self):
        return SkyUtil.startSingleCloudSky(self)

    def skyTrackSingle(self, task):
        return SkyUtil.singleCloudSkyTrack(task)
