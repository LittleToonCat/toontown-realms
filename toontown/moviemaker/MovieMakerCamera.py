import sys
from typing import Tuple, Optional

from direct.fsm.FSM import FSM
from panda3d.core import WindowProperties, NodePath, PointerData

from toontown.toonbase import ClientSettings
from direct.showbase.InputStateGlobal import inputState

from otp.avatar import OTPControlManager

MAX_SPEED = 60
MIN_SPEED = 2

class MovieMakerCamera(FSM):

    def __init__(self):
        FSM.__init__(self, 'MovieMakerCamera')
        self.sceneCamera = NodePath('movie-maker-scene-camera')
        self.sceneCamera.reparentTo(render)
        self.workCamera = NodePath('movie-maker-work-camera')
        self.workCamera.reparentTo(render)

        self.moveSpeed: int = 10

        self.activeCamera: Optional[NodePath] = None

        self.controlManager = OTPControlManager.OTPControlManager(True)
        self.controlManager.enable()
        self.controlManager.setStrafing(True)

        self.setActiveCamera(self.sceneCamera)

        self.__mouseOrigin: Tuple[int, int] = (0, 0)
        self.__mouseActive: bool = False
        self.__mouseDelta: Tuple[float, float] = (0, 0)
        self.__lastMousePos: Tuple[int, int] = (0, 0)

        self.accept('mouse3', self.startMouseControl)

    def speedUp(self):
        self.moveSpeed = min(self.moveSpeed + 2, MAX_SPEED)

    def speedDown(self):
        self.moveSpeed = max(self.moveSpeed - 2, MIN_SPEED)

    def setActiveCamera(self, camera: NodePath):
        self.activeCamera = camera
        base.camera.reparentTo(camera)
        base.camera.setPosHpr(0, 0, 0, 0, 0, 0)

    def startMouseControl(self):
        if hasattr(base, 'oobeMode') and base.oobeMode:
            return

        self.ignore('mouse3')
        self.accept('mouse3-up', self.stopMouseControl)
        self.accept('wheel_up', self.speedUp)
        self.accept('wheel_down', self.speedDown)

        self.__mouseActive = True

        mouseData: PointerData = base.win.getPointer(0)
        # Save the cursor origin so we can set it back when we are done controlling
        self.__mouseOrigin = int(mouseData.getX()), int(mouseData.getY())
        if sys.platform != 'win32':
            self.__lastMousePos = int(mouseData.getX()), int(mouseData.getY())
        else:
            base.win.movePointer(0, base.win.getXSize() // 2, base.win.getYSize() // 2)

            self.__lastMousePos = base.win.getXSize() // 2, base.win.getYSize() // 2

        props = WindowProperties()
        props.setCursorHidden(True)
        base.win.requestProperties(props)
        base.graphicsEngine.openWindows()
        self._startMouseControl()

    def stopMouseControl(self):
        self.ignore('mouse3-up')
        self.ignore('mouse3')
        self.ignore('wheel_up')
        self.ignore('wheel_down')
        self.accept('mouse3', self.startMouseControl)

        if hasattr(base, 'oobeMode') and base.oobeMode:
            return

        if self.__mouseActive:
            self.__mouseActive = False
            self._stopMouseControl()

            base.win.movePointer(0, *self.__mouseOrigin)
            props = WindowProperties()
            props.setCursorHidden(False)
            base.win.requestProperties(props)
            base.graphicsEngine.openWindows()

    def _startMouseControl(self):
        if self.__mouseActive:
            # set thje mouse mode to relative
            props = WindowProperties()
            props.setMouseMode(WindowProperties.MRelative)
            base.win.requestProperties(props)
            self._startReadingMouse()
            self._startMouseUpdateTasks()

    def _stopMouseControl(self):
        props = WindowProperties()
        props.setMouseMode(WindowProperties.MAbsolute)
        base.win.requestProperties(props)
        self._stopReadingMouse()
        self._stopMouseUpdateTasks()

    def _startReadingMouse(self):
        self.addTask(self._mouseReadTask, 'mouseRead')

    def _stopReadingMouse(self):
        self.removeTask('mouseRead')

    def _startMouseUpdateTasks(self):
        """ start all the tasks needed """
        self.addTask(self._mouseUpdateTask, 'mouseUpdates')

    def _stopMouseUpdateTasks(self):
        self.removeTask('mouseUpdates')

    def _mouseReadTask(self, task) -> int:
        # Don't run this if we are in OOBE, or there's no cursor in the window
        if hasattr(base, 'oobeMode') and base.oobeMode:
            self.__mouseDelta = (0, 0)
            return task.cont
        elif not base.mouseWatcherNode.hasMouse():
            self.__mouseDelta = (0, 0)
            return task.cont

        # We have a mouse and aren't in oobe mode? Lets continue
        winSize = base.win.getXSize(), base.win.getYSize()
        mouseData = base.win.getPointer(0)
        # distance between current frame and last frame mouse positions
        self.__mouseDelta = mouseData.getX() - self.__lastMousePos[0], mouseData.getY() - self.__lastMousePos[1]
        if sys.platform == 'win32':
            base.win.movePointer(0, winSize[0] // 2, winSize[1] // 2)
        mouseData = base.win.getPointer(0)
        # save this frame as the 'last' frame
        self.__lastMousePos = mouseData.getX(), mouseData.getY()
        return task.cont

    def _mouseUpdateTask(self, task) -> int:
        if any(self.__mouseDelta):
            dx, dy = self.__mouseDelta

            sensitivity = ClientSettings.CameraSensitivity.get() / 4
            self.activeCamera.setH(self.activeCamera, -dx * sensitivity)
            pitch = bound(self.activeCamera.getP() + -dy * sensitivity, -89.9, 89.9)
            self.activeCamera.setP(pitch)
            self.activeCamera.setR(render, 0) # todo: be able to change roll

        forward = inputState.isSet("forward")
        reverse = inputState.isSet("reverse")
        slideLeft = inputState.isSet("slideLeft")
        slideRight = inputState.isSet("slideRight")

        moveFwdSpeed = (forward and self.moveSpeed or reverse and -self.moveSpeed)
        sideSpeed = (slideLeft and -self.moveSpeed or slideRight and self.moveSpeed)

        dt = globalClock.getDt()
        self.activeCamera.setY(self.activeCamera, moveFwdSpeed*dt)
        self.activeCamera.setX(self.activeCamera, sideSpeed*dt)


        return task.cont
