from direct.gui.DirectGui import DGG
from typing import Optional

from direct.gui.DirectButton import DirectButton
from direct.gui.DirectFrame import DirectFrame
from panda3d.core import NodePath, TextNode

from direct.gui.DirectLabel import DirectLabel

from toontown.toonbase import ToontownGlobals, TTLocalizer, ClientSettings
from toontown.toonbase.ToonBaseGlobal import base
from toontown.toontowngui import ToontownGUIUtils
from toontown.toontowngui.ToontownScrolledFrame import ToontownScrolledFrame


class DatapacksListGUI(DirectFrame):
    def __init__(self):
        colorPickerModel: NodePath = base.loader.loadModel("phase_3/models/gui/ttoff_m_gui_opts_colorpicker", allowInstance = True)
        DirectFrame.__init__(self,
                             parent = base.aspect2dp,
                             relief = None,
                             image = colorPickerModel.find("**/temp_bg"),
                             image_scale = (2.2, 1, 1.4),
                             image_color = ToontownGlobals.GlobalDialogColor,
                             text = TTLocalizer.AvatarChooserDatapacks,
                             text_scale = 0.12, text_pos = (0.0, 0.5),
                             borderWidth = (0.01, 0.01))
        self.cancel: Optional[DirectButton] = None
        self.packList: Optional[ToontownScrolledFrame] = None
        self.initialiseoptions(DatapacksListGUI)

        colorPickerModel.removeNode()
        self.isLoaded = False

    def load(self):
        settingsButtonsModel = base.loader.loadModel('phase_3/models/gui/ttoff_m_gui_opts_buttons', allowInstance = True)

        self.cancel = DirectButton(
            parent = self,
            relief = None,
            image = (settingsButtonsModel.find('**/close_button_normal'),
                     settingsButtonsModel.find('**/close_button_click'),
                     settingsButtonsModel.find('**/close_button_hover')),
            image_scale = .14,
            pos = (-0.95, 0, 0.525),
            command = self.exit)

        settingsScrollbarModel = loader.loadModel('phase_3.5/models/gui/ttoff_m_gui_sbk_generic')

        self.packList = ToontownScrolledFrame(
            parent = self,
            relief = DGG.SUNKEN,
            borderWidth = (0.01, 0.01),
            geom = None,
            width = 0.75,
            height = 0.45,
            pos = (0.0, 0, -0.05),
            itemMargin = (-.68, 0),
            useItemBoundsForPadding = False,
            itemPadding = 0.15,
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
        settingsScrollbarModel.removeNode()
        settingsButtonsModel.removeNode()

        self.isLoaded = True

    def enter(self):
        if not self.isLoaded:
            self.load()

        base.transitions.fadeScreen(0.5)
        self.show()

        self.packList.clearItems()

        labels = []
        for pack in base.cr.dataPackMgr.getActivePacks():
            label = DirectLabel(relief = None,
                                text = f'{pack[0]}\n\tby {pack[1]}',
                                text_scale = 0.06,
                                text_align = TextNode.ALeft)
            labels.append(label)

        self.packList.addItems(*labels)

        if ClientSettings.GUIAnimations.get():
            ToontownGUIUtils.Animations.popup(self, self.getScale()).start()

    def unload(self):
        self.removeAllTasks()
        if not self.isLoaded:
            return
        self.isLoaded = False
        self.cancel.destroy()
        self.packList.destroy()
        self.exit()

        self.ignoreAll()
        DirectFrame.destroy(self)

    def exit(self):
        base.transitions.noTransitions()
        self.hide()
