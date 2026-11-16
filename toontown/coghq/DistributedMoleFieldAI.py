from otp.level import DistributedEntityAI
from toontown.coghq import MoleFieldBase
from direct.distributed.ClockDelta import globalClockDelta
from direct.directnotify import DirectNotifyGlobal

class DistributedMoleFieldAI(DistributedEntityAI.DistributedEntityAI, MoleFieldBase.MoleFieldBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedMoleFieldAI')

    def __init__(self, level, entId):
        DistributedEntityAI.DistributedEntityAI.__init__(self, level, entId)
        self.whackedMoles = {}
        self.started = 0

    def announceGenerate(self):
        DistributedEntityAI.DistributedEntityAI.announceGenerate(self)
        self.numMoles = self.numSquaresX * self.numSquaresY
        self.moleFieldEndTimeTaskName = self.uniqueName('moleFieldEndTime')

    def delete(self):
        DistributedEntityAI.DistributedEntityAI.delete(self)
        self.removeAllTasks()

    def setClientTriggered(self):
        if not hasattr(self, 'gameStartTime'):
            self.gameStartTime = globalClock.getRealTime()
        if not self.started:
            self.b_setGameStart(globalClockDelta.localToNetworkTime(self.gameStartTime))
            self.started = 1

    def b_setGameStart(self, timestamp):
        self.d_setGameStart(timestamp)
        self.setGameStart(timestamp)

    def d_setGameStart(self, timestamp):
        self.notify.debug('BASE: Sending setGameStart')
        self.sendUpdate('setGameStart', [timestamp])

    def setGameStart(self, timestamp):
        self.notify.debug('BASE: setGameStart')
        self.prepareForGameStart()

    def prepareForGameStart(self):
        self.scheduleMoles()
        self.whackedMoles = {}

    def whackedMole(self, moleIndex, popupNum):
        validMoleWhack = False
        if moleIndex in self.whackedMoles:
            if self.whackedMoles[moleIndex] < popupNum:
                validMoleWhack = True
        else:
            self.whackedMoles[moleIndex] = popupNum
            validMoleWhack = True
        if validMoleWhack:
            self.sendUpdate('updateMole', [moleIndex, self.WHACKED])

    def whackedBomb(self, moleIndex, popupNum, timestamp):
        senderId = self.air.getAvatarIdFromSender()
        self.sendUpdate('reportToonHitByBomb', [senderId, moleIndex, timestamp])
