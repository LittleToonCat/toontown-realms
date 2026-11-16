from direct.distributed import DistributedNode
from panda3d.core import NodePath

from . import Pumpkin


class DistributedPumpkin(Pumpkin.Pumpkin, DistributedNode.DistributedNode):

    def __init__(self, cr):
        try:
            self.DistributedPump_initialized
        except:
            self.DistributedPump_initialized = 1
            DistributedNode.DistributedNode.__init__(self, cr)
            Pumpkin.Pumpkin.__init__(self)

    def announceGenerate(self):
        super().announceGenerate()
        self.generatePumpkin()

        anim = self.getAnim(self.id)
        anim.loop()
        self.set_name(f'decorPumpkin{self.getDoId()}')
