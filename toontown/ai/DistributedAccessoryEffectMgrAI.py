from direct.distributed.DistributedObjectAI import DistributedObjectAI

from toontown.catalog.CatalogAccessoryItem import CatalogAccessoryItem
from toontown.toonbase import ToontownGlobals


class DistributedAccessoryEffectMgrAI(DistributedObjectAI):

    def __init__(self, air, phraseId: int, accessoryId: int):
        DistributedObjectAI.__init__(self, air)
        self.phraseId = phraseId
        self.accessoryId = accessoryId

    def getPhraseId(self) -> int:
        return self.phraseId

    def addAccessoryEffect(self):
        avId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(avId)
        if not av:
            return
        item = CatalogAccessoryItem(self.accessoryId)
        # check if the item has already been purchased for this avatar or if they already have it.
        if item.reachedPurchaseLimit(av):
            return
        if item.recordPurchase(av, None) == ToontownGlobals.P_ItemAvailable:
            self.sendUpdateToAvatarId(avId, 'addAccessoryEffectSuccess', [])
