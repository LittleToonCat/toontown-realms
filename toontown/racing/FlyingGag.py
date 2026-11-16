from panda3d.core import *
from panda3d.physics import ActorNode
from otp.avatar.ShadowCaster import ShadowCaster


class FlyingGag(NodePath, ShadowCaster):
    def __init__(self, name='flyingGagAN', geom = None):
        an = ActorNode(name)
        NodePath.__init__(self, an)
        self.actorNode = an
        self.gag = None
        self.gagNode = None
        ShadowCaster.__init__(self)
        if geom:
            self.gagNode = self.attachNewNode('PieNode')
            self.gag = geom.copyTo(self.gagNode)
            self.gag.setScale(3)
            self.gagNode.setHpr(0, -45, 0)
            self.gagNode.setPos(0, 0, 2)
            self.initializeDropShadow()
            self.setActiveShadow()
            self.dropShadow.setPos(0, 0, 2)
            self.dropShadow.setScale(3)
        return

    def delete(self):
        ShadowCaster.delete(self)
        NodePath.removeNode(self)
        self.gag = None
        return

    def getGeomNode(self):
        return self.gag
