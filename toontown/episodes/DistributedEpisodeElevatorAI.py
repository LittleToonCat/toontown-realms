from otp.ai.AIBase import *

from toontown.building.ElevatorUtils import *
from toontown.building import DistributedElevatorAI, DistributedElevatorExtAI


class DummyBldg:
    def getDoId(self):
        return 0


class DistributedEpisodeElevatorAI(DistributedElevatorExtAI.DistributedElevatorExtAI):

    def __init__(self, air, zone, toZone, x, y, z, h, p, r):
        DistributedElevatorExtAI.DistributedElevatorExtAI.__init__(self, air, DummyBldg(), numSeats=4, antiShuffle=0, minLaff=0)
        self.zone = zone
        self.toZone = toZone
        self.posHpr = (x, y, z, h, p, r)
        self.countdownTime = 2.0
        self.type = ELEVATOR_EPISODE

    def setPosHpr(self, x, y, z, h, p, r):
        self.posHpr = (x, y, z, h, p, r)

    def getPosHpr(self):
        return self.posHpr

    def elevatorClosed(self):
        numPlayers = self.countFullSeats()
        if numPlayers > 0:
            for seatIndex in range(len(self.seats)):
                avId = self.seats[seatIndex]
                if avId:
                    self.sendUpdateToAvatarId(avId, 'setEpisodeZone', [self.toZone])
                    self.clearFullNow(seatIndex)

        else:
            self.notify.warning('The elevator left, but was empty.')
        self.fsm.request('closed')

    def enterClosing(self):
        DistributedElevatorAI.DistributedElevatorAI.enterClosing(self)
        taskMgr.doMethodLater(self.countdownTime, self.elevatorClosedTask, self.uniqueName('closing-timer'))

    def enterClosed(self):
        DistributedElevatorExtAI.DistributedElevatorExtAI.enterClosed(self)
        self.fsm.request('opening')

    def enterOpening(self):
        DistributedElevatorAI.DistributedElevatorAI.enterOpening(self)
        taskMgr.doMethodLater(self.countdownTime, self.waitEmptyTask, self.uniqueName('opening-timer'))

    def requestBoard(self, *args):
        self.notify.debug('requestBoard')
        avId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(avId)
        if av:
             self.acceptingBoardersHandler(avId)
        else:
            self.notify.warning('avid: %s does not exist, but tried to board an elevator' % avId)
