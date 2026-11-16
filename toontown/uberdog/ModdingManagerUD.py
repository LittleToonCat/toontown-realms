from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectGlobalUD import DistributedObjectGlobalUD


class ModdingManagerUD(DistributedObjectGlobalUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('ModdingManagerUD')

    def __init__(self, air):
        DistributedObjectGlobalUD.__init__(self, air)
        self.cards = {}
        self.defaultMaxToon = False

    def setDefaultMaxToonAiToUd(self, state):
        self.defaultMaxToon = state

    def getDefaultMaxToon(self):
        return self.defaultMaxToon

    def setCardsAiToUd(self, cards):
        self.cards = cards

    def getCards(self):
        return self.cards

