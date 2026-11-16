from direct.directnotify import DirectNotifyGlobal
from . import HoodDataAI, ZoneUtil
from toontown.toonbase import ToontownGlobals
from toontown.safezone import DistributedPicnicBasketAI, DistributedSafezoneJukeboxAI,\
    DistributedPicnicTableAI, SPTreasurePlannerAI, DistributedTrolleyAI
from panda3d.core import Point3
from panda3d.toontown import *


class SpecialHoodDataAI(HoodDataAI.HoodDataAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('SpecialHoodDataAI')

    def __init__(self, air, zoneId=None):
        hoodId = ToontownGlobals.ToontownOutskirts
        if zoneId == None:
            zoneId = hoodId
        HoodDataAI.HoodDataAI.__init__(self, air, zoneId, hoodId)
        return

    def startup(self):
        HoodDataAI.HoodDataAI.startup(self)

        trolley = DistributedTrolleyAI.DistributedTrolleyAI(self.air)
        trolley.generateWithRequired(self.zoneId)
        trolley.start()
        self.addDistObj(trolley)

        self.treasurePlanner = SPTreasurePlannerAI.SPTreasurePlannerAI(self.zoneId)
        self.treasurePlanner.start()

        self.safezoneJukebox = DistributedSafezoneJukeboxAI.DistributedSafezoneJukeboxAI(self.air, 138, -235, 0, 180, self.zoneId)
        self.safezoneJukebox.generateWithRequired(self.zoneId)
        self.addDistObj(self.safezoneJukebox)

        self.createPicnicTables()
        self.createGameTables()

    def _deleteTrolley(self, task):
        self.trolley.requestDelete()
        taskMgr.doMethodLater(0.5, self._createTrolley, 'createTrolley')
        return task.done

    def _createTrolley(self, task):
        trolley = DistributedTrolleyAI.DistributedTrolleyAI(self.air)
        trolley.setBeta(True)
        trolley.generateWithRequired(self.zoneId)
        trolley.start()
        self.trolley = trolley
        taskMgr.doMethodLater(0.5, self._deleteTrolley, 'deleteTrolley')
        return task.done

    def findAndCreateGameTables(self, dnaGroup, zoneId, area, overrideDNAZone = 0, type = 'game_table'):
        picnicTables = []
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
