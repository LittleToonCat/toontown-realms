from .DistributedPresent import DistributedPresent


class DistributedRedPresent(DistributedPresent):
    def __init__(self, cr):
        DistributedPresent.__init__(self, cr)
        self.modelPath = 'phase_6/models/karting/qbox'
        self.scale = 1.5
        self.dropShadowScale = 0.5
