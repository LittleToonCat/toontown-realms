from panda3d.core import *
import sys

QuietZone = 1
UberZone = 2
WallBitmask = BitMask32(1)
FloorBitmask = BitMask32(2)
CameraBitmask = BitMask32(4)
CameraTransparentBitmask = BitMask32(8)
PropGenSnapPointBitMask = BitMask32(64)
SafetyNetBitmask = BitMask32(512)
SafetyGateBitmask = BitMask32(1024)
GhostBitmask = BitMask32(2048)
PathFindingBitmask = BitMask32.bit(29)
OriginalCameraFov = 39.0
DefaultCameraFov = 52.0
DefaultCameraFar = 400.0
DefaultCameraNear = 1.0
AICollisionPriority = 10
AICollMovePriority = 8
MaxFriends = 250
MaxPlayerFriends = 300
MaxBackCatalog = 48
FriendChat = 1
CommonChat = 1
SuperChat = 2
MaxCustomMessages = 25
SPInvalid = 0
SPHidden = 1
SPRender = 2
SPDynamic = 5
CENormal = 0
CEBigHead = 1
CESmallHead = 2
CEBigLegs = 3
CESmallLegs = 4
CEBigToon = 5
CESmallToon = 6
CEFlatPortrait = 7
CEFlatProfile = 8
CETransparent = 9
CENoColor = 10
CEInvisible = 11
CEPumpkin = 12
CEBigWhite = 13
CESnowMan = 14
CEGreenToon = 15
CEWireFrame = 16
CELongLegs = 17
CEWide = 18
CENoTorso = 19
CE20Dog = 20
CEVirtual = 21
CEMagicCat = 22
CEGhost = 'g'
BigToonScale = 1.5
SmallToonScale = 0.5
LongLegsScale = 2.5
DisconnectUnknown = 0
DisconnectBookExit = 1
DisconnectCloseWindow = 2
DisconnectPythonError = 3
DisconnectGraphicsError = 4
DisconnectReasons = {DisconnectUnknown: 'unknown',
 DisconnectBookExit: 'book exit',
 DisconnectCloseWindow: 'closed window',
 DisconnectPythonError: 'python error',
 DisconnectGraphicsError: 'graphics error'}
DatabaseDialogTimeout = 20.0
DatabaseGiveupTimeout = 45.0
PeriodTimerWarningTime = (600, 300, 60)
WalkCutOff = 0.5
RunCutOff = 8.0
FloorOffset = 0.025
AvatarDefaultRadius = 1
InterfaceFont = None
InterfaceFontPath = None
SignFont = None
SignFontPath = None
FancyFont = None
FancyFontPath = None
NametagFonts = {}
NametagFontPaths = {}
TransparentTexture = None
DialogClass = None
GlobalDialogClass = None
ProductPrefix = None

def getInterfaceFont():
    global InterfaceFontPath
    global InterfaceFont
    if InterfaceFont == None:
        if InterfaceFontPath == None:
            InterfaceFont = TextNode.getDefaultFont()
        else:
            InterfaceFont = loader.loadFont(InterfaceFontPath, lineHeight=1.0, pixelsPerUnit=128)
    return InterfaceFont


def setInterfaceFont(path):
    global InterfaceFontPath
    global InterfaceFont
    InterfaceFontPath = path
    InterfaceFont = None
    return


def getSignFont():
    global SignFont
    global SignFontPath
    if SignFont == None:
        if SignFontPath == None:
            InterfaceFont = TextNode.getDefaultFont()
            SignFont = TextNode.getDefaultFont()
        else:
            SignFont = loader.loadFont(SignFontPath, lineHeight=1.0)
    return SignFont


def setSignFont(path):
    global SignFontPath
    SignFontPath = path


def getFancyFont():
    global FancyFontPath
    global FancyFont
    if FancyFont == None:
        if FancyFontPath == None:
            FancyFont = TextNode.getDefaultFont()
        else:
            FancyFont = loader.loadFont(FancyFontPath, lineHeight=1.0)
    return FancyFont


def setFancyFont(path):
    global FancyFontPath
    FancyFontPath = path


def getNametagFont(index):
    global NametagFontPaths
    global NametagFonts
    if index not in NametagFonts or NametagFonts[index] == None:
        if index not in NametagFontPaths or NametagFontPaths[index] == None:
            NametagFonts[index] = TextNode.getDefaultFont()
        else:
            NametagFonts[index] = loader.loadFont(NametagFontPaths[index], lineHeight=1.0)
    return NametagFonts[index]


def setNametagFont(index, path):
    NametagFontPaths[index] = path


def getTransparentTexture():
    global TransparentTexture
    if TransparentTexture == None:
        image = PNMImage(1, 1)
        image.addAlpha()
        TransparentTexture = Texture()
        TransparentTexture.load(image)
    return TransparentTexture


def getDialogClass():
    global DialogClass
    if DialogClass == None:
        from otp.otpgui.OTPDialog import OTPDialog
        DialogClass = OTPDialog
    return DialogClass


def getGlobalDialogClass():
    global GlobalDialogClass
    if DialogClass == None:
        from otp.otpgui.OTPDialog import GlobalDialog
        GlobalDialogClass = GlobalDialog
    return GlobalDialogClass


def setDialogClasses(dialogClass, globalDialogClass):
    global DialogClass
    global GlobalDialogClass
    DialogClass = dialogClass
    GlobalDialogClass = globalDialogClass


def getDefaultProductPrefix():
    global ProductPrefix
    return ProductPrefix


def setDefaultProductPrefix(prefix):
    global ProductPrefix
    ProductPrefix = prefix


NetworkLatency = 1.0
maxLoginWidth = 9.1
STAND_INDEX = 0
WALK_INDEX = 1
RUN_INDEX = 2
REVERSE_INDEX = 3
STRAFE_LEFT_INDEX = 4
STRAFE_RIGHT_INDEX = 5
ToonStandableGround = 0.707
ToonSpeedFactor = 1.25
ToonForwardSpeedOld = 16.0
ToonForwardSpeed = ToonForwardSpeedOld * ToonSpeedFactor
ToonJumpForce = 24.0
ToonReverseSpeedOld = 8.0
ToonReverseSpeed = ToonReverseSpeedOld * ToonSpeedFactor
ToonRotateSpeedOld = 80.0
ToonRotateSpeed = ToonRotateSpeedOld * ToonSpeedFactor
ToonForwardSlowSpeed = 6.0
ToonJumpSlowForce = 4.0
ToonReverseSlowSpeed = 2.5
ToonRotateSlowSpeed = 33.0
MickeySpeed = 5.0
MinnieSpeed = 3.2
DonaldSpeed = 3.68
GoofySpeed = 5.2
PlutoSpeed = 5.5
if __debug__:
    RefreshHotkey = 'f5'
    RefreshAIHotkey = 'shift-f5'
Separator = '-'
Shift = 'shift'
Control = 'control'
Release = 'up'
HotkeyMovement = 'movement'
HotkeyInteraction = 'interaction'
HotkeyDebug = 'debug'
HotkeyMisc = 'misc'
Hotkeys = (HotkeyMovement, HotkeyInteraction, HotkeyDebug, HotkeyMisc)
HotkeyUp = 0
HotkeyDown = 1
HotkeyLeft = 2
HotkeyRight = 3
HotkeyJump = 4
HotkeyAction = 5
HotkeyDescend = 6
HotkeyMovementDefaults = {
    HotkeyUp: 'w',
    HotkeyDown: 's',
    HotkeyLeft: 'a',
    HotkeyRight: 'd',
    HotkeyJump: 'space',
    HotkeyAction: 'e',
    HotkeyDescend: 'control',
}
HotkeyBook = 0
HotkeyBookSecondary = 1
HotkeyTasks = 2
HotkeyTasksClose = 3
HotkeyInventory = 4
HotkeyInventoryClose = 5
HotkeyFriends = 6
HotkeyMap = 7
HotkeyMapClose = 8
HotkeyMagicMenu = 11
HotkeyScreenshot = 12
HotkeyChat = 13
HotkeyChatlog = 14
HotkeyInteract = 15
HotkeyInteractionDefaults = {
    HotkeyBook: 'b',
    HotkeyBookSecondary: 'escape',
    HotkeyTasks: 'o',
    HotkeyTasksClose: 'o' + Separator + Release,
    HotkeyInventory: 'i',
    HotkeyInventoryClose: 'i' + Separator + Release,
    HotkeyFriends: 'p',
    HotkeyMap: 'm',
    HotkeyMapClose: 'm' + Separator + Release,
    HotkeyMagicMenu: 'insert',
    HotkeyScreenshot: 'f9',
    HotkeyChat: 't',
    HotkeyChatlog: 'enter',
    HotkeyInteract: 'f'
}
if sys.platform == 'darwin':
    # Mac default interaction keys goes here
    HotkeyInteractionDefaults[HotkeyMagicMenu] = 'meta'
HotkeyDebugInfo = 0
HotkeyFacilityDebug = 1
HotkeyCameraDebug = 2
HotkeyGarbage = 3
HotkeySync = 4
HotkeyMarker = 5
HotkeyTaskMgr = 6
HotkeyIval = 7
HotkeyDebugDefaults = {
    HotkeyDebugInfo: Shift + Separator + 'f1',
    HotkeyFacilityDebug: Shift + Separator + 'f2',
    HotkeyCameraDebug: Shift + Separator + 'f12',
    HotkeyGarbage: Shift + Separator + 'f11',
    HotkeySync: Shift + Separator + 'f6',
    HotkeyMarker: Shift + Separator + 'f3',
    HotkeyTaskMgr: Shift + Separator + Control + Separator + 'f1',
    HotkeyIval: Shift + Separator + Control + Separator + 'f2'
}
HotkeyCameraForward = 0
HotkeyCameraBackward = 1
HotkeyCameraMode = 2
HotkeyPageUp = 3
HotkeyPageDown = 4
HotkeyNametags = 5
HotkeyMargins = 6
HotkeyOobe = 7
HotkeyMiscDefaults = {
    HotkeyCameraForward: 'tab',
    HotkeyCameraBackward: Shift + Separator + 'tab',
    HotkeyCameraMode: 'f5',
    HotkeyPageUp: 'page_up',
    HotkeyPageDown: 'page_down',
    HotkeyNametags: 'f2',
    HotkeyMargins: 'f3',
    HotkeyOobe: 'f4'
}
AllHotkeys = (HotkeyMovementDefaults, HotkeyInteractionDefaults, HotkeyDebugDefaults, HotkeyMiscDefaults)
SpecialKeys = {
    'page_up': 'Page Up',
    'page_down': 'Page Down',
    'escape': 'Escape',
    'delete': 'Delete',
    'shift': 'Shift',
    'control': 'Control',
    'meta': ['Windows', 'Command'],
    'alt': ['Alt', 'Option'],
    'insert': 'Insert',
    'arrow_up': 'Up Arrow',
    'arrow_down': 'Down Arrow',
    'arrow_left': 'Left Arrow',
    'arrow_right': 'Right Arrow',
    'num_lock': 'Number Lock',
    'print_screen': 'Print Screen',
    'caps_lock': 'Caps Lock'
}
InvalidKey = 'Unknown'
GlobalDialogColor = (1,
 1,
 0.75,
 1)
DefaultBackgroundColor = (0.0, 0.0, 0.0, 0.0)
toonBodyScales = {'mouse': 0.6,
 'cat': 0.73,
 'duck': 0.66,
 'rabbit': 0.74,
 'horse': 0.85,
 'dog': 0.85,
 'monkey': 0.68,
 'bear': 0.85,
 'pig': 0.77,
 'gyro': 0.69,
 'scrooge': 0.66}
toonHeadScales = {'mouse': Point3(1.0),
 'cat': Point3(1.0),
 'duck': Point3(1.0),
 'rabbit': Point3(1.0),
 'horse': Point3(1.0),
 'dog': Point3(1.0),
 'monkey': Point3(1.0),
 'bear': Point3(1.0),
 'pig': Point3(1.0),
 'gyro': Point3(0.9),
 'scrooge': Point3(1.0)}
legHeightDict = {'s': 1.5,
 'm': 2.0,
 'l': 2.75}
torsoHeightDict = {'s': 1.5,
 'm': 1.75,
 'l': 2.25,
 'ss': 1.5,
 'ms': 1.75,
 'ls': 2.25,
 'sd': 1.5,
 'md': 1.75,
 'ld': 2.25}
headHeightDict = {'dls': 0.75,
 'dss': 0.5,
 'dsl': 0.5,
 'dll': 0.75,
 'cls': 0.75,
 'css': 0.5,
 'csl': 0.5,
 'cll': 0.75,
 'hls': 0.75,
 'hss': 0.5,
 'hsl': 0.5,
 'hll': 0.75,
 'mls': 0.75,
 'mss': 0.5,
 'rls': 0.75,
 'rss': 0.5,
 'rsl': 0.5,
 'rll': 0.75,
 'fls': 0.75,
 'fss': 0.5,
 'fsl': 0.5,
 'fll': 0.75,
 'pls': 0.75,
 'pss': 0.5,
 'psl': 0.5,
 'pll': 0.75,
 'bls': 0.75,
 'bss': 0.5,
 'bsl': 0.5,
 'bll': 0.75,
 'sls': 0.75,
 'sss': 0.5,
 'ssl': 0.5,
 'sll': 0.75,
 'iss': 0.75,
 'oss': 0.75}
RandomButton = 'Randomize'
TypeANameButton = 'Type Name'
PickANameButton = 'Pick-A-Name'
NameShopSubmitButton = 'Submit'
RejectNameText = 'That name is not allowed. Please try again.'
WaitingForNameSubmission = 'Submitting your name...'
NameShopNameMaster = 'NameMasterEnglish.txt'
NameShopPay = 'Subscribe Now!'
NameShopPlay = 'Free Trial'
NameShopOnlyPaid = 'Only paid users\nmay name their Toons.\nUntil you subscribe\nyour name will be\n'
NameShopContinueSubmission = 'Continue Submission'
NameShopChooseAnother = 'Choose Another Name'
NameShopToonCouncil = 'The Toon Council\nwill review your\nname.  ' + 'Review may\ntake a few days.\nWhile you wait\nyour name will be\n '
PleaseTypeName = 'Please type your name:'
AllNewNames = 'All new names\nmust be approved\nby the Toon Council.'
NameShopNameRejected = 'The name you\nsubmitted has\nbeen rejected.'
NameShopNameAccepted = 'Congratulations!\nThe name you\nsubmitted has\nbeen accepted!'
NoPunctuation = "You can't use punctuation marks in your name!"
PeriodOnlyAfterLetter = 'You can use a period in your name, but only after a letter.'
ApostropheOnlyAfterLetter = 'You can use an apostrophe in your name, but only after a letter.'
NoNumbersInTheMiddle = 'Numeric digits may not appear in the middle of a word.'
ThreeWordsOrLess = 'Your name must be three words or fewer.'
CopyrightedNames = ('mickey',
 'mickey mouse',
 'mickeymouse',
 'minnie',
 'minnie mouse',
 'minniemouse',
 'donald',
 'donald duck',
 'donaldduck',
 'pluto',
 'goofy')
GuildUpdateMembersEvent = 'guildUpdateMembersEvent'
GuildInvitationEvent = 'guildInvitationEvent'
GuildAcceptInviteEvent = 'guildAcceptInviteEvent'
GuildRejectInviteEvent = 'guildRejectInviteEvent'
AvatarFriendAddEvent = 'avatarFriendAddEvent'
AvatarNewFriendAddEvent = 'avatarNewFriendAddEvent'
AvatarFriendUpdateEvent = 'avatarFriendUpdateEvent'
AvatarFriendRemoveEvent = 'avatarFriendRemoveEvent'
PlayerFriendAddEvent = 'playerFriendAddEvent'
PlayerFriendUpdateEvent = 'playerFriendUpdateEvent'
PlayerFriendRemoveEvent = 'playerFriendRemoveEvent'
AvatarFriendConsideringEvent = 'avatarFriendConsideringEvent'
AvatarFriendInvitationEvent = 'avatarFriendInvitationEvent'
AvatarFriendRejectInviteEvent = 'avatarFriendRejectInviteEvent'
AvatarFriendRetractInviteEvent = 'avatarFriendRetractInviteEvent'
AvatarFriendRejectRemoveEvent = 'avatarFriendRejectRemoveEvent'
PlayerFriendInvitationEvent = 'playerFriendInvitationEvent'
PlayerFriendRejectInviteEvent = 'playerFriendRejectInviteEvent'
PlayerFriendRetractInviteEvent = 'playerFriendRetractInviteEvent'
PlayerFriendRejectRemoveEvent = 'playerFriendRejectRemoveEvent'
PlayerFriendNewSecretEvent = 'playerFriendNewSecretEvent'
PlayerFriendRejectNewSecretEvent = 'playerFriendRejectNewSecretEvent'
PlayerFriendRejectUseSecretEvent = 'playerFriendRejectUseSecretEvent'
WhisperIncomingEvent = 'whisperIncomingEvent'
ChatFeedback_PassedBlacklist = 32
ChatFeedback_Whitelist = 64
ChatFeedback_OpenChat = 128
MaxChatLength = 256
AccessUnknown = 0
AccessVelvetRope = 1
AccessFull = 2
AccessInvalid = 3
AvatarPendingCreate = -1
AvatarSlotUnavailable = -2
AvatarSlotAvailable = -3
AccessLevelName2Int = {
 'RESTRICTED': -100,  # A user that has been banned, or is restricted in some manner
 'NO_ACCESS': 0,  # A user without access to commands
 'USER': 100,  # A user with access to most commands
 'BUILDER': 101, # A user with access to most commands, with additional access to SpawnProp features
 'MODERATOR': 200,  # A user with access to all commands
 'ADMIN': 300,  # A user with higher access level than previous
 'SYSTEM_ADMIN': 400,  # A user with higher access level than previous
 'SERVER_HOSTER': 500,  # The highest access level a normal player can obtain
 'TTOFF_CREATIVE_TEAM': 600,  # A Toontown Realms Creative Team member
 'TTOFF_MODERATOR': 700,  # A Toontown Realms Support Team member
 'TTOFF_DEVELOPER': 800  # A Toontown Realms Developer
}
AccessLevelInt2Name = {
 -100: 'RESTRICTED',
 0: 'NO_ACCESS',
 100: 'USER',
 101: 'BUILDER',
 200: 'MODERATOR',
 300: 'ADMIN',
 400: 'SYSTEM_ADMIN',
 500: 'SERVER_HOSTER',
 600: 'TTOFF_CREATIVE_TEAM',
 700: 'TTOFF_MODERATOR',
 800: 'TTOFF_DEVELOPER'
}
AccessLevelDebug2Name = {
    'RESTRICTED': 'Banned',
    'NO_ACCESS': 'Player',
    'USER': 'User',
    'BUILDER': 'Builder',
    'MODERATOR': 'Mod',
    'ADMIN': 'Admin',
    'SYSTEM_ADMIN': 'Sysadmin',
    'SERVER_HOSTER': 'Hoster',
    'TTOFF_CREATIVE_TEAM': 'Creative',
    'TTOFF_MODERATOR': 'Support',
    'TTOFF_DEVELOPER': 'Developer'
}

BootedUnexpectedProblem = 1
BootedLoggedInElsewhere = 100
BootedKeyboardChatAuth = 120 # If I remember correctly, this is a bogus error message for hackers, but it doesn't seem to be used in TTOff
BootedConnectionKilled = 122 # GSM issues this when it enters the "Kill" state
BootedVersionMismatch = 124
BootedFileMismatch = 125
BootedNoAdminPrivileges = 126
BootedToonIssue = 127 # ???
BootedKickedForMaintenance = 151
BootedBanned = 152
BootedMiniServerReset = 153
BootedKicked = 155
BootedOutOfTime = 288
BootedOfflineMode = 300
BootedOfflineModeChange = 301
BootedOldVersion = 302
BootedMoreInfo = [BootedUnexpectedProblem, BootedConnectionKilled, BootedToonIssue]
BootedNoReconnect = [BootedToonIssue, BootedBanned, BootedKicked, BootedOldVersion]
DefaultDNAString = ('dss', 'ms', 'm', 'm', 0, 0, 0, 0, 0, 27, 0, 27, 0, 27)

TempAvIdBegin = 500000000
TempAvIdEnd = 599999999

ModeServer = 0
ModeOffline = 1
ConnectToServer = 0
ConnectToOfflineNoHost = 1
ConnectToOfflineHost = 2

BAN_HWID = 0
BAN_UUID = 1
BAN_IP = 2

UUID_FALLBACK = 'FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF'

ScreenshotFormats = ('jpg', 'png', 'tga', 'tif', 'exr')

CHAT_FILTER_DEFAULT = 0
CHAT_FILTER_CENSOR = 1
CHAT_FILTER_WHITELIST = 2