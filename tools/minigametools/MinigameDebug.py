from direct.directnotify.DirectNotifyGlobal import directNotify

MgDebugNotify = directNotify.newCategory('MinigameDebug')

"""
TO START A MINIGAME:
First, call startMinigameAI() on the AI server (see MinigameDebugAI.py)

Lastly, call the below method on all participating avatars' clients
Pass in the minigameID and zoneId that was printed out by startMinigameAI()
"""


def startMinigame(minigameID, zoneId):
    place = base.cr.playGame.getPlace()
    if place:
        place.doneStatus = {'loader': 'minigame',
                            'where': 'minigame',
                            'hoodId': place.loader.hood.id,
                            'zoneId': zoneId,
                            'minigameId': minigameID}
        messenger.send(place.doneEvent)
    else:
        MgDebugNotify.warning('Place is None!')
