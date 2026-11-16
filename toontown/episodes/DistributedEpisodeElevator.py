from toontown.building.ElevatorConstants import *
from toontown.building.ElevatorUtils import *
from toontown.building import DistributedElevator
from toontown.building import DistributedElevatorExt


class DistributedEpisodeElevator(DistributedElevatorExt.DistributedElevatorExt):

    def __init__(self, cr):
        DistributedElevatorExt.DistributedElevatorExt.__init__(self, cr)
        self.type = ELEVATOR_EPISODE
        self.countdownTime = 2.0
        self.posHpr = None

    def delete(self):
        self.elevatorModel.removeNode()
        del self.elevatorModel
        DistributedElevatorExt.DistributedElevatorExt.delete(self)

    def setPosHpr(self, x, y, z, h, p, r):
        self.posHpr = (x, y, z, h, p, r)
        self.setupElevator()

    def setupElevator(self):
        self.elevatorModel = loader.loadModel('phase_5/models/cogdominium/tt_m_ara_csa_elevatorB')
        self.leftDoor = self.elevatorModel.find('**/left_door')
        self.rightDoor = self.elevatorModel.find('**/right_door')
        self.elevatorModel.reparentTo(render)
        self.elevatorModel.setPosHpr(*self.posHpr)
        DistributedElevator.DistributedElevator.setupElevator(self)
        # The trigger can be a pain to collide with in it's normal position,
        # so we move it out a bit to make it consistent
        self.elevatorSphereNodePath.setY(-1)

    def setBldgDoId(self, bldgDoId):
        self.bldg = None

    def getElevatorModel(self):
        return self.elevatorModel

    def getZoneId(self):
        return 0

    def __doorsClosed(self, zoneId):
        pass

    def setEpisodeZone(self, zoneId):
        if self.localToonOnBoard:
            self.cr.episodeManager.setEpisodeZone(zoneId)
            hoodId = self.cr.playGame.hood.hoodId
            doneStatus = {'loader': 'episodeLoader',
             'where': 'episodeZone',
             'how': 'teleportIn',
             'zoneId': zoneId,
             'hoodId': hoodId}
            self.cr.playGame.getPlace().elevator.signalDone(doneStatus)
