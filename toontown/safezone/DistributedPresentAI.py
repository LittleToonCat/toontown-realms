from .DistributedTreasureAI import DistributedTreasureAI
from direct.directnotify import DirectNotifyGlobal

import datetime


class DistributedPresentAI(DistributedTreasureAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPresentAI')

    def __init__(self, air, treasurePlanner, x, y, z):
        DistributedTreasureAI.__init__(self, air, treasurePlanner, x, y, z)
        self.moneyMult = 1

    def d_setGrab(self, avId):
        av = self.air.doId2do.get(avId)
        if not av:
            self.air.writeServerEvent('suspicious', avId, 'nonexistent av tried to take a present')
            return

        DistributedTreasureAI.d_setGrab(self, avId)

        dt = datetime.datetime.today()
        month = dt.month
        day = dt.day
        if month != 12:
            amount = 10
        else:
            if day >= 25:
                amount = 125
            else:
                amount = min(5 * (day + 1), 100)
        amount *= self.moneyMult
        av.addMoney(amount)
        av.d_generateScavengerEffect(amount)
