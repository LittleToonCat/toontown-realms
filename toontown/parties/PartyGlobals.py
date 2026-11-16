from enum import Enum, auto, IntEnum

from panda3d.core import BitMask32, Point3, VBase4
from direct.showbase import PythonUtil
from toontown.toonbase import TTLocalizer

KICK_TO_PLAYGROUND_EVENT = 'parties_kickToPlayground'
MaxSetInvites = 1000
MaxSetPartiesInvitedTo = 100
MaxSetHostedParties = 50
MaxPlannedYear = 2030
MinPlannedYear = 1975
JellybeanMultiplier = 1.5
JellyBeanDayMultiplier = 2
PARTY_DURATION = 1800.0
EventsPageGuestNameMaxWidth = 0.42
EventsPageGuestNameMaxLetters = 18
EventsPageHostNameMaxWidth = 0.37
PartyRefundPercentage = 0.95
PartyPlannerAsapMinuteRounding = 5
UberdogCheckPartyStartFrequency = 5.0
UberdogPurgePartyPeriod = 24.0
UberdogPartiesSanityCheckFrequency = 60
PartyStartTimeout = 15  # minutes before it's "too late" to start a party
JarLabelTextColor = (0.95,
                     0.95,
                     0.0,
                     1.0)
JarLabelMaxedTextColor = (1.0,
                          0.0,
                          0.0,
                          1.0)
TuftsOfGrass = 75
MaxToonsAtAParty = 20
DefaultPartyDuration = 0.5
DelayBeforeAutoKick = 30.0
MaxHostedPartiesPerToon = 1
PartyEditorGridBounds = ((-0.11, 0.289), (0.55, -0.447))
PartyEditorGridCenter = (PartyEditorGridBounds[0][0] + (PartyEditorGridBounds[1][0] - PartyEditorGridBounds[0][0]) / 2.0,
                         PartyEditorGridBounds[1][1] + (PartyEditorGridBounds[0][1] - PartyEditorGridBounds[1][1]) / 2.0)
PartyEditorGridSize = (18, 15)
PartyEditorGridSquareSize = ((PartyEditorGridBounds[1][0] - PartyEditorGridBounds[0][0]) / float(PartyEditorGridSize[0]),
                             (PartyEditorGridBounds[0][1] - PartyEditorGridBounds[1][1]) / float(PartyEditorGridSize[1]))
PartyEditorGridRotateThreshold = 0.08
AvailableGridSquares = 202
TrashCanPosition = (-0.24, 0.0, -0.65)
TrashCanScale = 0.7
PartyEditorTrashBounds = ((-0.16, -0.38), (-0.05, -0.56))


class ActivityRequestStatus(IntEnum):
    Joining = 0
    Exiting = 1


class InviteStatus(IntEnum):
    NotRead = 0
    ReadButNotReplied = 1
    Accepted = 2
    Rejected = 3


class InviteTheme(IntEnum):
    Birthday = 0
    GenericMale = 1
    GenericFemale = 2
    Racing = 3
    Valentoons = 4
    VictoryParty = 5
    Winter = 6


class PartyStatus(IntEnum):
    Pending = 0
    Cancelled = 1
    Finished = 2
    CanStart = 3
    Started = 4
    NeverStarted = 5


class AddPartyErrorCode(IntEnum):
    AllOk = 0
    ValidationError = 1
    DatabaseError = 2
    TooManyHostedParties = 3


class ChangePartyFieldErrorCode(IntEnum):
    AllOk = 0
    ValidationError = 1
    DatabaseError = 2
    AlreadyStarted = 3
    AlreadyRefunded = 4


class ActivityTypes(IntEnum):
    HostInitiated = 0
    GuestInitiated = 1
    Continuous = 2


class PartyGateDenialReasons(IntEnum):
    Unavailable = auto()
    Full = auto()


class ActivityIds(IntEnum):
    PartyJukebox = 0
    PartyCannon = 1
    PartyTrampoline = 2
    PartyCatch = 3
    PartyDance = 4
    PartyTugOfWar = 5
    PartyFireworks = 6
    PartyClock = 7
    PartyJukebox40 = 8
    PartyJukebox60 = 9
    PartyDance20 = 10
    PartyCog = 11
    PartyVictoryTrampoline = 12
    PartyWinterCatch = 13
    PartyWinterTrampoline = 14
    PartyWinterCog = 15
    PartyValentineDance = 16
    PartyValentineDance20 = 17
    PartyValentineJukebox = 18
    PartyValentineJukebox40 = 19
    PartyValentineJukebox60 = 20
    PartyValentineTrampoline = 21


PartyEditorActivityOrder = [ActivityIds.PartyCog,
                            ActivityIds.PartyWinterCog,
                            ActivityIds.PartyJukebox,
                            ActivityIds.PartyJukebox40,
                            ActivityIds.PartyJukebox60,
                            ActivityIds.PartyValentineJukebox,
                            ActivityIds.PartyValentineJukebox40,
                            ActivityIds.PartyValentineJukebox60,
                            ActivityIds.PartyCannon,
                            ActivityIds.PartyTrampoline,
                            ActivityIds.PartyValentineTrampoline,
                            ActivityIds.PartyVictoryTrampoline,
                            ActivityIds.PartyWinterTrampoline,
                            ActivityIds.PartyCatch,
                            ActivityIds.PartyWinterCatch,
                            ActivityIds.PartyDance,
                            ActivityIds.PartyDance20,
                            ActivityIds.PartyValentineDance,
                            ActivityIds.PartyValentineDance20,
                            ActivityIds.PartyTugOfWar,
                            ActivityIds.PartyFireworks,
                            ActivityIds.PartyClock]
UnreleasedActivityIds = ()
MutuallyExclusiveActivities = ((ActivityIds.PartyJukebox, ActivityIds.PartyJukebox40, ActivityIds.PartyJukebox60),
                               (ActivityIds.PartyValentineJukebox, ActivityIds.PartyValentineJukebox40, ActivityIds.PartyValentineJukebox60),
                               (ActivityIds.PartyDance, ActivityIds.PartyDance20),
                               (ActivityIds.PartyValentineDance, ActivityIds.PartyValentineDance20))
VictoryPartyActivityIds = frozenset([ActivityIds.PartyVictoryTrampoline])
VictoryPartyReplacementActivityIds = frozenset([ActivityIds.PartyTrampoline])
WinterPartyActivityIds = frozenset([ActivityIds.PartyWinterCatch, ActivityIds.PartyWinterTrampoline, ActivityIds.PartyWinterCog])
WinterPartyReplacementActivityIds = frozenset([ActivityIds.PartyCatch, ActivityIds.PartyTrampoline, ActivityIds.PartyCog])
ValentinePartyActivityIds = frozenset([ActivityIds.PartyValentineDance,
                                       ActivityIds.PartyValentineDance20,
                                       ActivityIds.PartyValentineJukebox,
                                       ActivityIds.PartyValentineJukebox40,
                                       ActivityIds.PartyValentineJukebox60,
                                       ActivityIds.PartyValentineTrampoline])
ValentinePartyReplacementActivityIds = frozenset([ActivityIds.PartyDance,
                                                  ActivityIds.PartyDance20,
                                                  ActivityIds.PartyJukebox,
                                                  ActivityIds.PartyJukebox40,
                                                  ActivityIds.PartyJukebox60,
                                                  ActivityIds.PartyTrampoline])


class DecorationIds(IntEnum):
    BalloonAnvil = 0
    BalloonStage = 1
    Bow = 2
    Cake = 3
    Castle = 4
    GiftPile = 5
    Horn = 6
    MardiGras = 7
    NoiseMakers = 8
    Pinwheel = 9
    GagGlobe = 10
    BannerJellyBean = 11
    CakeTower = 12
    HeartTarget = 13
    HeartBanner = 14
    FlyingHeart = 15
    Hydra = 16
    BannerVictory = 17
    CannonVictory = 18
    CogStatueVictory = 19
    TubeCogVictory = 20
    cogIceCreamVictory = 21
    cogIceCreamWinter = 22
    StageWinter = 23
    CogStatueWinter = 24
    snowman = 25
    snowDoodle = 26
    BalloonAnvilValentine = 27
    skybox_ttc = 28
    skybox_mml = 29
    skybox_br = 30
    skybox_ddl = 31
    skybox_hw = 32
    skybox_sbhq = 33
    skybox_sbhq2003 = 34
    skybox_bbhq = 35


MutuallyExclusiveDecorations = ((DecorationIds.skybox_ttc, DecorationIds.skybox_mml, DecorationIds.skybox_br,
                                 DecorationIds.skybox_ddl, DecorationIds.skybox_hw, DecorationIds.skybox_sbhq,
                                 DecorationIds.skybox_sbhq2003, DecorationIds.skybox_bbhq),)
DECORATION_VOLUME = 1.0
DECORATION_CUTOFF = 45
VictoryPartyDecorationIds = frozenset([DecorationIds.Hydra,
                                       DecorationIds.BannerVictory,
                                       DecorationIds.CannonVictory,
                                       DecorationIds.CogStatueVictory,
                                       DecorationIds.TubeCogVictory,
                                       DecorationIds.cogIceCreamVictory])
WinterPartyDecorationIds = frozenset([DecorationIds.cogIceCreamWinter,
                                      DecorationIds.StageWinter,
                                      DecorationIds.CogStatueWinter,
                                      DecorationIds.snowman,
                                      DecorationIds.snowDoodle])
VictoryPartyReplacementDecorationIds = frozenset([DecorationIds.BannerJellyBean])
ValentinePartyDecorationIds = frozenset([DecorationIds.BalloonAnvilValentine,
                                         DecorationIds.HeartBanner,
                                         DecorationIds.HeartTarget,
                                         DecorationIds.FlyingHeart])
ValentinePartyReplacementDecorationIds = frozenset([DecorationIds.BalloonAnvil, DecorationIds.BannerJellyBean])
UnreleasedDecorationIds = ()


class GoToPartyStatus(IntEnum):
    AllowedToGo = 0
    PartyFull = 1
    PrivateParty = 2
    PartyOver = 3
    PartyNotActive = 4

PlayGroundToPartyClockColors = {'tbr': (53.0 / 255.0,
                                        116.0 / 255.0,
                                        148.0 / 255.0,
                                        1.0),
                                'dga': (52.0 / 255.0,
                                        153.0 / 255.0,
                                        95.0 / 255.0,
                                        1.0),
                                'dod': (60.0 / 255.0,
                                        98.0 / 255.0,
                                        142.0 / 255.0,
                                        1.0),
                                'ddl': (79.0 / 255.0,
                                        92.0 / 255.0,
                                        120.0 / 255.0,
                                        1.0),
                                'mml': (128.0 / 255.0,
                                        62.0 / 255.0,
                                        142.0 / 255.0,
                                        1.0),
                                'ttc': (77.0 / 255.0,
                                        137.0 / 255.0,
                                        52.0 / 255.0,
                                        1.0),
                                'tnl': (77.0 / 255.0,
                                        137.0 / 255.0,
                                        52.0 / 255.0,
                                        1.0)}
PartyGridUnitLength = [14.4, 14.6]
PartyGridHeadingConverter = 15.0
PartyGridToPandaOffset = (-PartyGridUnitLength[0] * PartyEditorGridSize[0] / 2.0, -PartyGridUnitLength[1] * PartyEditorGridSize[1] / 2.0)
PartyCostMultiplier = 1
MinimumPartyCost = 100 * PartyCostMultiplier
ActivityInformationDict = {ActivityIds.PartyJukebox: {'cost': int(50 * PartyCostMultiplier),
                                                      'gridsize': (1, 1),
                                                      'numberPerPurchase': 1,
                                                      'limitPerParty': 1,
                                                      'paidOnly': False,
                                                      'gridAsset': 'PartyJukebox_activity_1x1'},
                           ActivityIds.PartyJukebox40: {'cost': int(100 * PartyCostMultiplier),
                                                        'gridsize': (1, 1),
                                                        'numberPerPurchase': 1,
                                                        'limitPerParty': 1,
                                                        'paidOnly': False,
                                                        'gridAsset': 'PartyJukebox_activity_1x1'},
                           ActivityIds.PartyJukebox60: {'cost': int(150 * PartyCostMultiplier),
                                                        'gridsize': (1, 1),
                                                        'numberPerPurchase': 1,
                                                        'limitPerParty': 1,
                                                        'paidOnly': False,
                                                        'gridAsset': 'PartyJukebox_activity_1x1'},
                           ActivityIds.PartyValentineJukebox: {'cost': int(50 * PartyCostMultiplier),
                                                               'gridsize': (1, 1),
                                                               'numberPerPurchase': 1,
                                                               'limitPerParty': 1,
                                                               'paidOnly': False,
                                                               'gridAsset': 'PartyJukebox_activity_1x1'},
                           ActivityIds.PartyValentineJukebox40: {'cost': int(100 * PartyCostMultiplier),
                                                                 'gridsize': (1, 1),
                                                                 'numberPerPurchase': 1,
                                                                 'limitPerParty': 1,
                                                                 'paidOnly': False,
                                                                 'gridAsset': 'PartyJukebox_activity_1x1'},
                           ActivityIds.PartyValentineJukebox60: {'cost': int(150 * PartyCostMultiplier),
                                                                 'gridsize': (1, 1),
                                                                 'numberPerPurchase': 1,
                                                                 'limitPerParty': 1,
                                                                 'paidOnly': False,
                                                                 'gridAsset': 'PartyJukebox_activity_1x1'},
                           ActivityIds.PartyCannon: {'cost': int(50 * PartyCostMultiplier),
                                                     'gridsize': (1, 1),
                                                     'numberPerPurchase': 5,
                                                     'limitPerParty': 10,
                                                     'paidOnly': False,
                                                     'gridAsset': 'PartyCannon_activity_1x1'},
                           ActivityIds.PartyTrampoline: {'cost': int(50 * PartyCostMultiplier),
                                                         'gridsize': (2, 2),
                                                         'numberPerPurchase': 1,
                                                         'limitPerParty': 8,
                                                         'paidOnly': False,
                                                         'gridAsset': 'PartyTrampoline_activity_2x2'},
                           ActivityIds.PartyValentineTrampoline: {'cost': int(50 * PartyCostMultiplier),
                                                                  'gridsize': (2, 2),
                                                                  'numberPerPurchase': 1,
                                                                  'limitPerParty': 8,
                                                                  'paidOnly': False,
                                                                  'gridAsset': 'PartyTrampoline_activity_2x2'},
                           ActivityIds.PartyVictoryTrampoline: {'cost': int(50 * PartyCostMultiplier),
                                                                'gridsize': (2, 2),
                                                                'numberPerPurchase': 1,
                                                                'limitPerParty': 8,
                                                                'paidOnly': False,
                                                                'gridAsset': 'PartyTrampoline_activity_2x2'},
                           ActivityIds.PartyWinterTrampoline: {'cost': int(50 * PartyCostMultiplier),
                                                               'gridsize': (2, 2),
                                                               'numberPerPurchase': 1,
                                                               'limitPerParty': 8,
                                                               'paidOnly': False,
                                                               'gridAsset': 'PartyTrampoline_activity_2x2'},
                           ActivityIds.PartyCatch: {'cost': int(300 * PartyCostMultiplier),
                                                    'gridsize': (5, 5),
                                                    'numberPerPurchase': 1,
                                                    'limitPerParty': 1,
                                                    'paidOnly': True,
                                                    'gridAsset': 'PartyCatch_activity_5x5'},
                           ActivityIds.PartyWinterCatch: {'cost': int(300 * PartyCostMultiplier),
                                                          'gridsize': (5, 5),
                                                          'numberPerPurchase': 1,
                                                          'limitPerParty': 1,
                                                          'paidOnly': True,
                                                          'gridAsset': 'PartyCatch_activity_5x5'},
                           ActivityIds.PartyCog: {'cost': int(300 * PartyCostMultiplier),
                                                  'gridsize': (5, 5),
                                                  'numberPerPurchase': 1,
                                                  'limitPerParty': 1,
                                                  'paidOnly': True,
                                                  'gridAsset': 'PartyCog_activity_5x5'},
                           ActivityIds.PartyWinterCog: {'cost': int(300 * PartyCostMultiplier),
                                                        'gridsize': (5, 5),
                                                        'numberPerPurchase': 1,
                                                        'limitPerParty': 1,
                                                        'paidOnly': True,
                                                        'gridAsset': 'PartyCog_activity_5x5'},
                           ActivityIds.PartyDance: {'cost': int(100 * PartyCostMultiplier),
                                                    'gridsize': (3, 3),
                                                    'numberPerPurchase': 1,
                                                    'limitPerParty': 1,
                                                    'paidOnly': True,
                                                    'gridAsset': 'PartyDance_activity_3x3'},
                           ActivityIds.PartyDance20: {'cost': int(200 * PartyCostMultiplier),
                                                      'gridsize': (3, 3),
                                                      'numberPerPurchase': 1,
                                                      'limitPerParty': 1,
                                                      'paidOnly': True,
                                                      'gridAsset': 'PartyDance_activity_3x3'},
                           ActivityIds.PartyValentineDance: {'cost': int(100 * PartyCostMultiplier),
                                                             'gridsize': (3, 3),
                                                             'numberPerPurchase': 1,
                                                             'limitPerParty': 1,
                                                             'paidOnly': True,
                                                             'gridAsset': 'PartyDance_activity_3x3'},
                           ActivityIds.PartyValentineDance20: {'cost': int(200 * PartyCostMultiplier),
                                                               'gridsize': (3, 3),
                                                               'numberPerPurchase': 1,
                                                               'limitPerParty': 1,
                                                               'paidOnly': True,
                                                               'gridAsset': 'PartyDance_activity_3x3'},
                           ActivityIds.PartyTugOfWar: {'cost': int(200 * PartyCostMultiplier),
                                                       'gridsize': (4, 4),
                                                       'numberPerPurchase': 1,
                                                       'limitPerParty': 1,
                                                       'paidOnly': False,
                                                       'gridAsset': 'PartyTufOfWar_activity_4x4'},
                           ActivityIds.PartyFireworks: {'cost': int(200 * PartyCostMultiplier),
                                                        'gridsize': (4, 2),
                                                        'numberPerPurchase': 1,
                                                        'limitPerParty': 1,
                                                        'paidOnly': False,
                                                        'gridAsset': 'PartyFireworks_activity_2x4'},
                           ActivityIds.PartyClock: {'cost': MinimumPartyCost,
                                                    'gridsize': (1, 1),
                                                    'numberPerPurchase': 1,
                                                    'limitPerParty': 1,
                                                    'paidOnly': False,
                                                    'gridAsset': 'PartyClock_activity_1x1'}}
DecorationInformationDict = {DecorationIds.BalloonAnvil: {'cost': int(10 * PartyCostMultiplier),
                                                          'gridsize': (1, 1),
                                                          'numberPerPurchase': 1,
                                                          'limitPerParty': 5,
                                                          'paidOnly': False,
                                                          'gridAsset': 'decoration_1x1'},
                             DecorationIds.BalloonAnvilValentine: {'cost': int(10 * PartyCostMultiplier),
                                                                   'gridsize': (1, 1),
                                                                   'numberPerPurchase': 1,
                                                                   'limitPerParty': 5,
                                                                   'paidOnly': False,
                                                                   'gridAsset': 'decoration_1x1'},
                             DecorationIds.BalloonStage: {'cost': int(25 * PartyCostMultiplier),
                                                          'gridsize': (1, 1),
                                                          'numberPerPurchase': 1,
                                                          'limitPerParty': 5,
                                                          'paidOnly': False,
                                                          'gridAsset': 'decoration_1x1'},
                             DecorationIds.Bow: {'cost': int(10 * PartyCostMultiplier),
                                                 'gridsize': (1, 1),
                                                 'numberPerPurchase': 1,
                                                 'limitPerParty': 5,
                                                 'paidOnly': False,
                                                 'gridAsset': 'decoration_1x1'},
                             DecorationIds.Cake: {'cost': int(10 * PartyCostMultiplier),
                                                  'gridsize': (1, 1),
                                                  'numberPerPurchase': 1,
                                                  'limitPerParty': 5,
                                                  'paidOnly': False,
                                                  'gridAsset': 'decoration_1x1'},
                             DecorationIds.Castle: {'cost': int(25 * PartyCostMultiplier),
                                                    'gridsize': (1, 1),
                                                    'numberPerPurchase': 1,
                                                    'limitPerParty': 5,
                                                    'paidOnly': False,
                                                    'gridAsset': 'decoration_1x1'},
                             DecorationIds.GiftPile: {'cost': int(10 * PartyCostMultiplier),
                                                      'gridsize': (1, 1),
                                                      'numberPerPurchase': 1,
                                                      'limitPerParty': 5,
                                                      'paidOnly': False,
                                                      'gridAsset': 'decoration_1x1'},
                             DecorationIds.Horn: {'cost': int(10 * PartyCostMultiplier),
                                                  'gridsize': (1, 1),
                                                  'numberPerPurchase': 1,
                                                  'limitPerParty': 5,
                                                  'paidOnly': False,
                                                  'gridAsset': 'decoration_1x1'},
                             DecorationIds.MardiGras: {'cost': int(25 * PartyCostMultiplier),
                                                       'gridsize': (1, 1),
                                                       'numberPerPurchase': 1,
                                                       'limitPerParty': 5,
                                                       'paidOnly': False,
                                                       'gridAsset': 'decoration_1x1'},
                             DecorationIds.NoiseMakers: {'cost': int(10 * PartyCostMultiplier),
                                                         'gridsize': (1, 1),
                                                         'numberPerPurchase': 1,
                                                         'limitPerParty': 5,
                                                         'paidOnly': False,
                                                         'gridAsset': 'decoration_1x1'},
                             DecorationIds.Pinwheel: {'cost': int(10 * PartyCostMultiplier),
                                                      'gridsize': (1, 1),
                                                      'numberPerPurchase': 1,
                                                      'limitPerParty': 5,
                                                      'paidOnly': False,
                                                      'gridAsset': 'decoration_1x1'},
                             DecorationIds.GagGlobe: {'cost': int(25 * PartyCostMultiplier),
                                                      'gridsize': (1, 1),
                                                      'numberPerPurchase': 1,
                                                      'limitPerParty': 5,
                                                      'paidOnly': False,
                                                      'gridAsset': 'decoration_1x1'},
                             DecorationIds.BannerJellyBean: {'cost': int(25 * PartyCostMultiplier),
                                                             'gridsize': (1, 1),
                                                             'numberPerPurchase': 1,
                                                             'limitPerParty': 5,
                                                             'paidOnly': False,
                                                             'gridAsset': 'decoration_1x1'},
                             DecorationIds.CakeTower: {'cost': int(25 * PartyCostMultiplier),
                                                       'gridsize': (1, 1),
                                                       'numberPerPurchase': 1,
                                                       'limitPerParty': 5,
                                                       'paidOnly': False,
                                                       'gridAsset': 'decoration_1x1'},
                             DecorationIds.HeartTarget: {'cost': int(25 * PartyCostMultiplier),
                                                         'gridsize': (1, 1),
                                                         'numberPerPurchase': 1,
                                                         'limitPerParty': 5,
                                                         'paidOnly': False,
                                                         'gridAsset': 'decoration_1x1'},
                             DecorationIds.HeartBanner: {'cost': int(25 * PartyCostMultiplier),
                                                         'gridsize': (1, 1),
                                                         'numberPerPurchase': 1,
                                                         'limitPerParty': 5,
                                                         'paidOnly': False,
                                                         'gridAsset': 'decoration_1x1'},
                             DecorationIds.FlyingHeart: {'cost': int(25 * PartyCostMultiplier),
                                                         'gridsize': (1, 1),
                                                         'numberPerPurchase': 1,
                                                         'limitPerParty': 5,
                                                         'paidOnly': False,
                                                         'gridAsset': 'decoration_1x1'},
                             DecorationIds.Hydra: {'cost': int(25 * PartyCostMultiplier),
                                                   'gridsize': (2, 2),
                                                   'numberPerPurchase': 1,
                                                   'limitPerParty': 5,
                                                   'paidOnly': False,
                                                   'gridAsset': 'decoration_propStage_2x2'},
                             DecorationIds.BannerVictory: {'cost': int(25 * PartyCostMultiplier),
                                                           'gridsize': (1, 1),
                                                           'numberPerPurchase': 1,
                                                           'limitPerParty': 5,
                                                           'paidOnly': False,
                                                           'gridAsset': 'decoration_1x1'},
                             DecorationIds.CannonVictory: {'cost': int(25 * PartyCostMultiplier),
                                                           'gridsize': (1, 1),
                                                           'numberPerPurchase': 1,
                                                           'limitPerParty': 5,
                                                           'paidOnly': False,
                                                           'gridAsset': 'decoration_1x1'},
                             DecorationIds.CogStatueVictory: {'cost': int(25 * PartyCostMultiplier),
                                                              'gridsize': (1, 1),
                                                              'numberPerPurchase': 1,
                                                              'limitPerParty': 5,
                                                              'paidOnly': False,
                                                              'gridAsset': 'decoration_1x1'},
                             DecorationIds.TubeCogVictory: {'cost': int(25 * PartyCostMultiplier),
                                                            'gridsize': (1, 1),
                                                            'numberPerPurchase': 1,
                                                            'limitPerParty': 5,
                                                            'paidOnly': False,
                                                            'gridAsset': 'decoration_1x1'},
                             DecorationIds.cogIceCreamVictory: {'cost': int(25 * PartyCostMultiplier),
                                                                'gridsize': (1, 1),
                                                                'numberPerPurchase': 1,
                                                                'limitPerParty': 5,
                                                                'paidOnly': False,
                                                                'gridAsset': 'decoration_1x1'},
                             DecorationIds.cogIceCreamWinter: {'cost': int(25 * PartyCostMultiplier),
                                                               'gridsize': (1, 1),
                                                               'numberPerPurchase': 1,
                                                               'limitPerParty': 5,
                                                               'paidOnly': False,
                                                               'gridAsset': 'decoration_1x1'},
                             DecorationIds.StageWinter: {'cost': int(25 * PartyCostMultiplier),
                                                         'gridsize': (2, 2),
                                                         'numberPerPurchase': 1,
                                                         'limitPerParty': 5,
                                                         'paidOnly': False,
                                                         'gridAsset': 'decoration_propStage_2x2'},
                             DecorationIds.CogStatueWinter: {'cost': int(25 * PartyCostMultiplier),
                                                             'gridsize': (1, 1),
                                                             'numberPerPurchase': 1,
                                                             'limitPerParty': 5,
                                                             'paidOnly': False,
                                                             'gridAsset': 'decoration_1x1'},
                             DecorationIds.snowman: {'cost': int(25 * PartyCostMultiplier),
                                                     'gridsize': (1, 1),
                                                     'numberPerPurchase': 1,
                                                     'limitPerParty': 5,
                                                     'paidOnly': False,
                                                     'gridAsset': 'decoration_1x1'},
                             DecorationIds.snowDoodle: {'cost': int(25 * PartyCostMultiplier),
                                                        'gridsize': (1, 1),
                                                        'numberPerPurchase': 1,
                                                        'limitPerParty': 5,
                                                        'paidOnly': False,
                                                        'gridAsset': 'decoration_1x1'},
                             DecorationIds.skybox_ttc: {'cost': int(0 * PartyCostMultiplier),
                                                        'gridsize': (1, 1),
                                                        'numberPerPurchase': 1,
                                                        'limitPerParty': 1,
                                                        'paidOnly': False,
                                                        'gridAsset': 'decoration_1x1'},
                             DecorationIds.skybox_mml: {'cost': int(500 * PartyCostMultiplier),
                                                        'gridsize': (1, 1),
                                                        'numberPerPurchase': 1,
                                                        'limitPerParty': 1,
                                                        'paidOnly': False,
                                                        'gridAsset': 'decoration_1x1'},
                             DecorationIds.skybox_br: {'cost': int(500 * PartyCostMultiplier),
                                                       'gridsize': (1, 1),
                                                       'numberPerPurchase': 1,
                                                       'limitPerParty': 1,
                                                       'paidOnly': False,
                                                       'gridAsset': 'decoration_1x1'},
                             DecorationIds.skybox_ddl: {'cost': int(500 * PartyCostMultiplier),
                                                        'gridsize': (1, 1),
                                                        'numberPerPurchase': 1,
                                                        'limitPerParty': 1,
                                                        'paidOnly': False,
                                                        'gridAsset': 'decoration_1x1'},
                             DecorationIds.skybox_hw: {'cost': int(500 * PartyCostMultiplier),
                                                       'gridsize': (1, 1),
                                                       'numberPerPurchase': 1,
                                                       'limitPerParty': 1,
                                                       'paidOnly': False,
                                                       'gridAsset': 'decoration_1x1'},
                             DecorationIds.skybox_sbhq: {'cost': int(500 * PartyCostMultiplier),
                                                         'gridsize': (1, 1),
                                                         'numberPerPurchase': 1,
                                                         'limitPerParty': 1,
                                                         'paidOnly': False,
                                                         'gridAsset': 'decoration_1x1'},
                             DecorationIds.skybox_sbhq2003: {'cost': int(500 * PartyCostMultiplier),
                                                             'gridsize': (1, 1),
                                                             'numberPerPurchase': 1,
                                                             'limitPerParty': 1,
                                                             'paidOnly': False,
                                                             'gridAsset': 'decoration_1x1'},
                             DecorationIds.skybox_bbhq: {'cost': int(500 * PartyCostMultiplier),
                                                         'gridsize': (1, 1),
                                                         'numberPerPurchase': 1,
                                                         'limitPerParty': 1,
                                                         'paidOnly': False,
                                                         'gridAsset': 'decoration_1x1'}}
DefaultRulesTimeout = 10.0


class DenialReasons(IntEnum):
    Default = 0
    Full = 1
    SilentFail = 2
    Transformation = 3


class FireworkShows(IntEnum):
    Summer = 200


FireworksGlobalXOffset = 160.0
FireworksGlobalYOffset = -20.0
FireworksPostLaunchDelay = 5.0
RocketSoundDelay = 2.0
RocketDirectionDelay = 2.0
FireworksStartedEvent = 'PartyFireworksStarted'
FireworksFinishedEvent = 'PartyFireworksFinished'
FireworksTransitionToDisabledDelay = 3.0


class TeamActivityTeams(IntEnum):
    LeftTeam = 0
    RightTeam = 1


TeamActivityNeitherTeam = 3
TeamActivityTextScale = 0.135
TeamActivityStartDelay = 8.0
TeamActivityClientWaitDelay = 30.0
TeamActivityDefaultMinPlayersPerTeam = 1
TeamActivityDefaultMaxPlayersPerTeam = 4
TeamActivityDefaultDuration = 60.0
TeamActivityDefaultConclusionDuration = 4.0
TeamActivityStatusColor = VBase4(1.0, 1.0, 0.65, 1.0)
CogActivityBalanceTeams = True
CogActivityStartDelay = 15.0
CogActivityConclusionDuration = 12
CogActivityDuration = 90
CogActivityMinPlayersPerTeam = 1
CogActivityMaxPlayersPerTeam = 4
CogActivityColors = (VBase4(0.22, 0.4, 0.98, 1.0), VBase4(1.0, 0.43, 0.04, 1.0))
CogActivitySplatColorBase = VBase4(0.98, 0.9, 0.094, 1.0)
CogActivitySplatColors = (
    VBase4(CogActivityColors[0][0] / CogActivitySplatColorBase[0], CogActivityColors[0][1] / CogActivitySplatColorBase[1], CogActivityColors[0][2] / CogActivitySplatColorBase[2],
           1.0),
    VBase4(CogActivityColors[1][0] / CogActivitySplatColorBase[0], CogActivityColors[1][1] / CogActivitySplatColorBase[1], CogActivityColors[1][2] / CogActivitySplatColorBase[2],
           1.0))
CogPinataHeadZ = 4.7
CogActivityHitPoints = 1
CogActivityHitPointsForHead = 3
CogPinataPushBodyFactor = 0.05
CogPinataPushHeadFactor = CogPinataPushBodyFactor * abs(CogActivityHitPointsForHead - CogActivityHitPoints)
CogActivityAvgBeansPerSecond = 0.15
CogActivityBeansToAward = round(CogActivityAvgBeansPerSecond * CogActivityDuration * 2.0)
CogActivityWinBeans = int(round(CogActivityBeansToAward * 0.6))
CogActivityLossBeans = int(round(CogActivityBeansToAward * 0.4))
CogActivityTieBeans = int(round(CogActivityBeansToAward * 0.4))
CogActivityPerfectWinBeans = int(round(CogActivityBeansToAward * 0.75))
CogActivityPerfectLossBeans = int(round(CogActivityBeansToAward * 0.25))
CogActivityArenaLength = 50.0
CogActivityPieMinDist = 0.0
CogActivityPieMaxDist = 110.0
CogActivityPowerMeterHeight = 0.4
CogActivityPowerMeterWidth = 0.1
CogActivityPowerMeterPos = (0.33, 0.0, 0.0)
CogActivityPowerMeterTextPos = (0.33, -0.26)
CogActivityVictoryBarPos = (-0.55, 0.0, 0.825)
CogActivityVictoryBarOrangePos = (0.1725, 0.0, -0.0325)
CogActivityVictoryBarPiePos = (0.47, 0.0, -0.015)
CogActivityVictoryBarArrow = (0.0, 0.0, 0.1)
CogActivityBarUnitScale = 1.1
CogActivityBarStartScale = CogActivityBarUnitScale * 5
CogActivityBarPieUnitMove = 0.07
CogActivityBarPieScale = 1.5
CogActivityScorePos = (-0.0833334, 0.55)
CogActivityScoreTitle = (-0.0933334, 0.5)
CogActivityPowerMeterTime = 1.0
CogActivityShortThrowTime = 0.1
ToonAttackIdleThreshold = 5.0
ToonMoveIdleThreshold = 5.0
CogActivityShortThrowSpam = 3
CogActivitySpamWarningShowTime = 5.0
CogActivityControlsShowTime = 2.0
PARTY_COG_CUTOFF = 60
TugOfWarStartDelay = 8.0
TugOfWarReadyDuration = 1.5
TugOfWarGoDuration = 0.75
TugOfWarDuration = 40.0
TugOfWarMinimumPlayersPerTeam = 1
TugOfWarMaximumPlayersPerTeam = 4
TugOfWarStartGameTimeout = 8
TugOfWarJoinCollisionEndPoints = [Point3(6.0, 0.0, 0.0), Point3(-6.0, 0.0, 0.0)]
TugOfWarJoinCollisionRadius = 1.75
TugOfWarJoinCollisionPositions = [Point3(-10.5, 0.25, 4.5), Point3(10.5, -0.25, 4.5)]
TugOfWarInitialToonPositionsXOffset = 8.0
TugOfWarToonPositionXSeparation = 2.0
TugOfWarToonPositionZ = 2.55
TugOfWarTextWordScale = 0.135
TugOfWarTextCountdownScale = 4.0
TugOfWarCameraPos = Point3(0.0, -33.0, 10.0)
TugOfWarCameraInitialHpr = Point3(0.0, -6.91123, 0.0)
TugOfWarCameraLookAtHeightOffset = 6.0
TugOfWarPowerMeterSize = 17
TugOfWarPowerMeterRulesTarget = 8
TugOfWarDisabledArrowColor = VBase4(1.0, 0.0, 0.0, 0.3)
TugOfWarEnabledArrowColor = VBase4(1.0, 0.0, 0.0, 1.0)
TugOfWarHilightedArrowColor = VBase4(1.0, 0.7, 0.0, 1.0)
TugOfWarTargetRateList = [(8.0, 6),
                          (5.0, 7),
                          (6.0, 8),
                          (6.0, 10),
                          (7.0, 11),
                          (8.0, 12)]
TugOfWarKeyPressTimeToLive = 1.0
TugOfWarKeyPressUpdateRate = 0.1
TugOfWarKeyPressReportRate = 0.2
TugOfWarMovementFactor = 0.03
TugOfWarSplashZOffset = 1.0
TugOfWarHeadings = [240.0, 120.0]
TugOfWarConclusionDuration = 4.0
TugOfWarFallInWinReward = 15
TugOfWarFallInLossReward = 4
TugOfWarWinReward = 12
TugOfWarLossReward = 8
TugOfWarTieReward = 5
TugOfWarTieThreshold = 0.75
TrampolineDuration = 60.0
TrampolineSignOffset = Point3(-6.0, -6.0, 0.0)
TrampolineLeverOffset = Point3(-5.0, -9.0, 0.0)
TrampolineNumJellyBeans = 12
TrampolineJellyBeanBonus = 10
CatchActivityDuration = 80
CatchActivityBitmask = BitMask32(16)
CatchLeverOffset = Point3(-3.0, -2.0, 0.0)
CatchDropShadowHeight = 0.5
CatchConclusionDuration = 3.0


class DropObject:

    def __init__(self, name, good, onscreenDurMult, modelPath):
        self.name = name
        self.good = good
        self.onscreenDurMult = onscreenDurMult
        self.modelPath = modelPath

    def isBaseline(self):
        return self.onscreenDurMult == 1.0


DropObjectTypes = [DropObject('apple', 1, 1.0, 'phase_4/models/minigames/apple'),
                   DropObject('orange', 1, 1.0, 'phase_4/models/minigames/orange'),
                   DropObject('pear', 1, 1.0, 'phase_4/models/minigames/pear'),
                   DropObject('coconut', 1, 1.0, 'phase_4/models/minigames/coconut'),
                   DropObject('watermelon', 1, 1.0, 'phase_4/models/minigames/watermelon'),
                   DropObject('pineapple', 1, 1.0, 'phase_4/models/minigames/pineapple'),
                   DropObject('anvil', 0, 0.4, 'phase_4/models/props/anvil-mod')]
Name2DropObjectType = {}
for type in DropObjectTypes:
    Name2DropObjectType[type.name] = type

Name2DOTypeId = {}
names = list(Name2DropObjectType.keys())
names.sort()
for i in range(len(names)):
    Name2DOTypeId[names[i]] = i

DOTypeId2Name = names
NumFruits = [{2000: 18,
              1000: 19,
              5000: 22,
              4000: 24,
              3000: 27,
              9000: 28,
              21000: 18,
              22000: 22,
              23000: 24,
              24000: 28,
              25000: 27,
              26000: 19},
             {2000: 30,
              1000: 33,
              5000: 38,
              4000: 42,
              3000: 46,
              9000: 50,
              21000: 30,
              22000: 38,
              23000: 42,
              24000: 50,
              25000: 46,
              26000: 33},
             {2000: 42,
              1000: 48,
              5000: 54,
              4000: 60,
              3000: 66,
              9000: 71,
              21000: 42,
              22000: 54,
              23000: 60,
              24000: 71,
              25000: 66,
              26000: 48},
             {2000: 56,
              1000: 63,
              5000: 70,
              4000: 78,
              3000: 85,
              9000: 92,
              21000: 56,
              22000: 70,
              23000: 78,
              24000: 92,
              25000: 85,
              26000: 63}]
DancePatternToAnims = {'dduu': 'slip-backward',
                       'ldddud': 'happy-dance',
                       'lll': 'left',
                       'rdu': 'struggle',
                       'rrr': 'right',
                       'rulu': 'running-jump',
                       'udlr': 'good-putt',
                       'udllrr': 'victory',
                       'ulu': 'jump',
                       'uudd': 'slip-forward'}
DancePatternToAnims20 = {'ddd': 'down',
                         'dduu': 'slip-backward',
                         'drul': 'sad-walk',
                         'ldr': 'push',
                         'ldddud': 'happy-dance',
                         'ldu': 'sprinkle-dust',
                         'lll': 'left',
                         'llrr': 'firehose',
                         'lrlr': 'wave',
                         'rdu': 'struggle',
                         'rlrl': 'confused',
                         'rrr': 'right',
                         'rulu': 'running-jump',
                         'uddd': 'reel-neutral',
                         'udlr': 'good-putt',
                         'udud': 'angry',
                         'udllrr': 'victory',
                         'ulu': 'jump',
                         'uudd': 'slip-forward',
                         'uuu': 'up'}
DanceAnimToName = {'right': TTLocalizer.DanceAnimRight,
                   'reel-neutral': TTLocalizer.DanceAnimReelNeutral,
                   'conked': TTLocalizer.DanceAnimConked,
                   'happy-dance': TTLocalizer.DanceAnimHappyDance,
                   'confused': TTLocalizer.DanceAnimConfused,
                   'walk': TTLocalizer.DanceAnimWalk,
                   'jump': TTLocalizer.DanceAnimJump,
                   'firehose': TTLocalizer.DanceAnimFirehose,
                   'shrug': TTLocalizer.DanceAnimShrug,
                   'slip-forward': TTLocalizer.DanceAnimSlipForward,
                   'sad-walk': TTLocalizer.DanceAnimSadWalk,
                   'wave': TTLocalizer.DanceAnimWave,
                   'struggle': TTLocalizer.DanceAnimStruggle,
                   'running-jump': TTLocalizer.DanceAnimRunningJump,
                   'slip-backward': TTLocalizer.DanceAnimSlipBackward,
                   'down': TTLocalizer.DanceAnimDown,
                   'up': TTLocalizer.DanceAnimUp,
                   'good-putt': TTLocalizer.DanceAnimGoodPutt,
                   'victory': TTLocalizer.DanceAnimVictory,
                   'push': TTLocalizer.DanceAnimPush,
                   'angry': TTLocalizer.DanceAnimAngry,
                   'left': TTLocalizer.DanceAnimLeft}
DanceReverseLoopAnims = ['left',
                         'right',
                         'up',
                         'down']


class ToonDancingStates(IntEnum):
    DanceMove = 0
    Run = 1


JUKEBOX_TIMEOUT = 60.0
MUSIC_PATH = 'phase_%s/audio/bgm/'
MUSIC_MIN_LENGTH_SECONDS = 50.0
MUSIC_GAP = 2.5
LOOP_GAP = 0.5
PhaseToMusicData = {3.5: {'TC_SZ.ogg': [TTLocalizer.MusicTcSz, 57]},
                    3: {'create_a_toon.ogg': [TTLocalizer.MusicCreateAToon, 175],
                        'tt_theme.ogg': [TTLocalizer.MusicTtTheme, 51]},
                    4: {'TC_nbrhood.ogg': [TTLocalizer.MusicTcNbrhood, 59],
                        'MG_TwoDGame.ogg': [TTLocalizer.MusicMgTwodgame, 60],
                        'MG_Vine.ogg': [TTLocalizer.MusicMgVine, 32],
                        'FF_safezone.ogg': [TTLocalizer.MusicFfSafezone, 47]},
                    6: {'DD_SZ.ogg': [TTLocalizer.MusicDdSz, 33],
                        'GS_SZ.ogg': [TTLocalizer.MusicGsSz, 60],
                        'OZ_SZ.ogg': [TTLocalizer.MusicOzSz, 31],
                        'GZ_SZ.ogg': [TTLocalizer.MusicGzSz, 59],
                        'MM_SZ.ogg': [TTLocalizer.MusicMmSz, 76]},
                    8: {'DG_SZ.ogg': [TTLocalizer.MusicDgSz, 48],
                        'DL_SZ.ogg': [TTLocalizer.MusicDlSz, 33],
                        'TB_SZ.ogg': [TTLocalizer.MusicTbSz, 54]},
                    9: {'encntr_hall_of_fame.ogg': [TTLocalizer.MusicEncntrHallOfFame, 51],
                        'encntr_head_suit_theme.ogg': [TTLocalizer.MusicEncntrHeadSuitTheme, 29]},
                    11: {'ttrm_s_ara_bgm_lbhq_facilitylobby': [TTLocalizer.MusicLbFacilityLobbyBg, 101],
                         'ttrm_s_ara_bgm_lbhq_facility': [TTLocalizer.MusicLbFacility, 49],
                         'ttrm_s_ara_bgm_encntr_lbhq_facility': [TTLocalizer.MusicLbFacilityBattle, 72],
                         'ttrm_s_ara_bgm_lbhq_bosslobby.ogg': [TTLocalizer.MusicLbBossLobbyBg, 33],
                         'ttrm_s_ara_bgm_encntr_lbhq_boss_round1.ogg': [TTLocalizer.MusicLbBarExamBg, 69],
                         'LB_juryBG.ogg': [TTLocalizer.MusicLbJurybg, 30],
                         'ttrm_s_ara_bgm_encntr_lbhq_boss_round3.ogg': [TTLocalizer.MusicLbTrialBg, 114]},
                    13: {'party_original_theme.ogg': [TTLocalizer.MusicPartyOriginalTheme, 56],
                         'party_generic_theme_jazzy.ogg': [TTLocalizer.MusicPartyGenericThemeJazzy, 64]}}
PhaseToMusicData40 = {3.5: {'encntr_general_bg.ogg': [TTLocalizer.MusicEncntrGeneralBg, 30],
                            'TC_SZ.ogg': [TTLocalizer.MusicTcSz, 57]},
                      3: {'create_a_toon.ogg': [TTLocalizer.MusicCreateAToon, 175],
                          'tt_theme.ogg': [TTLocalizer.MusicTtTheme, 51]},
                      4: {'minigame_race.ogg': [TTLocalizer.MusicMinigameRace, 77],
                          'TC_nbrhood.ogg': [TTLocalizer.MusicTcNbrhood, 59],
                          'MG_TwoDGame.ogg': [TTLocalizer.MusicMgTwodgame, 60],
                          'MG_CogThief.ogg': [TTLocalizer.MusicMgCogthief, 61],
                          'MG_Vine.ogg': [TTLocalizer.MusicMgVine, 32],
                          'MG_IceGame.ogg': [TTLocalizer.MusicMgIcegame, 56],
                          'FF_safezone.ogg': [TTLocalizer.MusicFfSafezone, 47]},
                      6: {'DD_SZ.ogg': [TTLocalizer.MusicDdSz, 33],
                          'GZ_PlayGolf.ogg': [TTLocalizer.MusicGzPlaygolf, 61],
                          'GS_SZ.ogg': [TTLocalizer.MusicGsSz, 60],
                          'OZ_SZ.ogg': [TTLocalizer.MusicOzSz, 31],
                          'GS_Race_CC.ogg': [TTLocalizer.MusicGsRaceCc, 58],
                          'GS_Race_SS.ogg': [TTLocalizer.MusicGsRaceSs, 61],
                          'GS_Race_RR.ogg': [TTLocalizer.MusicGsRaceRr, 60],
                          'GZ_SZ.ogg': [TTLocalizer.MusicGzSz, 59],
                          'MM_SZ.ogg': [TTLocalizer.MusicMmSz, 76],
                          'DD_nbrhood.ogg': [TTLocalizer.MusicDdNbrhood, 67],
                          'GS_KartShop.ogg': [TTLocalizer.MusicGsKartshop, 32]},
                      7: {'encntr_general_bg_indoor.ogg': [TTLocalizer.MusicEncntrGeneralBgIndoor, 31],
                          'encntr_suit_winning_indoor.ogg': [TTLocalizer.MusicEncntrGeneralSuitWinningIndoor, 36]},
                      8: {'DL_nbrhood.ogg': [TTLocalizer.MusicDlNbrhood, 30],
                          'DG_SZ.ogg': [TTLocalizer.MusicDgSz, 48],
                          'DL_SZ.ogg': [TTLocalizer.MusicDlSz, 33],
                          'TB_SZ.ogg': [TTLocalizer.MusicTbSz, 54]},
                      9: {'encntr_hall_of_fame.ogg': [TTLocalizer.MusicEncntrHallOfFame, 51],
                          'CHQ_FACT_bg.ogg': [TTLocalizer.MusicChqFactBg, 50],
                          'encntr_suit_winning.ogg': [TTLocalizer.MusicEncntrSuitWinning, 31],
                          'encntr_head_suit_theme.ogg': [TTLocalizer.MusicEncntrHeadSuitTheme, 29]},
                      11: {'LB_juryBG.ogg': [TTLocalizer.MusicLbJurybg, 30],
                           'LB_courtyard.ogg': [TTLocalizer.MusicLbCourtyard, 32]},
                      12: {'Bossbot_Factory_v1.ogg': [TTLocalizer.MusicBossbotFactoryV1, 30],
                           'BossBot_CEO_v1.ogg': [TTLocalizer.MusicBossbotCeoV1, 31]},
                      13: {'party_original_theme.ogg': [TTLocalizer.MusicPartyOriginalTheme, 56],
                           'party_polka_dance.ogg': [TTLocalizer.MusicPartyPolkaDance, 63],
                           'party_waltz_dance.ogg': [TTLocalizer.MusicPartyWaltzDance, 63],
                           'party_generic_theme_jazzy.ogg': [TTLocalizer.MusicPartyGenericThemeJazzy, 64]}}
PhaseToMusicData60 = {3.5: {'encntr_general_bg.ogg': [TTLocalizer.MusicEncntrGeneralBg, 30],
                            'TC_SZ.ogg': [TTLocalizer.MusicTcSz, 57]},
                      3: {'create_a_toon.ogg': [TTLocalizer.MusicCreateAToon, 175],
                          'tt_theme.ogg': [TTLocalizer.MusicTtTheme, 51],
                          'ttrm_s_gen_mainTheme_primary.ogg': [TTLocalizer.MusicTTRMThemePrimary, 77],
                          'ttrm_s_gen_mainTheme_secondary.ogg': [TTLocalizer.MusicTTRMThemeSecondary, 77],
                          'ttoff_winter_theme.ogg': [TTLocalizer.MusicTTRMThemeWinter, 63]},
                      4: {'minigame_race.ogg': [TTLocalizer.MusicMinigameRace, 77],
                          'TC_nbrhood.ogg': [TTLocalizer.MusicTcNbrhood, 59],
                          'TC_battle.ogg': [TTLocalizer.MusicTcBattle, 30],
                          'MG_TwoDGame.ogg': [TTLocalizer.MusicMgTwodgame, 60],
                          'MG_CogThief.ogg': [TTLocalizer.MusicMgCogthief, 61],
                          'MG_Vine.ogg': [TTLocalizer.MusicMgVine, 32],
                          'MG_IceGame.ogg': [TTLocalizer.MusicMgIcegame, 56],
                          'FF_safezone.ogg': [TTLocalizer.MusicFfSafezone, 47],
                          'ttoff_s_ara_ttc_nbrhood_halloween.ogg': [TTLocalizer.MusicTcHalloween, 58],
                          'ttoff_s_ara_ttc_nbrhood_winter.ogg': [TTLocalizer.MusicTcWinter, 57]},
                      5.5: {'estate_SZ.ogg': [TTLocalizer.MusicEstate, 63]},
                      6: {'DD_SZ.ogg': [TTLocalizer.MusicDdSz, 33],
                          'GZ_PlayGolf.ogg': [TTLocalizer.MusicGzPlaygolf, 61],
                          'GS_SZ.ogg': [TTLocalizer.MusicGsSz, 60],
                          'OZ_SZ.ogg': [TTLocalizer.MusicOzSz, 31],
                          'GS_Race_CC.ogg': [TTLocalizer.MusicGsRaceCc, 58],
                          'GS_Race_SS.ogg': [TTLocalizer.MusicGsRaceSs, 61],
                          'GS_Race_RR.ogg': [TTLocalizer.MusicGsRaceRr, 60],
                          'GZ_SZ.ogg': [TTLocalizer.MusicGzSz, 59],
                          'MM_SZ.ogg': [TTLocalizer.MusicMmSz, 76],
                          'MM_battle.ogg': [TTLocalizer.MusicMmBattle, 40],
                          'DD_nbrhood.ogg': [TTLocalizer.MusicDdNbrhood, 67],
                          'DD_battle.ogg': [TTLocalizer.MusicDdBattle, 30],
                          'GS_KartShop.ogg': [TTLocalizer.MusicGsKartshop, 32]},
                      7: {'encntr_general_bg_indoor.ogg': [TTLocalizer.MusicEncntrGeneralBgIndoor, 31],
                          'encntr_suit_winning_indoor.ogg': [TTLocalizer.MusicEncntrGeneralSuitWinningIndoor, 36]},
                      8: {'DL_nbrhood.ogg': [TTLocalizer.MusicDlNbrhood, 30],
                          'DG_SZ.ogg': [TTLocalizer.MusicDgSz, 48],
                          'DG_battle.ogg': [TTLocalizer.MusicDgBattle, 30],
                          'DL_SZ.ogg': [TTLocalizer.MusicDlSz, 33],
                          'DL_battle.ogg': [TTLocalizer.MusicDlBattle, 38],
                          'TB_SZ.ogg': [TTLocalizer.MusicTbSz, 54],
                          'TB_battle.ogg': [TTLocalizer.MusicTbBattle, 36]},
                      9: {'encntr_hall_of_fame.ogg': [TTLocalizer.MusicEncntrHallOfFame, 51],
                          'CHQ_FACT_bg.ogg': [TTLocalizer.MusicChqFactBg, 50],
                          'encntr_suit_winning.ogg': [TTLocalizer.MusicEncntrSuitWinning, 31],
                          'encntr_head_suit_theme.ogg': [TTLocalizer.MusicEncntrHeadSuitTheme, 29]},
                      11: {'LB_juryBG.ogg': [TTLocalizer.MusicLbJurybg, 30],
                           'LB_courtyard.ogg': [TTLocalizer.MusicLbCourtyard, 32]},
                      12: {'Bossbot_Factory_v1.ogg': [TTLocalizer.MusicBossbotFactoryV1, 30],
                           'BossBot_CEO_v1.ogg': [TTLocalizer.MusicBossbotCeoV1, 31]},
                      13: {'party_original_theme.ogg': [TTLocalizer.MusicPartyOriginalTheme, 56],
                           'party_polka_dance.ogg': [TTLocalizer.MusicPartyPolkaDance, 63],
                           'party_waltz_dance.ogg': [TTLocalizer.MusicPartyWaltzDance, 63],
                           'party_generic_theme_jazzy.ogg': [TTLocalizer.MusicPartyGenericThemeJazzy, 64]},
                      14: {'DB_nbrhood.ogg': [TTLocalizer.MusicDuckberg, 35],
                           'DB_flythrough.ogg': [TTLocalizer.MusicFlying, 35],
                           'LAB_activate.ogg': [TTLocalizer.MusicChairmanActivation, 152],
                           'LAB_idle.ogg': [TTLocalizer.MusicTtInstaller, 31],
                           'CBHQ_bar.ogg': [TTLocalizer.MusicCogBar, 28],
                           'CBHQ_episode_intro.ogg': [TTLocalizer.MusicShortWorkIntro, 44]},
                      14.5: {'SP_nbrhood_tt.ogg': [TTLocalizer.MusicPartySpNbrhoodTT, 55],
                             'SP_SZ_activity.ogg': [TTLocalizer.MusicPartySpActivity, 66]}}
PhaseToMusicDataSz = {3.5: {'encntr_general_bg.ogg': [TTLocalizer.MusicEncntrGeneralBg, 30],
                            'TC_SZ.ogg': [TTLocalizer.MusicTcSz, 57]},
                      3: {'create_a_toon.ogg': [TTLocalizer.MusicCreateAToon, 175],
                          'tt_theme.ogg': [TTLocalizer.MusicTtTheme, 51],
                          'ttrm_s_gen_mainTheme_primary.ogg': [TTLocalizer.MusicTTRMThemePrimary, 77],
                          'ttrm_s_gen_mainTheme_secondary.ogg': [TTLocalizer.MusicTTRMThemeSecondary, 77],
                          'ttoff_halloween_theme.ogg': [TTLocalizer.MusicTTRMThemeHalloween, 54],
                          'ttoff_winter_theme.ogg': [TTLocalizer.MusicTTRMThemeWinter, 63]},
                      4: {'minigame_race.ogg': [TTLocalizer.MusicMinigameRace, 77],
                          'TC_nbrhood.ogg': [TTLocalizer.MusicTcNbrhood, 59],
                          'TC_battle.ogg': [TTLocalizer.MusicTcBattle, 30],
                          'MG_TwoDGame.ogg': [TTLocalizer.MusicMgTwodgame, 60],
                          'MG_CogThief.ogg': [TTLocalizer.MusicMgCogthief, 61],
                          'MG_Vine.ogg': [TTLocalizer.MusicMgVine, 32],
                          'MG_IceGame.ogg': [TTLocalizer.MusicMgIcegame, 56],
                          'FF_safezone.ogg': [TTLocalizer.MusicFfSafezone, 47],
                          'ttoff_s_ara_ttc_nbrhood_halloween.ogg': [TTLocalizer.MusicTcHalloween, 58],
                          'ttoff_s_ara_ttc_nbrhood_winter.ogg': [TTLocalizer.MusicTcWinter, 57]
                          },
                      5.5: {'estate_SZ.ogg': [TTLocalizer.MusicEstate, 63]},
                      6: {'DD_SZ.ogg': [TTLocalizer.MusicDdSz, 33],
                          'GZ_PlayGolf.ogg': [TTLocalizer.MusicGzPlaygolf, 61],
                          'GS_SZ.ogg': [TTLocalizer.MusicGsSz, 60],
                          'OZ_SZ.ogg': [TTLocalizer.MusicOzSz, 31],
                          'GS_Race_CC.ogg': [TTLocalizer.MusicGsRaceCc, 58],
                          'GS_Race_SS.ogg': [TTLocalizer.MusicGsRaceSs, 61],
                          'GS_Race_RR.ogg': [TTLocalizer.MusicGsRaceRr, 60],
                          'GZ_SZ.ogg': [TTLocalizer.MusicGzSz, 59],
                          'MM_SZ.ogg': [TTLocalizer.MusicMmSz, 76],
                          'MM_battle.ogg': [TTLocalizer.MusicMmBattle, 40],
                          'DD_nbrhood.ogg': [TTLocalizer.MusicDdNbrhood, 67],
                          'DD_battle.ogg': [TTLocalizer.MusicDdBattle, 30],
                          'GS_KartShop.ogg': [TTLocalizer.MusicGsKartshop, 32]},
                      7: {'encntr_general_bg_indoor.ogg': [TTLocalizer.MusicEncntrGeneralBgIndoor, 31],
                          'encntr_suit_winning_indoor.ogg': [TTLocalizer.MusicEncntrGeneralSuitWinningIndoor, 36]},
                      8: {'DL_nbrhood.ogg': [TTLocalizer.MusicDlNbrhood, 30],
                          'DG_SZ.ogg': [TTLocalizer.MusicDgSz, 48],
                          'DG_battle.ogg': [TTLocalizer.MusicDgBattle, 30],
                          'DL_SZ.ogg': [TTLocalizer.MusicDlSz, 33],
                          'DL_battle.ogg': [TTLocalizer.MusicDlBattle, 38],
                          'TB_SZ.ogg': [TTLocalizer.MusicTbSz, 54],
                          'TB_battle.ogg': [TTLocalizer.MusicTbBattle, 36]},
                      9: {'encntr_hall_of_fame.ogg': [TTLocalizer.MusicEncntrHallOfFame, 51],
                          'CHQ_FACT_bg.ogg': [TTLocalizer.MusicChqFactBg, 50],
                          'encntr_suit_winning.ogg': [TTLocalizer.MusicEncntrSuitWinning, 31],
                          'encntr_head_suit_theme.ogg': [TTLocalizer.MusicEncntrHeadSuitTheme, 29],
                          'ttrm_s_ara_sbhq_factoryExterior.ogg': [TTLocalizer.MusicSBHQFactExt, 58],
                          'ttrm_s_ara_bgm_encntr_sbhq_boss_round1.ogg': [TTLocalizer.MusicSBHQBossRound1, 36],
                          'ttrm_s_ara_bgm_encntr_sbhq_boss_round2.ogg': [TTLocalizer.MusicSBHQBossRound2, 39],
                          'ttrm_s_ara_bgm_encntr_sbhq_boss_round3.ogg': [TTLocalizer.MusicSBHQBossRound3, 101]},
                      10: {'ttrm_s_ara_bgm_cbhq.ogg': [TTLocalizer.MusicCBHQ, 65],
                           'ttrm_s_bat_bgm_cbhq.ogg': [TTLocalizer.MusicCBHQBattle, 39],
                           'ttrm_s_ara_bgm_cbhq_facility.ogg': [TTLocalizer.MusicCBHQMint, 57],
                           'ttrm_s_bat_bgm_cbhq_facility.ogg': [TTLocalizer.MusicCBHQMintBattle, 52],
                           'ttrm_s_ara_bgm_cbhq_lobby.ogg': [TTLocalizer.MusicCBHQBossLobby, 105],
                           'ttrm_s_ara_bgm_encntr_cbhq_boss_round1.ogg': [TTLocalizer.MusicCBHQBossRound1, 65],
                           'ttrm_s_ara_bgm_cbhq_boss_round_2.ogg': [TTLocalizer.MusicCBHQBossRound2, 72]},
                      11: {'LB_juryBG.ogg': [TTLocalizer.MusicLbJurybg, 30],
                           'LB_courtyard.ogg': [TTLocalizer.MusicLbCourtyard, 32],
                           'ttoff_s_ara_bgm_lbhq_facility.ogg': [TTLocalizer.MusicLbOfficeBg, 62]},
                      12: {'Bossbot_Factory_v1.ogg': [TTLocalizer.MusicBossbotFactoryV1, 30],
                           'BossBot_CEO_v1.ogg': [TTLocalizer.MusicBossbotCeoV1, 31]},
                      13: {'party_original_theme.ogg': [TTLocalizer.MusicPartyOriginalTheme, 56],
                           'party_polka_dance.ogg': [TTLocalizer.MusicPartyPolkaDance, 63],
                           'party_waltz_dance.ogg': [TTLocalizer.MusicPartyWaltzDance, 63],
                           'party_generic_theme_jazzy.ogg': [TTLocalizer.MusicPartyGenericThemeJazzy, 64]},
                      14: {'DB_nbrhood.ogg': [TTLocalizer.MusicDuckberg, 35],
                           'DB_flythrough.ogg': [TTLocalizer.MusicFlying, 35],
                           'LAB_activate.ogg': [TTLocalizer.MusicChairmanActivation, 152],
                           'LAB_idle.ogg': [TTLocalizer.MusicTtInstaller, 31],
                           'CBHQ_bar.ogg': [TTLocalizer.MusicCogBar, 28],
                           'CBHQ_episode_intro.ogg': [TTLocalizer.MusicShortWorkIntro, 44]},
                      14.5: {'SP_nbrhood_tt.ogg': [TTLocalizer.MusicPartySpNbrhoodTT, 55],
                             'SP_nbrhood_dd.ogg': [TTLocalizer.MusicPartySpNbrhoodDD, 49],
                             'SP_nbrhood_dg.ogg': [TTLocalizer.MusicPartySpNbrhoodDG, 63],
                             'SP_nbrhood_mm.ogg': [TTLocalizer.MusicPartySpNbrhoodMM, 25.03375],
                             'SP_nbrhood_br.ogg': [TTLocalizer.MusicPartySpNbrhoodBR, 54],
                             'SP_nbrhood_dl.ogg': [TTLocalizer.MusicPartySpNbrhoodDL, 35],
                             'SP_SZ_activity.ogg': [TTLocalizer.MusicPartySpActivity, 66],
                             'museum.ogg': [TTLocalizer.MusicMuseum, 35],
                             'cog_pizzeria.ogg': [TTLocalizer.MusicPizzeria, 43],
                             'toon_jazz.ogg': [TTLocalizer.MusicToonJazz, 50],
                             'tt_elevator_winter.ogg': [TTLocalizer.MusicElevatorHoliday, 12],
                             'encntr_suit_winning_indoor_winter.ogg': [TTLocalizer.MusicCogtastropheHoliday, 36],
                             'encntr_general_bg_winter.ogg': [TTLocalizer.MusicBattleHoliday, 30],
                             'encntr_toon_winning_winter.ogg': [TTLocalizer.MusicIntermissionHoliday, 29],
                             'encntr_hall_of_fame_winter.ogg': [TTLocalizer.MusicHallOfFameOriginal, 35],
                             'ttrm_s_ara_blot_void.ogg': [TTLocalizer.MusicVoid, 97]}}


def countMusic():
    numMusic = 0
    for key in PhaseToMusicData:
        numMusic += len(PhaseToMusicData[key])

    print('PhaseToMusicData %d' % numMusic)
    numMusic = 0
    for key in PhaseToMusicData40:
        numMusic += len(PhaseToMusicData40[key])

    print('PhaseToMusicData40 %d' % numMusic)


def getMusicRepeatTimes(length, minLength = MUSIC_MIN_LENGTH_SECONDS):
    times = round(float(minLength) / length)
    if minLength <= 0 or times < 1.0:
        times = 1.0
    return int(times)


def sanitizePhase(phase):
    if phase == int(phase):
        phase = int(phase)
    return phase


CANNON_TIMEOUT = 30
CANNON_MOVIE_LOAD = 1
CANNON_MOVIE_CLEAR = 2
CANNON_MOVIE_FORCE_EXIT = 3
CANNON_MOVIE_LANDED = 4
CannonJellyBeanReward = 2
CannonMaxTotalReward = 200
CatchMaxTotalReward = 1000
PartyCannonCollisions = {'clouds': ['cloudSphere-0'],
                         'bounce': ['wall_collision',
                                    'discoBall_collision',
                                    'platform_left_collision',
                                    'platform_right_collision'],
                         'trampoline_bounce': 'TrampolineCollision',
                         'ground': ['floor_collision',
                                    'danceFloor_collision',
                                    'danceFloorRamp_collision',
                                    'hill_collision',
                                    'fence_floor'],
                         'fence': ['dockTube1_collision',
                                   'dockTube2_collision',
                                   'dockTube2_collision',
                                   'dockTube2_collision',
                                   'palm_collision_01',
                                   'palm_collision_02',
                                   'palm_collision_03',
                                   'wall_1_collision',
                                   'wall_2_collision',
                                   'wall_3_collision',
                                   'wall_4_collision',
                                   'wall_5_collision',
                                   'wall_6_collision',
                                   'tree_collision',
                                   'partyDecoration_collision',
                                   'launchPad_railing_collision',
                                   'launchPad_floor_collision',
                                   'launchPad_collision',
                                   'launchPad_railing2_collision',
                                   'launchPad__rocket_collision',
                                   'launchPad_lever_collision',
                                   'launchPad_bridge_collision',
                                   'launchPad_sphere2_collision',
                                   'launchPad_sphere1_collision',
                                   'partyClock_collision',
                                   'sign_collision']}


def getCostOfParty(partyInfo):
    newCost = 0
    for activityBase in partyInfo.activityList:
        newCost += ActivityInformationDict[activityBase.activityId]['cost']

    for decorBase in partyInfo.decors:
        newCost += DecorationInformationDict[decorBase.decorId]['cost']

    return newCost


PartyId = 0
PartyInfo = 1
PartyInvitees = 2
PartyInviteKey = 3
NoTrashElements = (ActivityIds.PartyClock, DecorationIds.skybox_ttc, DecorationIds.skybox_mml, DecorationIds.skybox_br,
                   DecorationIds.skybox_ddl, DecorationIds.skybox_hw, DecorationIds.skybox_sbhq,
                   DecorationIds.skybox_sbhq2003, DecorationIds.skybox_bbhq)
