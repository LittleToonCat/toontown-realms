from enum import IntEnum

from panda3d.core import Point3


class PropHuntRole(IntEnum):
    WAITING = 0
    HUNTER = 1
    PROP = 2
    SPECTATOR = 3


class PropHuntMapInfo:
    Identifier = 0
    Name = 1
    Author = 2


class PropHuntGeom:
    Type = 0
    Path = 1
    Pos = 2
    Hpr = 3
    Scale = 4
    Color = 5


class PropHuntGeomType:
    DNAStorageFile = 'dnastorage'
    DNAFile = 'dnafile'
    Prop = 'prop'
    Model = 'model'

VICTORY_ANIMS = [
    'good-putt',
    'victory',
    'applause'
]


# State Times
LoadMapTimeout = 20
IntroductionLength = 2  # 20 or something for prod
GracePeriodLength = 5  # 60 prod
HuntLength = 300  # 5 min - increase probably

GeomType = 0
GeomPath = 1
GeomPos = 2
GeomHpr = 3
GeomScale = 4
