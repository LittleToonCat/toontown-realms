from . import DistributedBarrelBaseAI


class DistributedHealBarrelAI(DistributedBarrelBaseAI.DistributedBarrelBaseAI):

    def __init__(self, level, entId):
        DistributedBarrelBaseAI.DistributedBarrelBaseAI.__init__(self, level, entId)

    def d_setGrab(self, avId):
        self.notify.debug('d_setGrab %s' % avId)
        self.sendUpdate('setGrab', [avId])
        av = self.air.doId2do.get(avId)
        if av:
            av.toonUp(self.getRewardPerGrab())
