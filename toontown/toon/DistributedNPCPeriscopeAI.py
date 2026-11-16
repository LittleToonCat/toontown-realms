from direct.directnotify.DirectNotifyGlobal import directNotify
from .DistributedNPCToonBaseAI import DistributedNPCToonBaseAI


class DistributedNPCPeriscopeAI(DistributedNPCToonBaseAI):
    notify = directNotify.newCategory('DistributedNPCPeriscopeAI')

    def __init__(self, air, npcId, hq=0):
        DistributedNPCToonBaseAI.__init__(self, air, npcId, None)
        self.hq = hq
        self.accept('invasionStatusMessage', self.d_speakAboutInvasionStatus)
        self.accept('maintenanceMessage', self.d_maintenanceMessage)
        self.accept('notifyFireworks', self.d_speakAboutFireworks)
        self.startAnimState = 'Periscope'

    def delete(self):
        self.ignore('invasionStatusMessage')
        self.ignore('maintenanceMessage')
        self.ignore('notifyFireworks')
        DistributedNPCToonBaseAI.delete(self)

    def getHq(self):
        return self.hq

    def d_speakAboutInvasionStatus(self, cogList, special, virtual, msgType, mega=0):
        self.sendUpdate('speakAboutInvasionStatus', [cogList, special, virtual, msgType, mega])

    def d_maintenanceMessage(self):
        self.sendUpdate('speakAboutMaintenance')

    def d_speakAboutFireworks(self, msg):
        self.sendUpdate('speakAboutFireworks', [msg])
