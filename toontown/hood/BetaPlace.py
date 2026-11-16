"""BetaPlace module: contains the BetaPlace class"""

from direct.directnotify.DirectNotifyGlobal import directNotify
from .Place import Place
from toontown.safezone.BetaWalk import BetaWalk
from toontown.toonbase import ClientSettings


class BetaPlace(Place):
    """This class is used to add additional functionality when entering/exiting Places in beta hoods.
    Examples include changing toon speed, jump behavior."""
    notify = directNotify.newCategory('BetaPlace')

    def load(self):
        Place.load(self)

        if ClientSettings.BetaPlaygroundMovement.get():
            # Don't use PublicWalk
            self.walkStateData.unload()
            del self.walkStateData

            # Use BetaWalk instead
            self.walkStateData = BetaWalk(self.fsm, self.walkDoneEvent)
            self.walkStateData.load()

    def enter(self):
        Place.enter(self)

        if ClientSettings.BetaPlaygroundInterface.get():
            base.localAvatar.chatMgr.showQuickTalkerButton()
            base.localAvatar.chatMgr.scButton.hide()

    def exit(self):
        if ClientSettings.BetaPlaygroundInterface.get():
            base.localAvatar.chatMgr.hideQuickTalkerButton()
            base.localAvatar.chatMgr.scButton.show()

        Place.exit(self)
