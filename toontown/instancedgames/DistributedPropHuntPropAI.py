from direct.distributed.DistributedNodeAI import DistributedNodeAI


class DistributedPropHuntPropAI(DistributedNodeAI):

    def __init__(self, air):  # , propType):
        DistributedNodeAI.__init__(self, air)
        self.model = None

    def d_setPropModel(self, model):
        self.model = model

        self.sendUpdate('setPropModel', [model])
