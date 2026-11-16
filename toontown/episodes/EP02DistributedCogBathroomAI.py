from direct.directnotify import DirectNotifyGlobal

from toontown.episodes.DistributedEpisodeZoneAI import DistributedEpisodeZoneAI
from toontown.toon import NPCToons


class EP02DistributedCogBathroomAI(DistributedEpisodeZoneAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedCogBathroomAI')

    def __init__(self, air, zoneId, zoneConnections, toonId):
        DistributedEpisodeZoneAI.__init__(self, air, zoneId, zoneConnections, toonId)

        # Professor Guffaw
        npcDesc = NPCToons.NPCToonDict.get(2126)
        self.npc = NPCToons.createNPC(self.air, 2126, npcDesc, self.zoneId, 0)

    def requestDelete(self):
        DistributedEpisodeZoneAI.requestDelete(self)
        if self.npc:
            self.npc.requestDelete()

    def cleanupNpc(self):
        if self.npc:
            self.npc.requestDelete()
            self.npc = None

    def getNpcId(self):
        return self.npc.getDoId()
