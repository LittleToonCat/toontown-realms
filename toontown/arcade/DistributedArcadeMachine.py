"""
DistributedArcadeMachine Client Side • Created by Drew @ 10/6/2022
Authorized for use ONLY in Toontown Realms
"""
from typing import Optional, Tuple, List, Union

from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObject import DistributedObject
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import NodePath, GraphicsOutput, Shader, CollisionSphere, CollisionNode, Point2, Point3, TextNode

from otp.otpbase.PythonUtil import bound
from toontown.arcade.ArcadeMachineGlobals import RequestPlayResponses
from toontown.toonbase import ToontownGlobals, TTLocalizer, HotkeySettings, ControlManager


class DistributedArcadeMachine(DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistArcadeMachine')

    def __init__(self, cr):
        DistributedObject.__init__(self, cr)
        self.gameRender: Optional[NodePath] = None
        self.gameRenderBuffer: Optional[GraphicsOutput] = None
        self.gameRenderCam: Optional[NodePath] = None
        self.machineNode: Optional[NodePath] = None
        self.displayedHotkeys: List[NodePath] = []

    def announceGenerate(self):
        DistributedObject.announceGenerate(self)
        if not self.machineNode:
            self.notify.error('No machineNode found! Did someone try spawning the base arcade machine class??')

        # Create a scene graph for this arcade machine.
        # We should probably only create this once we activate the machien instead of it always being there
        # but we havent done that functionality yet
        self.gameRender = NodePath(f'{self.__class__.__name__}:{self.getDoId()}')
        self.gameRenderBuffer: GraphicsOutput = base.win.makeTextureBuffer(
            f'arcadeBuffer::{self.__class__.__name__}:{self.getDoId()}', 512, 512)
        self.gameRenderCam: NodePath = base.makeCamera(self.gameRenderBuffer, aspectRatio = 1.0,
                                                       clearColor = (0, 0, 0, 1),
                                                       displayRegion = (0, 1, 0, 1))
        self.gameRenderCam.reparentTo(self.gameRender)

        self.gameRenderCam.node().getLens().setMinFov(60)

        screen: NodePath = self.machineNode.find('**/SCREEN')
        screen.setTexture(self.gameRenderBuffer.getTexture(), 1)
        screen.setShader(
            Shader.load(Shader.SLGLSL, vertex = 'phase_8/shaders/ttrm_sha_ara_int_arcade_machineScreen.vert',
                        fragment = 'phase_8/shaders/ttrm_sha_ara_int_arcade_machineScreen.frag')
        )
        self.machineNode.reparentTo(render)

        self.collSphere = CollisionSphere(0, 0, 2, 3)
        self.collSphere.setTangible(0)
        self.collNode = CollisionNode(self.collisionName)
        self.collNode.setCollideMask(ToontownGlobals.WallBitmask)
        self.collNode.addSolid(self.collSphere)
        self.collNodePath: NodePath = self.machineNode.attachNewNode(self.collNode)

        self.accept(f'enter{self.collisionName}', self.__enterSphere)

    def disable(self):
        base.graphicsEngine.removeWindow(self.gameRenderBuffer)
        self.gameRenderCam.removeNode()
        self.gameRender.removeNode()
        self.machineNode.removeNode()
        del self.gameRenderBuffer
        del self.gameRenderCam
        del self.gameRender
        self.ignoreAll()
        self.collNodePath.removeNode()

    def requestPlayResponse(self, respCode: RequestPlayResponses):
        if respCode == RequestPlayResponses.SOMEONE_ELSE_PLAYING:
            self.cr.playGame.getPlace().setState('walk')
        elif respCode == RequestPlayResponses.START_PLAYING:
            self.startPlaying()
        elif respCode == RequestPlayResponses.STOP_PLAYING:
            self.stopPlaying()

    def startPlaying(self):
        base.camera.reparentTo(self.machineNode)
        base.camera.setPos(0, 2.8, 3.9)
        base.camera.setHpr(180, -20, 0)
        base.localAvatar.setPos(self.machineNode, 0, 3, 0)
        base.localAvatar.setH(self.machineNode, 180)
        base.localAvatar.cameraFSM.request('Off')
        self.cr.playGame.getPlace().setState('stopped')
        base.localAvatar.hide()

    def stopPlaying(self):
        base.localAvatar.cameraFSM.requestLastCamera()
        base.localAvatar.show()
        self.clearDisplayedHotkeys()
        self.cr.playGame.getPlace().setState('walk')

    def displayHotkeys(self,  hotkeys: List[Tuple[Union[List[Tuple[str, int]], Tuple[str, int], str], str]]):
        """
        Displays hotkey hint sin the bottom right corner of the screen
        the hotkey parameter takes a list of tuples
        [
            ((ToontownGlobals.HotkeyMovement, ToontownGlobals.HotkeyAction), "Do an action!"),
            ((ToontownGlobals.HotkeyMovement, ToontownGlobals.HotkeyJump), "Jump"),

            # This one shows multiple keys for one action
            ([
                (ToontownGlobals.HotkeyMovement, ToontownGlobals.HotkeyUp),
                (ToontownGlobals.HotkeyMovement, ToontownGlobals.HotkeyDown),
                (ToontownGlobals.HotkeyMovement, ToontownGlobals.HotkeyLeft),
                (ToontownGlobals.HotkeyMovement, ToontownGlobals.HotkeyRight)
            ], "Move"),

            # this one jus directly uses a key name instead of a dedicated hotkey
            ("mouse", "Look")
        ]
        """
        self.clearDisplayedHotkeys()
        for i, control in enumerate(reversed(hotkeys)):
            # Todo: we will use textured glyphs for the key binds
            _displaytext = control[1]
            _key = ""
            if isinstance(control[0], list):
                for key in control[0]:
                    _key += f"\x01white\x01\5kbm_{base.controlManager.getKeyName(key[0], key[1])}\5\x02"
            elif isinstance(control[0], str):
                _key = f"\x01white\x01\5kbm_{control[0]}\5\x02"
            else:
                _key = f"\x01white\x01\5kbm_{base.controlManager.getKeyName(control[0][0], control[0][1])}\5\x02"

            _textString = f'{control[1]}  {_key}'
            _hotkeyString = OnscreenText(
                parent = base.a2dBottomRight,
                text = _textString,
                align = TextNode.ARight,
                pos = (-0.06, 0.1 + (i/10)),
                scale = 0.05,
                fg = (1.0, 1.0, 1.0, 1.0),
                shadow = (0.0, 0.0, 0.0, 0.7)
            )
            self.displayedHotkeys.append(_hotkeyString)

    def clearDisplayedHotkeys(self):
        for hotkey in self.displayedHotkeys:
            hotkey.removeNode()
            del hotkey
        self.displayedHotkeys = []

    @property
    def collisionName(self) -> str:
        return f'arcadeMachine:{self.__class__.__name__}:{self.getDoId()}'

    def __enterSphere(self, collEntry = None):
        """
        Toon has entered the trigger sphere
        """
        self.__createInteractHint()

    def __exitSphere(self, collEntry = None):
        self.ignore(f'exit{self.collisionName}')
        self.__destroyInteractHint()

    def __interact(self):
        """
        This is called when the user presses the Interact key
        or just collides with the sphere if interact key is disabled
        """
        self.notify.debug('interacted')
        self.__exitSphere()
        self.cr.playGame.getPlace().setState('stopped')
        self.sendUpdate('requestPlay')

    def __createInteractHint(self):
        if not hasattr(self, "interactHint"):
            self.accept(HotkeySettings.Interact.getPressed(),
                        self.__interact)
            self.accept(f'exit{self.collisionName}', self.__exitSphere)
            self.accept('toonExitWalk', self.__exitSphere)

            text = ControlManager.ControlManager.parseHotkeyString(TTLocalizer.ActivityInteractStatue, useGlyphs=True)
            self.interactHint = OnscreenText(text, style = 3, scale = .065, parent = base.a2dBottomCenter,
                font = ToontownGlobals.getFancyFont(),
                fg = (0.92, 0.93, 0.56, 1.0),
                pos = (0.0, 0.0))

            self.addTask(self.__alignInteractHint, self.alignInteractHintTaskName)

    def __destroyInteractHint(self):
        self.ignore(HotkeySettings.Interact.getPressed())
        self.ignore('toonExitWalk')
        # Remove interact hint
        if hasattr(self, "interactHint"):
            self.removeTask(self.alignInteractHintTaskName)
            self.interactHint.removeNode()
            del self.interactHint

    def __alignInteractHint(self, task):
        """
        Aligns the interact hint on the screen
        The hint should be positioned on the npc, then the position is projected to the aspect2d
        """
        if hasattr(self, 'interactHint'):
            center: Point3 = base.cam.getRelativePoint(self.machineNode, Point3(0, 0, 3))

            text: str = ControlManager.ControlManager.parseHotkeyString(
                TTLocalizer.ActivityInteractArcadeMachinePlay + f'\n{self.__class__.__name__}:{self.getDoId()}',
                useGlyphs=True
            )
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
    def alignInteractHintTaskName(self) -> str:
        return f'alignInteractHint::{self.__class__.__name__}:{self.getDoId()}'
