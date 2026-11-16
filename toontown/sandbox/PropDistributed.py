"""
Dummy prop type for Distributed Props
This is pretty much only for saving the data stuff into the
"""
from panda3d.core import Vec3

from toontown.sandbox.Prop import Prop
from toontown.sandbox import PropGlobals
from toontown.sandbox.PropGlobals import LIST_MODEL, PropPool


class PropDistributed(Prop):
    def __init__(self, generator, name, uuid, pos = Vec3(0, 0, 0), hpr = Vec3(0, 0, 0), scale = Vec3(1.0, 1.0, 1.0), data = None):
        if data is None:
            data = {}
        Prop.__init__(self, generator, name, uuid, pos, hpr, scale, data)

