"""BetaPlayground module: contains the BetaPlayground class"""

from direct.directnotify.DirectNotifyGlobal import directNotify
from .Playground import Playground
from toontown.hood.BetaPlace import BetaPlace


class BetaPlayground(Playground, BetaPlace):
    notify = directNotify.newCategory('BetaPlayground')

    def load(self):
        Playground.load(self)
        BetaPlace.load(self)

    def enter(self, requestStatus):
        Playground.enter(self, requestStatus)
        BetaPlace.enter(self)

    def exit(self):
        BetaPlace.exit(self)
        Playground.exit(self)
