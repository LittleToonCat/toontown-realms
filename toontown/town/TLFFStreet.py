from . import Street


class TLFFStreet(Street.Street):

    def __init__(self, loader, parentFSM, doneEvent):
        super().__init__(loader, parentFSM, doneEvent)

    def load(self):
        super().load()

    def unload(self):
        super().unload()
