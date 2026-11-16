from . import Playground
from toontown.effects.Fireflies import Fireflies
from typing import Optional

class DLPlayground(Playground.Playground):

    def __init__(self, loader, parentFSM, doneEvent):
        Playground.Playground.__init__(self, loader, parentFSM, doneEvent)
        self.fireflies: Optional[Fireflies] = None

    def showPaths(self):
        from toontown.classicchars import CCharPaths
        from toontown.toonbase import TTLocalizer
        self.showPathPoints(CCharPaths.getPaths(TTLocalizer.Donald))

    def enter(self, requestStatus):
        Playground.Playground.enter(self, requestStatus)

        self.fireflies = Fireflies()
        self.fireflies.reparentTo(base.localAvatar)
        self.fireflies.startLoop()

    def exit(self):
        if self.fireflies is not None:
            self.fireflies.destroy()
        Playground.Playground.exit(self)