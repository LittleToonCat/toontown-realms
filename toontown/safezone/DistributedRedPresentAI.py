from .DistributedPresentAI import DistributedPresentAI


class DistributedRedPresentAI(DistributedPresentAI):
    def __init__(self, air, treasurePlanner, x, y, z):
        DistributedPresentAI.__init__(self, air, treasurePlanner, x, y, z)
        self.moneyMult = 2
