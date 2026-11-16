from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObjectAI import DistributedObjectAI


class FishPokerManagerAI(DistributedObjectAI):
    notify = directNotify.newCategory('FishPokerManagerAI')

    def start(self):
        self.air.newsManager.pokerStart()
        self.sendUpdate('enterFishing', [])

    def stop(self):
        self.air.newsManager.pokerEnd()
        self.sendUpdate('exitFishing', [])

    def cashIn(self, money):
        avId = self.air.getAvatarIdFromSender()
        if avId:
            av = self.air.doId2do.get(avId)
            if av:
                av.addMoney(money)
