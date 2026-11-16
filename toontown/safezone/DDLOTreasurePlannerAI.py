from .RegenTreasurePlannerAI import RegenTreasurePlannerAI
from .DistributedDDLOTreasureAI import DistributedDDLOTreasureAI

class DDLOTreasurePlannerAI(RegenTreasurePlannerAI):

    def __init__(self, zoneId):
        self.healAmount = 14
        RegenTreasurePlannerAI.__init__(self, zoneId, DistributedDDLOTreasureAI, 'DDLOTreasurePlanner', 20, 4)

    def initSpawnPoints(self):
        # TEMP SPAWN POINTS
        self.spawnPoints = [
            (209, 39.82, 0.51),
            (183.63, 13.04, 0.51),
            (246.09, 47.95, 0.51),
            (148.74, 104.16, 1.21),
            (145.96, -8.08, 1.21),
            (228.40, 102.95, 1.21),
            (278.30, 76.26, 14.65),
            (277.08, -33.27, 14.65),
            (154.28, -32.71, 14.65)
        ]
        return self.spawnPoints
