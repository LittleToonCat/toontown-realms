from toontown.toonbase.ToontownGlobals import *
from . import RegenTreasurePlannerAI
from . import DistributedTTTreasureAI

class TTTreasurePlannerAI(RegenTreasurePlannerAI.RegenTreasurePlannerAI):

    def __init__(self, zoneId):
        self.healAmount = 3
        RegenTreasurePlannerAI.RegenTreasurePlannerAI.__init__(self, zoneId, DistributedTTTreasureAI.DistributedTTTreasureAI, 'TTTreasurePlanner', 20, 5)

    def initSpawnPoints(self):
        self.spawnPoints = [(-56.6, -16.10, -1.98),
         (-90.6, -5.77, -0.58),
         (27.1, -93.5, 2.5),
         (94.2, 33.5, 4),
         (35.4, 43.1, 4),
         (67.1, 105.5, 2.5),
         (-99.15, -87.3407, 0.52499),
         (1.60586, -119.492, 3.025),
         (46, -78.64, 3.025),
         (129.137, -61.9039, 2.525),
         (95, -158.399, 3.025),
         (111.749, -8.59927, 4.57466),
         (41.999, -30.2923, 4.025),
         (31.0649, -43.9149, 4.025),
         (10.5, 103, 2.525),
         (46.9667, 169.143, 3.025),
         (100.68, 93.9896, 2.525),
         (129.285, 58.6107, 2.525),
         (-28.6272, 85.9833, 0.525),
         (-114.613, 86.1727, 0.525),
         (-140, 31.32, 0.525)]
        return self.spawnPoints
