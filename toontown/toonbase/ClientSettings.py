# ClientSettings
# Created by drewc Apr 15 2024
import os
import platform
import sys
from enum import IntEnum

from panda3d.core import Vec4
from typing import List

from otp.settings.TOMLSettings import TOMLSettings
from toontown.social.SocialGlobals import ELoginPopupTypes, ETeleportRequestTypes
from toontown.toonbase.SettingsBase import SettingsCategory, FloatSetting, BoolSetting, IntegerSetting, StringSetting, \
    EnumSetting, ListSetting, SettingBase, SettingsWarning
from toontown.toonbase.ToontownSettings import ASPECT_RATIOS
from toontown.toontowngui.ColorUtils import hsvToRgb


class EChatFilterMode(IntEnum):
    DEFAULT = 0
    CENSOR = 1
    WHITELIST = 2


class EScreenshotFormat(IntEnum):
    JPG = 0
    PNG = 1
    TGA = 2
    TIF = 3
    EXR = 4


class EScreenshotDirectory(IntEnum):
    GAME = 0
    WINPHOTOS = 1


class EDisplayMode(IntEnum):
    WINDOWED = 0
    FULLSCREEN = 1
    BORDERLESS = 2


class EAnisotropicFiltering(IntEnum):
    OFF = 0
    AF_2x = 1
    AF_4x = 2
    AF_8x = 3
    AF_16x = 4


class EAntiAliasing(IntEnum):
    OFF = 0
    MSAA_2x = 1
    MSAA_4x = 2
    MSAA_8x = 3


class EAspectRatio(IntEnum):
    ADAPTIVE = 0
    FORCED_4_3 = 1
    FORCED_16_9 = 2
    FORCED_21_9 = 3


class EMaxFPS(IntEnum):
    UNLIMITED = 0
    LOCKED_30 = 1
    LOCKED_60 = 2
    LOCKED_120 = 3
    LOCKED_144 = 4
    LOCKED_165 = 5
    LOCKED_240 = 6
    LOCKED_360 = 7


class EReflectionQuality(IntEnum):
    OFF = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    ULTRA = 4


class ECameraMode(IntEnum):
    ORBITAL = 0
    CLASSIC = 1
    FIRSTPERSON = 2


class ETeleportGreeting(IntEnum):
    HI = 0
    HEYA = 1
    HELLO = 2
    HOWDY = 3
    WHATS_UP = 4
    YO = 5
    GREETINGS = 6
    HOW_ARE_YOU = 7
    TOON_NAME = 8
    NO_GREETING = 9


class ClientSettingsMgr(TOMLSettings):
    globalSettings = None

    def __init__(self):
        TOMLSettings.__init__(self, 'client.toml')
        self.settings = []


ClientSettingsManager = ClientSettingsMgr()

# == GAME ==
SmoothThrowing = BoolSetting(
    "SmoothThrowing",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.GAME,
    default = True
)

AllowServerPATScreens = BoolSetting(
    "AllowServerPATScreens",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.GAME,
    default = True
)

MagicWordActivator = IntegerSetting(
    "MagicWordActivator",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.GAME,
    default = 0,
    minVal = 0,
    maxVal = 5
)

PropGeneratorCollisions = BoolSetting(
    "PropGeneratorCollisions",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.GAME,
    default = True,
    changeWarning = SettingsWarning.SWReload
)

DefaultCameraMode = EnumSetting(
    "DefaultCameraMode",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.GAME,
    enum = ECameraMode,
    default = ECameraMode.ORBITAL
)

ScreenshotFormat = EnumSetting(
    "ScreenshotFormat",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.GAME,
    enum = EScreenshotFormat,
    default = EScreenshotFormat.JPG
)

ScreenshotDirectory = EnumSetting(
    "ScreenshotDirectory",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.GAME,
    enum = EScreenshotDirectory,
    default = EScreenshotDirectory.GAME
)

TeleportGreeting = EnumSetting(
    "TeleportGreeting",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.GAME,
    enum = ETeleportGreeting,
    default = ETeleportGreeting.HI
)

DiscordRPC = BoolSetting(
    "WantDiscordRPC",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.GAME,
    default = True
)

# == AUDIO ==
MusicEnabled = BoolSetting(
    "MusicEnabled",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.SOUND,
    default = True,
    onUpdate = lambda _: base.updateSfxMgrs()
)

MusicVolume = FloatSetting(
    "MusicVolume",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.SOUND,
    default = 0.35,
    minVal = 0.0,
    maxVal = 1.0,
    onUpdate = lambda _: base.updateSfxMgrs()
)


def __updateSFXVolume(val: float):
    for sfxManager in base.sfxManagerList:
        sfxManager.setVolume(val)

VolumeMasterEnabled = BoolSetting(
    "VolumeMasterEnabled",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.SOUND,
    default = True,
    onUpdate = lambda _: base.updateSfxMgrs()
)

VolumeMaster = FloatSetting(
    "VolumeMaster",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.SOUND,
    default = 0.35,
    minVal = 0.0,
    maxVal = 1.0,
    onUpdate = lambda _: base.updateSfxMgrs()
)

VolumeSFXEnabled = BoolSetting(
    "VolumeSFXEnabled",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.SOUND,
    default = True,
    onUpdate = lambda _: base.updateSfxMgrs()
)

VolumeSFX = FloatSetting(
    "VolumeSFX",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.SOUND,
    default = 1.0,
    minVal = 0.0,
    maxVal = 1.0,
    onUpdate = lambda _: base.updateSfxMgrs()
)

VolumeDialogEnabled = BoolSetting(
    "VolumeDialogEnabled",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.SOUND,
    default = True,
    onUpdate = lambda _: base.updateSfxMgrs()
)
VolumeDialog = FloatSetting(
    "VolumeDialog",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.SOUND,
    default = 1.0,
    minVal = 0.0,
    maxVal = 1.0,
    onUpdate = lambda _: base.updateSfxMgrs()
)

VolumeBattleEnabled = BoolSetting(
    "VolumeBattleEnabled",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.SOUND,
    default = True,
    onUpdate = lambda _: base.updateSfxMgrs()
)
VolumeBattle = FloatSetting(
    "VolumeBattle",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.SOUND,
    default = 1.0,
    minVal = 0.0,
    maxVal = 1.0,
    onUpdate = lambda _: base.updateSfxMgrs()
)

VolumeEnvironmentEnabled = BoolSetting(
    "VolumeEnvironmentEnabled",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.SOUND,
    default = True,
    onUpdate = lambda _: base.updateSfxMgrs()
)
VolumeEnvironment = FloatSetting(
    "VolumeEnvironment",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.SOUND,
    default = 1.0,
    minVal = 0.0,
    maxVal = 1.0,
    onUpdate = lambda _: base.updateSfxMgrs()
)

VolumeStreetPropsEnabled = BoolSetting(
    "VolumeStreetPropsEnabled",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.SOUND,
    default = True,
    onUpdate = lambda _: base.updateSfxMgrs()
)
VolumeStreetProps = FloatSetting(
    "VolumeStreetProps",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.SOUND,
    default = 1.0,
    minVal = 0.0,
    maxVal = 1.0,
    onUpdate = lambda _: base.updateSfxMgrs()
)

VolumeGuiEnabled = BoolSetting(
    "VolumeGuiEnabled",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.SOUND,
    default = True,
    onUpdate = lambda _: base.updateSfxMgrs()
)
VolumeGui = FloatSetting(
    "VolumeGui",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.SOUND,
    default = 1.0,
    minVal = 0.0,
    maxVal = 1.0,
    onUpdate = lambda _: base.updateSfxMgrs()
)

ToonChatSounds = BoolSetting(
    "ToonChatSounds",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.SOUND,
    default = True
)

PropSounds = BoolSetting(
    "PropSounds",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.SOUND,
    default = True
)

TextToSpeechEnabled = BoolSetting(
    "TextToSpeechEnabled",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.SOUND,
    default = False
)

TextToSpeechVolume = FloatSetting(
    "TextToSpeechVolume",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.SOUND,
    default = 0.35,
    minVal = 0.0,
    maxVal = 1.0
)


def getDefaultTTSPath() -> str:
    if sys.platform == 'win32':
        if platform.machine().endswith('64'):
            programFiles = os.environ['PROGRAMFILES(x86)']
        else:
            programFiles = os.environ['PROGRAMFILES']
        defaultPath = programFiles + '\\eSpeak\\command_line\\espeak'
    elif sys.platform == 'linux2':
        defaultPath = '/usr/bin/espeak'
    else:
        defaultPath = ''
    return defaultPath

TextToSpeechPath = StringSetting(
    "TextToSpeechPath",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.SOUND,
    default = getDefaultTTSPath()
)

JapanDialog = BoolSetting(
    "JapanDialog",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.SOUND,
    default = False
)

# == VIDEO ==
DisplayMode = EnumSetting(
    "DisplayMode",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.VIDEO,
    enum = EDisplayMode,
    default = EDisplayMode.WINDOWED
)

Resolution = ListSetting(
    "Resolution",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.VIDEO,
    listType = int,
    default = [1280, 720],
    length = 2
)

AnisotropicFiltering = EnumSetting(
    "AnisotropicFiltering",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.VIDEO,
    enum = EAnisotropicFiltering,
    default = EAnisotropicFiltering.AF_4x,
    changeWarning = SettingsWarning.SWRestart
)

AntiAliasing = EnumSetting(
    "AntiAliasing",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.VIDEO,
    enum = EAntiAliasing,
    default = EAntiAliasing.MSAA_2x,
    changeWarning = SettingsWarning.SWRestart
)

AspectRatio = EnumSetting(
    "AspectRatio",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.VIDEO,
    enum = EAspectRatio,
    default = EAspectRatio.ADAPTIVE,
    onUpdate = lambda val: base.setAspectRatio(ASPECT_RATIOS[val])
)


def __updateShtickerBookBackground(val: List[int]):
    base.cr.makeACogEgg = val == [0, 0, 0, 0]

    if hasattr(base, 'localAvatar'):
        col = val
        if col[3] == 1.0:
            base.render.hide()
        else:
            base.render.show()
        base.localAvatar.book.background.setColor(Vec4(*hsvToRgb(*val)))

ShtickerBookBackground = ListSetting(
    "ShtickerBookBackground",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.GAME,
    listType = int,
    default = [266, 87, 40, 70],
    length = 4,
    onUpdate = __updateShtickerBookBackground
)


def __updateShtickerBookScale():
    """
    Force the book to update live, the book itself only checks when opened
    """
    if hasattr(base, 'localAvatar') and hasattr(base.localAvatar, 'book'):
        base.localAvatar.book.updateScale()

ShtickerBookScale = FloatSetting(
    "ShtickerBookScale",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.GAME,
    default = 1.0,
    minVal = 0.9,
    maxVal = 1.1,
    onUpdate = lambda _: __updateShtickerBookScale()
)

PropSpawnerGUIScale = FloatSetting(
    "PropSpawnerGUIScale",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.VIDEO,
    default = 1.0,
    minVal = 0.75,
    maxVal = 1.0
)

SmoothAnimations = BoolSetting(
    "SmoothAnimations",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.VIDEO,
    default = True,
    changeWarning = SettingsWarning.SWRestart
)

StreetMapOpacity = FloatSetting(
    "StreetMapOpacity",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.VIDEO,
    default = 1.0,
    minVal = 0.25,
    maxVal = 1.0
)

VerticalSync = BoolSetting(
    "VerticalSync",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.VIDEO,
    default = True,
    changeWarning = SettingsWarning.SWRestart
)

VisualizeCollisionGenerators = BoolSetting(
    "VisualizeCollisionGenerators",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.VIDEO,
    default = True
)

CameraFOV = FloatSetting(
    "CameraFOV",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.VIDEO,
    default = 39,
    minVal = 30,
    maxVal = 120
)

ReflectionQuality = EnumSetting(
    "ReflectionQuality",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.VIDEO,
    enum = EReflectionQuality,
    default = EReflectionQuality.MEDIUM,
    changeWarning = SettingsWarning.SWReload
)

AvatarLODs = BoolSetting(
    "AvatarLODs",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.VIDEO,
    default = True,
    changeWarning = SettingsWarning.SWReload
)

AvatarFrustumCulling = BoolSetting(
    "AvatarFrustumCulling",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.VIDEO,
    default = False,
    changeWarning = SettingsWarning.SWReload
)

GUIAnimations = BoolSetting(
    "GUIAnimations",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.VIDEO,
    default = True
)

FrameRateCap = EnumSetting(
    "FrameRateCap",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.VIDEO,
    enum = EMaxFPS,
    default = EMaxFPS.LOCKED_165
)

# == SOCIAL ==
AcceptingNewFriends = BoolSetting(
    "AcceptingNewFriends",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.SOCIAL,
    default = True
)

AcceptingNonFriendWhispers = BoolSetting(
    "AcceptingNonFriendWhispers",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.SOCIAL,
    default = True
)

GlobalChatPopups = BoolSetting(
    "GlobalChatPopups",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.SOCIAL,
    default = True
)

LoginMessages = EnumSetting(
    "LoginMessages",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.SOCIAL,
    enum = ELoginPopupTypes,
    default = ELoginPopupTypes.EVERYONE
)

TeleportRequests = EnumSetting(
    "TeleportRequests",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.SOCIAL,
    enum = ETeleportRequestTypes,
    default = ETeleportRequestTypes.EVERYONE
)

ChatFilterMode = EnumSetting(
    "ChatFilterMode",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.SOCIAL,
    enum = EChatFilterMode,
    default = EChatFilterMode.CENSOR
)

# == CONTROLS ==
DoorInteraction = BoolSetting(
    "DoorInteraction",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.CONTROL,
    default = True
)

NPCInteraction = BoolSetting(
    "NPCInteraction",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.CONTROL,
    default = True
)

ActivityInteraction = BoolSetting(
    "ActivityInteraction",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.CONTROL,
    default = True
)

CogInteraction = BoolSetting(
    "CogInteraction",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.CONTROL,
    default = False
)

CameraSensitivity = FloatSetting(
    "CameraSensitivity",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.CONTROL,
    default = 0.24,
    minVal = 0.1,
    maxVal = 1.0
)

# == HIDDEN ==
LastWelcomeVersion = StringSetting(
    "LastWelcomeVersion",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.HIDDEN,
    default = '0'
)

SoftwareMode = BoolSetting(
    "SoftwareMode",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.HIDDEN,
    default = False
)

MickeyModeEasterEgg = BoolSetting(
    "MickeyModeEasterEgg",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.HIDDEN,
    default = False
)

SmootherDelay = FloatSetting(
    "SmootherDelay",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.HIDDEN,
    default = 0.2,
    minVal = 0.0,
    maxVal = 1.0
)

PositionSendRate = FloatSetting(
    "PositionSendRate",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.HIDDEN,
    default = 0.04,
    minVal = 0.0,
    maxVal = 1.0
)

DistancedDialog = BoolSetting(
    "DistancedDialog",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.HIDDEN,
    default = False
)

SelectedAccount = StringSetting(
    "SelectedAccount",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.HIDDEN,
    default = ''
)

ThreadedNetwork = BoolSetting(
    "ThreadedNetwork",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.HIDDEN,
    default = True
)

LastDirectConnectAddress = StringSetting(
    "LastDirectConnectAddress",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.HIDDEN,
    default = ''
)

# == SAVED ==
FavoriteProps = ListSetting(
    "FavoriteProps",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.SAVED,
    listType = str,
    default = []
)

SavedPropTextures = ListSetting(
    "SavedPropTextures",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.SAVED,
    listType = str,
    default = []
)

SavedSwatches = ListSetting(
    "SavedSwatches",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.SAVED,
    listType = list,
    default = []
)

FavoriteMagicWords = ListSetting(
    "FavoriteMagicWords",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.SAVED,
    listType = str,
    default = []
)

# == RETRO ==
NewStreetBattleMusic = BoolSetting(
    "NewStreetBattleMusic",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.RETRO,
    default = True
)

EstateMusic = BoolSetting(
    "EstateMusic",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.RETRO,
    default = True,
    changeWarning = SettingsWarning.SWEstate
)

EstatePopsicleTreasures = BoolSetting(
    "EstatePopsicleTreasures",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.RETRO,
    default = True,
    changeWarning = SettingsWarning.SWEstate
)

UpdatedMap = BoolSetting(
    "UpdatedMap",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.GAME,
    default = True,
    changeWarning = SettingsWarning.SWRestart
)

NewSpeedchatPhrases = BoolSetting(
    "NewSpeedchatPhrases",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.RETRO,
    default = True,
    changeWarning = SettingsWarning.SWRestart
)

NewRecordColor = BoolSetting(
    "NewRecordColor",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.RETRO,
    default = True
)

CogBattlePanels = BoolSetting(
    "CogBattlePanels",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.RETRO,
    default = True
)

PhotoAlbumPage = BoolSetting(
    "PhotoAlbumPage",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.RETRO,
    default = True,
    changeWarning = SettingsWarning.SWRestart
)

CEOTableSquish = BoolSetting(
    "CEOTableSquish",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.RETRO,
    default = True
)

BetaPlaygroundInterface = BoolSetting(
    "BetaPlaygroundInterface",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.RETRO,
    default = True
)

BetaPlaygroundMovement = BoolSetting(
    "BetaPlaygroundMovement",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.RETRO,
    default = True
)

ClassicPickAToon = BoolSetting(
    "ClassicPickAToon",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.RETRO,
    default = False,
    changeWarning = SettingsWarning.SWRestart
)

ClassicLoadingScreen = BoolSetting(
    "ClassicLoadingScreen",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.RETRO,
    default = False,
    changeWarning = SettingsWarning.SWRestart
)

ClassicMakeAToon = BoolSetting(
    "ClassicMakeAToon",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.RETRO,
    default = False
)

ClassicNametags = BoolSetting(
    "ClassicNametags",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.RETRO,
    default = False,
    changeWarning = SettingsWarning.SWRestart
)

ClassicChatBubbles = BoolSetting(
    "ClassicChatBubbles",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.RETRO,
    default = False,
    changeWarning = SettingsWarning.SWRestart
)

ClassicSFX = BoolSetting(
    "ClassicSFX",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.RETRO,
    default = False,
    changeWarning = SettingsWarning.SWRestart
)

ClassicDogs = BoolSetting(
    "ClassicDogs",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.RETRO,
    default = False,
    changeWarning = SettingsWarning.SWReload
)

ShowAccessoriesInPickAToon = BoolSetting(
    "ShowAccessoriesInPickAToon",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.RETRO,
    default = True
)

PerPlaygroundTrolleyGagShops = BoolSetting(
    "PerPlaygroundTrolleyGagShops",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.RETRO,
    default = True
)

ClassicTrolleyGamePortraits = BoolSetting(
    "ClassicTrolleyGamePortraits",
    settingsFile = ClientSettingsManager,
    category = SettingsCategory.RETRO,
    default = False
)

# Instantiate all classes defined here to register them.
# A bit hacky, but better than the old system
for item in list(globals().values()):
    if isinstance(item, SettingBase):
        ClientSettingsManager.settings.append(item)
