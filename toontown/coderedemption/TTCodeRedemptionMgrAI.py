from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from toontown.toonbase import ToontownGlobals

from toontown.catalog.CatalogBeanItem import CatalogBeanItem
from toontown.catalog.CatalogClothingItem import CatalogClothingItem
from toontown.catalog.CatalogRentalItem import CatalogRentalItem
from toontown.catalog.CatalogInvalidItem import CatalogInvalidItem
from toontown.catalog.CatalogFurnitureItem import CatalogFurnitureItem

import time


class TTCodeRedemptionMgrAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory("TTCodeRedemptionMgrAI")

    Success = 0
    InvalidCode = 1
    ExpiredCode = 2
    Ineligible = 3
    AwardError = 4
    TooManyFails = 5
    ServiceUnavailable = 6

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)
        self.air = air

    def announceGenerate(self):
        DistributedObjectAI.announceGenerate(self)

    def delete(self):
        DistributedObjectAI.delete(self)

    def giveAwardToToonResult(self, todo0, todo1):
        pass

    def redeemCode(self, context, code):
        avId = self.air.getAvatarIdFromSender()
        if not avId:
            self.air.writeServerEvent('suspicious', avId=avId, issue='Tried to redeem a code from an invalid avId')
            return

        av = self.air.doId2do.get(avId)
        if not av:
            self.air.writeServerEvent('suspicious', avId=avId, issue='Invalid avatar tried to redeem a code')
            return

        valid = True
        eligible = True
        expired = False
        delivered = False

        codes = av.getRedeemedCodes()
        if not codes:
            codes = [code]
            av.setRedeemedCodes(codes)
        else:
            if not code in codes:
                codes.append(code)
                av.setRedeemedCodes(codes)
                valid = True
            else:
                valid = False

        if not valid:
            self.air.writeServerEvent('code-redeemed', avId=avId, issue='Invalid code: %s' % code)
            self.sendUpdateToAvatarId(avId, 'redeemCodeResult', [context, self.InvalidCode, 0])
            return

        if expired:
            self.air.writeServerEvent('code-redeemed', avId=avId, issue='Expired code: %s' % code)
            self.sendUpdateToAvatarId(avId, 'redeemCodeResult', [context, self.ExpiredCode, 0])
            return

        if not eligible:
            self.air.writeServerEvent('code-redeemed', avId=avId, issue='Ineligible for code: %s' % code)
            self.sendUpdateToAvatarId(avId, 'redeemCodeResult', [context, self.Ineligible, 0])
            return

        items = self.getItemsForCode(code)
        for item in items:
            if isinstance(item, CatalogInvalidItem):
                self.air.writeServerEvent('suspicious', avId=avId, issue='Invalid CatalogItem\'s for code: %s' % code)
                self.sendUpdateToAvatarId(avId, 'redeemCodeResult', [context, self.InvalidCode, 0])
                break

            if len(av.mailboxContents) + len(av.onGiftOrder) >= ToontownGlobals.MaxMailboxContents:
                delivered = False
                break

            item.deliveryDate = int(time.time() / 60) + 1
            av.onOrder.append(item)
            av.b_setDeliverySchedule(av.onOrder)
            delivered = True

        if not delivered:
            self.air.writeServerEvent('code-redeemed', avId=avId, issue='Could not deliver items for code: %s' % code)
            self.sendUpdateToAvatarId(avId, 'redeemCodeResult', [context, self.InvalidCode, 0])
            return

        self.air.writeServerEvent('code-redeemed', avId=avId, issue='Successfuly redeemed code: %s' % code)
        self.sendUpdateToAvatarId(avId, 'redeemCodeResult', [context, self.Success, 0])

    def getItemsForCode(self, code):
        avId = self.air.getAvatarIdFromSender()
        if not avId:
            self.air.writeServerEvent('suspicious', avId=avId, issue='Could not parse the gender of an invalid avId')
            return

        av = self.air.doId2do.get(avId)
        if not av:
            self.air.writeServerEvent('suspicious', avId=avId, issue='Could not parse the gender of an invalid avatar')
            return

        '''
        # Here is an example of giving clothing to specific genders.
        if code == "GenderExample":
            # The following code will check to see if the gender is a male.
            # If it is, then they will be given shirt 2002.
            if av.getStyle().getGender() == 'm':
                shirt = CatalogClothingItem(2002, 0)
            # If it sees the gender isn't male, it will give shirt 2003.
            else:
                shirt = CatalogClothingItem(2003, 0)
            return [shirt]
        '''

        code = code.lower()
        code = code.replace(" ", "")

        if code == "gadzooks":
            shirt = CatalogClothingItem(1807, 0)
            return [shirt]

        if code == "silly meter":
            shirt = CatalogClothingItem(1753, 0)
            return [shirt]

        if code == "gc sbfo":
            shirt = CatalogClothingItem(1788, 0)
            return [shirt]

        if code == "get connected":
            shirt = CatalogClothingItem(1752, 0)
            return [shirt]

        if code == "summer":
            shirt = CatalogClothingItem(1709, 0)
            return [shirt]

        if code == "brrrgh":
            shirt = CatalogClothingItem(1800, 0)
            return [shirt]

        if code == "toontastic":
            shirt = CatalogClothingItem(1820, 0)
            return [shirt]

        if code == "sunburst":
            shirt = CatalogClothingItem(1809, 0)
            return [shirt]

        if code == "sweet":
            beans = CatalogBeanItem(12000, tagCode=2)
            return [beans]

        if code == "winter":
            rent = CatalogRentalItem(ToontownGlobals.RentalCannon, 48 * 60, 0)
            return [rent]

        if code == "spooky":
            shirt = CatalogClothingItem(1799, 0)
            return [shirt]

        if code == "greener":
            items = []
            for id in (20000, 20010, 20020, 20030, 20040, 20050):
                item = CatalogFurnitureItem(id)
                items.append(item)
            return items

        if code == "toontrees":
            shirt = CatalogClothingItem(1821, 0)
            if av.getStyle().getGender() == 'm':
                shorts = CatalogClothingItem(1822, 0)
            else:
                shorts = CatalogClothingItem(1823, 0)
            return [shirt, shorts]

        return []

    def requestCodeRedeem(self, todo0, todo1):
        pass

    def redeemCodeResult(self, todo0, todo1, todo2):
        pass
