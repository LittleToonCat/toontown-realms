from .DistributedPresentAI import DistributedPresentAI


class DistributedBluePresentAI(DistributedPresentAI):
    def __init__(self, air, treasurePlanner, x, y, z):
        DistributedPresentAI.__init__(self, air, treasurePlanner, x, y, z)
