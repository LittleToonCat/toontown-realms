# Global values for episodes
# Drewcification 5/31/2021
from enum import Enum

from direct.interval.ActorInterval import LerpAnimInterval
from direct.interval.FunctionInterval import Wait, Func
from direct.interval.MetaInterval import Sequence
from panda3d.core import Point3

# === Episode 1: Prologue ===


# === Episode 2: Short Work ===


# === Episode 3: Storm Sellbot ===

# SCENE 1: DAISY GARDENS

# NPC START POSITIONS

EP03_01_NPCS = (
    # Near Left Ramp
    (
        # POSITION / HPR ([0])
        (
            Point3(65.5, 180, 10.02),
            Point3(160.0, 0.0, 0.0)
        ),
        # ANIMATION ([1])
        'neutral'
    ),

    # Fishing
    (
        (
            Point3(63.55, 58.86, 0.24),
            Point3(135.0, 0.0, 0.0)
        ),
        'pole-neutral'
    ),

    # HQ
    (
        (
            Point3(-33.76, 61, 0.03),
            Point3(160.27, 0.0, 0.0)
        ),
        'neutral'
    ),

    # CONVO IN FRONT OF DD TUNNEL 1
    (
        (
            Point3(-67.72, 170.63, 10.02),
            Point3(330.63, 0.0, 0.0)
        ),
        'neutral'
    ),

    # CONVO IN FRONT OF DD TUNNEL 2
    (
        (
            Point3(-64.78, 176.26, 10.02),
            Point3(150.0, 0.0, 0.00)
        ),
        'neutral'
    ),

    # GAG SHOP
    (
        (
            Point3(-13.47, 208.36, 10.03),
            Point3(9.0, 0.0, 0.0)
        ),
        'neutral'
    ),

    # MAZE 1
    (
        (
            Point3(-8.92, 147.49, 0.02),
            Point3(117.94, 0.0, 0.0)
        ),
        'neutral'
    ),

    # MAZE 2
    (
        (
            Point3(-40.94, 90.76, 0.02),
            Point3(337.90, 0.0, 0.0)
        ),
        'neutral'
    ),

    # TROLLEY
    (
        (
            Point3(28.62, 232.58, 12.02),
            Point3(180.0, 0.0, 0.0)
        ),
        'sit'
    )
)

# STORM SELLBOT SCENE 3 (SELLBOT HQ PRE-NERD)
EP03_03_COGS = (
    # left
    # POSITION / HPR
    (
        Point3(-9, -17, 0),
        Point3(200.0, 0.0, 0.0)
    ),
    # POSITION / HPR
    (
        Point3(-3, -15, 0),
        Point3(190.0, 0.0, 0.0)
    ),
    # POSITION / HPR
    (
        Point3(3, -15, 0),
        Point3(170.0, 0.0, 0.0)
    ),
    # POSITION / HPR
    (
        Point3(9, -17, 0),
        Point3(160.0, 0.0, 0.0)
    ),

    # right
    # POSITION / HPR
    (
        Point3(-9, 17, 0),
        Point3(-20.0, 0.0, 0.0)
    ),
    # POSITION / HPR
    (
        Point3(-3, 15, 0),
        Point3(-10.0, 0.0, 0.0)
    ),
    # POSITION / HPR
    (
        Point3(3, 15, 0),
        Point3(10.0, 0.0, 0.0)
    ),
    # POSITION / HPR
    (
        Point3(9, 17, 0),
        Point3(20.0, 0.0, 0.0)
    )
)

EP03_03_NPCS = (
    # left
    (
        # POSITION / HPR ([0])
        (
            Point3(-4, -30, 0),
            Point3(0.0, 0.0, 0.0)
        ),
        # ANIMATION ([1])
        'neutral'
    ),

    (
        (
            Point3(0, -30, 0),
            Point3(0.0, 0.0, 0.0)
        ),
        'neutral'
    ),

    (
        (
            Point3(4, -30, 0.0),
            Point3(0.0, 0.0, 0.0)
        ),
        'neutral'
    ),

    # right
    (
        (
            Point3(-6, 30, 0.0),
            Point3(180, 0.0, 0.0)
        ),
        'neutral'
    ),

    (
        (
            Point3(-2, 30, 0.0),
            Point3(180, 0.0, 0.0)
        ),
        'neutral'
    ),

    (
        (
            Point3(2, 30, 0.0),
            Point3(180, 0.0, 0.0)
        ),
        'neutral'
    ),

    (
        (
            Point3(6, 30, 0.0),
            Point3(180, 0.0, 0.0)
        ),
        'neutral'
    ),

)