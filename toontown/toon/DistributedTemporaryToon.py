from . import DistributedToon
from direct.directnotify import DirectNotifyGlobal


# In the future, rewrite to be a slimmer version of DistributedToon, as this toon doesn't need everything like catalogs, etc.
class DistributedTemporaryToon(DistributedToon.DistributedToon):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedTemporaryToon')