"""
DistributedBuildLot Client Side • Created by Drew @ 12/17/2022
Authorized for use ONLY in Toontown Realms
"""
from typing import Optional

from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObject import DistributedObject
from direct.gui import DirectGuiGlobals
from direct.gui.DirectButton import DirectButton
from direct.gui.DirectFrame import DirectFrame
from direct.interval.LerpInterval import LerpPosInterval
from panda3d.core import NodePath, CSDefault, Fog, Vec4, TextNode, CompassEffect
from panda3d.toontown import DNAStorage, loadDNAFile, WhisperPopup

from direct.gui.OnscreenText import OnscreenText

from otp.otpgui import OTPGUIUtils
from toontown.battle import BattleParticles
from toontown.hood import SkyUtil, ZoneUtil
from toontown.sandbox.BuildLotGlobals import BuildLotThemes, THEME_TO_TITLE_COLOR
from toontown.toonbase import ToontownGlobals, TTLocalizer

import random

from toontown.toontowngui import ToontownGUIUtils
from toontown.toontowngui.AnimatedButton import AnimatedButton
from toontown.toontowngui.ToontownScrolledFrame import ToontownScrolledFrame

THEME_TO_DNA = (
    'ttrm_d_ara_bdl_ttc.dna',
    'ttrm_d_ara_bdl_dod.dna',
    'ttrm_d_ara_bdl_dga.dna',
    'ttrm_d_ara_bdl_mml.dna',
    'ttrm_d_ara_bdl_tbr.dna',
    'ttrm_d_ara_bdl_ddl.dna',
    'ttrm_d_ara_bdl_sbhq.dna',
    'ttrm_d_ara_bdl_cbhq.dna',
    'ttrm_d_ara_bdl_lbhq.dna',
    'ttrm_d_ara_bdl_bbhq.dna',
    'ttrm_d_ara_bdl_nosky.dna'
    # 'ttrm_d_ara_bdl_tts.dna',
)
THEME_TO_SKY = (
    'phase_3.5/models/props/TT_sky',
    'phase_3.5/models/props/BR_sky',
    'phase_3.5/models/props/TT_sky',
    'phase_6/models/props/MM_sky',
    'phase_3.5/models/props/BR_sky',
    'phase_8/models/props/DL_sky',
    'phase_9/models/cogHQ/cog_sky',
    'phase_9/models/cogHQ/cog_sky',
    'phase_9/models/cogHQ/cog_sky',
    'phase_9/models/cogHQ/cog_sky',
    # 'phase_3.5/models/props/TT_sky',  # temp
    None
)
THEME_TO_GROUND = (
    'phase_3.5/maps/grassTT.png',
    'phase_6/maps/grassDD.png',
    'phase_3.5/maps/grassDG.png',
    'phase_3.5/maps/cobblestone_pink.png',
    'phase_3.5/maps/snow.png',
    'phase_3.5/maps/cobblestone_purple.png',
    'phase_9/maps/ground7.png',
    'phase_10/maps/floor1.png',
    'phase_11/maps/LB_CementGround_2.png',
    'phase_12/maps/dirt_golf.png',
    'phase_6/maps/grassDD.png'
)
THEME_TO_MUSIC = (
    'phase_4/audio/bgm/TC_nbrhood.ogg',
    'phase_6/audio/bgm/DD_nbrhood.ogg',
    'phase_8/audio/bgm/DG_nbrhood.ogg',
    'phase_6/audio/bgm/MM_nbrhood.ogg',
    'phase_8/audio/bgm/TB_nbrhood.ogg',
    'phase_8/audio/bgm/DL_nbrhood.ogg',
    'phase_9/audio/bgm/encntr_suit_HQ_nbrhood.ogg',
    'phase_10/audio/bgm/ttrm_s_ara_bgm_cbhq.ogg',
    'phase_11/audio/bgm/LB_courtyard.ogg',
    ['phase_12/audio/bgm/Bossbot_Entry_v1.ogg',
     'phase_12/audio/bgm/Bossbot_Entry_v2.ogg',
     'phase_12/audio/bgm/Bossbot_Entry_v3.ogg'],
    'phase_14.5/audio/bgm/ttrm_s_ara_blot_void.ogg'
)


class DistributedBuildLot(DistributedObject):
    DNAStorage = DNAStorage()
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBuildLot')
    notify.setDebug(1)
    guiModel: NodePath = loader.loadModel('phase_3/models/gui/ttrm_m_gui_mvmk')
    actionBarModel: NodePath = loader.loadModel('phase_3.5/models/gui/ttoff_m_gui_hud_actionBar')

    def __init__(self, cr):
        DistributedObject.__init__(self, cr)
        self.gui: Optional[DirectFrame] = None
        self.firstLoad = True

    def announceGenerate(self):
        DistributedObject.announceGenerate(self)
        base.cr.buildLot = self

        self.settingsButton = AnimatedButton(
                relief = None,
                parent = base.localAvatar.actionBar,
                pos = (-0.24, 0, 0.0),
                image = (self.actionBarModel.find('**/actionbar_settings_normal'), self.actionBarModel.find('**/actionbar_settings_hover')),
                image_scale = OTPGUIUtils.getImageScale(452, 495),
                scale = 0.08,
                text=('', '', TTLocalizer.ActionBarSettings),
                text_align = TextNode.ACenter,
                text_scale = 0.6,
                text_fg = (1.0, 1.0, 1.0, 1.0),
                text_shadow = (0, 0, 0, 0.7),
                text_pos = (0, 1),
                text_font = ToontownGlobals.getInterfaceFont(),
                command = self.openSettings
        )
        base.localAvatar.mapButton.hide()

    def setTheme(self, theme: BuildLotThemes):
        self.notify.debug(f'Loading lot with theme {theme}...')
        if not self.firstLoad:
            self.deleteTheme()
        self.firstLoad = False
        loadDNAFile(self.DNAStorage, 'phase_14.5/dna/ttrm_d_strg_bdl.dna', CSDefault, 1)
        base.loader.tick()

        # TODO: fix me
        np: NodePath = loadDNAFile(self.DNAStorage, 'phase_14.5/dna/ttrm_d_ara_bdl_ttc.dna', CSDefault, 1)  # THEME_TO_DNA[theme]
        if np.getNumParents() == 1:
            self.geom = NodePath(np.getParent(0))
            self.geom.reparentTo(render)
        else:
            self.geom: NodePath = render.attachNewNode(np)
        if theme == BuildLotThemes.VOID:
            self.geom.find('**/plains').removeNode()
        else:
            self.geom.find('**/plains').setTexture(loader.loadTexture(THEME_TO_GROUND[theme]), 1)

        base.loader.tick()

        if theme < 10:
            self.sky: NodePath = loader.loadModel(THEME_TO_SKY[theme])
            self.sky.reparentTo(render)
            if theme in [BuildLotThemes.TTC, BuildLotThemes.DGA]:  # , BuildLotThemes.TTS]:
                self.startCloudSky()
            elif theme in [BuildLotThemes.DOD, BuildLotThemes.TBR]:
                self.startNoCloudSky()
            elif theme in [BuildLotThemes.MML, BuildLotThemes.DDL]:
                self.startSingleCloudSky()
            elif theme in [BuildLotThemes.SBHQ, BuildLotThemes.CBHQ, BuildLotThemes.LBHQ, BuildLotThemes.BBHQ]:
                self.startCogHQSky()
            else:
                self.startSky()
            base.loader.tick()
        else:
            self.sky = None

        self.snow = None
        self.fog = None
        if theme == BuildLotThemes.DOD:
            self.fog = Fog('DODBuildLotFog')
            self.fog.setColor(Vec4(0.8, 0.8, 0.8, 1))
            self.fog.setLinearRange(0.0, 600)
            self.geom.setFog(self.fog)
            self.sky.setFog(self.fog)
        elif theme == BuildLotThemes.TBR:
            self.snow = BattleParticles.loadParticleFile('ttoff_p_efx_launch_tbrSnow')
            self.snow.setPos(0, 40, 10)
            self.snowRender = self.geom.attachNewNode('snowRender')
            self.snowRender.setDepthWrite(0)
            self.snowRender.setBin('fixed', 1)
            self.snow.start(base.camera, self.snowRender)

            self.fog = Fog('TBRBuildLotFog')
            self.fog.setColor(Vec4(0.8, 0.8, 0.8, 1))
            self.fog.setLinearRange(0.0, 400)
            self.geom.setFog(self.fog)
            self.sky.setFog(self.fog)
        elif theme == BuildLotThemes.DDL:
            render.setColorScale(0.65, 0.65, 0.75, 1)

        musicFile = THEME_TO_MUSIC[theme]
        if isinstance(musicFile, list):
            musicFile = random.choice(musicFile)
        if musicFile:
            self.music = base.loader.loadMusic(musicFile)
            base.playMusic(self.music, looping = 1, volume = 0.8)
        else:
            self.music = None

        if hasattr(self, 'smallTitleText') and self.smallTitleText:
            self.smallTitleText['fg'] = THEME_TO_TITLE_COLOR[theme]

        self.theme = theme

    def setLotName(self, lotName):
        self.lotName = lotName
        for emoji in base.emojis:
            self.lotName = self.lotName.replace(f':{emoji}:', f'\x01white\x01\5{emoji}\5\x02')
        if base.cr.getChatFilterMode() >= ToontownGlobals.CHAT_FILTER_CENSOR:
            self.lotName = base.profanityFilter.censor(self.lotName)
        if hasattr(self, 'smallTitleText'):
            self.smallTitleText['text'] = self.lotName
            self.smallTitleText['fg'] = THEME_TO_TITLE_COLOR[self.theme]
        else:
            self.smallTitleText = OnscreenText(
                    self.lotName,
                    parent = base.a2dTopRight,
                    fg = THEME_TO_TITLE_COLOR[self.theme],
                    font = ToontownGlobals.getSignFont(),
                    pos = (-0.15, -0.15),
                    scale = 0.08,
                    drawOrder = 0,
                    mayChange = 1,
                    bg = (0.5, 0.5, 0.5, 0.5),
                    align = TextNode.ARight)

    def openSettings(self):
        self.settingsButton['command'] = self.closeSettings
        self.gui = DirectFrame(
                relief = None,
                parent = base.a2dBottomRight,
                pos = (-0.65, 0, .65),
                image = self.guiModel.find('**/actor_editor_bg'),
                image_scale = OTPGUIUtils.getImageScale(646, 932),
                state = DirectGuiGlobals.NORMAL
        )
        
        OTPGUIUtils.Animations.slideUp(self.gui, 0.65, -0.4).start()

        self.themeDropdown = ScrollableDropdown(
                scale = 0.08,
                pos = (0, 0, 0.4),
                parent = self.gui,
                label = TTLocalizer.BuildLotCreateThemeLabel,
                items = TTLocalizer.BuildLotCreateThemes,
                selectedItem = self.theme,
                onChange = self.__doChangeTheme
        )

        self.saveButton = Button(
                scale = 0.08,
                pos = (0.1, 0, 0.3),
                parent = self.gui,
                label = TTLocalizer.BuildLotSaveButtonLabel,
                text = TTLocalizer.BuildLotSaveButtonLabel,
                command = lambda: self.sendUpdate('requestSaveLot', [False])
        )
        self.backupButton = Button(
                scale = 0.08,
                pos = (0.1, 0, 0.2),
                parent = self.gui,
                label = TTLocalizer.BuildLotBackupButtonLabel,
                text = TTLocalizer.BuildLotBackupButtonLabel,
                command = lambda: self.sendUpdate('requestSaveLot', [True])
        )

        self.closeBtn = DirectButton(
                relief = None,
                parent = self.gui,
                pos = (.3, 0, .46),
                image = (
                    self.guiModel.find('**/tab_close'),
                    self.guiModel.find('**/tab_close'),
                    self.guiModel.find('**/tab_close_h'),
                ),
                image1_color = (0.8, 0.8, 0.8, 1.0),
                scale = 0.05,
                command = self.closeSettings
        )

    def __doChangeTheme(self, index: int):
        self.sendUpdate('requestChangeTheme', [index])

    def closeSettings(self):
        self.settingsButton['command'] = self.openSettings
        if self.gui:
            self.gui.destroy()
            self.gui = None

    def deleteTheme(self):
        self.DNAStorage.resetNodes()
        self.DNAStorage.resetTextures()
        render.clearColorScale()

        self.geom.clearFog()
        self.geom.removeNode()
        if self.sky:
            self.sky.clearFog()
            self.sky.removeNode()
            taskMgr.remove('skyTrack')
        if self.snow:
            self.snow.cleanup()

        if self.music is not None:
            self.music.stop()
        del self.music

    def delete(self):
        self.notify.debug(f'Cleaning up lot...')
        self.deleteTheme()
        base.localAvatar.mapButton.show()

        self.smallTitleText.cleanup()
        del self.smallTitleText
        self.closeSettings()
        self.settingsButton.destroy()

        base.cr.buildLot = None

    def startCloudSky(self):
        return SkyUtil.startCloudSky(self)

    def startSingleCloudSky(self):
        return SkyUtil.startSingleCloudSky(self)

    def startNoCloudSky(self):
        return SkyUtil.startNoCloudSky(self)

    def startCogHQSky(self):
        skyInner = self.sky.find('**/InnerGroup')
        skyMiddle = self.sky.find('**/MiddleGroup')
        skyOuter = self.sky.find('**/OutterSky')
        if not skyOuter.isEmpty():
            skyOuter.setBin('background', 0)
        if not skyMiddle.isEmpty():
            skyMiddle.setBin('background', 10)
        if not skyInner.isEmpty():
            skyInner.setBin('background', 20)
        self.startSky()

    def startSky(self):
        self.sky.setDepthTest(0)
        self.sky.setDepthWrite(0)
        self.sky.setBin('background', 100)
        self.sky.reparentTo(camera)
        ce = CompassEffect.make(NodePath(), CompassEffect.PRot | CompassEffect.PZ)
        self.sky.node().setEffect(ce)

    def skyTrack(self, task):
        return SkyUtil.cloudSkyTrack(task)

    def skyTrackSingle(self, task):
        return SkyUtil.singleCloudSkyTrack(task)

    def skyTrackNoClouds(self, task):
        return SkyUtil.noCloudSkyTrack(task)

    def kickOut(self):
        zoneId = base.localAvatar.lastHood
        base.cr.playGame.getPlace().requestLeave({'loader': ZoneUtil.getBranchLoaderName(zoneId),
                                                  'where': ZoneUtil.getToonWhereName(zoneId),
                                                  'how': 'teleportIn',
                                                  'hoodId': zoneId,
                                                  'zoneId': zoneId,
                                                  'avId': -1
                                                  })

    def lotMessage(self, index):
        # TODO: this system message system sucks! replace it with something better lol
        base.localAvatar.setSystemMessage(0, TTLocalizer.BuildLotMessages[index], WhisperPopup.WTSystem)


class Button(DirectButton):

    def __init__(self, parent = hidden, **kwargs):
        """
        :param parent: Parent Frame
        :param row: The row in which the option is placed
        :param kwargs: extra key word args if needed
        """
        ui = DistributedBuildLot.guiModel
        optiondefs = (
            ('relief', None, None),
            ('text', 'BUTTON', None),
            ('text_pos', (0.0, -0.12), None),
            ('text_fg', (0.0, 0.0, 0.0, 1.0), None),
            ('text_scale', 0.4, None),
            ('text_align', TextNode.ACenter, None),
            ('label', 'label', None),
            ('image', (
                ui.find('**/dropdown_button_item'),
                ui.find('**/dropdown_button_item'),
                ui.find('**/dropdown_button_item_h')
            ), None),
            ('image1_color', (1.0, 1.0, 1.0, 1.0), None),
            ('image_scale', OTPGUIUtils.getImageScale(682, 133), None),
            ('pressEffect', False, None),
        )

        self.defineoptions(kwargs, optiondefs)
        DirectButton.__init__(self, parent)
        self.initialiseoptions(Button)
        self.dropdownButtons = []

        self.label = OnscreenText(parent = self, align = TextNode.ALeft,
                                  text = self['label'],
                                  pos = (-5, -.1), scale = .5, wordwrap = 20, mayChange = False)


class ScrollableDropdown(DirectButton):

    def __init__(self, parent = hidden, **kwargs):
        """
        :param parent: Parent Frame
        :param row: The row in which the option is placed
        :param kwargs: extra key word args if needed
        """
        ui = DistributedBuildLot.guiModel
        optiondefs = (
            ('relief', None, None),
            ('text', 'DROPDOWN', None),
            ('text_pos', (0.0, -0.12), None),
            ('text_fg', (0.0, 0.0, 0.0, 1.0), None),
            ('text_scale', 0.4, None),
            ('xOffset', 0.1, None),
            ('labelPos', (-5, -.1), None),
            ('labelAlign', TextNode.ALeft, None),
            ('text_align', TextNode.ACenter, None),
            ('label', 'label', None),
            ('image', (
                ui.find('**/dropdown_button'),
                ui.find('**/dropdown_button'),
                ui.find('**/dropdown_button_h')
            ), None),
            ('image1_color', (0.8, 0.8, 0.8, 1.0), None),
            ('image_scale', OTPGUIUtils.getImageScale(682, 133), None),
            ('pressEffect', False, None),
            ('command', self.openDropdown, None),
            ('selectedItem', 0, None),
            ('items', None, None),
            ('onChange', None, None),
        )

        self.defineoptions(kwargs, optiondefs)
        DirectButton.__init__(self, parent)
        self.initialiseoptions(ScrollableDropdown)
        self.dropdownButtons = []

        self.label = OnscreenText(parent = self, align = self['labelAlign'],
                                  text = self['label'],
                                  pos = self['labelPos'], scale = .5, wordwrap = 20, mayChange = False)
        self.setX(self.getX() + self['xOffset'])
        self['text'] = self['items'][self['selectedItem']]

    def openDropdown(self):
        ui = DistributedBuildLot.guiModel
        settingsScrollbarModel = loader.loadModel('phase_3.5/models/gui/ttoff_m_gui_sbk_generic')
        self['command'] = self.closeDropdown
        self.dropdownFrame = ToontownScrolledFrame(
            parent = self,
            image = ui.find('**/dropdown_bg'),
            image_scale = OTPGUIUtils.getImageScale(682, 1064),
            scale = 8,
            height = 0.49,
            width = 0.3,
            itemPadding = 0.104,
            itemMargin = (0.025, -.01) if len(self['items'])>9 else (0.05, -0.01),
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
            verticalScroll_incButton_relief = None
        )

        self.dropdownFrame.setPos(0, 0, -4.5)
        self.dropdownFrame.setBin('gui-popup', 100)
        settingsScrollbarModel.removeNode()
        btns = []
        for index, option in enumerate(self['items']):
            btn = DirectButton(parent = self.dropdownFrame,
                               relief = None,
                               scale = 0.104,
                               text = option,
                               text_pos = (0, -0.15),
                               text_scale = .5,
                               image = (
                                   ui.find('**/dropdown_button_item'),
                                   ui.find('**/dropdown_button_item'),
                                   ui.find('**/dropdown_button_item_h')
                               ),
                               image0_color = (1.0, 1.0, 1.0, 0.0),
                               image_scale = OTPGUIUtils.getImageScale(682, 133),
                               command = self.chooseItem,
                               extraArgs = [index],
                               pressEffect = False)
            btns.append(btn)
        self.dropdownFrame.addItems(*btns)

    def chooseItem(self, index: int):
        self['selectedItem'] = index

        self['text'] = self['items'][self['selectedItem']]
        if self['onChange']:
            self['onChange'](index)

        self.closeDropdown()

    def closeDropdown(self):
        self['command'] = self.openDropdown
        self.dropdownFrame.destroy()
