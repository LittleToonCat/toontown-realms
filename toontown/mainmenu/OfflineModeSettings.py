import os
import webbrowser
from subprocess import call
from sys import platform
from typing import Optional

from direct.fsm.FSM import FSM
from direct.gui import DirectGuiGlobals
from direct.gui.DirectButton import DirectButton
from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectSlider import DirectSlider
from direct.gui.OnscreenText import OnscreenText
from direct.interval.MetaInterval import Parallel
from panda3d.core import TextNode, Vec4, Vec3

from otp.otpgui import OTPGUIUtils
from otp.otpgui.OTPGUIUtils import Animations
from otp.settings.SimpleSettings import SimpleSettings
from otp.speedchat import SpeedChat, SCColorScheme, SCStaticTextTerminal
from toontown.toonbase import TTLocalizer, ClientSettings, ServerSettings
from toontown.toonbase import ToontownGlobals as ttg
from toontown.toontowngui import FileBrowser
from toontown.shtiker import ControlSettingsDialog, DisplaySettingsDialog
from toontown.toonbase.ToontownSettings import speedChatStyles
from toontown.toontowngui.HelpButton import HelpButton
from toontown.toontowngui.SettingsGUI import SliderOption, ToggleOption, DropdownOption
from toontown.toontowngui.ToontownScrolledFrame import ToontownScrolledFrame

FRAME_WIDTH = 0.84
FRAME_HEIGHT = 0.64


class OfflineModeSettings(DirectFrame):
    settingsDecorationModel = loader.loadModel('phase_3/models/gui/ttoff_m_gui_opts_decor', allowInstance = True)
    settingsScrollbarModel = loader.loadModel('phase_3.5/models/gui/ttoff_m_gui_sbk_generic', allowInstance = True)
    settingsButtonsModel = loader.loadModel('phase_3/models/gui/ttoff_m_gui_opts_buttons', allowInstance = True)


    def __init__(self):
        self.inBook = True
        DirectFrame.__init__(self)

        mainMenuModel = loader.loadModel('phase_3/models/gui/ttrm_m_gui_launch_mainGui')
        self.frame = ToontownScrolledFrame(parent = self,
                                           image = mainMenuModel.find('**/ttrm_m_gui_launch_offlineMode_settingsBg'),
                                           image_pos = (0, 0, -0.131),
                                           image_scale = OTPGUIUtils.getImageScale(1614, 1443, 2.21),
                                           itemMargin = (0.4, 0),
                                           useItemBoundsForPadding = False,
                                           itemPadding = 0.15,
                                           pos = (0, 0, .14),
                                           width = .985,
                                           height = .4845,
                                           manageScrollBars = False,
                                           verticalScroll_frameColor = (0, 0, 0, 0),
                                           verticalScroll_manageButtons = False,
                                           verticalScroll_thumb_geom = (
                                               self.settingsScrollbarModel.find('**/scrollbar_normal'),
                                               self.settingsScrollbarModel.find('**/scrollbar_press'),
                                               self.settingsScrollbarModel.find('**/scrollbar_hover')),
                                           verticalScroll_thumb_geom_scale = OTPGUIUtils.getImageScale(151, 399, 0.15),
                                           verticalScroll_thumb_relief = None,
                                           verticalScroll_resizeThumb = False,
                                           verticalScroll_decButton_relief = None,
                                           verticalScroll_incButton_relief = None)

        mainMenuModel.removeNode()
        del mainMenuModel
        opts = (
            ToggleOption(self, ServerSettings.LegitMode),
            ToggleOption(self, ServerSettings.NerfsMode),
            ToggleOption(self, ServerSettings.SelfToonUp),
            ToggleOption(self, ServerSettings.ExperimentalFeatures),
            DropdownOption(self, ServerSettings.ChatFilterMode),
            # TODO: INT SLIDER OPTION SUPPORT (DIDNT EXIST FOR SOME REASON IN THE NORMAL SETITNGS GUI)
            SliderOption(self, ServerSettings.GagExperienceMultiplier, minimum = ttg.ExpMultiplierMin, maximum = 100, unit = 'x'),
            ToggleOption(self, ServerSettings.StartAsMaxToon),
            DropdownOption(self, ServerSettings.NewToonStartingArea),
            ToggleOption(self, ServerSettings.PropGenerator),
            ToggleOption(self, ServerSettings.ClassicFishingDocks),
            ToggleOption(self, ServerSettings.RaceGameEasterEgg),
            ToggleOption(self, ServerSettings.DaisyGardensEasterEgg),
            ToggleOption(self, ServerSettings.PlaygroundDisneyCharacters),
            ToggleOption(self, ServerSettings.ToontownCentralJukebox),
            ToggleOption(self, ServerSettings.ClearGagInventoryOnDeath),
            ToggleOption(self, ServerSettings.ClearBossRewardInventoryOnDeath),
            ToggleOption(self, ServerSettings.BuildingHelpers),
            ToggleOption(self, ServerSettings.KnockKnockDoorsHealing),
            ToggleOption(self, ServerSettings.YearRoundPresentTreasures),
            ToggleOption(self, ServerSettings.BossCombineGroupsUnder4Players),
            ToggleOption(self, ServerSettings.ProRacerMode),
            ToggleOption(self, ServerSettings.SafezoneActivities),
            SliderOption(self, ServerSettings.CogCountMultiplier, unit = 'x'),
            SliderOption(self, ServerSettings.PlaygroundPassiveHealingAmount, unit = 'hp / 30s'),
            ToggleOption(self, ServerSettings.ClassicAnimatedPropFaceOffDuration),
            ToggleOption(self, ServerSettings.FacilityReserveCogs),
            ToggleOption(self, ServerSettings.SpawnFieldOffices),
            ToggleOption(self, ServerSettings.BossParties),
            SliderOption(self, ServerSettings.FishTargetsInPonds),
            ToggleOption(self, ServerSettings.SpawnCogs)


        )
        # opts = (
        #     ToggleOption('legit-mode'),
        #     ToggleOption('nerfs-mode'),
        #     ToggleOption('self-toon-up'),
        #     ToggleOption('experimental-features'),
        #     DropdownOption('chat-filter-mode'),
        #     SliderOption('exp-multiplier', minimum = ttg.ExpMultiplierMin, maximum = 100, unit = 'x'),  # can set higher in options settings
        #     SliderOption('exp-cap', minimum = ttg.ExpCapMin, maximum = ttg.ExpCapMax, isInt = True),
        #     SliderOption('merit-multiplier', minimum = ttg.MeritMultiplierMin, maximum = ttg.MeritMultiplierMax, unit = 'x'),
        #     SliderOption('doodle-multiplier', minimum = ttg.DoodleMultiplierMin, maximum = ttg.DoodleMultiplierMax, unit = 'x'),
        #     ToggleOption('default-max-toon'),
        #     DropdownOption('default-playground'),
        #     ToggleOption('prop-generator'),
        #     ToggleOption('classic-fishing'),
        #     ToggleOption('easter-eggs'),
        #     ToggleOption('disney-characters'),
        #     ToggleOption('jukebox'),
        #     ToggleOption('lose-inventory'),
        #     ToggleOption('lose-rewards'),
        #     ToggleOption('building-helpers'),
        #     ToggleOption('knock-knock-healing'),
        #     ToggleOption('want-yearround-present-treasures'),
        #     ToggleOption('boss-group-toons-if-numToons<=4'),
        #     ToggleOption('racing-pro-racer'),
        #     ToggleOption('safezone-activities'),
        #     SliderOption('cog-count-multiplier', minimum = 0.1, maximum = 200.0, unit = 'x'),
        #     SliderOption('playground-passive-healing-amount', minimum = 1, maximum = 25, isInt = True, unit = 'hp / 30s')
        # )

        self.frame.addItems(*opts)

    def destroy(self):
        self.frame.clearItems()
        DirectFrame.destroy(self)
