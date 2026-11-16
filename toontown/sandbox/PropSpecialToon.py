"""
Toon Statue prop
Functions basically just like the SZ activity statue
"""
from panda3d.core import Vec3, NodePath, ShaderAttrib, Shader, CollisionSphere, CollisionNode

from toontown.sandbox.PropGlobals import PropPool
from toontown.sandbox.PropSpecial import PropSpecial
from toontown.toon.Toon import Toon
from toontown.avatar.ToontownAvatarUtils import createUniqueToon
from toontown.toon.ToonDNA import ToonDNA
from toontown.toonbase import ToontownGlobals
from typing import Optional, Dict


class PropSpecialToon(PropSpecial):

    def __init__(self, generator, name, uuid, pos = Vec3(0, 0, 0), hpr = Vec3(0, 0, 0), scale = Vec3(1.0, 1.0, 1.0),
                 data: Optional[Dict] = None):
        PropSpecial.__init__(self, generator, name, uuid, pos, hpr, scale, data)

        # todo: replace this model with a like statue thingy. thiswill only really be used for the previews
        self.model = PropPool.getProp(name)
        self.model.reparentTo(hidden)

        collisions = self.findAllMatches('**/+CollisionNode')
        if collisions:
            for coll in collisions:
                coll.stash()

        # Generate a blank toon
        dna = ToonDNA()
        dna.newToonRandom()
        self.toon = createUniqueToon("test", dna)
        self.toon.reparentTo(self)
        self.toon.initializeBodyCollisions('toonStatue')

