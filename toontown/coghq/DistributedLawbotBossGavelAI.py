from panda3d.core import CollisionNode, CollisionSphere, NodePath
from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from toontown.toonbase import ToontownGlobals


class DistributedLawbotBossGavelAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedLawbotBossGavelAI')

    def __init__(self, air, boss, index):
        DistributedObjectAI.__init__(self, air)
        self.boss = boss
        self.index = index
        cn = CollisionNode('controls')
        cs = CollisionSphere(0, -6, 0, 6)
        cn.addSolid(cs)
        self.goonShield = NodePath(cn)
        self.goonShield.setPosHpr(*ToontownGlobals.LawbotBossGavelPosHprs[self.index])
        self.avId = 0
        self.objectId = 0

    def delete(self):
        self.goonShield.removeNode()
        DistributedObjectAI.delete(self)

    def getBossCogId(self):
        return self.boss.doId

    def getIndex(self):
        return self.index

    def turnOn(self):
        self.sendUpdate('activate')
