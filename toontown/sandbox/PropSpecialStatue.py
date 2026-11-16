"""
Toon Statue prop
Functions basically just like the SZ activity statue
"""
from panda3d.core import Vec3, NodePath, ShaderAttrib, Shader, CollisionSphere, CollisionNode

from toontown.sandbox.PropGlobals import PropPool
from toontown.sandbox.PropSpecial import PropSpecial
from toontown.toon.Toon import Toon
from toontown.toonbase import ToontownGlobals
from typing import Optional, Dict


class PropSpecialStatue(PropSpecial):
    stoneTexture = loader.loadTexture('phase_5.5/maps/smoothwall_1.png')

    desatShirtTex = loader.loadTexture('phase_3/maps/desat_shirt_1.png')
    desatSleeveTex = loader.loadTexture('phase_3/maps/desat_sleeve_1.png')
    desatShortsTex = loader.loadTexture('phase_3/maps/desat_shorts_1.png')
    desatSkirtTex = loader.loadTexture('phase_3/maps/desat_skirt_1.png')

    attr = ShaderAttrib.make(Shader.load(Shader.SLGLSL,
                                         fragment = 'phase_3/shaders/ttoff_sha_av_toon_statue.frag',
                                         vertex = 'phase_3/shaders/ttoff_sha_av_toon_statue.vert'))
    attr = attr.setFlag(ShaderAttrib.F_hardware_skinning, True)

    def __init__(self, generator, name, uuid, pos = Vec3(0, 0, 0), hpr = Vec3(0, 0, 0), scale = Vec3(1.0, 1.0, 1.0),
                 data: Optional[Dict] = None):
        PropSpecial.__init__(self, generator, name, uuid, pos, hpr, scale, data)
        self.model = PropPool.getProp(name)
        self.model.reparentTo(self)

        collisions = self.findAllMatches('**/+CollisionNode')
        if collisions:
            for coll in collisions:
                coll.stash()

        # Generate a blank toon
        self.toon = Toon()
        self.toon.reparentTo(self)
        self.toon.initializeBodyCollisions('toonStatue')
        self.toon.stopBlink()
        self.toon.stopLookAround()
        self.toon.setZ(3.29)

        # Apply the shader
        self.toon.setAttrib(self.attr)
        self.collSphere = CollisionSphere(0, 0, 2, 3)
        self.collSphere.setTangible(0)
        self.collNode = CollisionNode(self.collisionName)
        self.collNode.setCollideMask(ToontownGlobals.WallBitmask)
        self.collNode.addSolid(self.collSphere)
        self.collNodePath = self.attachNewNode(self.collNode)

        #self.accept(f'enter{self.collisionName}', self.__enterSphere)
        #self.setStoneTexture()

    def __enterSphere(self, collEntry = None):
        """
        Toon has entered the trigger sphere
        """
        #self.__createInteractHint()
        pass

    def __exitSphere(self, collEntry = None):
        self.ignore(f'exit{self.collisionName}')
        #self.__destroyInteractHint()