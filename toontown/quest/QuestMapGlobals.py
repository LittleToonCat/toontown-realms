import enum
from enum import Enum

from panda3d.core import Point3

CogInfoPosTable = {
    'ttrm_t_map_ttc_2000': Point3(0, 0, -5),
    'ttrm_t_map_ttc_2100': Point3(-0.3, 0, -0.2),
    'ttrm_t_map_ttc_2200': Point3(0.2, 0, -0.2),
    'ttrm_t_map_ttc_2300': Point3(0.35, 0, -0.2),
    'ttrm_t_map_mml_4100': Point3(0.45, 0, -0.2),
    'ttrm_t_map_mml_4200': Point3(0.3, 0, -0.3),
    'ttrm_t_map_mml_4300': Point3(0.4, 0, -0.2),
    'ttrm_t_map_dod_1100': Point3(0.35, 0, -0.2),
    'ttrm_t_map_dod_1200': Point3(0.3, 0, -0.35),
    'ttrm_t_map_dod_1300': Point3(0.3, 0, -0.25),
    'ttrm_t_map_dga_5100': Point3(0.3, 0, -0.2),
    'ttrm_t_map_dga_5200': Point3(0.3, 0, -0.2),
    'ttrm_t_map_dga_5300': Point3(-0.3, 0, -0.3),
    'ttrm_t_map_tbr_3100':  Point3(0.37, 0, -0.2),
    'ttrm_t_map_tbr_3200':  Point3(0.35, 0, -0.35),
    'ttrm_t_map_tbr_3300':  Point3(0.3, 0, -0.2),
    'ttrm_t_map_ddl_9100': Point3(0.2, 0, -0.2),
    'ttrm_t_map_ddl_9200': Point3(-0.25, 0, -0.2)
    }
HQPosTable = {
    'ttrm_t_map_ttc_2000': Point3(24.6425, 24.8587, 4.00001),
    'ttrm_t_map_ttc_2100': Point3(-55, -350, 0),
    'ttrm_t_map_ttc_2200': Point3(-385, 70, 0),
    'ttrm_t_map_ttc_2300': Point3(490, 140, 0),
    'ttrm_t_map_mml_4100': Point3(-330, -40, 0),
    'ttrm_t_map_mml_4200': Point3(0, 555, 0),
    'ttrm_t_map_mml_4300': Point3(326, 172, 5),
    'ttrm_t_map_dod_1100': Point3(365, 100, 0),
    'ttrm_t_map_dod_1200': Point3(-25, -410, 0),
    'ttrm_t_map_dod_1300': Point3(210, -200, 0),
    'ttrm_t_map_dga_5100': Point3(357.935, 28.45, 0),
    'ttrm_t_map_dga_5200': Point3(345, 150, 0),
    'ttrm_t_map_dga_5300': Point3(-138.597, 77.1236, -0.5),
    'ttrm_t_map_tbr_3100':  Point3(129.737, 51.9612, 0),
    'ttrm_t_map_tbr_3200':  Point3(230, 200, 0),
    'ttrm_t_map_tbr_3300':  Point3(268.052, 228.052, 0),
    'ttrm_t_map_ddl_9100': Point3(-250, -160, 0),
    'ttrm_t_map_ddl_9200': Point3(322.91, -67.1147, 0)
}
GyroPosTable = {'ttrm_t_map_dod_1300': Point3(340, -90, 0)}
FishingSpotPosTable = {
                       'ttrm_t_map_ttc_2000': Point3(0,0,0),
                       'ttrm_t_map_ttc_2100': Point3(4.45088, -658.174, 0.431656),
                       'ttrm_t_map_ttc_2200': Point3(-223.506, 161.474, 0.477789),
                       'ttrm_t_map_ttc_2300': Point3(512.4, -69.9997, 0.485466),
                       'ttrm_t_map_mml_4100': Point3(-570.662, -101.811, 1.9065),
                       'ttrm_t_map_mml_4200': Point3(-205.722, 238.179, 1.92272),
                       'ttrm_t_map_mml_4300': Point3(705.052, -26.4757, 1.93412),
                       'ttrm_t_map_dod_1100': Point3(368.148, -339.916, 0.419537),
                       'ttrm_t_map_dod_1200': Point3(-394.913, -243.085, 0.462966),
                       'ttrm_t_map_dod_1300': Point3(346.219, 88.2058, 0.643978),
                       'ttrm_t_map_dga_5100': Point3(162.961, 57.4756, 0.360527),
                       'ttrm_t_map_dga_5200': Point3(162.961, 113.59, 0.404519),
                       'ttrm_t_map_dga_5300': Point3(120.848, -55.6079, 0.388995),
                       'ttrm_t_map_tbr_3100': Point3(455.445, 15.6579, 0.376913),
                       'ttrm_t_map_tbr_3200': Point3(340.009, 462.856, 0.415845),
                       'ttrm_t_map_tbr_3300': Point3(54.17, 75.405, 0.141113),
                       'ttrm_t_map_ddl_9100': Point3(106.796, -197.427, 0.354809),
                       'ttrm_t_map_ddl_9200': Point3(239.646, -330.58, 0.347881)
                       }
CornerPosTable = {
    'ttrm_t_map_dga_5200': [Point3(781.219727, 476.963623, 0), Point3(-123.380096, -427.636261, 0)],
    'ttrm_t_map_mml_4100': [Point3(-98.880981, 349.36908, 0), Point3(-658.680908, -210.430862, 0)],
    'ttrm_t_map_dod_1300': [Point3(713.403076, 361.576324, 0), Point3(-83.596741, -435.423615, 0)],
    'ttrm_t_map_ttc_2000': [Point3(191.56, 208.044, 0), Point3(-211.647, -195.163, 0)],
    'ttrm_t_map_ddl_9200': [Point3(420.817871, 204.719116, 0), Point3(-220.182007, -436.280853, 0)],
    'ttrm_t_map_tbr_3100': [Point3(535.648132, 267.004578, 0), Point3(59.248276, -209.395325, 0)],
    'ttrm_t_map_tbr_3300': [Point3(461.503418, 467.348511, 0), Point3(-27.896454, -22.051422, 0)],
    'ttrm_t_map_ttc_2200': [Point3(1.816254, 335.417358, 0), Point3(-641.983643, -308.382629, 0)],
    'ttrm_t_map_mml_4200': [Point3(283.292847, 658.077393, 0), Point3(-289.50708, 85.277466, 0)],
    'ttrm_t_map_dod_1200': [Point3(34.281967, -47.717041, 0), Point3(-464.517944, -546.516968, 0)],
    'ttrm_t_map_dod_1100': [Point3(596.439575, 146.409653, 0), Point3(28.039612, -421.990356, 0)],
    'ttrm_t_map_mml_4300': [Point3(801.294067, 430.992218, 0), Point3(-5.505768, -375.807678, 0)],
    'ttrm_t_map_dga_5300': [Point3(203.715881, 429.168274, 0), Point3(-390.284027, -164.83165, 0)],
    'ttrm_t_map_ddl_9100': [Point3(279.354584, 111.658554, 0), Point3(-423.445221, -591.141357, 0)],
    'ttrm_t_map_dga_5100': [Point3(760.089722, 526.236206, 0), Point3(-139.510132, -373.3638, 0)],
    'ttrm_t_map_ttc_2300': [Point3(870.224243, 536.165771, 0), Point3(-89.175751, -423.234344, 0)],
    'ttrm_t_map_ttc_2100': [Point3(161.735336, -59.985107, 0), Point3(-512.664612, -734.385193, 0)],
    'ttrm_t_map_tbr_3200': [Point3(429.647949, 561.224304, 0), Point3(-31.951935, 99.624283, 0)]
}


class LandmarkIcons(Enum):
    TTC = enum.auto()
    GSW = enum.auto()
    DOD = enum.auto()
    DGA = enum.auto()
    MML = enum.auto()
    TBR = enum.auto()
    DDL = enum.auto()
    SBHQ = enum.auto()
    LBHQ = enum.auto()
    CBHQ = enum.auto()  # we dont need a bbhq one yet
    TOONHQ = enum.auto()
    GAGSHOP = enum.auto()
    TROLLEY = enum.auto()
    CLOTHSHOP = enum.auto()
    PETSHOP = enum.auto()
    FISHERMAN = enum.auto()
    PARTYGATE = enum.auto()
    NOICON = enum.auto()


def getIconNodeName(_type):  # type: (LandmarkIcons) -> str
    return f'**/landmark_{_type.name.lower()}'


def isZoneIcon(_type):  # type: (LandmarkIcons) -> bool
    return _type in (LandmarkIcons.TTC, LandmarkIcons.DOD, LandmarkIcons.DGA, LandmarkIcons.MML, LandmarkIcons.TBR,
                     LandmarkIcons.DDL, LandmarkIcons.SBHQ, LandmarkIcons.LBHQ, LandmarkIcons.CBHQ)


# (Name, Icon, World Position)
LandmarkPosTable = {
    'ttrm_t_map_ttc_2000': (
        #('Toon HQ', LandmarkIcons.TOONHQ, Point3(24.6425, 24.8587, 0)),
        #('Fisherman', LandmarkIcons.FISHERMAN, Point3(-68, -2, 0)),
        ('Silly Street\n(to Daisy Gardens)', LandmarkIcons.DGA, Point3(27, -168, 0)),
        ('Loopy Lane\n(to Minnie\'s Melodyland)', LandmarkIcons.MML, Point3(-155, 6, 0)),
        ('Punchline Place\n(to Donald\'s Dock)', LandmarkIcons.DOD, Point3(-42, 109, 0))
    ),

    'ttrm_t_map_ttc_2100': (
        # TTC PLAYGROUND TUNNEL
        #('Playground', LandmarkIcons.TTC, Point3(-60, -114, 0)),
        ## FISHERMAN
        #('Fisherman', LandmarkIcons.FISHERMAN, Point3(11.4, -633, 0))
    )
}
