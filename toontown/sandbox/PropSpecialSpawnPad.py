"""
Spawn pad prop type.
This is a special prop that allows the owner of this prop to be able to spawn in its coodinates when teleporting into a zone.

TODO: show hologram of owner dna + name (?)
TODO: wonder if up to 5-10 avIds should be able to subscribe to a spawn pad instead of it being owner-only
"""

from panda3d.core import Vec3, NodePath

from toontown.sandbox.PropSpecial import PropSpecial


class PropSpecialSpawnPad(PropSpecial):
    localSpawnPads = []

    def __init__(self, generator, name, uuid, pos = Vec3(0, 0, 0), hpr = Vec3(0, 0, 0), scale = Vec3(1.0, 1.0, 1.0), data = {}):
        PropSpecial.__init__(self, generator, name, uuid, pos, hpr, scale, data)

        ownerId = self.data.get('spawned_by_avid', '$UNKNOWN')
        if ownerId == base.localAvatar.doId:
            PropSpecialSpawnPad.localSpawnPads.append(self)

    def removeNode(self):
        PropSpecial.removeNode(self)

        if self in PropSpecialSpawnPad.localSpawnPads:
            PropSpecialSpawnPad.localSpawnPads.remove(self)
        