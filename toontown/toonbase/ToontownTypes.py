"""
Just some aliases for types in TT
"""

from typing import Tuple, List, Dict, Union

# Some places in the game (like networking related stuff) pass colors as a tuple of 4 floats, not a VBase4
TColor = Tuple[float, float, float, float]
TSDRColor = Tuple[int, int, int, int]
TVec3 = Tuple[float, float, float]
TPosHpr = Tuple[float, float, float, float, float, float]

TColoredTexture = Tuple[str, TColor]

# Shirt: (shirtId, shirtColor, sleeveId, sleeveColor)
TShirt = Tuple[int, TColor, int, TColor]
TBottom = Tuple[int, TColor]

TAccessory = Tuple[int, int, int]

TTypedKeyValuePair = Tuple[
    int,
    str,
    Union[str, int, float]
]

TPickAToonProp = Tuple[str, str, List[str], TPosHpr, TVec3, TSDRColor, List[Tuple[str, str]]]


# DataPack
TCogHead = Tuple[
    str,  # path
    str,  # node
    str,  # texture
    TVec3,
    TVec3,
    TVec3,
    TColor,
    List[str]
]
TCogAppearance = Tuple[
    str,  # COG ABBREVIATION
    List[TCogHead],  # COG HEAD MODEL(S)
    int,  # BODY TYPE
    float,  # SCALE
    float,  # HEIGHT
    str,  # TORSO TEX
    str,  # LEG TEX
    str,  # ARM TEX
    str,  # WRIST TEX
    str,  # SHOE TEX

    str,  # NAME
    str,  # NAME SINGULAR
    str,  # NAME PLURAL
    TColor,  # HAND COLOR
    TColor,  # NORMAL COLOR SCALE
    TColor,  # SKELETON COLOR SCALE
    TColor,  # VIRTUAL COLOR SCALE
    TColor,  # MEDALLION COLOR
    bool,  # isSkeleton
    bool,  # isVirtual
    List[str],  # QUOTE SETS
    List[str] # SOUND PATH SETS
]
TCogAppearance_D = Tuple[
    List[TCogHead],  # COG HEAD MODEL(S)
    int,  # BODY TYPE
    float,  # SCALE
    float,  # HEIGHT
    str,  # TORSO TEX
    str,  # LEG TEX
    str,  # ARM TEX

    str,  # NAME
    str,  # NAME SINGULAR
    str,  # NAME PLURAL
    str,  # HAND TEXTURE
    TColor,  # HAND COLOR
    TColor,  # NORMAL COLOR SCALE
    TColor,  # SKELETON COLOR SCALE
    TColor,  # VIRTUAL COLOR SCALE
    TColor,  # MEDALLION COLOR
    bool,  # isSkeleton
    bool,  # isVirtual
    str, # NORMAL GRUNT
    str, # NORMAL MURMUR
    str, # NORMAL STATEMENT
    str, # NORMAL QUESTION
    str, # SKELECOG GRUNT
    str, # SKELECOG MURMUR
    str, # SKELECOG STATEMENT
    str, # SKELECOG QUESTION
    List[str]  # QUOTE SETS
]


class CogAppearanceIndex:
    HEAD = 0
    BODY_TYPE = 1
    SCALE = 2
    HEIGHT = 3
    TORSO_TEX = 4
    LEG_TEX = 5
    ARM_TEX = 6
    WRIST_TEX = 7
    SHOE_TEX = 8
    NAME = 9
    NAME_SINGULAR = 10
    NAME_PLURAL = 11
    HAND_TEX = 12
    HAND_COLOR = 13
    NORMAL_COLOR_SCALE = 14
    SKELETON_COLOR_SCALE = 15
    VIRTUAL_COLOR_SCALE = 16
    MEDALLION_COLOR = 17
    SKELETON = 18
    VIRTUAL = 19
    NORMAL_VOICE_GRUNT = 20
    NORMAL_VOICE_MURMUR = 21
    NORMAL_VOICE_STATEMENT = 22
    NORMAL_VOICE_QUESTION = 23
    SKELECOG_VOICE_GRUNT = 24
    SKELECOG_VOICE_MURMUR = 25
    SKELECOG_VOICE_STATEMENT = 26
    SKELECOG_VOICE_QUESTION = 27
    QUOTE_SETS = 28


TCogQuote = Tuple[
    str,  # COG ABBREVIATION
    List[str],  # BRUSH OFF TAUNTS
    List[str],  # FACEOFF TAUNTS
    List[str],  # BLDG BOSS FACEOFF TAUNTS
    List[str],  # FACILITY BOSS FACEOFF TAUNTS
    List[str],  # FACTORY BOSS MINION FACEOFF TAUNTS
    List[str],  # ACTION PROP EXPLODE DIALOGUE
    List[str],  # FIRE DIALOGUE
    List[str]   # BATTLE EXPLODE DIALOGUE
]
TCogQuote_D = Tuple[
    List[str],  # BRUSH OFF TAUNTS
    List[str],  # FACEOFF TAUNTS
    List[str],  # BLDG BOSS FACEOFF TAUNTS
    List[str],  # FACILITY BOSS FACEOFF TAUNTS
    List[str],  # FACILITY BOSS MINION FACEOFF TAUNTS
    List[str],  # ACTION PROP EXPLODE DIALOGUE
    List[str],  # FIRE DIALOGUE
    List[str]   # BATTLE EXPLODE DIALOGUE
]


class CogQuoteIndex:
    BRUSH_OFFS = 0
    FACEOFF_TAUNTS = 1
    FACEOFF_TAUNTS_BLDG_BOSS = 2
    FACEOFF_TAUNTS_FACILITY_BOSS = 3
    FACEOFF_TAUNTS_FACILITY_BOSS_MINION = 4
    COG_ACTION_PROP_EXPLODE_DIAL = 5
    COG_FIRE_DIAL = 6
    COG_BATTLE_EXPLODE_DIAL = 7

TStatusEffectClient = Tuple[
    str,    # IDENTIFIER
    str,    # DISPLAY NAME
    TColor, # DISPLAY COLOR
    int     # ROUNDS
]
TStatusEffect_D_Server = Tuple[
    int     # ROUNDS
]
TStatusEffect_D_Client = Tuple[
    str,    # DISPLAY NAME
    TColor, # DISPLAY COLOR
    int     # ROUNDS
]

TCogAttackClient = Tuple[
    str, # IDENTIFIER
    str, # DISPLAY NAME
    str, # ATTACK DESCRIPTION
    str, # COG ANIMATION
    str  # TARGET TYPE
]
TCogAttack_D_Server = Tuple[
    str,      # TARGET TYPE
    List[str] # ATTACK QUOTE SETS
]
TCogAttack_D_Client = Tuple[
    str, # DISPLAY NAME
    str, # ATTACK DESCRIPTION
    str, # COG ANIMATION
    str  # TARGET TYPE
]