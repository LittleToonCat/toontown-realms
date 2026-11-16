import collections
import enum

from direct.showbase.PythonUtil import invertDict
from panda3d.core import BitMask32, Vec4

from otp.otpbase.OTPGlobals import *
from . import TTLocalizer

MapHotkey = 'alt'
AccountDatabaseChannelId = 4008
ToonDatabaseChannelId = 4021
DoodleDatabaseChannelId = 4023
DefaultDatabaseChannelId = AccountDatabaseChannelId
DatabaseIdFromClassName = {'Account': AccountDatabaseChannelId}
CogHQElevCamFov = 59
MakeAToonCameraFov = 52.0 / (4. / 3.)
MakeAToonCameraFovRetro = 35.0
# Make a toon camera zoom
MakeAToonCameraFarFov = 36.0  # Default position - zoomed out
MakeAToonCameraCloseFov = 12.0  # Closest zoom in
MakeAToonCameraDefaultHeight = 2.15  # Height at base zoom level
# offset the camera down a little bit from the toon height
MakeAToonCameraHeightOffset = -1

MakeAToonRotArrowPos = (
                    # zoomed out        zoomed in
                    ((-0.33, 0.0, 0.2), (-0.75, 0.0, 0.1)), # left
                    ((0.33, 0.0, 0.2),  (0.75, 0.0, 0.1)))   # right

# Bitmasks
CeilingBitmask = BitMask32(256)
FloorEventBitmask = BitMask32(16)
PieBitmask = BitMask32(256)
PetBitmask = BitMask32(8)
CatchGameBitmask = BitMask32(16)
CashbotBossObjectBitmask = BitMask32(16)
FurnitureSideBitmask = BitMask32(32)
FurnitureTopBitmask = BitMask32(64)
FurnitureDragBitmask = BitMask32(128)
PetLookatPetBitmask = BitMask32(256)
PetLookatNonPetBitmask = BitMask32(512)
BanquetTableBitmask = BitMask32(1024)

FullPies = 65535

CogHQCameraFar = 1500.0
CogHQCameraNear = 1.0
CashbotHQCameraFar = 2000.0
CashbotHQCameraNear = 1.0
LawbotHQCameraFar = 3000.0
LawbotHQCameraNear = 1.0
BossbotHQCameraFar = 3000.0
BossbotHQCameraNear = 1.0
SpeedwayCameraFar = 8000.0
SpeedwayCameraNear = 1.0
SpecialHoodCameraFar = 8000.0
SpecialHoodCameraNear = 1.0
DreamyDriveOutcoveCameraFar = 8000.0
DreamyDriveOutcoveCameraNear = 1.0
PartyCameraFar = 5000.0
PartyCameraNear = 1.0
EpisodeCameraFar = 10000.0
EpisodeCameraNear = 1.0

MaxMailboxContents = 30
MaxHouseItems = 45
MaxAccessories = 50
ExtraDeletedItems = 5
DeletedItemLifetime = 7 * 24 * 60
CatalogNumWeeksPerSeries = 13
CatalogNumWeeks = 78
PetFloorCollPriority = 5
PetPanelProximityPriority = 6

P_NoTrunk = -28
P_AlreadyOwnBiggerCloset = -27
P_ItemAlreadyRented = -26
P_OnAwardOrderListFull = -25
P_AwardMailboxFull = -24
P_ItemInPetTricks = -23
P_ItemInMyPhrases = -22
P_ItemOnAwardOrder = -21
P_ItemInAwardMailbox = -20
P_ItemAlreadyWorn = -19
P_ItemInCloset = -18
P_ItemOnGiftOrder = -17
P_ItemOnOrder = -16
P_ItemInMailbox = -15
P_PartyNotFound = 14
P_WillNotFit = -13
P_NotAGift = -12
P_OnOrderListFull = -11
P_MailboxFull = -10
P_NoPurchaseMethod = -9
P_ReachedPurchaseLimit = -8
P_NoRoomForItem = -7
P_NotShopping = -6
P_NotAtMailbox = -5
P_NotInCatalog = -4
P_NotEnoughMoney = -3
P_InvalidIndex = -2
P_UserCancelled = -1
P_ItemAvailable = 1
P_ItemUnneeded = 2
GIFT_user = 0
GIFT_admin = 1
GIFT_RAT = 2
GIFT_mobile = 3
GIFT_cogs = 4
GIFT_partyrefund = 5
FM_InvalidItem = -7
FM_NondeletableItem = -6
FM_InvalidIndex = -5
FM_NotOwner = -4
FM_NotDirector = -3
FM_RoomFull = -2
FM_HouseFull = -1
FM_MovedItem = 1
FM_SwappedItem = 2
FM_DeletedItem = 3
FM_RecoveredItem = 4
SPDonaldsBoat = 3
SPMinniesPiano = 4
MaxHpLimit = 137
MaxCarryLimit = 80
MaxQuestCarryLimit = 4
GravityValue = 32.174
NormalGravity = GravityValue * 2.0
AprilFoolsGravity = GravityValue * 0.75
MaxCogSuitLevel = 50 - 1
CogSuitHPLevels = (15 - 1,
 20 - 1,
 30 - 1,
 40 - 1,
 50 - 1)
setInterfaceFont(TTLocalizer.InterfaceFont)
setSignFont(TTLocalizer.SignFont)
from toontown.toontowngui import TTDialog
setDialogClasses(TTDialog.TTDialog, TTDialog.TTGlobalDialog)
ToonFont = None
BuildingNametagFont = None
MinnieFont = None
SuitFont = None
EpisodeFont = None
DebugFont = None
RealmsFont = None


def getToonFont():
    global ToonFont
    if ToonFont is None:
        ToonFont = loader.loadFont(TTLocalizer.ToonFont, lineHeight=1.0)
    return ToonFont


def getBuildingNametagFont():
    global BuildingNametagFont
    if BuildingNametagFont is None:
        BuildingNametagFont = loader.loadFont(TTLocalizer.BuildingNametagFont)
    return BuildingNametagFont


def getMinnieFont():
    global MinnieFont
    if MinnieFont is None:
        MinnieFont = loader.loadFont(TTLocalizer.MinnieFont)
    return MinnieFont


def getSuitFont():
    global SuitFont
    if SuitFont is None:
        SuitFont = loader.loadFont(TTLocalizer.SuitFont, pixelsPerUnit=128, spaceAdvance=0.25, lineHeight=1.0)
    return SuitFont


def getEpisodeFont():
    global EpisodeFont
    if EpisodeFont is None:
        EpisodeFont = loader.loadFont(TTLocalizer.EpisodeFont)
    return EpisodeFont


def getDebugFont():
    global DebugFont
    if DebugFont is None:
        DebugFont = loader.loadFont(TTLocalizer.DebugFont)
    return DebugFont

def getRealmsFont():
    global RealmsFont
    if RealmsFont is None:
        RealmsFont = loader.loadFont(TTLocalizer.RealmsFont)
    return RealmsFont

DonaldsDock = 1000
ToontownCentral = 2000
TheBrrrgh = 3000
MinniesMelodyland = 4000
DaisyGardens = 5000
OutdoorZone = 6000
HiddenCamp = 6100
FunnyFarm = 7000
GoofySpeedway = 8000
DonaldsDreamland = 9000
BarnacleBoulevard = 1100
SeaweedStreet = 1200
LighthouseLane = 1300
SillyStreet = 2100
LoopyLane = 2200
PunchlinePlace = 2300
WalrusWay = 3100
SleetStreet = 3200
PolarPlace = 3300
AltoAvenue = 4100
BaritoneBoulevard = 4200
TenorTerrace = 4300
ElmStreet = 5100
MapleStreet = 5200
OakStreet = 5300
LullabyLane = 9100
PajamaPlace = 9200
DreamyDriveOutcove = 9300
DreamyDrive = 9400
ToonHall = 2513
Kongdominium = 4656
Pizzeria = 19504
ToonyLab = 19505
PrivateServerCafe = 19513
ToonMuseum = 19515
TutorialInterior = 19602
GyrosLab = 22634
ToonlandLibrary = 31518
WelcomeValleyToken = 0
BossbotHQ = 10000
BossbotLobby = 10100
BossbotCountryClubIntA = 10500
BossbotCountryClubIntB = 10600
BossbotCountryClubIntC = 10700
SellbotHQ = 11000
SellbotLobby = 11100
SellbotFactoryExt = 11200
SellbotFactoryInt = 11500
CashbotHQ = 12000
CashbotLobby = 12100
CashbotMintIntA = 12500
CashbotMintIntB = 12600
CashbotMintIntC = 12700
LawbotHQ = 13000
LawbotLobby = 13100
LawbotOfficeExt = 13200
LawbotOfficeInt = 13300
LawbotStageIntA = 13300
LawbotStageIntB = 13400
LawbotStageIntC = 13500
LawbotStageIntD = 13600
Tutorial = 15000
MyEstate = 16000
GolfZone = 17000
PartyHood = 18000
ToontownOutskirts = 19000
TutorialTerrace = 19100
SellbotHQFuture = 19200
CogtownCentral = 19300
TutorialHood = 20000
ToontownCentralBeta = 21000
SillyStreetBeta = 21100
DaisyGardensBeta = 22000
OakStreetBeta = 22100
MinniesMelodylandBeta = 23000
DonaldsDreamlandBeta = 24000
TheBrrrghBeta = 25000
DonaldsDockBeta = 26000
ToontownSkies = 30000
CreativeFieldsA = 30100
CreativeFieldsB = 30200
CreativeFieldsC = 30300
CreativeFieldsD = 30400
CreativeFieldsE = 30500
ToonLandFunnyFarm = 31000
ToonLandBarkingBoulv = 31100
Episode = 50000
# These are temporary for the map on prod.
Duckburg = 69
Scrapyards = 420
HoodsAlwaysVisited = [GolfZone, PartyHood, ToontownOutskirts, SellbotHQFuture, CogtownCentral,
                      ToontownCentralBeta, DaisyGardensBeta, MinniesMelodylandBeta, DonaldsDreamlandBeta,
                      TheBrrrghBeta, DonaldsDockBeta, ToontownSkies,  ToonLandFunnyFarm]

WelcomeValleyBegin = 40000
WelcomeValleyEnd = 60000
DynamicZonesBegin = 61000
DynamicZonesEnd = 1 << 20
HoodHierarchy = {ToontownCentral: (SillyStreet, LoopyLane, PunchlinePlace),
                 DonaldsDock: (BarnacleBoulevard, SeaweedStreet, LighthouseLane),
                 TheBrrrgh: (WalrusWay, SleetStreet, PolarPlace),
                 MinniesMelodyland: (AltoAvenue, BaritoneBoulevard, TenorTerrace),
                 DaisyGardens: (ElmStreet, MapleStreet, OakStreet),
                 DonaldsDreamland: (LullabyLane, PajamaPlace, DreamyDriveOutcove, DreamyDrive),
                 OutdoorZone: (HiddenCamp,),
                 GoofySpeedway: (),
                 ToontownOutskirts: (TutorialTerrace, CogtownCentral, SellbotHQFuture),
                 ToontownCentralBeta: (SillyStreetBeta,),
                 DaisyGardensBeta: (OakStreetBeta,),
                 MinniesMelodylandBeta: (),
                 DonaldsDreamlandBeta: (),
                 TheBrrrghBeta: (),
                 DonaldsDockBeta: (),
                 ToonLandFunnyFarm: (ToonLandBarkingBoulv,),
                 ToontownSkies: (CreativeFieldsA, CreativeFieldsB, CreativeFieldsC, CreativeFieldsD)}

cogDept2index = {'c': 0,
 'l': 1,
 'm': 2,
 's': 3}
cogIndex2dept = invertDict(cogDept2index)
HQToSafezone = {SellbotHQ: DaisyGardens,
 CashbotHQ: DonaldsDreamland,
 LawbotHQ: TheBrrrgh,
 BossbotHQ: DonaldsDock}
CogDeptNames = [TTLocalizer.Bossbot,
 TTLocalizer.Lawbot,
 TTLocalizer.Cashbot,
 TTLocalizer.Sellbot]


def cogHQZoneId2deptIndex(zone):
    if 13000 <= zone <= 13999:
        # LBHQ
        return 1
    elif zone >= 12000:
        # CBHQ
        return 2
    elif zone >= 11000:
        # SBHQ
        return 3
    else:
        # BBHQ
        return 0


def cogHQZoneId2dept(zone):
    return cogIndex2dept[cogHQZoneId2deptIndex(zone)]


def dept2cogHQ(dept):
    dept2hq = {'c': BossbotHQ,
     'l': LawbotHQ,
     'm': CashbotHQ,
     's': SellbotHQ}
    return dept2hq[dept]


MockupFactoryId = 0
MintNumFloors = {CashbotMintIntA: 20,
 CashbotMintIntB: 20,
 CashbotMintIntC: 20}
CashbotMintCogLevel = 10
CashbotMintSkelecogLevel = 11
CashbotMintBossLevel = 12
MintNumBattles = {CashbotMintIntA: 4,
 CashbotMintIntB: 6,
 CashbotMintIntC: 8}
MintCogBuckRewards = {CashbotMintIntA: 8,
 CashbotMintIntB: 14,
 CashbotMintIntC: 20}
MintNumRooms = {CashbotMintIntA: 2 * (6,) + 5 * (7,) + 5 * (8,) + 5 * (9,) + 3 * (10,),
 CashbotMintIntB: 3 * (8,) + 6 * (9,) + 6 * (10,) + 5 * (11,),
 CashbotMintIntC: 4 * (10,) + 10 * (11,) + 6 * (12,)}
BossbotCountryClubCogLevel = 11
BossbotCountryClubSkelecogLevel = 12
BossbotCountryClubBossLevel = 12
CountryClubNumRooms = {BossbotCountryClubIntA: (4,),
 BossbotCountryClubIntB: 3 * (8,) + 6 * (9,) + 6 * (10,) + 5 * (11,),
 BossbotCountryClubIntC: 4 * (10,) + 10 * (11,) + 6 * (12,)}
CountryClubNumBattles = {BossbotCountryClubIntA: 3,
 BossbotCountryClubIntB: 2,
 BossbotCountryClubIntC: 3}
CountryClubCogBuckRewards = {BossbotCountryClubIntA: 8,
 BossbotCountryClubIntB: 14,
 BossbotCountryClubIntC: 20}
LawbotStageCogLevel = 10
LawbotStageSkelecogLevel = 11
LawbotStageBossLevel = 12
StageNumBattles = {LawbotStageIntA: 0,
 LawbotStageIntB: 0,
 LawbotStageIntC: 0,
 LawbotStageIntD: 0}
StageNoticeRewards = {LawbotStageIntA: 75,
 LawbotStageIntB: 150,
 LawbotStageIntC: 225,
 LawbotStageIntD: 300}
StageNumRooms = {LawbotStageIntA: 2 * (6,) + 5 * (7,) + 5 * (8,) + 5 * (9,) + 3 * (10,),
 LawbotStageIntB: 3 * (8,) + 6 * (9,) + 6 * (10,) + 5 * (11,),
 LawbotStageIntC: 4 * (10,) + 10 * (11,) + 6 * (12,),
 LawbotStageIntD: 4 * (10,) + 10 * (11,) + 6 * (12,)}
FT_FullSuit = 'fullSuit'
FT_Leg = 'leg'
FT_Arm = 'arm'
FT_Torso = 'torso'
factoryId2factoryType = {MockupFactoryId: FT_FullSuit,
 SellbotFactoryInt: FT_FullSuit,
 LawbotOfficeInt: FT_FullSuit}
StreetNames = TTLocalizer.GlobalStreetNames
StreetBranchZones = list(StreetNames.keys())
Hoods = (DonaldsDock,
         ToontownCentral,
         TheBrrrgh,
         MinniesMelodyland,
         DaisyGardens,
         OutdoorZone,
         FunnyFarm,
         GoofySpeedway,
         DonaldsDreamland,
         BossbotHQ,
         SellbotHQ,
         CashbotHQ,
         LawbotHQ,
         GolfZone,
         ToontownOutskirts,
         ToontownCentralBeta,
         DaisyGardensBeta,
         MinniesMelodylandBeta,
         DonaldsDreamlandBeta,
         TheBrrrghBeta,
         DonaldsDockBeta,
         ToontownSkies,
         ToonLandFunnyFarm
         )
HoodsForTeleportAll = (DonaldsDock,
                       ToontownCentral,
                       TheBrrrgh,
                       MinniesMelodyland,
                       DaisyGardens,
                       OutdoorZone,
                       GoofySpeedway,
                       DonaldsDreamland,
                       BossbotHQ,
                       SellbotHQ,
                       CashbotHQ,
                       LawbotHQ,
                       GolfZone,
                       ToontownOutskirts,
                       ToontownCentralBeta,
                       DaisyGardensBeta,
                       MinniesMelodylandBeta,
                       DonaldsDreamlandBeta,
                       TheBrrrghBeta,
                       DonaldsDockBeta,
                       ToontownSkies,
                       ToonLandFunnyFarm)
HoodsWithMinigames = (DonaldsDock,
 ToontownCentral,
 TheBrrrgh,
 MinniesMelodyland,
 DaisyGardens,
 DonaldsDreamland,
 ToontownCentralBeta,
 DaisyGardensBeta,
 MinniesMelodylandBeta,
 DonaldsDreamlandBeta,
 TheBrrrghBeta,
 DonaldsDockBeta,
 ToontownOutskirts)
NoPreviousGameId = 0
RaceGameId = 1
CannonGameId = 2
TagGameId = 3
PatternGameId = 4
RingGameId = 5
MazeGameId = 6
TugOfWarGameId = 7
CatchGameId = 8
DivingGameId = 9
TargetGameId = 10
PairingGameId = 11
VineGameId = 12
IceGameId = 13
CogThiefGameId = 14
TwoDGameId = 15
PhotoGameId = 16
MinigameTemplateId = 17
PatternGameBetaId = 18
RaceGameBetaId = 19
TravelGameId = 100
MinigameNames = {'race': RaceGameId,
 'racing': RaceGameId,
 'racebeta': RaceGameBetaId,
 'racingbeta': RaceGameBetaId,
 'cannon': CannonGameId,
 'tag': TagGameId,
 'toontag': TagGameId,
 'pattern': PatternGameId,
 'minnie': PatternGameId,
 'match': PatternGameId,
 'matching': PatternGameId,
 'patternbeta': PatternGameBetaId,
 'minniebeta': PatternGameBetaId,
 'matchbeta': PatternGameBetaId,
 'matchingbeta': PatternGameBetaId,
 'ring': RingGameId,
 'maze': MazeGameId,
 'tug': TugOfWarGameId,
 'tugofwar': TugOfWarGameId,
 'catch': CatchGameId,
 'diving': DivingGameId,
 'target': TargetGameId,
 'toonslingshot': TargetGameId,
 'slingshot': TargetGameId,
 'pairing': PairingGameId,
 'memory': PairingGameId,
 'vine': VineGameId,
 'junglevines': VineGameId,
 'ice': IceGameId,
 'iceslide': IceGameId,
 'cogthief': CogThiefGameId,
 'thief': CogThiefGameId,
 '2d': TwoDGameId,
 'escape': TwoDGameId,
 'toonescape': TwoDGameId,
 'photo': PhotoGameId,
 'photofun': PhotoGameId,
 'template': MinigameTemplateId,
 'travel': TravelGameId}
MinigameIDs = (RaceGameId,
 CannonGameId,
 TagGameId,
 PatternGameId,
 RingGameId,
 MazeGameId,
 TugOfWarGameId,
 CatchGameId,
 DivingGameId,
 TargetGameId,
 PairingGameId,
 VineGameId,
 IceGameId,
 CogThiefGameId,
 TwoDGameId,
 PhotoGameId,
 MinigameTemplateId,
 TravelGameId,
 PatternGameBetaId,
 RaceGameBetaId)
MinigamePlayerMatrix = {1: (CannonGameId,
     RingGameId,
     MazeGameId,
     TugOfWarGameId,
     CatchGameId,
     DivingGameId,
     TargetGameId,
     PairingGameId,
     VineGameId,
     CogThiefGameId,
     TwoDGameId),
 2: (CannonGameId,
     PatternGameId,
     RingGameId,
     TagGameId,
     MazeGameId,
     TugOfWarGameId,
     CatchGameId,
     DivingGameId,
     TargetGameId,
     PairingGameId,
     VineGameId,
     IceGameId,
     CogThiefGameId,
     TwoDGameId),
 3: (CannonGameId,
     PatternGameId,
     RingGameId,
     TagGameId,
     RaceGameId,
     MazeGameId,
     TugOfWarGameId,
     CatchGameId,
     DivingGameId,
     TargetGameId,
     PairingGameId,
     VineGameId,
     IceGameId,
     CogThiefGameId,
     TwoDGameId),
 4: (CannonGameId,
     PatternGameId,
     RingGameId,
     TagGameId,
     RaceGameId,
     MazeGameId,
     TugOfWarGameId,
     CatchGameId,
     DivingGameId,
     TargetGameId,
     PairingGameId,
     VineGameId,
     IceGameId,
     CogThiefGameId,
     TwoDGameId)}
MinigameReleaseDates = {IceGameId: (2008, 8, 5),
                        PhotoGameId: (2008, 8, 13),
                        TwoDGameId: (2008, 8, 20),
                        CogThiefGameId: (2008, 8, 27)}
KeyboardTimeout = 300
phaseMap = {Tutorial: 4,
            ToontownCentral: 4,
            MyEstate: 5.5,
            DonaldsDock: 6,
            MinniesMelodyland: 6,
            GoofySpeedway: 6,
            TheBrrrgh: 8,
            DaisyGardens: 8,
            FunnyFarm: 8,
            DonaldsDreamland: 8,
            OutdoorZone: 6,
            BossbotHQ: 12,
            SellbotHQ: 9,
            CashbotHQ: 10,
            LawbotHQ: 11,
            GolfZone: 6,
            PartyHood: 13,
            ToontownOutskirts: 14.5,
            ToontownCentralBeta: 14.5,
            DaisyGardensBeta: 14.5,
            MinniesMelodylandBeta: 14.5,
            DonaldsDreamlandBeta: 14.5,
            TheBrrrghBeta: 14.5,
            DonaldsDockBeta: 14.5,
            Episode: 14,
            # TODO: Sort these out, they shouldn't have to be here
            ToontownSkies: 14.5,
            CogtownCentral: 14.5,
            SellbotHQFuture: 14.5,
            ToonLandFunnyFarm: 14.5}
streetPhaseMap = {ToontownCentral: 5,
                  DonaldsDock: 6,
                  MinniesMelodyland: 6,
                  GoofySpeedway: 6,
                  TheBrrrgh: 8,
                  DaisyGardens: 8,
                  FunnyFarm: 8,
                  DonaldsDreamland: 8,
                  OutdoorZone: 6,
                  BossbotHQ: 12,
                  SellbotHQ: 9,
                  CashbotHQ: 10,
                  LawbotHQ: 11,
                  PartyHood: 13,
                  ToontownOutskirts: 14.5,
                  ToontownCentralBeta: 14.5,
                  DaisyGardensBeta: 14.5,
                  MinniesMelodylandBeta: 14.5,
                  DonaldsDreamlandBeta: 14.5,
                  TheBrrrghBeta: 14.5,
                  DonaldsDockBeta: 14.5,
                  # TODO: Sort these out, they shouldn't have to be here
                  ToontownSkies: 14.5,
                  CogtownCentral: 14.5,
                  SellbotHQFuture: 14.5,
                  ToonLandFunnyFarm: 14.5}
dnaMap = {Tutorial: 'ttc',
          ToontownCentral: 'ttc',
          DonaldsDock: 'dod',
          MinniesMelodyland: 'mml',
          GoofySpeedway: 'gsw',
          TheBrrrgh: 'tbr',
          DaisyGardens: 'dga',
          FunnyFarm: 'trash',
          DonaldsDreamland: 'ddl',
          OutdoorZone: 'cda',
          BossbotHQ: 'bbhq',
          SellbotHQ: 'sbhq',
          CashbotHQ: 'cbhq',
          LawbotHQ: 'lbhq',
          GolfZone: 'cmg',
          ToontownCentralBeta: 'ttcb',
          DaisyGardensBeta: 'dgb',
          MinniesMelodylandBeta: 'mmlb',
          DonaldsDreamlandBeta: 'ddlb',
          TheBrrrghBeta: 'brb',
          DonaldsDockBeta: 'ddb',
          ToontownSkies: 'crf',
          ToonLandFunnyFarm: 'tnl'
          }
hoodNameMap = {DonaldsDock: TTLocalizer.DonaldsDock,
               ToontownCentral: TTLocalizer.ToontownCentral,
               TheBrrrgh: TTLocalizer.TheBrrrgh,
               MinniesMelodyland: TTLocalizer.MinniesMelodyland,
               DaisyGardens: TTLocalizer.DaisyGardens,
               OutdoorZone: TTLocalizer.OutdoorZone,
               FunnyFarm: TTLocalizer.FunnyFarm,
               GoofySpeedway: TTLocalizer.GoofySpeedway,
               DonaldsDreamland: TTLocalizer.DonaldsDreamland,
               BossbotHQ: TTLocalizer.BossbotHQ,
               SellbotHQ: TTLocalizer.SellbotHQ,
               CashbotHQ: TTLocalizer.CashbotHQ,
               LawbotHQ: TTLocalizer.LawbotHQ,
               Tutorial: TTLocalizer.Tutorial,
               MyEstate: TTLocalizer.MyEstate,
               GolfZone: TTLocalizer.GolfZone,
               PartyHood: TTLocalizer.PartyHood,
               ToontownOutskirts: TTLocalizer.SpecialHood,
               ToontownCentralBeta: TTLocalizer.ToontownCentralBeta,
               DaisyGardensBeta: TTLocalizer.DaisyGardensBeta,
               MinniesMelodylandBeta: TTLocalizer.MinniesMelodylandBeta,
               DonaldsDreamlandBeta: TTLocalizer.DonaldsDreamlandBeta,
               TheBrrrghBeta: TTLocalizer.TheBrrrghBeta,
               DonaldsDockBeta: TTLocalizer.DonaldsDockBeta,
               Episode: TTLocalizer.EpisodeHood,
               Duckburg: TTLocalizer.Duckburg,
               Scrapyards: TTLocalizer.Scrapyards,
               ToontownSkies: TTLocalizer.CreativeFields,
               CogtownCentral: TTLocalizer.CogtownCentral,
               SellbotHQFuture: TTLocalizer.SellbotHQ,
               ToonLandFunnyFarm: TTLocalizer.ToonLandFunnyFarm}
safeZoneCountMap = {MyEstate: 90,
                    Tutorial: 6,
                    ToontownCentral: 30,
                    DonaldsDock: 35,
                    MinniesMelodyland: 27,
                    GoofySpeedway: 20,
                    TheBrrrgh: 21,
                    DaisyGardens: 33,
                    FunnyFarm: 500,
                    DonaldsDreamland: 25,
                    OutdoorZone: 41,
                    GolfZone: 32,
                    PartyHood: 84,
                    ToontownOutskirts: 85,
                    ToontownCentralBeta: 27,
                    DaisyGardensBeta: 31,
                    MinniesMelodylandBeta: 27,
                    DonaldsDreamlandBeta: 27,
                    TheBrrrghBeta: 31,
                    DonaldsDockBeta: 37,
                    Episode: 6,
                    ToontownSkies: 77,
                    CogtownCentral: 5,
                    SellbotHQFuture: 5,
                    ToonLandFunnyFarm: 5}
townCountMap = {MyEstate: 8,
                Tutorial: 40,
                ToontownCentral: 200,
                DonaldsDock: 220,
                MinniesMelodyland: 220,
                GoofySpeedway: 220,
                TheBrrrgh: 220,
                DaisyGardens: 220,
                FunnyFarm: 40,
                DonaldsDreamland: 220,
                OutdoorZone: 40,
                PartyHood: 20,
                ToontownOutskirts: 40,
                ToontownCentralBeta: 40,
                DaisyGardensBeta: 40,
                MinniesMelodylandBeta: 40,
                DonaldsDreamlandBeta: 40,
                TheBrrrghBeta: 40,
                DonaldsDockBeta: 40,
                Episode: 40,
                # TODO: Sort these two out, they shouldn't need to be here
                ToontownSkies: 5,
                CogtownCentral: 5,
                SellbotHQFuture: 5,
                ToonLandFunnyFarm: 40}
hoodCountMap = {MyEstate: 2,
                Tutorial: 2,
                ToontownCentral: 2,
                DonaldsDock: 2,
                MinniesMelodyland: 2,
                GoofySpeedway: 2,
                TheBrrrgh: 2,
                DaisyGardens: 2,
                FunnyFarm: 2,
                DonaldsDreamland: 2,
                OutdoorZone: 2,
                BossbotHQ: 37,
                SellbotHQ: 39,
                CashbotHQ: 38,
                LawbotHQ: 37,
                GolfZone: 2,
                PartyHood: 2,
                ToontownOutskirts: 2,
                ToontownCentralBeta: 2,
                DaisyGardensBeta: 2,
                MinniesMelodylandBeta: 2,
                DonaldsDreamlandBeta: 2,
                TheBrrrghBeta: 2,
                DonaldsDockBeta: 2,
                Episode: 2,
                # TODO: Sort these two out, they shouldn't need to be here
                ToontownSkies: 2,
                CogtownCentral: 2,
                SellbotHQFuture: 2,
                ToonLandFunnyFarm: 2}
TrophyStarLevels = (10, 20, 30, 50, 75, 100, 150, 200)
TrophyStarColors = (Vec4(0.9, 0.6, 0.2, 1),
                    Vec4(0.9, 0.6, 0.2, 1),
                    Vec4(1, 1, 1, 1),
                    Vec4(1, 1, 1, 1),
                    Vec4(1, 1, 0, 1),
                    Vec4(1, 1, 0, 1))
TrophyStarSpeed = (0, 8, 0, 10, 0, 15, 0, 15)
MickeySpeed = 5.0
VampireMickeySpeed = 1.15
MinnieSpeed = 3.2
WitchMinnieSpeed = 1.8
DonaldSpeed = 3.68
BetaDonaldSpeed = 4.6
FrankenDonaldSpeed = 0.9
DaisySpeed = 2.3
GoofySpeed = 5.2
SuperGoofySpeed = 1.6
PlutoSpeed = 5.5
WesternPlutoSpeed = 3.2
ChipSpeed = 3
DaleSpeed = 3.5
DaleOrbitDistance = 3
SuitWalkSpeed = 4.8
PieCodeBossCog = 1
PieCodeNotBossCog = 2
PieCodeToon = 3
PieCodeBossInsides = 4
PieCodeDefensePan = 5
PieCodeProsecutionPan = 6
PieCodeLawyer = 7
PieCodeColors = {PieCodeBossCog: None,
                 PieCodeNotBossCog: (0.8, 0.8, 0.8, 1),
                 PieCodeToon: None}
BossCogRollSpeed = 7.5
BossCogTurnSpeed = 20
BossCogTreadSpeed = 3.5
BossCogDizzy = 0
BossCogElectricFence = 1
BossCogSwatLeft = 2
BossCogSwatRight = 3
BossCogAreaAttack = 4
BossCogFrontAttack = 5
BossCogRecoverDizzyAttack = 6
BossCogDirectedAttack = 7
BossCogStrafeAttack = 8
BossCogNoAttack = 9
BossCogGoonZap = 10
BossCogSlowDirectedAttack = 11
BossCogDizzyNow = 12
BossCogGavelStomp = 13
BossCogGavelHandle = 14
BossCogLawyerAttack = 15
BossCogMoveAttack = 16
BossCogGolfAttack = 17
BossCogGolfAreaAttack = 18
BossCogGearDirectedAttack = 19
BossCogOvertimeAttack = 20
BossCogProlongedLawyerAttack = 21
BossCogAttackTimes = {BossCogElectricFence: 0,
                      BossCogSwatLeft: 5.5,
                      BossCogSwatRight: 5.5,
                      BossCogAreaAttack: 4.21,
                      BossCogFrontAttack: 2.65,
                      BossCogRecoverDizzyAttack: 5.1,
                      BossCogDirectedAttack: 4.84,
                      BossCogNoAttack: 6,
                      BossCogSlowDirectedAttack: 7.84,
                      BossCogMoveAttack: 3,
                      BossCogGolfAttack: 6,
                      BossCogGolfAreaAttack: 7,
                      BossCogGearDirectedAttack: 4.84,
                      BossCogOvertimeAttack: 5}
BossCogDamageLevels = {BossCogElectricFence: 1,
                       BossCogSwatLeft: 5,
                       BossCogSwatRight: 5,
                       BossCogAreaAttack: 10,
                       BossCogFrontAttack: 3,
                       BossCogRecoverDizzyAttack: 3,
                       BossCogDirectedAttack: 3,
                       BossCogStrafeAttack: 2,
                       BossCogGoonZap: 5,
                       BossCogSlowDirectedAttack: 10,
                       BossCogGavelStomp: 20,
                       BossCogGavelHandle: 2,
                       BossCogLawyerAttack: 5,
                       BossCogMoveAttack: 20,
                       BossCogGolfAttack: 15,
                       BossCogGolfAreaAttack: 15,
                       BossCogGearDirectedAttack: 15,
                       BossCogOvertimeAttack: 10,
                       BossCogProlongedLawyerAttack: 5}
BossCogBattleAPosHpr = (0, -25, 0, 0, 0, 0)
BossCogBattleBPosHpr = (0, 25, 0, 180, 0, 0)
SellbotBossMaxDamage = 100
SellbotBossMaxDamageHardcore = 200
SellbotBossMaxDamageNerfed = 100
SellbotBossMaxDamageNerfs = 50
SellbotBossBattleOnePosHpr = (0, -35, 0, -90, 0, 0)
SellbotBossBattleTwoPosHpr = (0, 60, 18, -90, 0, 0)
SellbotBossBattleThreeHpr = (180, 0, 0)
SellbotBossBottomPos = (0, -110, -6.5)
SellbotBossDeathPos = (0, -175, -6.5)
SellbotBossBottomPosHardcore = (0, -286, -39.09)
SellbotBossDeathPosHardcore = (0, -362, -39.09)
SellbotBossDooberTurnPosA = (-20, -50, 0)
SellbotBossDooberTurnPosB = (20, -50, 0)
SellbotBossDooberTurnPosDown = (0, -50, 0)
SellbotBossDooberExtendPosHardcore = (0, -60, 0)
SellbotBossDooberFlyPos = (0, -135, -6.5)
SellbotBossDooberFlyPosHardcore = (0, -287, -39.09)
SellbotBossTopRampPosA = (-80, -35, 18)
SellbotBossTopRampTurnPosA = (-80, 10, 18)
SellbotBossP3PosA = (-50, 40, 18)
SellbotBossTopRampPosB = (80, -35, 18)
SellbotBossTopRampTurnPosB = (80, 10, 18)
SellbotBossP3PosB = (50, 60, 18)
CashbotBossMaxDamage = 500
CashbotBossMaxDamageHardcore = 1500
CashbotBossMaxDamageNerfs = 250
CashbotBossOffstagePosHpr = (120, -195, 0, 0, 0, 0)
CashbotBossBattleOnePosHpr = (120, -230, 0, 90, 0, 0)
CashbotRTBattleOneStartPosHpr = (94, -220, 0, 110, 0, 0)
CashbotBossBattleThreePosHpr = (120, -315, 0, 180, 0, 0)
CashbotToonsBattleThreeStartPosHpr = [(105, -285, 0, 208, 0, 0),
                                      (136, -342, 0, 398, 0, 0),
                                      (105, -342, 0, 333, 0, 0),
                                      (135, -292, 0, 146, 0, 0),
                                      (93, -303, 0, 242, 0, 0),
                                      (144, -327, 0, 64, 0, 0),
                                      (145, -302, 0, 117, 0, 0),
                                      (93, -327, 0, -65, 0, 0)]
CashbotBossSafePosHprs = [(120, -315, 30, 0, 0, 0),
                          (77.2, -329.3, 0, -90, 0, 0),
                          (77.1, -302.7, 0, -90, 0, 0),
                          (165.7, -326.4, 0, 90, 0, 0),
                          (165.5, -302.4, 0, 90, 0, 0),
                          (107.8, -359.1, 0, 0, 0, 0),
                          (133.9, -359.1, 0, 0, 0, 0),
                          (107.0, -274.7, 0, 180, 0, 0),
                          (134.2, -274.7, 0, 180, 0, 0)]
CashbotBossCranePosHprs = [(97.4, -337.6, 0, -45, 0, 0),
                           (97.4, -292.4, 0, -135, 0, 0),
                           (142.6, -292.4, 0, 135, 0, 0),
                           (142.6, -337.6, 0, 45, 0, 0)]
CashbotBossToMagnetTime = 0.2
CashbotBossFromMagnetTime = 1
CashbotBossSafeKnockImpact = 0.5
CashbotBossSafeNewImpact = 0.0
CashbotBossGoonImpact = 0.1
CashbotBossKnockoutDamage = 15
TTWakeWaterHeight = -4.79
DDWakeWaterHeight = 1.669
EstateWakeWaterHeight = -.3
OZWakeWaterHeight = -0.5
WakeRunDelta = 0.1
WakeWalkDelta = 0.2
NoItems = 0
NewItems = 1
OldItems = 2
SuitInvasionBegin = 0
SuitInvasionUpdate = 1
SuitInvasionEnd = 2
SuitInvasionBulletin = 3

# Holidays
# TODO: reorganize holidays
NO_HOLIDAY = 0
JULY4_FIREWORKS = 1
NEWYEARS_FIREWORKS = 2
HALLOWEEN = 3
WINTER_DECORATIONS = 4
SKELECOG_INVASION = 5
MR_HOLLYWOOD_INVASION = 6
FISH_BINGO_NIGHT = 7
ELECTION_PROMOTION = 8
BLACK_CAT_DAY = 9
KART_RECORD_DAILY_RESET = 11
KART_RECORD_WEEKLY_RESET = 12
TRICK_OR_TREAT = 13
CIRCUIT_RACING = 14
CIRCUIT_RACING_EVENT = 16
TROLLEY_HOLIDAY = 17
TROLLEY_WEEKEND = 18
SILLY_SATURDAY_BINGO = 19
SILLY_SATURDAY_CIRCUIT = 20
SILLY_SATURDAY_TROLLEY = 21
ROAMING_TRIALER_WEEKEND = 22
BOSSCOG_INVASION = 23
MARCH_INVASION = 24
MORE_XP_HOLIDAY = 25
HALLOWEEN_PROPS = 26
HALLOWEEN_COSTUMES = 27
DECEMBER_INVASION = 28
APRIL_FOOLS_COSTUMES = 29
CRASHED_LEADERBOARD = 30
SELLBOT_SURPRISE_1 = 33
SELLBOT_SURPRISE_2 = 34
SELLBOT_SURPRISE_3 = 35
SELLBOT_SURPRISE_4 = 36
CASHBOT_CONUNDRUM_1 = 37
CASHBOT_CONUNDRUM_2 = 38
CASHBOT_CONUNDRUM_3 = 39
CASHBOT_CONUNDRUM_4 = 40
LAWBOT_GAMBIT_1 = 41
LAWBOT_GAMBIT_2 = 42
LAWBOT_GAMBIT_3 = 43
LAWBOT_GAMBIT_4 = 44
TROUBLE_BOSSBOTS_1 = 45
TROUBLE_BOSSBOTS_2 = 46
TROUBLE_BOSSBOTS_3 = 47
TROUBLE_BOSSBOTS_4 = 48
JELLYBEAN_DAY = 49
BIGWIG_INVASION = 54
COLD_CALLER_INVASION = 53
BEAN_COUNTER_INVASION = 54
DOUBLE_TALKER_INVASION = 55
DOWNSIZER_INVASION = 56
WINTER_CAROLING = 57
HYDRANT_ZERO_HOLIDAY = 58
VALENTINES_DAY = 59
SILLYMETER_HOLIDAY = 60
MAILBOX_ZERO_HOLIDAY = 61
TRASHCAN_ZERO_HOLIDAY = 62
SILLY_SURGE_HOLIDAY = 63
HYDRANTS_BUFF_BATTLES = 64
MAILBOXES_BUFF_BATTLES = 65
TRASHCANS_BUFF_BATTLES = 66
SILLY_CHATTER_ONE = 67
SILLY_CHATTER_TWO = 68
SILLY_CHATTER_THREE = 69
SILLY_CHATTER_FOUR = 70
SILLY_TEST = 71
YES_MAN_INVASION = 72
TIGHTWAD_INVASION = 73
TELEMARKETER_INVASION = 74
HEADHUNTER_INVASION = 75
SPINDOCTOR_INVASION = 76
MONEYBAGS_INVASION = 77
TWOFACES_INVASION = 78
MINGLER_INVASION = 79
LOANSHARK_INVASION = 80
CORPORATE_RAIDER_INVASION = 81
ROBBER_BARON_INVASION = 82
LEGAL_EAGLE_INVASION = 83
BIG_WIG_INVASION = 84
BIG_CHEESE_INVASION = 85
DOWN_SIZER_INVASION = 86
MOVER_AND_SHAKER_INVASION = 87
DOUBLETALKER_INVASION = 88
PENNY_PINCHER_INVASION = 89
NAME_DROPPER_INVASION = 90
AMBULANCE_CHASER_INVASION = 91
MICROMANAGER_INVASION = 92
NUMBER_CRUNCHER_INVASION = 93
SILLY_CHATTER_FIVE = 94
VICTORY_PARTY_HOLIDAY = 95
SELLBOT_NERF_HOLIDAY = 96
JELLYBEAN_TROLLEY_HOLIDAY = 97
JELLYBEAN_FISHING_HOLIDAY = 98
JELLYBEAN_PARTIES_HOLIDAY = 99
BANK_UPGRADE_HOLIDAY = 100
TOP_TOONS_MARATHON = 101
SELLBOT_INVASION = 102
SELLBOT_FIELD_OFFICE = 103
SELLBOT_INVASION_MOVER_AND_SHAKER = 104
IDES_OF_MARCH = 105
EXPANDED_CLOSETS = 106
TAX_DAY_INVASION = 107
KARTING_TICKETS_HOLIDAY = 109
PRE_JULY_4_DOWNSIZER_INVASION = 110
PRE_JULY_4_BIGWIG_INVASION = 111
COMBO_FIREWORKS = 112
JELLYBEAN_TROLLEY_HOLIDAY_MONTH = 113
JELLYBEAN_FISHING_HOLIDAY_MONTH = 114
JELLYBEAN_PARTIES_HOLIDAY_MONTH = 115
SILLYMETER_EXT_HOLIDAY = 116
SPOOKY_BLACK_CAT = 117
SPOOKY_TRICK_OR_TREAT = 118
SPOOKY_PROPS = 119
SPOOKY_COSTUMES = 120
WACKY_WINTER_DECORATIONS = 121
WACKY_WINTER_CAROLING = 122
SILLY_SATURDAY = 123    # the main controller
MEGAINVASION_IDES_OF_MARCH = 124
MEGAINVASION_TAX_DAY = 125
MEGAINVASION_MEMORIAL_DAY = 126
MEGAINVASION_HALLOWEEN = 127
APRIL_FOOLS = 128
FISH_POKER = 129
TOT_REWARD_JELLYBEAN_AMOUNT = 100
TOT_REWARD_END_OFFSET_AMOUNT = 0
LawbotBossMaxDamage = 2700
LawbotBossMaxDamageNerfs = 1350
LawbotBossWinningTilt = 40
LawbotBossInitialDamage = 1350
LawbotBossInitialDamageNerfs = 675
LawbotBossStartPosHpr = (-3.00, 140, 21, 0, 0, 0)
LawbotBossBattleOnePosHpr = (-3.00, 15, 0, 0, 0, 0)
LawbotBossBattleTwoPosHpr = (-2.798, 89, 19.145, 0, 0, 0)
LawbotBossTopRampPosA = (-80, -35, 18)
LawbotBossTopRampTurnPosA = (-80, 10, 18)
LawbotBossP3PosA = (55, -9, 0)
LawbotBossTopRampPosB = (80, -35, 18)
LawbotBossTopRampTurnPosB = (80, 10, 18)
LawbotBossP3PosB = (55, -9, 0)
LawbotBossBattleThreePosHpr = LawbotBossBattleTwoPosHpr
LawbotBossBottomPos = (50, 39, 0)
LawbotBossDeathPos = (50, 40, 0)
LawbotBossGavelPosHprs = [(35, 78.328, 0, -135, 0, 0),
                          (68.5, 78.328, 0, 135, 0, 0),
                          (47, -33, 0, 45, 0, 0),
                          (-50, -39, 0, -45, 0, 0),
                          (-9, -37, 0, 0, 0, 0),
                          (-9, 49, 0, -180, 0, 0),
                          (32, 0, 0, 45, 0, 0),
                          (33, 56, 0, 135, 0, 0)]
LawbotBossGavelTimes = [(0.2, 0.9, 0.6),
                        (0.25, 1, 0.5),
                        (1.0, 6, 0.5),
                        (0.3, 3, 1),
                        (0.26, 0.9, 0.45),
                        (0.24, 1.1, 0.65),
                        (0.27, 1.2, 0.45),
                        (0.25, 0.95, 0.5)]
LawbotBossGavelHeadings = [(0, -15, 4, -70 - 45, 5, 45),
                           (0, -45, -4, -35, -45, -16, 32),
                           (0, -8, 19, -7, 5, 23),
                           (0, -4, 8, -16, 32, -45, 7, 7, -30, 19, -13, 25),
                           (0, -45, -90, 45, 90),
                           (0, -45, -90, 45, 90),
                           (0, -45, 45),
                           (0, -45, 45)]
LawbotBossCogRelBattleAPosHpr = (-25, -10, 0, 0, 0, 0)
LawbotBossCogRelBattleBPosHpr = (-25, 10, 0, 0, 0, 0)
LawbotBossCogAbsBattleAPosHpr = (-5, -2, 0, 0, 0, 0)
LawbotBossCogAbsBattleBPosHpr = (-5, 0, 0, 0, 0, 0)
LawbotBossWitnessStandPosHpr = (54, 100, 0, -90, 0, 0)
LawbotBossInjusticePosHpr = (-3, 12, 0, 90, 0, 0)
LawbotBossInjusticeScale = (1.75, 1.75, 1.5)
LawbotBossDefensePanDamage = 1
LawbotBossLawyerPosHprs = [(-57, -24, 0, -90, 0, 0),
                           (-57, -12, 0, -90, 0, 0),
                           (-57, 0, 0, -90, 0, 0),
                           (-57, 12, 0, -90, 0, 0),
                           (-57, 24, 0, -90, 0, 0),
                           (-57, 36, 0, -90, 0, 0),
                           (-57, 48, 0, -90, 0, 0),
                           (-57, 60, 0, -90, 0, 0),
                           (-3, -37.3, 0,  0, 0, 0),
                           (-3, 53, 0, -180, 0, 0),
                           (45, -24, 0, 90, 0, 0),
                           (45, -12, 0, 90, 0, 0),
                           (45, 0, 0, 90, 0, 0),
                           (45, 12, 0, 90, 0, 0),
                           (45, 24, 0, 90, 0, 0),
                           (45, 36, 0, 90, 0, 0),
                           (45, 48, 0, 90, 0, 0),
                           (45, 60, 0, 90, 0, 0)]
LawbotBossLawyerCycleTime = 6
LawbotBossLawyerToPanTime = 2.5
LawbotBossLawyerChanceToAttack = 50
LawbotBossLawyerHeal = 2
LawbotBossLawyerStunTime = 5
LawbotBossDifficultySettings = [(38, 4, 8, 1, 0, 0),
                                (36, 5, 8, 1, 0, 0),
                                (34, 5, 8, 1, 0, 0),
                                (32, 6, 8, 2, 0, 0),
                                (30, 6, 8, 2, 0, 0),
                                (28, 7, 8, 3, 0, 0),
                                (26, 7, 9, 3, 1, 1),
                                (24, 8, 9, 4, 1, 1),
                                (22, 8, 10, 4, 1, 0),
                                (20, 8, 18, 2, 1, 0)]
LawbotBossDifficultySettingsNerfs = [(38, 4, 4, 1, 0, 0),
                                     (36, 5, 4, 1, 0, 0),
                                     (34, 5, 4, 1, 0, 0),
                                     (32, 6, 4, 2, 0, 0),
                                     (30, 6, 5, 2, 0, 0),
                                     (28, 7, 6, 3, 0, 0),
                                     (26, 7, 7, 3, 1, 1),
                                     (24, 8, 8, 4, 1, 1),
                                     (22, 8, 8, 4, 1, 0),
                                     (20, 8, 18, 2, 1, 0)]
LawbotBossCannonPosHprs = [(-40, -12, 0, -90, 0, 0),
                           (-40, 0, 0, -90, 0, 0),
                           (-40, 12, 0, -90, 0, 0),
                           (-40, 24, 0, -90, 0, 0),
                           (-40, 36, 0, -90, 0, 0),
                           (-40, 48, 0, -90, 0, 0),
                           (-40, 60, 0, -90, 0, 0),
                           (-40, 72, 0, -90, 0, 0)]
LawbotBossCannonPosA = (-80, -51.48, 0)
LawbotBossCannonPosB = (-80, 70.73, 0)
LawbotBossChairPosHprs = [(60, 72, 0, -90, 0, 0),
                          (60, 62, 0, -90, 0, 0),
                          (60, 52, 0, -90, 0, 0),
                          (60, 42, 0, -90, 0, 0),
                          (60, 32, 0, -90, 0, 0),
                          (60, 22, 0, -90, 0, 0),
                          (70, 72, 5, -90, 0, 0),
                          (70, 62, 5, -90, 0, 0),
                          (70, 52, 5, -90, 0, 0),
                          (70, 42, 5, -90, 0, 0),
                          (70, 32, 5, -90, 0, 0),
                          (70, 22, 5, -90, 0, 0)]
LawbotBossChairRow1PosB = (59.3, 48, 14.05)
LawbotBossChairRow1PosA = (59.3, -18.2, 14.05)
LawbotBossChairRow2PosB = (75.1, 48, 28.2)
LawbotBossChairRow2PosA = (75.1, -18.2, 28.2)
LawbotBossCannonBallMax = 12
LawbotBossCannonBallMaxNerfs = 24
LawbotBossJuryBoxStartPos = (94, -8, 5)
LawbotBossJuryBoxRelativeEndPos = (30, 0, 12.645)
LawbotBossJuryBoxMoveTime = 70
LawbotBossJuryBoxMoveTimeHardcore = 30
LawbotBossJuryBoxMoveTimeNerfs = 90
LawbotBossJurorsForBalancedScale = 8
LawbotBossDamagePerJuror = 68
LawbotBossCogJurorFlightTime = 10
LawbotBossCogJurorDistance = 75
LawbotBossBaseJurorNpcId = 2001
LawbotBossWitnessEpiloguePosHpr = (-3,
 0,
 0,
 180,
 0,
 0)
LawbotBossChanceForTaunt = 25
LawbotBossBonusWaitTime = 60
LawbotBossBonusDuration = 20
LawbotBossBonusToonup = 10
LawbotBossBonusWeightMultiplier = 2
LawbotBossChanceToDoAreaAttack = 11
LawbotBossChanceToDoAreaAttackHardcore = 25
POP_LIMIT_MIN = 1
DEFAULT_POP_LIMIT = 16
POP_LIMIT = 128
PinballCannonBumper = 0
PinballCloudBumperLow = 1
PinballCloudBumperMed = 2
PinballCloudBumperHigh = 3
PinballTarget = 4
PinballRoof = 5
PinballHouse = 6
PinballFence = 7
PinballBridge = 8
PinballStatuary = 9
PinballScoring = [(100, 1),
 (150, 1),
 (200, 1),
 (250, 1),
 (350, 1),
 (100, 1),
 (50, 1),
 (25, 1),
 (100, 1),
 (10, 1)]
PinballCannonBumperInitialPos = (0, -20, 40)
RentalCop = 0
RentalCannon = 1
RentalGameTable = 2
ColorPlayer = (0.3, 0.7, 0.3, 1)
ColorAvatar = (0.3, 0.3, 0.7, 1)
ColorPet = (0.6, 0.4, 0.2, 1)
ColorFreeChat = (0.3, 0.3, 0.8, 1)
ColorSpeedChat = (0.2, 0.6, 0.4, 1)
ColorNoChat = (0.8, 0.5, 0.1, 1)
ColorOnlineFriend = (0.3, 0.5, 0.8, 1.0)
ColorOfflineFriend = (0.6, 0.7, 0.9, 0.9)
FactoryLaffMinimums = [(0, 0),
 (0, 0, 0),
 (0, 0, 0, 0),
 (0, 0, 0)]

# CEO Battle stuff
BossbotRTIntroStartPosHpr = (0, -64, 0, 180, 0, 0)
BossbotRTPreTwoPosHpr = (0, -20, 0, 180, 0, 0)
BossbotRTEpiloguePosHpr = ( 0, 90, 0, 180, 0, 0)
BossbotBossBattleOnePosHpr = (0, 355, 0, 0, 0, 0)
BossbotBossPreTwoPosHpr = (0, 20, 0, 0, 0, 0)
BossbotElevCamPosHpr  = (0,  -100.544,  7.18258, 0, 0, 0)
BossbotFoodModelScale = 0.75 # do we scale up or down from the cog food model
BossbotNumFoodToExplode = 3
BossbotBossServingDuration = 300
BossbotPrepareBattleThreeDuration = 20
# relative to bosscog coordinates for waiter battles
WaiterBattleAPosHpr = (20, -400, 0, 0, 0, 0)
WaiterBattleBPosHpr = (-20, -400, 0, 0, 0, 0)
BossbotBossBattleThreePosHpr = (0, 355, 0, 0, 0, 0)
DinerBattleAPosHpr = (20, -240, 0, 0, 0, 0)
DinerBattleBPosHpr = (-20, -240, 0, 0, 0, 0)
BossbotBossMaxDamage = 500
BossbotBossMaxDamageHardcore = 600
BossbotBossMaxDamageNerfs = 100
BossbotMaxSpeedDamage = 90
# in speed damage recovered per MINUTE
BossbotSpeedRecoverRate = 20
BossbotBossSpeedDamage = 10
BossbotBossSpeedDamageHardcore = 5
# num tables, diners per table, level of diners, table unflatten time, hungry duration, eating duration
BossbotBossDifficultySettings = [(8, 4, 11, 3,   30, 25),
                                 (9, 5, 12, 6,   28, 26),
                                 (10, 6, 11, 7,  26, 27),
                                 (8, 8, 12, 8, 24, 28),
                                 (13, 5, 12, 9, 22, 29),
                                 (13, 8, 12, 10, 20, 30)]
BossbotBossDifficultySettingsNerfs = [(2, 3, 8, 3,   60, 10),
                                      (3, 4, 9, 6,   56, 11),
                                      (3, 4, 8, 7,  52, 12),
                                      (2, 7, 9, 8, 48, 13),
                                      (4, 4, 10, 9, 44, 14),
                                      (13, 8, 12, 10, 20, 30)]
BossbotRollSpeedMax = 22
BossbotRollSpeedMin = 7.5
BossbotTurnSpeedMax = 60
BossbotTurnSpeedMin = 20
BossbotTreadSpeedMax = 10.5
BossbotTreadSpeedMin = 3.5

BossbotRollSpeedMaxHardcore = 32.5
BossbotRollSpeedMinHardcore = 17.5
BossbotTurnSpeedMaxHardcore = 85
BossbotTurnSpeedMinHardcore = 45
BossbotTreadSpeedMaxHardcore = 13.5
BossbotTreadSpeedMinHardcore = 6.0

BossbotBossFoodCanDamage = 10

CalendarFilterShowAll = 0
CalendarFilterShowOnlyHolidays = 1
CalendarFilterShowOnlyParties = 2
TTC = 1
DD = 2
MM = 3
GS = 4
DG = 5
BR = 6
OZ = 7
DL = 8
DefaultWantNewsPageSetting = 1
gmMagicWordList = ['restock',
 'restockUber',
 'autoRestock',
 'resistanceRestock',
 'restockSummons',
 'uberDrop',
 'rich',
 'maxBankMoney',
 'toonUp',
 'rod',
 'cogPageFull',
 'pinkSlips',
 'Tickets',
 'newSummons',
 'who',
 'who all']
NewsPageScaleAdjust = 0.85


class AnimPropTypes(enum.IntEnum):
    Unknown = -1
    Hydrant = 0
    Mailbox = 1
    Trashcan = 2


class EmblemTypes(enum.IntEnum):
    Silver = 0
    Gold = 1


NumEmblemTypes = 2
DefaultMaxBankMoney = 12000
MaxJarMoney = 9999
DefaultBankItemId = 1350
ToonAnimStates = ('off', 'neutral', 'victory', 'Happy', 'Sad', 'Catching', 'CatchEating', 'Sleep', 'walk', 'jumpSquat',
                  'jump', 'jumpAirborne', 'jumpLand', 'run', 'swim', 'swimhold', 'dive', 'cringe', 'OpenBook',
                  'ReadBook', 'CloseBook', 'TeleportOut', 'Died', 'TeleportedOut', 'TeleportIn', 'Emote', 'SitStart',
                  'Sit', 'Push', 'Squish', 'FallDown', 'GolfPuttLoop', 'GolfRotateLeft', 'GolfRotateRight',
                  'GolfPuttSwing', 'GolfGoodPutt', 'GolfBadPutt', 'Flattened', 'CogThiefRunning', 'ScientistJealous',
                  'ScientistEmcee', 'ScientistWork', 'ScientistLessWork', 'ScientistPlay', 'PortalOut', 'PortaledOut',
                  'PortalIn')
AV_FLAG_REASON_TOUCH = 1
AV_FLAG_HISTORY_LEN = 500
AV_TOUCH_CHECK_DELAY_AI = 3.0
AV_TOUCH_CHECK_DELAY_CL = 1.0
AV_TOUCH_CHECK_DIST = 2.0
AV_TOUCH_CHECK_DIST_Z = 5.0
AV_TOUCH_CHECK_TIMELIMIT_CL = 0.002
AV_TOUCH_COUNT_LIMIT = 5
AV_TOUCH_COUNT_TIME = 300
EasterEggPhraseLifetime = 120
EasterEggPhraseThreshold = 100
# another todo: redo this garbage tuple madness that ben loved
hood2Id = [(ToontownCentral, ('toontowncentral', 'central', 'ttc', 'tt', '2000')),
           (DonaldsDock, ('donaldsdock', 'dock', 'dd', 'dod', '1000')),
           (DaisyGardens, ('daisygardens', 'gardens', 'dg', 'dga', '5000')),
           (MinniesMelodyland, ('minniesmelodyland', 'melodyland', 'mml', 'mm', '4000')),
           (TheBrrrgh, ('thebrrrgh', 'brrrgh', 'tb', 'br', 'tbr', '3000')),
           (DonaldsDreamland, ('donaldsdreamland', 'dreamland', 'ddl', 'dl', '9000')),
           (DreamyDriveOutcove, ('dreamydrive', 'drdr', '9300')),
           (GoofySpeedway, ('goofyspeedway', 'speedway', 'goofystadium', 'goofycolosseum', 'colosseum', 'gs', 'gsw', '8000')),
           (OutdoorZone, ('outdoorzone', 'outdoor', 'outdoors', 'acornacres', 'acres', 'oz', 'aa', 'cda', '6000')),
           (GolfZone, ('golfzone', 'golf', 'minigolf', 'gz', 'mg', 'cmg', '17000')),
           (SellbotHQ, ('sellbothq', 'sbhq', 'vp', '11000')),
           (SellbotFactoryExt, ('factory', 'long', 'side', '11200')),
           (CashbotHQ, ('cashbothq', 'cbhq', 'cfo', 'mint', 'coin', 'dollar', 'bullion', '12000')),
           (LawbotHQ, ('lawbothq', 'lbhq', 'cj', '13000')),
           (LawbotOfficeExt, ('daoffice', 'office', 'da', 'office', 'officea', 'officeb', 'officec', 'officed', '13200')),
           (BossbotHQ, ('bossbothq', 'bbhq', 'ceo', 'front', 'middle', 'back', '10000')),
           (MyEstate, ('estate', 'home', 'house', '16000')),
           (ToontownSkies, ('tsk', 'skies', 'sky', 'plainsarea', 'theplains', 'plains', 'p', 'fieldsarea', 'thefields', 'toontownfields', 'ttf', 'f', '30000')),
           #(ToontownOutskirts, ('toontownoutskirts', 'outskirts', 'tto', 'sp', '19000')),
           (TutorialTerrace, ('tutorialterrace', 'tutorial', 'toontorial', 'tut', '19100')),
           (HiddenCamp, ('hiddencamp', 'camp', 'campsite', 'hc', 'cs', '6100')),
           (GyrosLab, ('gyroslab', 'gl', 'lab', '22634')),
           (SellbotHQFuture, ('sellbothqfuture', 'sbhqfuture', 'sbhqf', 'sbf', 'hqfuture', 'sbfuture', '19200')),
           #(CogtownCentral, ('cogtowncentral', 'cogtown', 'ctc', 'ttctakeover', 'cogcentral', 'cogttc', '19300')),
           (ToontownCentralBeta, ('toontowncentralbeta', 'centralbeta', 'ttcbeta', 'ttcb', 'ttbeta', 'ttb', '21000')),
           (DonaldsDockBeta, ('donaldsdockbeta', 'dockbeta', 'ddbeta', 'ddb', '26000')),
           (DaisyGardensBeta, ('daisygardensbeta', 'gardensbeta', 'dgbeta', 'dgb', '22000')),
           (MinniesMelodylandBeta, ('minniesmelodylandbeta', 'melodylandbeta', 'mmlbeta', 'mmlb', 'mlbeta', 'mlb', '23000')),
           (TheBrrrghBeta, ('thebrrrghbeta', 'brrrghbeta', 'tbbeta', 'tbb', 'brbeta', 'brb', '25000')),
           (DonaldsDreamlandBeta, ('donaldsdreamlandbeta', 'dreamlandbeta', 'ddlbeta', 'ddlb', 'dlbeta', 'dlb', '24000')),

           (ToonLandFunnyFarm, ('toonland', 'tl', 'tlff', 'funnyfarm', 'funnyfarms', 'ff', '31000'))
           #(CreativeFieldsA, ('plainsa', 'cfa', 'ttfa', '30100')),
           #(CreativeFieldsB, ('plainsb', 'cfb', 'ttfb', '30200')),
           #(CreativeFieldsC, ('plainsc', 'cfc', 'ttfc', '30300')),
           #(CreativeFieldsD, ('plainsd', 'cfd', 'ttfd', '30400')),

           ]
hood2Id = collections.OrderedDict(hood2Id)
hoodsForTeleport = []
for hood in list(hood2Id.values()):
    for shorthand in hood:
        hoodsForTeleport.append(shorthand)
hood2Coords = {('dreamydrive', 'drdr', '9300'): (70, 60, 0.03, 163.80, 0.0, 0.0),
               ('ceo',): (61.044, 119.014, 0.025, -4.680, 0, 0),
               ('cj',): (333.700, -179.869, -42.932, -807.174, 0, 0),
               ('cfo',): (125.155, 546.084, 32.246, 360.056, 0, 0),
               ('vp',): (25.512, -51.193, 10.095, 40.868, 0, 0),
               ('factory', '11200'): (62.204, -89.739, 0.025, -7.144, 0, 0),
               ('long',): (62.204, -89.739, 0.025, -7.144, 0, 0),
               ('side',): (-165.940, 26.804, 0.025, -97.144, 0, 0),
               ('bullion',): (-118.641, 64.131, -23.434, 449.182, 0, 0),
               ('dollar',): (178.612, -175.786, -63.244, 274.225, 0, 0),
               ('coin',): (-122.43, -428.856, -23.439, 450.141, 0, 0),
               ('daoffice', 'office', 'da', 'office', '13200'): (118.05, 60.45, 51.69, 0, 0, 0),
               ('officea',): (47.594, 78.874, 51.692, -35, 0, 0),
               ('officeb',): (94.816, 78.874, 51.692, -15, 0, 0),
               ('officec',): (137.586, 78.874, 51.692, 15, 0, 0),
               ('officed',): (178.331, 78.874, 51.692, 35, 0, 0),
               ('back',): (-42.23, 1.93, 0.03, 47.40, 0, 0),
               ('middle',): (139.25, -66.80, 0.03, 206.90, 0, 0),
               ('front',): (156.68, 20.53, 0.03, 336.70, 0, 0),
               ('tutorialterrace', 'tutorial', 'toontorial', 'tt', '19100'): (107.85, -49.32, 0.03, 40.58, 0.0, 0.0),
               ('sellbothqfuture', 'sbhqfuture', 'sbhqf', 'sbf', 'hqfuture', 'sbfuture', '19200'): (28, -385, 101.408, -448, 0, 0),
               ('cogtowncentral', 'cogtown', 'ctc', 'ttctakeover', 'cogcentral', 'cogttc', '19300'): (40.6708, 0.482345, 3.98244, 90.0, 0.0, 0.0),
               ('hiddencamp', 'camp', 'campsite', 'hc', 'cs', '6100'): (27.46, 164.46, 3.42, 164.38, 0.0, 0.0),
               ('gyroslab', 'gl', 'lab', '22634'): (-38.01, -19.48, 0.03, 287.54, 0.0, 0.0),
               ('tlff', 'funnyfarm', 'toonland', 'tl'): (4.65, -12.12, 10.03, 276.07, 0.00, 0.00),
               ('tsk', 'skies', 'sky', 'plainsarea', 'theplains', 'plains', 'p', 'fieldsarea', 'thefields', 'CreativeFields', 'ttf', 'f',
                '30000'): (0.0, 55.0, -0.47, 180, 0.0, 0.0)}
hoodExemptions = (DreamyDriveOutcove, SellbotHQFuture, ToontownSkies,
                  CreativeFieldsA, CreativeFieldsB,
                  CreativeFieldsC, CreativeFieldsD,
                  ToonLandFunnyFarm, MyEstate, 9401)
hoodDescriptions = {HiddenCamp: "Come hang out with your Doodle here! This little campfire site serves as a place to chill, relax, play games, and sing a song. Just don't touch the fire!",
                    ToontownOutskirts: "The gap between the Toontorial and the rest of Toontown Central. Stop by for a visit and pay homage to Toontown's history!",
                    TutorialTerrace: 'Come back to the Toontorial for a visit! Be warned, you may encounter a few low level Cogs on the way.',
                    ToontownSkies: "What could be here??",
                    GyrosLab: "Ah, the glorious days of Toontown. Experience one of Gyro's Laboratories, and check out what Oak Street looked like before the Cogs invaded.",
                    CogtownCentral: "An imagination of what Toontown Central could look like if taken over by the Cogs. Don't worry, it's just that- imagination.",
                    ToontownCentralBeta: "Travel back to the past, and visit the round capital of Toontown before Mickey redesigned it.",
                    DonaldsDockBeta: "Travel back to the past, and attempt to move around the Dock before Donald made it more accessible.",
                    DaisyGardensBeta: "Travel back to the past, and meet a version of Goofy who grew the flowers back then.",
                    MinniesMelodylandBeta: "Travel back to the past, and experience the Merry-Go-Round before it malfunctioned.",
                    TheBrrrghBeta: "Travel back to the past, and see the igloo before it was converted to a Toon Headquarters.",
                    DonaldsDreamlandBeta: "Travel back to the past, and watch the construction of Pajama Place take place!",
                    ToonLandFunnyFarm: 'Experience the iconic "Hackland" from Toontown Online.'
                    }
MaxCogLevel = 100
MoleHillPositions = [(136.542, 98.415, -1.212),
                     (121.312, 8.031, -0.904),
                     (104.776, -36.965, -0.904),
                     (80.159, -64.127, -0.904),
                     (7.309, -15.040, -0.433),
                     (29.393, 30.864, -1.025),
                     (-84.014, -89.770, 10.586),
                     (220.143, -6.165, -1.792)]  # This is in the BBHQ tunnel, remove if required.
KongdominiumSongs = {'One Day, Everything Will Be Okay': 'phase_14.5/audio/bgm/KDM_theme_3.ogg',
                     'Mayday': 'phase_14.5/audio/bgm/KDM_theme_5.ogg',
                     'I Wrote You a Chiptune': 'phase_14.5/audio/bgm/KDM_theme_2.ogg',
                     'How to Win a World War, Somewhere': 'phase_14.5/audio/bgm/KDM_theme_1.ogg',
                     'It\'s Love': 'phase_14.5/audio/bgm/KDM_theme_4.ogg'}
Phrase2Location = {1131: ToontownOutskirts,
                   1004: ToontownOutskirts,
                   1105: ToontownCentralBeta,
                   1106: DonaldsDockBeta,
                   1107: MinniesMelodylandBeta,
                   1108: DaisyGardensBeta,
                   1109: TheBrrrghBeta,
                   1110: DonaldsDreamlandBeta}
Location2Hood = {SellbotFactoryExt: SellbotHQ,
                 LawbotOfficeExt: LawbotHQ}
MeetHereNpcIds = [7100,  # Crazy Clover
                  7101,  # Crazy Clyde
                  7102,  # Crazy Cuddles
                  7103,  # Crazy Curly
                  7104,  # Crazy Comet
                  7105,  # Crazy Coconut
                  7106,  # Crazy Chester
                  7107]  # Crazy Cecil
ResistanceRangersNpcIds = [7200,  #Resistance Ranger Randolph
                           7201,  #Resistance Ranger Reg
                           7202,  #Resistance Ranger Ruth
                           7203,  #Resistance Ranger Rocky
                           7204,  #Resistance Ranger Ridley
                           7205,  #Resistance Ranger Roy
                           7206,  #Resistance Ranger Ralph
                           7207,  #Resistance Ranger Ripley
                           7208,  #Resistance Ranger Randy
                           7209,  #Resistance Ranger Rupert
                           7210,  #Resistance Ranger Rusty
                           7211,  #Resistance Ranger Ruby
                           7212]  #Resistance Ranger Raven

# Text-to-speech related information
TextToSpeechLink = 'http://sourceforge.net/projects/espeak/files/latest/download'
Species2Voice = {'dog': 'Alex',
                 'cat': 'Samantha',
                 'horse': 'Daniel',
                 'mouse': 'Junior',
                 'rabbit': 'Princess',
                 'duck': 'Fred',
                 'monkey': 'Deranged',
                 'bear': 'Bruce',
                 'pig': 'Albert'
}
Species2Pitch = {'dog': 50,
                 'cat': 80,
                 'horse': 30,
                 'mouse': 99,
                 'rabbit': 95,
                 'duck': 35,
                 'monkey': 85,
                 'bear': 20,
                 'pig': 25}
DefaultVoice = 'Alex'
DefaultVoiceSuit = 'Thomas'
DefaultVoiceCogBoss = 'Albert'
DefaultVoiceChairman = 'Ralph'
DefaultVoiceClassicChar = 'Princess'
VoiceFemalePet = 'Samantha'
DefaultPitch = 50
FemalePetPitch = 80


def getPath(phase, model):
    return f'phase_{phase}/models/props/{model}'

Props = ((5, 'partyBall', 'partyBall'),
 (5,
  'feather',
  'feather-mod',
  'feather-chan'),
 (5, 'lips', 'lips'),
 (5, 'lipstick', 'lipstick'),
 (5, 'hat', 'hat'),
 (5, 'cane', 'cane'),
 (5,
  'cubes',
  'cubes-mod',
  'cubes-chan'),
 (5, 'ladder', 'ladder2'),
 (4,
  'fishing-pole',
  'fishing-pole-mod',
  'fishing-pole-chan'),
 (5,
  '1dollar',
  '1dollar-bill-mod',
  '1dollar-bill-chan'),
 (5, 'big-magnet', 'magnet'),
 (5,
  'hypno-goggles',
  'hypnotize-mod',
  'hypnotize-chan'),
 (5, 'slideshow', 'av_screen'),
 (5,
  'banana',
  'banana-peel-mod',
  'banana-peel-chan'),
 (5,
  'rake',
  'rake-mod',
  'rake-chan'),
 (5,
  'marbles',
  'marbles-mod',
  'marbles-chan'),
 (5,
  'tnt',
  'tnt-mod',
  'tnt-chan'),
 (5, 'trapdoor', 'trapdoor'),
 (5, 'quicksand', 'quicksand'),
 (5, 'traintrack', 'traintrack2'),
 (5, 'train', 'train'),
 (5, 'megaphone', 'megaphone'),
 (5, 'aoogah', 'aoogah'),
 (5, 'bikehorn', 'bikehorn'),
 (5, 'bugle', 'bugle'),
 (5, 'elephant', 'elephant'),
 (5, 'fog_horn', 'fog_horn'),
 (5, 'whistle', 'whistle'),
 (5, 'singing', 'singing'),
 (3.5, 'creampie', 'tart'),
 (5, 'fruitpie-slice', 'fruit-pie-slice'),
 (5, 'creampie-slice', 'cream-pie-slice'),
 (5,
  'birthday-cake',
  'birthday-cake-mod',
  'birthday-cake-chan'),
 (5, 'wedding-cake', 'wedding_cake'),
 (3.5, 'squirting-flower', 'squirting-flower'),
 (5,
  'glass',
  'glass-mod',
  'glass-chan'),
 (4, 'water-gun', 'water-gun'),
 (3.5, 'bottle', 'bottle'),
 (5,
  'firehose',
  'firehose-mod',
  'firehose-chan'),
 (5, 'hydrant', 'battle_hydrant'),
 (4,
  'stormcloud',
  'stormcloud-mod',
  'stormcloud-chan'),
 (5, 'geyser', 'geyser'),
 (3.5, 'button', 'button'),
 (5,
  'flowerpot',
  'flowerpot-mod',
  'flowerpot-chan'),
 (5,
  'sandbag',
  'sandbag-mod',
  'sandbag-chan'),
 (4,
  'anvil',
  'anvil-mod',
  'anvil-chan'),
 (5,
  'weight',
  'weight-mod',
  'weight-chan'),
 (5,
  'safe',
  'safe-mod',
  'safe-chan'),
 (5,
  'piano',
  'piano-mod',
  'piano-chan'),
 (5,
  'rake-react',
  'rake-step-mod',
  'rake-step-chan'),
 (5, 'pad', 'pad'),
 (4,
  'propeller',
  'propeller-mod',
  'propeller-chan'),
 (5,
  'calculator',
  'calculator-mod',
  'calculator-chan'),
 (5, 'rollodex', 'roll-o-dex'),
 (5, 'rubber-stamp', 'rubber-stamp'),
 (5,
  'rubber-stamp-pad',
  'rubber-stamp-pad-mod',
  'rubber-stamp-pad-chan'),
 (5,
  'smile',
  'smile-mod',
  'smile-chan'),
 (5, 'golf-club', 'golf-club'),
 (5, 'golf-ball', 'golf-ball'),
 (5, 'redtape', 'redtape'),
 (5, 'redtape-tube', 'redtape-tube'),
 (5, 'bounced-check', 'bounced-check'),
 (5,
  'calculator',
  'calculator-mod',
  'calculator-chan'),
 (3.5,
  'clip-on-tie',
  'clip-on-tie-mod',
  'clip-on-tie-chan'),
 (5, 'pen', 'pen'),
 (5, 'pencil', 'pencil'),
 (3.5, 'phone', 'phone'),
 (3.5, 'receiver', 'receiver'),
 (5, 'sharpener', 'sharpener'),
 (3.5, 'shredder', 'shredder'),
 (3.5,
  'shredder-paper',
  'shredder-paper-mod',
  'shredder-paper-chan'),
 (5, 'watercooler', 'watercooler'),
 (5, 'dagger', 'dagger'),
 (5, 'card', 'card'),
 (5, 'baseball', 'baseball'),
 (5, 'bird', 'bird'),
 (5, 'can', 'can'),
 (5, 'cigar', 'cigar'),
 (5, 'evil-eye', 'evil-eye'),
 (5, 'evil-glare', 'ttrm_m_ene_prp_evilGlare'),
 (5, 'gavel', 'gavel'),
 (5, 'half-windsor', 'half-windsor'),
 (5, 'lawbook', 'lawbook'),
 (5, 'newspaper', 'newspaper'),
 (5, 'pink-slip', 'pink-slip'),
 (5,
  'teeth',
  'teeth-mod',
  'teeth-chan'),
 (5, 'power-tie', 'power-tie'),
 (3.5, 'spray', 'spray'),
 (3.5,
  'splat',
  'splat-mod',
  'splat-chan'),
 (3.5,
  'stun',
  'stun-mod',
  'stun-chan'),
 (3.5, 'glow', 'glow'),
 (3.5,
  'suit_explosion',
  'suit_explosion-mod',
  'suit_explosion-chan'),
 (3.5, 'suit_explosion_dust', 'dust_cloud'),
 (4, 'ripples', 'ripples'),
 (4, 'wake', 'wake'),
 (4,
  'splashdown',
  'SZ_splashdown-mod',
  'SZ_splashdown-chan'),
 (14.5, 'snowball', 'snowball'))
PropsBattle = [('tart', 'model', (getPath(3.5, 'tart'),)),
               ('fruitpie', 'model', (getPath(3.5, 'tart'),)),
               ('double-windsor', 'model', (getPath(5, 'half-windsor'),)),
               ('splat-tart', 'actor', (getPath(3.5, 'splat-mod'), getPath(3.5, 'splat-chan'))),
               ('splat-fruitpie-slice', 'actor', (getPath(3.5, 'splat-mod'), getPath(3.5, 'splat-chan'))),
               ('splat-creampie-slice', 'actor', (getPath(3.5, 'splat-mod'), getPath(3.5, 'splat-chan'))),
               ('splat-fruitpie', 'actor', (getPath(3.5, 'splat-mod'), getPath(3.5, 'splat-chan'))),
               ('splat-creampie', 'actor', (getPath(3.5, 'splat-mod'), getPath(3.5, 'splat-chan'))),
               ('splat-birthday-cake', 'actor', (getPath(3.5, 'splat-mod'), getPath(3.5, 'splat-chan'))),
               ('splat-wedding-cake', 'actor', (getPath(3.5, 'splat-mod'), getPath(3.5, 'splat-chan'))),
               ('splat-snowball', 'actor', (getPath(3.5, 'splat-mod'), getPath(3.5, 'splat-chan'))),
               ('splash-from-splat', 'actor', (getPath(3.5, 'splat-mod'), getPath(3.5, 'splat-chan'))),
               ('small-magnet', 'model', (getPath(5, 'magnet'),)),
               ('5dollar', 'actor', (getPath(5, '1dollar-bill-mod'), getPath(5, '1dollar-bill-chan'))),
               ('10dollar', 'actor', (getPath(5, '1dollar-bill-mod'), getPath(5, '1dollar-bill-chan'))),
               ('dust', 'actor', (getPath(5, 'dust-mod'), getPath(5, 'dust-chan'))),
               ('kapow', 'actor', (getPath(5, 'kapow-mod'), getPath(5, 'kapow-chan'))),
               ('ship', 'model', (getPath(5, 'ship'),))]
CreampieColor = VBase4(250.0 / 255.0, 241.0 / 255.0, 24.0 / 255.0, 1.0)
FruitpieColor = VBase4(55.0 / 255.0, 40.0 / 255.0, 148.0 / 255.0, 1.0)
BirthdayCakeColor = VBase4(253.0 / 255.0, 119.0 / 255.0, 220.0 / 255.0, 1.0)
SnowballColor = VBase4(255.0 / 255.0, 255.0 / 255.0, 255.0 / 255.0, 1.0)
Splats = {'tart': (0.3, FruitpieColor),
          'fruitpie-slice': (0.5, FruitpieColor),
          'creampie-slice': (0.5, CreampieColor),
          'fruitpie': (0.7, FruitpieColor),
          'creampie': (0.7, CreampieColor),
          'birthday-cake': (0.9, BirthdayCakeColor),
          'wedding-cake': (1, BirthdayCakeColor),
          'snowball': (0.4, SnowballColor)}

GreenEffectMassFlyPositions = [(-4, 0), (-4, -4), (-4, 4), (0, -4), (0, 4), (4, 4), (4, -4), (4, 0)]
GreenEffectMassFlyCogs = [('cc', 'tm', 'nd', 'gh', 'ms', 'tf', 'm', 'mh'),
                          ('sc', 'pp', 'tw', 'bc', 'nc', 'mb', 'ls', 'rb'),
                          ('bf', 'b', 'dt', 'ac', 'bs', 'sd', 'le', 'bw'),
                          ('f', 'p', 'ym', 'mm', 'ds', 'hh', 'cr', 'tbc')]
PutOnSuitToonHead = [0, 3, 9]
PutOnSuitCogs = [1, 2, 4, 5, 8, 10]
PutOnSuitSkeleRevive = [2, 5]
PutOnSuitWaiter = [3, 4, 5]
PutOnSuitSkelecog = [6, 7]
PutOnSuitVirtual = [7, 8]
PutOnSuitRental = [9, 10]
NPCTailorCost = 1000
DefaultIcon = 'ttoff'
Zone2String = {
    ToontownCentral: 'ttc',
    DonaldsDock: 'dd',
    DaisyGardens: 'dg',
    MinniesMelodyland: 'mml',
    TheBrrrgh: 'tb',
    DonaldsDreamland: 'ddl',
    GoofySpeedway: 'gs',
    OutdoorZone: 'oz',
    GolfZone: 'gz',
    SellbotHQ: 'sbhq',
    SellbotFactoryExt: 'sbhq-f',
    CashbotHQ: 'cbhq',
    LawbotHQ: 'lbhq',
    LawbotOfficeExt: 'lbhq-o',
    BossbotHQ: 'bbhq',
    ToontownOutskirts: 'ttc-sz',
    MyEstate: 'estate',
    Tutorial: 'ttc',
    ToontownCentralBeta: 'ttcb',
    DaisyGardensBeta: 'dg-b',
    MinniesMelodylandBeta: 'mml-b',
    DonaldsDreamlandBeta: 'ddl-b',
    TheBrrrghBeta: 'tb-b',
    DonaldsDockBeta: 'dd-b'
}
Dept2Zone = {
 's': 11000,
 'm': 12000,
 'l': 13000,
 'c': 10000
}
Dept2Dept = {
    's': 'Sellbot',
    'm': 'Cashbot',
    'l': 'Lawbot',
    'c': 'Bossbot'
}
Dept2NameDept = {
    'Sellbot': 's',
    'Cashbot': 'm',
    'Lawbot': 'l',
    'Bossbot': 'c'
}
CogDepts = ['c', 'l', 'm', 's']
DiscordDefaultAvatarFile = "phase_14.5/maps/discord-default.png"
TransformationToon = -1
TransformationCog = 0
TransformationClassicChar = 1
TransformationDoodle = 2
TransformationGoon = 3
TransformationProp = 4
TransformationBoss = 5
TransformationFish = 6
TransformationButterfly = 7
TransformationMisc = 8
TransformationStreet = 9
TransformationMiscStatue = 0
TransformationMiscPanda = 1
TransformationMiscChaser = 2
TransformationMiscCheese = 3
TransformationMiscMickey = 4
TransformationCharExtra = {'mickey': 3.0,
                           'vampire_mickey': 3.0,
                           'minnie': 3.0,
                           'witch_minnie': 3.0,
                           'goofy': 4.8,
                           'super_goofy': 4.8,
                           'donald': 4.5,
                           'donald-wheel': 4.5,
                           'franken_donald': 4.5,
                           'donald_old': 4.0,
                           'daisy': 4.5,
                           'sockHop_daisy': 4.5,
                           'pluto': 3.0,
                           'western_pluto': 3.0,
                           'clarabelle': 3.0,
                           'chip': 2.0,
                           'dale': 2.0,
                           'police_chip': 2.0,
                           'jailbird_dale': 2.0}
TransformationFishExtra = {0: (2.5, 3, (0, 0, 0), 0, 'swim'),
                           2: (1.0, 3, (0, 0, 0), 0, 'swim'),
                           4: (1.0, 3, (0, 0, 0), 0, 'swim'),
                           6: (1.0, 3, (0, 0, 0), 0, 'swim'),
                           8: (1.0, 2, (0, 0, -0.75), 0, 'swim'),
                           10: (3.0, 2, (0, -7, -1), 0, 'intro'),
                           12: (1.0, 3, (0, 0, 0), 0, 'swim'),
                           14: (1.0, 1, (0, 0, -1.75), 0, 'intro'),
                           16: (1.0, 3, (0, 0, 0), 0, 'swim'),
                           18: (1.0, 2, (0, 0, -2), 0, 'swim'),
                           20: (1.0, 4, (1, -10, -1), 0, 'swim'),
                           22: (1.0, 3.5, (0, 0, -2), 0, 'intro'),
                           24: (1.0, 3, (0, 0, -2), 0, 'swim'),
                           26: (1.0, 4, (0, 0, -3), 0, 'swim'),
                           28: (1.0, 2, (0, 0, -1), 0, 'swim'),
                           30: (1.0, 2, (0, 0, -0.5), 90, 'swim'),
                           32: (1.0, 3, (0, 0, 0), 0, 'intro'),
                           34: (1.0, 2, (0, 0, -1), 0, 'intro')}
TransformationMiscExtra = {TransformationMiscStatue: 9.0,
                           TransformationMiscPanda: 3.0,
                           TransformationMiscChaser: 7.0,
                           TransformationMiscCheese: 8.5,
                           TransformationMiscMickey: 3.0}
TransformationExtraScale = 0
TransformationExtraNametagHeight = 1
TransformationExtraPos = 2
TransformationExtraH = 3
TransformationExtraAnimation = 4
StreetProps2Anim = {
    'phase_5/models/char/tt_r_ara_ttc_mailbox': 'phase_5/models/char/tt_a_ara_ttc_mailbox_idle0',
    'phase_6/models/char/tt_r_ara_dod_mailbox': 'phase_6/models/char/tt_a_ara_dod_mailbox_idle0',
    'phase_8/models/char/tt_r_ara_dga_mailbox': 'phase_8/models/char/tt_a_ara_dga_mailbox_idle0',
    'phase_6/models/char/tt_r_ara_mml_mailbox': 'phase_6/models/char/tt_a_ara_mml_mailbox_idle0',
    'phase_8/models/char/tt_r_ara_tbr_mailbox': 'phase_8/models/char/tt_a_ara_tbr_mailbox_idleShiver1',
    'phase_8/models/char/tt_r_ara_ddl_mailbox': 'phase_8/models/char/tt_a_ara_ddl_mailbox_idleSleep0',
    'phase_5/models/char/tt_r_ara_ttc_hydrant': 'phase_5/models/char/tt_a_ara_ttc_hydrant_idle0',
    'phase_8/models/char/tt_r_ara_dga_hydrant': 'phase_8/models/char/tt_a_ara_dga_hydrant_idle0',
    'phase_6/models/char/tt_r_ara_mml_hydrant': 'phase_6/models/char/tt_a_ara_mml_hydrant_idle0',
    'phase_8/models/char/tt_r_ara_tbr_hydrant': 'phase_8/models/char/tt_a_ara_tbr_hydrant_idleShiver1',
    'phase_8/models/char/tt_r_ara_ddl_hydrant': 'phase_8/models/char/tt_a_ara_ddl_hydrant_idle0',
    'phase_5/models/char/tt_r_ara_ttc_trashcan': 'phase_5/models/char/tt_a_ara_ttc_trashcan_idleTake2',
    'phase_6/models/char/tt_r_ara_dod_trashcan': 'phase_6/models/char/tt_a_ara_dod_trashcan_idleBounce2',
    'phase_8/models/char/tt_r_ara_dga_trashcan': 'phase_8/models/char/tt_a_ara_dga_trashcan_idleTake2',
    'phase_6/models/char/tt_r_ara_mml_trashcan': 'phase_6/models/char/tt_a_ara_mml_trashcan_idleBounce0',
    'phase_8/models/char/tt_r_ara_tbr_trashcan': 'phase_8/models/char/tt_a_ara_tbr_trashcan_idleShiver1',
    'phase_8/models/char/tt_r_ara_ddl_trashcan': 'phase_8/models/char/tt_a_ara_ddl_trashcan_idleSleep0'
}
HalloweenPumpkinInfo = {
    ToontownCentral: (('s', 79.688, 158.123, 2.483, -15.427),
                      ('s', -128.618, -65.178, 0.484, -230.316),
                      ('s', -62.478, -22.103, -1.975, 0),
                      ('s', 140.478, -84.103, 2.525, -80),
                      ('s', 28.324, 18.202, 4.0, -60),
                      ('s', -60.928, -13.498, 1.216, 195),
                      ('s', 66.447, -29.925, 6.01, 195),
                      ('l', 10.371, -130.137, 3.025, -227),
                      ('l', 110.094, 26.642, 4.025, -55),
                      ('l', 44.119, 60.559, 4.025, 16),
                      ('l', 127.134, 57.558, 2.525, -165),
                      ('l', 17.830, 28.1354, 4.0, -15),
                      ('l', 54.338, -31.099, 6.01, 150),
                      ('l', 112.212, 10.099, 4.548, 285),
                      )
    ,
    DonaldsDock: (('l', -31.25, 100.15, 2.17, -91.91), ('s', -61.68, 149.45, 3.28, 62.85),
                  ('l', -118.33, -49.83, 5.69, -608.73	), ('s', -21.70, 2.85, 5.76, -51.71),
                  ('l',	55.64, -69.57, 3.28, -496.25), ('s', 63.59, 49.88, 5.69, -406.36)),
    DaisyGardens: (('s', 50.15, 210.12, 10.02, -42.68), ('l', -82.82, 164.23, 10.02, 133.45),
                   ('l', -101.19, 95.29, 0.03, 151.26), ('s', -7.78, 17.99, 1.73, 180),
                   ('s', 7.37, 15.48, 1.73, 180), ('l', 100.33, 98.10, 0.03, -418.37),
                   ('l', 83.51, 160.25, 10.01, -446.70), ('s', 23.21, 105.92, 5.08, -1429.56)),
    MinniesMelodyland: (('l', 42.74, 76.49, 6.53, -324.55), ('s', -25.18, 76.35, 6.53, -340.22),
                        ('s', -71.93, 23.78, 6.53, -287.56), ('l', -29.57, -113.89, 6.53, -191.89),
                        ('l', 135.34, -21.20, 7.46, -91.24), ('s', 100.93, -71.97, -4.50, 270.72),
                        ('s', 83.57, -34.08, -13.48, -1.42), ('l', -58.18, 19.84, -14.49, 72.21)),
    TheBrrrgh: (('l', -36.97, -153.12, 6.19, -178.01), ('l', 35.55, -98.53, 6.19, -115.98),
                ('s', 35.03, 69.56, 6.19, 4.75), ('s', -65.32, 114.56, 6.19, 50.27),
                ('l', -128.99, 82.48, 6.19, 82.26), ('s', -88.14, 53.74, 6.19, 442.47),
                ('s', -159.25, -64.96, 6.19, 486,29), ('l', -82.00, -77.92, 3.01, 871.50)),
    DonaldsDreamland: (('s', -101.56, -102.10, 0.03, -590.41), ('l', -29.47, -96.72, 0.03, -524.91),
                       ('l', 78.62, -102.57, 0.03, -485.42), ('s', 188.57, 3.10, -15.00, -450.76),
                       ('s', -28.36, -0.76, -14.98, -628.87), ('s', 60.15, 102.78, 0.03, -713.22),
                       ('l', -88.55, 102.66, 0.03, -315.92), ('l', -83.12, 102.81, 0.03, -419.09),
                       ('l', -35.85, 101.44, 0.03, -357.40)),
    GoofySpeedway: (('l', 21.77, 72.39, 0.09, 354.50,), ('s', -20.77, 72.01, 0.09, 386.96),
                    ('l', -23.52, -47.91, 0.07, 149.76), ('s', 26.33, -44.90, 0.08, 227.99),
                    ('s', 67.41, -90.64, -0.70, 317.75), ('l', 67.40, -128.76, -0.70, 227.40),
                    ('l', 17.19, -179.96, -0.73, 587.69), ('s', -21.13, -178.65, -0.73, 482.66),
                    ('s', -68.22, -92.15, -0.71, 404.58)),
    OutdoorZone: (('l', -35.06, -135.60, 0.03, 173.00), ('s', -59.62, -135.03, 0.02, 181.19),
                  ('l', -235.85, -24.40, 0.03, 461.12), ('l', -244.38, 6.39, 0.02, 457.85),
                  ('s', 72.39, 150.47, 0.03, 671.53), ('s', 91.61, 134.48, 0.03, 663.82),
                  ('l', 24.60, 60.16, 5.92, 856.35), ('s', 19.89, 38.18, 5.92, 694.63),
                  ('l', 46.18, -126.77, 0.03, 545.35)),
    GolfZone: (('l', 134.11, 32.55, 0.03, -111.43), ('s', 128.51, 8.60, 0.03, -93.33),
               ('s', -7.29, -99.70, 0.03, -208.53), ('s', -30.13, -93.81, 0.03, -205.59),
               ('l', -103.59, -14.85, 0.03, -262.87), ('l', -109.65, 6.68, 0.03, -256.57),
               ('s', 2.99, 85.39, 0.03, -543.35)),
    ToontownOutskirts: (('s', 103.71, 111.67, 0.03, 24.47), ('s', 180.73, -47.95, 0.03, -776.64),
                        ('l', 170.27, -236.80, 0.03, -179.10), ('l', 40.92, -238.60, 0.03, -179.35),
                        ('s', 44.37, -134.82, 0.03, -629.22), ('l', -34.11, -114.01, 0.03, -236.21),
                        ('l', -336.70, -84.13, 25.02, -643.62), ('s', -388.34, 85.07, 25.02, -340.95),
                        ('s', -413.40, -112.76, 25.02, -961.35), ('l', -336.94, -224.10, 25.02, -497.37),
                        ('l', -511.30, 38.30, 25.02, -1048.05), ('s', -628.22, -203.26, 25.02, -907.64),
                        ('s', -597.51, 60.44, 25.02, -748.74), ('l', -754.36, 83.71, 25.02, 19.17))
}
WinterPresentInfo = {
    ToontownCentral: ((79.688, 158.123, 2.483, -15.427), (-128.618, -65.178, 0.484, -230.316),
                      (-62.478, -22.103, -1.975, 0), (140.478, -84.103, 2.525, -80),
                      (10.371, -130.137, 3.025, -227), (110.094, 26.642, 4.025, -55),
                      (44.119, 60.559, 4.025, 16), (127.134, 57.558, 2.525, -165)),
    DonaldsDock: ((-31.25, 100.15, 2.17, -91.91), (-61.68, 149.45, 3.28, 62.85),
                  (-118.33, -49.83, 5.69, -608.73  ), (-21.70, 2.85, 5.76, -51.71),
                  (55.64, -69.57, 3.28, -496.25), (63.59, 49.88, 5.69, -406.36)),
    DaisyGardens: ((50.15, 210.12, 10.02, -42.68), (-82.82, 164.23, 10.02, 133.45),
                   (-101.19, 95.29, 0.03, 151.26), (-13.21, 16.81, 0.02, 180),
                   (13.21, 16.81, 0.02, 180), (100.33, 98.10, 0.03, -418.37),
                   (83.51, 160.25, 10.01, -446.70), (27.17, 113.42, 0.02, -1429.56)),
    MinniesMelodyland: ((42.74, 76.49, 6.53, -324.55), (-25.18, 76.35, 6.53, -340.22),
                        (-71.93, 23.78, 6.53, -287.56), (-29.57, -113.89, 6.53, -191.89),
                        (135.34, -21.20, 7.46, -91.24), (100.93, -71.97, -4.50, 270.72),
                        (83.57, -34.08, -13.48, -1.42), (-58.18, 19.84, -14.49, 72.21)),
    TheBrrrgh: ((-36.97, -153.12, 6.19, -178.01), (35.55, -98.53, 6.19, -115.98),
                (35.03, 69.56, 6.19, 4.75), (-65.32, 114.56, 6.19, 50.27),
                (-128.99, 82.48, 6.19, 82.26), (-88.14, 53.74, 6.19, 442.47),
                (-159.25, -64.96, 6.19, 486,29), (-82.00, -77.92, 3.01, 871.50)),
    DonaldsDreamland: ((-101.56, -102.10, 0.03, -590.41), (-29.47, -96.72, 0.03, -524.91),
                       (78.62, -102.57, 0.03, -485.42), (188.57, 3.10, -15.00, -450.76),
                       (-28.36, -0.76, -14.98, -628.87), (60.15, 102.78, 0.03, -713.22),
                       (-79.55, 102.66, 0.03, -315.92), (-74.12, 102.81, 0.03, -419.09),
                       (-35.85, 101.44, 0.03, -357.40)),
    GoofySpeedway: ((21.77, 72.39, 0.09, 354.50,), (-20.77, 72.01, 0.09, 386.96),
                    (-23.52, -47.91, 0.07, 149.76), (26.33, -44.90, 0.08, 227.99),
                    (67.41, -90.64, -0.70, 317.75), (67.40, -128.76, -0.70, 227.40),
                    (17.19, -179.96, -0.73, 587.69), (-21.13, -178.65, -0.73, 482.66),
                    (-68.22, -92.15, -0.71, 404.58)),
    OutdoorZone: ((-35.06, -135.60, 0.03, 173.00), (-59.62, -135.03, 0.02, 181.19),
                  (-235.85, -24.40, 0.03, 461.12), (-244.38, 6.39, 0.02, 457.85),
                  (72.39, 150.47, 0.03, 671.53), (91.61, 134.48, 0.03, 663.82),
                  (24.60, 60.16, 5.92, 856.35), (19.89, 38.18, 5.92, 694.63),
                  (46.18, -126.77, 0.03, 545.35)),
    GolfZone: ((134.11, 32.55, 0.03, -111.43), (128.51, 8.60, 0.03, -93.33),
               (-7.29, -99.70, 0.03, -208.53), (-30.13, -93.81, 0.03, -205.59),
               (-103.59, -14.85, 0.03, -262.87), (-109.65, 6.68, 0.03, -256.57),
               (2.99, 85.39, 0.03, -543.35)),
    ToontownOutskirts: ((103.71, 111.67, 0.03, 24.47), (180.73, -47.95, 0.03, -776.64),
                        (170.27, -236.80, 0.03, -179.10), (40.92, -238.60, 0.03, -179.35),
                        (44.37, -134.82, 0.03, -629.22), (-34.11, -114.01, 0.03, -236.21),
                        (-336.70, -84.13, 25.02, -643.62), (-388.34, 85.07, 25.02, -340.95),
                        (-413.40, -112.76, 25.02, -961.35), (-336.94, -224.10, 25.02, -497.37))
}
HalloweenStart = (10, 24)
WinterStart = (12, 1)
WinterEnd = (1, 1)
AprilFoolsStart = (4, 1)
HolidayColors = (Vec4(1, 0.941, 0.09, 1), Vec4(1, 0.5, 0, 1), Vec4(0.8, 0.1, 0.1, 1), Vec4(1, 0.941, 0.09, 1))
BackgroundNodeNames = ['default', 'halloween', 'holiday', 'fools', 'test']
HolidayNormal = 0
HolidayHalloween = 1
HolidayWinter = 2
HolidayAprilFools = 3
HolidayID2Name = {HolidayNormal: 'default', HolidayHalloween: 'halloween', HolidayWinter: 'holiday', HolidayAprilFools: 'fools'}
HolidayID2Colors = {HolidayNormal: ((1, 0.9, 0.1, 1), (0.977, 0.816, 0.133, 1)),
                    HolidayHalloween: ((0.4, 0, 0.8, 1), (0.8, 0.4, 0, 1), (0.4, 0, 0.8, 1), (0.8, 0.4, 0, 1)),
                    HolidayWinter: ((0.8, 0.1, 0.1, 1), (0.1, 0.8, 0.1, 1), (0.1, 0.8, 0.1, 1), (0.8, 0.1, 0.1, 1)),
                    HolidayAprilFools: ((1, 0.9, 0.1, 1), (0.977, 0.816, 0.133, 1))}
ShortWorkTrainYardCogs = [
    ('mb', 13.111, 515.17, 25.268, 46.2),
    ('bc', -37.20, 496.70, 25.267, -60.0),
    ('sc', 178.29, 216.96, 86.899, 270.0),
    ('nc', 202.39, -192.1, -63.18, 91.2),
    ('nc', 263.86, -98.31, -63.05, 127.0),
    ('pp', 134.67, -185.4, -63.13, -77.0),
    ('tw', 167.09, -153.6, -63.23, -143.0),
    ('mb', -23.96, 187.27, -23.45, -36.0),
    ('tw', 120.68, 266.78, -23.45, 87.5),
    ('bc', 109.43, 110.41, -23.45, 0.0)
]
ShortWorkBathroomBattleDuration = 20
ShortWorkBathroomBattleAttackInfo = ((5, 'watercooler', 'Watercooler', 2, 50, 0, (0, 0, 0, -28.0, 246.0, 0), 'watercooler'),
                                     (5, 'bounced-check', 'Bounce Check', 3, 75, 0, (0, 0, 0, 180, -115, 0), 'throw-paper'),
                                     (5, '1dollar-bill-mod', 'Pick Pocket', 2, 50, 0, (0, 0, 0, -82.0, 20.0, 45), 'pickpocket'),
                                     (3.5, 'clip-on-tie-mod', 'Clip On Tie', 1, 95, 0, (0, 0, 0, 0, 0, 0), 'throw-paper'))
ShortWorkBathroomBattleToonAttackInfo = ((4, 75), (3, 95), (0, 100))
ShortWorkBarProps = [
    (5, 'cogdominium', 'tt_m_ara_csa_elevatorB', (-48.24, 200.79, 0.0), (0.0, 0.0, 0.0)),
    (5, 'cogdominium', 'tt_m_ara_csa_elevatorB', (31.649, 200.79, 0.0), (0.0, 0.0, 0.0)),
    (10, 'cashbotHQ', 'boiler_B2', (51.500, 188.33, 0.06), (-182.0, 0.0, 0.0)),
    (10, 'cashbotHQ', 'CBMetalCrate', (-66.84, 173.45, 0.0), (-182.0, 0.0, 0.0)),
    (10, 'cashbotHQ', 'CBMetalCrate', (-66.63, 179.44, 0.0), (-182.0, 0.0, 0.0)),
    (10, 'cashbotHQ', 'CBMetalCrate', (-67.07, 176.70, 5.5999), (-182.0, 0.0, 0.0)),
    (10, 'cashbotHQ', 'CBMetalCrate', (-60.77, 175.23, 0.0), (-182.0, 0.0, 0.0)),
    (10, 'cashbotHQ', 'VaultDoorCover', (-69.82, 142.44, 0.0), (90.0, 0.0, 0.0)),
    (11, 'lawbotHQ', 'LB_couchA', (16.455, 55.559, 0.0500), (-13.0, 0.0, 0.0)),
    (11, 'lawbotHQ', 'LB_couchA', (-55.97, 54.798, 0.0500), (37.4, 0.0, 0.0)),
    (12, 'bossbotHQ', 'BanquetTableChairs', (-43.7, -11.85, 0.0), (0.0, 0.0, 0.0)),
    (12, 'bossbotHQ', 'BanquetTableChairs', (-43.7, 12.15, 0.0), (0.0, 0.0, 0.0)),
    (12, 'bossbotHQ', 'BanquetTableChairs', (-43.7, 37.15, 0.0), (0.0, 0.0, 0.0)),
    (12, 'bossbotHQ', 'BanquetTableChairs', (39.95, -35.95, 0.0), (0.0, 0.0, 0.0)),
    (12, 'bossbotHQ', 'BanquetTableChairs', (14.8, -36.25, 0.0), (0.0, 0.0, 0.0)),
    (12, 'bossbotHQ', 'BanquetTableChairs', (14.8, -11.85, 0.0), (0.0, 0.0, 0.0)),
    (12, 'bossbotHQ', 'BanquetTableChairs', (14.8, 12.75, 0.0), (0.0, 0.0, 0.0)),
    (12, 'bossbotHQ', 'BanquetTableChairs', (14.8, 37.55, 0.0), (0.0, 0.0, 0.0)),
    (12, 'bossbotHQ', 'BanquetTableChairs', (39.8, -11.45, 0.0), (0.0, 0.0, 0.0)),
    (12, 'bossbotHQ', 'BanquetTableChairs', (39.8, 13.55, 0.0), (0.0, 0.0, 0.0))]
ShortWorkBarSeatPos = [(3.35, -6.75, 0.725), (6.45, -2.7, 0.725), (2.6, 6.55, 0.725), (-2.8, 6.3, 0.725),
                       (-6.25, 2.15, 0.725)]
ShortWorkBarSeatHpr = [(0, 0, 0), (90, 0, 0), (180, 0, 0), (180, 0, 0), (270, 0, 0)]
ShortWorkBarSeating = [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4),
                       (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (3, 0), (3, 1), (3, 2), (3, 3), (3, 4),
                       (4, 0), (4, 1), (4, 2), (4, 3), (4, 4), (5, 0), (5, 1), (5, 2), (5, 3), (5, 4),
                       (6, 0), (6, 1), (6, 2), (6, 3), (6, 4), (7, 0), (7, 1), (7, 2), (7, 3), (7, 4),
                       (8, 0), (8, 1), (8, 2), (8, 3), (8, 4), (9, 0), (9, 1), (9, 2), (9, 3), (9, 4)]
PrologueCogInfo = (('ym', 3), ('tbc', 8), ('bc', 4), ('cc', 1), ('bs', 5), ('rb', 8), ('tw', 3), ('f', 1), ('m', 7),
                   ('ac', 4), ('nd', 3), ('mm', 4), ('ac', 4), ('le', 7), ('nc', 5), ('b', 2), ('pp', 2), ('sd', 6),
                   ('ms', 5), ('ds', 5), ('bs', 5), ('tm', 2), ('tf', 6), ('ls', 7), ('le', 7), ('tw', 3), ('cr', 7),
                   ('bf', 1), ('hh', 6), ('bw', 8), ('sc', 1), ('mb', 6), ('mh', 8), ('p', 2), ('dt', 3), ('gh', 4),
                   ('cc', 1), ('mm', 4), ('tbc', 8))
PrologueCogPosInfo = [(58.269, 10.913, 3.5499, -169),
                      (60.689, 14.184, 3.5499, -170),
                      (66.031, 10.810, 3.5499, -170),
                      (68.464, 14.285, 3.5499, -173),
                      (72.922, 11.205, 3.5499, -177),
                      (76.536, 13.858, 3.5499, -181),
                      (81.663, 11.068, 3.5499, -181),
                      (85.904, 13.394, 3.5499, -182),
                      (91.206, 10.507, 3.5499, -182),
                      (93.865, 13.603, 3.5499, -182),
                      (98.872, 10.876, 3.5499, -182),
                      (100.67, 13.789, 3.5499, -182),
                      (105.25, 11.077, 3.5499, -185),
                      (107.39, 13.582, 3.5499, -194),
                      (111.56, 11.007, 3.5499, -200),
                      (113.90, 13.094, 3.5499, -206),
                      (122.48, 0.3078, 0.0098, -215),
                      (118.39, 10.667, 3.5499, -212),
                      (120.35, 13.415, 3.5499, -219),
                      (124.87, 10.567, 3.5499, -219),
                      (127.20, 12.776, 3.5499, -219),
                      (131.17, 10.927, 3.5499, -219),
                      (58.486, 1.3549, 0.0099, -135),
                      (63.294, 0.1528, 0.0098, -141),
                      (66.694, 1.4790, 0.0098, -147),
                      (71.228, 1.1296, 0.0098, -150),
                      (76.249, -0.386, 0.0098, -156),
                      (79.420, 0.7948, 0.0098, -162),
                      (83.852, 0.0041, 0.0098, -168),
                      (87.000, 1.5424, 0.0098, -171),
                      (91.532, 0.0807, 0.0098, -178),
                      (95.089, 1.2137, 0.0098, -190),
                      (99.656, 0.1926, 0.0098, -193),
                      (102.41, 1.7373, 0.0098, -193),
                      (106.65, 0.4988, 0.0098, -205),
                      (110.37, -0.064, 0.0098, -206),
                      (113.50, 0.5370, 0.0098, -215),
                      (116.40, 1.3548, 0.0098, -215),
                      (119.58, 1.4588, 0.0098, -215),
                      (122.48, 2.2766, 0.0098, -215),
                      (125.94, 1.6668, 0.0098, -215),
                      (129.87, 0.9873, 0.0098, -215)]
LoadingScreenInfo = (('toons', 48), ('cogs', 21), ('halloween', 7), ('winter', 11), ('fools', 2), ('short_work', 10), ('prologue', 10))
ToonNameRegex = r"^[a-zA-Z0-9!?.*@#$&()+\-`+,/|: ]*$"    # TODO: simplify & improve this regex as needed
TestServerGameserver = 'gameserver.toontownoffline.net'

# Prop Generator globals... should probably add more at a later point then move to their own file
PropGeneratorPropID = 0
PropGeneratorTimestamp = 2
PropGeneratorGeneratedBy = 4
PropGeneratorEditedBy = 6

MAX_PROPS = 0
MAX_PROPS_HARD = 1
PROPS_LOCKED = 2
PROPS_LOCKED_ZONE = 3
PROPS_UNLOCKED = 4
PROPS_UNLOCKED_ZONE = 5
PROPS_SPAWNING_LOCKED = 6
PROPS_DELETED = 7
PROPS_DELETED_ZONE = 8
PROPS_SPAMMING = 9
PROPS_ERROR = 10
CORRUPTED_SAVE = 11
PIXEL_ART_ERROR = 12
PIXEL_ART_OVERFLOW = 13
PROPS_DELETED_ZONE_ERROR_NO_PROPGEN = 14
PROPS_DELETED_ZONE_ERROR_INVALID_ZONE = 15
PROPS_LOCKED_ZONE_ERROR_INVALID_ZONE = 16
PROPS_LOCKED_ZONE_ERROR_NO_PROPGEN = 17
PROPS_FUTURE_SAVE = 18
PROPS_OUTDATED_SAVE = 19
PROPS_NO_PERMISSION = 20
PROPS_EXPERIMENTAL = 21
PROP_LOCKED = 22
PROP_NO_PERMISSION = 23


# Micro Game Types
MicroGameTypePieBlitz = 0
MicroGameTypeHideAndSeek = 1

# Micro Game Timer
MicroGameTimerOff = 65535

# Pie Blitz
DefaultPieBlitzDamage = 5
DefaultPieBlitzPie = 4
DefaultPieBlitzDuration = 60
MaxPieBlitzDuration = 300

# Speedchat index
YouStink = 905

# Boss Party
DefaultBossPartyDuration = 60

BossPartySellbotBoss = 0
BossPartySellbotBossHardcore = 1
BossPartySellbotBossStormSellbot = 2
BossPartySellbotBossWinter = 3
BossPartySellbotBossArena = 4

BossPartyCashbotBoss = 5
BossPartyCashbotBossHardcore = 6

BossPartyLawbotBoss = 7
BossPartyLawbotBossHardcore = 8
BossPartyLawbotBossArena = 9

BossPartyBossbotBoss = 10
BossPartyBossbotBossHardcore = 11

BossPartyCategoryMinigames = 0
BossPartyCategorySellbot = 1
BossPartyCategoryCashbot = 2
BossPartyCategoryLawbot = 3
BossPartyCategoryBossbot = 4

BossPartyPropHunt = 12
BossPartyDeception = 13

BossPartyDict = {
    BossPartySellbotBoss: (BossPartySellbotBossHardcore, BossPartySellbotBossStormSellbot, BossPartySellbotBossWinter,
                           BossPartySellbotBossArena),
    BossPartyCashbotBoss: (BossPartyCashbotBossHardcore,),
    BossPartyLawbotBoss: (BossPartyLawbotBossHardcore, BossPartyLawbotBossArena),
    BossPartyBossbotBoss: (BossPartyBossbotBossHardcore,)
}

BossPartyCategories = {
    BossPartyCategoryMinigames: (BossPartyPropHunt,),

    BossPartyCategorySellbot: (BossPartySellbotBoss,
                               BossPartySellbotBossHardcore, BossPartySellbotBossStormSellbot,
                               BossPartySellbotBossWinter, BossPartySellbotBossArena),

    BossPartyCategoryCashbot: (BossPartyCashbotBoss, BossPartyCashbotBossHardcore),

    BossPartyCategoryLawbot: (BossPartyLawbotBoss, BossPartyLawbotBossHardcore, BossPartyLawbotBossArena),

    BossPartyCategoryBossbot: (BossPartyBossbotBoss, BossPartyBossbotBossHardcore)
}

BossPartyPlayerLimits = {BossPartySellbotBoss: 8,
                         BossPartySellbotBossHardcore: 8,
                         BossPartySellbotBossStormSellbot: 8,
                         BossPartySellbotBossWinter: 8,
                         BossPartySellbotBossArena: 16,
                         BossPartyCashbotBoss: 8,
                         BossPartyCashbotBossHardcore: 8,
                         BossPartyLawbotBoss: 8,
                         BossPartyLawbotBossHardcore: 8,
                         BossPartyLawbotBossArena: 16,
                         BossPartyBossbotBoss: 8,
                         BossPartyBossbotBossHardcore: 8,
                         BossPartyPropHunt: 16,
                         BossPartyDeception: 8}

BossPartyPromotionInfo = {
    BossPartyCategoryBossbot: 0,
    BossPartyCategoryLawbot: 1,
    BossPartyCategoryCashbot: 2,
    BossPartyCategorySellbot: 3
}

# Hide and Seek
DefaultHideAndSeekHidingDuration = 60
MaxHideAndSeekHidingDuration = 300
DefaultHideAndSeekSeekingDuration = 60
MaxHideAndSeekSeekingDuration = 300

# Limitation used by Magic Words for emblems a Toon can have
EmblemsMax = 10000

# Multiplier limitations for realm hosters
ExpMultiplierMin = 1
ExpMultiplierMax = 100
ExpCapMin = 1
ExpCapMax = 10000
MeritMultiplierMin = 1
MeritMultiplierMax = 100
DoodleMultiplierMin = 1
DoodleMultiplierMax = 100

# Used for the "TO BE CONTINUED" message when attempting to enter Gyro's Lab
GyroDoorRejectLabelInfo = ((-0.3, 0.0, 0.125), (0.3, 0.0, 0.125), (0.0, 0.0, -0.325))
GyroDoorRejectDelays = ((0.0, 1.5, 3.0), (3.0, 1.5, 0.0))

# Welcome prompt
WelcomePromptIconScales = (2.2, 2.2, 1.3, 2.2, 1.0)

# Magic Menu things
MagicMenuButtonPositions = ((-0.35, 0.0, 0.1), (0.35, 0.0, 0.1), (-0.35, 0.0, -0.2), (0.35, 0.0, -0.2))
MagicMenuIconPositions = ((-0.775, 0.0, 0.1), (0.775, 0.0, 0.1), (-0.775, 0.0, -0.2), (0.775, 0.0, -0.2))
MagicMenuIconScales = (2.5, 1.4, 2.5, 2.5)
MagicMenuDisabled = -2
MagicMenuInvalid = -1
MagicMenuTeleportMenu = 0
MagicMenuPropGenerator = 1
MagicMenuMountKart = 2
MagicMenuBossParty = 3
MagicMenuBuildLots = 4

# Teleport Interface
TeleportInterfaceModeNormal = 0
TeleportInterfaceModeMagicMenu = 1

# Boss Arena
BossArenaNoTeam = -1
BossArenaTeamA = 0
BossArenaTeamB = 1

# Sellbot Arena
SellbotArenaPieDmgMult = 2
SellbotArenaSuddenDeathPieDmgMult = 2
SellbotArenaPieDamages = {
  BossArenaTeamA: -1,
  BossArenaTeamB: 1
}
SellbotArenaUpcomingSuddenDeathDuration = 240
SellbotArenaSuddenDeathDuration = 300
SellbotArenaBattleOneHpr = (90, 0, 0)
SellbotArenaTeamBBottomPos = (239, -40, -17.95)
SellbotArenaTeamBDeathPos = (317, -40, -17.95)
SellbotArenaCenterPos = (0, -40, 0.03)
SellbotArenaTeamABottomPos = (-239, -40, -17.95)
SellbotArenaTeamADeathPos = (-317, -40, -17.95)

# Lawbot Arena
LawbotArenaMaxDamage = 2500
LawbotArenaInitialDamage = 1250
LawbotArenaLawyerPosHprs = [(-45, -24, 0, -90, 0, 0),
                            (-45, -12, 0, -90, 0, 0),
                            (-45, 0, 0, -90, 0, 0),
                            (-45, 12, 0, -90, 0, 0),
                            (-45, 24, 0, -90, 0, 0),
                            (-45, 36, 0, -90, 0, 0),
                            (-45, 48, 0, -90, 0, 0),
                            (-45, 60, 0, -90, 0, 0),
                            (45, -24, 0, 90, 0, 0),
                            (45, -12, 0, 90, 0, 0),
                            (45, 0, 0, 90, 0, 0),
                            (45, 12, 0, 90, 0, 0),
                            (45, 24, 0, 90, 0, 0),
                            (45, 36, 0, 90, 0, 0),
                            (45, 48, 0, 90, 0, 0),
                            (45, 60, 0, 90, 0, 0)]
LawbotArenaGavelPosHprs = [(-15, 50, 0, 165, 0, 0),
                           (10, -35, 0, 15, 0, 0),
                           (-17, -35, 0, 15, 0, 0),
                           (10, 50, 0, -135, 0, 0),
                           (-80, 70, 0, 270, 0, 0),
                           (80, 70, 0, 90, 0, 0)]
LawbotArenaGavelHeadings = [(0, -15, 4, -70 - 45, 5, 45),
                            (0, -45, -4, -35, -45, -16, 32),
                            (0, -8, 19, -7, 5, 23),
                            (0, -4, 8, -16, 32, -45, 7, 7, -30, 19, -13, 25),
                            (0, -15, -25, 15, 25),
                            (0, -15, -25, 15, 25)]
LawbotArenaWitnessStandAPosHpr = (54, 100, 0, -90, 0, 0)
LawbotArenaWitnessStandBPosHpr = (-54, 100, 0, -90, 0, 0)
LawbotArenaInvalidMode = -1
LawbotArenaProsecutingBoth = 0
LawbotArenaProsecutingToons = 1
LawbotArenaProsecutingBoss = 2
LawbotArenaLawyerExp = 3
LawbotArenaLawyerStunTime = 5
LawbotArenaSuddenDeathDuration = 900
LawbotArenaSuddenDeathInitialMultiplier = 1.2
LawbotArenaSuddenDeathOvertimeMultiplier = 0.1
LawbotArenaSuddenDeathOvertimeDuration = 30

LockedStateFlagChangeOnly = -1
LockedStateAvatarControlsExemption = 1
LockedStateMessengerExemption = 2
LockedStateDualExemption = 3
LockedStateCagedExemption = 4

# Museum Toon indices
MuseumToonDeskFlippy = 0
MuseumToonBetaFlippy = 1
MuseumToonCoachZ = 2
MuseumToonClerkPeppy = 3
MuseumToonAnitaWinn = 4
MuseumToonProfessorFlake = 5
MuseumToonChip = 6
MuseumToonShepAhoy = 7
MuseumToonPartyPlanner = 8
MuseumToonProfessorPrepostera = 9
MuseumToonLowdenClear = 10
MuseumToonLilOldman = 11
MuseumToonBigCheese = 12

# Beta Playground Minigames
BetaPlaygroundMinigames = [
    CannonGameId,
    RaceGameBetaId,
    PatternGameBetaId,
    TagGameId
]

# Offsets for No Torso Cheesy Effect
torsoToOffset = {'l': -1.5, 'm': -1.2, 's': -1.1}

# Valid inputs for Toontown Outskirts playground theme
ToontownOutskirtsThemes = ('tt', 'dd', 'dg', 'mm', 'br', 'dl')

# Fog, snow, and winter options for each Toontown Outskirts playground theme
ThemeSnow = 0
ThemeFog = 1
ThemeWinter = 2
ThemeHalloween = 3
Theme2Decoration = {'tt': (0, 0, 1, 1),
                    'dd': (0, 1, 0, 1),
                    'dg': (0, 0, 1, 1),
                    'mm': (0, 0, 0, 1),
                    'br': (1, 1, 1, 1),
                    'dl': (0, 0, 0, 0)}

# Treasure info for each playground type
Treasure2Model = {ToontownCentral: 'phase_4/models/props/icecream',
                  DonaldsDock: 'phase_6/models/props/starfish_treasure',
                  TheBrrrgh: 'phase_8/models/props/snowflake_treasure',
                  MinniesMelodyland: 'phase_6/models/props/music_treasure',
                  DaisyGardens: 'phase_8/models/props/flower_treasure',
                  DonaldsDreamland: 'phase_8/models/props/zzz_treasure'}

# Skybox info for each playground type
Playground2Skybox = {'tt': 'phase_3.5/models/props/TT_sky',
                     'dd': 'phase_3.5/models/props/BR_sky',
                     'dg': 'phase_3.5/models/props/TT_sky',
                     'mm': 'phase_6/models/props/MM_sky',
                     'br': 'phase_3.5/models/props/BR_sky',
                     'dl': 'phase_8/models/props/DL_sky'}

# Title color info for each playground type
Playground2Title = {'tt': (1.0, 0.5, 0.4, 1.0),
                    'dd': (0.8, 0.6, 0.5, 1.0),
                    'dg': (0.8, 0.6, 1.0, 1.0),
                    'mm': (1.0, 0.5, 0.5, 1.0),
                    'br': (0.3, 0.6, 1.0, 1.0),
                    'dl': (1.0, 0.9, 0.5, 1.0)}

# Positions of the snow piles in the Holiday VP
HolidayVPSnowPiles = ((51.51, 49.40, 17.95),
                      (109.86, -16.93, 17.95),
                      (-36.19, -19.35, 0.02),
                      (18.48, -132.41, -6.53),
                      (36.25, -37.14, 0.02),
                      (-50.85, 61.47, 17.95),
                      (-82.94, -40.76, 17.95))

HolidayVPSnowPilesHardcore = ((51.51, 49.40, 17.95),
                              (109.86, -16.93, 17.95),
                              (-36.19, -19.35, 0.02),
                              (18.48, -325.13, -39.03),
                              (36.25, -37.14, 0.02),
                              (-50.85, 61.47, 17.95),
                              (-82.94, -40.76, 17.95))

ZonesNoVirtualCogCredit = (LawbotStageIntA, LawbotStageIntB, LawbotStageIntC, LawbotStageIntD)


class SettingsWarning(enum.Enum):
    SWRestart = enum.auto()
    SWReload = enum.auto()
    SWEstate = enum.auto()
    SWStreet = enum.auto()


# 0 is restart, 1 is reload
SettingsWarnings = {
    'antialiasing': SettingsWarning.SWRestart,
    'anisotropic-filtering': SettingsWarning.SWRestart,
    'avatar-culling': SettingsWarning.SWReload,
    'character-lods': SettingsWarning.SWReload,
    'font-quality': SettingsWarning.SWRestart,
    'smooth-animations': SettingsWarning.SWRestart,
    'vsync': SettingsWarning.SWRestart,
    'low-memory-mode': SettingsWarning.SWRestart,
    'propgen-collisions': SettingsWarning.SWReload,
    'reflection-rtt-resolution': SettingsWarning.SWReload,

    'classic-dogs': SettingsWarning.SWReload,  # technically this just needs a new loading of a toon head
    'classic-loading-screen': SettingsWarning.SWRestart,
    'classic-nametags': SettingsWarning.SWRestart,
    'classic-chat-bubbles': SettingsWarning.SWRestart,
    'classic-pick-a-toon': SettingsWarning.SWRestart,
    'classic-sfx': SettingsWarning.SWRestart,
    'estate-music': SettingsWarning.SWEstate,
    'estate-popsicle-treasures': SettingsWarning.SWEstate,
    'new-speedchat-phrases': SettingsWarning.SWRestart,
    'photo-album': SettingsWarning.SWRestart,
    'street-battle-music': SettingsWarning.SWStreet,
    'updated-map': SettingsWarning.SWRestart,  # TODO: this can probably just be changed
    }

BackgroundColors = [
    [266, 87, 40, 70],  # PURPLE (DEFAULT)
    [223, 87, 40, 100],  # BLUE (RETRO)
    [0, 0, 0, 50],  # BLACK
    ]

NPCHalloweenCostumes = (
    # later we can clean this up and make it more dynamic and shit, i threw this together in 10 min
    # (top, color), (sleeve, color), (pants, color), (hat, tex), (glasses, tex), (backpack, tex), (shoes, tex)
    # COWBOY
    ((52, 27), (41, 27), (1, 9), (15, 0), (0, 0), (0, 0), (3, 11)),
    # PIRATE
    ((120, 27), (107, 27), (47, 27), (16, 0), (20, 0), (18, 0), (3, 47)),
    # DINOSAUR
    ((123, 27), (110, 27), (50, 27), (54, 0), (0, 0), (21, 0), (3, 48)),
    # SUPER TOON
    ((121, 27), (108, 27), (48, 27), (0, 0), (0, 0), (19, 0), (0, 0)),
    # VAMPIRE
    ((122, 27), (109, 27), (49, 27), (0, 0), (0, 0), (20, 0), (0, 0)),
    # BETA
    ((151, 27), (138, 27), (60, 27), (0, 0), (0, 0), (0, 0), (0, 0)),

    # These are costumes with just accessories
    # (hat, tex), (glasses, tex), (backpack, tex), (shoes, tex)
    ((16, 0), (20, 0), (0, 0), (0, 0)),
    ((19, 0), (0, 0), (0, 0), (0, 0)),
    ((34, 0), (0, 0), (0, 0), (0, 0)),
    ((39, 0), (0, 0), (0, 0), (0, 0)),
    ((43, 0), (0, 0), (0, 0), (0, 0)),
    ((44, 0), (0, 0), (0, 0), (0, 0)),
    ((45, 0), (0, 0), (0, 0), (0, 0)),
    ((46, 0), (0, 0), (0, 0), (0, 0)),
    ((48, 0), (0, 0), (0, 0), (0, 0)),
    ((53, 0), (0, 0), (0, 0), (0, 0)),
    ((53, 0), (20, 0), (0, 0), (0, 0)),
    ((0, 0), (5, 0), (0, 0), (0, 0)),
    ((0, 0), (12, 0), (0, 0), (0, 0)),
    ((0, 0), (17, 0), (0, 0), (0, 0)),
)

ValidAnimalTypes = [
  'skelecog', 'skeleton', 'suit', 'doodle', 'goon',
  'boss', 'dog', 'cat', 'horse', 'mouse', 'rabbit',
  'duck', 'monkey', 'bear', 'pig', 'gyro',
  'scrooge', 'mickey', 'minnie', 'donald-wheel',
  'donald', 'clarabelle', 'daisy', 'chip', 'dale',
  'doodle', 'trolley', 'cog', 'goofy'
]

PIE_BTN_POS_NORMAL = 0
PIE_BTN_POS_INSTANCE = 1

KnockKnockCooldown = 180
Hood2KnockKnockHeal = {ToontownCentral: 5,
  DonaldsDock: 7,
  DaisyGardens: 9,
  MinniesMelodyland: 11,
  TheBrrrgh: 13,
  DonaldsDreamland: 15}

FLOWER_SPIN_RATE_MIN = 4.0
FLOWER_SPIN_RATE_DEFAULT = 9.5
FLOWER_SPIN_RATE_MAX = 100.0