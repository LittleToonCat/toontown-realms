from toontown.toonbase.ToontownGlobals import *
from . import RegenTreasurePlannerAI
from . import DistributedTTTreasureAI

class TTBTreasurePlannerAI(RegenTreasurePlannerAI.RegenTreasurePlannerAI):

    def __init__(self, zoneId):
        self.healAmount = 3
        RegenTreasurePlannerAI.RegenTreasurePlannerAI.__init__(self, zoneId, DistributedTTTreasureAI.DistributedTTTreasureAI, 'TTBTreasurePlanner', 20, 5)

    def initSpawnPoints(self):
        self.spawnPoints = [(47.9, -93.3, 6.7),
                            (134.7, 9.2, -1.3),
                            (141.5, -58.1, -1.3),
                            (77.05, -66.75, -1.3),
                            (109.8, -31.6, 1.9),
                            (172.8, 29.9, 6.7),
                            (42.65, 27.9, 6.7),
                            (194.1, -60.1, 6.7),
                            (83.8, -24.4, -1.3)]
        return self.spawnPoints
