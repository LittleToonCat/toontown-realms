from direct.gui.DirectGui import *
from direct.fsm import StateData
from direct.directnotify import DirectNotifyGlobal

from panda3d.core import *

from toontown.toonbase import ToontownGlobals, ClientSettings
from toontown.toonbase import TTLocalizer

import time

from toontown.toontowngui import ToontownGUIUtils


class WelcomeGUI(DirectFrame, StateData.StateData):
    notify = DirectNotifyGlobal.directNotify.newCategory('Welcome')
    # We don't use the server version bc sometimes we don't have new stuff to convey
    VERSION = "beta1_roadmap"

    def __init__(self, avChooser):
        colorPickerModel: NodePath = loader.loadModel("phase_3/models/gui/ttoff_m_gui_opts_colorpicker", allowInstance = True)
        DirectFrame.__init__(self, pos=(0, 0, 0.05), relief=None, image = colorPickerModel.find("**/temp_bg"),
                             image_scale=(1.8, 1, 1.6), image_pos=(0, 0, -0.05),
                             image_color=ToontownGlobals.GlobalDialogColor, text=TTLocalizer.WelcomePromptTitle,
                             text_scale=0.06, text_pos=(0, 0.625), borderWidth=(0.01, 0.01))
        StateData.StateData.__init__(self, 'welcome-gui-done')
        self.isLoaded = False
        self.setBin('gui-popup', 0)
        self.initialiseoptions(WelcomeGUI)
        self.avChooser = avChooser
        self.textRolloverColor = Vec4(1, 1, 0, 1)
        self.textDownColor = Vec4(0.5, 0.9, 1, 1)
        self.textDisabledColor = Vec4(0.4, 0.8, 0.4, 1)

        colorPickerModel.removeNode()

    def unload(self):
        if not self.isLoaded:
            return
        self.isLoaded = False
        self.exit()
        DirectFrame.destroy(self)

    def load(self):
        if self.isLoaded:
            return

        self.isLoaded = True

        settingsButtonsModel = loader.loadModel('phase_3/models/gui/ttoff_m_gui_opts_buttons')

        self.label = DirectLabel(
                parent = self,
                relief = None,
                pos = (0, 0, 0.55),
                scale = 0.05,
                text_align = TextNode.ACenter,
                text_fg = (0.2, 0.2, 0.2, 1),
                text = 'We are currently in Beta 1. Below is a roadmap of future betas to come!'
        )

        self.betaRoadmap = OnscreenImage(
            parent = self,
            image = loader.loadTexture('phase_3/maps/ttrm_t_welcome_betaRoadmap.png'),
            scale = ToontownGUIUtils.getImageScale(1940, 1581, 0.65),
            pos = (0, 0, -0.14)
        )

        self.acknowledge = DirectButton(
            parent=self, 
            relief=None, 
            image = (settingsButtonsModel.find('**/close_button_normal'),
                     settingsButtonsModel.find('**/close_button_click'),
                     settingsButtonsModel.find('**/close_button_hover')),
            image_scale = .09, 
            pos=(0.775, 0, 0.65),
            command=self.__cancel)

        settingsButtonsModel.removeNode()
        self.hide()

    def enter(self):
        if self.isEntered == 1:
            return
        self.isEntered = 1
        if self.isLoaded == 0:
            self.load()
        base.transitions.fadeScreen(0.5)
        self.show()
        ClientSettings.LastWelcomeVersion.set(self.VERSION)
        if ClientSettings.GUIAnimations.get():
            ToontownGUIUtils.Animations.popup(self, self.getScale()).start()

    def exit(self):
        if self.isEntered == 0:
            return
        self.isEntered = 0
        base.transitions.noTransitions()
        self.ignoreAll()
        self.hide()

    def __cancel(self):
        self.exit()
