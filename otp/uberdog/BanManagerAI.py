from direct.distributed.DistributedObjectGlobalAI import DistributedObjectGlobalAI
from direct.directnotify import DirectNotifyGlobal


class BanManagerAI(DistributedObjectGlobalAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('BanManagerAI')

    def __init__(self, air):
        DistributedObjectGlobalAI.__init__(self, air)

    def sendBan(self, accId=0, avId=0, name='N/A', modAvId=0, modName='N/A', minutes=0, reason='Unknown'):
        self.sendUpdate('handleBan', [accId, avId, name, modAvId, modName, minutes, reason])

    def sendMute(self, accId=0, avId=0, name='N/A', modAvId=0, modName='N/A', minutes=0, reason='Unknown'):
        self.sendUpdate('handleMute', [accId, avId, name, modAvId, modName, minutes, reason])

    def sendUnmute(self, accId=0):
        self.sendUpdate('handleUnmute', [accId])

    def sendKick(self, avId=0, reason='N/A', silent=0):
        self.sendUpdate('handleKick', [avId, reason, silent])
