from panda3d.core import *
from . import BetaPlayground
import random
from direct.fsm import ClassicFSM, State
from direct.actor import Actor
from toontown.toonbase import ToontownGlobals

class MMBPlayground(BetaPlayground.BetaPlayground):

    def __init__(self, loader, parentFSM, doneEvent):
        BetaPlayground.BetaPlayground.__init__(self, loader, parentFSM, doneEvent)
        self.activityFsm = ClassicFSM.ClassicFSM('Activity', [State.State('off', self.enterOff, self.exitOff, ['OnPiano']), State.State('OnPiano', self.enterOnPiano, self.exitOnPiano, ['off'])], 'off', 'off')
        self.activityFsm.enterInitialState()

    def load(self):
        BetaPlayground.BetaPlayground.load(self)

    def unload(self):
        del self.activityFsm
        BetaPlayground.BetaPlayground.unload(self)

    def enter(self, requestStatus):
        BetaPlayground.BetaPlayground.enter(self, requestStatus)

    def exit(self):
        BetaPlayground.BetaPlayground.exit(self)

    def handleBookClose(self):
        BetaPlayground.BetaPlayground.handleBookClose(self)

    def teleportInDone(self):
        BetaPlayground.BetaPlayground.teleportInDone(self)

    def enterOff(self):
        return None

    def exitOff(self):
        return None

    def enterOnPiano(self):
        base.localAvatar.b_setParent(ToontownGlobals.SPMinniesPiano)

    def exitOnPiano(self):
        base.localAvatar.b_setParent(ToontownGlobals.SPRender)

    def showPaths(self):
        from toontown.classicchars import CCharPaths
        from toontown.toonbase import TTLocalizer
        self.showPathPoints(CCharPaths.getPaths(TTLocalizer.Minnie))
