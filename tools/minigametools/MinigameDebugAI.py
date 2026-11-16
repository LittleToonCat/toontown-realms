from direct.directnotify.DirectNotifyGlobal import directNotify
from toontown.minigame.MinigameCreatorAI import initializeMinigames, MgCtors

MgDebugNotify = directNotify.newCategory('MinigameDebugAI')

"""
TO START A MINIGAME:

First, call the below method on the AI server
Pass in a minigame ID and a list of avatar IDs for the avatars participating

Finally, call startMinigame() on the client for each participating avatar (see MinigameDebug.py)
"""


def startMinigameAI(minigameId, avIds):
    # allocate a zone
    zoneId = simbase.air.allocateZone()
    # Create the minigame
    initializeMinigames()
    mg = MgCtors.get(minigameId)
    if mg:
        mg(simbase.air, minigameId)
        # Generate it in that zone
        mg.generateWithRequired(zoneId)
        # set the expected avatars directly
        # (I do not think this needs to be an update)
        mg.setExpectedAvatars(*avIds)
        MgDebugNotify.info('Successfully created minigame %d in zoneId %d.' % (minigameId, zoneId))
    else:
        MgDebugNotify.warning('No class found for minigame ID %d!' % minigameId)
