from direct.directnotify.DirectNotifyGlobal import directNotify
from .DistributedNPCToonAI import DistributedNPCToonAI


class DistributedNPCMuseumToonAI(DistributedNPCToonAI):
    notify = directNotify.newCategory('DistributedNPCMuseumToonAI')

    def __init__(self, air, npcId):
        DistributedNPCToonAI.__init__(self, air, npcId)

    def avatarEnter(self):
        avId = self.air.getAvatarIdFromSender()
        if not self.busy:
            self.busy = avId
            self.notify.debug('avatar enter ' + str(avId))
            self.sendUpdate('handleInteract', [avId])
            taskMgr.doMethodLater(60.0, self.sendTimeoutMovie, self.uniqueName('clearMovie'))
