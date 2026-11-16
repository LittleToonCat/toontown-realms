from direct.directnotify import DirectNotifyGlobal
from direct.gui.DirectGui import *
from direct.fsm import StateData

from panda3d.core import *

from otp.camera.CameraGlobals import CameraMode

from toontown.toonbase import ToontownGlobals, ClientSettings
from toontown.toonbase import TTLocalizer

from . import ToontownGUIUtils
from .AnimatedButton import AnimatedButton


class CameraMenu(DirectFrame, StateData.StateData):
    notify = DirectNotifyGlobal.directNotify.newCategory('CameraMenu')
    menuModel = loader.loadModel('phase_3.5/models/gui/ttoff_m_gui_hud_actionBar')

    def __init__(self):
        DirectFrame.__init__(self, parent=aspect2d, relief=None,
                             image=CameraMenu.menuModel.find('**/cameramenu_bg'), scale=0.2,
                             image_scale=(2.9, 1, 1), image_pos=(0, 0, .8),
                             borderWidth=(0.01, 0.01))
        StateData.StateData.__init__(self, 'magic-menu-done')
        self.isLoaded = False
        self.setBin('gui-popup', 0)
        self.initialiseoptions(CameraMenu)

        self.noticeLabel = None
        self.buttons = []
        self.icons = []

    def unload(self):
        # Set loaded status to false
        if not self.isLoaded:
            return
        self.isLoaded = False

        # Exit out before we unload anything
        self.exit()

        # Allow parent class to do everything else
        DirectFrame.destroy(self)

    def load(self):
        # Set loaded status to true
        if self.isLoaded:
            return
        self.isLoaded = True

        # Buttons in the Camera Menu that do stuff
        self.orbitalButton = AnimatedButton(
                image = (CameraMenu.menuModel.find('**/cameramenu_orbital'),
                         CameraMenu.menuModel.find('**/cameramenu_orbital_hover')),
                scale = 0.4, parent = self,
                pos = (-0.9, 0, 0.95),
                text = ('', '', TTLocalizer.CameraModeOrbital, ''),
                text_align = TextNode.ACenter,
                text_scale = 0.6,
                text_fg = (1.0, 1.0, 1.0, 1.0),
                text_shadow = (0, 0, 0, 0.7),
                text_pos = (0, 1),
                textMayChange = 0,
                command = self.handleButton, extraArgs = [CameraMode.ORBITAL])

        self.firstPersonButton = AnimatedButton(
                image = (CameraMenu.menuModel.find('**/cameramenu_firstperson'),
                         CameraMenu.menuModel.find('**/cameramenu_firstperson_hover')),
                scale = 0.4, parent = self,
                pos = (-0.3, 0, 0.95),
                text = ('', '', TTLocalizer.CameraModeFirstPerson, ''),
                text_align = TextNode.ACenter,
                text_scale = 0.6,
                text_fg = (1.0, 1.0, 1.0, 1.0),
                text_shadow = (0, 0, 0, 0.7),
                text_pos = (0, 1),
                textMayChange = 0,
                command = self.handleButton, extraArgs = [CameraMode.FIRSTPERSON])

        self.classicButton = AnimatedButton(
                image = (CameraMenu.menuModel.find('**/cameramenu_classic'),
                         CameraMenu.menuModel.find('**/cameramenu_classic_hover')),
                scale = 0.4, parent = self,
                pos = (0.3, 0, 0.95),
                text = ('', '', TTLocalizer.CameraModeClassic, ''),
                text_align = TextNode.ACenter,
                text_scale = 0.6,
                text_fg = (1.0, 1.0, 1.0, 1.0),
                text_shadow = (0, 0, 0, 0.7),
                text_pos = (0, 1),
                textMayChange = 0,
                command = self.handleButton, extraArgs = [CameraMode.CLASSIC])

        self.shoulderButton = AnimatedButton(
                image = (CameraMenu.menuModel.find('**/cameramenu_shoulder'),
                         CameraMenu.menuModel.find('**/cameramenu_shoulder_hover')),
                scale = 0.4, parent = self,
                pos = (0.9, 0, 0.95),
                text = ('', '', TTLocalizer.CameraModeShoulder, ''),
                text_align = TextNode.ACenter,
                text_scale = 0.6,
                text_fg = (1.0, 1.0, 1.0, 1.0),
                text_shadow = (0, 0, 0, 0.7),
                text_pos = (0, 1),
                textMayChange = 0,
                command = self.handleButton, extraArgs = [CameraMode.MOUSESHOULDER])

        self.hide()
        self.accept('toon-caged', self.exit)

    def enter(self):
        # If our UI is hidden, don't even bother trying to open the Camera Menu
        if aspect2d.isHidden():
            return

        # Set entered status to true
        if self.isEntered == 1:
            return
        self.isEntered = 1

        # If we haven't loaded yet, do so
        if self.isLoaded == 0:
            self.load()

        # Show the interface
        self.show()

        if ClientSettings.GUIAnimations.get():
            ToontownGUIUtils.Animations.popup(self, self.getScale()).start()

    def exit(self):
        # Set entered status to false
        if self.isEntered == 0:
            return
        self.isEntered = 0

        # Ignore all events
        self.ignoreAll()

        # Hide the interface
        self.hide()

    def handleButton(self, cameraMode):
        if base.localAvatar.cameraFSM.activeCameraMode == CameraMode.EDITOR:
            return
        base.localAvatar.cameraFSM.changeCameraMode(cameraMode)
