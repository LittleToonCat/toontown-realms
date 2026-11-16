from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI


class DistributedEpisodeZoneAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedEpisodeZoneAI')

    def __init__(self, air, zoneId, zoneConnections, toonId):
        DistributedObjectAI.__init__(self, air)
        self.zoneId = zoneId
        self.zoneConnections = zoneConnections
        self.toonId = toonId
        self.__doors = []

    def setZoneConnections(self, zoneConnections):
        self.zoneConnections = zoneConnections

    def getZoneConnections(self):
        return self.zoneConnections

    def setToonId(self, toonId):
        self.toonId = toonId

    def getToonId(self):
        return self.toonId

    def appendDoor(self, door):
        self.__doors.append(door)

    def requestDelete(self):
        for door in self.__doors:
            door.requestDelete()
        self.__doors = []
        DistributedObjectAI.requestDelete(self)
