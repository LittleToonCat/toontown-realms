# ServerSettings
# Created by drewc Apr 17 2024
from enum import IntEnum

from otp.settings.TOMLSettings import TOMLSettings
from toontown.toonbase.ClientSettings import EChatFilterMode
from toontown.toonbase.SettingsBase import SettingsCategory, StringSetting, ListSetting, EnumSetting, BoolSetting, IntegerSetting, FloatSetting, SettingBase


class ServerSettingsMgr(TOMLSettings):

    def __init__(self):
        TOMLSettings.__init__(self, 'config/server.toml')
        self.settings = []


ServerSettingsManager = ServerSettingsMgr()


# ('Toontown Central', "Donald's Dock", "Daisy Gardens", "Minnie's Melodyland", "The Brrrgh", "Donald's Dreamland")
class EStartingArea(IntEnum):
    TOONTOWN_CENTRAL = 2000
    DONALDS_DOCK = 1000
    DAISY_GARDENS = 5000
    MINNIES_MELODYLAND = 4000
    THE_BRRRGH = 3000
    DONALDS_DREAMLAND = 9000
    ACORN_ACRES = 6000
    ACORN_ACRES_CAMPSITE = 6100
    ACORN_ACRES_GOLF = 17000
    BOSSBOT_HQ = 10000
    SELLBOT_HQ = 11000
    CASHBOT_HQ = 12000
    LAWBOT_HQ = 13000
    TOONTOWN_CENTRAL_BETA = 21000
    DONALDS_DOCK_BETA = 26000
    DAISY_GARDENS_BETA = 22000
    MINNIES_MELODYLAND_BETA = 23000
    THE_BRRRGH_BETA = 25000
    DONALDS_DREAMLAND_BETA = 24000
    TOONLAND_FUNNY_FARM = 31000


# == ACCESS ==
ServerPassword = StringSetting(
    "ServerPassword",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.SERVER_ACCESS,
    default = ''
)

WhitelistedUsers = ListSetting(
    "WhitelistedUsers",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.SERVER_ACCESS,
    listType = str,
    default = [],
    length = -1
)

NotWhitelistedMessage = StringSetting(
    "NotWhitelistedMessage",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.SERVER_ACCESS,
    default = "Your username is not whitelisted on this Realm."
)

DefaultAccessLevel = StringSetting(
    "DefaultAccessLevel",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.SERVER_ACCESS,
    default = "USER"
)

MinimumAccessLevel = StringSetting(
    "MinimumAccessLevel",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.SERVER_ACCESS,
    default = "NO_ACCESS"
)

MaxPlayers = IntegerSetting(
    "MaxPlayers",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.SERVER_ACCESS,
    default = 16,
    minVal = 2,
    maxVal = 128
)

ServerPort = IntegerSetting(
    "ServerPort",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.SERVER_ACCESS,
    default = 7198,
    minVal = 7198,
    maxVal = 7198
)

PropGeneratorLockMinimumAccessLevel = StringSetting(
    "PropGeneratorLockMinimumAccessLevel",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.SERVER_ACCESS,
    default = 'MODERATOR'
)

MagicWordCooldownBypassMinimumAccess = StringSetting(
    "MagicWordCooldownBypassMinimumAccess",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.SERVER_ACCESS,
    default = 'MODERATOR'
)

# == MODERATION ==
ChatFilterMode = EnumSetting(
    "ChatFilterMode",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.SERVER_MODERATION,
    enum = EChatFilterMode,
    default = EChatFilterMode.DEFAULT
)

BanHardwareIDs = BoolSetting(
    "BanHardwareIDs",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.SERVER_MODERATION,
    default = True
)

BanUUIDs = BoolSetting(
    "BanUUIDs",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.SERVER_MODERATION,
    default = True
)

BanIPAddresses = BoolSetting(
    "BanIPAddresses",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.SERVER_MODERATION,
    default = True
)

LogMagicWords = BoolSetting(
    "LogMagicWords",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.SERVER_MODERATION,
    default = True
)

GlobalChat = BoolSetting(
    "GlobalChat",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.GAME,
    default = True
)

# == API ==
AccessLevelEndpoint = StringSetting(
    "AccessLevelEndpoint",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.SERVER_API,
    default = 'localdb'
)

ReportsEndpoint = StringSetting(
    "ReportsEndpoint",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.SERVER_API,
    default = 'local'
)

ReportsEndpointAuthHeader = StringSetting(
    "ReportsEndpointAuthHeader",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.SERVER_API,
    default = ""
)

LoggingEndpoint = StringSetting(
    "LoggingEndpoint",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.SERVER_API,
    default = ""
)

LoggingEndpointAuthHeader = StringSetting(
    "LoggingEndpointAuthHeader",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.SERVER_API,
    default = ""
)

# == DISPLAY ==
ServerDisplayName = StringSetting(
    "ServerDisplayName",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.SERVER_DISPLAY,
    default = 'My Realm'
)

ServerDescription = StringSetting(
    "ServerDescription",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.SERVER_DISPLAY,
    default = 'A Toontown Realms Realm'
)

ShowInPublicServerBrowser = BoolSetting(
    "ShowInPublicServerBrowser",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.SERVER_DISPLAY,
    default = False
)

ServerIconURL = StringSetting(
    "ServerIconURL",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.SERVER_DISPLAY,
    default = 'https://toontownrealms.com/images/realms_icon.png'
)

# == GAME ==
LegitMode = BoolSetting(
    "LegitMode",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.GAME,
    default = False
)

NerfsMode = BoolSetting(
    "NerfsMode",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.GAME,
    default = False  # Deprecated
)

GagExperienceMultiplier = IntegerSetting(
    "GagExperienceMultiplier",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.GAME,
    default = 1,
    minVal = 1,
    maxVal = 100
)

PerBattleGagExperienceLimit = IntegerSetting(
    "PerBattleGagExperienceLimit",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.GAME,
    default = 200,
    minVal = 1,
    maxVal = 10000
)

DoodleExperienceMultiplier = IntegerSetting(
    "DoodleExperienceMultiplier",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.GAME,
    default = 1,
    minVal = 1,
    maxVal = 100
)

MeritMultiplier = IntegerSetting(
    "MeritMultiplier",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.GAME,
    default = 1,
    minVal = 1,
    maxVal = 100
)

StartAsMaxToon = BoolSetting(
    "StartAsMaxToon",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.GAME,
    default = False
)

NewToonStartingArea = EnumSetting(
    "NewToonStartingArea",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.GAME,
    enum = EStartingArea,
    default = EStartingArea.TOONTOWN_CENTRAL
)

PropGenerator = BoolSetting(
    "PropGenerator",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.GAME,
    default = True
)

ClassicFishingDocks = BoolSetting(
    "ClassicFishingDocks",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.RETRO,
    default = False
)

PlaygroundDisneyCharacters = BoolSetting(
    "PlaygroundDisneyCharacters",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.GAME,
    default = True
)

ToontownCentralJukebox = BoolSetting(
    "ToontownCentralJukebox",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.GAME,
    default = False
)

BuildingHelpers = BoolSetting(
    "BuildingHelpers",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.GAME,
    default = True
)

RaceGameEasterEgg = BoolSetting(
    "RaceGameEasterEgg",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.GAME,
    default = True
)

DetailedVehicleRotation = BoolSetting(
    "DetailedVehicleRotation",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.GAME,
    default = True
)

TimeZone = StringSetting(
    "TimeZone",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.GAME,
    default = 'US/Eastern'
)

SafezoneActivities = BoolSetting(
    "SafezoneActivities",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.GAME,
    default = True
)

CogCountMultiplier = FloatSetting(
    "CogCountMultiplier",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.GAME,
    default = 1.0,
    minVal = 0.1,
    maxVal = 5.0
)

ClassicAnimatedPropFaceOffDuration = BoolSetting(
    "ClassicAnimatedPropFaceOffDuration",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.RETRO,
    default = False
)

PlaygroundPassiveHealingAmount = IntegerSetting(
    "PlaygroundPassiveHealingAmount",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.GAME,
    default = 1,
    minVal = 1,
    maxVal = 25
)

FacilityReserveCogs = BoolSetting(
    "FacilityReserveCogs",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.GAME,
    default = False
)

SelfToonUp = BoolSetting(
    "SelfToonUp",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.GAME,
    default = True
)

ClearGagInventoryOnDeath = BoolSetting(
    "ClearGagInventoryOnDeath",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.GAME,
    default = True
)

ClearBossRewardInventoryOnDeath = BoolSetting(
    "ClearBossRewardInventoryOnDeath",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.GAME,
    default = False)

KnockKnockDoorsHealing = BoolSetting(
    "KnockKnockDoorsHealing",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.GAME,
    default = True)

YearRoundPresentTreasures = BoolSetting(
    "YearRoundPresentTreasures",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.GAME,
    default = False)

BossCombineGroupsUnder4Players = BoolSetting(
    "BossCombineGroupsUnder4Players",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.GAME,
    default = False)

ExperimentalFeatures = BoolSetting(
    "ExperimentalFeatures",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.GAME,
    default = False)

DaisyGardensEasterEgg = BoolSetting(
    "DaisyGardensEasterEgg",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.GAME,
    default = True)

ProRacerMode = BoolSetting(
    "ProRacerMode",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.GAME,
    default = False)

SpawnFieldOffices = BoolSetting(
    "SpawnFieldOffices",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.GAME,
    default = True)

BossParties = BoolSetting(
    "BossParties",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.GAME,
    default = True)

FishTargetsInPonds = IntegerSetting(
    "FishTargetsInPonds",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.GAME,
    default = 2,
    minVal = 1,
    maxVal = 10)

SpawnCogs = BoolSetting(
    "SpawnCogs",
    settingsFile = ServerSettingsManager,
    category = SettingsCategory.GAME,
    default = True)

# Instantiate all classes defined here to register them.
# A bit hacky, but better than the old system
for item in list(globals().values()):
    if isinstance(item, SettingBase):
        ServerSettingsManager.settings.append(item)
