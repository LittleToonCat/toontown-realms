from otp.ai.AIBaseGlobal import *
import random
from toontown.suit import SuitDNA
from direct.directnotify import DirectNotifyGlobal
from toontown.suit import DistributedSuitAI
from . import SuitBuildingGlobals
from toontown.toonbase.ToontownGlobals import Dept2NameDept
import types, math


class SuitPlannerInteriorAI:
    notify = DirectNotifyGlobal.directNotify.newCategory('SuitPlannerInteriorAI')

    def __init__(self, numFloors, bldgLevel, bldgTracks, zone, respectInvasions=1, interior=None, boss=None):
        self.dbg_nSuits1stRound = config.GetBool('n-suits-1st-round', 0)
        self.dbg_4SuitsPerFloor = config.GetBool('4-suits-per-floor', 0)
        self.dbg_1SuitPerFloor = config.GetBool('1-suit-per-floor', 0)
        self.interior = interior
        self.zoneId = zone
        self.numFloors = numFloors
        self.bldgTracks = bldgTracks
        self.respectInvasions = respectInvasions
        self.boss = boss
        self.previousNumCogs: int = 0
        if isinstance(bldgLevel, bytes):
            self.notify.warning('bldgLevel is a string!')
            bldgLevel = int(bldgLevel)
        if not interior:
            self._genSuitInfos(numFloors, bldgLevel)
        else:
            self.randomGenerator = random.Random()
            self.remainderLevels = 0

    def __genJoinChances(self, num):
        joinChances = []
        for currChance in range(num):
            if hasattr(self, 'randomGenerator'):
                joinChances.append(self.randomGenerator.randint(1, 100))
            else:
                joinChances.append(random.randint(1, 100))

        joinChances.sort()
        return joinChances

    def _genSuitInfos(self, numFloors, bldgLevel):
        self.suitInfos = []
        self.notify.debug('\n\ngenerating suitsInfos with numFloors (' + str(numFloors) + ') bldgLevel (' + str(bldgLevel) + '+1) and bldgTracks (' + str(self.bldgTracks) + ')')
        for currFloor in range(numFloors):
            infoDict = {}
            lvls = self.__genLevelList(bldgLevel, currFloor, numFloors)
            activeDicts = []
            maxActive = min(4, len(lvls))
            if self.dbg_nSuits1stRound:
                numActive = min(self.dbg_nSuits1stRound, maxActive)
            else:
                numActive = random.randint(1, maxActive)
            if currFloor + 1 == numFloors and len(lvls) > 1:
                origBossSpot = len(lvls) - 1
                if numActive == 1:
                    newBossSpot = numActive - 1
                else:
                    newBossSpot = numActive - 2
                tmp = lvls[newBossSpot]
                lvls[newBossSpot] = lvls[origBossSpot]
                lvls[origBossSpot] = tmp
            if simbase.air.nerfsMode:
                bldgInfo = SuitBuildingGlobals.SuitBuildingInfoNerfs[bldgLevel]
            else:
                bldgInfo = SuitBuildingGlobals.SuitBuildingInfo[bldgLevel]
            if len(bldgInfo) > SuitBuildingGlobals.SUIT_BLDG_INFO_REVIVES:
                revives = bldgInfo[SuitBuildingGlobals.SUIT_BLDG_INFO_REVIVES][0]
            else:
                revives = 0
            for currActive in range(numActive - 1, -1, -1):
                level = lvls[currActive]
                type = self.__genNormalSuitType(level)
                activeDict = {}
                activeDict['type'] = type
                activeDict['track'] = self.chooseSuitTrack()
                activeDict['level'] = level
                activeDict['revives'] = revives
                activeDicts.append(activeDict)

            infoDict['activeSuits'] = activeDicts
            reserveDicts = []
            numReserve = len(lvls) - numActive
            joinChances = self.__genJoinChances(numReserve)
            for currReserve in range(numReserve):
                level = lvls[currReserve + numActive]
                type = self.__genNormalSuitType(level)
                reserveDict = {}
                reserveDict['type'] = type
                reserveDict['track'] = self.chooseSuitTrack()
                reserveDict['level'] = level
                reserveDict['revives'] = revives
                reserveDict['joinChance'] = joinChances[currReserve]
                reserveDicts.append(reserveDict)

            infoDict['reserveSuits'] = reserveDicts
            self.suitInfos.append(infoDict)

    def __genNormalSuitType(self, lvl):
        return SuitDNA.getRandomSuitType(lvl)

    def __genLevelList(self, bldgLevel, currFloor, numFloors):
        if simbase.air.nerfsMode:
            bldgInfo = SuitBuildingGlobals.SuitBuildingInfoNerfs[bldgLevel]
        else:
            bldgInfo = SuitBuildingGlobals.SuitBuildingInfo[bldgLevel]
        if self.dbg_1SuitPerFloor:
            return [1]
        else:
            if self.dbg_4SuitsPerFloor:
                return [5, 6, 7, 10]
        lvlPoolRange = bldgInfo[SuitBuildingGlobals.SUIT_BLDG_INFO_LVL_POOL]
        maxFloors = bldgInfo[SuitBuildingGlobals.SUIT_BLDG_INFO_FLOORS][1]
        lvlPoolMults = bldgInfo[SuitBuildingGlobals.SUIT_BLDG_INFO_LVL_POOL_MULTS]
        floorIdx = min(currFloor, maxFloors - 1)
        lvlPoolMin = lvlPoolRange[0] * lvlPoolMults[floorIdx]
        lvlPoolMax = lvlPoolRange[1] * lvlPoolMults[floorIdx]
        lvlPool = random.randint(int(lvlPoolMin), int(lvlPoolMax))
        lvlMin = bldgInfo[SuitBuildingGlobals.SUIT_BLDG_INFO_SUIT_LVLS][0]
        lvlMax = bldgInfo[SuitBuildingGlobals.SUIT_BLDG_INFO_SUIT_LVLS][1]
        self.notify.debug('Level Pool: ' + str(lvlPool))
        lvlList = []
        while lvlPool >= lvlMin:
            newLvl = random.randint(lvlMin, min(lvlPool, lvlMax))
            lvlList.append(newLvl)
            lvlPool -= newLvl

        if currFloor + 1 == numFloors:
            bossLvlRange = bldgInfo[SuitBuildingGlobals.SUIT_BLDG_INFO_BOSS_LVLS]
            newLvl = random.randint(bossLvlRange[0], bossLvlRange[1])
            lvlList.append(newLvl)
        lvlList.sort()
        self.notify.debug('LevelList: ' + repr(lvlList))
        return lvlList

    def genBldgCogs(self, floor, difficulty, battleNum):
        # TODO: use different seed for second battle.
        self.randomGenerator.seed(self.interior.becameSuitTime + floor)

        if simbase.air.nerfsMode:
            bldgInfo = SuitBuildingGlobals.SuitBuildingInfoNerfs[difficulty]
        else:
            bldgInfo = SuitBuildingGlobals.SuitBuildingInfo[difficulty]

        bossFloor = floor == self.numFloors - 1
        midpoint = self.numFloors / 2
        if bossFloor:
            floorType = SuitBuildingGlobals.FLOOR_TYPE_BOSS
        elif floor == 0:
            floorType = SuitBuildingGlobals.FLOOR_TYPE_FIRST
        elif isinstance(midpoint, float) and floor == math.ceil(midpoint):
            floorType = SuitBuildingGlobals.FLOOR_TYPE_MID
        elif floor <= midpoint:
            floorType = SuitBuildingGlobals.FLOOR_TYPE_LOW
        else:
            floorType = SuitBuildingGlobals.FLOOR_TYPE_HIGH

        lvlPool = bldgInfo[SuitBuildingGlobals.SUIT_BLDG_INFO_LVL_POOL]
        lvlPoolMult = bldgInfo[SuitBuildingGlobals.SUIT_BLDG_INFO_LVL_POOL_MULTS][floorType]
        lvlPoolMin = int(lvlPool[0] * lvlPoolMult)
        lvlPoolMax = int(lvlPool[1] * lvlPoolMult)
        remainingLevels = self.randomGenerator.randint(lvlPoolMin, lvlPoolMax) + self.remainderLevels

        minLevel = bldgInfo[SuitBuildingGlobals.SUIT_BLDG_INFO_SUIT_LVLS][0]
        maxLevel = bldgInfo[SuitBuildingGlobals.SUIT_BLDG_INFO_SUIT_LVLS][1]

        levels = []
        highestNumRequestedCogs = 0
        for toonId in self.interior.toons:
            toon = simbase.air.doId2do.get(toonId)
            if toon:
                if toon.getNumRequestedBldgCogs() > highestNumRequestedCogs:
                    highestNumRequestedCogs = toon.getNumRequestedBldgCogs()
                toon.setNumRequestedBldgCogs(0)

        if highestNumRequestedCogs:
            for i in range(highestNumRequestedCogs):
                level = self.randomGenerator.randint(minLevel, maxLevel)
                levels.append(level)
            self.remainderLevels = 0
        else:
            while remainingLevels >= minLevel:
                level = self.randomGenerator.randint(minLevel, maxLevel)
                remainingLevels -= level
                levels.append(level)
            self.remainderLevels = remainingLevels
        numCogs = len(levels) + 1 if bossFloor else len(levels)
        activeCogs = self.randomGenerator.randint(1, min(numCogs, 4))
        reserveCogs = len(levels) - activeCogs
        levels.sort()

        # Insert the boss level into the sorted list of levels
        if bossFloor:
            leaderIndex = 0 if activeCogs == 1 else 1
            bossLevelRange = bldgInfo[SuitBuildingGlobals.SUIT_BLDG_INFO_BOSS_LVLS]
            bossLevel = self.randomGenerator.randint(bossLevelRange[0], bossLevelRange[1])
            if battleNum == 1:
                bossLevel += 5
            levels.insert(leaderIndex, bossLevel)

        cogHandles = {}
        activeCogList = []
        reserveCogList = []

        self.previousNumCogs = activeCogs + reserveCogs
        for i in range(activeCogs):
            level = levels[0]
            suitInfo = self.boss if bossFloor and i == leaderIndex else None
            cogType = 0 if suitInfo else self.__genNormalSuitType(level)
            track = self.chooseSuitTrack()
            cog = self.__genSuitObject(self.zoneId, cogType, track, level, battleNum, suitInfo)
            activeCogList.append(cog)
            del levels[0]

        joinChances = self.__genJoinChances(reserveCogs)
        for i in range(reserveCogs):
            level = levels[0]
            cogType = self.__genNormalSuitType(level)
            track = self.chooseSuitTrack()
            cog = self.__genSuitObject(self.zoneId, cogType, track, level, battleNum, None)
            reserveCogList.append((cog, joinChances[i]))
            del levels[0]

        cogHandles['activeCogs'] = activeCogList
        cogHandles['reserveCogs'] = reserveCogList

        return cogHandles

    def __setupSuitInfo(self, suit, bldgTrack, suitLevel, suitType, suitInfo):
        suitName, special, virtual = simbase.air.suitInvasionManager.getInvadingCog()
        if suitInfo:
            suitName = suitInfo.get('name')
            if suitName:
                special = suitInfo.get('skelecog', 0)
                virtual = suitInfo.get('virtual', 0)
                suitLevel = suitInfo.get('level', simbase.air.datapackMgr.getCogCappedLevel(suitName, suitLevel))

        if suitName and self.respectInvasions and not suitInfo:
            if suitName.capitalize() in SuitDNA.suitDeptFullnames.values():
                suitName = SuitDNA.getRandomSuitByDept(Dept2NameDept.get(suitName.capitalize()))
            suitLevel = simbase.air.datapackMgr.getCogCappedLevel(suitName, suitLevel)
        if not self.respectInvasions:
            special = 0
            virtual = False

        dna = SuitDNA.SuitDNA()
        if suitName and self.respectInvasions:
            dna.newSuit(suitName)
        else:
            dna.newSuitRandom(suitType, bldgTrack)
        suit.dna = dna
        self.notify.debug('Creating suit type ' + suit.dna.name + ' of level ' + str(suitLevel))
        suit.setLevel(suitLevel)
        return special, virtual

    def __genSuitObject(self, suitZone, suitType, bldgTrack, suitLevel, revives=0, suitInfo = None):
        newSuit = DistributedSuitAI.DistributedSuitAI(simbase.air, None)
        special, virtual = self.__setupSuitInfo(newSuit, bldgTrack, suitLevel, suitType, suitInfo)
        if suitInfo:
            revives = suitInfo.get('revives', revives)
        if special == 1:
            newSuit.setSkelecog(1)
        elif revives:
            newSuit.setSkeleRevives(revives)
        elif special == 2:
            newSuit.setSkeleRevives(1)
        if virtual:
            newSuit.setVirtual(1)
        newSuit.generateWithRequired(suitZone)
        newSuit.node().setName('suit-%s' % newSuit.doId)
        return newSuit

    def myPrint(self):
        self.notify.info('Generated suits for building: ')
        for currInfo in suitInfos:
            whichSuitInfo = suitInfos.index(currInfo) + 1
            self.notify.debug(' Floor ' + str(whichSuitInfo) + ' has ' + str(len(currInfo[0])) + ' active suits.')
            for currActive in range(len(currInfo[0])):
                self.notify.debug('  Active suit ' + str(currActive + 1) + ' is of type ' + str(currInfo[0][currActive][0]) + ' and of track ' + str(currInfo[0][currActive][1]) + ' and of level ' + str(currInfo[0][currActive][2]))

            self.notify.debug(' Floor ' + str(whichSuitInfo) + ' has ' + str(len(currInfo[1])) + ' reserve suits.')
            for currReserve in range(len(currInfo[1])):
                self.notify.debug('  Reserve suit ' + str(currReserve + 1) + ' is of type ' + str(currInfo[1][currReserve][0]) + ' and of track ' + str(currInfo[1][currReserve][1]) + ' and of lvel ' + str(currInfo[1][currReserve][2]) + ' and has ' + str(currInfo[1][currReserve][3]) + '% join restriction.')

    def genFloorSuits(self, floor):
        suitHandles = {}
        floorInfo = self.suitInfos[floor]
        activeSuits = []
        for activeSuitInfo in floorInfo['activeSuits']:
            suit = self.__genSuitObject(self.zoneId, activeSuitInfo['type'], activeSuitInfo['track'], activeSuitInfo['level'], activeSuitInfo['revives'])
            activeSuits.append(suit)

        suitHandles['activeSuits'] = activeSuits
        reserveSuits = []
        for reserveSuitInfo in floorInfo['reserveSuits']:
            suit = self.__genSuitObject(self.zoneId, reserveSuitInfo['type'], reserveSuitInfo['track'], reserveSuitInfo['level'], reserveSuitInfo['revives'])
            reserveSuits.append((suit, reserveSuitInfo['joinChance']))

        suitHandles['reserveSuits'] = reserveSuits
        return suitHandles

    def genSuits(self):
        suitHandles = []
        for floor in range(len(self.suitInfos)):
            floorSuitHandles = self.genFloorSuits(floor)
            suitHandles.append(floorSuitHandles)

        return suitHandles

    def chooseSuitTrack(self):
        tracksLen = len(self.bldgTracks)
        if tracksLen == 1:
            return self.bldgTracks[0]

        return random.choices(self.bldgTracks, weights=SuitBuildingGlobals.MIXED_BLDG_TRACK_WEIGHT[tracksLen])[0]
