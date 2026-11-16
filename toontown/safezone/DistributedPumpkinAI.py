from direct.distributed import DistributedNodeAI


class DistributedPumpkinAI(DistributedNodeAI.DistributedNodeAI):

    def __init__(self, air, size='s', id=-1):
        try:
            self.DistributedPumpkinAI_initialized
        except:
            self.DistributedPumpkinAI_initialized = 1
            DistributedNodeAI.DistributedNodeAI.__init__(self, air)
            self.size = size
            self.id = id

    def getSize(self):
        return self.size

    def getId(self):
        return self.id

    def cleanup(self):
        self.d_cleanupPumpkin()
        taskMgr.doMethodLater(1.0, self.requestDelete, self.uniqueName('cleanup'), extraArgs=[])

    def d_generatePumpkin(self):
        self.sendUpdate('showPumpkin', [])

    def d_cleanupPumpkin(self):
        self.sendUpdate('hidePumpkin', [])
