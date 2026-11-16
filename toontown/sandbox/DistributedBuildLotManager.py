"""
DistributedBuildLotManager Client Side • Created by Drew @ 12/17/2022
Authorized for use ONLY in Toontown Realms
"""
import random
import datetime
import sys
import time
from typing import Optional, List, Tuple

from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObject import DistributedObject
from direct.gui import DirectGuiGlobals

from direct.gui.DirectButton import DirectButton
from direct.gui.DirectEntry import DirectEntry
from direct.gui.DirectFrame import DirectFrame
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import NodePath, TextNode, Vec3, Vec4

from otp.otpgui import OTPGUIUtils
from toontown.instancedgames.InstancedGamesGUI import ToonPortrait
from toontown.hood import ZoneUtil
from toontown.moviemaker.MovieMakerGUI import MovieMakerGUI
from toontown.parties.PartyUtils import getTimeDeltaInSeconds
from toontown.sandbox.BuildLotGlobals import BuildLotThemes, RequestCreateErrors, PRIVACY_MODE_PUBLIC, AUTOSAVE_FILENAME, THEME_TO_TITLE_COLOR, MaxLotCount
from toontown.toon.Toon import Toon
from toontown.toon.ToonDNA import ToonDNA
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals
from toontown.toonbase.ToonBaseGlobal import base
from toontown.toonbase.ToontownTypes import TAccessory
from toontown.toontowngui.SelectableButton import SelectableButton
from toontown.toontowngui.AnimatedButton import AnimatedButton
from toontown.toontowngui.ToontownScrolledGridFrame import ToontownScrolledGridFrame
from toontown.toontowngui.ToontownScrolledFrame import ToontownScrolledFrame

THEME_TO_PORTRAIT_COLOR = (
    Vec4(0.580, 0.694, 0.270, 1.0),  # ttc
    Vec4(0.8, 0.6, 0.5, 1.0),  # dod
    Vec4(0.2117, 0.584, 0.2117, 1.0),  # dga
    Vec4(1.0, 0.5, 0.5, 1.0),  # mml
    Vec4(0.3, 0.6, 1.0, 1.0),  # tbr
    Vec4(0.329, 0.317, 0.4313, 1.0),  # ddl
    Vec4(0.55, 0.5, 0.55, 1.0),  # sb
    Vec4(0.5, 0.6, 0.5, 1.0),  # cb
    Vec4(0.5, 0.5, 0.6, 1.0),  # lb
    Vec4(0.55, 0.5, 0.5, 1.0),  # bb
    Vec4(1.0, 1.0, 1.0, 1.0)
    # Vec4(1.0, 0.5, 0.4, 1.0),  # TODO
)

THEME_TO_ICON = (
    '**/zone_2000',
    '**/zone_1000',
    '**/zone_5000',
    '**/zone_4000',
    '**/zone_3000',
    '**/zone_9000',
    '**/zone_11000',
    '**/zone_12000',
    '**/zone_13000',
    '**/zone_10000',
    '**/zone_void'
)


class DistributedBuildLotManager(DistributedObject):
    propGui: NodePath = base.loader.loadModel('phase_3.5/models/gui/ttoff_m_gui_propgen', allowInstance = True)
    trashcanGui: NodePath = base.loader.loadModel('phase_3/models/gui/trashcan_gui', allowInstance = True)
    themeIcons = base.loader.loadModel('phase_3/models/gui/ttoff_m_gui_mgmn_teleport_icons', allowInstance = True)

    notify = DirectNotifyGlobal.directNotify.newCategory('DistBuildLotMGR')
    notify.setDebug(1)
    neverDisable = 1

    def __init__(self, cr):
        DistributedObject.__init__(self, cr)
        self.notify.debug('init buildlot mgr')

        cr.buildLotMgr = self

        self.lotListItems: List[DirectFrame] = []

        settingsScrollbarModel = base.loader.loadModel('phase_3.5/models/gui/ttoff_m_gui_sbk_generic')

        self.lotListGUI = DirectFrame(
                relief = None,
                parent = base.hidden,
                geom = self.propGui.find('**/lotlist_bg'),
                geom_scale = OTPGUIUtils.getImageScale(1614, 1281, 1.8),
                geom_pos = (0, 0, -0.055)
        )
        self.lotListScroll = ToontownScrolledFrame(
                parent = self.lotListGUI,
                width = 0.75,
                height = 0.485,
                pos = (0, 0, 0),
                itemMargin = (0.0375, 0.0025),
                useItemBoundsForPadding = False,
                itemPadding = 0.2,
                manageScrollBars = False,
                verticalScroll_frameColor = (0, 0, 0, 0),
                verticalScroll_manageButtons = False,
                verticalScroll_thumb_geom = (
                    settingsScrollbarModel.find('**/scrollbar_normal'),
                    settingsScrollbarModel.find('**/scrollbar_press'),
                    settingsScrollbarModel.find('**/scrollbar_hover')),
                verticalScroll_thumb_geom_scale = OTPGUIUtils.getImageScale(151, 399, 0.125),
                verticalScroll_thumb_relief = None,
                verticalScroll_resizeThumb = False,
                verticalScroll_decButton_relief = None,
                verticalScroll_incButton_relief = None)
        self.emptyLotListNotice = OnscreenText(
                parent = self.lotListGUI,
                pos = (0, 0.2),
                text = TTLocalizer.BuildLotEmptyNotice,
                fg = (0.75, 0.65, 0.45, 1),
                wordwrap = 15.0,
                scale = 0.08
        )
        self.emptyLotListNotice.hide()
        self.createLotButton = DirectButton(
                parent = self.lotListGUI,
                relief = None,
                text = TTLocalizer.BuildLotCreateButton,
                text_scale = 0.4,
                text_pos = (0, -.12),
                image = (
                    MovieMakerGUI.gui.find('**/dropdown_button_item'),
                    MovieMakerGUI.gui.find('**/dropdown_button_item'),
                    MovieMakerGUI.gui.find('**/dropdown_button_item_h')
                ),
                image_scale = OTPGUIUtils.getImageScale(682, 133),
                scale = 0.15,
                pos = (0.0, 0, -0.61),
                command = self.openCreateUI
        )
        self.closeButton = AnimatedButton(
                parent = self.lotListGUI,
                image = (
                    MovieMakerGUI.gui.find('**/tab_close'),
                    MovieMakerGUI.gui.find('**/tab_close_p'),
                    MovieMakerGUI.gui.find('**/tab_close_h')),
                scale = 0.1,
                pos = (0.825, 0, 0.57),
                command = self.hideList
        )

        self.createLotFrame = DirectFrame(
                relief = None,
                parent = base.hidden,
                geom = self.propGui.find('**/createlot_bg'),
                geom_scale = OTPGUIUtils.getImageScale(1614, 1281, 1.8),
                geom_pos = (0, 0, -0.055)
        )
        self.createLotClose = AnimatedButton(
                parent = self.createLotFrame,
                image = self.propGui.find('**/close_button_normal'),
                scale = 0.1,
                pos = (-0.825, 0, -0.58),
                command = self.closeCreateUI
        )

        self.createLotCreateButton = AnimatedButton(
                parent = self.createLotFrame,
                image = self.propGui.find('**/duplicate'),
                scale = 0.1,
                pos = (0.825, 0, -0.58),
                command = self.__doCreateLot
        )

        self.saveList = ToontownScrolledFrame(
                parent = self.createLotFrame,
                width = 0.4625,
                height = 0.503,
                pos = (.395, 0, 0.017),
                itemMargin = (0.05, -.01),
                useItemBoundsForPadding = False,
                itemPadding = 0.22,
                manageScrollBars = False,
                verticalScroll_frameColor = (0, 0, 0, 0),
                verticalScroll_manageButtons = False,
                verticalScroll_thumb_geom = (
                    settingsScrollbarModel.find('**/scrollbar_normal'),
                    settingsScrollbarModel.find('**/scrollbar_press'),
                    settingsScrollbarModel.find('**/scrollbar_hover')),
                verticalScroll_thumb_geom_scale = OTPGUIUtils.getImageScale(151, 399, 0.125),
                verticalScroll_thumb_relief = None,
                verticalScroll_resizeThumb = False,
                verticalScroll_decButton_relief = None,
                verticalScroll_incButton_relief = None)
        self.saveListLabel = OnscreenText(
                parent = self.saveList,
                pos = (0, .55),
                text = TTLocalizer.BuildLotCreateSaveLabel,
                scale = 0.07
        )
        self.hoverFrame = DirectFrame(
                parent = self.createLotFrame,
                relief = None,
                image = self.propGui.find('**/CreateLotHoverFrame'),
                image_scale = OTPGUIUtils.getImageScale(2050, 349, 0.25),
                pos = (0, 0, -0.5)
        )
        self.hoverFrame.setBin('gui-popup', 100)
        self.hoverFrame.hide()
        self.hoverFrameTitle = OnscreenText(
                parent = self.hoverFrame,
                text = '',
                font = ToontownGlobals.getFancyFont(),
                shadow = Vec4(0, 0, 0, 1),
                pos = (0, 0.04)
        )
        self.hoverFrameDesc = OnscreenText(
                parent = self.hoverFrame,
                text = '',
                scale = 0.055,
                fg = Vec4(.5, .5, .5, 1),
                pos = (0, -0.035),
                wordwrap = 24
        )

        settingsScrollbarModel.removeNode()

    def requestMySaves(self):
        self.sendUpdate('requestMySaves')

    def requestCreateLot(self, theme: BuildLotThemes = BuildLotThemes.TTC, saveToLoad: str = '', name = 'unimpl', privacyMode: int = PRIVACY_MODE_PUBLIC):
        if saveToLoad is None:
            saveToLoad = ''
        self.sendUpdate('requestCreateLot', [theme, saveToLoad, name, privacyMode])

    def requestCreateSuccessResponse(self, toZoneId: int):
        self.notify.debug(f'Success! Your lot is on {toZoneId}. Teleporting...')
        self.teleportToLot(toZoneId, base.localAvatar.doId)

    def requestCreateErrorResponse(self, errorCode: int):
        base.localAvatar.setSystemMessage(0, RequestCreateErrors[errorCode])

    """ === LIST GUI === """

    def showList(self):
        self.lotListGUI.reparentTo(base.aspect2dp)
        base.localAvatar.setLocked(True)
        base.transitions.fadeScreen(0.5)
        self.accept('toon-caged', self.handleToonCaged)
        self.requestOpenLots()
        OTPGUIUtils.Animations.popup(self.lotListGUI).start()

    def hideList(self):
        self.ignore('toon-caged')
        self.lotListGUI.reparentTo(base.hidden)
        base.localAvatar.setLocked(False, 0)
        base.transitions.noFade()

    def handleToonCaged(self):
        if not self.createLotFrame.isbase.hidden():
            self.closeCreateUI()

        self.hideList()

    def openCreateUI(self):
        self.lotListGUI.reparentTo(base.hidden)
        self.createLotFrame.reparentTo(base.aspect2dp)
        OTPGUIUtils.Animations.popup(self.createLotFrame).start()

        settingsScrollbarModel = base.loader.loadModel('phase_3.5/models/gui/ttoff_m_gui_sbk_generic')

        self.nameLabel = OnscreenText(
                parent = self.createLotFrame,
                text = TTLocalizer.BuildLotCreateNameLabel,
                scale = 0.05,
                pos = (-.5, .6)
        )
        self.nameEntryFrame = DirectFrame(
                parent = self.createLotFrame,
                relief = None,
                image = self.propGui.find('**/CreateLotNameEntry'),
                image_scale = OTPGUIUtils.getImageScale(1229, 252, 0.105),
                pos = (-.48, 0, .525)
        )
        self.nameEntry = DirectEntry(
                parent = self.nameEntryFrame,
                relief = None,
                text_scale = 0.04,
                text_align = TextNode.ACenter,
                width = 11,
                pos = (0.02, 0, -0.01),
                focusInCommand = self.toggleSpeedchat,
                focusInExtraArgs = [False],
                focusOutCommand = self.toggleSpeedchat,
                focusOutExtraArgs = [True]
        )

        self.themeLabelText = OnscreenText(
                parent = self.createLotFrame,
                text = TTLocalizer.BuildLotCreateThemeLabel,
                scale = 0.05,
                pos = (-.48, .36)
        )
        self.themeList = ToontownScrolledGridFrame(
                parent = self.createLotFrame,
                height = 0.26,
                width = 0.32,
                useItemBoundsForPadding = False,
                itemPadding = 0.14,
                itemsPerRow = 4,
                itemMargin = (-0.0925, -0.16),
                pos = (-.48, 0, 0.04),
                scrollAmount = 1,
                manageScrollBars = False,
                verticalScroll_frameColor = (0, 0, 0, 0),
                verticalScroll_manageButtons = False,
                verticalScroll_thumb_geom = (
                    settingsScrollbarModel.find('**/scrollbar_normal'),
                    settingsScrollbarModel.find('**/scrollbar_press'),
                    settingsScrollbarModel.find('**/scrollbar_hover')),
                verticalScroll_thumb_geom_scale = OTPGUIUtils.getImageScale(151, 399, 0.125),
                verticalScroll_thumb_relief = None,
                verticalScroll_resizeThumb = False,
                verticalScroll_decButton_relief = None,
                verticalScroll_incButton_relief = None
        )
        themeBtns = []
        for index, btnName in enumerate(THEME_TO_ICON):
            themeBtn = SelectableButton(
                    relief = None,
                    listInst = self.themeList,
                    image = self.themeIcons.find(THEME_TO_ICON[index]),
                    image_color = Vec4(1, 1, 1, 0.4),
                    selectedImageColor = Vec4(1, 1, 1, 1),
                    unselectedImageColor = Vec4(1, 1, 1, 0.4),
                    image_scale = 0.125,
                    selectedArgs = [index]
            )
            themeBtn.bind(DirectGuiGlobals.WITHIN, self.__showHoverFrame, extraArgs = [0, index])
            themeBtn.bind(DirectGuiGlobals.WITHOUT, self.__hideHoverFrame)
            themeBtns.append(themeBtn)
        self.themeList.addItems(*themeBtns)
        self.themeList.selectItemByIndex(0)
        self.privacyLabelText = OnscreenText(
                parent = self.createLotFrame,
                text = TTLocalizer.BuildLotCreatePrivacyLabel,
                scale = 0.05,
                pos = (-.48, -.215)
        )
        self.privacyList = ToontownScrolledGridFrame(
                parent = self.createLotFrame,
                height = 0.1,
                width = 0.3,
                useItemBoundsForPadding = False,
                itemPadding = 0.16,
                itemsPerRow = 4,
                itemMargin = (-0.05, -0.175),
                pos = (-.473, 0, -0.3)
        )
        privacyBtns = []
        for index, btnName in enumerate(['PrivacyPublicButton', 'PrivacyFriendsButton', 'PrivacyPrivateButton']):
            privacyBtn = SelectableButton(
                    relief = None,
                    listInst = self.privacyList,
                    image = self.propGui.find(f'**/{btnName}_Normal'),
                    selectedImage = self.propGui.find(f'**/{btnName}_Selected'),
                    unselectedImage = self.propGui.find(f'**/{btnName}_Normal'),
                    image_scale = OTPGUIUtils.getImageScale(322, 322, 0.125),
                    text_scale = 0.06,
                    selectedArgs = [index]
            )
            privacyBtn.bind(DirectGuiGlobals.WITHIN, self.__showHoverFrame, extraArgs = [1, index])
            privacyBtn.bind(DirectGuiGlobals.WITHOUT, self.__hideHoverFrame)
            privacyBtns.append(privacyBtn)
        self.privacyList.addItems(*privacyBtns)
        self.privacyList.selectItemByIndex(0)

        btn = SelectableButton(
                relief = None,
                listInst = self.saveList,
                image = self.propGui.find('**/SaveListItem_Normal'),
                selectedImage = self.propGui.find('**/SaveListItem_Selected'),
                unselectedImage = self.propGui.find('**/SaveListItem_Normal'),
                image_scale = OTPGUIUtils.getImageScale(1228, 478, 0.3),
                text = (TTLocalizer.BuildLotNewBtnNormal,
                        TTLocalizer.BuildLotNewBtnNormal,
                        TTLocalizer.BuildLotNewBtnNormal,
                        TTLocalizer.BuildLotNewBtnDisabled),
                text_fg = Vec4(0.75, 0.5, 0.275, 1.0),
                selectedTextFg = Vec4(0.275, 0.5, 0.75, 1.0),
                unselectedTextFg = Vec4(0.75, 0.5, 0.275, 1.0),
                scale = 0.7,
                text_scale = 0.06,
                text_pos = (-0.125, 0),
                text_align = TextNode.ALeft,
                selectedArgs = [None],
                command = self.__autosetSettings,
                extraArgs = [TTLocalizer.BuildLotDefaultName, 0, 0]
        )
        newIcon = OnscreenImage(
                parent = btn,
                image = self.themeIcons.find(f'**/zone_new'),
                scale = 0.19,
                pos = (-0.244, 0, -0.0025)
        )

        self.saveList.addItems(btn)
        self.saveList.selectItemByIndex(0)
        settingsScrollbarModel.removeNode()
        self.sendUpdate('requestMySaves')

    def requestMySavesResponse(self, saves):
        saves.sort(key = lambda save: save[4], reverse = True)
        btns = []
        for save, lotName, theme, privacy, lastEdited in saves:
            for emoji in base.emojis:
                lotName = lotName.replace(f':{emoji}:', f'\x01white\x01\5{emoji}\5\x02')
            if base.cr.getChatFilterMode() >= ToontownGlobals.CHAT_FILTER_CENSOR:
                lotName = base.profanityFilter.censor(lotName)
            saveBtnText = TTLocalizer.BuildLotInfo % {
                'name': lotName,
                'lastEdited': self.formatTime(datetime.datetime.fromtimestamp(lastEdited))
            }
            if save == AUTOSAVE_FILENAME:
                saveBtnText += TTLocalizer.BuildLotInfoAutosaved
            # TODO: fix scaling, especially with the animated hover
            btn = SelectableButton(
                    relief = None,
                    listInst = self.saveList,
                    image = self.propGui.find('**/SaveListItem_Normal'),
                    selectedImage = self.propGui.find('**/SaveListItem_Selected'),
                    unselectedImage = self.propGui.find('**/SaveListItem_Normal'),
                    image_scale = OTPGUIUtils.getImageScale(1228, 478, 0.3),
                    text = saveBtnText,
                    text_fg = Vec4(0.75, 0.5, 0.275, 1.0),
                    selectedTextFg = Vec4(0.275, 0.5, 0.75, 1.0),
                    unselectedTextFg = Vec4(0.75, 0.5, 0.275, 1.0),
                    scale = 0.7,
                    text_scale = 0.04,
                    text_align = TextNode.ALeft,
                    text_pos = (-0.125, 0.01),
                    selectedArgs = [save],
                    command = self.__autosetSettings,
                    extraArgs = [lotName, theme, privacy]
            )
            themeIcon = OnscreenImage(
                    parent = btn,
                    image = self.themeIcons.find(THEME_TO_ICON[theme]),
                    scale = 0.19,
                    pos = (-0.244, 0, -0.0025)
            )
            deleteButton = AnimatedButton(
                    parent = btn,
                    relief = None,
                    image = (self.trashcanGui.find('**/TrashCan_CLSD'),
                             self.trashcanGui.find('**/TrashCan_OPEN_default'),
                             self.trashcanGui.find('**/TrashCan_RLVR_default')),
                    text = ('', TTLocalizer.AvatarChoiceDelete, TTLocalizer.AvatarChoiceDelete),
                    text_fg = (1, 1, 1, 1),
                    text_shadow = (0, 0, 0, 1),
                    text_scale = 0.15,
                    text_pos = (0, -0.1),
                    pos = (0.325, 0, -0.08),
                    scale = 0.275,
                    command = self.handleDelete,
                    extraArgs = [btn, save])
            btns.append(btn)

        self.saveList.addItems(*btns)

        if len(btns) >= MaxLotCount:
            # Disable the new button
            newBtn = self.saveList.items[0][0]
            newBtn['state'] = DirectGuiGlobals.DISABLED
            # Select the first save
            self.saveList.selectItemByIndex(1)
            extraArgs = self.saveList.items[1][0]['extraArgs']
            self.__autosetSettings(extraArgs[0], extraArgs[1], extraArgs[2])

    def handleDelete(self, btn: SelectableButton, save):
        # Get the selected item first.
        selectedBtn = self.saveList.getSelectedItem(0)
        # Then remove the button from the saves list.
        self.saveList.removeItem(btn)
        # Select a new save if we deleted our selected save.
        if btn == selectedBtn:
            # Autoselect either new button or first save depending on our new lot count.
            if len(self.saveList.items) - 1 >= MaxLotCount:
                index = 1
            else:
                index = 0
                newBtn = self.saveList.items[0][0]
                newBtn['state'] = DirectGuiGlobals.NORMAL
            self.saveList.selectItemByIndex(index)
            extraArgs = self.saveList.items[index][0]['extraArgs']
            self.__autosetSettings(extraArgs[0], extraArgs[1], extraArgs[2])
        self.sendUpdate('deleteMySave', [save])

    def __autosetSettings(self, lotName: str, theme: BuildLotThemes, privacy: int):
        self.nameEntry.enterText(lotName)
        self.themeList.selectItemByIndex(theme)
        self.privacyList.selectItemByIndex(privacy)

    def closeCreateUI(self):
        self.showList()
        self.createLotFrame.reparentTo(base.hidden)
        self.nameEntryFrame.destroy()
        self.nameEntryFrame = None
        self.nameLabel.destroy()
        self.nameLabel = None
        self.saveList.clearItems()
        self.themeLabelText.destroy()
        self.themeLabelText = None
        self.themeList.destroy()
        self.themeList = None
        self.privacyLabelText.destroy()
        self.privacyLabelText = None
        self.privacyList.destroy()
        self.privacyList = None

    def __doCreateLot(self):
        selectedTheme = self.themeList.getSelectedItem(0)
        _theme = selectedTheme['selectedArgs'][0]
        _name = self.nameEntry.get(plain = True)
        selectedPrivacy = self.privacyList.getSelectedItem(0)
        _privacy = selectedPrivacy['selectedArgs'][0]
        selectedSaveItem = self.saveList.getSelectedItem(0)
        _saveToLoad = selectedSaveItem['selectedArgs'][0]

        self.requestCreateLot(_theme, name = _name if _name != "" else TTLocalizer.BuildLotDefaultName, privacyMode = _privacy, saveToLoad = _saveToLoad)
        self.closeCreateUI()
        self.hideList()
        self.__createLot_selectedSave = None

    def requestOpenLots(self):
        self.lotListScroll.clearItems()

        self.lotListItems = []
        self.sendUpdate('requestOpenLots')

    def requestOpenLotsResponse(self, lots: List[Tuple[int, str, str, int, int, int, bytes, TAccessory, TAccessory]]):
        self.notify.debug(f'Got lots: {lots}')

        for _ownerId, _ownerName, _lotName, _privacy, _theme, _numToons, _dnaString, _hat, _glasses in lots:
            for emoji in base.emojis:
                _ownerName = _ownerName.replace(f':{emoji}:', f'\x01white\x01\5{emoji}\5\x02')
                _lotName = _lotName.replace(f':{emoji}:', f'\x01white\x01\5{emoji}\5\x02')
            if base.cr.getChatFilterMode() >= ToontownGlobals.CHAT_FILTER_CENSOR:
                _ownerName = base.profanityFilter.censor(_ownerName)
                _lotName = base.profanityFilter.censor(_lotName)

            frame = DirectFrame(geom = self.propGui.find('**/LotListItem'),
                                geom_scale = OTPGUIUtils.getImageScale(1810, 235, 0.2),
                                relief = None,
                                scale = 0.9)
            lotNameLabel = OnscreenText(
                    parent = frame,
                    align = TextNode.ALeft,
                    pos = (-.58, 0.03),
                    scale = 0.065,
                    text = _lotName
            )

            ownerNameLabel = OnscreenText(
                    parent = frame,
                    align = TextNode.ALeft,
                    pos = (-0.58, -0.03),
                    scale = 0.040,
                    text = _ownerName
            )

            privacyLabel = OnscreenText(
                    parent = frame,
                    align = TextNode.ALeft,
                    pos = (-0.58, -0.08),
                    scale = 0.035,
                    text = TTLocalizer.BuildLotPrivacyLabels[_privacy]
            )

            playerCountLabel = OnscreenText(
                    parent = frame,
                    align = TextNode.ARight,
                    pos = (0.725, -0.06),
                    scale = 0.030,
                    fg = (0.0, 0.0, 0.0, 0.8),
                    text = f'{_numToons} {TTLocalizer.BuildLotPlayerCountMultiple}' if _numToons != 1 else TTLocalizer.BuildLotPlayerCountSingle
            )

            tpButton = AnimatedButton(
                    parent = frame,
                    image = (self.propGui.find('**/Teleport_Normal'),
                             self.propGui.find('**/Teleport_Press'),
                             self.propGui.find('**/Teleport_Hover'),
                             self.propGui.find('**/Teleport_Press')),
                    image_scale = OTPGUIUtils.getImageScale(1248, 440, 0.085),
                    pos = (0.61, 0, 0.02),
                    command = self.attemptTeleport,
                    extraArgs = [_ownerId]
            )

            if _dnaString != b'None':
                portrait: ToonPortrait = ToonPortrait((_dnaString, _hat, _glasses))
                portrait.setPos(-.67, 0, 0)
                portrait['image_color'] = THEME_TO_PORTRAIT_COLOR[_theme]
                portrait.reparentTo(frame)

            self.lotListItems.append(frame)
        self.lotListScroll.addItems(*self.lotListItems)

        if self.lotListItems:
            self.emptyLotListNotice.hide()
        else:
            self.emptyLotListNotice.show()

    def attemptTeleport(self, ownerId: int):
        self.sendUpdate('requestTeleport', [ownerId])
        self.hideList()

    def requestTeleportResponse(self, zoneId: int, ownerId: int):
        self.teleportToLot(zoneId, ownerId)

    def teleportToLot(self, zoneId: int, ownerId: int):
        base.cr.playGame.getPlace().requestLeave(
                {'loader': ZoneUtil.getBranchLoaderName(30000),
                 'where': 'toonInterior',  # This is a little hack to prevent showing the skies geometry
                 # maybe at somepoint we just make a build lot base.loader like estates
                 # but that can hold off
                 'how': 'teleportIn',
                 'hoodId': 30000,
                 'zoneId': zoneId,
                 'avId': -1,
                 'ownerId': ownerId,
                 'buildLot': 1
                 })

    def __showHoverFrame(self, category: int, index: int, _):
        title, desc = TTLocalizer.BuildLotCreateHoverText[category][index]
        self.hoverFrameTitle['text'] = title
        if category == 1:
            self.hoverFrameTitle['fg'] = Vec4(.95, .95, .95, 1)
        else:
            self.hoverFrameTitle['fg'] = THEME_TO_TITLE_COLOR[index]
        self.hoverFrameDesc['text'] = f'\x01WLDisplay\x01{desc}\x02'
        self.hoverFrame.show()

    def __hideHoverFrame(self, _):
        self.hoverFrame.hide()

    @staticmethod
    def formatTime(inTime: datetime) -> str:
        curServerTime = base.cr.toontownTimeManager.getCurServerDateTime()
        ltime = time.localtime()
        localTime = datetime.datetime(year=ltime.tm_year, month=ltime.tm_mon, day=ltime.tm_mday, hour=ltime.tm_hour, minute=ltime.tm_min, second=ltime.tm_sec)
        naiveServerTime = curServerTime.replace(tzinfo=None)
        newTimeDelta = localTime - naiveServerTime
        localDifference = getTimeDeltaInSeconds(newTimeDelta)
        inTime = inTime + datetime.timedelta(seconds=localDifference)

        # Realistically this won't be used at all right now, in
        # the future we will have it refresh the times when opening up
        # incase someone is playing thru to another day to show the date

        # why does datetime use different syntax on different platforms who designed this
        zeroCanceller = '#' if sys.platform == 'win32' else '-'

        return inTime.strftime(f'%{zeroCanceller}m/%{zeroCanceller}d/%y %{zeroCanceller}I:%M %p')

    def toggleSpeedchat(self, state):
        if not state:
            base.localAvatar.chatMgr.disableBackgroundFocus()
        else:
            base.localAvatar.chatMgr.setBackgroundFocus(base.controlManager.getChatDisabled(), True)