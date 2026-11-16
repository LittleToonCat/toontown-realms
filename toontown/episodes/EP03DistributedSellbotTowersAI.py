from direct.directnotify import DirectNotifyGlobal

from toontown.episodes.DistributedEpisodeZoneAI import DistributedEpisodeZoneAI


class EP03DistributedSellbotTowersAI(DistributedEpisodeZoneAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedSellbotTowersAI')

    def announceGenerate(self):
        DistributedEpisodeZoneAI.announceGenerate(self)
