from toontown.episodes import EpisodeLocalizer
from toontown.toonbase import TTLocalizer, ToontownGlobals
from toontown.building.DoorTypes import DoorType

import collections

DEFAULT_EPISODE_ZONE = 0

# 02 SHORT WORK
EP02_CASHBOT_HQ_TRAIN_YARD = 1
EP02_SHORT_CHANGE_OFFICE = 2
EP02_HIGH_RISE_HALLWAY = 3
EP02_HIGH_RISE_BATHROOM = 4
EP02_HIGH_RISE_BAR = 5

# 01 PROLOGUE
EP01_THE_MONEYBIN = 6
EP01_OAK_STREET = 7
EP01_GYROS_LAB = 8

# 00 TESTING GROUNDS
EP00_TESTING_GROUNDS = 9

# 03 STORM SELLBOT
EP03_DAISY_GARDENS = 10
EP03_OAK_STREET = 11
EP03_SELLBOT_HQ = 12
EP03_SELLBOT_TOWERS = 13

# 04 SOS ATW
EP04_INTRO = 14
EP04_SCENE2 = 15
EP04_SCENE3 = 16

# 05 2024 ATW
EP05_INTRO = 17

UNKNOWN = 0
EXTERIOR = 1
INTERIOR = 2

OPEN = 0
COMING_SOON = 1
UNAVAILABLE = 2
HIDDEN = 3
DEV_OPEN = 4

DELAY_MOVIE_STATES = ('doorIn',)

DISPLAYTALK = 0
CHATABSOLUTE = 1

EPISODES = collections.OrderedDict()

EPISODES['testing_grounds'] = {
    'name': EpisodeLocalizer.EpisodeTestingGrounds,
    'desc': EpisodeLocalizer.EpisodeTestingGroundsDesc,
    'thumbnail': 'ttoff_t_gui_epThumb_unknown.png',
    'state': DEV_OPEN,
    'toon': {
        'name': 'Toon',
        'dna': ('dss', 'ms', 'm', 'm', 0, 0, 0, 0, 0, 27, 0, 27, 0, 27)
    },
    'zones': collections.OrderedDict([
        ('Linux Land', EP00_TESTING_GROUNDS)
     ]),
    'zoneId2String': collections.OrderedDict([
        (EP00_TESTING_GROUNDS, 'Linux Land')
    ]),
    'zoneConnections': collections.OrderedDict([
        (EP00_TESTING_GROUNDS, ())
    ]),
    'zoneTypes': collections.OrderedDict([
        (EP00_TESTING_GROUNDS, EXTERIOR)
    ]),
    'zone2Subzone': collections.OrderedDict([
        ('Linux Land', 'Testing Grounds')
    ]),
    'zoneTitleColors': collections.OrderedDict([
        (EP00_TESTING_GROUNDS, (0.2, 0.2, 0.8, 1.0))
    ]),
    'zone2Music': collections.OrderedDict([
        (EP00_TESTING_GROUNDS, 'phase_14.5/audio/bgm/KDM_theme_1.ogg')
    ])
}

EPISODES['prologue'] = {
    'name': EpisodeLocalizer.EpisodePrologue,
    'desc': EpisodeLocalizer.EpisodePrologueDesc,
    'thumbnail': 'ttoff_t_gui_epThumb_prologue.png',
    'state': OPEN,
    'toon': {
        'name': 'Scrooge McDuck',
        'dna': ('oss', 'ms', 's', 'm', 0, 0, 9, 0, 153, 27, 140, 27, 62, 27)
    },
    'zones': collections.OrderedDict([
        ('The Moneybin', EP01_THE_MONEYBIN),
        ('Oak Street', EP01_OAK_STREET),
        ("Gyro's Laboratory", EP01_GYROS_LAB)
     ]),
    'zoneId2String': collections.OrderedDict([
        (EP01_THE_MONEYBIN, ''),
        (EP01_OAK_STREET, 'Oak Street'),
        (EP01_GYROS_LAB, "Gyro's Laboratory")
    ]),
    'zoneConnections': collections.OrderedDict([
        (EP01_THE_MONEYBIN, (EP01_OAK_STREET,)),
        (EP01_OAK_STREET, (EP01_GYROS_LAB,)),
        (EP01_GYROS_LAB, (EP01_OAK_STREET,))
    ]),
    'zoneTypes': collections.OrderedDict([
        (EP01_THE_MONEYBIN, EXTERIOR),
        (EP01_OAK_STREET, EXTERIOR),
        (EP01_GYROS_LAB, INTERIOR)
    ]),
    'zone2Subzone': collections.OrderedDict([
        ('The Moneybin', 'Duckburg'),
        ('Oak Street', 'Daisy Gardens'),
        ("Gyro's Laboratory", 'Daisy Gardens')
    ]),
    'zoneTitleColors': collections.OrderedDict([
        (EP01_THE_MONEYBIN, (0.8, 0.6, 1.0, 1.0)),
        (EP01_OAK_STREET, (0.8, 0.6, 1.0, 1.0)),
        (EP01_GYROS_LAB, (0.8, 0.6, 1.0, 1.0))
    ]),
    'zone2Music': collections.OrderedDict([
        (EP01_THE_MONEYBIN, ''),
        (EP01_OAK_STREET, 'phase_8/audio/bgm/DG_nbrhood.ogg'),
        (EP01_GYROS_LAB, '')
    ]),
    'zoneDoors': {
        EP01_OAK_STREET: ({'doorType': DoorType.STANDARD, 'hoodZone': ToontownGlobals.OakStreetBeta, 'blockVal': True,
                           'bldgZone': ToontownGlobals.GyrosLab, 'intZone': EP01_GYROS_LAB},)
    }
}

EPISODES['short_work'] = {
    'name': EpisodeLocalizer.EpisodeCogHighrise,
    'desc': EpisodeLocalizer.EpisodeCogHighriseDesc,
    'thumbnail': 'ttoff_t_gui_epThumb_shortwork.png',
    'state': OPEN,
    'toon': {
        'name': 'Short Change',
        'dna': ('dss', 'ms', 'm', 'm', 0, 0, 0, 0, 0, 27, 0, 27, 0, 27)
    },
    'zones': collections.OrderedDict([
        ('Cashbot Train Yard', EP02_CASHBOT_HQ_TRAIN_YARD),
        ('Short Change Office', EP02_SHORT_CHANGE_OFFICE),
        ('High Rise Hallway', EP02_HIGH_RISE_HALLWAY),
        ('High Rise Bathroom', EP02_HIGH_RISE_BATHROOM),
        ('High Rise Bar', EP02_HIGH_RISE_BAR)
     ]),
    'zoneId2String': collections.OrderedDict([
        (EP02_CASHBOT_HQ_TRAIN_YARD, 'Cashbot Train Yard'),
        (EP02_SHORT_CHANGE_OFFICE, 'Short Change Office'),
        (EP02_HIGH_RISE_HALLWAY, 'High Rise Hallway'),
        (EP02_HIGH_RISE_BATHROOM, 'High Rise Bathroom'),
        (EP02_HIGH_RISE_BAR, 'High Rise Bar')
    ]),
    'zoneConnections': collections.OrderedDict([
        (EP02_CASHBOT_HQ_TRAIN_YARD, (EP02_SHORT_CHANGE_OFFICE,)),
        (EP02_SHORT_CHANGE_OFFICE, (EP02_HIGH_RISE_HALLWAY,)),
        (EP02_HIGH_RISE_HALLWAY, (EP02_SHORT_CHANGE_OFFICE, EP02_HIGH_RISE_BATHROOM, EP02_HIGH_RISE_BAR)),
        (EP02_HIGH_RISE_BATHROOM, (EP02_HIGH_RISE_HALLWAY,)),
        (EP02_HIGH_RISE_BAR, (EP02_HIGH_RISE_HALLWAY,))
    ]),
    'zoneTypes': collections.OrderedDict([
        (EP02_CASHBOT_HQ_TRAIN_YARD, INTERIOR),
        (EP02_SHORT_CHANGE_OFFICE, INTERIOR),
        (EP02_HIGH_RISE_HALLWAY, INTERIOR),
        (EP02_HIGH_RISE_BATHROOM, INTERIOR),
        (EP02_HIGH_RISE_BAR, INTERIOR)
    ]),
    'zone2Subzone': collections.OrderedDict([
        ('Cashbot Train Yard', 'Cashbot Headquarters'),
        ('Short Change Office', 'Cashbot Headquarters'),
        ('High Rise Hallway', 'Cashbot Headquarters'),
        ('High Rise Bathroom', 'Cashbot Headquarters'),
        ('High Rise Bar', 'Cashbot Headquarters')
    ]),
    'zoneTitleColors': collections.OrderedDict([
        (EP02_CASHBOT_HQ_TRAIN_YARD, (0.5, 0.5, 0.5, 1.0)),
        (EP02_SHORT_CHANGE_OFFICE, (0.5, 0.5, 0.5, 1.0)),
        (EP02_HIGH_RISE_HALLWAY, (0.5, 0.5, 0.5, 1.0)),
        (EP02_HIGH_RISE_BATHROOM, (0.5, 0.5, 0.5, 1.0)),
        (EP02_HIGH_RISE_BAR, (0.5, 0.5, 0.5, 1.0))
    ]),
    'zone2Music': collections.OrderedDict([
        (EP02_CASHBOT_HQ_TRAIN_YARD, 'phase_14/audio/bgm/CBHQ_episode_intro.ogg'),
        (EP02_SHORT_CHANGE_OFFICE, 'phase_9/audio/bgm/CHQ_FACT_bg.ogg'),
        (EP02_HIGH_RISE_HALLWAY, 'phase_9/audio/bgm/CHQ_FACT_bg.ogg'),
        (EP02_HIGH_RISE_BATHROOM, 'phase_9/audio/bgm/CHQ_FACT_bg.ogg'),
        (EP02_HIGH_RISE_BAR, 'phase_14/audio/bgm/CBHQ_bar.ogg')
    ])
}

EPISODES['storm_sellbot'] = {
    'name': EpisodeLocalizer.EpisodeStormSellbot,
    'desc': EpisodeLocalizer.EpisodeStormSellbotDesc,
    'thumbnail': 'ttoff_t_gui_epThumb_unknown.png',
    'state': DEV_OPEN,
    'toon': {
        'name': 'Flippy',
        'dna': ('fss', 'ms', 'm', 'm', 0, 0, 0, 0, 0, 27, 0, 27, 0, 27)
    },
    'zones': collections.OrderedDict([
        ('Playground', EP03_DAISY_GARDENS),
        ('Oak Street', EP03_OAK_STREET),
        ('Sellbot Headquarters', EP03_SELLBOT_HQ),
        ('Sellbot Towers', EP03_SELLBOT_TOWERS)
     ]),
    'zoneId2String': collections.OrderedDict([
        (EP03_DAISY_GARDENS, 'Playground'),
        (EP03_OAK_STREET, 'Oak Street'),
        (EP03_SELLBOT_HQ, 'Sellbot Headquarters'),
        (EP03_SELLBOT_TOWERS, 'Sellbot Towers')
    ]),
    'zoneConnections': collections.OrderedDict([
        (EP03_DAISY_GARDENS, (EP03_OAK_STREET,)),
        (EP03_OAK_STREET, (EP03_SELLBOT_TOWERS,)),
        (EP03_SELLBOT_TOWERS, (EP03_SELLBOT_HQ,)),
        (EP03_SELLBOT_HQ, (EP03_SELLBOT_TOWERS,))
    ]),
    'zoneTypes': collections.OrderedDict([
        (EP03_DAISY_GARDENS, EXTERIOR),
        (EP03_OAK_STREET, EXTERIOR),
        (EP03_SELLBOT_HQ, EXTERIOR),
        (EP03_SELLBOT_TOWERS, INTERIOR)
    ]),
    'zone2Subzone': collections.OrderedDict([
        ('Playground', 'Daisy Gardens'),
        ('Oak Street', 'Daisy Gardens'),
        ('Sellbot Headquarters', 'Sellbot HQ'),
        ('Sellbot Towers', 'Sellbot Headquarters')
    ]),
    'zoneTitleColors': collections.OrderedDict([
        (EP03_DAISY_GARDENS, (0.8, 0.6, 1.0, 1.0)),
        (EP03_OAK_STREET, (0.8, 0.6, 1.0, 1.0)),
        (EP03_SELLBOT_HQ, (0.5, 0.5, 0.5, 1.0)),
        (EP03_SELLBOT_TOWERS, (0.5, 0.5, 0.5, 1.0))
    ]),
    'zone2Music': collections.OrderedDict([
        (EP03_DAISY_GARDENS, 'phase_8/audio/bgm/DG_nbrhood.ogg'),
        (EP03_OAK_STREET, 'phase_8/audio/bgm/DG_SZ.ogg'),
        (EP03_SELLBOT_HQ, 'phase_9/audio/bgm/encntr_suit_HQ_nbrhood.ogg'),
        (EP03_SELLBOT_TOWERS, 'phase_7/audio/bgm/encntr_suit_winning_indoor.ogg')
    ])
}

EPISODES['squirting_flower'] = {
    'name': EpisodeLocalizer.EpisodeSquirtingFlower,
    'desc': EpisodeLocalizer.EpisodeSquirtingFlowerDesc,
    'thumbnail': 'ttoff_t_gui_epThumb_unknown.png',
    'state': HIDDEN,
    'toon': {
        'name': 'Coach Zucchini',
        'dna': ('fls', 'ls', 'm', 'm', 10, 0, 10, 10, 0, 12, 0, 12, 1, 1)
    }
}

EPISODES['atw_sos'] = {
    'name': EpisodeLocalizer.EpisodeATWSos,
    'desc': EpisodeLocalizer.EpisodeATWSosDesc,
    'thumbnail': 'ttoff_t_gui_epThumb_sosAtw.png',
    'state': HIDDEN,
    'toon': {
        'name': 'Flippy',
        'dna': ('dss', 'ms', 'm', 'm', 17, 0, 17, 17, 3, 3, 3, 3, 7, 2)
    },
    'zones': collections.OrderedDict([
        ('Playground', EP04_INTRO),
        ('????', EP04_SCENE2),
        ('?????', EP04_SCENE3)
     ]),
    'zoneId2String': collections.OrderedDict([
        (EP04_INTRO, 'Playground'),
        (EP04_SCENE2, '????'),
        (EP04_SCENE3, '?????')
    ]),
    'zoneConnections': collections.OrderedDict([
        (EP04_INTRO, (EP04_SCENE2,)),
        (EP04_SCENE2, (EP04_SCENE3,)),
        (EP04_SCENE3, ())
    ]),
    'zoneTypes': collections.OrderedDict([
        (EP04_INTRO, EXTERIOR),
        (EP04_SCENE2, EXTERIOR),
        (EP04_SCENE3, INTERIOR)
    ]),
    'zone2Subzone': collections.OrderedDict([
        ('Playground', 'Toontown Central'),
        ('????', 'Toontown Central'),
        ('?????', '??????????????????????')
    ]),
    'zoneTitleColors': collections.OrderedDict([
        (EP04_INTRO, (1.0, 0.5, 0.4, 1.0)),
        (EP04_SCENE2, (1.0, 0.5, 0.4, 1.0)),
        (EP04_SCENE3, (1.0, 0.5, 0.4, 1.0))
    ]),
    'zone2Music': collections.OrderedDict([
        (EP04_INTRO, 'phase_14/audio/bgm/ttoff_s_ara_bgm_thb_nbrhood.ogg'),
        (EP04_SCENE2, 'phase_14/audio/bgm/ttoff_s_ara_bgm_ttc_streetAtw.ogg'),
        (EP04_SCENE3, 'phase_14/audio/bgm/ttoff_s_ara_bgm_ttc_streetAtw.ogg'),
    ])
}


# this next one is the default completion statuses for episodes that will be sent over from the UberDOG
# (ep #, 0/1)
# ep # is just anything that will be associated with the episode
# 0 = False, 1 = True
DefaultEpisodeStatuses = [
    [0, 0],   # test grounds
    [1, 0],   # prologue
    [2, 0],   # short_work
    [3, 0],   # storm_sellbot
    [4, 0],   # atw_sos
    [5, 0]    # atw 2024
]

EpisodeId2Name = {
    0: 'testing_grounds',
    1: 'prologue',
    2: 'short_work',
    3: 'storm_sellbot',
    4: 'atw_sos',
    5: 'atw_2024'
}

EpisodeName2Id = {
    'testing_grounds': 0,
    'prologue': 1,
    'short_work': 2,
    'storm_sellbot': 3,
    'atw_sos': 4,
    'atw_2024': 5
}
