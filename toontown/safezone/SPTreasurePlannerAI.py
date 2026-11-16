from toontown.toonbase.ToontownGlobals import *
from . import RegenTreasurePlannerAI
from . import DistributedSPTreasureAI


class SPTreasurePlannerAI(RegenTreasurePlannerAI.RegenTreasurePlannerAI):

    def __init__(self, zoneId):
        self.healAmount = 3
        RegenTreasurePlannerAI.RegenTreasurePlannerAI.__init__(self, zoneId, DistributedSPTreasureAI.DistributedSPTreasureAI, 'SPTreasurePlanner', 20, 5)

    def initSpawnPoints(self):
        self.spawnPoints = [(232.67, -8.21, 0.02),
                            (161.57, -98.86, 0.02),
                            (86.57, -234.97, 0.02),
                            (39.79, -123.86, 0.02),
                            (86.75, -42.29, 0.02),
                            (105.72, 98.16, 0.02),
                            (134.93, 49.25, 0.02),
                            (-175.94, -83.60, 9.52),
                            (129.137, -61.9039, 0.02),
                            (-387.93, -115.00, 25.02),
                            (-321.26, 14.83, 25.02),
                            (-323.64, -278.69, 25.02)]
        return self.spawnPoints
