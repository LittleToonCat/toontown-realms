from direct.directnotify import DirectNotifyGlobal
from direct.interval.IntervalGlobal import *
from panda3d.core import Vec3, Point3

from .DistributedTreasure import DistributedTreasure


class DistributedPresent(DistributedTreasure):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPresent')

    def __init__(self, cr):
        DistributedTreasure.__init__(self, cr)
        self.grabSoundPath = 'phase_4/audio/sfx/MG_pairing_match_bonus_both.ogg'
        self.scale = 1
        self.dropShadowScale = 1
        self.animateIval = Parallel()

    def makeNodePath(self):
        DistributedTreasure.makeNodePath(self)
        self.nodePath.setScale(self.scale)
        self.dropShadow.setScale(self.dropShadowScale)

    def disable(self):
        self.animateIval.finish()
        DistributedTreasure.disable(self)

    def startAnimation(self):
        self.animateIval = Parallel(
                Sequence(
                        LerpPosInterval(self.treasure, 2, startPos = Vec3(0),
                                        pos = Vec3(0, 0, 1), blendType = 'easeInOut'),
                        LerpPosInterval(self.treasure, 2, startPos = Vec3(0, 0, 1),
                                        pos = Vec3(0), blendType = 'easeInOut')
                ),
                LerpHprInterval(self.treasure, 4, startHpr = Point3(0), hpr = Point3(360, 0, 0))
        )
        self.animateIval.loop()
