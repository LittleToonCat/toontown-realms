from direct.directnotify import DirectNotifyGlobal

from toontown.episodes import DistributedEpisodeElevatorAI
from toontown.episodes.DistributedEpisodeZoneAI import DistributedEpisodeZoneAI


class EP02DistributedHighRiseHallwayAI(DistributedEpisodeZoneAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedHighRiseHallwayAI')

    def announceGenerate(self):
        # Elevator back to Short Change Office
        self.officeElevator = DistributedEpisodeElevatorAI.DistributedEpisodeElevatorAI(self.air, self.zoneId, self.zoneConnections[0], 0, 49.25, 0, 0, 0, 0)
        self.officeElevator.generateWithRequired(self.zoneId)

        # Elevator to Cog Bar
        self.barElevator = DistributedEpisodeElevatorAI.DistributedEpisodeElevatorAI(self.air, self.zoneId, self.zoneConnections[2], 0, -49.25, 0, 180, 0, 0)
        self.barElevator.generateWithRequired(self.zoneId)

        DistributedEpisodeZoneAI.announceGenerate(self)
