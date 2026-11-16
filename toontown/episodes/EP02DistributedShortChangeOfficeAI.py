from direct.directnotify import DirectNotifyGlobal

from toontown.episodes import DistributedEpisodeElevatorAI
from toontown.episodes.DistributedEpisodeZoneAI import DistributedEpisodeZoneAI


class EP02DistributedShortChangeOfficeAI(DistributedEpisodeZoneAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedShortChangeOfficeAI')

    def announceGenerate(self):
        self.elevator = DistributedEpisodeElevatorAI.DistributedEpisodeElevatorAI(self.air, self.zoneId, self.zoneConnections[0], 0, -25, 0, 180, 0, 0)
        self.elevator.generateWithRequired(self.zoneId)
        DistributedEpisodeZoneAI.announceGenerate(self)
