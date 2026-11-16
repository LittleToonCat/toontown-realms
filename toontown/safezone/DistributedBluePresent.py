from .DistributedPresent import DistributedPresent


class DistributedBluePresent(DistributedPresent):
    def __init__(self, cr):
        DistributedPresent.__init__(self, cr)
        self.modelPath = 'phase_13/models/parties/tt_m_ara_pty_winterPresent'
        self.scale = 0.6
        self.dropShadowScale = 3.5
