from direct.gui.DirectWaitBar import DirectWaitBar
from direct.gui.OnscreenText import OnscreenText
from direct.interval.IntervalGlobal import *

from panda3d.toontown import *

from panda3d.core import *

from toontown.episodes import DistributedEpisodeZone
from toontown.episodes import EpisodeConfig
from toontown.toonbase import TTLocalizer, ToontownGlobals, HotkeySettings, ControlManager


class EP03DistributedSellbotHQ(DistributedEpisodeZone.DistributedEpisodeZone):

    def __init__(self, cr):
        DistributedEpisodeZone.DistributedEpisodeZone.__init__(self, cr)
        self.episodeZoneId = EpisodeConfig.EP03_SELLBOT_HQ

    def announceGenerate(self):
        DistributedEpisodeZone.DistributedEpisodeZone.announceGenerate(self)
        # QTE
        self.__chewProgress = 0.0
        self.__chewQTEStarted = False
        self.__chewDecayTaskName = self.taskName('chew-qte-decay')

    def disable(self):
        DistributedEpisodeZone.DistributedEpisodeZone.disable(self)

    def generateGeom(self):
        self.geom = loader.loadModel('phase_9/models/cogHQ/SellbotHQExterior')

        self.geom.reparentTo(render)

        dgLinkTunnel = self.geom.find('**/Tunnel1')
        dgLinkTunnel.setName('linktunnel_dg_5316_DNARoot')
        factoryLinkTunnel = self.geom.find('**/Tunnel2')
        factoryLinkTunnel.setName('linktunnel_sellhq_11200_DNARoot')
        cogSignModel = loader.loadModel('phase_4/models/props/sign_sellBotHeadHQ')
        cogSign = cogSignModel.find('**/sign_sellBotHeadHQ')

        # OAK STREET SIGN
        dgSign = cogSign.copyTo(dgLinkTunnel)
        dgSign.setPosHprScale(0.0, -291.5, 29, 180.0, 0.0, 0.0, 23, 23, 23 * 0.7227)
        dgSign.node().setEffect(DecalEffect.make())
        dgText = OnscreenText(text = TTLocalizer.DaisyGardens[-1], font = ToontownGlobals.getSuitFont(),
                              pos = (0, -0.3), scale = TTLocalizer.SCHQLdgText, mayChange = False, parent = dgSign)
        dgText.setDepthWrite(0)

        # FACTORY SIGN
        factorySign = cogSign.copyTo(factoryLinkTunnel)
        factorySign.setPosHprScale(148.625, -155, 27, -90.0, 0.0, 0.0, 23, 23, 23 * 0.7227)
        factorySign.node().setEffect(DecalEffect.make())
        factoryTypeText = OnscreenText(text = TTLocalizer.Sellbot, font = ToontownGlobals.getSuitFont(),
                                       pos = (0, -0.25), scale = 0.075, mayChange = False, parent = factorySign)
        factoryTypeText.setDepthWrite(0)
        factoryText = OnscreenText(text = TTLocalizer.Factory, font = ToontownGlobals.getSuitFont(), pos = (0, -0.34),
                                   scale = 0.12, mayChange = False, parent = factorySign)
        factoryText.setDepthWrite(0)
        doors = self.geom.find('**/doors')
        door0 = doors.find('**/door_0')
        door1 = doors.find('**/door_1')
        door2 = doors.find('**/door_2')
        door3 = doors.find('**/door_3')
        index = 0
        for door in (door0, door1, door2, door3):
            doorFrame = door.find('**/doorDoubleFlat/+GeomNode')
            door.find('**/doorFrameHoleLeft').wrtReparentTo(doorFrame)
            door.find('**/doorFrameHoleRight').wrtReparentTo(doorFrame)
            doorFrame.node().setEffect(DecalEffect.make())
            index += 1
        self.factGeom = loader.loadModel('phase_9/models/cogHQ/SellbotFactoryExterior')
        self.factGeom.setPos(504.997, -200, -24)
        self.factGeom.setHpr(-90, 0, 0)
        self.factGeom.setScale(0.859913)
        self.factGeom.find('**/tunnel_group2').removeNode()
        self.factGeom.wrtReparentTo(self.geom)

        # SKY STUFF
        self.sky = loader.loadModel('phase_9/models/cogHQ/cog_sky')
        self.sky.reparentTo(camera)
        self.sky.setScale(2.5)
        self.sky.setZ(0.0)
        self.sky.setHpr(0.0, 0.0, 0.0)
        ce = CompassEffect.make(NodePath(), CompassEffect.PRot | CompassEffect.PZ)
        self.sky.node().setEffect(ce)
        skyInner = self.sky.find('**/InnerGroup')
        skyMiddle = self.sky.find('**/MiddleGroup')
        skyOuter = self.sky.find('**/OuterSky')
        if not skyOuter.isEmpty():
            skyOuter.setBin('background', 0)
        if not skyMiddle.isEmpty():
            skyMiddle.setDepthWrite(0)
            skyMiddle.setBin('background', 10)
        if not skyInner.isEmpty():
            skyInner.setDepthWrite(0)
            skyInner.setBin('background', 20)

        # Hide the black parts in the doors
        doorHoles = self.geom.findAllMatches('**/doorFrameHole*')
        for hole in doorHoles:
            hole.removeNode()

        # wire interaction
        self.wires = loader.loadModel('phase_14.5/models/props/ffc')
        self.wires.reparentTo(self.geom)
        self.wires.setPos(-30, -108, 0.29)
        cSphere = CollisionSphere(0.0, 0.0, 0.0, 8)
        cSphere.setTangible(0)
        cSphereNode = CollisionNode('wire_interact')
        cSphereNode.addSolid(cSphere)
        self.cSphereNodePath = self.wires.attachNewNode(cSphereNode)
        self.cSphereNodePath.show()
        cSphereNode.setCollideMask(ToontownGlobals.WallBitmask)

        gsg = base.win.getGsg()
        if gsg:
            self.geom.prepareScene(gsg)

        self.acceptOnce('enterwire_interact', self.__interactWithWires)

    def generateMovie(self):
        self.movie = Sequence(
                Func(base.transitions.irisIn, 0.5),
                Func(self.releaseToon),
                Func(self.toon.enableAvatarControls)
                )

    def __interactWithWires(self, collEntry):
        # gameplay prototype, obviously not final
        self.lockToon()

        # show a tooltip
        text: str = ControlManager.ControlManager.parseHotkeyString(TTLocalizer.EP03_InteractWithWires, useGlyphs=True)
        self.qteSpamHint = OnscreenText(text, style = 3, scale = .065, parent = aspect2d,
                           font = ToontownGlobals.getSuitFont(), fg = (0.5, 0.5, 0.5, 1.0),
                           pos = (0.0, -0.45))
        self.qteSpamProgress = DirectWaitBar(range = 100.0, value = 0.0)

        self.accept(HotkeySettings.Interact.getPressed(),
                    self.__chewQTETap)

    def __chewQTETap(self):
        self.__chewProgress += 10.0
        if not self.__chewQTEStarted:
            self.__chewQTEStarted = True
            taskMgr.doMethodLater(0.08, self.__chewQTEDecay, self.__chewDecayTaskName)
        self.__updateQTEProgress()

    def __chewQTEDecay(self, task):
        self.__chewProgress -= 1.0
        self.__updateQTEProgress()
        return task.again

    def __updateQTEProgress(self):
        self.qteSpamProgress['value'] = self.__chewProgress
        if self.__chewProgress < 0:
            taskMgr.remove(self.__chewDecayTaskName)
            self.ignore(HotkeySettings.Interact.getPressed())
            self.qteSpamProgress.hide()
            self.qteSpamHint['text'] = 'fail lol'
        if self.__chewProgress >= 100:
            taskMgr.remove(self.__chewDecayTaskName)
            self.ignore(HotkeySettings.Interact.getPressed())
            self.qteSpamProgress.hide()
            self.qteSpamHint['text'] = 'Done'
            self.wires.hide()


