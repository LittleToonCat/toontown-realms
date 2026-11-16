from direct.directnotify import DirectNotifyGlobal
from . import DistributedRaceAI
from toontown.toonbase import ToontownGlobals, TTLocalizer
from toontown.ai import HolidayBaseAI
from direct.showbase import DirectObject
from . import RaceGlobals
import os, json, sys


class RaceManagerAI(DirectObject.DirectObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('RaceManagerAI')
    serverDataFolder = simbase.config.GetString('server-data-folder', '')

    def __init__(self, air):
        DirectObject.DirectObject.__init__(self)
        self.air = air
        self.races = []
        self.shard = str(air.districtId)
        self.filename = self.getFilename()
        self.trackRecords = self.loadRecords()

    def createRace(self, trackId, raceType, laps, players, circuitLoop, circuitPoints, circuitTimes, qualTimes=[], circuitTimeList={}, circuitTotalBonusTickets={}):
        raceZone = self.air.allocateZone()
        race = DistributedRaceAI.DistributedRaceAI(self.air, trackId, raceZone, players, laps, raceType, self.exitedRace, self.raceOver, circuitLoop, circuitPoints, circuitTimes, qualTimes, circuitTimeList, circuitTotalBonusTickets)
        race.generateWithRequired(raceZone)
        race.playersFinished = []
        race.lastTotalTime = 0
        self.races.append(race)
        return raceZone

    def exitedRace(self, race, playerInfo):
        self.notify.debug('exited race: %s' % playerInfo.avId)
        totalTime = playerInfo.totalTime
        entryFee = 0
        bonus = 0
        placeMultiplier = 0
        qualify = 0
        winnings = 0
        trophies = []
        points = []
        race.playersFinished.append(playerInfo.avId)
        place = len(race.playersFinished)
        self.notify.debug('place: %s of %s' % (place, race.toonCount))
        self.notify.debug('pre-tie totalTime: %s' % totalTime)
        if totalTime <= race.lastTotalTime:
            totalTime = race.lastTotalTime + 0.01
        race.lastTotalTime = totalTime
        self.notify.debug('totalTime: %s, qualify: %s' % (totalTime, RaceGlobals.getQualifyingTime(race.trackId)))
        circuitTime = totalTime + race.circuitTimes.get(playerInfo.avId, 0)
        race.circuitTimes[playerInfo.avId] = circuitTime
        if not race.circuitTimeList.get(playerInfo.avId):
            race.circuitTimeList[playerInfo.avId] = []
        race.circuitTimeList[playerInfo.avId].append([totalTime, 0])
        self.notify.debug('CircuitTimeList %s' % race.circuitTimeList)
        if race.raceType == RaceGlobals.Circuit:
            points = race.circuitPoints.get(playerInfo.avId, [])
            points.append(RaceGlobals.CircuitPoints[place - 1])
            race.circuitPoints[playerInfo.avId] = points
        currentTimeIndex = len(race.circuitTimeList[playerInfo.avId]) - 1
        if totalTime <= RaceGlobals.getQualifyingTime(race.trackId):
            race.circuitTimeList[playerInfo.avId][currentTimeIndex][1] = 1
            self.notify.debug('Racer Qualified time: %s required: %s' % (totalTime, RaceGlobals.getQualifyingTime(race.trackId)))
            qualify = 1
            self.checkPersonalBest(race.trackId, totalTime, playerInfo.avId)
            if race.raceType == RaceGlobals.Practice:
                winnings = RaceGlobals.PracticeWinnings
                self.notify.debug('GrandTouring: Checking from branch: practice %s' % playerInfo.avId)
                trophies = self.checkForNonRaceTrophies(playerInfo.avId)
                if trophies:
                    self.updateTrophiesFromList(playerInfo.avId, trophies)
            else:
                self.air.writeServerEvent('kartingPlaced', playerInfo.avId, '%s|%s' % (place, race.toonCount))
                if race.raceType != RaceGlobals.Circuit:
                    entryFee = RaceGlobals.getEntryFee(race.trackId, race.raceType)
                    placeMultiplier = RaceGlobals.Winnings[place - 1 + (RaceGlobals.MaxRacers - race.toonCount)]
                    winnings = int(entryFee * placeMultiplier)
                    newHistory = self.getNewSingleRaceHistory(race, playerInfo.avId, place)
                    av = self.air.doId2do.get(playerInfo.avId)
                    if newHistory:
                        self.notify.debug('history %s' % newHistory)
                        av.b_setKartingHistory(newHistory)
                        trophies = self.checkForRaceTrophies(playerInfo.avId)
                    else:
                        trophies = self.checkForNonRaceTrophies(playerInfo.avId)
                    if trophies:
                        self.updateTrophiesFromList(playerInfo.avId, trophies)
                bonus = self.checkTimeRecord(race.trackId, totalTime, race.raceType, race.toonCount, playerInfo.avId)
                if playerInfo.avId in race.circuitTotalBonusTickets:
                    race.circuitTotalBonusTickets[playerInfo.avId] += bonus
                else:
                    race.circuitTotalBonusTickets[playerInfo.avId] = bonus
            av = self.air.doId2do.get(playerInfo.avId)
            if av:
                oldTickets = av.getTickets()
                self.notify.debug('old tickets: %s' % oldTickets)
                newTickets = oldTickets + winnings + entryFee + bonus
                self.air.writeServerEvent('kartingTicketsWon', playerInfo.avId, '%s' % (newTickets - oldTickets))
                self.notify.debug('entry fee: %s' % entryFee)
                self.notify.debug('place mult: %s' % placeMultiplier)
                self.notify.debug('winnings: %s' % winnings)
                self.notify.debug('bonus: %s' % bonus)
                self.notify.debug('new tickets: %s' % newTickets)
                self.notify.debug('circuit points: %s' % points)
                self.notify.debug('circuit time: %s' % circuitTime)
                self.notify.debug('circuitTotalBonusTickets: %s' % race.circuitTotalBonusTickets)
                av.b_setTickets(newTickets)
        else:
            race.circuitTimeList[playerInfo.avId][currentTimeIndex][1] = -1
            self.notify.debug('GrandTouring: Checking from branch: Not Qualified %s' % playerInfo.avId)
            trophies = self.checkForNonRaceTrophies(playerInfo.avId)
            if trophies:
                self.updateTrophiesFromList(playerInfo.avId, trophies)
        if race in self.races:
            race.d_setPlace(playerInfo.avId, totalTime, place, entryFee, qualify, winnings, bonus, trophies, points, circuitTime)
            if race.isCircuit():
                self.notify.debug('isCircuit')
                if race.everyoneDone():
                    self.notify.debug('everyoneDone')
                    if race.isLastRace():
                        taskMgr.doMethodLater(10, self.endCircuitRace, 'DelayEndCircuitRace=%d' % race.doId, (race, bonus))
                    else:
                        self.endCircuitRace(race, bonus)
            else:
                self.notify.debug('not isCircuit')
        return

    def endCircuitRace(self, race, bonus=0):
        self.notify.debug('endCircuitRace')
        pointTotals = []
        for avId in race.circuitPoints:
            pointTotals.append([avId, sum(race.circuitPoints[avId])])

        numVals = len(pointTotals)
        finalStandings = []

        def swap(x, y):
            t = pointTotals[x]
            pointTotals[x] = pointTotals[y]
            pointTotals[y] = t

        for i in range(numVals - 1, 0, -1):
            for j in range(i):
                if pointTotals[j][1] < pointTotals[j + 1][1]:
                    swap(j, j + 1)
                elif pointTotals[j][1] == pointTotals[j + 1][1]:
                    avId1 = pointTotals[j][0]
                    avId2 = pointTotals[j + 1][0]
                    if race.circuitTimes[avId1] > race.circuitTimes[avId2]:
                        swap(j, j + 1)

        for i in range(numVals):
            finalStandings.append(pointTotals[i][0])

        self.notify.debug('Final standings %s' % finalStandings)
        for avId in finalStandings:
            self.notify.debug('avId %s' % avId)
            place = finalStandings.index(avId) + 1
            places = len(finalStandings)
            if race.isLastRace():
                self.notify.debug('isLastRace')
                av = self.air.doId2do.get(avId)
                if av and avId in race.playersFinished:
                    self.air.writeServerEvent('kartingCircuitFinished', avId, '%s|%s' % (place, places))
                    self.notify.info('kartingCircuitFinished %s|%s|%s' % (avId, place, places))
                    entryFee = RaceGlobals.getEntryFee(race.trackId, race.raceType)
                    placeMultiplier = RaceGlobals.Winnings[place - 1 + (RaceGlobals.MaxRacers - places)]
                    winnings = int(entryFee * placeMultiplier)
                    newHistory = self.getNewCircuitHistory(race, avId, place)
                    if newHistory:
                        self.notify.debug('history %s' % newHistory)
                        trophies = self.checkForCircuitTrophies(avId, newHistory)
                        av.b_setKartingHistory(newHistory)
                        if trophies:
                            self.updateTrophiesFromList(avId, trophies)
                    else:
                        self.notify.debug('no new history')
                        trophies = self.checkForNonRaceTrophies(avId)
                    oldTickets = av.getTickets()
                    self.notify.debug('endCircuitRace: old tickets: %s' % oldTickets)
                    newTickets = oldTickets + winnings + entryFee
                    self.air.writeServerEvent('kartingTicketsWonCircuit', avId, '%s' % (newTickets - oldTickets))
                    self.notify.debug('entry fee: %s' % entryFee)
                    self.notify.debug('place mult: %s' % placeMultiplier)
                    self.notify.debug('winnings: %s' % winnings)
                    self.notify.debug('new tickets: %s' % newTickets)
                    self.notify.debug('trophies: %s' % trophies)
                    self.notify.debug('bonus: %s' % bonus)
                    av.b_setTickets(newTickets)
                    finalBonus = 0
                    if avId in race.circuitTotalBonusTickets:
                        finalBonus = race.circuitTotalBonusTickets[avId]
                    race.d_setCircuitPlace(avId, place, entryFee, winnings, finalBonus, trophies)

        race.playersFinished = finalStandings
        race.d_endCircuitRace()

    def updateTrophiesFromList(self, avId, trophies):
        self.air.writeServerEvent('Writing Trophies: Updating trophies from list', avId, '%s' % trophies)
        av = self.air.doId2do.get(avId)
        if not av:
            return
        if not trophies:
            return
        trophyField = av.getKartingTrophies()
        for trophy in trophies:
            trophyField[trophy] = 1

        av.b_setKartingTrophies(trophyField)

    def checkForCircuitTrophies(self, avId, inHistory=None):
        av = self.air.doId2do.get(avId)
        if not av:
            return []
        if inHistory:
            history = inHistory
        else:
            history = av.getKartingHistory()
        winIndex = RaceGlobals.CircuitWins
        wonCircuitRaces = RaceGlobals.getWonCircuitRaces(self.air.nerfsMode)
        winReqList = wonCircuitRaces
        winIndices = RaceGlobals.CircuitWinsList
        sweepIndex = RaceGlobals.CircuitSweeps
        sweptCircuitRaces = RaceGlobals.getSweptCircuitRaces(self.air.nerfsMode)
        sweepReqList = sweptCircuitRaces
        sweepIndices = RaceGlobals.CircuitSweepsList
        qualIndex = RaceGlobals.CircuitQuals
        qualifiedCircuitRaces = RaceGlobals.getQualifiedCircuitRaces(self.air.nerfsMode)
        qualReqList = qualifiedCircuitRaces
        qualIndices = RaceGlobals.CircuitQualList
        trophies = av.getKartingTrophies()
        newTrophies = []
        newTrophies.extend(self.checkHistoryForTrophy(trophies, history, winIndex, winReqList, winIndices))
        newTrophies.extend(self.checkHistoryForTrophy(trophies, history, sweepIndex, sweepReqList, sweepIndices))
        newTrophies.extend(self.checkHistoryForTrophy(trophies, history, qualIndex, qualReqList, qualIndices))
        self.notify.debug('GrandTouring: Checking from branch: Circuit %s' % avId)
        newTrophies.extend(self.checkForNonRaceTrophies(avId, history))
        newTrophies.sort()
        return newTrophies

    def checkForRaceTrophies(self, avId, inHistory=None):
        av = self.air.doId2do.get(avId)
        if not av:
            return []
        trophies = av.getKartingTrophies()
        if inHistory:
            history = inHistory
        else:
            history = av.getKartingHistory()
        newTrophies = []
        numTrackGenres = len(RaceGlobals.WinsList)
        wonRaces = RaceGlobals.getWonRaces(self.air.nerfsMode)
        for genre in range(numTrackGenres):
            singleGenreNewTrophies = self.checkHistoryForTrophy(trophies, history, RaceGlobals.WinsList[genre], wonRaces, RaceGlobals.AllWinsList[genre])
            newTrophies.extend(singleGenreNewTrophies)

        numTrackGenres = len(RaceGlobals.QualsList)
        qualifiedRaces = RaceGlobals.getQualifiedRaces(self.air.nerfsMode)
        for genre in range(numTrackGenres):
            singleGenreNewTrophies = self.checkHistoryForTrophy(trophies, history, RaceGlobals.QualsList[genre], qualifiedRaces, RaceGlobals.AllQualsList[genre])
            newTrophies.extend(singleGenreNewTrophies)

        totalWins = 0
        for genre in range(numTrackGenres):
            totalWins += history[RaceGlobals.WinsList[genre]]

        totalWonRaces = RaceGlobals.getTotalWonRaces(self.air.nerfsMode)
        singleGenreNewTrophies = self.checkHistoryForTrophyByValue(trophies, totalWins, [
         totalWonRaces], [
         RaceGlobals.TotalWins])
        newTrophies.extend(singleGenreNewTrophies)
        totalQuals = 0
        for genre in range(numTrackGenres):
            totalQuals += history[RaceGlobals.QualsList[genre]]

        totalQualifiedRaces = RaceGlobals.getTotalQualifiedRaces(self.air.nerfsMode)
        singleGenreNewTrophies = self.checkHistoryForTrophyByValue(trophies, totalQuals, [
         totalQualifiedRaces], [
         RaceGlobals.TotalQuals])
        newTrophies.extend(singleGenreNewTrophies)
        self.notify.debug('GrandTouring: Checking from branch: Race %s ' % avId)
        newTrophies.extend(self.checkForNonRaceTrophies(avId, history))
        newTrophies.sort()
        return newTrophies

    def checkForNonRaceTrophies(self, avId, inHistory=None):
        self.notify.debug('CHECKING FOR NONRACE TROPHIES')
        self.notify.debug('GrandTouring: Checking for non-race trophies %s' % avId)
        av = self.air.doId2do.get(avId)
        if not av:
            self.notify.debug('NO AV %s' % avId)
            self.notify.debug("GrandTouring: can't convert avId to Av %s" % avId)
            return []
        trophies = av.getKartingTrophies()
        oldTrophies = trophies[:]
        if inHistory:
            history = inHistory
        else:
            history = av.getKartingHistory()
        newTrophies = []
        self.notify.debug('GrandTouring: history-- %s' % history)
        self.notify.debug('GrandTouring: trophies- %s' % trophies)
        addTrophyCount = 0
        kartTrophyDescriptions = TTLocalizer.getKartTrophyDescriptions(self.air.nerfsMode)
        if not trophies[RaceGlobals.GrandTouring]:
            self.notify.debug('checking for grand touring')
            self.notify.debug('GrandTouring: checking for grand touring %s' % trophies[RaceGlobals.GrandTouring])
            best = av.getKartingPersonalBestAll()
            self.notify.debug('personal best %s' % best)
            self.notify.debug('GrandTouring: checking personal best %s' % best)
            counter = 0
            for time in best:
                if not time == 0:
                    counter += 1

            self.notify.debug('counter %s tracks %s' % (counter, len(RaceGlobals.TrackDict)))
            self.notify.debug('GrandTouring: bests comparison counter: %s tracks: %s' % (counter, len(RaceGlobals.TrackDict)))
            if counter >= len(RaceGlobals.TrackDict):
                newTrophies.append(RaceGlobals.GrandTouring)
                addTrophyCount += 1
                self.air.writeServerEvent('kartingTrophy', avId, '%s' % RaceGlobals.GrandTouring)
                self.notify.debug('trophy: ' + kartTrophyDescriptions[RaceGlobals.GrandTouring])
                self.notify.debug('GrandTouring: awarding grand touring new trophies %s' % newTrophies)
        else:
            self.notify.debug('already has grandtouring')
            self.notify.debug('trophies %s' % trophies)
            self.notify.debug('GrandTouring: already has grand touring %s' % trophies[RaceGlobals.GrandTouring])

        oldLaffTrophyCount = sum([1 if x else 0 for x in oldTrophies[:RaceGlobals.NumTrophies]]) // RaceGlobals.TrophiesPerCup
        newLaffTrophyCount = sum([1 if x else 0 for x in trophies[:RaceGlobals.NumTrophies]]) // RaceGlobals.TrophiesPerCup
        self.notify.debug(f"{avId} Laff trophies: old={oldLaffTrophyCount}, new={newLaffTrophyCount}")
        if newLaffTrophyCount < oldLaffTrophyCount:
            # this patches (at least attempts to) laff and laff trophy bugs for av (if they do a new race)
            self.notify.warning(f"Avatar {avId}'s laff racing trophies were borked; patching...")
            oldMaxHp = av.getMaxHp()
            newMaxHp = max(15, oldMaxHp - (oldLaffTrophyCount - newLaffTrophyCount))
            self.notify.debug(f"{avId}: old max HP was {oldMaxHp}; readjusting to {newMaxHp}...")
            av.toonUp(newMaxHp)
            av.b_setMaxHp(newMaxHp)
            self.notify.debug(f"Resetting {avId}'s laff trophies...")
            trophyPatch = oldTrophies[:]
            trophyPatch[RaceGlobals.NumTrophies:] = [0] * RaceGlobals.NumCups
            self.notify.debug(f"{avId} oldTrohpies={oldTrophies}, trophyPatch={trophyPatch}")
            if newLaffTrophyCount > 0:
                for i in range(newLaffTrophyCount):
                    idx = RaceGlobals.NumTrophies + i
                    trophyPatch[idx] = 1
            av.b_setKartingTrophies(trophyPatch)
        elif oldLaffTrophyCount < newLaffTrophyCount:
            self.notify.debug(f"{avId} has some laff to acquire! Beginning adjustments...")
            newLaffTrophies = list(range(RaceGlobals.NumTrophies + oldLaffTrophyCount,
                                         RaceGlobals.NumTrophies + newLaffTrophyCount))
            self.notify.debug(f"{avId}: Adding trophies {newLaffTrophies} to newTrophies...")
            newTrophies.extend(newLaffTrophies)
            oldMaxHp = av.getMaxHp()
            newMaxHp = min(ToontownGlobals.MaxHpLimit, oldMaxHp + (newLaffTrophyCount - oldLaffTrophyCount))
            self.notify.debug(f"{avId} old max laff={av.getMaxHp()}, new max laff={newMaxHp}")
            av.b_setMaxHp(newMaxHp)
            av.toonUp(newMaxHp)
            # this chunk is mainly to log kartingTrophy stuff, and serves no other purpose really...
            for i in range(oldLaffTrophyCount, newLaffTrophyCount):
                idx = RaceGlobals.NumTrophies + i
                self.air.writeServerEvent('kartingTrophy', avId, f"{idx}")
                self.notify.debug(f"trophy: {kartTrophyDescriptions[idx]}")
        else:
            self.notify.debug(f"No laff adjustments required for {avId}.")

        self.notify.debug('NONRACE TROPHIES %s' % newTrophies)
        return newTrophies

    def checkHistoryForTrophyByValue(self, trophies, historyIndexValue, trophyReqList, trophyIndices):
        newTrophies = []
        self.notify.debug('Checking History for Trophy')
        self.notify.debug('Index %s Num %s ReqList %s Indices %s' % (0, historyIndexValue, trophyReqList, trophyIndices))
        for index in range(len(trophyIndices)):
            if not trophies[trophyIndices[index]]:
                if historyIndexValue >= trophyReqList[index]:
                    trophies[trophyIndices[index]] = 1
                    newTrophies.append(trophyIndices[index])

        return newTrophies

    def checkHistoryForTrophy(self, trophies, history, historyIndex, trophyReqList, trophyIndices):
        newTrophies = []
        self.notify.debug('Checking History for Trophy')
        self.notify.debug('Index %s Num %s ReqList %s Indices %s' % (historyIndex, history[historyIndex], trophyReqList, trophyIndices))
        for index in range(len(trophyIndices)):
            if not trophies[trophyIndices[index]]:
                if history[historyIndex] >= trophyReqList[index]:
                    trophies[trophyIndices[index]] = 1
                    newTrophies.append(trophyIndices[index])

        return newTrophies

    def mergeHistories(self, historyA, historyB):
        newHistorySize = len(historyA)
        if len(historyB) > len(historyA):
            newHistorySize = historyB
        mergedHistory = []
        for index in range(newHistorySize):
            mergedHistory[index] = 0
            if len(historyA) > index:
                if historyA[index] > mergedHistory[index]:
                    historyA[index] = mergedHistory[index]
            if len(historyB) > index:
                if historyB[index] > mergedHistory[index]:
                    historyB[index] = mergedHistory[index]

        return mergedHistory

    def getNewSingleRaceHistory(self, race, avId, positionFinished):
        newHistory = 0
        av = self.air.doId2do.get(avId)
        if not av:
            return []
        history = av.getKartingHistory()
        trackGenre = RaceGlobals.getTrackGenre(race.trackId)
        winIndex = RaceGlobals.WinsList[trackGenre]
        wonRaces = RaceGlobals.getWonRaces(self.air.nerfsMode)
        winReqList = wonRaces
        qualIndex = RaceGlobals.QualsList[trackGenre]
        qualifiedRaces = RaceGlobals.getQualifiedRaces(self.air.nerfsMode)
        qualReqList = qualifiedRaces
        if history[winIndex] < winReqList[-1] and positionFinished == 1:
            history[winIndex] += 1
            self.notify.debug('New History Won!')
            newHistory = 1
        if history[qualIndex] < qualReqList[-1]:
            history[qualIndex] += 1
            self.notify.debug('New History Qualified!')
            newHistory = 1
        if newHistory:
            return history

    def getNewCircuitHistory(self, race, avId, positionFinished):
        newHistory = 0
        av = self.air.doId2do.get(avId)
        if not av:
            return []
        history = av.getKartingHistory()
        historyIndex = RaceGlobals.CircuitWins
        wonCircuitRaces = RaceGlobals.getWonCircuitRaces(self.air.nerfsMode)
        trophyReqList = wonCircuitRaces
        sweptCircuitRaces = RaceGlobals.getSweptCircuitRaces(self.air.nerfsMode)
        sweepReqList = sweptCircuitRaces
        self.notify.debug('getNewCircuitHistory: avId=%d positionFinished=%d history =%s' % (avId, positionFinished, history))
        if history[historyIndex] < trophyReqList[-1] and positionFinished == 1:
            history[historyIndex] += 1
            self.notify.debug('New History Won!')
            newHistory = 1
        swept = 0
        totalPoints = sum(race.circuitPoints[avId])
        if totalPoints == len(race.circuitPoints[avId]) * RaceGlobals.CircuitPoints[0]:
            swept = 1
        if swept:
            if history[RaceGlobals.CircuitSweeps] < sweepReqList[-1]:
                if not history[RaceGlobals.CircuitSweeps]:
                    history[RaceGlobals.CircuitSweeps] = 0
                history[RaceGlobals.CircuitSweeps] += 1
                self.notify.debug('New History Swept!')
                newHistory = 1
        self.notify.debug('qual times %s' % race.qualTimes)
        self.notify.debug('avatar times %s' % race.circuitTimeList[avId])
        qualified = 1
        self.notify.debug('End Race Circuit Time List %s' % race.circuitTimeList)
        self.notify.debug('check for qualify')
        for qual in race.circuitTimeList[avId]:
            self.notify.debug('qual %s' % qual)
            if qual[1] == -1:
                qualified = 0
                self.notify.debug('not qualified')

        if qualified:
            qualifiedCircuitRaces = RaceGlobals.getQualifiedCircuitRaces(self.air.nerfsMode)
            self.notify.debug('qualified has %s needs %s' % (history[RaceGlobals.CircuitQuals], qualifiedCircuitRaces[-1]))
            if history[RaceGlobals.CircuitQuals] < qualifiedCircuitRaces[-1]:
                history[RaceGlobals.CircuitQuals] += 1
                self.notify.debug('New History qualified!')
                newHistory = 1
        if newHistory:
            return history

    def raceOver(self, race, normalExit=True):
        if race in self.races:
            if normalExit and race.isCircuit() and not race.isLastRace():
                nextTrackId = race.circuitLoop[0]
                continuingAvs = []
                for avId in race.avIds:
                    if avId not in race.kickedAvIds:
                        continuingAvs.append(avId)

                lastRace = False
                if len(continuingAvs) > 0:
                    raceZone = self.createRace(nextTrackId, race.raceType, race.lapCount, continuingAvs, race.circuitLoop[1:], race.circuitPoints, race.circuitTimes, race.qualTimes, race.circuitTimeList, race.circuitTotalBonusTickets)
                    race.sendToonsToNextCircuitRace(raceZone, nextTrackId)
                else:
                    lastRace = True
                self.races.remove(race)
                race.requestDelete(lastRace)
            else:
                self.races.remove(race)
                race.requestDelete()

    def checkForTrophies(self, place, trackId, raceType, avId):
        av = self.air.doId2do.get(avId)
        outHistory = av.getKartingHistory()
        trophies = av.getKartingTrophies()
        trophiesWon = []
        trackGenre = RaceGlobals.getTrackGenre(trackId)
        if place == 1:
            historyIndex = RaceGlobals.WinsList[trackGenre]
            trophyIndices = RaceGlobals.AllWinsList[trackGenre]
            wonRaces = RaceGlobals.getWonRaces(self.air.nerfsMode)
            trophyReqList = wonRaces
            historyTotalList = RaceGlobals.WinsList
            totalTrophyIndex = RaceGlobals.TotalWins
            totalWonRaces = RaceGlobals.getTotalWonRaces(self.air.nerfsMode)
            totalReq = totalWonRaces
            trophiesWon += self.checkForTrophy(raceType, avId, historyIndex, trophyIndices, trophyReqList, historyTotalList, totalTrophyIndex, totalReq)
        historyIndex = RaceGlobals.QualsList[trackGenre]
        trophyIndices = RaceGlobals.AllQualsList[trackGenre]
        qualifiedRaces = RaceGlobals.getQualifiedRaces(self.air.nerfsMode)
        trophyReqList = qualifiedRaces
        historyTotalList = RaceGlobals.QualsList
        totalTrophyIndex = RaceGlobals.TotalQuals
        totalQualifiedRaces = RaceGlobals.getTotalQualifiedRaces(self.air.nerfsMode)
        totalReq = totalQualifiedRaces
        trophiesWon += self.checkForTrophy(raceType, avId, historyIndex, trophyIndices, trophyReqList, historyTotalList, totalTrophyIndex, totalReq)
        if not trophies[RaceGlobals.GrandTouring]:
            self.notify.debug('checking for grand touring')
            best = av.getKartingPersonalBestAll()
            self.notify.debug('personal best %s' % best)
            counter = 0
            for time in best:
                if not time == 0:
                    counter += 1

            self.notify.debug('counter %s tracks %s' % (counter, len(RaceGlobals.TrackDict)))
            if counter >= len(RaceGlobals.TrackDict):
                trophiesWon.append(RaceGlobals.GrandTouring)
        if outHistory:
            av.b_setKartingHistory(outHistory)
        if len(trophiesWon):
            for trophy in trophiesWon:
                trophies[trophy] = 1

            av.b_setKartingTrophies(trophies)
        trophiesWon.sort()
        return trophiesWon

    def checkForTrophy(self, raceType, avId, historyIndex, trophyIndices, trophyReqList, historyTotalList, totalTrophyIndex, totalReq):
        av = self.air.doId2do.get(avId)
        if not av:
            return []
        history = av.getKartingHistory()
        newHistory = 0
        trophies = av.getKartingTrophies()
        oldTrophies = trophies[:]
        newTrophies = []
        if history[historyIndex] < trophyReqList[-1]:
            history[historyIndex] += 1
            newHistory = 1
        kartTrophyDescriptions = TTLocalizer.getKartTrophyDescriptions(self.air.nerfsMode)
        for i in range(0, len(trophyReqList)):
            if not trophies[trophyIndices[i]]:
                if history[historyIndex] == trophyReqList[i]:
                    trophies[trophyIndices[i]] = 1
                    newTrophies.append(trophyIndices[i])
                    self.air.writeServerEvent('kartingTrophy', avId, '%s' % trophyIndices[i])
                    self.notify.debug('trophy: ' + kartTrophyDescriptions[trophyIndices[i]])
                    break

        if not raceType == RaceGlobals.Circuit:
            if not trophies[totalTrophyIndex]:
                total = 0
                for i in historyTotalList:
                    total += history[i]

                self.notify.debug('checking for total trophy: %s >= %s' % (total, totalReq))
                if total >= totalReq:
                    trophies[totalTrophyIndex] = 1
                    newTrophies.append(totalTrophyIndex)
                    self.air.writeServerEvent('kartingTrophy', avId, '%s' % totalTrophyIndex)
                    self.notify.debug('trophy: ' + kartTrophyDescriptions[totalTrophyIndex])

        oldLaffTrophyCount = sum([1 if x else 0 for x in oldTrophies[:RaceGlobals.NumTrophies]]) // RaceGlobals.TrophiesPerCup
        newLaffTrophyCount = sum([1 if x else 0 for x in trophies[:RaceGlobals.NumTrophies]]) // RaceGlobals.TrophiesPerCup
        self.notify.debug(f"{avId} Laff trophies: old={oldLaffTrophyCount}, new={newLaffTrophyCount}")
        if newLaffTrophyCount < oldLaffTrophyCount:
            # this patches (at least attempts to) laff and laff trophy bugs for av (if they do a new race)
            self.notify.warning(f"Avatar {avId}'s laff racing trophies were borked; patching...")
            oldMaxHp = av.getMaxHp()
            newMaxHp = max(15, oldMaxHp - (oldLaffTrophyCount - newLaffTrophyCount))
            self.notify.debug(f"{avId}: old max HP was {oldMaxHp}; readjusting to {newMaxHp}...")
            av.toonUp(newMaxHp)
            av.b_setMaxHp(newMaxHp)
            self.notify.debug(f"Resetting {avId}'s laff trophies...")
            trophyPatch = oldTrophies[:]
            trophyPatch[RaceGlobals.NumTrophies:] = [0] * RaceGlobals.NumCups
            self.notify.debug(f"{avId} oldTrohpies={oldTrophies}, trophyPatch={trophyPatch}")
            if newLaffTrophyCount > 0:
                for i in range(newLaffTrophyCount):
                    idx = RaceGlobals.NumTrophies + i
                    trophyPatch[idx] = 1
            av.b_setKartingTrophies(trophyPatch)
        elif oldLaffTrophyCount < newLaffTrophyCount:
            self.notify.debug(f"{avId} has some laff to acquire! Beginning adjustments...")
            newLaffTrophies = list(range(RaceGlobals.NumTrophies + oldLaffTrophyCount,
                                         RaceGlobals.NumTrophies + newLaffTrophyCount))
            self.notify.debug(f"{avId}: Adding trophies {newLaffTrophies} to newTrophies...")
            newTrophies.extend(newLaffTrophies)
            oldMaxHp = av.getMaxHp()
            newMaxHp = min(ToontownGlobals.MaxHpLimit, oldMaxHp + (newLaffTrophyCount - oldLaffTrophyCount))
            self.notify.debug(f"{avId} old max laff={av.getMaxHp()}, new max laff={newMaxHp}")
            av.b_setMaxHp(newMaxHp)
            av.toonUp(newMaxHp)
            # this chunk is mainly to log kartingTrophy stuff, and serves no other purpose really...
            for i in range(oldLaffTrophyCount, newLaffTrophyCount):
                idx = RaceGlobals.NumTrophies + i
                self.air.writeServerEvent('kartingTrophy', avId, f"{idx}")
                self.notify.debug(f"trophy: {kartTrophyDescriptions[idx]}")
        else:
            self.notify.debug(f"No laff adjustments required for {avId}.")

        self.notify.debug('newTrophies: %s' % newTrophies)
        self.notify.debug('trophies: %s' % trophies)
        self.notify.debug('kartingHistory: %s' % history)
        if newHistory:
            av.b_setKartingHistory(history)
        return newTrophies

    def checkPersonalBest(self, trackId, time, avId):
        av = simbase.air.doId2do.get(avId)
        if av:
            bestTimes = av.getKartingPersonalBestAll()
            trackIndex = RaceGlobals.TrackIds.index(trackId)
            bestTime = bestTimes[trackIndex]
            self.notify.debug('thisTime: %s, bestTime: %s' % (time, bestTime))
            if bestTime == 0.0 or time < bestTime:
                bestTimes[trackIndex] = time
                self.notify.debug('new personal best!')
                av.b_setKartingPersonalBest(bestTimes)
                self.notify.debug('personal best: %s' % bestTimes)

    def checkTimeRecord(self, trackId, time, raceType, numRacers, avId):
        bonus = 0
        newRecord = 0
        for period in RaceGlobals.PeriodIds:
            for record in range(0, RaceGlobals.NumRecordsPerPeriod):
                recordTime = self.trackRecords[str(trackId)][str(period)][record][0]
                if time < recordTime:
                    newRecord = 1
                    self.notify.debug('new %s record!' % TTLocalizer.RecordPeriodStrings[period])
                    av = simbase.air.doId2do.get(avId)
                    if av:
                        name = av.name
                        self.trackRecords[str(trackId)][str(period)].insert(record, (time, raceType, numRacers, name))
                        self.trackRecords[str(trackId)][str(period)] = self.trackRecords[str(trackId)][str(period)][:RaceGlobals.NumRecordsPerPeriod]
                        self.updateLeaderboards(trackId, period)
                        bonus = RaceGlobals.PeriodDict[period]
                        self.air.writeServerEvent('kartingRecord', avId, '%s|%s|%s' % (period, trackId, time))
                    else:
                        self.notify.warning('warning: av not logged in!')
                    break

        if newRecord:
            self.updateRecordFile()
        return bonus

    def updateRecordFile(self):
        try:
            backup = self.filename + '.bu'
            if os.path.exists(self.filename):
                os.rename(self.filename, backup)
            file = open(self.filename, 'w')
            json.dump(self.trackRecords, file, indent=4)
            file.close()
            if os.path.exists(backup):
                os.remove(backup)
        except EnvironmentError:
            self.notify.warning(str(sys.exc_info()[1]))

    def getFilename(self):
        return '%s%s_trackRecords.json' % (self.serverDataFolder, self.shard)

    def loadRecords(self):
        try:
            file = open(self.filename + '.bu', 'r')
            if os.path.exists(self.filename):
                os.remove(self.filename)
        except IOError:
            try:
                file = open(self.filename, 'r')
            except IOError:
                return self.getRecordTimes()

        records = self.loadFrom(file)
        file.close()
        for trackId in RaceGlobals.TrackIds:
            if str(trackId) not in records:
                records[str(trackId)] = {}
                for i in RaceGlobals.PeriodIds:
                    records[str(trackId)][str(i)] = []
                    for j in range(0, RaceGlobals.NumRecordsPerPeriod):
                        records[str(trackId)][str(i)].append(RaceGlobals.getDefaultRecord(trackId))

        self.resetLeaderboards()
        return records

    def loadFrom(self, file):
        records = {}
        try:
            records = json.load(file)
        except ValueError:
            pass

        return records

    def getRecordTimes(self):
        records = {}
        for trackId in RaceGlobals.TrackIds:
            records[str(trackId)] = {}
            for i in RaceGlobals.PeriodIds:
                records[str(trackId)][str(i)] = []
                for j in range(0, RaceGlobals.NumRecordsPerPeriod):
                    records[str(trackId)][str(i)].append(RaceGlobals.getDefaultRecord(trackId))

        return records

    def resetRecordPeriod(self, period):
        for trackId in RaceGlobals.TrackIds:
            for i in range(0, RaceGlobals.NumRecordsPerPeriod):
                self.trackRecords[str(trackId)][str(period)][i] = RaceGlobals.getDefaultRecord(trackId)

            self.updateLeaderboards(trackId, period)

        self.updateRecordFile()

    def getRecords(self, trackId, period):
        return self.trackRecords[str(trackId)][str(period)]

    def updateLeaderboards(self, trackId, period):
        messenger.send('UpdateRaceRecord', [(trackId, period)])

    def resetLeaderboards(self):
        for track in RaceGlobals.TrackIds:
            for period in RaceGlobals.PeriodIds:
                self.updateLeaderboards(track, period)


class KartRecordDailyResetter(HolidayBaseAI.HolidayBaseAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('ResistanceEventMgrAI')
    PostName = 'kertRecordDailyReset'

    def __init__(self, air, holidayId):
        HolidayBaseAI.HolidayBaseAI.__init__(self, air, holidayId)

    def start(self):
        bboard.post(KartRecordDailyResetter.PostName)
        simbase.air.raceMgr.resetRecordPeriod(RaceGlobals.Daily)

    def stop(self):
        bboard.remove(KartRecordDailyResetter.PostName)


class KartRecordWeeklyResetter(HolidayBaseAI.HolidayBaseAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('ResistanceEventMgrAI')
    PostName = 'kartRecordWeeklyReset'

    def __init__(self, air, holidayId):
        HolidayBaseAI.HolidayBaseAI.__init__(self, air, holidayId)

    def start(self):
        bboard.post(KartRecordWeeklyResetter.PostName)
        simbase.air.raceMgr.resetRecordPeriod(RaceGlobals.Weekly)

    def stop(self):
        bboard.remove(KartRecordWeeklyResetter.PostName)


class CircuitRaceHolidayMgr(HolidayBaseAI.HolidayBaseAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('CircuitRaceHolidayMgr')
    PostName = 'CircuitRaceHoliday'
    StartStopMsg = 'CircuitRaceHolidayStartStop'

    def __init__(self, air, holidayId):
        HolidayBaseAI.HolidayBaseAI.__init__(self, air, holidayId)

    def start(self):
        bboard.post(CircuitRaceHolidayMgr.PostName, True)
        if self.holidayId != ToontownGlobals.CIRCUIT_RACING_EVENT:
            simbase.air.newsManager.circuitRaceStart()
        messenger.send(CircuitRaceHolidayMgr.StartStopMsg)

    def stop(self):
        bboard.remove(CircuitRaceHolidayMgr.PostName)
        simbase.air.newsManager.circuitRaceEnd()
        messenger.send(CircuitRaceHolidayMgr.StartStopMsg)
