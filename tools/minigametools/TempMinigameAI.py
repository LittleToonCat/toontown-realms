"""
@author: Schell Games
3-16-2010

Allows the creation of temp minigames for testing new game ideas
under the minigame framework without hard-coding them in.
"""

from direct.directnotify.DirectNotifyGlobal import directNotify
from toontown.toonbase import ToontownGlobals

ALLOW_TEMP_MINIGAMES = simbase.config.GetBool('allow-temp-minigames', False)
TempMgNotify = directNotify.newCategory('TempMinigameAI')
TempMgCtors = {}


def _registerTempMinigame(name, mgClass, mgId, minPlayers=1, maxPlayers=4):
    """Temporarily registers a minigame in Toontown. Can be used for prototyping a new idea under
    the minigame framework without hardcoding. 'allow-temp-minigames' config has to be set to True."""
    if not ALLOW_TEMP_MINIGAMES:
        TempMgNotify.warning('registerTempMinigame: allow-temp-minigames config is set to false, '
                             'but we are trying to register temp minigame %s' % name)
        import traceback
        traceback.print_stack()
        return

    assert 1 <= minPlayers <= 4 and 1 <= maxPlayers <= 4 and minPlayers <= maxPlayers
    assert name not in ToontownGlobals.MinigameNames
    assert mgId is not None and mgId not in ToontownGlobals.MinigameIDs and mgId < ToontownGlobals.TravelGameId

    ToontownGlobals.MinigameIDs += (mgId,)
    ToontownGlobals.MinigameNames[name] = mgId
    TempMgCtors[mgId] = mgClass
    for i in range(minPlayers, maxPlayers):
        ToontownGlobals.MinigamePlayerMatrix[i] += (mgId,)

    TempMgNotify.info('Registered new temp minigame: %s with ID %d' % (name, mgId))


# ------------------------------------------------------------------------------
# Temp Minigames
# Please remove when done with them!
# What to do:
# 1. Create AI/client class
# 2. Add the empty declaration to the DC file
# 3. Register right here with a custom name, and give it a unique id < 100

if ALLOW_TEMP_MINIGAMES:
    # Examples:

    # from toontown.cogdominium.DistCogdoMazeGameAI import DistCogdoMazeGameAI
    # _registerTempMinigame("cogdomaze", DistCogdoMazeGameAI, id=50)

    # from toontown.cogdominium.DistCogdoFlyingGameAI import DistCogdoFlyingGameAI
    # _registerTempMinigame("cogdoflying", DistCogdoFlyingGameAI, id=51)
    pass
