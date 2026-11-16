from enum import IntEnum
from panda3d.core import Vec4


class BuildLotThemes(IntEnum):
    TTC = 0
    DOD = 1
    DGA = 2
    MML = 3
    TBR = 4
    DDL = 5
    SBHQ = 6
    CBHQ = 7
    LBHQ = 8
    BBHQ = 9
    VOID = 10
    #TTS = 11


CREATION_ERROR_ALREADY_OPEN = 0
CREATION_ERROR_UNKNOWN_THEME = 1
CREATION_ERROR_UNKNOWN_SAVE = 2

RequestCreateErrors = [
    'You already have a lot opened! Close that one before opening a new one.',
    "You selected an unknown theme. (You shouldn't be able to see this, contact a dev immediately!)",
    "You tried to load an unknown save. (You shouldn't be able to see this, contact a dev immediately!)"
]

PRIVACY_MODE_PUBLIC = 0
PRIVACY_MODE_FRIENDS_ONLY = 1
PRIVACY_MODE_PRIVATE = 2


# Build Permission Flags
FLPermBuild = 1  # basic building privilages
FLPermClearLoad = 2  # ability to clear lot or load a prop save
FLPermEditPerms = 4  # ability to edit user privileges / invite users

# Lot Messages
LOT_LIMIT_REACHED = 0

MaxLotCount = 40

AUTOSAVE_FILENAME = 'last_autosave.blot'

THEME_TO_TITLE_COLOR = (
    Vec4(1.0, 0.5, 0.4, 1.0),
    Vec4(0.8, 0.6, 0.5, 1.0),
    Vec4(0.8, 0.6, 1.0, 1.0),
    Vec4(1.0, 0.5, 0.5, 1.0),
    Vec4(0.3, 0.6, 1.0, 1.0),
    Vec4(1.0, 0.9, 0.5, 1.0),
    Vec4(0.5, 0.5, 0.5, 1.0),
    Vec4(0.5, 0.5, 0.5, 1.0),
    Vec4(0.5, 0.5, 0.5, 1.0),
    Vec4(0.5, 0.5, 0.5, 1.0),
    Vec4(0.5, 0.5, 0.5, 1.0)
    # Vec4(1.0, 0.5, 0.4, 1.0),  # TODO
)