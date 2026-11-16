from direct.directnotify import DirectNotifyGlobal

from toontown.episodes import DistributedEpisodeElevatorAI
from toontown.episodes.DistributedEpisodeZoneAI import DistributedEpisodeZoneAI


class EP02DistributedCogBarAI(DistributedEpisodeZoneAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedCogBarAI')

    def announceGenerate(self):
        # Elevator back to High Rise Hallway
        self.hallwayElevator = DistributedEpisodeElevatorAI.DistributedEpisodeElevatorAI(self.air, self.zoneId, self.zoneConnections[0], -8.350, 200.79, 0.0, 0.0, 0.0, 0.0)
        self.hallwayElevator.generateWithRequired(self.zoneId)

        DistributedEpisodeZoneAI.announceGenerate(self)
