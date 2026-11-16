from direct.distributed.DistributedObject import DistributedObject


class PetParkManager(DistributedObject):
    neverDisable = 1

    def generate(self):
        DistributedObject.generate(self)
        base.cr.petParkMgr = self
