from . import DistributedToonAI
from direct.directnotify import DirectNotifyGlobal


# In the future, rewrite to be a slimmer version of DistributedToonAI, as this toon doesn't need everything like catalogs, etc.
class DistributedTemporaryToonAI(DistributedToonAI.DistributedToonAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedTemporaryToonAI')
    
    # Don't count these toons towards population
    def incrementPopulation(self):
        pass

    def decrementPopulation(self):
        pass

    def isTemporaryToon(self):
        return True