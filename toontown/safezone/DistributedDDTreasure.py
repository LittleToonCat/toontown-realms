from . import DistributedSZTreasure


class DistributedDDTreasure(DistributedSZTreasure.DistributedSZTreasure):

    def __init__(self, cr):
        DistributedSZTreasure.DistributedSZTreasure.__init__(self, cr)
        self.modelPath = 'phase_6/models/props/starfish_treasure' # 'phase_4/models/props/ttrm_m_trsre_dod_starPickup'
        self.grabSoundPath = 'phase_4/audio/sfx/SZ_DD_treasure.ogg'

    #def loadModel(self, modelPath: str, modelFindString: str = None):
    #    DistributedSZTreasure.DistributedSZTreasure.loadModel(self, modelPath, modelFindString)

    #    self.startBounceSpin()
