import builtins
import json
import os
import random
import webbrowser

from direct.fsm.FSM import FSM
from direct.gui import DirectGuiGlobals
from direct.gui.DirectButton import DirectButton
from direct.gui.DirectEntry import DirectEntry
from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectLabel import DirectLabel
from direct.gui.DirectScrolledList import DirectScrolledList
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import OnscreenText
from direct.interval.LerpInterval import LerpScaleInterval, LerpHprInterval, LerpFunctionInterval, LerpPosHprInterval
from direct.interval.MetaInterval import Parallel
from panda3d.core import TextNode, NodePath, ModelPool, TexturePool, HTTPClient, \
    DocumentSpec, HTTPChannel, Ramfile, VBase4, URLSpec
from panda3d.toontown import CFSpeech, CFThought, CFTimeout

from otp.otpbase.OTPLocalizerEnglish import CRLoadingGameServices
from otp.otpgui import OTPGUIUtils
from toontown.mainmenu.MainMenuGlobals import *
from toontown.mainmenu.MainMenuLoadingGUI import MainMenuLoadingGUI
from toontown.mainmenu.MainMenuZoneBR import MainMenuZoneBR
from toontown.mainmenu.MainMenuZoneBeta2 import MainMenuZoneBeta2
from toontown.mainmenu.MainMenuZoneDD import MainMenuZoneDD
from toontown.mainmenu.MainMenuZoneDG import MainMenuZoneDG
from toontown.mainmenu.MainMenuZoneDL import MainMenuZoneDL
from toontown.mainmenu.MainMenuZoneMM import MainMenuZoneMM
from toontown.mainmenu.MainMenuZoneTT import MainMenuZoneTT
from toontown.mainmenu.MiniserverItem import MiniserverItem
from toontown.mainmenu.OfflineModeSettings import OfflineModeSettings
from toontown.moviemaker.MovieMakerGUI import MovieMakerGUI
from toontown.toonbase import TTLocalizer, DisplayOptions, ToontownGlobals, ClientSettings
from toontown.toontowngui import TTDialog
from toontown.toontowngui.AnimatedButton import AnimatedButton
from toontown.toontowngui.HelpButton import HelpButton
from toontown.toontowngui.SettingsGUI import ToggleOption
from toontown.toontowngui.SettingsScreen import SettingsScreen


class ToontownMainMenu(FSM):
    avatarGui = loader.loadModel('phase_3/models/gui/ttoff_m_gui_launch_accIcons')
    avatars = [
        avatarGui.find('**/Cupcake'),  # 0
        avatarGui.find('**/Flower'),  # 1
        avatarGui.find('**/Flippy'),  # 2
        avatarGui.find('**/Star'),  # 3
        avatarGui.find('**/Troll'),  # 4
        avatarGui.find('**/Wand'),  # 5
        avatarGui.find('**/20Dog')  # 6
    ]

    DisplayOptions = None

    def __init__(self):
        FSM.__init__(self, 'ToontownMainMenu')
        self.isLoaded = False
        self.hoveredButton = None

    def load(self):
        """
        Load the ui
        :return:
        """
        if self.isLoaded:
            return

        base.loader.beginBulkLoad('mainmenu', TTLocalizer.HeadingToHood % {'to': 'to',
                                                                           'hood': 'the Main Menu'
                                                                           }, 31, 1, TTLocalizer.TIP_GENERAL)

        if not ToontownMainMenu.DisplayOptions:
            ToontownMainMenu.DisplayOptions = DisplayOptions.DisplayOptions()
        base.camera.setPosHpr(*HomeCameraPos)
        base.camLens.setMinFov(55)

        self.zone = random.choice(
               (
                   MainMenuZoneTT,
                   MainMenuZoneDD,
                   MainMenuZoneDG,
                   MainMenuZoneMM,
                   MainMenuZoneBR,
                   MainMenuZoneDL,
               )
        )()
        #self.zone = MainMenuZoneBeta2()
        self.geom = self.zone.geom

        # Add the character
        self.char = self.zone.char

        self.loggedInAsLabel = OnscreenText(
            parent = base.a2dTopRight,
            text = TTLocalizer.MainMenuNotLoggedIn,
            align = TextNode.ARight,
            pos = LoggedInAsLabelPos,
            scale = LoggedInAsLabelScale,
            fg = VBase4(1.0),
            shadow = VBase4(0.0, 0.0, 0.0, 1.0)
        )

        self.switchAccountsButton = AnimatedButton(
            relief = None,
            parent = base.a2dTopRight,
            pos = SwitchAccountsButtonPos,
            scale = SwitchAccountsButtonScale,
            image = self.avatars[0],
            command = lambda: self.request('Accounts')
        )
        mmgui = loader.loadModel('phase_3/models/gui/ttrm_m_gui_launch_mainGui')  # type: NodePath
        self.switchAccountsHover = OnscreenImage(
            parent = base.a2dTopRight,
            image = mmgui.find('**/SwitchProfileHover'),
            scale = SwitchAccountsHoverScale
        )
        mmgui.removeNode()

        self.switchAccountsHover.setPos(self.switchAccountsButton, SwitchAccountsHoverPos)
        self.switchAccountsHover.hide()
        self.switchAccountsHover.setBin('unsorted', 0)

        self.switchAccountsButton.bind(DirectGuiGlobals.WITHIN, self.__profileHoverOn)
        self.switchAccountsButton.bind(DirectGuiGlobals.WITHOUT, self.__profileHoverOff)

        self.isLoaded = True
        http = HTTPClient.getGlobalPtr()  # type: HTTPClient
        self.url = DocumentSpec(MiniserverListUrl)
        self.ch = http.makeChannel(True)  # type: HTTPChannel
        http.setVerifySsl(HTTPClient.VSNoVerify)
        self.ch.beginGetHeader(self.url)
        self.addTask(self.downloadHeaderTask, 'downloadHeader')
        # for debugging the gui: throttle download
        # self.ch.setDownloadThrottle(1)
        # self.ch.setMaxBytesPerSecond(2000)
        self.gotHeader = False

        self.serverListFilters = [1,  # Verified Only
                                  0,  # TODO
                                  0]

        self.previousChatterStr = ''
        # self.addTask(self.charChatterTask, 'charChatterTask', delay = random.randint(5, 8))


    def __checkLaunchOption(self, task = None):
        if _env := os.environ.get('TTOFF_LAUNCH_SERVER', '') is not '':
            print(_env)
            if _env.startswith('ttrealms://'):
                _env = _env.replace('ttrealms://', '')
            self.connect(_env)
            os.environ['TTOFF_LAUNCH_SERVER'] = ''
        return 0

    def charChatterTask(self, task = None):
        holidayName = ToontownGlobals.BackgroundNodeNames[loader.loadingScreen.getActiveHoliday()]
        if holidayName not in TTLocalizer.MainMenuCharChatter:
            holidayName = "default"
        chatterOptions = TTLocalizer.MainMenuCharChatter[holidayName][self.zone.zone][:]
        if self.previousChatterStr:
            chatterOptions.remove(self.previousChatterStr)
        chosenChatterString = random.choice(chatterOptions)
        self.previousChatterStr = chosenChatterString

        if self.char.style.name in ['p', 'wp', 'd']:
            self.char.setChatAbsolute(chosenChatterString, CFThought | CFTimeout)
        else:
            self.char.setChatAbsolute(chosenChatterString, CFSpeech | CFTimeout)

        task.delayTime = random.randint(14, 20)
        return task.again

    def __profileHoverOn(self, e):
        self.switchAccountsHover.show()

    def __profileHoverOff(self, e):
        self.switchAccountsHover.hide()

    def downloadHeaderTask(self, task):
        result = self.ch.run()
        if result == 0:
            base.graphicsEngine.renderFrame()
            base.loader.endBulkLoad('mainmenu')
            return task.done

        return task.cont

    def unload(self):
        if not self.isLoaded:
            return
        self.char.delete()
        self.removeAllTasks()
        # self.logo.destroy()
        self.zone.unload()

        self.loggedInAsLabel.destroy()
        self.switchAccountsButton.destroy()
        self.switchAccountsHover.destroy()
        ModelPool.garbageCollect()
        TexturePool.garbageCollect()

        self.request('Off')

        self.isLoaded = False

    def enterHome(self):
        """
        The Home tab will include a play offline button, a multiplayer button, and a settings button
        :return:
        """

        mmgui = loader.loadModel('phase_3/models/gui/ttrm_m_gui_launch_mainGui')  # type: NodePath

        settingsDecorationModel = loader.loadModel('phase_3/models/gui/ttoff_m_gui_opts_colorpicker')  # type: NodePath
        settingsSliderModel = loader.loadModel('phase_3/models/gui/ttoff_m_gui_opts_slider')  # type: NodePath
        settingsButtonsModel = loader.loadModel('phase_3/models/gui/ttoff_m_gui_opts_buttons')  # type: NodePath
        # self.sign.find('**/offline').show()
        # self.sign.find('**/online').show()
        # self.sign.find('**/options').show()
        # self.sign.find('**/quit').show()
        # self.sign.find('**/back').hide()
        # self.logo = OnscreenImage(
        #        parent = base.a2dTopCenter,
        #        pos = LogoPos,
        #        image = 'phase_3/maps/toontown-logo.png',
        #        scale = LogoAspect
        # )
        # self.logo.setTransparency(TransparencyAttrib.MAlpha)
        # self.logo.setScale(self.logo, LogoScale)

        # if loader.loadingScreen.getActiveHoliday() == ToontownGlobals.HolidayHalloween:
        #   hgui = loader.loadModel('phase_3/models/gui/ttoff_m_gui_launch_halloweenGui')  # type: NodePath
        #  guiModel = hgui
        # else:
        guiModel = mmgui
        self.offlineButton = AnimatedButton(
            relief = None,
            parent = base.a2dBottomCenter,
            pos = HomeOfflineButtonPos,
            image = (guiModel.find('**/PlayOffline_Normal'),
                     guiModel.find('**/PlayOffline_Hover'),
                     guiModel.find('**/PlayOffline_Hover'),
                     guiModel.find('**/PlayOffline_Hover')),
            image_scale = 0.5,
            pressEffect = False,
            command = lambda: self.request('Offline')
        )
        self.multiplayerButton = AnimatedButton(
            relief = None,
            parent = base.a2dBottomCenter,
            pos = HomeMultiplayerButtonPos,
            image = (guiModel.find('**/PlayOnline_Normal'),
                     guiModel.find('**/PlayOnline_Hover'),
                     guiModel.find('**/PlayOnline_Hover'),
                     guiModel.find('**/PlayOnline_Hover')),
            image_scale = 0.5,
            pressEffect = False,
            command = lambda: self.request('Multiplayer')
        )
        self.optionsButton = AnimatedButton(
            relief = None,
            parent = base.a2dBottomRight,
            pos = HomeOptionsButtonPos,
            image = (
                mmgui.find('**/Options_Normal'),
                mmgui.find('**/Options_Hover'),
                mmgui.find('**/Options_Hover'),
                mmgui.find('**/Options_Hover')
            ),
            image_scale = (2.93, 1, 1),
            scale = 0.2,
            pressEffect = False,
            command = self.__handleOptions
        )

        self.quitButton = AnimatedButton(
            relief = None,
            parent = base.a2dBottomLeft,
            pos = HomeQuitButtonPos,
            image = (mmgui.find('**/Quit_Normal'),
                     mmgui.find('**/Quit_Hover'),
                     mmgui.find('**/Quit_Hover'),
                     mmgui.find('**/Quit_Hover')),
            image_scale = OTPGUIUtils.getImageScale(671, 693, 0.425),
            pressEffect = False,
            command = self.__handleQuit
        )
        self.quitArrow = OnscreenImage(
            parent = self.quitButton,
            pos = HomeQuitArrowPos,
            image = mmgui.find('**/Quit_Arrow'),
            scale = OTPGUIUtils.getImageScale(428, 391, 0.25)
        )

        self.debugMenu = DirectFrame(
            relief = None,
            parent = base.a2dTopRight,
            pos = (-0.35, 0, -0.6),
            image = MovieMakerGUI.gui.find('**/actor_editor_bg'),
            image_scale = OTPGUIUtils.getImageScale(646, 932),
            state = DirectGuiGlobals.NORMAL
        )

        self.movieMakerButton = DirectButton(
            parent = self.debugMenu,
            pos = (-.13, 0, .3),
            frameSize = (-2.5, 2.5, -1, 1),
            text = 'Movie\nMaker',
            text_pos = (0, 0.15),
            text_scale = 0.7,
            scale = 0.05,
            command = self.__enterMovieMaker
        )

        self.levelEditorButton = DirectButton(
            parent = self.debugMenu,
            pos = (.13, 0, .3),
            frameSize = (-2.5, 2.5, -1, 1),
            text = 'Level\nEditor',
            text_pos = (0, 0.15),
            text_scale = 0.7,
            scale = 0.05,
            command = self.__enterLevelEditor
        )
        self.debugMenu.hide()

        def __setButtonRoll(roll: float):
            self.quitButton['image_hpr'] = (0, 0, roll)

        self.portalRotateIval = LerpFunctionInterval(__setButtonRoll, duration = 90, fromData = 0, toData = 360)
        self.portalRotateIval.loop()

        self.newsPostFrame = DirectFrame(
            pos = (.35, 0, -.25),
            parent = base.a2dTopLeft,
            relief = None,
            image_scale = (0.6, 1.0, 0.4),
            image = settingsDecorationModel.find('**/temp_bg'))
        OnscreenText("Dreamy Drive is now open! Press below for an introduction!",
                     parent = self.newsPostFrame,
                     pos = (0, 0.08),
                     scale = 0.0375, wordwrap = 15)
        AnimatedButton(parent = self.newsPostFrame, pos = (0, 0, -0.1), text = "Read More", scale = 0.4,
                       text_scale = 0.08,
                       image_scale = (0.8, 1.0, 0.22),
                       text_pos = (0.0, -0.024),
                       relief = None,
                       image = (settingsButtonsModel.find('**/button_green_up'),
                                settingsButtonsModel.find('**/button_green_down'),
                                settingsButtonsModel.find('**/button_green_rollover'),
                                settingsButtonsModel.find('**/button_inactive')),
                       command = lambda: webbrowser.open('https://toontownrealms.com/events/welcometodreamydrive'))

        # Discard these unneeded models
        mmgui.removeNode()
        settingsSliderModel.removeNode()
        settingsDecorationModel.removeNode()
        settingsButtonsModel.removeNode()

        # Check if a user has used the --server launch option  in the launcher (or more likely the url protocol)
        self.addTask(self.__checkLaunchOption, '__checkLaunchOption')
        self.accept('`', self.debugMenu.show)

    def exitHome(self):
        self.ignore('`')
        self.offlineButton.destroy()
        self.multiplayerButton.destroy()
        self.optionsButton.destroy()
        self.portalRotateIval.finish()
        self.quitButton.destroy()
        self.quitArrow.destroy()
        self.debugMenu.destroy()
        self.newsPostFrame.destroy()

    def __handleOptions(self):
        self.settingsScreen = SettingsScreen()
        OTPGUIUtils.Animations.popup(self.settingsScreen).start()

    def __handleQuit(self):
        base.cr.loginFSM.request('shutdown')

    def enterOffline(self):
        """
        Offline mode screen
        ----
        Gives the user the option to start an offline session, and the ability to change
        the 'server' settings.

        self.startOfflineServer()
        """
        self.startingOffline = False
        mmgui = loader.loadModel('phase_3/models/gui/ttrm_m_gui_launch_mainGui')  # type: NodePath

        gui = loader.loadModel('phase_3/models/gui/ttoff_m_gui_opts_buttons')  # type: NodePath
        buttonTextures = (gui.find('**/button_green_up'),
                          gui.find('**/button_green_down'),
                          gui.find('**/button_green_rollover'),
                          gui.find('**/button_inactive'))  # type: tuple[NodePath, NodePath, NodePath, NodePath]
        self.backButton = AnimatedButton(
            relief = None,
            parent = base.a2dBottomRight,
            pos = OfflineBackButton,
            image = buttonTextures,
            image_scale = ButtonImageScale,
            pressEffect = False,
            text = TTLocalizer.MakeAToonLast,
            text_scale = ButtonTextScale,
            text_pos = ButtonTextPos,
            command = lambda: self.request('Home')
        )

        self.offlineSettings = OfflineModeSettings()
        self.offlineSettings.reparentTo(base.aspect2d)
        self.offlineSettings.setPos(-.3, 0, 0)
        self.offlineSettings.setScale(0.9)

        self.offlineStartButton = DirectButton(
            relief = None,
            parent = self.offlineSettings,
            pos = (.4, 0, -0.63),
            image = (mmgui.find('**/off_enter_normal'),
                     mmgui.find('**/off_enter_press'),
                     mmgui.find('**/off_enter_hover')),
            image_scale = OTPGUIUtils.getImageScale(739, 248, 1.0),
            image1_scale = OTPGUIUtils.getImageScale(741, 250, 1.0),
            scale = 0.3,
            pressEffect = False,
            command = self.startOfflineServer
        )
        mmgui.removeNode()
        gui.removeNode()

        if ClientSettings.GUIAnimations.get():
            Parallel(
                #LerpFunctionInterval(base.camLens.setMinFov, 0.5, fromData = 55, toData = 45, blendType = 'easeInOut'),
                #LerpPosHprInterval(base.camera, 0.5,
                #                   Vec3(-10, -6.4, 2.8),
                #                   Vec3(-75, 5, 0.0), blendType = 'easeInOut'
                #                   ),
                OTPGUIUtils.Animations.slideUp(self.offlineSettings, finalZ = 0.0, startZ = -.5, intensity = 0.5),
                OTPGUIUtils.Animations.popup(self.backButton),
            ).start()

        url = URLSpec('127.0.0.1', 1)
        url.setPort(7198)
        base.cr.connect([url], successCallback = self.__success, failureCallback = self.__failure)

    def __success(self):
        if hasattr(self, 'startingOffline') and self.startingOffline:
            return
        self.__alreadyHostingServerDialog = TTDialog.TTDialog(style = TTDialog.YesNo, text = TTLocalizer.MainMenuFoundLocalServer, command = self.__alreadyHostingCallback)
        self.__alreadyHostingServerDialog.show()

    def __alreadyHostingCallback(self, value):
        self.__alreadyHostingServerDialog.destroy()
        self.__alreadyHostingServerDialog = None
        if value > 0:
            self.connect('127.0.0.1')

    def __failure(self, *args):
        return

    def exitOffline(self):
        self.offlineStartButton.destroy()
        self.backButton.destroy()
        del self.offlineStartButton
        del self.backButton
        self.offlineSettings.destroy()
        del self.offlineSettings
        #Parallel(
        #    LerpPosHprInterval(
        #        base.camera, 0.5,
        #        Vec3(-10, -8.5, 2.8),
        #        Vec3(-60, 5, 0.0),
        #        blendType = 'easeInOut'
        #    ),
        #    LerpFunctionInterval(base.camLens.setMinFov, 0.5, fromData = 45, toData = 55, blendType = 'easeInOut')
        #).start()

    def enterMultiplayer(self):
        """
        The multiplayer screen will have a list of bookmarked servers, an IP input, and a button to access the
        official server list
        :return:
        """
        # base.camera.setPosHpr(*MultiplayerCameraPos)

        # self.sign.find('**/offline').hide()
        # self.sign.find('**/online').hide()
        # self.sign.find('**/options').hide()
        # self.sign.find('**/quit').hide()
        # self.sign.find('**/back').show()
        gui = loader.loadModel('phase_3/models/gui/ttoff_m_gui_opts_buttons')  # type: NodePath
        buttonTextures = (gui.find('**/button_green_up'),
                          gui.find('**/button_green_down'),
                          gui.find('**/button_green_rollover'),
                          gui.find('**/button_inactive'))  # type: tuple[NodePath, NodePath, NodePath, NodePath]

        mmGui = loader.loadModel('phase_3/models/gui/ttrm_m_gui_launch_mainGui')  # type: NodePath

        settingsDecorationModel = loader.loadModel('phase_3/models/gui/ttoff_m_gui_opts_colorpicker')  # type: NodePath
        self.bottomBar = DirectFrame(
            relief = None,
            parent = base.a2dBottomCenter,
            pos = MultiplayerBottomBarPos,
            image = mmGui.find('**/ServerListItem'),
            image_scale = MultiplayerServerListGeomScale,
            scale = 1.6
        )
        self.directConnectButton = AnimatedButton(
            relief = None,
            parent = base.a2dBottomCenter,
            pos = MultiplayerDirectConnectPos,
            image = buttonTextures,
            image_scale = ButtonImageScale,
            pressEffect = False,
            text = TTLocalizer.MainMenuServerListDirectConnect,
            text_scale = ButtonTextScale,
            text_pos = ButtonTextPos,
            command = lambda: self.request('DirectConnect')
        )
        self.backButton = AnimatedButton(
            relief = None,
            parent = base.a2dBottomCenter,
            pos = MultiplayerBackPos,
            image = buttonTextures,
            image_scale = ButtonImageScale,
            pressEffect = False,
            text = TTLocalizer.MakeAToonLast,
            text_scale = ButtonTextScale,
            text_pos = ButtonTextPos,
            command = lambda: self.request('Home')
        )

        self.filtersLabel = OnscreenText(
            parent = base.a2dBottomCenter,
            # pos = MultiplayerFiltersLabel,
            text = 'Filters',
            scale = 0.05
        )
        self.filtersLabel.set_pos(MultiplayerFiltersLabel)

        self.toggleVerifiedFilterButton = DirectButton(
            relief = None,
            parent = base.a2dBottomCenter,
            image = (ToggleOption.offTextures, ToggleOption.onTextures)[self.serverListFilters[0]],
            pos = MultiplayerVerifyTogglePos,
            text_scale = 0.055,
            text_pos = (.065, -0.015),
            text_align = TextNode.ALeft,
            text = 'Verified Realms',
            command = self.toggleFilter,
            image_scale = 0.08,
            extraArgs = [0],
            pressEffect = False
        )

        self.toggleLegitFilterButton = DirectButton(
            relief = None,
            parent = base.a2dBottomCenter,
            image = (ToggleOption.offTextures, ToggleOption.onTextures)[self.serverListFilters[1]],
            pos = MultiplayerLegitTogglePos,
            text_scale = 0.055,
            text_pos = (.065, -0.015),
            text_align = TextNode.ALeft,
            text = 'Legit Realms',
            command = self.toggleFilter,
            image_scale = 0.08,
            extraArgs = [1],
            pressEffect = False
        )
        self.dlBlocker = MainMenuLoadingGUI(text = TTLocalizer.MainMenuFetchingServers,
                                            indeterminate = True,
                                            mini = True)
        ## removed for open source release
        #self.ch.beginGetDocument(self.url)
        #self.ramFile = Ramfile()
        #self.ch.downloadToRam(self.ramFile)
        #self.addTask(self.downloadListTask, 'downloadServerListTask')
        # Discard these unneeded models
        gui.removeNode()
        mmGui.removeNode()
        settingsDecorationModel.removeNode()

        if ClientSettings.GUIAnimations.get():
            Parallel(
                OTPGUIUtils.Animations.slideUp(self.bottomBar, finalZ = 0.2, intensity = 1),
                OTPGUIUtils.Animations.slideUp(self.directConnectButton, finalZ = 0.14, startZ = -0.06, intensity = 1),
                OTPGUIUtils.Animations.slideUp(self.backButton, finalZ = 0.26, startZ = 0.06, intensity = 1),
                OTPGUIUtils.Animations.slideUp(self.filtersLabel, finalZ = 0.28, startZ = 0.08, intensity = 1),
                OTPGUIUtils.Animations.slideUp(self.toggleVerifiedFilterButton, finalZ = 0.22, startZ = 0.02, intensity = 1),
                OTPGUIUtils.Animations.slideUp(self.toggleLegitFilterButton, finalZ = 0.15, startZ = -0.05, intensity = 1),
            ).start()

    def exitMultiplayer(self):
        self.removeTask('downloadServerListTask')
        if self.dlBlocker:
            self.dlBlocker.destroy()
            del self.dlBlocker
        if hasattr(self, 'serverList'):
            self.serverList.destroy()
            del self.serverList
        self.ch.reset()
        self.filtersLabel.destroy()
        self.toggleVerifiedFilterButton.destroy()
        self.toggleLegitFilterButton.destroy()
        self.bottomBar.destroy()
        self.directConnectButton.destroy()
        del self.directConnectButton
        self.backButton.destroy()
        del self.backButton

    def toggleFilter(self, filter):
        self.serverListFilters[filter] = not self.serverListFilters[filter]
        self.request('Multiplayer')

    def enterAddServer(self):
        pass

    def exitAddServer(self):
        pass

    def enterDirectConnect(self):
        gui = loader.loadModel('phase_3/models/gui/ttoff_m_gui_opts_buttons')  # type: NodePath
        buttonTextures = (gui.find('**/button_green_up'),
                          gui.find('**/button_green_down'),
                          gui.find('**/button_green_rollover'),
                          gui.find('**/button_inactive'))  # type: tuple[NodePath, NodePath, NodePath, NodePath]

        settingsDecorationModel = loader.loadModel('phase_3/models/gui/ttoff_m_gui_opts_colorpicker')  # type: NodePath
        base.transitions.fadeScreen(0.4)
        # Create the UI
        self.entryFrame = DirectFrame(
            parent = aspect2dp,
            relief = None,
            image = settingsDecorationModel.find('**/temp_bg'))
        self.ipInput = DirectEntry(
            parent = self.entryFrame,
            scale = 0.05,
            text_align = TextNode.ACenter,
            width = 18)
        lastIp = ClientSettings.LastDirectConnectAddress.get()
        self.ipInput.enterText(lastIp)
        self.connectButton = AnimatedButton(
            relief = None,
            parent = base.a2dpBottomCenter,
            pos = DirectConnectConnectPos,
            image = buttonTextures,
            image_scale = (.4, 1, .11),
            pressEffect = False,
            text = TTLocalizer.MainMenuServerConnect,
            text_scale = 0.055,
            text_pos = (0.0, -0.015),
            command = self.connect
        )
        self.backButton = AnimatedButton(
            relief = None,
            parent = base.a2dpBottomCenter,
            pos = GenericBackPos,
            image = buttonTextures,
            image_scale = ButtonImageScale,
            pressEffect = False,
            text = TTLocalizer.MakeAToonLast,
            text_scale = ButtonTextScale,
            text_pos = ButtonTextPos,
            command = lambda: self.request('Multiplayer')
        )
        # Discard these unneeded models
        gui.removeNode()
        settingsDecorationModel.removeNode()

        if ClientSettings.GUIAnimations.get():
            OTPGUIUtils.Animations.popup(self.entryFrame, 1.0).start()

    def exitDirectConnect(self):
        base.transitions.noFade()
        self.entryFrame.destroy()
        self.ipInput.destroy()
        self.connectButton.destroy()
        self.backButton.destroy()

    def downloadListTask(self, task):
        result = self.ch.run()
        # if task.time > 0.3 and self.dlBlocker.mini:
        #    self.dlBlocker.setMini(False)
        # if self.ch.isValid():
        #    self.dlBlocker.setPercentage((self.ch.getBytesDownloaded() / self.ch.getFileSize()) * 100.0)
        if result == 0:
            self.notify.debug('Done downloading server list')
            self.dlBlocker.destroy()
            self.dlBlocker = None

            if self.ch.getStatusCode() != 200:
                self.notify.warning("ERROR DOWNLOADING " + str(self.ch.getStatusCode()) + str(self.ch.getStatusString()))
                return task.done

            self.serverListData = json.loads(self.ramFile.getData())

            self.ramFile.clear()

            self.__populateServerList()

            return task.done
        return task.cont

    def __populateServerList(self):
        filteredList = []
        for server in self.serverListData:
            valid = True
            if self.serverListFilters[0] and server['Verified'] == "none":
                valid = False

            if self.serverListFilters[1] and not server['LegitMode']:
                valid = False

            if valid:
                filteredList.append(server)

        def makeButton(data):  # type: (dict) -> MiniserverItem
            btn = MiniserverItem(data)
            return btn

        gui = loader.loadModel('phase_3/models/gui/ttoff_m_gui_opts_buttons')  # type: NodePath
        buttonTextures = (gui.find('**/button_green_up'),
                          gui.find('**/button_green_down'),
                          gui.find('**/button_green_rollover'),
                          gui.find('**/button_inactive'))  # type: tuple[NodePath, ...]
        self.serverList = DirectScrolledList(
            parent = aspect2d,
            relief = None,
            numItemsVisible = 6,
            itemFrame_scale = 1,
            itemFrame_frameSize = (-.4, .4, -.6, .3),
            pos = MultiplayerServerListPos,
            itemFrame_relief = None,
            incButton_image = (
                gui.find('**/arrow_l_normal'),
                gui.find('**/arrow_l_click'),
                gui.find('**/arrow_l_hover'),
                gui.find('**/arrow_l_disabled')
            ),
            incButton_relief = None,
            incButton_pressEffect = False,
            incButton_pos = (0.0, 0.0, -1.15),
            incButton_scale = (0.1, 1, 0.2),
            incButton_hpr = (0, 0, -90),
            decButton_image = (
                gui.find('**/arrow_r_normal'),
                gui.find('**/arrow_r_click'),
                gui.find('**/arrow_r_hover'),
                gui.find('**/arrow_r_disabled')
            ),
            decButton_relief = None,
            decButton_pressEffect = False,
            decButton_pos = (0.0, 0.0, 0.15),
            decButton_scale = (0.1, 1, 0.2),
            decButton_hpr = (0, 0, -90),

        )
        if not self.serverListFilters[0]:
            self.serverList.addItem(
                DirectLabel(text = TTLocalizer.MainMenuUnverifiedWarning, text_fg = (1.0, 1.0, 1.0, 1.0), text_bg = (1.0, 0.0, 0.0, 0.4), text_wordwrap = 60, text_scale = 0.05,
                            relief = None)
            )

        for i in filteredList:
            self.serverList.addItem(makeButton(i))

        if len(filteredList) < self.serverList['numItemsVisible']:
            self.serverList['decButton_image'] = None
            self.serverList['incButton_image'] = None

        if self.serverListFilters[0]:
            numUnverified = len([x for x in self.serverListData if x['Verified'] == 'none'])
            self.serverList.addItem(DirectLabel(text = f'+ {numUnverified} unverified realms', text_scale = 0.05, relief = None))
        gui.removeNode()

        if ClientSettings.GUIAnimations.get():
            OTPGUIUtils.Animations.slideUp(self.serverList, finalZ = 0.6, startZ = 0).start()

    def enterConnecting(self):
        #base.camera.setPosHpr(*HomeCameraPos)
        self.switchAccountsButton['state'] = DirectGuiGlobals.DISABLED

    def exitConnecting(self):
        self.switchAccountsButton['state'] = DirectGuiGlobals.NORMAL

    def enterFail(self):
        pass

    def exitFail(self):
        pass

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    def connect(self, ip = None):
        if ip is None:
            ip = self.ipInput.get(plain = True)
            ClientSettings.LastDirectConnectAddress.set(ip)

        if ip == '':
            return

        base.connectToMiniserver(ip)

    def startOfflineServer(self):
        self.startingOffline = True
        builtins.gameServicesDialog = MainMenuLoadingGUI(text = CRLoadingGameServices)
        builtins.gameServicesDialog.show()
        from toontown.server.DedicatedServer import DedicatedServer
        builtins.localServer = DedicatedServer(isLocal = True)
        builtins.localServer.start()

        def localServerReady():
            builtins.gameServicesDialog.destroy()
            del builtins.gameServicesDialog
            base.connectToMiniserver('127.0.0.1')

        self.acceptOnce('localServerReady', localServerReady)

    ''' ACCOUNTS '''

    def enterAddAccount(self):
        self.switchAccountsButton['state'] = DirectGuiGlobals.DISABLED
        gui = loader.loadModel('phase_3/models/gui/ttoff_m_gui_opts_buttons')  # type: NodePath
        settingsDecorationModel = loader.loadModel('phase_3/models/gui/ttoff_m_gui_opts_colorpicker')  # type: NodePath
        base.transitions.fadeScreen(0.4)
        buttonTextures = (gui.find('**/button_green_up'),
                          gui.find('**/button_green_down'),
                          gui.find('**/button_green_rollover'),
                          gui.find('**/button_inactive'))
        mmgui = loader.loadModel('phase_3/models/gui/ttrm_m_gui_launch_mainGui')  # type: NodePath
        cdrGui = loader.loadModel('phase_3.5/models/gui/tt_m_gui_sbk_codeRedemptionGui')  # type: NodePath

        self.addAccountEntryFrame = DirectFrame(
            parent = aspect2dp,
            relief = None,
            image = settingsDecorationModel.find('**/temp_bg'),
            image_scale = 1.1
        )
        self.addAccountTitle = OnscreenImage(parent = self.addAccountEntryFrame,
                                             image = mmgui.find('**/CreateProfileTitle'),
                                             pos = (0, 0, 0.45),
                                             scale = (1, 1, 0.125))
        self.usernameLabel = OnscreenText(
            parent = self.addAccountEntryFrame,
            text = TTLocalizer.MainMenuAccountUsername,
            scale = 0.05,
            pos = AccountsUsernameLabelPos
        )
        self.usernameEntry = DirectEntry(
            parent = self.addAccountEntryFrame,
            relief = None,
            pos = AccountsUsernameInputPos,
            image = cdrGui.find('**/tt_t_gui_sbk_cdrCodeBox'),
            text_scale = 0.05,
            scale = 0.7,
            text_align = TextNode.ACenter,
            width = 12
        )

        self.displayNameLabel = OnscreenText(
            parent = self.addAccountEntryFrame,
            text = TTLocalizer.MainMenuAccountDisplayName,
            scale = 0.05,
            pos = AccountsDisplayNameLabelPos
        )
        self.displayNameEntry = DirectEntry(
            parent = self.addAccountEntryFrame,
            relief = None,
            pos = AccountsDisplayNameInputPos,
            image = cdrGui.find('**/tt_t_gui_sbk_cdrCodeBox'),
            text_scale = 0.05,
            scale = 0.7,
            text_align = TextNode.ACenter,
            width = 12
        )

        # self.addIconSelector = AnimatedButton
        self.__accountCreatorActiveIcon = 0
        self.__profileCreatorBtns = []

        for index, icon in enumerate(self.avatars):
            icon = AnimatedButton(
                relief = None,
                parent = self.addAccountEntryFrame,
                pos = (-.45 + (0.15 * index), 0, 0.25),
                image = icon,
                image0_color = VBase4(1.0, 1.0, 1.0, 0.4),
                scale = AccountsListIconScale / 1.4,
                pressEffect = False,
                command = self.__selectIcon, extraArgs = [index]
            )
            self.__profileCreatorBtns.append(icon)

        self.__profileCreatorBtns[self.__accountCreatorActiveIcon]['state'] = DirectGuiGlobals.DISABLED

        self.displayHelp = HelpButton(parent = self.addAccountEntryFrame,
                                      pos = AccountsDisplayNameHelpPos,
                                      contents = TTLocalizer.MainMenuDisplayNameHelp)

        self.usernameHelp = HelpButton(parent = self.addAccountEntryFrame,
                                       pos = AccountsUsernameHelpPos,
                                       contents = TTLocalizer.MainMenuUsernameHelp)
        mmgui.removeNode()
        del mmgui
        self.addSubmitButton = AnimatedButton(
            relief = None,
            parent = base.a2dpBottomCenter,
            pos = DirectConnectConnectPos,
            image = buttonTextures,
            image_scale = (.4, 1, .11),
            pressEffect = False,
            text = TTLocalizer.MainMenuAccountAdd,
            text_scale = 0.055,
            text_pos = (0.0, -0.015),
            command = self.addAccount
        )
        self.backButton = AnimatedButton(
            relief = None,
            parent = base.a2dpBottomCenter,
            pos = GenericBackPos,
            image = buttonTextures,
            image_scale = ButtonImageScale,
            pressEffect = False,
            text = TTLocalizer.MakeAToonLast,
            text_scale = ButtonTextScale,
            text_pos = ButtonTextPos,
            command = lambda: self.request('Home')
        )

        if base.cr.requireAccountAction == 'MigrateAccount':
            self.usernameEntry.set(ClientSettings.SelectedAccount.get())
        if base.cr.requireAccountAction in ('MigrateAccount', 'AddAccount', 'ChooseAccount'):
            self.backButton['state'] = DirectGuiGlobals.DISABLED

        gui.removeNode()

    def exitAddAccount(self):
        base.transitions.noFade()
        self.addAccountEntryFrame.destroy()
        self.displayNameLabel.destroy()
        self.displayNameEntry.destroy()
        self.usernameLabel.destroy()
        self.usernameEntry.destroy()
        self.backButton.destroy()
        self.addSubmitButton.destroy()
        self.switchAccountsButton['state'] = DirectGuiGlobals.NORMAL
        pass

    def __selectIcon(self, index):
        self.__accountCreatorActiveIcon = index
        for i, btn in enumerate(self.__profileCreatorBtns):
            btn['state'] = DirectGuiGlobals.DISABLED if i == index else DirectGuiGlobals.NORMAL

    def addAccount(self):
        """
        Add the entered account info in the ADD ACCOUNT screen to the saved accounts list
        """
        displayName = self.displayNameEntry.get(True)
        userName = self.usernameEntry.get(True)
        if displayName != '' and userName != '':
            if userName not in base.cr.accountData:
                base.cr.accountData[userName] = {
                    "display_name": displayName,
                    "avatar": self.__accountCreatorActiveIcon
                }
                self.chooseAccount(userName)
                self.request('Home')

    def chooseAccount(self, username):  # type: (str) -> None
        """
        Log into an account
        :param username: The secret username
        """
        if username in list(base.cr.accountData.keys()):
            self.activeAccount = username
            ClientSettings.SelectedAccount.set(self.activeAccount)
            base.cr.playToken = self.activeAccount
            self.loggedInAsLabel['text'] = TTLocalizer.MainMenuLoggedInAs % \
                                           base.cr.accountData[self.activeAccount]['display_name']
            self.switchAccountsButton['image'] = self.avatars[base.cr.accountData[self.activeAccount]['avatar']]

    def enterAccounts(self):
        self.accountButtons = []  # type: list[AnimatedButton]
        base.transitions.fadeScreen(0.4)
        gui = loader.loadModel('phase_3/models/gui/ttoff_m_gui_opts_buttons')  # type: NodePath
        buttonTextures = (gui.find('**/button_green_up'),
                          gui.find('**/button_green_down'),
                          gui.find('**/button_green_rollover'),
                          gui.find('**/button_inactive'))
        self.backButton = AnimatedButton(
            relief = None,
            parent = base.a2dpBottomCenter,
            pos = GenericBackPos,
            image = buttonTextures,
            image_scale = ButtonImageScale,
            pressEffect = False,
            text = TTLocalizer.MakeAToonLast,
            text_scale = ButtonTextScale,
            text_pos = ButtonTextPos,
            command = lambda: self.request('Home')
        )
        self.addAccountButton = AnimatedButton(
            relief = None,
            parent = base.a2dpBottomCenter,
            pos = DirectConnectConnectPos,
            image = buttonTextures,
            image_scale = ButtonImageScale,
            pressEffect = False,
            text = TTLocalizer.MainMenuAccountAdd,
            text_scale = ButtonTextScale,
            text_pos = ButtonTextPos,
            command = lambda: self.request('AddAccount')
        )
        gui.removeNode()
        del gui

        self.switchAccountsButton['state'] = DirectGuiGlobals.DISABLED

        def makeButton(username):  # type: (str) -> AnimatedButton
            btn = AnimatedButton(
                relief = None,
                parent = base.a2dpTopCenter,
                image = self.avatars[base.cr.accountData[username]['avatar']],
                scale = AccountsListIconScale,
                pressEffect = False,
                text = base.cr.accountData[username]['display_name'],
                text_scale = AccountsListTextScale,
                text_pos = AccountsListTextPos,
                text_fg = (1.0, 1.0, 1.0, 1.0),
                text_wordwrap = 5,
                text_style = 3,
                command = self.__selectAccount, extraArgs = [username]
            )
            btn.bind(DirectGuiGlobals.B3RELEASE, self.__rightClickAccount, extraArgs = [username])
            return btn

        startX = -0.4
        if len(base.cr.accountData) <= 4:
            startX = 0 - len(base.cr.accountData) / 10. + 0.1

        pos = Vec3(startX, 0, -.6)
        for i in range(len(base.cr.accountData)):
            username = list(base.cr.accountData.keys())[i]
            btn = makeButton(username)
            btn.setPos(pos)
            pos.addX(0.2)
            if not (i + 1) % 5:
                pos.setX(startX)
                pos.addZ(-0.3)
            self.accountButtons.append(btn)

        if base.cr.requireAccountAction in ('MigrateAccount', 'AddAccount', 'ChooseAccount'):
            self.backButton['state'] = DirectGuiGlobals.DISABLED
        else:
            self.backButton['state'] = DirectGuiGlobals.NORMAL

    def exitAccounts(self):
        for btn in self.accountButtons:
            btn.destroy()
        base.transitions.noFade()
        self.backButton.destroy()
        self.addAccountButton.destroy()
        self.switchAccountsButton['state'] = DirectGuiGlobals.NORMAL

    def __selectAccount(self, username: str):
        """
        Private method for selecting an account from the account list
        This simply selects the account and goes back home
        """
        self.chooseAccount(username)
        self.request('Home')
        base.cr.requireAccountAction = 'None'

    def __rightClickAccount(self, username: str, _):
        self.__editingAccount = username
        self.request('EditAccount')

    def enterEditAccount(self):
        self.switchAccountsButton['state'] = DirectGuiGlobals.DISABLED
        gui = loader.loadModel('phase_3/models/gui/ttoff_m_gui_opts_buttons')  # type: NodePath
        settingsDecorationModel = loader.loadModel('phase_3/models/gui/ttoff_m_gui_opts_colorpicker')  # type: NodePath
        base.transitions.fadeScreen(0.4)
        buttonTextures = (gui.find('**/button_green_up'),
                          gui.find('**/button_green_down'),
                          gui.find('**/button_green_rollover'),
                          gui.find('**/button_inactive'))
        mmgui = loader.loadModel('phase_3/models/gui/ttrm_m_gui_launch_mainGui')  # type: NodePath
        cdrGui = loader.loadModel('phase_3.5/models/gui/tt_m_gui_sbk_codeRedemptionGui')  # type: NodePath

        self.editAccountEntryFrame = DirectFrame(
            parent = aspect2dp,
            relief = None,
            image = settingsDecorationModel.find('**/temp_bg'),
            image_scale = 1.1
        )
        self.editAccountTitle = OnscreenImage(parent = self.editAccountEntryFrame,
                                              image = mmgui.find('**/CreateProfileTitle'),
                                              pos = (0, 0, 0.45),
                                              scale = (1, 1, 0.125))
        self.usernameLabel = OnscreenText(
            parent = self.editAccountEntryFrame,
            text = TTLocalizer.MainMenuAccountUsername,
            scale = 0.05,
            pos = AccountsUsernameLabelPos
        )
        self.usernameEntry = DirectEntry(
            parent = self.editAccountEntryFrame,
            relief = None,
            pos = AccountsUsernameInputPos,
            initialText = self.__editingAccount,
            state = DirectGuiGlobals.DISABLED,
            image = cdrGui.find('**/tt_t_gui_sbk_cdrCodeBox'),
            text_scale = 0.05,
            scale = 0.7,
            text_align = TextNode.ACenter,
            width = 12
        )

        self.displayNameLabel = OnscreenText(
            parent = self.editAccountEntryFrame,
            text = TTLocalizer.MainMenuAccountDisplayName,
            scale = 0.05,
            pos = AccountsDisplayNameLabelPos
        )
        self.displayNameEntry = DirectEntry(
            parent = self.editAccountEntryFrame,
            relief = None,
            pos = AccountsDisplayNameInputPos,
            image = cdrGui.find('**/tt_t_gui_sbk_cdrCodeBox'),
            text_scale = 0.05,
            scale = 0.7,
            initialText = base.cr.accountData[self.__editingAccount]['display_name'],
            text_align = TextNode.ACenter,
            width = 12
        )

        # self.addIconSelector = AnimatedButton
        self.__accountCreatorActiveIcon = base.cr.accountData[self.__editingAccount]['avatar']
        self.__profileCreatorBtns = []

        for index, icon in enumerate(self.avatars):
            icon = AnimatedButton(
                relief = None,
                parent = self.editAccountEntryFrame,
                pos = (-.45 + (0.15 * index), 0, 0.25),
                image = icon,
                image0_color = VBase4(1.0, 1.0, 1.0, 0.4),
                scale = AccountsListIconScale / 1.4,
                pressEffect = False,
                command = self.__selectIcon, extraArgs = [index]
            )
            self.__profileCreatorBtns.append(icon)

        self.__profileCreatorBtns[self.__accountCreatorActiveIcon]['state'] = DirectGuiGlobals.DISABLED

        self.displayHelp = HelpButton(parent = self.editAccountEntryFrame,
                                      pos = AccountsDisplayNameHelpPos,
                                      contents = TTLocalizer.MainMenuDisplayNameHelp)

        self.usernameHelp = HelpButton(parent = self.editAccountEntryFrame,
                                       pos = AccountsUsernameHelpPos,
                                       contents = TTLocalizer.MainMenuUsernameHelp)
        mmgui.removeNode()
        del mmgui
        self.editSubmitButton = AnimatedButton(
            relief = None,
            parent = base.a2dpBottomCenter,
            pos = DirectConnectConnectPos,
            image = buttonTextures,
            image_scale = (.4, 1, .11),
            pressEffect = False,
            text = TTLocalizer.MainMenuAccountEdit,
            text_scale = 0.055,
            text_pos = (0.0, -0.015),
            command = self.editAccount,
            extraArgs = [self.__editingAccount]
        )
        self.backButton = AnimatedButton(
            relief = None,
            parent = base.a2dpBottomCenter,
            pos = GenericBackPos,
            image = buttonTextures,
            image_scale = ButtonImageScale,
            pressEffect = False,
            text = TTLocalizer.MakeAToonLast,
            text_scale = ButtonTextScale,
            text_pos = ButtonTextPos,
            command = lambda: self.request('Home')
        )

        if base.cr.requireAccountAction == 'MigrateAccount':
            self.usernameEntry.set(ClientSettings.SelectedAccount.get())
        if base.cr.requireAccountAction in ('MigrateAccount', 'AddAccount', 'ChooseAccount'):
            self.backButton['state'] = DirectGuiGlobals.DISABLED

        gui.removeNode()

    def exitEditAccount(self):
        base.transitions.noFade()
        self.editAccountEntryFrame.destroy()
        self.displayNameLabel.destroy()
        self.displayNameEntry.destroy()
        self.usernameLabel.destroy()
        self.usernameEntry.destroy()
        self.backButton.destroy()
        self.editSubmitButton.destroy()
        self.switchAccountsButton['state'] = DirectGuiGlobals.NORMAL
        pass

    def editAccount(self, userName):
        """
        Add the entered account info in the ADD ACCOUNT screen to the saved accounts list
        """
        displayName = self.displayNameEntry.get(True)
        if displayName != '' and userName != '':
            if userName in base.cr.accountData:
                base.cr.accountData[userName] = {
                    "display_name": displayName,
                    "avatar": self.__accountCreatorActiveIcon
                }
                self.chooseAccount(userName)
                self.request('Home')

    def __enterMovieMaker(self):
        base.cr.loginFSM.request('movieMaker')

    def __enterLevelEditor(self):
        base.cr.loginFSM.request('levelEditor')
