from direct.directnotify import DirectNotifyGlobal
from direct.distributed.ClockDelta import *
from direct.interval.IntervalGlobal import *

from panda3d.core import *

from toontown.avatar import ToontownAvatarUtils
from toontown.battle import BattleProps
from toontown.suit import SuitDNA
from toontown.toonbase import ToontownGlobals

import random, time

FlyPaths = (((-279.401, -438.464, 85.0), (179.692, -327.786, 85.0)),
            ((268.928, -333.079, 85.0), (-486.369, -282.339, 85.0)),
            ((407.618, -197.317, 75.0), (-164.214, -262.931, 75.0)),
            ((333.982, -401.932, 75.0), (-269.932, -397.364, 75.0)),
            ((-303.809, -557.6, 85.0), (266.406, -457.633, 85.0)),
            ((-227.500, -241.773, 55.0), (115.916, -339.67, 55.0)))
Sellbots = ToontownGlobals.GreenEffectMassFlyCogs[0]


class FlyingCogs:
    notify = DirectNotifyGlobal.directNotify.newCategory('FlyingCogs')

    def __init__(self):
        self.suits = []
        self.intervals = []

    def startFlying(self, seed):
        currentTime = time.time()
        for x in range(len(FlyPaths)):
            # Create a suit
            flyPath = FlyPaths[x]
            index = FlyPaths.index(flyPath)
            seed -= index
            random.seed(seed + currentTime)
            suitType = random.choice(Sellbots)
            suit = ToontownAvatarUtils.createCog(suitType)
            suit.pose('landing', 0)
            if not suit.prop:
                suit.prop = BattleProps.globalPropPool.getProp('propeller')
                suit.prop.reparentTo(suit.find('**/joint_head'))
            suit.prop.loop('propeller', fromFrame=0, toFrame=8)
            x, y, z = flyPath[0]
            suit.setPos(x, y, z)
            self.suits.append(suit)

            # Intervals to fade the suit out and in
            fadeOutTrack = Sequence(Func(suit.setTransparency, 1),
                                    suit.colorScaleInterval(1, colorScale=VBase4(1, 1, 1, 0), startColorScale=VBase4(1, 1, 1, 1)))
            fadeInTrack = Sequence(Func(suit.setTransparency, 1),
                                   suit.colorScaleInterval(1, colorScale=VBase4(1, 1, 1, 1), startColorScale=VBase4(1, 1, 1, 0)),
                                   Func(suit.clearColorScale), Func(suit.clearTransparency))

            xDist = None
            self.lastX = None
            self.lastXDist = None
            beginWait = random.randint(0, 1)
            endWait = random.randint(1, 2)
            pathTrack = Sequence()

            for path in flyPath:
                self.pathX = path[0]
                self.pathY = path[1]
                if self.lastX:
                    if self.lastX > self.pathX:
                        xDist = self.lastX - self.pathX
                    elif self.lastX < self.pathX:
                        xDist = self.pathX - self.lastX
                    else:
                        xDist = 0
                    if self.lastY > self.pathY:
                        yDist = self.lastY - self.pathY
                    elif self.lastY < self.pathY:
                        yDist = self.pathY - self.lastY
                    else:
                        yDist = 0

                self.lastX = self.pathX
                self.lastY = self.pathY

                if xDist != None:
                    self.lastXDist = xDist
                    self.lastYDist = yDist

                if self.lastXDist != None:
                    duration = (xDist + yDist) / 15
                    endPoint = Point3(path[0], path[1], path[2])
                    pathTrack.append(Sequence(Func(suit.headsUp, endPoint), Parallel(fadeInTrack, Wait(beginWait)), suit.posInterval(duration, endPoint),
                                              Parallel(fadeOutTrack, Wait(endWait)), Func(suit.setPos, x, y, z), Func(self.resetDNA, suit, seed), Wait(endWait)))
            pathTrack.loop()
            random.seed(seed + currentTime)
            offset = random.randrange(0, 30)
            pathTrack.setT(offset)
            self.intervals.append(pathTrack)

    def resetDNA(self, suit, seed):
        # Hide the propeller
        suit.prop.reparentTo(hidden)

        # Generate new DNA for them
        dna = SuitDNA.SuitDNA()
        currentTime = time.time()
        random.seed(seed + currentTime)
        suitType = random.choice(Sellbots)
        dna.newSuit(suitType)
        suit.setDNA(dna)

        # Remove old suit and generate the new one
        suit.getGeomNode().getChildren().getPath(0).removeNode()
        suit.generateSuit()

        # Pose them as landing and reparent propeller to head
        suit.pose('landing', 0)
        suit.prop.reparentTo(suit.find('**/joint_head'))

    def delete(self):
        for interval in self.intervals:
            interval.finish()
        del self.intervals

        for suit in self.suits:
            suit.removeActive()
            suit.cleanup()
            suit.removeNode()
        del self.suits
