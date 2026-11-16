from . import DistributedSZTreasure
from ..toonbase import ClientSettings


class DistributedETreasure(DistributedSZTreasure.DistributedSZTreasure):

    def __init__(self, cr):
        DistributedSZTreasure.DistributedSZTreasure.__init__(self, cr)
        if ClientSettings.EstatePopsicleTreasures.get():
            self.modelPath = 'phase_5.5/models/props/popsicle_treasure'
        else:
            self.modelPath = 'phase_4/models/props/icecream'
        self.grabSoundPath = 'phase_4/audio/sfx/SZ_DD_treasure.ogg'
