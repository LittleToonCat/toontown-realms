from direct.directnotify import DirectNotifyGlobal
from .RegenTreasurePlannerAI import RegenTreasurePlannerAI
from .DistributedRedPresentAI import DistributedRedPresentAI
from .DistributedBluePresentAI import DistributedBluePresentAI
from toontown.toonbase import ToontownGlobals

import random


class RegenPresentPlannerAI(RegenTreasurePlannerAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('RegenPresentPlannerAI')

    def __init__(self, zoneId):
        RegenTreasurePlannerAI.__init__(self, zoneId, (DistributedRedPresentAI, DistributedBluePresentAI),
                                        'RegenPresentPlanner-' + str(zoneId), 20, 5)

    def start(self):
        self.rng = random.Random()
        self.rng.seed(self.zoneId)

        RegenTreasurePlannerAI.start(self)

    def stop(self):
        del self.rng

        RegenTreasurePlannerAI.stop(self)

    def initSpawnPoints(self):
        self.spawnPoints = ToontownGlobals.WinterPresentInfo.get(self.zoneId, [])
        return self.spawnPoints

    def placeTreasure(self, index):
        spawnPoint = self.spawnPoints[index]
        randVal = self.rng.random()
        # Red treasures give more jellybeans so we're gonna make them rarer
        if randVal > 0.75:
            constructor = self.treasureConstructor[0]
        else:
            constructor = self.treasureConstructor[1]
        treasure = constructor(simbase.air, self, spawnPoint[0], spawnPoint[1], spawnPoint[2])
        treasure.generateWithRequired(self.zoneId)
        self.treasures[index] = treasure
