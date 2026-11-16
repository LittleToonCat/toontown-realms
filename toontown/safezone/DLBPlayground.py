from panda3d.core import *
from . import BetaPlayground
import random

class DLBPlayground(BetaPlayground.BetaPlayground):

    def __init__(self, loader, parentFSM, doneEvent):
        BetaPlayground.BetaPlayground.__init__(self, loader, parentFSM, doneEvent)

    def showPaths(self):
        from toontown.classicchars import CCharPaths
        from toontown.toonbase import TTLocalizer
        self.showPathPoints(CCharPaths.getPaths(TTLocalizer.Donald))
