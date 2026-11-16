from typing import Optional
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from direct.directnotify import DirectNotifyGlobal
from ..sandbox.DistributedPropGeneratorAI import DistributedPropGeneratorAI

class LobbyManagerAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('LobbyManagerAI')

    def __init__(self, air, bossConstructor):
        DistributedObjectAI.__init__(self, air)
        self.air = air
        self.bossConstructor = bossConstructor
        self.propGenerator: Optional[DistributedPropGeneratorAI] = None

    def generate(self):
        DistributedObjectAI.generate(self)
        self.notify.debug('generate')

    def generateWithRequired(self, zoneId: int):
        if self.air.propGenerator:
            self.propGenerator = DistributedPropGeneratorAI(self.air, zoneId)
            self.propGenerator.generateWithRequired(zoneId)
            self.air.propGenerators[zoneId] = self.propGenerator
        DistributedObjectAI.generateWithRequired(self, zoneId)

    def delete(self):
        self.notify.debug('delete')
        self.ignoreAll()
        if self.propGenerator:
            self.propGenerator.requestDelete()
            self.propGenerator = None
            if self.zoneId in self.air.propGenerators:
                del self.air.propGenerators[self.zoneId]
        del self.propGenerator
        DistributedObjectAI.delete(self)

    def createBossOffice(self, avIdList):
        bossZone = self.air.allocateZone()
        self.notify.info('createBossOffice: %s' % bossZone)
        bossCog = self.bossConstructor(self.air)
        for avId in avIdList:
            if avId:
                bossCog.addToon(avId)

        bossCog.generateWithRequired(bossZone)
        self.acceptOnce(bossCog.uniqueName('BossDone'), self.destroyBossOffice, extraArgs=[bossCog])
        bossCog.b_setState('WaitForToons')
        return bossZone

    def destroyBossOffice(self, bossCog):
        bossZone = bossCog.zoneId
        self.notify.info('destroyBossOffice: %s' % bossZone)
        bossCog.requestDelete()
        self.air.deallocateZone(bossZone)
