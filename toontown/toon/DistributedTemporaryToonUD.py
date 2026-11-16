from . import DistributedToonUD
from direct.directnotify import DirectNotifyGlobal


# In the future, rewrite to be a slimmer version of DistributedToonUD, as this toon doesn't need everything like catalogs, etc.
class DistributedTemporaryToonUD(DistributedToonUD.DistributedToonUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedTemporaryToonUD')