from typing import Tuple

class DropProp:

   def __init__(self, modelPath, scale, hpr, dropSfxPath = 'phase_5/audio/sfx/cogbldg_drop.ogg', landSfxPath = 'phase_5/audio/sfx/AA_drop_boat_cog.ogg',
                extraSfxPath = 'phase_4/audio/sfx/MG_sfx_travel_game_bell_for_trolley.ogg', fadeSfxPath = 'phase_4/audio/sfx/SZ_trolley_bell.ogg'):
       self.modelPath: str = modelPath
       self.scale: float = scale
       self.hpr: Tuple[float, float, float] = hpr
       self.dropSfxPath: str = dropSfxPath
       self.landSfxPath: str = landSfxPath
       self.extraSfxPath: str = extraSfxPath
       self.fadeSfxPath: str = fadeSfxPath

DropPropList = {
    'Trolley': DropProp(modelPath = 'phase_14.5/models/props/trolley-station', scale = 1.0, hpr = (0, 0, 0)),
    'Big Weight': DropProp(modelPath = 'phase_5/models/props/weight-mod', scale = 1.0, hpr = (0, 0, 0), landSfxPath = 'phase_5/audio/sfx/AA_drop_bigweight.ogg', extraSfxPath = None, fadeSfxPath = None),
    'Safe': DropProp(modelPath = 'phase_5/models/props/safe-mod', scale = 4.0, hpr = (0, 0, 0), landSfxPath = 'phase_5/audio/sfx/AA_drop_safe.ogg', extraSfxPath = None, fadeSfxPath = None),
    'Piano': DropProp(modelPath = 'phase_5/models/props/piano-mod', scale = 5.5, hpr = (180, 90, 0), landSfxPath = 'phase_5/audio/sfx/AA_drop_piano.ogg', extraSfxPath = None, fadeSfxPath = None)
}

def getDropPropNameCaseInsensitive(name):
    for propName in (DropPropList.keys()):
        propLower = propName.lower()
        propStripped = propLower.replace(" ", "")
        if name.lower() == propLower or name == propStripped:
            return propName
    return None