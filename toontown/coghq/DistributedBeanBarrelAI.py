from . import DistributedBarrelBaseAI


class DistributedBeanBarrelAI(DistributedBarrelBaseAI.DistributedBarrelBaseAI):

    def __init__(self, level, entityId):
        DistributedBarrelBaseAI.DistributedBarrelBaseAI.__init__(self, level, entityId)

    def d_setGrab(self, avId):
        self.notify.debug('d_setGrab %s' % avId)
        self.sendUpdate('setGrab', [avId])
        av = self.air.doId2do.get(avId)
        if av:
            av.addMoney(self.rewardPerGrab)
