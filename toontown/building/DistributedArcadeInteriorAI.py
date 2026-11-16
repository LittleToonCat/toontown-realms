from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from toontown.arcade.DistributedTestGameArcadeMachineAI import DistributedTestGameArcadeMachineAI


class DistributedArcadeInteriorAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedArcadeInteriorAI')

    def __init__(self, block, air, zoneId):
        DistributedObjectAI.__init__(self, air)
        self.block = block
        self.zoneId = zoneId

    def generate(self):
        DistributedObjectAI.generate(self)
        self.testMachine = DistributedTestGameArcadeMachineAI(self.air)
        self.testMachine.generateWithRequired(self.zoneId)

    def getZoneIdAndBlock(self):
        return [self.zoneId, self.block]
