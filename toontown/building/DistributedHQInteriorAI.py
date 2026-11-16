import random
from direct.distributed import DistributedObjectAI
from direct.directnotify import DirectNotifyGlobal
from toontown.toon import NPCToons

periscopeNPCs = (15000, 15001, 15002, 15003, 15004, 15005, 15006, 15007, 15008, 15009, 15010, 15011, 15012, 15013, 15014)


class DistributedHQInteriorAI(DistributedObjectAI.DistributedObjectAI):

    def __init__(self, block, air, zoneId):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.block = block
        self.zoneId = zoneId
        self.tutorial = 0
        self.isDirty = False
        self.periscopeNPC = None
        self.accept('leaderboardChanged', self.leaderboardChanged)
        self.accept('leaderboardFlush', self.leaderboardFlush)

    def announceGenerate(self):
        DistributedObjectAI.DistributedObjectAI.announceGenerate(self)
        if config.GetBool('want-periscope-npcs', True) and not self.getTutorial():
            # There aren't enough unique NPCs to populate every HQ right now
            # so I'll just do random for now
            npcId = random.choice(periscopeNPCs)
            self.periscopeNPC = NPCToons.createNPC(self.air, npcId, NPCToons.NPCToonDict[npcId], self.zoneId)

    def delete(self):
        self.ignore('leaderboardChanged')
        self.ignore('leaderboardFlush')
        self.ignore('setLeaderBoard')
        self.ignore('AIStarted')
        if self.periscopeNPC and self.periscopeNPC.isGenerated():
            self.periscopeNPC.requestDelete()
        DistributedObjectAI.DistributedObjectAI.delete(self)

    def getZoneIdAndBlock(self):
        r = [self.zoneId, self.block]
        return r

    def leaderboardChanged(self):
        self.isDirty = True

    def leaderboardFlush(self):
        if self.isDirty:
            self.sendNewLeaderBoard()

    def sendNewLeaderBoard(self):
        if self.air:
            self.isDirty = False
            self.sendUpdate('setLeaderBoard', self.air.trophyMgr.getLeaderInfo())

    def getLeaderBoard(self):
        return self.air.trophyMgr.getLeaderInfo()

    def getTutorial(self):
        return self.tutorial

    def setTutorial(self, flag):
        if self.tutorial != flag:
            self.tutorial = flag
