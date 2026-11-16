from direct.directnotify import DirectNotifyGlobal
from . import HoodDataAI, ZoneUtil
from toontown.toonbase import ToontownGlobals
from toontown.safezone import OZTreasurePlannerAI
from panda3d.core import *
from panda3d.toontown import *
from toontown.safezone import DistributedPicnicBasketAI
from toontown.classicchars import DistributedChipAI
from toontown.classicchars import DistributedDaleAI
from toontown.distributed import DistributedTimerAI
from toontown.safezone import DistributedPicnicTableAI
from toontown.safezone.DistributedPetParkAI import DistributedPetParkAI


class OZHoodDataAI(HoodDataAI.HoodDataAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('OZHoodDataAI')

    def __init__(self, air, zoneId=None):
        hoodId = ToontownGlobals.OutdoorZone
        if zoneId == None:
            zoneId = hoodId
        HoodDataAI.HoodDataAI.__init__(self, air, zoneId, hoodId)
        self.classicChars = []

    def startup(self):
        HoodDataAI.HoodDataAI.startup(self)
        if simbase.air.config.GetBool('create-chip-and-dale', 1) and self.air.disneyCharacters:
            chip = DistributedChipAI.DistributedChipAI(self.air)
            chip.generateWithRequired(self.zoneId)
            chip.start()
            self.addDistObj(chip)
            self.classicChars.append(chip)
            dale = DistributedDaleAI.DistributedDaleAI(self.air, chip.doId)
            dale.generateWithRequired(self.zoneId)
            dale.start()
            self.addDistObj(dale)
            self.classicChars.append(dale)
            chip.setDaleId(dale.doId)
        self.treasurePlanner = OZTreasurePlannerAI.OZTreasurePlannerAI(self.zoneId)
        self.treasurePlanner.start()
        self.timer = DistributedTimerAI.DistributedTimerAI(self.air)
        self.timer.generateWithRequired(self.zoneId)
        self.petPark = DistributedPetParkAI(self.air)
        self.petPark.generateWithRequired(ToontownGlobals.HiddenCamp)
        self.addDistObj(self.petPark)
        self.createPicnicTables()
        self.createGameTables()

    def cleanup(self):
        self.timer.delete()

    def findAndCreateGameTables(self, dnaGroup, zoneId, area, overrideDNAZone = 0, type = 'game_table'):
        picnicTables = []
        picnicTableGroups = []
        if isinstance(dnaGroup, DNAGroup) and dnaGroup.getName().find(type) >= 0:
            if type == 'game_table':
                nameInfo = dnaGroup.getName().split('_')
                pos = Point3(0, 0, 0)
                hpr = Point3(0, 0, 0)
                for i in range(dnaGroup.getNumChildren()):
                    childDnaGroup = dnaGroup.at(i)
                    if childDnaGroup.getName().find('game_table') >= 0:
                        pos = childDnaGroup.getPos()
                        hpr = childDnaGroup.getHpr()
                        break

                picnicTable = DistributedPicnicTableAI.DistributedPicnicTableAI(self.air, zoneId, nameInfo[2], pos[0], pos[1], pos[2], hpr[0], hpr[1], hpr[2])
                picnicTables.append(picnicTable)
        else:
            if isinstance(dnaGroup, DNAVisGroup) and not overrideDNAZone:
                zoneId = int(dnaGroup.getName().split(':')[0])
            for i in range(dnaGroup.getNumChildren()):
                childPicnicTables = self.findAndCreateGameTables(dnaGroup.at(i), zoneId, area, overrideDNAZone, type)
                picnicTables += childPicnicTables

        return picnicTables

    def findAndCreatePicnicTables(self, dnaGroup, zoneId, area, overrideDNAZone = 0, type = 'picnic_table'):
        picnicTables = []
        picnicTableGroups = []
        if isinstance(dnaGroup, DNAGroup) and dnaGroup.getName().find(type) >= 0:
            if type == 'picnic_table':
                nameInfo = dnaGroup.getName().split('_')
                pos = Point3(0, 0, 0)
                hpr = Point3(0, 0, 0)
                for i in range(dnaGroup.getNumChildren()):
                    childDnaGroup = dnaGroup.at(i)
                    if childDnaGroup.getName().find('picnic_table') >= 0:
                        pos = childDnaGroup.getPos()
                        hpr = childDnaGroup.getHpr()
                        break

                picnicTable = DistributedPicnicBasketAI.DistributedPicnicBasketAI(self.air, nameInfo[2], pos[0], pos[1], pos[2], hpr[0], hpr[1], hpr[2])
                picnicTable.generateWithRequired(zoneId)
                picnicTables.append(picnicTable)
        else:
            if isinstance(dnaGroup, DNAVisGroup) and not overrideDNAZone:
                zoneId = int(dnaGroup.getName().split(':')[0])
            for i in range(dnaGroup.getNumChildren()):
                childPicnicTables = self.findAndCreatePicnicTables(dnaGroup.at(i), zoneId, area, overrideDNAZone, type)
                picnicTables += childPicnicTables

        return picnicTables

    def createGameTables(self):
        self.gameTables = []
        for zone in self.air.zoneTable[self.canonicalHoodId]:
            zoneId = zone[0]
            dnaData = self.air.dnaDataMap.get(zoneId, None)
            if isinstance(dnaData, DNAData):
                area = ZoneUtil.getCanonicalZoneId(zoneId)
                foundTables = self.findAndCreateGameTables(dnaData, zoneId, area, overrideDNAZone=True)
                self.gameTables += foundTables

        for picnicTable in self.gameTables:
            self.addDistObj(picnicTable)

    def createPicnicTables(self):
        self.picnicTables = []
        for zone in self.air.zoneTable[self.canonicalHoodId]:
            zoneId = zone[0]
            dnaData = self.air.dnaDataMap.get(zoneId, None)
            if isinstance(dnaData, DNAData):
                area = ZoneUtil.getCanonicalZoneId(zoneId)
                foundTables = self.findAndCreatePicnicTables(dnaData, zoneId, area, overrideDNAZone=True)
                self.picnicTables += foundTables

        for picnicTable in self.picnicTables:
            picnicTable.start()
            self.addDistObj(picnicTable)
