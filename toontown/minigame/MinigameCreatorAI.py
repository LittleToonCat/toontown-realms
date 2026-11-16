import copy
import random
import time
from toontown.toonbase import ToontownGlobals
from . import DistributedMinigameTemplateAI
from . import DistributedRaceGameAI
from . import DistributedRaceGameBetaAI
from . import DistributedCannonGameAI
from . import DistributedTagGameAI
from . import DistributedPatternGameAI
from . import DistributedPatternGameBetaAI
from . import DistributedRingGameAI
from . import DistributedMazeGameAI
from . import DistributedTugOfWarGameAI
from . import DistributedCatchGameAI
from . import DistributedDivingGameAI
from . import DistributedTargetGameAI
from . import DistributedPairingGameAI
from . import DistributedPhotoGameAI
from . import DistributedVineGameAI
from . import DistributedIceGameAI
from . import DistributedCogThiefGameAI
from . import DistributedTwoDGameAI
from . import DistributedTravelGameAI
from . import TravelGameGlobals
from toontown.hood.ZoneUtil import isBetaPlaygroundZone

ALLOW_TEMP_MINIGAMES = simbase.config.GetBool('allow-temp-minigames', False)
simbase.forcedMinigameId = simbase.config.GetInt('minigame-id', 0)
RequestMinigame = {}
MinigameZoneRefs = {}
MinigamesNotAllowed = [ToontownGlobals.TravelGameId, ToontownGlobals.MinigameTemplateId]
MgCtors = {}


def initializeMinigames():
    global MgCtors
    if len(MgCtors) == 0:
        MgCtors = {ToontownGlobals.RaceGameId: DistributedRaceGameAI.DistributedRaceGameAI,
                   ToontownGlobals.CannonGameId: DistributedCannonGameAI.DistributedCannonGameAI,
                   ToontownGlobals.TagGameId: DistributedTagGameAI.DistributedTagGameAI,
                   ToontownGlobals.PatternGameId: DistributedPatternGameAI.DistributedPatternGameAI,
                   ToontownGlobals.RingGameId: DistributedRingGameAI.DistributedRingGameAI,
                   ToontownGlobals.MazeGameId: DistributedMazeGameAI.DistributedMazeGameAI,
                   ToontownGlobals.TugOfWarGameId: DistributedTugOfWarGameAI.DistributedTugOfWarGameAI,
                   ToontownGlobals.CatchGameId: DistributedCatchGameAI.DistributedCatchGameAI,
                   ToontownGlobals.DivingGameId: DistributedDivingGameAI.DistributedDivingGameAI,
                   ToontownGlobals.TargetGameId: DistributedTargetGameAI.DistributedTargetGameAI,
                   ToontownGlobals.MinigameTemplateId: DistributedMinigameTemplateAI.DistributedMinigameTemplateAI,
                   ToontownGlobals.PairingGameId: DistributedPairingGameAI.DistributedPairingGameAI,
                   ToontownGlobals.VineGameId: DistributedVineGameAI.DistributedVineGameAI,
                   ToontownGlobals.IceGameId: DistributedIceGameAI.DistributedIceGameAI,
                   ToontownGlobals.CogThiefGameId: DistributedCogThiefGameAI.DistributedCogThiefGameAI,
                   ToontownGlobals.TwoDGameId: DistributedTwoDGameAI.DistributedTwoDGameAI,
                   ToontownGlobals.TravelGameId: DistributedTravelGameAI.DistributedTravelGameAI,
                   ToontownGlobals.PhotoGameId: DistributedPhotoGameAI.DistributedPhotoGameAI,
                   ToontownGlobals.PatternGameBetaId: DistributedPatternGameBetaAI.DistributedPatternGameBetaAI,
                   ToontownGlobals.RaceGameBetaId: DistributedRaceGameBetaAI.DistributedRaceGameBetaAI}

        if ALLOW_TEMP_MINIGAMES and __debug__:
            from tools.minigametools.TempMinigameAI import TempMgCtors
            for key, value in list(TempMgCtors.items()):
                MgCtors[key] = value


def createMinigame(air, playerArray, trolleyZone, minigameZone=None, previousGameId=ToontownGlobals.NoPreviousGameId,
                   newbieIds=None, startingVotes=None, metagameRound=-1, desiredNextGame=None):
    if minigameZone is None:
        minigameZone = air.allocateZone()
    acquireMinigameZone(minigameZone)
    mgId = None
    mgDiff = None
    mgSzId = None
    for avId in playerArray:
        request = RequestMinigame.get(avId)
        if request is not None:
            mgId, mgKeep, mgDiff, mgSzId = request
            if mgSzId == 0:
                mgSzId = trolleyZone
            if not mgKeep:
                del RequestMinigame[avId]
            break

    if mgId is not None:
        pass
    elif simbase.forcedMinigameId:
        mgId = simbase.forcedMinigameId
    elif isBetaPlaygroundZone(trolleyZone):
        randomList = ToontownGlobals.BetaPlaygroundMinigames
        if len(playerArray) == 1 and ToontownGlobals.TagGameId in randomList:
            randomList.remove(ToontownGlobals.TagGameId)
        mgId = random.choice(randomList)
    elif playerArray:
        if simbase.air.useAllMinigames and len(playerArray) > 1:
            randomList = list(copy.copy(ToontownGlobals.MinigameIDs))
        else:
            randomList = list(copy.copy(ToontownGlobals.MinigamePlayerMatrix[len(playerArray)]))

        for gameId in MinigamesNotAllowed:
            if gameId in randomList:
                randomList.remove(gameId)

        if previousGameId != ToontownGlobals.NoPreviousGameId:
            if randomList.count(previousGameId) != 0:
                randomList.remove(previousGameId)
        randomList = removeUnreleasedMinigames(randomList, True)
        mgId = random.choice(randomList)
        if metagameRound > -1:
            if metagameRound % 2 == 0:
                mgId = ToontownGlobals.TravelGameId
            elif desiredNextGame:
                mgId = desiredNextGame
    else:
        mgId = ToontownGlobals.CannonGameId

    try:
        initializeMinigames()
        mg = MgCtors[mgId](air, mgId)
    except KeyError:
        raise Exception('unknown minigame ID: %s' % mgId)

    mg.setExpectedAvatars(playerArray)
    mg.setNewbieIds(newbieIds)
    mg.setTrolleyZone(trolleyZone)
    mg.setDifficultyOverrides(mgDiff, mgSzId)
    if startingVotes is None:
        for avId in playerArray:
            mg.setStartingVote(avId, TravelGameGlobals.DefaultStartingVotes)
    else:
        for index in range(len(startingVotes)):
            avId = playerArray[index]
            votes = startingVotes[index]
            if votes < 0:
                print('createMinigame negative votes, avId=%s votes=%s' % (avId, votes))
                votes = 0
            mg.setStartingVote(avId, votes)

    mg.setMetagameRound(metagameRound)
    mg.generateWithRequired(minigameZone)
    toons = []
    for id in playerArray:
        toon = simbase.air.doId2do.get(id)
        if toon is not None:
            if id in newbieIds:
                toon.inventory.zeroInv()
                toon.d_setInventory(toon.inventory.makeNetString())
            toons.append(toon)

    for toon in toons:
        simbase.air.questManager.toonPlayedMinigame(toon, toons)

    retVal = {'minigameZone': minigameZone, 'minigameId': mgId}
    return retVal


def acquireMinigameZone(zoneId):
    if zoneId not in MinigameZoneRefs:
        MinigameZoneRefs[zoneId] = 0
    MinigameZoneRefs[zoneId] += 1


def releaseMinigameZone(zoneId):
    MinigameZoneRefs[zoneId] -= 1
    if MinigameZoneRefs[zoneId] <= 0:
        del MinigameZoneRefs[zoneId]
        simbase.air.deallocateZone(zoneId)


def removeUnreleasedMinigames(startList, increaseChanceOfNewGames=0):
    randomList = startList[:]
    for gameId in ToontownGlobals.MinigameReleaseDates:
        dateTuple = ToontownGlobals.MinigameReleaseDates[gameId]
        currentTime = time.time()
        releaseTime = time.mktime((dateTuple[0], dateTuple[1], dateTuple[2], 0, 0, 0, 0, 0, -1))
        releaseTimePlus1Week = releaseTime + 7 * 24 * 60 * 60
        if currentTime < releaseTime:
            if gameId in randomList:
                doRemove = True
                if gameId == ToontownGlobals.CogThiefGameId and simbase.air.config.GetBool('force-allow-thief-game', 0):
                    doRemove = False
                    if increaseChanceOfNewGames:
                        randomList += [gameId] * 4
                elif gameId == ToontownGlobals.IceGameId and simbase.air.config.GetBool('force-allow-ice-game', 0):
                    doRemove = False
                    if increaseChanceOfNewGames:
                        randomList += [gameId] * 4
                elif gameId == ToontownGlobals.TwoDGameId and simbase.air.config.GetBool('force-allow-2d-game', 0):
                    doRemove = False
                    if increaseChanceOfNewGames:
                        randomList += [gameId] * 4
                elif gameId == ToontownGlobals.PhotoGameId and simbase.air.config.GetBool('force-allow-photo-game', 0):
                    doRemove = False
                    if increaseChanceOfNewGames:
                        randomList += [gameId] * 4
                if doRemove:
                    randomList.remove(gameId)
        if releaseTime < currentTime < releaseTimePlus1Week and gameId in randomList and increaseChanceOfNewGames:
            randomList += [gameId] * 4

    return randomList
