"""
Base class for all special props to inherit from
"""
from panda3d.core import Vec3, NodePath

from toontown.sandbox.Prop import Prop
from typing import Optional, Dict

class PropSpecial(Prop):
    def __init__(self, generator, name, uuid, pos = Vec3(0, 0, 0), hpr = Vec3(0, 0, 0), scale = Vec3(1.0, 1.0, 1.0), data: Optional[Dict] = None):
        Prop.__init__(self, generator, name, uuid, pos, hpr, scale, data)
