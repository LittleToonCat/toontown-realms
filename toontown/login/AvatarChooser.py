from panda3d.core import *

from direct.fsm import StateData
from direct.fsm import ClassicFSM, State
from typing import List, Tuple, Optional

from direct.gui.DirectGui import *
from direct.directnotify import DirectNotifyGlobal
from direct.interval.IntervalGlobal import *
from panda3d.toontown import DNAStorage, loadDNAFile, NametagGroup

from otp.distributed.PotentialAvatar import PotentialAvatar
from otp.otpgui import OTPGUIUtils
from toontown.episodes.EpisodeSelector import EpisodeSelector
from toontown.launcher import DownloadForceAcknowledge
from toontown.login.InfoGUI import InfoGUI
from toontown.login.WelcomeGUI import WelcomeGUI
from toontown.toonbase import TTLocalizer, ToontownGlobals, ClientSettings

from toontown.toontowngui.SettingsScreen import SettingsScreen

from . import AvatarChoice
import random

from .DatapacksListGUI import DatapacksListGUI
from ..avatar import ToontownAvatarUtils
from ..datapack.DataPackManager import DataPackManager
from ..hood import ZoneUtil
from ..toon.Toon import Toon
from ..toon.ToonDNA import ToonDNA
from ..toonbase.ToonBaseGlobal import base
from ..toonbase.ToontownTypes import TPickAToonProp, TPosHpr
from ..toontowngui.AnimatedButton import AnimatedButton

MAX_AVATARS = 6
RETRO_MODE = ClientSettings.ClassicPickAToon.get()

if RETRO_MODE:
    POSITIONS = (Vec3(-0.81999999999999995, 0, 0.34999999999999998), Vec3(0, 0, 0.34999999999999998),
                 Vec3(0.81999999999999995, 0, 0.34999999999999998), Vec3(-0.81999999999999995, 0, -0.46999999999999997),
                 Vec3(0, 0, -0.46999999999999997), Vec3(0.81999999999999995, 0, -0.46999999999999997))
    COLORS = (
        Vec4(0.91700000000000004, 0.16400000000000001, 0.16400000000000001, 1),
        Vec4(0.152, 0.75, 0.25800000000000001, 1),
        Vec4(0.59799999999999998, 0.40200000000000002, 0.875, 1),
        Vec4(0.13300000000000001, 0.58999999999999997, 0.97699999999999998, 1),
        Vec4(0.89500000000000002, 0.34799999999999998, 0.60199999999999998, 1),
        Vec4(0.97699999999999998, 0.81599999999999995, 0.13300000000000001, 1))
else:
    POSITIONS = (Vec3(-0.840167, 0, 0.359333),
                 Vec3(0.00933349, 0, 0.306533),
                 Vec3(0.862, 0, 0.3293),
                 Vec3(-0.863554, 0, -0.445659),
                 Vec3(0.00999999, 0, -0.5181),
                 Vec3(0.864907, 0, -0.445659))
    COLORS = (Vec4(0.917, 0.164, 0.164, 1),
              Vec4(0.152, 0.75, 0.258, 1),
              Vec4(0.598, 0.402, 0.875, 1),
              Vec4(0.133, 0.59, 0.977, 1),
              Vec4(0.895, 0.348, 0.602, 1),
              Vec4(0.977, 0.816, 0.133, 1))
chooser_notify = DirectNotifyGlobal.directNotify.newCategory('AvatarChooser')

"""
FOR 3D

WHEN CLICKING ON A TOON
CAMERA WILL ZOOM INTO THE TOON  WITH THE TOON APPEARING OFFSET TO THE LEFT, AND A FEW OPTIONS APPEARING ON THE RIGHT
ALL OTHER TOONS WILL FADE OUT
OPTIONS WILL SHOW AS
PLAY
DELETE
MAYBE ADD SOME MORE DETAILS LIKE LAFF, GAGS MAYBE ACTIVE TASKS IF IM FEELING EXOTIC
DOODLE SHOULD JUMP OUT AND SIT TO THE RIGHT OF THE TOON
"""


class AvatarChooser(StateData.StateData):
    dnaStorage: DNAStorage = DNAStorage()

    def __init__(self, avatarList: List[PotentialAvatar], parentFSM, doneEvent):
        StateData.StateData.__init__(self, doneEvent)
        self.choice = None
        self.avatarList: List[PotentialAvatar] = avatarList
        self.fsm = ClassicFSM.ClassicFSM('AvatarChooser',
                                         [State.State('Choose', self.enterChoose, self.exitChoose, ['CheckDownload']),
                                          State.State('CheckDownload', self.enterCheckDownload, self.exitCheckDownload,
                                                      ['Choose'])], 'Choose', 'Choose')
        self.fsm.enterInitialState()
        self.parentFSM = parentFSM
        self.parentFSM.getCurrentState().addChild(self.fsm)

        self.geom: Optional[NodePath] = None

        self.toonModels: List[Toon] = []

        self.lastSelectedToon: Optional[Toon] = None

    def enter(self):
        self.notify.info('AvatarChooser.enter')

        if self.isLoaded == 0:
            self.load()

        base.disableMouse()

        self.title.reparentTo(aspect2d)

        self.quitButton.show()
        self.logoutButton.show()
        self.episodesButton.show()
        self.settingsButton.show()
        self.datapacksButton.show()
        self.infoButton.show()
        self.helpButton.show()

        self.pickAToonBG.setBin('background', 1)
        self.pickAToonBG.reparentTo(aspect2d)

        if base.cr.gameServicesManager.motdDialog:
            base.cr.gameServicesManager.motdDialog.show()
        else:
            if ClientSettings.LastWelcomeVersion.get() != WelcomeGUI.VERSION:
                self.__handleWelcome()

        bgColors = [(0.145, 0.368, 0.78, 1.0), (0.0, 0.0, 0.0, 1.0), (0.145, 0.368, 0.78, 1.0),
                    (0.145, 0.368, 0.78, 1.0)]
        holidayIndex = loader.loadingScreen.getActiveHoliday()
        base.setBackgroundColor(Vec4(*bgColors[holidayIndex]))
        choice = base.config.GetInt('auto-avatar-choice', -1)
        for panel in self.panelList:
            panel.show()
            self.accept(panel.doneEvent, self.__handlePanelDone)
            if panel.position == choice and panel.mode == AvatarChoice.AvatarChoice.MODE_CHOOSE:
                self.__handlePanelDone('chose', panelChoice = choice)

        if base.cr.gameServicesManager.pickAToonBackground and ClientSettings.AllowServerPATScreens.get():
            self.pickAToonBG.reparentTo(base.hidden)

            bg: Tuple[List[str], str, int, List[TPickAToonProp], List[
                TPosHpr], TPosHpr] = base.cr.gameServicesManager.pickAToonBackground
            storages, dna, sky, props, toonPositions, cameraPos = bg

            loadDNAFile(self.dnaStorage, 'phase_4/dna/ttrm_d_strg.dna', CSDefault, 1)
            for storage in storages:
                loadDNAFile(self.dnaStorage, storage, CSDefault, 1)
                # base.loader.tick()
            if dna:
                np: PandaNode = loadDNAFile(self.dnaStorage, dna, CSDefault, 1)
                if np.getNumParents() == 1:
                    self.geom = NodePath(np.getParent(0))
                    self.geom.reparentTo(base.render)
                else:
                    self.geom: NodePath = base.render.attachNewNode(np)
            else:
                self.geom: NodePath = base.render.attachNewNode('pickatoonbackgroundnodna')
            base.camera.setPosHpr(*cameraPos)
            self.cameraPos3D = cameraPos
            base.camLens.setMinFov(55)

            if sky != -1:
                skyPath = ('phase_3.5/models/props/TT_sky',
                           'phase_3.5/models/props/BR_sky',
                           'phase_6/models/props/MM_sky',
                           'phase_8/models/props/DL_sky',
                           'phase_9/models/cogHQ/cog_sky')[sky]
                self.sky: NodePath = base.loader.loadModel(skyPath)
                self.sky.reparentTo(self.geom)

            for prop in props:
                _path, _node, _hideNodes, _posHpr, _scale, _color, _textureOverrides = prop
                _propModel = DataPackManager.getModelNode(_path, _node if _node is not '' else None)
                if _hideNodes:
                    for _subnodename in _hideNodes:
                        _subnode = _propModel.find(_subnodename)
                        if not _subnode.isEmpty():
                            _subnode.removeNode()
                _propModel.reparentTo(self.geom)
                _propModel.setPosHpr(*_posHpr)
                _propModel.setScale(*_scale)
                _propModel.setColorScale(*_color)
                if _textureOverrides:
                    for nodeName, newTexture in _textureOverrides:
                        _np = _propModel.find(nodeName)
                        if not _np.isEmpty():
                            _np.setTexture(DataPackManager.getTexture(newTexture), 1)

            if toonPositions:
                fullList: List[Optional[PotentialAvatar]] = [None] * 6

                for _av in self.avatarList:
                    fullList[_av.position] = _av

                potAv: PotentialAvatar
                for i, potAv in enumerate(fullList):
                    toonDNA = ToonDNA()
                    if potAv is None:
                        # toonDNA.newToonFromProperties('dls', 'ms', 'm', 'm',
                        #                              (1.0, 1.0, 1.0, 1.0), (1.0, 1.0, 1.0, 1.0),
                        #                              (1.0, 1.0, 1.0, 1.0), (1.0, 1.0, 1.0, 1.0),
                        #                              0, (1.0, 1.0, 1.0, 1.0),
                        #                              0, (1.0, 1.0, 1.0, 1.0),
                        #                              0, (1.0, 1.0, 1.0, 1.0)
                        #                              )
                        toonDNA.newToonRandom()
                        toon = ToontownAvatarUtils.createUniqueToon(TTLocalizer.AvatarChooserMakeAToon, toonDNA,
                                                                    colorType = NametagGroup.CCSpeedChat)
                        toon.getGeomNode().setColorScale(0, 0, 0, 1.0)
                        toon.pickAToonExists = False
                        toon.getGeomNode().setShader(Shader.load(Shader.SLGLSL,
                                                                 fragment = 'phase_3/shaders/ttrm_sha_av_patToon.frag',
                                                                 vertex = 'phase_3/shaders/ttrm_sha_av_patToon.vert',
                                                                 ))
                        toon.getGeomNode().setShaderInput('dither', 1.0)
                    else:
                        toonDNA.makeFromNetString(potAv.dna)
                        toon = ToontownAvatarUtils.createUniqueToon(
                            potAv.name,
                            toonDNA,
                            potAv.hat,
                            potAv.glasses,
                            potAv.backpack,
                            potAv.shoes,
                            colorType = NametagGroup.CCNormal,
                            nametagStyle = potAv.nametagStyle
                        )

                        toon.pickAToonExists = True
                        toon.getGeomNode().setShader(Shader.load(Shader.SLGLSL,
                                                                 fragment = 'phase_3/shaders/ttrm_sha_av_patToon.frag',
                                                                 vertex = 'phase_3/shaders/ttrm_sha_av_patToon.vert',
                                                                 ))

                        toon.getGeomNode().setShaderInput('dither', 1.0)
                        toon.pickAToonLastLocation = potAv.lastZone
                    toon.startLookAround()
                    toon.startBlink()

                    self.toonModels.append(toon)
                    toon.reparentTo(base.hidden)
                    toon.setPosHpr(*toonPositions[i])
                    toon.setPickable(True)
                    toon.hide()
                startCameraPos = base.render.getRelativePoint(base.camera, Vec3(0, -10, 0))
                ival = Parallel(
                    Sequence(
                        Func(base.transitions.fadeScreen, 1.0),
                        Wait(0.5),
                        Parallel(
                            base.transitions.getFadeInIval(),
                            base.camera.posInterval(1, cameraPos[0:3], startCameraPos, blendType = 'easeOut')
                        )
                    )
                )

                for i, toon in enumerate(self.toonModels):
                    ival.append(Sequence(
                        Wait(0.5 + (0.2 * i)),
                        Func(toon.reparentTo, self.geom),
                        Func(toon.animFSM.request, 'TeleportIn', [1, 0, toon.animFSM.request, ['neutral']]),
                        Wait(.4),
                        Func(toon.addActive)
                    ))
                ival.start()

                for panel in self.panelList:
                    panel.reparentTo(base.hidden)
                self.acceptOnce('clickedNametag', self.__clickToon)
                base.toggleNametags(False)
                base.toggleNametags(True)
            else:
                for panel in self.panelList:
                    panel.reparentTo(base.aspect2d)
                    panel['image_color'] = (1.0, 1.0, 1.0, 1.0)
                startCameraPos = base.render.getRelativePoint(base.camera, Vec3(0, -10, 0))
                ival = Sequence(
                    Func(base.transitions.fadeScreen, 1.0),
                    Wait(0.5),
                    Parallel(
                        base.transitions.getFadeInIval(),
                        base.camera.posInterval(1, cameraPos[0:3], startCameraPos, blendType = 'easeOut')
                    )
                )

                ival.start()
                # todo: populate with the buttons
                return

    def exit(self):
        if self.isLoaded == 0:
            return None
        for panel in self.panelList:
            panel.hide()

        if hasattr(self, 'sky'):
            self.sky.removeNode()
            del self.sky
        if self.geom:
            self.geom.removeNode()
            self.geom = None

        self.dnaStorage.resetNodes()
        self.dnaStorage.resetTextures()

        for toon in self.toonModels:
            toon.stopLookAroundNow()
            toon.stopBlink()
            toon.setPickable(False)
            toon.removeActive()
            toon.delete()
            del toon
        self.toonModels = []

        self.ignoreAll()
        self.title.reparentTo(hidden)
        self.quitButton.hide()
        self.logoutButton.hide()
        self.settingsButton.hide()
        self.datapacksButton.hide()
        self.episodesButton.hide()
        self.infoButton.hide()
        self.helpButton.hide()
        self.pickAToonBG.reparentTo(hidden)
        base.setBackgroundColor(ToontownGlobals.DefaultBackgroundColor)
        return None

    def load(self, isPaid):
        if self.isLoaded == 1:
            return None
        self.isPaid = isPaid
        gui = loader.loadModel('phase_3/models/gui/pick_a_toon_gui')
        gui2 = loader.loadModel('phase_3/models/gui/quit_button')
        newGui = loader.loadModel('phase_3/models/gui/tt_m_gui_pat_mainGui')

        if RETRO_MODE:
            newGui.find("**/tt_t_gui_pat_background").setTexture(
                loader.loadTexture("phase_3/maps/tt_t_gui_pat_background_retro.png"), 1)

        holidayIndex = loader.loadingScreen.getActiveHoliday()
        self.pickAToonBG = newGui.find(
            '**/tt_m_gui_pat_mainGUI_' + ToontownGlobals.BackgroundNodeNames[holidayIndex] + '/tt_t_gui_pat_background')
        self.pickAToonBG.reparentTo(hidden)
        self.pickAToonBG.setPos(0.0, 2.73, 0.0)
        self.pickAToonBG.setScale(1, 1, 1)

        if RETRO_MODE:
            self.title = OnscreenText(TTLocalizer.AvatarChooserPickAToon, scale = 0.125, parent = hidden,
                                      font = ToontownGlobals.getSignFont(),
                                      fg = (1, 0.90000000000000002, 0.10000000000000001, 1),
                                      pos = (0.0, 0.81999999999999995))
        else:
            self.title = OnscreenText(TTLocalizer.AvatarChooserPickAToon, scale = TTLocalizer.ACtitle, parent = hidden,
                                      font = ToontownGlobals.getSignFont(),
                                      fg = ToontownGlobals.HolidayID2Colors.get(holidayIndex)[0], pos = (0.0, 0.82))

        nodeName = ToontownGlobals.HolidayID2Name.get(holidayIndex)
        quitHover = gui.find('**/QuitBtn_RLVR_' + nodeName)
        if RETRO_MODE:
            self.quitButton = DirectButton(
                image = (gui.find('**/QuitBtn_UP'), gui.find('**/QuitBtn_DN'), gui.find('**/QuitBtn_RLVR_default')),
                relief = None, text = TTLocalizer.AvatarChooserQuit, text_font = ToontownGlobals.getSignFont(),
                text0_fg = (0.152, 0.75, 0.25800000000000001, 1), text1_fg = (0.152, 0.75, 0.25800000000000001, 1),
                text2_fg = (0.97699999999999998, 0.81599999999999995, 0.13300000000000001, 1),
                text_pos = (0, -0.035000000000000003), text_scale = 0.10000000000000001, scale = 1.05,
                pos = (0, 0, -0.92400000000000004), command = self.__handleQuit)
            self.logoutButton = DirectButton(relief = None, pos = (-0.75, 0, -0.92400000000000004), scale = 0.65,
                                             image = (gui.find('**/QuitBtn_UP'), gui.find('**/QuitBtn_DN'),
                                                      gui.find('**/QuitBtn_RLVR_default')),
                                             image_scale = 1.15, image1_scale = 1.15, image2_scale = 1.18,
                                             text = TTLocalizer.AvatarChooserMainMenu,
                                             text_font = ToontownGlobals.getSignFont(),
                                             text0_fg = (0.152, 0.75, 0.25800000000000001, 1),
                                             text1_fg = (0.152, 0.75, 0.25800000000000001, 1),
                                             text2_fg = (
                                             0.97699999999999998, 0.81599999999999995, 0.13300000000000001, 1),
                                             text_scale = 0.07, text_pos = (0, -0.025),
                                             command = self.__handleLogoutWithoutConfirm)
            self.infoButton = DirectButton(relief = None, pos = (-0.4, 0, -0.92400000000000004), scale = 0.65,
                                           image = (gui.find('**/QuitBtn_UP'), gui.find('**/QuitBtn_DN'),
                                                    gui.find('**/QuitBtn_RLVR_default')),
                                           image_scale = 1.15, image1_scale = 1.15, image2_scale = 1.18,
                                           text = TTLocalizer.AvatarChooserInfo,
                                           text_font = ToontownGlobals.getSignFont(),
                                           text0_fg = (0.152, 0.75, 0.25800000000000001, 1),
                                           text1_fg = (0.152, 0.75, 0.25800000000000001, 1),
                                           text2_fg = (
                                           0.97699999999999998, 0.81599999999999995, 0.13300000000000001, 1),
                                           text_scale = TTLocalizer.ACepisodesButtonRetro,
                                           text_pos = TTLocalizer.ACepisodesButtonPos,
                                           command = self.__handleInfo)
            self.helpButton = DirectButton(relief = None, pos = (0.4, 0, -0.92400000000000004), scale = 0.65,
                                           image = (gui.find('**/QuitBtn_UP'), gui.find('**/QuitBtn_DN'),
                                                    gui.find('**/QuitBtn_RLVR_default')),
                                           image_scale = 1.15, image1_scale = 1.15, image2_scale = 1.18,
                                           text = TTLocalizer.AvatarChooserHelp,
                                           text_font = ToontownGlobals.getSignFont(),
                                           text0_fg = (0.152, 0.75, 0.25800000000000001, 1),
                                           text1_fg = (0.152, 0.75, 0.25800000000000001, 1),
                                           text2_fg = (
                                           0.97699999999999998, 0.81599999999999995, 0.13300000000000001, 1),
                                           text_pos = TTLocalizer.ACepisodesButtonPos,
                                           text_scale = TTLocalizer.ACepisodesButtonRetro,
                                           command = self.__handleWelcome)
            self.episodesButton = DirectButton(relief = None, pos = (0.75, 0, -0.92400000000000004), scale = 0.65,
                                               image = (gui.find('**/QuitBtn_UP'), gui.find('**/QuitBtn_DN'),
                                                        gui.find('**/QuitBtn_RLVR_default')),
                                               image_scale = 1.15, image1_scale = 1.15, image2_scale = 1.18,
                                               text = TTLocalizer.AvatarChooserEpisodes,
                                               text_font = ToontownGlobals.getSignFont(),
                                               text0_fg = (0.152, 0.75, 0.25800000000000001, 1),
                                               text1_fg = (0.152, 0.75, 0.25800000000000001, 1),
                                               text2_fg = (
                                               0.97699999999999998, 0.81599999999999995, 0.13300000000000001, 1),
                                               text_pos = TTLocalizer.ACepisodesButtonPos,
                                               text_scale = TTLocalizer.ACepisodesButtonRetro,
                                               command = self.__handleEpisodeSelect)

            self.settingsButton = DirectButton(relief = None, parent = base.a2dBottomLeft, pos = (0.2, 0, 0.086),
                                               scale = 0.5,
                                               image = (gui.find('**/QuitBtn_UP'), gui.find('**/QuitBtn_DN'),
                                                        gui.find('**/QuitBtn_RLVR_default')),
                                               image_scale = 1.15,
                                               image1_scale = 1.15,
                                               image2_scale = 1.18, text = TTLocalizer.AvatarChooserOptions,
                                               text_font = ToontownGlobals.getSignFont(),
                                               text0_fg = (0.152, 0.75, 0.25800000000000001, 1),
                                               text1_fg = (0.152, 0.75, 0.25800000000000001, 1),
                                               text2_fg = (
                                               0.97699999999999998, 0.81599999999999995, 0.13300000000000001, 1),
                                               text_pos = (0, -0.035),
                                               text_scale = TTLocalizer.AClogoutButton,
                                               command = self.__handleOptions)
            self.datapacksButton = DirectButton(relief = None, parent = base.a2dBottomRight, pos = (-0.2, 0, 0.086),
                                                scale = 0.5,
                                                image = (gui.find('**/QuitBtn_UP'), gui.find('**/QuitBtn_DN'),
                                                         gui.find('**/QuitBtn_RLVR_default')),
                                                image_scale = 1.15,
                                                image1_scale = 1.15,
                                                image2_scale = 1.18, text = TTLocalizer.AvatarChooserDatapacks,
                                                text_font = ToontownGlobals.getSignFont(),
                                                text0_fg = (0.152, 0.75, 0.25800000000000001, 1),
                                                text1_fg = (0.152, 0.75, 0.25800000000000001, 1),
                                                text2_fg = (
                                                0.97699999999999998, 0.81599999999999995, 0.13300000000000001, 1),
                                                text_pos = (0, -0.035),
                                                text_scale = 0.08,
                                                command = self.__handlePackList)
        else:
            self.quitButton = DirectButton(image = (quitHover, quitHover, quitHover), relief = None,
                                           text = TTLocalizer.AvatarChooserQuit,
                                           text_font = ToontownGlobals.getSignFont(),
                                           text_fg = ToontownGlobals.HolidayID2Colors.get(holidayIndex)[1],
                                           text_pos = TTLocalizer.ACquitButtonPos,
                                           text_scale = TTLocalizer.ACquitButton,
                                           image_scale = 1, image1_scale = 1.05, image2_scale = 1.05, scale = 1.05,
                                           parent = base.a2dBottomRight, pos = (-0.253333, 0, 0.093),
                                           command = self.__handleQuit)
            self.episodesButton = DirectButton(relief = None, parent = base.a2dBottomRight, pos = (-0.725, 0, 0.093),
                                               scale = 1.05,
                                               image = (quitHover, quitHover, quitHover), image_scale = 1,
                                               image1_scale = 1.05,
                                               image2_scale = 1.05, text = TTLocalizer.AvatarChooserEpisodes,
                                               text_font = ToontownGlobals.getSignFont(),
                                               text_fg = ToontownGlobals.HolidayID2Colors.get(holidayIndex)[1],
                                               text_pos = TTLocalizer.ACepisodesButtonPos,
                                               text_scale = TTLocalizer.ACepisodesButton,
                                               command = self.__handleEpisodeSelect)
            self.logoutButton = DirectButton(relief = None, image = (quitHover, quitHover, quitHover),
                                             text = TTLocalizer.AvatarChooserMainMenu,
                                             text_font = ToontownGlobals.getSignFont(),
                                             text_fg = ToontownGlobals.HolidayID2Colors.get(holidayIndex)[1],
                                             text_scale = 0.07, text_pos = (0, -0.025),
                                             parent = base.a2dBottomLeft, pos = (0.163333, 0, 0.086),
                                             image_scale = 1.15,
                                             image1_scale = 1.15, image2_scale = 1.18, scale = 0.5,
                                             command = self.__handleLogoutWithoutConfirm)
            self.infoButton = DirectButton(relief = None, parent = base.a2dBottomLeft, pos = (0.403333, 0, 0.086),
                                           scale = 0.5,
                                           image = (quitHover, quitHover, quitHover), image_scale = 1.15,
                                           image1_scale = 1.15,
                                           image2_scale = 1.18, text = TTLocalizer.AvatarChooserInfo,
                                           text_font = ToontownGlobals.getSignFont(),
                                           text_fg = ToontownGlobals.HolidayID2Colors.get(holidayIndex)[1],
                                           text_scale = TTLocalizer.AClogoutButton, text_pos = (0, -0.035),
                                           command = self.__handleInfo)
            self.helpButton = DirectButton(relief = None, parent = base.a2dBottomLeft, pos = (0.643333, 0, 0.086),
                                           scale = 0.5,
                                           image = (quitHover, quitHover, quitHover), image_scale = 1.15,
                                           image1_scale = 1.15,
                                           image2_scale = 1.18, text = TTLocalizer.AvatarChooserHelp,
                                           text_font = ToontownGlobals.getSignFont(),
                                           text_fg = ToontownGlobals.HolidayID2Colors.get(holidayIndex)[1],
                                           text_scale = TTLocalizer.AClogoutButton, text_pos = (0, -0.035),
                                           command = self.__handleWelcome)
            self.settingsButton = DirectButton(relief = None, parent = base.a2dBottomLeft, pos = (0.883333, 0, 0.086),
                                               scale = 0.5,
                                               image = (quitHover, quitHover, quitHover), image_scale = 1.15,
                                               image1_scale = 1.15,
                                               image2_scale = 1.18, text = TTLocalizer.AvatarChooserOptions,
                                               text_font = ToontownGlobals.getSignFont(),
                                               text_fg = ToontownGlobals.HolidayID2Colors.get(holidayIndex)[1],
                                               text_pos = (0, -0.035),
                                               text_scale = TTLocalizer.ACquitButton,
                                               command = self.__handleOptions)
            self.datapacksButton = DirectButton(relief = None, parent = base.a2dBottomLeft, pos = (1.123333, 0, 0.086),
                                                scale = 0.5,
                                                image = (quitHover, quitHover, quitHover), image_scale = 1.15,
                                                image1_scale = 1.15,
                                                image2_scale = 1.18, text = TTLocalizer.AvatarChooserDatapacks,
                                                text_font = ToontownGlobals.getSignFont(),
                                                text_fg = ToontownGlobals.HolidayID2Colors.get(holidayIndex)[1],
                                                text_pos = (0, -0.035),
                                                text_scale = 0.07,
                                                command = self.__handlePackList)
            if len(base.cr.dataPackMgr.getActivePacks()) > 1:
                self.datapacksIndicator = DirectFrame(
                    parent = self.datapacksButton,
                    relief = None,
                    image_color = (1.0, 1.0, 1.0, 0.5),
                    pos = (0.22, 0, 0.035),
                    scale = 0.05,
                    text = f'({len(base.cr.dataPackMgr.getActivePacks()) - 1})',
                    text_scale = 1.5,
                    text_roll = -15,
                    text_font = ToontownGlobals.getSignFont(),
                    text_fg = ToontownGlobals.HolidayID2Colors.get(holidayIndex)[1]
                )

        self.logoutButton.hide()
        self.infoButton.hide()
        self.helpButton.hide()
        self.episodesButton.hide()
        self.settingsButton.hide()
        self.datapacksButton.hide()

        self.infoGui = InfoGUI(self)
        self.infoGui.hide()

        self.packList = DatapacksListGUI()
        self.packList.hide()

        self.episodeSelector = EpisodeSelector(self)
        self.episodeSelector.hide()

        self.welcomeGui = WelcomeGUI(self)
        self.welcomeGui.hide()

        matGui: NodePath = base.loader.loadModel('phase_3/models/gui/tt_m_gui_mat_mainGui')

        self.toon3DFrame = DirectFrame(parent = base.aspect2d, pos = (0.6, 0, 0))
        self.toon3DName = OnscreenText(
            parent = self.toon3DFrame,
            pos = (0.0, -0.026),
            text = 'Toon Name',
            font = ToontownGlobals.getSignFont(),
            fg = (0.0, 0.6, 1.0, 1.0),
            scale = 0.16
        )
        NodePath.setPos(self.toon3DName, Vec3(-0.6, 0.0, 0.6))
        self.toon3DLastSeen = OnscreenText(
            parent = self.toon3DFrame,
            pos = (0.0, 0.0),
            text = TTLocalizer.AvatarChooserLastSeen,
            font = ToontownGlobals.getRealmsFont(),
            fg = (0.0, 0.6, 1.0, 1.0),
            shadow = (0.0, 0.0, 0.0, 0.60),
            scale = 0.05
        )
        self.toon3DPlayOrCreate = AnimatedButton(
            parent = self.toon3DFrame,
            text = TTLocalizer.AvatarChooserMakeAToon,
            pos = (0.0, 0.0, 0.1),
            image = (
                matGui.find('**/tt_t_gui_mat_shuffleUp'),
                matGui.find('**/tt_t_gui_mat_shuffleDown'),
                matGui.find('**/tt_t_gui_mat_shuffleUp'),
            ),
            image_scale = OTPGUIUtils.getImageScale(120, 80, 1.0),
            text_fg = (1.0, 1.0, 1.0, 1.0),
            text_shadow = (0.0, 0.0, 0.0, 0.60),
            text_pos = (0.0, -0.02),
            text_scale = 0.088)
        self.toon3DBack = AnimatedButton(
            parent = self.toon3DFrame,
            image = (
                matGui.find('**/tt_t_gui_mat_shuffleUp'),
                matGui.find('**/tt_t_gui_mat_shuffleDown'),
                matGui.find('**/tt_t_gui_mat_shuffleUp'),
            ),
            image_scale = OTPGUIUtils.getImageScale(-100, 80, .8),
            text = TTLocalizer.SettingsTabBack,
            text_fg = (1.0, 1.0, 1.0, 1.0),
            text_shadow = (0.0, 0.0, 0.0, 0.60),
            text_pos = (0.0, -0.03),
            pos = (0.0, 0.0, -0.3),
            text_scale = 0.088,
            command = self.__handleBack)
        self.toon3DFrame.reparentTo(base.hidden)

        gui.removeNode()
        gui2.removeNode()
        newGui.removeNode()

        self.panelList = []
        used_position_indexs = []
        for av in self.avatarList:
            if av.position == 6:
                continue
            if base.cr.isPaid():
                okToLockout = 0
            else:
                okToLockout = 1
                if av.position in AvatarChoice.AvatarChoice.OLD_TRIALER_OPEN_POS:
                    okToLockout = 0
            panel = AvatarChoice.AvatarChoice(av, position = av.position, paid = isPaid, okToLockout = okToLockout)
            panel.setPos(POSITIONS[av.position])
            if RETRO_MODE:
                panel['image_color'] = COLORS[av.position]
            used_position_indexs.append(av.position)
            self.panelList.append(panel)

        for panelNum in range(0, MAX_AVATARS):
            if panelNum not in used_position_indexs:
                panel = AvatarChoice.AvatarChoice(position = panelNum, paid = isPaid)
                panel.setPos(POSITIONS[panelNum])
                if RETRO_MODE:
                    panel['image_color'] = COLORS[panelNum]
                self.panelList.append(panel)

        if len(self.avatarList) > 0:
            self.initLookAtInfo()
        self.isLoaded = 1

    def getLookAtPosition(self, toonHead, toonidx):
        lookAtChoice = random.random()
        if len(self.used_panel_indexs) == 1:
            lookFwdPercent = 0.33
            lookAtOthersPercent = 0
        else:
            lookFwdPercent = 0.2
            if len(self.used_panel_indexs) == 2:
                lookAtOthersPercent = 0.4
            else:
                lookAtOthersPercent = 0.65
        lookRandomPercent = 1.0 - lookFwdPercent - lookAtOthersPercent
        if lookAtChoice < lookFwdPercent:
            self.IsLookingAt[toonidx] = 'f'
            return Vec3(0, 1.5, 0)
        elif lookAtChoice < lookRandomPercent + lookFwdPercent or len(self.used_panel_indexs) == 1:
            self.IsLookingAt[toonidx] = 'r'
            return toonHead.getRandomForwardLookAtPoint()
        else:
            other_toon_idxs = []
            for i in range(len(self.IsLookingAt)):
                if self.IsLookingAt[i] == toonidx:
                    other_toon_idxs.append(i)

            if len(other_toon_idxs) == 1:
                IgnoreStarersPercent = 0.4
            else:
                IgnoreStarersPercent = 0.2
            NoticeStarersPercent = 0.5
            bStareTargetTurnsToMe = 0
            if len(other_toon_idxs) == 0 or random.random() < IgnoreStarersPercent:
                other_toon_idxs = []
                for i in self.used_panel_indexs:
                    if i != toonidx:
                        other_toon_idxs.append(i)

                if random.random() < NoticeStarersPercent:
                    bStareTargetTurnsToMe = 1
            if len(other_toon_idxs) == 0:
                return toonHead.getRandomForwardLookAtPoint()
            else:
                lookingAtIdx = random.choice(other_toon_idxs)
            if bStareTargetTurnsToMe:
                self.IsLookingAt[lookingAtIdx] = toonidx
                otherToonHead = None
                for panel in self.panelList:
                    if panel.position == lookingAtIdx:
                        otherToonHead = panel.headModel

                otherToonHead.doLookAroundToStareAt(otherToonHead, self.getLookAtToPosVec(lookingAtIdx, toonidx))
            self.IsLookingAt[toonidx] = lookingAtIdx
            return self.getLookAtToPosVec(toonidx, lookingAtIdx)

    def getLookAtToPosVec(self, fromIdx, toIdx):
        x = -(POSITIONS[toIdx][0] - POSITIONS[fromIdx][0])
        y = POSITIONS[toIdx][1] - POSITIONS[fromIdx][1]
        z = POSITIONS[toIdx][2] - POSITIONS[fromIdx][2]
        return Vec3(x, y, z)

    def initLookAtInfo(self):
        self.used_panel_indexs = []
        for panel in self.panelList:
            if panel.dna != None:
                self.used_panel_indexs.append(panel.position)

        if len(self.used_panel_indexs) == 0:
            return
        self.IsLookingAt = []
        for i in range(MAX_AVATARS):
            self.IsLookingAt.append('f')

        holidayIndex = loader.loadingScreen.getActiveHoliday()
        for panel in self.panelList:
            if panel.dna != None and not holidayIndex == ToontownGlobals.HolidayAprilFools:
                panel.headModel.setLookAtPositionCallbackArgs((self, panel.headModel, panel.position))

        return

    def unload(self):
        if self.isLoaded == 0:
            return None
        cleanupDialog('globalDialog')
        for panel in self.panelList:
            panel.destroy()

        del self.panelList
        self.title.removeNode()
        del self.title
        self.quitButton.destroy()
        del self.quitButton
        self.logoutButton.destroy()
        del self.logoutButton
        self.episodesButton.destroy()
        del self.episodesButton
        self.settingsButton.destroy()
        del self.settingsButton
        self.datapacksButton.destroy()
        del self.datapacksButton
        self.infoButton.destroy()
        del self.infoButton
        self.helpButton.destroy()
        del self.helpButton
        self.infoGui.unload()
        del self.infoGui
        self.packList.unload()
        del self.packList
        self.episodeSelector.unload()
        del self.episodeSelector
        self.welcomeGui.unload()
        del self.welcomeGui
        self.pickAToonBG.removeNode()
        del self.pickAToonBG
        del self.avatarList
        self.parentFSM.getCurrentState().removeChild(self.fsm)
        del self.parentFSM
        del self.fsm
        self.toon3DFrame.destroy()
        self.toon3DBack.destroy()
        self.toon3DPlayOrCreate.destroy()
        self.toon3DName.destroy()
        self.ignoreAll()
        self.isLoaded = False
        ModelPool.garbageCollect()
        TexturePool.garbageCollect()
        base.setBackgroundColor(ToontownGlobals.DefaultBackgroundColor)
        return None

    def __handlePanelDone(self, panelDoneStatus, panelChoice = 0):
        self.doneStatus = {}
        self.doneStatus['mode'] = panelDoneStatus
        self.choice = panelChoice
        if panelDoneStatus == 'chose':
            self.__handleChoice()
        elif panelDoneStatus == 'nameIt':
            self.__handleCreate()
        elif panelDoneStatus == 'delete':
            self.__handleDelete()
        elif panelDoneStatus == 'create':
            self.__handleCreate()

    def getChoice(self):
        return self.choice

    def __handleChoice(self):
        self.fsm.request('CheckDownload')

    def __handleCreate(self):
        base.transitions.fadeOut(finishIval = EventInterval(self.doneEvent, [self.doneStatus]))

    def __handleDelete(self):
        messenger.send(self.doneEvent, [self.doneStatus])

    def __handleQuit(self):
        cleanupDialog('globalDialog')
        self.doneStatus = {'mode': 'exit'}
        messenger.send(self.doneEvent, [self.doneStatus])

    def handleEpisode(self, episode):
        # Declare with the Episode Manager that we are in a particular Episode
        base.cr.episodeManager.setEpisode(episode)
        self.__handlePanelDone('chose')

    def enterChoose(self):
        pass

    def exitChoose(self):
        pass

    def enterCheckDownload(self):
        self.accept('downloadAck-response', self.__handleDownloadAck)
        self.downloadAck = DownloadForceAcknowledge.DownloadForceAcknowledge('downloadAck-response')
        self.downloadAck.enter(4)

    def exitCheckDownload(self):
        self.downloadAck.exit()
        self.downloadAck = None
        self.ignore('downloadAck-response')
        return

    def __handleDownloadAck(self, doneStatus):
        if doneStatus['mode'] == 'complete':
            base.transitions.fadeOut(finishIval = EventInterval(self.doneEvent, [self.doneStatus]))
        else:
            self.fsm.request('Choose')

    def __handleLogoutWithoutConfirm(self):
        base.cr.loginFSM.request('logout')
        base.cr.loginFSM.request('mainMenu')

    def __handleEpisodeSelect(self):
        self.episodeSelector.enter()

    def __handleInfo(self):
        self.infoGui.enter()

    def __handleWelcome(self):
        self.welcomeGui.enter()

    def __handleOptions(self):
        self.settingsScreen = SettingsScreen()
        OTPGUIUtils.Animations.popup(self.settingsScreen).start()

    def __handlePackList(self):
        self.packList.enter()

    def __clickToon(self, toon: Toon, playerId: Optional[int] = None):
        position = self.toonModels.index(toon)
        self.lastSelectedToon = toon
        ival = Parallel(
            Sequence(
                Func(self.__disableButtons),
                base.camera.posQuatInterval(0.5,
                                            Vec3(0, self.__getScaledDistance(toon, 8), toon.getHeight() * .8),
                                            Vec3(165, 0, 0),
                                            other = toon,
                                            blendType = 'easeInOut'
                                            ),
                Func(self.toon3DFrame.reparentTo, base.aspect2d),
                Parallel(
                    OTPGUIUtils.Animations.popup(self.toon3DName),
                    OTPGUIUtils.Animations.slideUp(self.toon3DLastSeen, .25, .05, intensity = 0.2),
                    OTPGUIUtils.Animations.slideUp(self.toon3DPlayOrCreate, .1, -0.1, intensity = 0.2),
                    OTPGUIUtils.Animations.slideUp(self.toon3DBack, -0.3, -0.5, intensity = 0.2),
                ),
                Func(self.__enableButtons)
            )
        )

        def setDitherShader(_d: float, _t: NodePath):
            _t.setShaderInput('dither', _d)

        hideToon = Parallel()
        for toonModel in self.toonModels:
            if toonModel != toon:
                hideToon.append(
                    LerpFunctionInterval(setDitherShader, 0.5, 1.0, 0.0, 'easeInOut', [toonModel.getGeomNode()]))
                toonModel.removeActive()
        ival.append(hideToon)
        ival.start()

        if toon.pickAToonExists:
            self.toon3DPlayOrCreate['text'] = TTLocalizer.AvatarChooserPlayThisToon
            self.toon3DPlayOrCreate['command'] = self.__playToon
            self.toon3DPlayOrCreate['extraArgs'] = [position]
            self.toon3DLastSeen.show()

            lastLoc: int = toon.pickAToonLastLocation
            # the last 2 must always be zero!
            lastLoc = lastLoc // 100
            lastLoc *= 100
            lastZoneNames: Tuple[str, str]
            try:
                if lastLoc in TTLocalizer.PlaygroundNameMap:
                    lastZoneNames = TTLocalizer.PlaygroundNameMap[lastLoc][1], TTLocalizer.PlaygroundNameMap[lastLoc][2]
                elif lastLoc >= 61000:
                    lastZoneNames = 'in an', 'activity'
                else:
                    if lastLoc in TTLocalizer.GlobalStreetNames:
                        lastZoneNames = TTLocalizer.GlobalStreetNames[lastLoc][1], TTLocalizer.GlobalStreetNames[lastLoc][2]
                    else:
                        lastZoneNames = (TTLocalizer.PlaygroundNameMap[ZoneUtil.getCanonicalHoodId(lastLoc)][1],
                                         TTLocalizer.PlaygroundNameMap[ZoneUtil.getCanonicalHoodId(lastLoc)][2])
            except KeyError:
                lastZoneNames = 'in', 'Toontown'

            self.toon3DLastSeen['text'] = TTLocalizer.AvatarChooserLastSeen.format(*lastZoneNames)
            self.toon3DName['text'] = toon.getName()
        else:
            self.toon3DPlayOrCreate['text'] = TTLocalizer.AvatarChooserMakeAToon
            self.toon3DPlayOrCreate['command'] = self.__createToon
            self.toon3DPlayOrCreate['extraArgs'] = [position]
            self.toon3DLastSeen.hide()
            self.toon3DName['text'] = TTLocalizer.AvatarChooserMakeAToon

    def __playToon(self, position: int):
        base.messenger.send(f'avChoicePanel-{position}', ['chose', position])

    def __createToon(self, position: int):
        base.messenger.send(f'avChoicePanel-{position}', ['create', position])

    def __handleBack(self):
        # TODO: THIS NEEDS TO BE ANIMATED!
        self.toon3DPlayOrCreate['command'] = None
        self.toon3DPlayOrCreate['extraArgs'] = None
        self.acceptOnce('clickedNametag', self.__clickToon)
        self.toon3DFrame.reparentTo(base.hidden)

        ival = Parallel(
            Sequence(
                base.camera.posQuatInterval(
                    0.5,
                    Vec3(*self.cameraPos3D[0:3]),
                    Vec3(*self.cameraPos3D[3:6]),
                    blendType = 'easeInOut')
            )
        )

        def setDitherShader(_d: float, _t: NodePath):
            _t.setShaderInput('dither', _d)

        hideToon = Parallel()
        for toonModel in self.toonModels:
            if toonModel != self.lastSelectedToon:
                hideToon.append(
                    Sequence(
                        LerpFunctionInterval(setDitherShader, 0.5, 0.0, 1.0, 'easeInOut', [toonModel.getGeomNode()]),
                        Func(toonModel.addActive)
                    )
                )
        ival.append(hideToon)

        ival.start()

    def __getScaledDistance(self, toon: Toon, distance: float) -> float:
        camHeight = toon.getHeight()
        heightScaleFactor = camHeight * 0.3333333333
        return distance * heightScaleFactor

    def __disableButtons(self):
        for button in (
        self.quitButton, self.episodesButton, self.logoutButton, self.infoButton, self.helpButton, self.settingsButton,
        self.datapacksButton):
            button['state'] = DGG.DISABLED

    def __enableButtons(self):
        for button in (
        self.quitButton, self.episodesButton, self.logoutButton, self.infoButton, self.helpButton, self.settingsButton,
        self.datapacksButton):
            button['state'] = DGG.NORMAL
