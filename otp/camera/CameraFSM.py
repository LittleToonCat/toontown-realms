from direct.fsm.FSM import FSM
from direct.interval.FunctionInterval import Func
from direct.interval.MetaInterval import Sequence
from direct.showbase.InputStateGlobal import inputState

from otp.camera.CameraBase import CameraBase
from otp.camera.CameraEditor import CameraEditor
from otp.camera.CameraFirstPerson import CameraFirstPerson
from otp.camera.CameraGlobals import CameraMode
from otp.camera.CameraLegacy import CameraClassic
from otp.camera.CameraOrbital import CameraOrbital
from otp.camera.CameraShoulder import CameraShoulder
from otp.otpgui.RadialMenu import RadialMenu
from otp.otpbase import OTPGlobals
from toontown.toonbase import ClientSettings, HotkeySettings
from toontown.toontowngui.CameraMenu import CameraMenu


class CameraFSM(FSM):

    def __init__(self, avatar):
        super().__init__('CameraFSM')

        # we dont want it to prevent it when holding shift or something
        self.__rmbToken = inputState.watchWithModifiers('rmb', 'mouse3')

        self.classicCamera = CameraClassic(avatar = avatar)
        self.orbitCamera = CameraOrbital(avatar = avatar)
        self.firstPersonCamera = CameraFirstPerson(avatar = avatar)
        self.shoulderCamera = CameraShoulder(avatar = avatar)
        self.editorCamera = CameraEditor(avatar = avatar)

        self.radialMenu = RadialMenu(
                CameraMenu.menuModel.find('**/cameramenu_orbital'),
                CameraMenu.menuModel.find('**/cameramenu_classic'),
                CameraMenu.menuModel.find('**/cameramenu_firstperson'),
                CameraMenu.menuModel.find('**/cameramenu_shoulder'))

        self.activeCamera = None  # type: CameraBase

        # this will be used when entering and exiting activity specific cameras like the 'editor' camera
        self.__lastWalkCamera = None  # type: CameraMode

        self.activeCameraMode = None

        self.wantCameraTransition = True

    def cleanup(self):
        super().cleanup()
        self.__rmbToken.release()
        del self.__rmbToken
        self.ignoreAll()

    def startMouseControl(self):
        self.activeCamera.startMouseControl()

    def stopMouseControl(self):
        self.activeCamera.stopMouseControl()

    # == Camera Types ==

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    def enterOrbital(self):
        self.initHotkeys()
        self.orbitCamera.request('Active')
        self.activeCamera = self.orbitCamera
        self.activeCameraMode = CameraMode.ORBITAL
        self.__lastWalkCamera = CameraMode.ORBITAL

    def exitOrbital(self):
        self.activeCamera = None
        self.ignoreHotkeys()
        self.orbitCamera.request('Inactive')

    def enterClassic(self):
        self.initHotkeys()
        self.classicCamera.request('Active')
        self.activeCamera = self.classicCamera
        self.activeCameraMode = CameraMode.CLASSIC
        self.__lastWalkCamera = CameraMode.CLASSIC

    def exitClassic(self):
        self.ignoreHotkeys()
        self.classicCamera.request('Inactive')
        self.activeCamera = None

    def enterFirstPerson(self):
        self.initHotkeys()
        self.firstPersonCamera.request('Active')
        self.activeCamera = self.firstPersonCamera
        self.activeCameraMode = CameraMode.FIRSTPERSON
        self.__lastWalkCamera = CameraMode.FIRSTPERSON

    def exitFirstPerson(self):
        self.ignoreHotkeys()
        self.firstPersonCamera.request('Inactive')
        self.activeCamera = None

    def enterShoulder(self):
        self.initHotkeys()
        self.shoulderCamera.request('Active')
        self.activeCamera = self.shoulderCamera
        self.activeCameraMode = CameraMode.MOUSESHOULDER
        self.__lastWalkCamera = CameraMode.MOUSESHOULDER

    def exitShoulder(self):
        self.ignoreHotkeys()
        self.shoulderCamera.request('Inactive')
        self.activeCamera = None

    def enterEditor(self):
        # self.initHotkeys()
        self.editorCamera.request('Active')
        self.activeCamera = self.editorCamera
        self.activeCameraMode = CameraMode.EDITOR

    def exitEditor(self):
        # self.ignoreHotkeys()
        self.editorCamera.request('Inactive')
        self.activeCamera = None
        self.activeCameraMode = None

    def changePreset(self, direction):
        if self.activeCamera:
            self.activeCamera.changePreset(direction)

    def posCamera(self, todo0, todo1):
        pass

    def pageUp(self):
        if self.activeCamera:
            self.activeCamera.pageUp()

    def pageDown(self):
        if self.activeCamera:
            self.activeCamera.pageDown()

    def initHotkeys(self):
        self.accept(HotkeySettings.NextCameraView.getPressed(), self.changePreset, [1])
        self.accept(HotkeySettings.PreviousCameraView.getPressed(), self.changePreset, [-1])
        self.accept(HotkeySettings.CameraModeMenu.getPressed(), self.showRadialMenu)
        self.accept(HotkeySettings.CameraModeMenu.getReleased(), self.hideRadialMenu)
        self.accept(HotkeySettings.ZoomIn.getPressed(), self.pageUp)
        self.accept(HotkeySettings.ZoomOut.getPressed(), self.pageDown)

    def ignoreHotkeys(self):
        self.ignore(HotkeySettings.NextCameraView.getPressed())
        self.ignore(HotkeySettings.PreviousCameraView.getPressed())
        self.ignore(HotkeySettings.CameraModeMenu.getPressed())
        self.ignore(HotkeySettings.CameraModeMenu.getReleased())
        self.ignore(HotkeySettings.ZoomIn.getPressed())
        self.ignore(HotkeySettings.ZoomOut.getPressed())

    def attachCamera(self):
        if self.activeCamera:
            self.activeCamera.attachCamera()

    def showRadialMenu(self):
        if not self.activeCamera:
            return
        if not self.activeCamera.mouseActive:
            self.radialMenu.activate()

    def hideRadialMenu(self):
        if self.radialMenu.isActive:
            result = self.radialMenu.getChoice()
            self.radialMenu.deactivate()
            if result > 3:
                return
            self.changeCameraMode(result)

    def changeCameraMode(self, mode: int, wantTransition: bool = True):
        if mode == self.activeCameraMode:
            return
        modes = ('Orbital', 'Classic', 'FirstPerson', 'Shoulder', 'Editor')
        self.ignoreHotkeys()

        if wantTransition:
            transition = Sequence(
                    base.transitions.getFadeOutIval(0.1),
                    Func(self.request, modes[mode]),
                    base.transitions.getFadeInIval(0.1)
            )
            transition.start()
        else:
            self.request(modes[mode])

    def requestLastWalkCamera(self, wantTransition: bool = True):
        """ For special cases where we are using a special activity camera, and we
        want to switch back to the previous camera mode """
        assert self.__lastWalkCamera is not None, "No last walk camera set. This shouldn't happen"
        self.changeCameraMode(self.__lastWalkCamera, wantTransition)

    def requestLastCamera(self):
        modes = ('Orbital', 'Classic', 'FirstPerson', 'Shoulder')

        self.request(modes[self.activeCameraMode if self.activeCameraMode else ClientSettings.DefaultCameraMode.get()])
