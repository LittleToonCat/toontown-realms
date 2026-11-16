from .DistributedMinigameAI import *
from toontown.ai.ToonBarrier import *
from direct.fsm import ClassicFSM, State
import random
from . import PatternGameGlobals


class DistributedPatternGameBetaAI(DistributedMinigameAI):

    def __init__(self, air, minigameId):
        try:
            self.DistributedPatternGameBetaAI_initialized
        except:
            self.DistributedPatternGameBetaAI_initialized = 1
            DistributedMinigameAI.__init__(self, air, minigameId)
            self.gameFSM = ClassicFSM.ClassicFSM('DistributedPatternGameBetaAI', [State.State('off', self.enterInactive, self.exitInactive, ['waitClientsReady', 'cleanup']),
             State.State('waitClientsReady', self.enterWaitClientsReady, self.exitWaitClientsReady, ['generatePattern', 'cleanup']),
             State.State('generatePattern', self.enterGeneratePattern, self.exitGeneratePattern, ['waitForResults', 'cleanup']),
             State.State('waitForResults', self.enterWaitForResults, self.exitWaitForResults, ['waitClientsReady', 'cleanup']),
             State.State('cleanup', self.enterCleanup, self.exitCleanup, [])], 'off', 'cleanup')
            self.addChildGameFSM(self.gameFSM)

    def delete(self):
        self.notify.debug('delete')
        del self.gameFSM
        DistributedMinigameAI.delete(self)

    def setGameReady(self):
        self.notify.debug('setGameReady')
        DistributedMinigameAI.setGameReady(self)
        self.__initGameVars()

    def setGameStart(self, timestamp):
        self.notify.debug('setGameStart')
        DistributedMinigameAI.setGameStart(self, timestamp)
        self.gameFSM.request('waitClientsReady')

    def setGameAbort(self, normalExit = 0):
        self.notify.debug('setGameAbort')
        if self.gameFSM.getCurrentState():
            self.gameFSM.request('cleanup')
        DistributedMinigameAI.setGameAbort(self, normalExit)

    def gameOver(self):
        self.notify.debug('gameOver')
        self.gameFSM.request('cleanup')
        DistributedMinigameAI.gameOver(self)

    def enterInactive(self):
        self.notify.debug('enterInactive')

    def exitInactive(self):
        pass

    def __initGameVars(self):
        self.pattern = []
        self.round = 0
        if self.isSinglePlayer():
            self.__madeAMistake = False
            self.__chances = PatternGameGlobals.SP_NUM_CHANCES
        self.perfectResults = {}
        for avId in self.avIdList:
            self.perfectResults[avId] = 1

        self.readyClients = []
        self.timeoutTaskName = self.uniqueName('PatternGameResultsTimeout')

    def enterWaitClientsReady(self):
        self.notify.debug('enterWaitClientsReady')
        self.nextRoundBarrier = ToonBarrier('nextRoundReady', self.uniqueName('nextRoundReady'), self.avIdList, PatternGameGlobals.ClientsReadyTimeout, self.__allPlayersReady, self.__clientsReadyTimeout)
        for avId in self.readyClients:
            self.nextRoundBarrier.clear(avId)

    def clientReadyForNextRound(self):
        if not self._inState('waitClientsReady'):
            return

        avId = self.air.getAvatarIdFromSender()

        if avId not in self.avIdList:
            self.notify.warning('Got clientReadyForNextRound from an avId: %s not in our list: %s' % (avId, self.avIdList))
        else:
            self.readyClients.append(avId)
            self.nextRoundBarrier.clear(avId)

    def __allPlayersReady(self):
        self.readyClients = []
        self.gameFSM.request('generatePattern')

    def __clientsReadyTimeout(self, avIds):
        self.notify.debug('__clientsReadyTimeout: clients %s have not responded' % avIds)
        self.setGameAbort()

    def exitWaitClientsReady(self):
        self.nextRoundBarrier.cleanup()
        del self.nextRoundBarrier

    def enterGeneratePattern(self):
        self.notify.debug('enterGeneratePattern')
        if self.isSinglePlayer():
            if not self.__madeAMistake:
                self.round += 1
            else:
                self.__madeAMistake = False
        else:
            self.round += 1
        targetLen = PatternGameGlobals.INITIAL_LENGTH + PatternGameGlobals.INCREMENT * (self.round - 1)
        count = targetLen - len(self.pattern)

        for i in range(0, count):
            buttonVal = random.randint(0, 3)
            self.pattern.append(buttonVal)

        self.gameFSM.request('waitForResults')
        self.sendUpdate('setPattern', [self.pattern])

    def exitGeneratePattern(self):
        pass

    def enterWaitForResults(self):
        self.notify.debug('enterWaitForResults')
        self.results = [0] * self.numPlayers
        self.resultsBarrier = ToonBarrier('results', self.uniqueName('results'), self.avIdList, PatternGameGlobals.InputTimeout, self.__gotAllPatterns, self.__resultsTimeout)

        # Don't make players wait for others
        # who are already out
        if not self.isSinglePlayer():
            for avId in self.avIdList:
                if not self.perfectResults[avId]:
                    self.resultsBarrier.clear(avId)

    def reportPlayerResult(self, success):
        avId = self.air.getAvatarIdFromSender()

        if not self._inState('waitForResults'):
            return
        if avId not in self.avIdList:
            self.air.writeServerEvent('suspicious', avId, 'PatternGameAI.reportButtonPress avId not on list')
            return
        if success not in [0, 1]:
            self.air.writeServerEvent('warning', success, "PatternGameAI.reportButtonPress got bad 'wrong'")
            return

        if not success and self.isSinglePlayer():
            self.__chances -= 1
            self.__madeAMistake = True

        self.reportPlayerPattern(avId, success)
        self.sendUpdate('setPlayerResult', [avId, success])

    def __resultsTimeout(self, avIds):
        self.notify.debug('__resultsTimeout: %s' % avIds)
        for avId in avIds:
            self.__acceptPlayerPattern(avId, 0)

        self.__gotAllPatterns()

    def reportPlayerPattern(self, avId, success):
        if not self._inState('waitForResults'):
            return

        self.__acceptPlayerPattern(avId, success)
        self.resultsBarrier.clear(avId)

    def __acceptPlayerPattern(self, avId, success):
        index = self.avIdList.index(avId)
        self.results[index] = success

    def __gotAllPatterns(self):
        for i in range(0, self.numPlayers):
            avId = self.avIdList[i]
            if not self.results[i]:
                self.perfectResults[avId] = 0
            else:
                self.scoreDict[avId] += self.round

        def continueGame():
            self.gameFSM.request('waitClientsReady')
            self.sendUpdate('setGameOver', [0])

        def endGame():
            self.sendUpdate('setGameOver', [1])
            self.gameOver()

        if self.isSinglePlayer():
            if self.round < PatternGameGlobals.SP_NUM_ROUNDS and self.__chances > 0:
                continueGame()
            elif self.perfectResults[self.avIdList[0]]:
                self.scoreDict[avId] += 4
                self.logPerfectGame(avId)
                endGame()
            else:
                endGame()
        else:
            if not list(self.perfectResults.values()).count(0) == len(self.avIdList):
                continueGame()
            else:
                endGame()

    def exitWaitForResults(self):
        self.resultsBarrier.cleanup()
        del self.resultsBarrier

    def enterCleanup(self):
        self.notify.debug('enterCleanup')

    def exitCleanup(self):
        pass
