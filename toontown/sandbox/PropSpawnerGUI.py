"""
Prop Spawner - Main GUI
"""
from typing import List, Optional, Dict

from direct.gui import DirectGuiGlobals
from direct.gui.DirectGui import *
from direct.interval.FunctionInterval import Func
from direct.interval.LerpInterval import LerpPosInterval
from direct.interval.MetaInterval import Sequence
from direct.task import Task
from panda3d.core import Vec3, NodePath, TextNode, VBase4, PointerData, BoundingVolume, LVector3f, Vec3F, AudioSound

from direct.showbase.ShowBaseGlobal import hidden

from otp.camera.CameraGlobals import CameraMode
from otp.otpbase import OTPGlobals
from otp.otpbase.PythonUtil import bound
from otp.otpgui import OTPGUIUtils
from toontown.moviemaker.MovieMakerGUI import BROWSER_OPEN, MovieMakerGUI, BROWSER_HIDDEN
from toontown.sandbox import PropGlobals
from toontown.sandbox.DistributedBuildLot import ScrollableDropdown
from toontown.sandbox.PropGlobals import PropCategory
from toontown.sandbox.PropUI import NumberInput, ToggleSwitch
from toontown.sandbox.PropUIGlobals import *
from toontown.toonbase import ToontownGlobals, TTLocalizer, ClientSettings, HotkeySettings
from toontown.toonbase.ControlManager import ControlManager
from toontown.toonbase.ToonBaseGlobal import base
from toontown.toontowngui.AnimatedButton import AnimatedButton
from toontown.sandbox.PropSpawnerItem import PropSpawnerItem
from toontown.toontowngui.ToontownScrolledGridFrame import ToontownScrolledGridFrame


class PropSpawnerGUI(DirectFrame):
    page = 0
    propList = list(PropGlobals.PropList.keys())
    totalPages = len(propList) // 35
    category = PropCategory.All
    open = False
    SearchHasFocus = False
    PlacingProp = False
    OffSwitch = (
        MovieMakerGUI.gui.find('**/toggle_off'),
        MovieMakerGUI.gui.find('**/toggle_off'),
        MovieMakerGUI.gui.find('**/toggle_off_h'),
    )
    OnSwitch = (
        MovieMakerGUI.gui.find('**/toggle_on'),
        MovieMakerGUI.gui.find('**/toggle_on'),
        MovieMakerGUI.gui.find('**/toggle_on_h'),
    )

    OpenSound: AudioSound = base.loader.loadSfx('phase_3/audio/sfx/GUI_create_toon_bodyshop.ogg')

    def __init__(self, generator, **kwargs):
        optiondefs = (
            ('pos', (0, 0, 0), None),
            ('relief', None, None),
        )

        self.defineoptions(kwargs, optiondefs)
        DirectFrame.__init__(self, base.a2dBottomLeft)
        self.initialiseoptions(PropSpawnerGUI)
        self.propButtons: List[PropSpawnerItem] = []

        self.generator = generator
        self.snapOpen: bool = False
        self.settingsOpen: bool = False
        self.adminOpen: bool = False
        self.shareOpen: bool = False
        self.browserVisible: bool = True

        base.setCellsAvailable([*base.leftCells, base.bottomCells[0], base.bottomCells[1], base.bottomCells[2]], 0)

        ## Lock the Toon down
        # base.localAvatar.setLocked(True)
        # if base.cr.playGame.getPlace().getState() != 'battle':
        #    base.cr.playGame.getPlace().setState('stopped')
        scrollbar = base.loader.loadModel('phase_3.5/models/gui/ttoff_m_gui_sbk_generic', allowInstance = True)

        self.browser = ToontownScrolledGridFrame(
            parent = self,
            pos = BROWSER_OPEN,
            relief = None,
            image = MovieMakerGUI.gui.find('**/browser_with_tab'),
            image_scale = OTPGUIUtils.getImageScale(1582, 750, 0.885),
            image_pos = (0, 0, 0.046),
            image_color = VBase4(1.0, 1.0, 1.0, 1.0),
            height = .313,
            width = .88,
            itemPadding = .154,
            itemMargin = (-.5415, -.16),
            itemsPerRow = 10,
            manageScrollBars = False,
            verticalScroll_thumb_geom = (
                scrollbar.find('**/scrollbar_normal'),
                scrollbar.find('**/scrollbar_press'),
                scrollbar.find('**/scrollbar_hover')),
            verticalScroll_thumb_geom_scale = OTPGUIUtils.getImageScale(151, 399, 0.15),
            verticalScroll_thumb_relief = None,
            verticalScroll_resizeThumb = False,
            verticalScroll_manageButtons = False,
        )
        scrollbar.removeNode()
        self.browserTop = DirectFrame(
            relief = None,
            parent = self.browser,
            pos = Vec3(0.64, 0, 0.39),
            scale = 0.12
        )

        self.searchContainer = DirectFrame(
            relief = None,
            parent = self.browser,
            pos = Vec3(0.158, 0, 0.385)
        )
        self.searchContainer.hide()

        self.closeButton = DirectButton(
            relief = None,
            parent = self.browserTop,
            pos = POS_TOP_CLOSE,
            scale = 0.55,
            image = (
                MovieMakerGUI.gui.find('**/tab_close'),
                MovieMakerGUI.gui.find('**/tab_close_p'),
                MovieMakerGUI.gui.find('**/tab_close_h'),
            ),
            command = self.generator.closeNewPropWindow
        )

        self.toggleBrowserButton = DirectButton(
            relief = None,
            parent = self.browserTop,
            pos = (1.65, 0, 0),
            scale = 0.55,
            image = (
                MovieMakerGUI.gui.find('**/minimize'),
                MovieMakerGUI.gui.find('**/minimize_p'),
                MovieMakerGUI.gui.find('**/minimize_h'),
            ),
            command = self.toggleBrowserVisibility
        )

        self.toggleBrowserButton.bind(DGG.ENTER, lambda e: self.showTooltip(TTLocalizer.PropGeneratorToggleBrowser))
        self.toggleBrowserButton.bind(DGG.EXIT, lambda e: self.hideTooltip())

        self.snapSettingsButton = DirectButton(
            relief = None,
            parent = self.browserTop,
            pos = POS_TOP_SNAP_SETTINGS,
            scale = 0.55,
            image = (
                MovieMakerGUI.gui.find('**/tab_snap'),
                MovieMakerGUI.gui.find('**/tab_snap_p'),
                MovieMakerGUI.gui.find('**/tab_snap_h'),
            ),
            command = self.toggleSnapSettings
        )

        self.snapSettingsButton.bind(DGG.ENTER, lambda e: self.showTooltip(TTLocalizer.PropGeneratorSnapSettings))
        self.snapSettingsButton.bind(DGG.EXIT, lambda e: self.hideTooltip())

        self.snapSettingsUI = DirectFrame(
            relief = None,
            parent = self.browser,
            scale = 0.9,
            image = MovieMakerGUI.gui.find('**/settings_popup_bg'),
            image_scale = OTPGUIUtils.getImageScale(702, 1078, .85),
            image_pos = (0, 0, -.025)
        )
        self.snapSettingsUI.setPos(self.snapSettingsButton, Vec3(0, 0, 6.3))

        self.snapSettingsLabel = OnscreenText(
            parent = self.snapSettingsUI,
            text = TTLocalizer.PropGeneratorSnapSettings,
            pos = (0, 0.31),
            scale = 0.045,
            fg = (1.0, 1.0, 1.0, 1.0),
            shadow = VBase4(0.0, 0.0, 0.0, 0.7),
        )

        self.togglePosSnapButton = ToggleSwitch(
            relief = None,
            parent = self.snapSettingsUI,
            text = TTLocalizer.PropGeneratorPosSnap,
            text_pos = (-5.2, -0.17),
            text_align = TextNode.ALeft,
            text_scale = 0.7,
            text_fg = (1.0, 1.0, 1.0, 1.0),
            scale = 0.06,
            pos = (0.125, 0, 0.22),
            onChange = self.generator.toggleSnap,
            onChangeExtraArgs = (0,),
            toggled = self.generator.gridSnapState[0]
        )

        self.posSnapHorizontal = NumberInput(
            parent = self.snapSettingsUI,
            pos = (-0.1, 0, 0.10),
            scale = 0.6,
            incrementType = 'MUL',
            incrementScale = 2,
            minMax = (0.625, 80),
            startValue = self.generator.gridSnap[0],
            onChange = self.generator.setSnapSize,
            onChangeExtraArgs = (0,)
        )

        self.accept(HotkeySettings.PropGeneratorDecreaseGridSize.getPressed(), self.posSnapHorizontal.decrement)
        self.accept(HotkeySettings.PropGeneratorIncreaseGridSize.getPressed(), self.posSnapHorizontal.increment)

        self.posSnapHorizontalLabel = OnscreenText(
            parent = self.posSnapHorizontal,
            scale = 0.04,
            text = TTLocalizer.PropGeneratorPosSnapHorizontal,
            fg = (1.0, 1.0, 1.0, 1.0),
            pos = (0, 0.1)
        )

        self.posSnapHeight = NumberInput(
            parent = self.snapSettingsUI,
            pos = (0.1, 0, 0.10),
            scale = 0.6,
            incrementType = 'MUL',
            incrementScale = 2,
            minMax = (0.5, 64),
            startValue = self.generator.gridSnap[2],
            onChange = self.generator.setSnapSize,
            onChangeExtraArgs = (2,)
        )

        self.posSnapHeightLabel = OnscreenText(
            parent = self.posSnapHeight,
            scale = 0.04,
            text = TTLocalizer.PropGeneratorPosSnapVertical,
            fg = (1.0, 1.0, 1.0, 1.0),
            pos = (0, 0.1)
        )

        self.toggleRotSnapButton = ToggleSwitch(
            parent = self.snapSettingsUI,
            text = TTLocalizer.PropGeneratorRotSnap,
            text_pos = (-5.2, -0.17),
            text_align = TextNode.ALeft,
            text_scale = 0.7,
            text_fg = (1.0, 1.0, 1.0, 1.0),
            scale = 0.06,
            pos = (0.125, 0, 0.02),
            pressEffect = False,
            onChange = self.generator.toggleSnap,
            onChangeExtraArgs = (1,),
            toggled = self.generator.gridSnapState[1]
        )

        self.rotSnapHorizontal = NumberInput(
            parent = self.snapSettingsUI,
            pos = (0, 0, -0.06),
            scale = 0.6,
            incrementType = 'MUL',
            incrementScale = 2,
            minMax = (6.225, 180),
            startValue = self.generator.gridSnap[1],
            onChange = self.generator.setSnapSize,
            onChangeExtraArgs = (1,)
        )

        self.toggleGridButton = ToggleSwitch(
            parent = self.snapSettingsUI,
            text = TTLocalizer.PropGeneratorGridEnable,
            text_pos = (-5.2, -0.17),
            text_align = TextNode.ALeft,
            text_scale = 0.7,
            text_fg = (1.0, 1.0, 1.0, 1.0),
            scale = 0.06,
            pos = (0.125, 0, -0.16),
            onChange = self.generator.toggleSnap,
            onChangeExtraArgs = (2,),
            toggled = self.generator.gridSnapState[2]
        )

        self.toggleHeightLockButton = ToggleSwitch(
            parent = self.snapSettingsUI,
            text = TTLocalizer.PropGeneratorLockHeight,
            text_pos = (-5.2, -0.17),
            text_align = TextNode.ALeft,
            text_scale = 0.7,
            text_fg = (1.0, 1.0, 1.0, 1.0),
            scale = 0.06,
            pos = (0.125, 0, -0.26),
            onChange = self.generator.toggleHeightLock,
            toggled = self.generator.lockHeight
        )

        self.snapSettingsUI.reparentTo(hidden)

        self.settingsButton = DirectButton(
            relief = None,
            parent = self.browserTop,
            pos = POS_TOP_SETTINGS,
            scale = 0.55,
            image = (
                MovieMakerGUI.gui.find('**/tab_settings'),
                MovieMakerGUI.gui.find('**/tab_settings_p'),
                MovieMakerGUI.gui.find('**/tab_settings_h'),
            ),
            command = self.toggleSettings
        )

        self.settingsButton.bind(DGG.ENTER, lambda e: self.showTooltip(TTLocalizer.PropGeneratorSettings))
        self.settingsButton.bind(DGG.EXIT, lambda e: self.hideTooltip())

        self.settingsUI = DirectFrame(
            relief = None,
            parent = self.browser,
            scale = 0.9,
            image = MovieMakerGUI.gui.find('**/settings_popup_bg'),
            image_scale = OTPGUIUtils.getImageScale(702, 1078, .85),
            image_pos = (0, 0, -.025)
        )

        self.settingsUI.setPos(self.settingsButton, Vec3(0, 0, 6.3))

        self.settingsLabel = OnscreenText(
            parent = self.settingsUI,
            text = TTLocalizer.PropGeneratorSettings,
            pos = (0, 0.31),
            scale = 0.045,
            fg = (1.0, 1.0, 1.0, 1.0),
            shadow = VBase4(0.0, 0.0, 0.0, 0.7),
        )

        self.defaultStreetTexture = ScrollableDropdown(
            scale = 0.08,
            pos = (0, 0, 0.18),
            parent = self.settingsUI,
            label = TTLocalizer.PropGeneratorDefaultPrefix + TTLocalizer.PropEditorStreetLabelStreet,
            items = TTLocalizer.PropEditorStreetTypes,
            selectedItem = 0,
            labelPos = (0, 0.65),
            labelAlign = TextNode.ACenter,
            xOffset = 0,
            onChange = lambda _: self.generator.selectProp(self.generator.currentProp)
        )

        self.defaultCurbTexture = ScrollableDropdown(
            scale = 0.08,
            pos = (0, 0, 0.04),
            parent = self.settingsUI,
            label = TTLocalizer.PropGeneratorDefaultPrefix + TTLocalizer.PropEditorStreetLabelCurb,
            items = TTLocalizer.PropEditorSideTypes,
            selectedItem = 0,
            labelPos = (0, 0.65),
            labelAlign = TextNode.ACenter,
            xOffset = 0,
            onChange = lambda _: self.generator.selectProp(self.generator.currentProp)
        )

        self.defaultSidewalkTexture = ScrollableDropdown(
            scale = 0.08,
            pos = (0, 0, -0.1),
            parent = self.settingsUI,
            label = TTLocalizer.PropGeneratorDefaultPrefix + TTLocalizer.PropEditorStreetLabelSidewalk,
            items = TTLocalizer.PropEditorSideTypes,
            selectedItem = 0,
            labelPos = (0, 0.65),
            labelAlign = TextNode.ACenter,
            xOffset = 0,
            onChange = lambda _: self.generator.selectProp(self.generator.currentProp)
        )

        self.noclipCommandButton = DirectButton(
            parent = self.settingsUI,
            relief = None,
            scale = 0.08,
            pos = (0, 0, -0.24),
            image = (
                MovieMakerGUI.gui.find('**/dropdown_button_item'),
                MovieMakerGUI.gui.find('**/dropdown_button_item'),
                MovieMakerGUI.gui.find('**/dropdown_button_item_h')
            ),
            image_scale = OTPGUIUtils.getImageScale(682, 133),
            text = TTLocalizer.PropGeneratorSettingsToggleNoclip,
            text_scale = 0.4,
            text_pos = (0, -.12),
            command = lambda: base.cr.magicWordManager.handleMagicWord(f'{base.cr.magicWordManager.chatPrefix}ToggleNoClip')
        )

        self.settingsUI.reparentTo(base.hidden)

        # ===Admin===
        self.adminButton = DirectButton(
            relief = None,
            parent = self.browserTop,
            pos = POS_TOP_ADMIN,
            scale = 0.55,
            image = (
                MovieMakerGUI.gui.find('**/tab_admin'),
                MovieMakerGUI.gui.find('**/tab_admin_p'),
                MovieMakerGUI.gui.find('**/tab_admin_h'),
                MovieMakerGUI.gui.find('**/tab_admin')
            ),
            image3_color = VBase4(1, 1, 1, 0.5),
            command = self.toggleAdmin
        )
        if base.localAvatar.getAccessLevel() < OTPGlobals.AccessLevelName2Int.get('BUILDER'):
            self.adminButton['state'] = DGG.DISABLED

            self.adminButton.bind(DGG.ENTER, lambda e: self.showTooltip(TTLocalizer.PropGeneratorAdminSettingsNoPerm))
        else:
            self.adminButton.bind(DGG.ENTER, lambda e: self.showTooltip(TTLocalizer.PropGeneratorAdminSettings))
        self.adminButton.bind(DGG.EXIT, lambda e: self.hideTooltip())

        self.adminUI = DirectFrame(
            relief = None,
            parent = self.browser,
            scale = 0.9,
            image = MovieMakerGUI.gui.find('**/settings_popup_bg'),
            image_scale = OTPGUIUtils.getImageScale(702, 1078, .85),
            image_pos = (0, 0, -.025)
        )

        self.adminUI.setPos(self.adminButton, Vec3(0, 0, 6.3))
        self.adminUI.reparentTo(hidden)
        self.adminLabel = OnscreenText(
            parent = self.adminUI,
            text = TTLocalizer.PropGeneratorAdminSettings,
            pos = (0, 0.31),
            scale = 0.045,
            fg = (1.0, 1.0, 1.0, 1.0),
            shadow = VBase4(0.0, 0.0, 0.0, 0.7),
        )
        self.adminCurrentZoneLabel = OnscreenText(
            parent = self.adminUI,
            text = TTLocalizer.PropGeneratorAdminCurrentZoneTitle,
            pos = (0, 0.25),
            scale = 0.03,
        )
        self.adminClearZoneButton = DirectButton(
            parent = self.adminUI,
            relief = None,
            scale = 0.08,
            pos = (0, 0, .2),
            image = (
                MovieMakerGUI.gui.find('**/dropdown_button_item'),
                MovieMakerGUI.gui.find('**/dropdown_button_item'),
                MovieMakerGUI.gui.find('**/dropdown_button_item_h')
            ),
            image_scale = OTPGUIUtils.getImageScale(682, 133),
            text = TTLocalizer.PropGeneratorAdminClearZone,
            text_scale = 0.4,
            text_pos = (0, -.12),
            command = self.generator.confirmDeletePropsInZone
        )

        self.adminLockZoneButton = DirectButton(
            parent = self.adminUI,
            relief = None,
            scale = 0.08,
            pos = (0, 0, .1),
            image = (
                MovieMakerGUI.gui.find('**/dropdown_button_item'),
                MovieMakerGUI.gui.find('**/dropdown_button_item'),
                MovieMakerGUI.gui.find('**/dropdown_button_item_h')
            ),
            image_scale = OTPGUIUtils.getImageScale(682, 133),
            text = TTLocalizer.PropGeneratorAdminToggleLock,
            text_scale = 0.4,
            text_pos = (0, -.12),
            command = self.generator.confirmLockPropsInZone
        )

        self.adminRealmLabel = OnscreenText(
            parent = self.adminUI,
            text = TTLocalizer.PropGeneratorAdminRealmTitle,
            pos = (0, 0),
            scale = 0.03,
        )

        self.adminClearRealmButton = DirectButton(
            parent = self.adminUI,
            relief = None,
            scale = 0.08,
            pos = (0, 0, -0.05),
            image = (
                MovieMakerGUI.gui.find('**/dropdown_button_item'),
                MovieMakerGUI.gui.find('**/dropdown_button_item'),
                MovieMakerGUI.gui.find('**/dropdown_button_item_h')
            ),
            image_scale = OTPGUIUtils.getImageScale(682, 133),
            text = TTLocalizer.PropGeneratorAdminClearRealm,
            text_scale = 0.4,
            text_pos = (0, -.12),
            command = self.generator.confirmDeleteAllProps
        )

        self.adminLockRealmButton = DirectButton(
            parent = self.adminUI,
            relief = None,
            scale = 0.08,
            pos = (0, 0, -0.15),
            image = (
                MovieMakerGUI.gui.find('**/dropdown_button_item'),
                MovieMakerGUI.gui.find('**/dropdown_button_item'),
                MovieMakerGUI.gui.find('**/dropdown_button_item_h')
            ),
            image_scale = OTPGUIUtils.getImageScale(682, 133),
            text = TTLocalizer.PropGeneratorAdminToggleLock,
            text_scale = 0.4,
            text_pos = (0, -.12),
            command = self.generator.confirmLockProps
        )

        # ===Save/Load===
        self.shareButton = DirectButton(
            relief = None,
            parent = self.browserTop,
            pos = POS_TOP_SHARE,
            scale = 0.55,
            image = (
                MovieMakerGUI.gui.find('**/tab_save'),
                MovieMakerGUI.gui.find('**/tab_save_p'),
                MovieMakerGUI.gui.find('**/tab_save_h'),
            ),
            command = self.toggleShare
        )
        self.shareButton.bind(DGG.ENTER, lambda e: self.showTooltip(TTLocalizer.PropGeneratorShare))
        self.shareButton.bind(DGG.EXIT, lambda e: self.hideTooltip())

        self.shareUI = DirectFrame(
            relief = None,
            parent = self.browser,
            scale = 0.9,
            image = MovieMakerGUI.gui.find('**/settings_popup_bg'),
            image_scale = OTPGUIUtils.getImageScale(702, 1078, .85),
            image_pos = (0, 0, -.025)
        )

        self.shareUI.setPos(self.shareButton, Vec3(0, 0, 6.3))
        self.shareUI.reparentTo(hidden)

        self.shareLabel = OnscreenText(
            parent = self.shareUI,
            text = TTLocalizer.PropGeneratorShare,
            pos = (0, 0.31),
            scale = 0.045,
            fg = (1.0, 1.0, 1.0, 1.0),
            shadow = VBase4(0.0, 0.0, 0.0, 0.7),
        )

        self.saveButton = DirectButton(
            parent = self.shareUI,
            relief = None,
            scale = 0.08,
            pos = (0, 0, .2),
            image = (
                MovieMakerGUI.gui.find('**/dropdown_button_item'),
                MovieMakerGUI.gui.find('**/dropdown_button_item'),
                MovieMakerGUI.gui.find('**/dropdown_button_item_h')
            ),
            image_scale = OTPGUIUtils.getImageScale(682, 133),
            text = TTLocalizer.PropGeneratorDump,
            text_scale = 0.4,
            text_pos = (0, -.12),
            command = self.generator.savePropsToJson
        )

        self.loadButton = DirectButton(
            parent = self.shareUI,
            relief = None,
            scale = 0.08,
            pos = (0, 0, .1),
            image = (
                MovieMakerGUI.gui.find('**/dropdown_button_item'),
                MovieMakerGUI.gui.find('**/dropdown_button_item'),
                MovieMakerGUI.gui.find('**/dropdown_button_item_h')
            ),
            image_scale = OTPGUIUtils.getImageScale(682, 133),
            text = TTLocalizer.PropGeneratorLoad,
            text_scale = 0.4,
            text_pos = (0, -.12),
            command = self.generator.loadPropsFromJson
        )

        cdrGui: NodePath = base.loader.loadModel('phase_3.5/models/gui/tt_m_gui_sbk_codeRedemptionGui')

        self.searchBar = DirectEntry(
            parent = self.searchContainer,
            text_align = TextNode.ACenter,
            relief = None,
            image = cdrGui.find('**/tt_t_gui_sbk_cdrCodeBox'),
            image_scale = (1.1, 1, 1),
            text_scale = 0.06, width = 12,
            textMayChange = 1,
            pos = (0, 0, 0),
            scale = 0.4,
            backgroundFocus = 0,
            focusInCommand = self.__toggleSearchFocus,
            focusInExtraArgs = [True],
            focusOutCommand = self.__toggleSearchFocus,
            focusOutExtraArgs = [False]
        )
        self.searchBar.bind(DGG.TYPE, self.__updateSearch)
        self.searchBar.bind(DGG.ERASE, self.__updateSearch)
        self.categoryButtons: Dict[str, AnimatedButton] = {}
        for i, category in enumerate(PropCategory):
            icn = AnimatedButton(
                parent = base.a2dBottomLeft,
                image = PropGlobals.PropUi.find(f'**/category_{category.name.lower()}'),
                image_scale = 0.065,
                image3_color = (0.8, 0.8, 0.8, 0.5),
                pos = (0.068, 0, .649 - i / 15),
                command = self.applyFilter,
                extraArgs = [category],
                hoverEvent = self.showTooltip,
                hoverEventArgs = [category.name],
                unHoverEvent = self.hideTooltip
            )
            icn.wrtReparentTo(self.browser)

            self.categoryButtons[category] = icn
        if self.category == PropCategory.Search:
            self.applyFilter(PropCategory.All)
        else:
            self.loadProps()

        cdrGui.removeNode()

        self.selectedPropHolder: NodePath = DirectFrame(
            relief = None,
            parent = self.browser,
            image = MovieMakerGUI.gui.find('**/browser_placing'),
            image_pos = (1.1, 0, 0),
            image_scale = OTPGUIUtils.getImageScale(810, 195, 0.6)
        )
        self.selectedPropHolder.setScale(0.3)
        self.selectedPropHolder.setPos(-0.85, 0, 0.444)
        self.selectedPropText: OnscreenText = OnscreenText(
            parent = self.selectedPropHolder,
            pos = (0, 0.1),
            align = TextNode.ALeft,
            scale = 0.07,
            text = TTLocalizer.PropGeneratorCurrentlyPlacing)
        self.selectedPropName: OnscreenText = OnscreenText(
            parent = self.selectedPropHolder,
            pos = (0, -0.13),
            align = TextNode.ALeft,
            scale = 0.12,
            wordwrap = 15,
            text = 'propgenui3 (shouldnt see this)')
        self.stopPlacingButton = DirectButton(
            relief = None,
            parent = self.selectedPropHolder,
            pos = (2.33, 0, 0.3),
            scale = 0.25,
            image = (
                MovieMakerGUI.gui.find('**/tab_close'),
                MovieMakerGUI.gui.find('**/tab_close_p'),
                MovieMakerGUI.gui.find('**/tab_close_h'),
            ),
            command = self.stopPlacing
        )

        if not PropSpawnerGUI.PlacingProp:
            self.selectedPropHolder.hide()

        self.controlsLabel = OnscreenText(
            parent = self.browser,
            text = ControlManager.parseHotkeyString(TTLocalizer.PropGeneratorControls, useGlyphs = True),
            scale = 0.04,
            fg = (1.0, 1.0, 1.0, 1.0),
            shadow = (0.0, 0.0, 0.0, 0.6),
            pos = (-.86, .98),
            align = TextNode.ALeft
        )

        self.hoverTooltip: Optional[DirectLabel] = None
        PropSpawnerGUI.open = True
        PropSpawnerGUI.OpenSound.play()

        self.setScale(ClientSettings.PropSpawnerGUIScale.get())

        base.graphicsEngine.renderFrame()
        base.localAvatar.cameraFSM.changeCameraMode(CameraMode.EDITOR)

    def toggleBrowserVisibility(self):
        self.browserVisible = not self.browserVisible

        def setBtnState(state: str):
            self.toggleBrowserButton['state'] = state

        Sequence(
            Func(setBtnState, DGG.DISABLED),
            LerpPosInterval(self.browser, 0.1, BROWSER_OPEN if self.browserVisible else BROWSER_HIDDEN, blendType = 'easeInOut'),
            Func(setBtnState, DGG.NORMAL),
        ).start()

    def toggleSnapSettings(self):
        if self.settingsOpen:
            self.toggleSettings()
        if self.adminOpen:
            self.toggleAdmin()
        if self.shareOpen:
            self.toggleShare()

        self.snapSettingsUI.reparentTo(base.hidden if self.snapOpen else self.browser)
        self.snapOpen = not self.snapOpen

        self.snapSettingsButton['image'] = (
            MovieMakerGUI.gui.find('**/tab_snap_p'),
            MovieMakerGUI.gui.find('**/tab_snap_p'),
            MovieMakerGUI.gui.find('**/tab_snap_h'),
        ) if self.snapOpen else (
            MovieMakerGUI.gui.find('**/tab_snap'),
            MovieMakerGUI.gui.find('**/tab_snap_p'),
            MovieMakerGUI.gui.find('**/tab_snap_h'),
        )

    def toggleSettings(self):
        if self.snapOpen:
            self.toggleSnapSettings()
        if self.adminOpen:
            self.toggleAdmin()
        if self.shareOpen:
            self.toggleShare()

        self.settingsUI.reparentTo(hidden if self.settingsOpen else self.browser)
        self.settingsOpen = not self.settingsOpen

        self.settingsButton['image'] = (
            MovieMakerGUI.gui.find('**/tab_settings_p'),
            MovieMakerGUI.gui.find('**/tab_settings_p'),
            MovieMakerGUI.gui.find('**/tab_settings_h'),
        ) if self.settingsOpen else (
            MovieMakerGUI.gui.find('**/tab_settings'),
            MovieMakerGUI.gui.find('**/tab_settings_p'),
            MovieMakerGUI.gui.find('**/tab_settings_h'),
        )

    def toggleAdmin(self):
        if self.settingsOpen:
            self.toggleSettings()
        if self.snapOpen:
            self.toggleSnapSettings()
        if self.shareOpen:
            self.toggleShare()

        self.adminUI.reparentTo(base.hidden if self.adminOpen else self.browser)
        self.adminOpen = not self.adminOpen

        self.adminButton['image'] = (
            MovieMakerGUI.gui.find('**/tab_admin_p'),
            MovieMakerGUI.gui.find('**/tab_admin_p'),
            MovieMakerGUI.gui.find('**/tab_admin_h'),
        ) if self.adminOpen else (
            MovieMakerGUI.gui.find('**/tab_admin'),
            MovieMakerGUI.gui.find('**/tab_admin_p'),
            MovieMakerGUI.gui.find('**/tab_admin_h'),
        )

    def toggleShare(self):
        if self.settingsOpen:
            self.toggleSettings()
        if self.snapOpen:
            self.toggleSnapSettings()
        if self.adminOpen:
            self.toggleAdmin()

        self.shareUI.reparentTo(base.hidden if self.shareOpen else self.browser)
        self.shareOpen = not self.shareOpen

        self.shareButton['image'] = (
            MovieMakerGUI.gui.find('**/tab_save_p'),
            MovieMakerGUI.gui.find('**/tab_save_p'),
            MovieMakerGUI.gui.find('**/tab_save_h'),
        ) if self.shareOpen else (
            MovieMakerGUI.gui.find('**/tab_save'),
            MovieMakerGUI.gui.find('**/tab_save_p'),
            MovieMakerGUI.gui.find('**/tab_save_h'),
        )

    def changePage(self, off = 0):
        base.messenger.send('wakeup')
        PropSpawnerGUI.page = bound(self.page + off, 0, self.totalPages)
        self.loadProps()

    def loadProps(self):
        self.__updatePageNumber()
        for btn in self.propButtons:
            btn.destroy()
            del btn

        self.browser.clearItems()

        self.propButtons = []
        pos = Vec3(-0.9, 0, .6)
        for i, prop in enumerate(self.propList):
            btn = PropSpawnerItem(self, prop, parent = self, pos = pos)

            self.propButtons.append(btn)

        self.browser.addItems(*self.propButtons)

    def applyFilter(self, category: PropCategory):
        self.__focusOutSearchBar()
        self.searchContainer.hide()
        self.browser['image'] = MovieMakerGUI.gui.find('**/browser_with_tab')
        if category == PropCategory.All:
            PropSpawnerGUI.propList = list(PropGlobals.PropList.keys())
        elif category == PropCategory.Favorites:
            PropSpawnerGUI.propList = []  # todo: save and load favotires
            favorites: List[str] = ClientSettings.FavoriteProps.get()
            for i in favorites:
                if i in PropGlobals.PropList:
                    self.propList.append(i)
        elif category == PropCategory.Search:
            PropSpawnerGUI.propList = list(PropGlobals.PropList.keys())
            self.browser['image'] = MovieMakerGUI.gui.find('**/browser_with_tab_search')
            self.searchContainer.show()
        else:
            PropSpawnerGUI.propList = []
            for i in PropGlobals.PropCategories[category]:
                if i in PropGlobals.PropList:
                    self.propList.append(i)
        PropSpawnerGUI.totalPages = len(self.propList) // 35
        PropSpawnerGUI.page = 0
        PropSpawnerGUI.category = category
        self.loadProps()

    def __updateSearch(self, e):
        PropSpawnerGUI.propList = []
        searchTerm = self.searchBar.get().lower()
        for prop in PropGlobals.PropList:
            if searchTerm in prop.lower():
                self.propList.append(prop)

        PropSpawnerGUI.page = 0
        if len(self.propList) == 0:
            PropSpawnerGUI.totalPages = 0
        else:
            PropSpawnerGUI.totalPages = len(self.propList) // 35

        self.loadProps()

    def __focusOutSearchBar(self):
        self.searchBar['focus'] = 0
        self.searchBar.setFocus()
        self.__toggleSearchFocus(False)

    def __toggleSearchFocus(self, state):
        if state:
            base.localAvatar.chatMgr.disableBackgroundFocus()
            base.controlManager.disableAlphaNumericHotkeys = True
        else:
            base.localAvatar.chatMgr.setBackgroundFocus(base.controlManager.getChatDisabled(), True)
            base.controlManager.disableAlphaNumericHotkeys = False

    def __updatePageNumber(self):
        for btn in self.categoryButtons:
            self.categoryButtons[btn]['state'] = DGG.DISABLED if btn == self.category else DGG.NORMAL

    def select(self, prop):
        PropSpawnerGUI.PlacingProp = True
        self.selectedPropHolder.show()
        self.generator.selectProp(list(PropGlobals.PropList.keys()).index(prop))

    def stopPlacing(self):
        PropSpawnerGUI.PlacingProp = False
        self.selectedPropHolder.hide()

    def exit(self, wantTransition: bool = True):

        PropSpawnerGUI.PlacingProp = False
        self.__focusOutSearchBar()
        for btn in self.propButtons:
            btn.destroy()
            del btn

        for btn in self.categoryButtons.values():
            btn.destroy()
            del btn

        self.closeButton.destroy()

        self.categoryButtons = {}

        base.localAvatar.cameraFSM.requestLastWalkCamera(wantTransition)

        base.setCellsAvailable(base.leftCells, 1)
        base.setCellsAvailable(base.bottomCells, 1)

        self.browser.clearItems()
        self.browser.destroy()
        self.browserTop.destroy()
        self.searchContainer.destroy()
        self.controlsLabel.destroy()
        self.hideTooltip()
        self.destroy()

        self.ignoreAll()

        PropSpawnerGUI.open = False

    def addToFavorites(self, prop: str):
        favoriteList: List[str] = ClientSettings.FavoriteProps.get()
        if prop not in favoriteList:
            favoriteList.append(prop)
            ClientSettings.FavoriteProps.set(favoriteList)
        if self.category == PropCategory.Favorites:
            self.applyFilter(PropCategory.Favorites)

    def removeFromFavorites(self, prop: str):
        favoriteList: List[str] = ClientSettings.FavoriteProps.get()
        if prop in favoriteList:
            favoriteList.remove(prop)
            ClientSettings.FavoriteProps.set(favoriteList)
        if self.category == PropCategory.Favorites:
            self.applyFilter(PropCategory.Favorites)

    def showTooltip(self, text: str):
        if self.hoverTooltip:
            self.hoverTooltip.destroy()
            self.hoverTooltip = None
        self.hoverTooltip: DirectLabel = DirectLabel(
            relief = DGG.RAISED,
            text_style = 3,
            borderWidth = (0.01, 0.01),
            parent = base.aspect2d,
            text_fg = (.5, .9, 1, 1),
            text_scale = 0.06,
            frameColor = (0, .4, .5, .4),
            text = text
        )
        self.hoverTooltip.reparentTo(base.aspect2d)
        self.addTask(self.doTooltipTask, 'tooltip')

    def hideTooltip(self):
        self.removeTask('tooltip')
        if self.hoverTooltip:
            self.hoverTooltip.destroy()
            self.hoverTooltip = None

    def doTooltipTask(self, task):
        if base.mouseWatcherNode.hasMouse():
            width: float = self.hoverTooltip.getWidth()

            mouse: PointerData = base.mouseWatcherNode.getMouse()
            x: float = mouse.getX()
            y: float = mouse.getY()
            y += 0.05
            self.hoverTooltip.setPos(base.render2d, Vec3(x, 0, y))

            __pos = base.a2dBottomLeft.getRelativePoint(self.hoverTooltip, Vec3(-width / 2, 0, 0))
            if __pos.getX() < 0.025:
                self.hoverTooltip.setX(base.a2dBottomLeft, width / 2 + 0.025)

        return task.cont

    def setPropCount(self, currentProps: int, maxProps: int):
        ...
