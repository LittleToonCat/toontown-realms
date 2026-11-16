"""BetaStreet module: contains the BetaStreet class"""

from direct.directnotify.DirectNotifyGlobal import directNotify
from .Street import Street
from toontown.hood.BetaPlace import BetaPlace


class BetaStreet(Street, BetaPlace):
    notify = directNotify.newCategory('BetaStreet')

    def load(self):
        Street.load(self)
        BetaPlace.load(self)

    def enter(self, requestStatus, visibilityFlag = 1, arrowsOn = 1):
        Street.enter(self, requestStatus, visibilityFlag, arrowsOn)
        BetaPlace.enter(self)

    def exit(self, visibilityFlag=1):
        BetaPlace.exit(self)
        Street.exit(self, visibilityFlag)
