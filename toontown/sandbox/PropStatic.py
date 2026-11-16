"""
All generic static props for the prop generator will use this type
"""
from panda3d.core import Vec3, NodePathCollection, CollisionNode, NodePath

from toontown.sandbox.Prop import Prop
from toontown.sandbox import PropGlobals
from toontown.sandbox.PropGlobals import LIST_MODEL, PropPool
from toontown.toonbase import ToontownGlobals, ClientSettings
from toontown.toonbase.ToonBaseGlobal import base


class PropStatic(Prop):
    def __init__(self, generator, name, uuid, pos = Vec3(0, 0, 0), hpr = Vec3(0, 0, 0), scale = Vec3(1.0, 1.0, 1.0), data = {}):
        Prop.__init__(self, generator, name, uuid, pos, hpr, scale, data)
        self.model = PropPool.getProp(name)
        self.model.reparentTo(self)

        self.addSnapPoints()

        if 'offset' in self.attributes:
            PropPool.notify.debug(f'{name}: Setting position offset to {self.attributes["offset"]}')
            self.model.setPos(self.attributes['offset'])

        if not generator.isBuildLotOrEstate or not ClientSettings.PropGeneratorCollisions.get():
            collisions: NodePathCollection = self.findAllMatches('**/+CollisionNode')
            if collisions:
                coll: NodePath
                for coll in collisions:
                    if coll.getCollideMask() != ToontownGlobals.PropGenSnapPointBitMask:
                        coll.stash()
