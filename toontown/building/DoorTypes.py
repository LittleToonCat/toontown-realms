from enum import Enum

EXT_STANDARD = 1
INT_STANDARD = 2
EXT_HQ = 3
INT_HQ = 4
EXT_HOUSE = 5
INT_HOUSE = 6
EXT_COGHQ = 7
INT_COGHQ = 8
EXT_KS = 9
INT_KS = 10
EXT_ANIM_STANDARD = 11
INT_TUTORIAL = 12


class DoorType(Enum):
    STANDARD = 0
    HQ = 1
    HOUSE = 2
    COGHQ = 3
    KS = 4
    ANIM = 5
    TUTORIAL = 6

