from .DistributedSZTreasure import DistributedSZTreasure


class DistributedDDLOTreasure(DistributedSZTreasure):

    def __init__(self, cr):
        DistributedSZTreasure.__init__(self, cr)
        self.modelPath = 'phase_4/models/props/ttrm_m_trsre_ddl_starPickup'
        self.grabSoundPath = 'phase_4/audio/sfx/SZ_DD_treasure.ogg'

    def loadModel(self, modelPath: str, modelFindString: str = None):
        DistributedSZTreasure.loadModel(self, modelPath, modelFindString)

        self.startBounceSpin()
