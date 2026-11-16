"""
Toontown Central Safe Zone Activity
Toon Statues
Based off of the concept in the Toontown Online Design Document
https://toontown.online/905ea572bbde4ec5850454f3b12bf521?v=99a0801f64d54d1a989c2783dc267ad7&p=0f26100190ea41fe98a77dcd49ecf9a0
"""

from direct.distributed.DistributedNode import DistributedNode
from direct.gui.DirectLabel import DirectLabel
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import NodePath, VBase4, TextureStage, ShaderAttrib, Shader, CollisionSphere, CollisionNode, Point2, \
    Point3

from otp.otpbase.PythonUtil import bound
from toontown.toon.LocalToon import LocalToon
from toontown.toon.Toon import Toon
from toontown.toon.ToonDNA import ToonDNA
from toontown.toonbase import ToontownGlobals, TTLocalizer, HotkeySettings
from toontown.toonbase.ControlManager import ControlManager


class DistributedTTStatueActivity(DistributedNode, NodePath):
    stoneTexture = loader.loadTexture('phase_5.5/maps/smoothwall_1.png')

    desatShirtTex = loader.loadTexture('phase_3/maps/desat_shirt_1.png')
    desatSleeveTex = loader.loadTexture('phase_3/maps/desat_sleeve_1.png')
    desatShortsTex = loader.loadTexture('phase_3/maps/desat_shorts_1.png')
    desatSkirtTex = loader.loadTexture('phase_3/maps/desat_skirt_1.png')

    attr = ShaderAttrib.make(Shader.load(Shader.SLGLSL,
                                         fragment = 'phase_3/shaders/ttoff_sha_av_toon_statue.frag',
                                         vertex = 'phase_3/shaders/ttoff_sha_av_toon_statue.vert'))
    attr = attr.setFlag(ShaderAttrib.F_hardware_skinning, True)

    def __init__(self, cr):
        DistributedNode.__init__(self, cr)
        NodePath.__init__(self, 'tt_activity_statue')
        self.cr = cr

    def generate(self):
        self.reparentTo(render)
        DistributedNode.generate(self)

        # Generate a blank toon
        self.toon = Toon()
        self.toon.reparentTo(self)
        self.toon.initializeBodyCollisions('toonStatue')
        self.toon.stopBlink()
        self.toon.stopLookAround()
        self.toon.setZ(3.29)

        # Apply the shader
        self.toon.setAttrib(self.attr)

        # Load the pedestal the toon will stand on
        self.pedestal = loader.loadModel('phase_14.5/models/props/tt-activity-statue-pedestal')
        self.pedestal.reparentTo(self)
        self.pedestal.setScale(0.25)

        # Add the name of the toon on the bottom of the pedestal
        self.label = DirectLabel(parent = self, relief = None, text = 'TEXT', text_fg = (1.0, 1.0, 1.0, 1.0),
                                 scale = 0.1, text_wordwrap = 12)
        self.label.setPos(0, 0.8, 0.3)
        self.label.setH(180)

        self.collSphere = CollisionSphere(0, 0, 2, 3)
        self.collSphere.setTangible(0)
        self.collNode = CollisionNode(self.collisionName)
        self.collNode.setCollideMask(ToontownGlobals.WallBitmask)
        self.collNode.addSolid(self.collSphere)
        self.collNodePath = self.attachNewNode(self.collNode)

        self.accept(f'enter{self.collisionName}', self.__enterSphere)

    def announceGenerate(self):
        DistributedNode.announceGenerate(self)
        self.setStoneTexture()

    def __enterSphere(self, collEntry = None):
        """
        Toon has entered the trigger sphere
        """
        self.__createInteractHint()

    def __exitSphere(self, collEntry = None):
        self.ignore(f'exit{self.collisionName}')
        self.__destroyInteractHint()

    def disable(self):
        self.notify.debug('disable statue')
        self.ignoreAll()
        self.collNodePath.removeNode()
        DistributedNode.disable(self)
        if hasattr(self, 'nodePath'):
            self.nodePath.detachNode()

    def __interact(self):
        """
        This is called when the user presses the Interact key
        or just collides with the sphere if interact key is disabled
        """
        self.notify.debug('interacted')
        self.sendUpdate('touchedStatue', [])

    def setDNA(self, dna):
        """
        Sets the DNA from a net string
        This is sent from the AI

        :param dna: DNA Net String
        :type dna: bytes
        """
        self.dna = dna
        self.toon.setDNAString(dna)
        self.toon.stopBlink()
        self.toon.stopLookAround()
        self.toon.deleteDropShadow()

    def setInfo(self, name, pose, poseFrame, hat, backpack, glasses, shoes):
        """
        Sets other info sent from the AI

        :param name: The Toon's Name
        :param pose: Animation
        :param poseFrame: Frame of animation to pose
        :type name: str
        :type pose: str
        :type poseFrame: int
        :type hat: tuple[int, int, int]
        :type backpack: tuple[int, int, int]
        :type glasses: tuple[int, int, int]
        :type shoes: tuple[int, int, int]
        """
        self.notify.debug(f'{name} {pose}:{poseFrame}')
        self.info = (name, pose, poseFrame, hat, backpack, glasses, shoes)

        self.toon.pose(pose, poseFrame)

        self.toon.setHat(*hat)
        self.toon.setBackpack(*backpack)
        self.toon.setGlasses(*glasses)
        self.toon.setShoes(*shoes)

        for emoji in base.emojis:
            name = name.replace(f':{emoji}:', f'\x01white\x01\5{emoji}\5\x02')
        if base.cr.getChatFilterMode() >= ToontownGlobals.CHAT_FILTER_CENSOR:
            # todo: handle whitelist
            name = base.profanityFilter.censor(name)
        self.label['text'] = name

    def setStoneTexture(self):
        """
        Applies the Stone Texture to the toon objects
        """
        ts = TextureStage('ts')
        ts.setPriority(1)
        self.toon.setTexture(ts, self.stoneTexture)
        tsDetail = TextureStage('tsDetail')
        tsDetail.setPriority(2)
        tsDetail.setSort(10)
        tsDetail.setCombineRgb(tsDetail.CMInterpolate, tsDetail.CSTexture, tsDetail.COSrcColor, tsDetail.CSPrevious,
                               tsDetail.COSrcColor, tsDetail.CSConstant, tsDetail.COSrcColor)
        tsDetail.setColor(VBase4(0.5, 0.5, 0.5, 1))
        if self.toon.hasLOD():
            for lodName in self.toon.getLODNames():
                head = self.toon.getPart('head', lodName)
                eyes = head.find('**/eye*')
                if not eyes.isEmpty():
                    eyes.setColor(VBase4(1.4, 1.4, 1.4, 1.0), 10)
                ears = head.find('**/ears*')
                animal = self.toon.style.getAnimal()
                if animal != 'dog':
                    muzzle = head.find('**/muzzle*neutral')
                else:
                    muzzle = head.find('**/muzzle*')
                if ears != ears.notFound():
                    if self.toon.style.getAnimal() == 'cat':
                        ears.setTexture(tsDetail, self.stoneTexture)
                    elif self.toon.style.getAnimal() == 'horse':
                        pass
                    elif self.toon.style.getAnimal() == 'rabbit':
                        ears.setTexture(tsDetail, self.stoneTexture)
                    elif self.toon.style.getAnimal() == 'monkey':
                        ears.setTexture(tsDetail, self.stoneTexture)
                        ears.setColor(VBase4(0.6, 0.9, 1, 1), 10)
                if muzzle != muzzle.notFound():
                    muzzle.setTexture(tsDetail, self.stoneTexture)
                if self.toon.style.getAnimal() == 'dog':
                    nose = head.find('**/nose')
                    if nose != nose.notFound():
                        nose.setTexture(tsDetail, self.stoneTexture)

        tsLashes = TextureStage('tsLashes')
        tsLashes.setPriority(2)
        tsLashes.setMode(tsLashes.MDecal)
        if self.toon.style.gender == 'f':
            if self.toon.hasLOD():
                head = self.toon.getPart('head', '1000')
            else:
                head = self.toon.getPart('head', 'lodRoot')
            if self.toon.style.head[1] == 'l':
                openString = 'open-long'
                closedString = 'closed-long'
            else:
                openString = 'open-short'
                closedString = 'closed-short'
            lashesOpen = head.find('**/' + openString)
            lashesClosed = head.find('**/' + closedString)
            if lashesOpen != lashesOpen.notFound():
                lashesOpen.setTexture(tsLashes, self.stoneTexture)
                lashesOpen.setColor(VBase4(1, 1, 1, 0.4), 10)
            if lashesClosed != lashesClosed.notFound():
                lashesClosed.setTexture(tsLashes, self.stoneTexture)
                lashesClosed.setColor(VBase4(1, 1, 1, 0.4), 10)

    @property
    def collisionName(self):
        return f'tt-statue-{self.getDoId()}'

    def __createInteractHint(self):
        if not hasattr(self, "interactHint"):
            self.accept(HotkeySettings.Interact.getPressed(), self.__interact)
            self.accept(f'exit{self.collisionName}', self.__exitSphere)
            self.accept('toonExitWalk', self.__exitSphere)

            self.interactHint = OnscreenText(ControlManager.parseHotkeyString(TTLocalizer.ActivityInteractStatue, useGlyphs = True),
                                             style = 3, scale = .065, parent = base.a2dBottomCenter,
                                             font = ToontownGlobals.getFancyFont(),
                                             fg = (0.92, 0.93, 0.56, 1.0),
                                             pos = (0.0, 0.0))

            taskMgr.add(self.__alignInteractHint, self.alignInteractHintTaskName)

    def __destroyInteractHint(self):
        self.ignore(HotkeySettings.Interact.getPressed())
        self.ignore('toonExitWalk')
        # Remove interact hint
        if hasattr(self, "interactHint"):
            taskMgr.remove(self.alignInteractHintTaskName)
            self.interactHint.removeNode()
            del self.interactHint

    def __alignInteractHint(self, task):
        """
        Aligns the interact hint on the screen
        The hint should be positioned on the npc, then the position is projected to the aspect2d
        """
        if hasattr(self, 'interactHint'):
            center = base.cam.getRelativePoint(self, Point3(0, 0, 3))

            if self.dna == base.localAvatar.style.makeNetString():
                text = ControlManager.parseHotkeyString(TTLocalizer.ActivityInteractStatuePose, useGlyphs = True)
            else:
                text = ControlManager.parseHotkeyString(TTLocalizer.ActivityInteractStatue, useGlyphs = True)
            if self.interactHint['text'] != text:
                self.interactHint['text'] = text

            if base.camNode.isInView(center):
                center2d = Point2()
                base.camLens.project(center, center2d)

                center2d.x = bound(center2d.x, -0.7, 0.7)
                center2d.y = bound(center2d.y, -0.9, 0.95)
            else:
                # If the point isnt in the view, we set it to the 'default' position
                center2d = Point2(0.0, -0.45)

            self.interactHint.set_pos(render2d, Point3(center2d.x, 0, center2d.y))

        return task.cont

    @property
    def alignInteractHintTaskName(self):
        return f'alignInteractHint-{self.getDoId()}'
