from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObject import DistributedObject

class DistributedDistrict(DistributedObject):
    notify = directNotify.newCategory('DistributedDistrict')
    neverDisable = 1

    def __init__(self, cr):
        DistributedObject.__init__(self, cr)
        self.name = 'NotGiven'
        self.available = 0
        self.full = 0
        self.avatarCount = 0
        self.newAvatarCount = 0

    def announceGenerate(self):
        DistributedObject.announceGenerate(self)
        base.cr.distributedDistrict = self
        messenger.send('shardInfoUpdated')

    def delete(self):
        if base.cr.distributedDistrict is self:
            base.cr.distributedDistrict = None
        DistributedObject.delete(self)
        messenger.send('shardInfoUpdated')

    def setAvailable(self, available):
        self.available = available
        messenger.send('shardInfoUpdated')

    def setFull(self, full):
        self.full = full
        messenger.send('shardInfoUpdated')

    def setName(self, name):
        self.name = name
        messenger.send('shardInfoUpdated')
