from direct.gui.DirectGui import *
from direct.fsm import StateData
from direct.directnotify import DirectNotifyGlobal

from panda3d.core import *

from toontown.server.MiniserverIcon import MiniserverIcon
from toontown.toonbase import ToontownGlobals, ClientSettings
from toontown.toonbase import TTLocalizer

import time
import random

from toontown.instancedgames.InstancedGamesGUI import ToonPortrait
from toontown.toon.Toon import Toon
from toontown.toon.ToonDNA import ToonDNA
from toontown.toontowngui.ToontownScrolledFrame import ToontownScrolledFrame
from toontown.toontowngui import ToontownGUIUtils


class InfoGUI(DirectFrame, StateData.StateData):
    notify = DirectNotifyGlobal.directNotify.newCategory('InfoGUI')

    bpGui: NodePath = loader.loadModel('phase_3.5/models/gui/ttoff_m_gui_mgmn_bossParty')

    def __init__(self, avChooser):
        colorPickerModel: NodePath = loader.loadModel("phase_3/models/gui/ttoff_m_gui_opts_colorpicker", allowInstance = True)
        DirectFrame.__init__(self, pos=(0, 0, 0.05), relief=None, image = colorPickerModel.find("**/temp_bg"),
                             image_scale=(2.2, 1, 1.4), image_pos=(0, 0, -0.05),
                             image_color=ToontownGlobals.GlobalDialogColor, text=TTLocalizer.AvatarChooserInfo,
                             text_scale=0.12, text_pos=(-0.45, 0.5), borderWidth=(0.01, 0.01))
        StateData.StateData.__init__(self, 'info-gui-done')

        self.isLoaded = False
        self.setBin('gui-popup', 0)
        self.initialiseoptions(InfoGUI)
        self.avChooser = avChooser

        self.textRolloverColor = Vec4(1, 1, 0, 1)
        self.textDownColor = Vec4(0.5, 0.9, 1, 1)
        self.textDisabledColor = Vec4(0.4, 0.8, 0.4, 1)
        self.descPos = (0.485, 0, -0.2)

        self.server = None
        self.description = None
        self.uptime = None
        self.population = None
        self.logo = None
        self.cancel = None
        self.players = []

        colorPickerModel.removeNode()

    def unload(self):
        self.removeAllTasks()
        if not self.isLoaded:
            return
        self.isLoaded = False

        self.exit()

        self.ignoreAll()
        DirectFrame.destroy(self)

    def load(self):
        if self.isLoaded:
            return
        self.isLoaded = True

        gui = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
        guiButton = loader.loadModel('phase_3/models/gui/quit_button')

        settingsButtonsModel = loader.loadModel('phase_3/models/gui/ttoff_m_gui_opts_buttons', allowInstance = True)
        settingsScrollbarModel = loader.loadModel('phase_3.5/models/gui/ttoff_m_gui_sbk_generic')

        # The name of our server
        self.server = DirectLabel(parent=self, text=base.cr.serverName,
                                  relief=None, pos=(-1.0, 0.0, 0.3), scale=0.06, text_fg=Vec4(0, 0, 0, 1),
                                  text_align=TextNode.ALeft, text_font=ToontownGlobals.getToonFont())

        maxLength = 80
        newDescription = base.cr.serverDescription[:maxLength]
        if len(newDescription) < len(base.cr.serverDescription):
            newDescription = newDescription + TTLocalizer.ServerPageEllipse

        # This server's description
        self.description = DirectLabel(parent=self, text=newDescription,
                                       relief=None, pos=(-1.0, 0.0, 0.2), scale=0.06, text_fg=Vec4(0, 0, 0, 1),
                                       text_wordwrap=18, text_align=TextNode.ALeft,
                                       text_font=ToontownGlobals.getToonFont())

        # How long this server has been up for
        self.uptime = DirectLabel(parent=self, text='', relief=None,
                                  pos=(-1.0, 0.0, 0.0), scale=0.06, text_fg=Vec4(0, 0, 0, 1), text_wordwrap=24,
                                  text_align=TextNode.ALeft, text_font=ToontownGlobals.getToonFont())
        self.calculateUptime()

        # The current population on this server
        self.population = DirectLabel(parent=self, text='', relief=None,
                                      pos=(-1.0, 0.0, -0.1), scale=0.06, text_fg=Vec4(0, 0, 0, 1), text_wordwrap=24,
                                      text_align=TextNode.ALeft, text_font=ToontownGlobals.getToonFont())
        self.calculatePopulation()

        self.playerScroll = ToontownScrolledFrame(
            parent = self,
            relief = DGG.SUNKEN,
            borderWidth = (0.01, 0.01),
            geom = None,
            width = 0.4,
            height = 0.65,
            pos = (0.54, 0, -0.05),
            itemMargin = (0, 0),
            useItemBoundsForPadding = False,
            itemPadding = 0.3,
            frameColor = (0.85, 0.95, 1, 1),
            manageScrollBars = False,
            verticalScroll_frameColor = (0, 0, 0, 0),
            verticalScroll_manageButtons = False,
            verticalScroll_thumb_geom = (
                settingsScrollbarModel.find('**/scrollbar_normal'),
                settingsScrollbarModel.find('**/scrollbar_press'),
                settingsScrollbarModel.find('**/scrollbar_hover')),
            verticalScroll_thumb_geom_scale = ToontownGUIUtils.getImageScale(151, 399, 0.15),
            verticalScroll_thumb_relief = None,
            verticalScroll_resizeThumb = False,
            verticalScroll_decButton_relief = None,
            verticalScroll_incButton_relief = None)

        self.logo = MiniserverIcon(
                parent = self,
                url = base.cr.serverIconPath,
                pos = (-0.375, 0.0, -0.4),
                scale = .15
        )

        # A button to cancel out of the interface
        self.cancel = DirectButton(
            parent=self, 
            relief=None, 
            image = (settingsButtonsModel.find('**/close_button_normal'),
                     settingsButtonsModel.find('**/close_button_click'),
                     settingsButtonsModel.find('**/close_button_hover')),
            image_scale = .14, 
            pos=(-0.95, 0, 0.525),
            command=self.__cancel)

        gui.removeNode()
        guiButton.removeNode()
        settingsButtonsModel.removeNode()
        settingsScrollbarModel.removeNode()
        self.hide()

        self.accept('setAvatarCount', self.calculatePopulation)

    def calculateUptime(self, task=None):
        currentTime = time.time()
        m, s = divmod(currentTime - base.cr.timestamp, 60)
        h, m = divmod(m, 60)
        serverUptime = (str(int(h)), str(int(m)), str(int(s)))
        self.uptime.setText(TTLocalizer.InfoUptime.format(*serverUptime))

        if task:
            return task.again

    def calculatePopulation(self):
        maxPop = base.cr.discordManager.getDistrictLimit()
        currentPop = len(self.players)
        self.population.setText(TTLocalizer.ServerPagePopulation.format(currentPop, maxPop))

    def setOnlineAvatars(self):
        self.playerScroll.clearItems()

        self.players = []
        for toon in list(base.cr.onlineAvatars.values()):
            if not toon.getVisibility():
                continue
            name = toon.getName()
            dnaString = toon.getDNAString()
            hat = toon.getHat()
            glasses = toon.getGlasses()

            frame = DirectFrame(relief = None)
            playerName = OnscreenText(
                parent = frame,
                align = TextNode.ALeft,
                pos = (-.06, 0.02),
                scale = 0.055,
                text = name,
                wordwrap = 7.5)

            portrait: ToonPortrait = ToonPortrait((dnaString, hat, glasses), scale = 0.25)
            portrait.setPos(-.2, 0, 0)
            portrait.reparentTo(frame)

            self.players.append(frame)

        self.playerScroll.addItems(*self.players)

        self.calculatePopulation()

    def enter(self):
        if self.isEntered == 1:
            return
        self.isEntered = 1

        if self.isLoaded == 0:
            self.load()

        base.transitions.fadeScreen(0.5)
        self.doMethodLater(1.0, self.calculateUptime, self.uniqueName('calculateUptime'))

        self.setOnlineAvatars()
        self.accept('onlineAvatarsChanged', self.setOnlineAvatars)

        self.show()

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
