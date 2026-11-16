from direct.distributed.DistributedObjectAI import DistributedObjectAI


class DistributedSnowPileManagerAI(DistributedObjectAI):
    def __init__(self, air, pileInfo, numSnowBalls=20):
        DistributedObjectAI.__init__(self, air)

        self.pileInfo = pileInfo
        self.numSnowBalls = numSnowBalls

    def getPileInfo(self):
        return self.pileInfo

    def touchedSnow(self):
        avId = self.air.getAvatarIdFromSender()
        toon = self.air.doId2do.get(avId)
        if toon:
            toon.b_setPieType(8)
            toon.b_setNumPies(self.numSnowBalls)
