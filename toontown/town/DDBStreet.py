from . import BetaStreet

class DDBStreet(BetaStreet.BetaStreet):

    def __init__(self, loader, parentFSM, doneEvent):
        BetaStreet.BetaStreet.__init__(self, loader, parentFSM, doneEvent)

    def load(self):
        BetaStreet.BetaStreet.load(self)

    def unload(self):
        BetaStreet.BetaStreet.unload(self)

    def enter(self, requestStatus):
        self.loader.hood.setWhiteFog()
        BetaStreet.BetaStreet.enter(self, requestStatus)

    def exit(self):
        self.loader.hood.setNoFog()
        BetaStreet.BetaStreet.exit(self)
