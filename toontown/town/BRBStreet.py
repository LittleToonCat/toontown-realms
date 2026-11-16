from . import BetaStreet

class BRBStreet(BetaStreet.BetaStreet):

    def __init__(self, loader, parentFSM, doneEvent):
        BetaStreet.BetaStreet.__init__(self, loader, parentFSM, doneEvent)

    def load(self):
        BetaStreet.BetaStreet.load(self)

    def unload(self):
        BetaStreet.BetaStreet.unload(self)
