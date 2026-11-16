from otp.level import DistributedEntityAI
from direct.directnotify import DirectNotifyGlobal

class DistributedMazeAI(DistributedEntityAI.DistributedEntityAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedMazeAI')

    def __init__(self, level, entId):
        DistributedEntityAI.DistributedEntityAI.__init__(self, level, entId)
        self.roomDoId = level.doId
        self.finishedList = []

    def delete(self):
        self.removeAllTasks()
        DistributedEntityAI.DistributedEntityAI.delete(self)

    def getRoomDoId(self):
        return self.roomDoId
