from .DistributedRaceGame import DistributedRaceGame
from toontown.suit import SuitDNA
from toontown.suit.Suit import Suit

import random, time


class DistributedRaceGameBeta(DistributedRaceGame):
    def __init__(self, cr):
        DistributedRaceGame.__init__(self, cr)
        self.suitId2Suit = {}

    def isBeta(self):
        return True

    def onstage(self):
        DistributedRaceGame.onstage(self)
        if self.numPlayers < 4:
            while len(self.suitId2Suit) < 4 - self.numPlayers:
                suit = Suit()
                dna = SuitDNA.SuitDNA()
                random.seed(time.time() * len(self.suitId2Suit))
                # Only allow Cogs rank 1 through 4
                level = random.randrange(1, 5)
                dna.newSuitRandom(level=level)
                suit.setDNA(dna)
                self.suitId2Suit[id(suit)] = suit

    def offstage(self):
        DistributedRaceGame.offstage(self)
        for suit in list(self.suitId2Suit.values()):
            suit.delete()

    def setGameReady(self):
        DistributedRaceGame.setGameReady(self)
        for i, suit in enumerate(list(self.suitId2Suit.values())):
            suit.reparentTo(render)
            self.setAnimState(suit, 'neutral', 1)
            self.positionInPlace(suit, i + self.numPlayers, 0)
            self.avIdList.append(id(suit))

        # This will make it easier to move the suits
        self.numPlayers += len(self.suitId2Suit)

    def moveCamera(self):
        # Camera didn't move in beta
        pass

    def getAvatar(self, avId):
        if avId in list(self.suitId2Suit.keys()):
            return self.suitId2Suit[avId]
        return DistributedRaceGame.getAvatar(self, avId)

    def resetPositions(self):
        DistributedRaceGame.resetPositions(self)
        for suit in list(self.suitId2Suit.values()):
            self.avatarPositions[id(suit)] = 0
