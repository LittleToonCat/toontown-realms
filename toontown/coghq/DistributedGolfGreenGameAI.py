from typing import List, Tuple
from otp.ai.AIBase import *
from direct.interval.IntervalGlobal import *
from direct.directnotify import DirectNotifyGlobal
from direct.distributed import ClockDelta
from direct.task import Task
from otp.level import DistributedEntityAI
from otp.level import BasicEntities
from toontown.coghq import BattleBlockerAI
from direct.distributed.ClockDelta import *
from toontown.toonbase import ToontownBattleGlobals
from .GolfGreenGameGlobals import *
import random
import time

class DistributedGolfGreenGameAI(BattleBlockerAI.BattleBlockerAI, NodePath, BasicEntities.NodePathAttribs):

    def __init__(self, level, entId):
        BattleBlockerAI.BattleBlockerAI.__init__(self, level, entId)
        random.seed(time.time() * entId)
        node = hidden.attachNewNode('DistributedLaserFieldAI')
        NodePath.__init__(self, node)
        if not hasattr(self, 'switchId'):
            self.switchId = 0
        self.gridScale = 1
        self.enabled = 1
        self.hasShownSuits = 0
        self.healReady = 1
        self.playedSound = 0
        self.canButton = 1
        self.title = 'MemTag: This is a golfGreenGame %s' % random.random()
        self.translateData = {}
        self.translateData['r'] = 0
        self.translateData['b'] = 1
        self.translateData['g'] = 2
        self.translateData['w'] = 3
        self.translateData['k'] = 4
        self.translateData['l'] = 5
        self.translateData['y'] = 6
        self.translateData['o'] = 7
        self.translateData['a'] = 8
        self.translateData['s'] = 9
        self.translateData['R'] = 10
        self.translateData['B'] = 11
        self.joinedToons = []
        self.everJoinedToons = []
        self.avId2BoardList = {}
        self.avId2ScoreData = {}
        self.avId2GagEarnCount = {}

    def selectBoard(self, avId: int) -> Tuple[List[Tuple[int, int, int]], List[int]]:
        if avId not in self.avId2BoardList or self.avId2BoardList[avId] == []:
            self.avId2BoardList[avId] = list(range(0, len(gameBoards)))
        boardSelect = random.choice(self.avId2BoardList[avId])
        self.avId2BoardList[avId].remove(boardSelect)

        board = gameBoards[boardSelect]
        gameBoardData = []
        attackPattern = []
        for rowIndex in range(1, len(board)):
            for columnIndex in range(len(board[rowIndex])):
                color = self.translateData.get(board[rowIndex][columnIndex])
                if color != None:
                    gameBoardData.append((len(board[rowIndex]) - (columnIndex + 1), rowIndex - 1, color))
        attackString = board[0]
        for ball in attackString:
            color = self.translateData.get(ball)
            if color or color == 0:
                place = random.choice(list(range(0, len(attackPattern) + 1)))
                attackPattern.insert(place, color)
                place = random.choice(list(range(0, len(attackPattern) + 1)))
                attackPattern.insert(place, color)

        return gameBoardData, attackPattern

    def leaveGame(self):
        senderId = self.air.getAvatarIdFromSender()
        if senderId in self.joinedToons:
            self.joinedToons.remove(senderId)
            self.sendUpdate('acceptJoin', [self.joinedToons])

    def requestJoin(self):
        senderId = self.air.getAvatarIdFromSender()
        if senderId not in self.joinedToons:
            self.joinedToons.append(senderId)
            if senderId not in self.everJoinedToons:
                self.everJoinedToons.append(senderId)
            self.sendUpdate('acceptJoin', [self.joinedToons])
            self.sendScoreData()

    def requestBoard(self, boardCompleted: bool):
        avId = self.air.getAvatarIdFromSender()
        if boardCompleted:
            self.sendUpdate('helpOthers', [avId])
            if avId not in self.avId2ScoreData:
                self.avId2ScoreData[avId] = 1
            else:
                self.avId2ScoreData[avId] = min(self.avId2ScoreData[avId] + 1, 255)
            self.sendScoreData()
            if avId in self.avId2GagEarnCount and self.avId2GagEarnCount[avId] >= 3:
                pass
            elif random.random() <= 0.25:
                if avId not in self.avId2GagEarnCount:
                    self.avId2GagEarnCount[avId] = 1
                else:
                    self.avId2GagEarnCount[avId] += 1
                self.addGag(avId)
        gameBoardData, attackPattern = self.selectBoard(avId)
        self.sendUpdateToAvatarId(avId, 'startBoard', [gameBoardData, attackPattern])

    def addGag(self, avId):
        av = simbase.air.doId2do.get(avId)
        if av:
            level = ToontownBattleGlobals.LAST_REGULAR_GAG_LEVEL
            track = int(random.random() * ToontownBattleGlobals.NUM_GAG_TRACKS)
            while not av.hasTrackAccess(track):
                track = int(random.random() * ToontownBattleGlobals.NUM_GAG_TRACKS)

            maxGags = av.getMaxCarry()
            av.inventory.calcTotalProps()
            numGags = av.inventory.totalProps
            numReward = min(1, maxGags - numGags)
            while numReward > 0 and level >= 0:
                result = av.inventory.addItem(track, level)
                if result <= 0:
                    level -= 1
                else:
                    numReward -= 1
                    self.sendUpdateToAvatarId(avId, 'informGag', [track, level])

            av.d_setInventory(av.inventory.makeNetString())

    def switchFire(self):
        if self.switchId != 0:
            switch = self.level.getEntity(self.switchId)
            if switch:
                switch.setIsOn(1)

    def generate(self):
        BattleBlockerAI.BattleBlockerAI.generate(self)
        if self.switchId != 0:
            self.accept(self.getOutputEventName(self.switchId), self.reactToSwitch)
        self.detectName = 'golfGreenGame %s' % self.doId
        taskMgr.doMethodLater(1.0, self.__detect, self.detectName)
        self.setPos(self.pos)
        self.setHpr(self.hpr)

    def registerBlocker(self):
        BattleBlockerAI.BattleBlockerAI.registerBlocker(self)
        if hasattr(self, 'hideSuits'):
            self.hideSuits()

    def delete(self):
        taskMgr.remove(self.detectName)
        self.ignoreAll()
        BattleBlockerAI.BattleBlockerAI.delete(self)

    def destroy(self):
        self.notify.info('destroy entity(laserField) %s' % self.entId)
        BattleBlockerAI.BattleBlockerAI.destroy(self)

    def __detect(self, task):
        isThereAnyToons = False
        if hasattr(self, 'level'):
            toonInRange = 0
            for avId in self.level.presentAvIds:
                if avId in self.air.doId2do:
                    av = self.air.doId2do[avId]
                    isThereAnyToons = True
                    distance = self.getDistance(av)

            if isThereAnyToons:
                taskMgr.doMethodLater(1.0, self.__detect, self.detectName)
                self.__run()
        return Task.done

    def __run(self):
        pass

    def reactToSwitch(self, on):
        pass

    def setBattleFinished(self):
        BattleBlockerAI.BattleBlockerAI.setBattleFinished(self)
        messenger.send(self.getOutputEventName(), [1])
        self.switchFire()

    def sendScoreData(self):
        self.sendUpdate('scoreData', [list(self.avId2ScoreData.items())])
