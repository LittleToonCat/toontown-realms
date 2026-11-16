from direct.distributed.DistributedNode import DistributedNode
from panda3d.core import CollisionBox, Point3, CollisionNode

from toontown.sandbox.PropGlobals import PropPool
from toontown.toonbase.ToontownGlobals import WallBitmask, PieBitmask

class DistributedPropHuntProp(DistributedNode):

    def __init__(self, cr):
        DistributedNode.__init__(self, cr)

    def generate(self):
        super().generate()
        self.reparentTo(render)

    def disable(self):
        self.ignoreAll()
        super().disable()

    def delete(self):
        self.removeNode()
        super().delete()

    def setPropModel(self, model):
        # Generate prop
        prop = PropPool.getProp(model)
        prop.reparentTo(self)
        self.setupCollision(prop)

    def setupCollision(self, model):
        collisions = model.findAllMatches('**/+CollisionNode')

        if collisions:
            for coll in collisions:
                coll.setCollideMask(WallBitmask)
        else:
            # Some props don't have collisions, so gotta make one
            bMin, bMax = model.getTightBounds()
            collBox = CollisionBox(Point3(bMin), Point3(bMax))
            collNode = CollisionNode(f'propHuntProp-{self.getDoId()}')
            collNode.addSolid(collBox)
            collNode.setCollideMask(WallBitmask)
            collNodePath = self.attachNewNode(collNode)
