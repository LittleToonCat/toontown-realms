from panda3d.core import *
from . import BetaPlayground
from direct.task.Task import Task
import random
from toontown.hood import Place
from toontown.toonbase import ToontownGlobals

class BRBPlayground(BetaPlayground.BetaPlayground):
    STILL = 1
    RUN = 2
    ROTATE = 3
    stillPos = Point3(0, 20, 8)
    runPos = Point3(0, 60, 8)
    rotatePos = Point3(0, 0, 8)
    timeFromStill = 1.0
    timeFromRotate = 2.0

    def __init__(self, loader, parentFSM, doneEvent):
        BetaPlayground.BetaPlayground.__init__(self, loader, parentFSM, doneEvent)

    def load(self):
        BetaPlayground.BetaPlayground.load(self)

    def unload(self):
        BetaPlayground.BetaPlayground.unload(self)

    def enter(self, requestStatus):
        BetaPlayground.BetaPlayground.enter(self, requestStatus)
        self.nextWindTime = 0
        taskMgr.add(self.__windTask, 'br-wind')
        self.state = 0

    def exit(self):
        taskMgr.remove('br-wind')
        taskMgr.remove('lerp-snow')
        BetaPlayground.BetaPlayground.exit(self)

    def enterTunnelOut(self, requestStatus):
        Place.Place.enterTunnelOut(self, requestStatus)

    def __windTask(self, task):
        now = globalClock.getFrameTime()
        if now < self.nextWindTime:
            return Task.cont
        randNum = random.random()
        wind = int(randNum * 100) % 3 + 1
        if wind == 1:
            base.playSfx(self.loader.wind1Sound)
        elif wind == 2:
            base.playSfx(self.loader.wind2Sound)
        elif wind == 3:
            base.playSfx(self.loader.wind3Sound)
        self.nextWindTime = now + randNum * 8.0
        return Task.cont

    def showPaths(self):
        from toontown.classicchars import CCharPaths
        from toontown.toonbase import TTLocalizer
        self.showPathPoints(CCharPaths.getPaths(TTLocalizer.Pluto))
