from . import Street


class BRStreet(Street.Street):

    def __init__(self, loader, parentFSM, doneEvent):
        Street.Street.__init__(self, loader, parentFSM, doneEvent)

    def enter(self, requestStatus):
        self.loader.hood.startAmbience()
        Street.Street.enter(self, requestStatus)

    def exit(self):
        self.loader.hood.stopAmbience()
        Street.Street.exit(self)
