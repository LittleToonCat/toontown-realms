from . import BetaPlayground

class DGBPlayground(BetaPlayground.BetaPlayground):

    def __init__(self, loader, parentFSM, doneEvent):
        BetaPlayground.BetaPlayground.__init__(self, loader, parentFSM, doneEvent)
        self.parentFSM = parentFSM

    def showPaths(self):
        from toontown.classicchars import CCharPaths
        from toontown.toonbase import TTLocalizer
        self.showPathPoints(CCharPaths.getPaths(TTLocalizer.Goofy))
