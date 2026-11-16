from otp.level import DistributedLevelAI
from direct.directnotify import DirectNotifyGlobal
from . import LevelSuitPlannerAI
from . import FactoryBase
from . import FactoryEntityCreatorAI
from . import FactorySpecs
from otp.level import LevelSpec
from toontown.suit import DistributedFactorySuitAI
from toontown.toonbase import ToontownBattleGlobals
from toontown.coghq import DistributedBattleFactoryAI
from toontown.sandbox.DistributedPropGeneratorAI import DistributedPropGeneratorAI


class DistributedFactoryAI(DistributedLevelAI.DistributedLevelAI, FactoryBase.FactoryBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedFactoryAI')

    def __init__(self, air, factoryId, zoneId, entranceId, avIds):
        DistributedLevelAI.DistributedLevelAI.__init__(self, air, zoneId, entranceId, avIds)
        FactoryBase.FactoryBase.__init__(self)
        self.setFactoryId(factoryId)
        self.propGenerator = None

    def createEntityCreator(self):
        return FactoryEntityCreatorAI.FactoryEntityCreatorAI(level=self)

    def getBattleCreditMultiplier(self):
        return ToontownBattleGlobals.getFactoryCreditMultiplier(self.factoryId)

    def generate(self):
        self.notify.info('generate')
        self.notify.info('start factory %s %s creation, frame=%s' % (self.factoryId, self.doId, globalClock.getFrameCount()))
        if __dev__:
            simbase.factory = self
        self.notify.info('loading spec')
        specModule = FactorySpecs.getFactorySpecModule(self.factoryId)
        factorySpec = LevelSpec.LevelSpec(specModule)
        if __dev__:
            self.notify.info('creating entity type registry')
            typeReg = self.getEntityTypeReg()
            factorySpec.setEntityTypeReg(typeReg)
        self.notify.info('creating entities')
        DistributedLevelAI.DistributedLevelAI.generate(self, factorySpec)
        self.notify.info('creating cogs')
        cogSpecModule = FactorySpecs.getCogSpecModule(self.factoryId)
        nerfsOffset = 0
        if self.air.nerfsMode:
            nerfsOffset = 2
        self.planner = LevelSuitPlannerAI.LevelSuitPlannerAI(self.air, self, DistributedFactorySuitAI.DistributedFactorySuitAI, DistributedBattleFactoryAI.DistributedBattleFactoryAI, cogSpecModule.CogData, cogSpecModule.ReserveCogData, cogSpecModule.BattleCells, nerfsOffset=nerfsOffset)
        suitHandles = self.planner.genSuits()
        self.accept(f'deleteCogs-{self.zoneId}', self.__deleteFacilityCogs)
        messenger.send('plannerCreated-' + str(self.doId))
        self.suits = suitHandles['activeSuits']
        self.reserveSuits = suitHandles['reserveSuits']
        self.d_setSuits()
        scenario = 0
        description = '%s|%s|%s|%s' % (self.factoryId,
         self.entranceId,
         scenario,
         self.avIdList)
        for avId in self.avIdList:
            self.air.writeServerEvent('factoryEntered', avId, description)

        self.notify.info('finish factory %s %s creation' % (self.factoryId, self.doId))

    def generateWithRequired(self, zoneId):
        if self.air.propGenerator:
            self.propGenerator = DistributedPropGeneratorAI(self.air, zoneId)
            self.propGenerator.generateWithRequired(zoneId)
            self.air.propGenerators[self.zoneId] = self.propGenerator
        DistributedLevelAI.DistributedLevelAI.generateWithRequired(self, zoneId)

    # used in magic words to delete facility cogs.
    def __deleteFacilityCogs(self):
        suits = self.suits
        for reserve in self.reserveSuits:
            suits.append(reserve[0])
        for suit in suits:
            # if the suit has a battleTrap, it currently is in battle, therefore don't delete it.
            if not suit.isDeleted() and not hasattr(suit, 'battleTrap'):
                suit.requestDelete()

    def delete(self):
        self.notify.info('delete: %s' % self.doId)
        self.ignore(f'deleteCogs-{self.zoneId}')
        if __dev__:
            if hasattr(simbase, 'factory') and simbase.factory is self:
                del simbase.factory
        suits = self.suits
        for reserve in self.reserveSuits:
            suits.append(reserve[0])

        self.planner.destroy()
        del self.planner
        for suit in suits:
            if not suit.isDeleted():
                suit.factoryIsGoingDown()
                suit.requestDelete()

        DistributedLevelAI.DistributedLevelAI.delete(self)

    def getTaskZoneId(self):
        return self.factoryId

    def getFactoryId(self):
        return self.factoryId

    def d_setForemanConfronted(self, avId):
        if avId in self.avIdList:
            self.sendUpdate('setForemanConfronted', [avId])
        else:
            self.notify.warning('%s: d_setForemanConfronted: av %s not in av list %s' % (self.doId, avId, self.avIdList))

    def setVictors(self, victorIds):
        activeVictors = []
        activeVictorIds = []
        for victorId in victorIds:
            toon = self.air.doId2do.get(victorId)
            if toon is not None:
                activeVictors.append(toon)
                activeVictorIds.append(victorId)

        scenario = 0
        description = '%s|%s|%s|%s' % (self.factoryId,
         self.entranceId,
         scenario,
         activeVictorIds)
        for avId in activeVictorIds:
            self.air.writeServerEvent('factoryDefeated', avId, description)

        for toon in activeVictors:
            simbase.air.questManager.toonDefeatedFactory(toon, self.factoryId, activeVictors)

        return

    def b_setDefeated(self):
        self.d_setDefeated()
        self.setDefeated()

    def d_setDefeated(self):
        self.sendUpdate('setDefeated')

    def setDefeated(self):
        pass

    def getCogLevel(self):
        return self.cogLevel

    def d_setSuits(self):
        self.sendUpdate('setSuits', [self.getSuits(), self.getReserveSuits()])

    def getSuits(self):
        suitIds = []
        for suit in self.suits:
            suitIds.append(suit.doId)

        return suitIds

    def getReserveSuits(self):
        suitIds = []
        for suit in self.reserveSuits:
            suitIds.append(suit[0].doId)

        return suitIds
        
    # For compatibility with BBHQ entities
    def challengeDefeated(self):
        pass
