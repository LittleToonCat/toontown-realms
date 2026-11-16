from .DistributedRaceGameAI import DistributedRaceGameAI
from . import RaceGameGlobals
import random


class DistributedRaceGameBetaAI(DistributedRaceGameAI):
    def announceGenerate(self):
        DistributedRaceGameAI.announceGenerate(self)
        self.suitPositions = [0] * (4 - self.numPlayers)
        self.suitChoices = [0] * (4 - self.numPlayers)

    def enterProcessChoices(self):
        validChoices = RaceGameGlobals.ValidChoices
        for i in range(len(self.suitPositions)):
            choice = random.randint(validChoices[1], validChoices[-1])
            self.suitChoices[i] = choice

        DistributedRaceGameAI.enterProcessChoices(self)

    def checkForWinners(self):
        allChoices = list(list(self.avatarChoices.values()) + self.suitChoices)

        for i in range(len(self.suitPositions)):
            choice = self.suitChoices[i]
            freq = allChoices.count(choice)
            self.processSuitChoice(i, choice, freq)

        del allChoices

        DistributedRaceGameAI.checkForWinners(self)

    def processChoice(self, avId, choice, freq = 1):
        # We need to count the cog choices too
        freq += self.suitChoices.count(choice)

        DistributedRaceGameAI.processChoice(self, avId, choice, freq)

    def processSuitChoice(self, index, choice, freq=1):
        self.notify.debug('processSuitChoice: index = ' + str(index) + ' choice = ' + str(choice))
        if freq == 1:
            if choice != 0:
                if self.suitPositions[index] < RaceGameGlobals.NumberToWin:
                    self.suitPositions[index] += choice
                    if self.suitPositions[index] < 0:
                        self.suitPositions[index] = 0
        self.choiceArray.append(choice)
        self.positionArray.append(self.suitPositions[index])
        self.notify.debug('Process suit choice (' + str(choice) + ') for index: ' + str(index))
        self.notify.debug('      choiceArray: ' + str(self.choiceArray))
        self.notify.debug('    positionArray: ' + str(self.positionArray))

    def anyAvatarWon(self, positionDict):
        for position in self.suitPositions:
            if position >= RaceGameGlobals.NumberToWin:
                self.notify.debug('anyAvatarWon: A suit won')
                return 1

        return DistributedRaceGameAI.anyAvatarWon(self, positionDict)

    def isBeta(self):
        return True
