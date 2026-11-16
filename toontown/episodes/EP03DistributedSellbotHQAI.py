from direct.directnotify import DirectNotifyGlobal

from toontown.episodes.DistributedEpisodeZoneAI import DistributedEpisodeZoneAI


class EP03DistributedSellbotHQAI(DistributedEpisodeZoneAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('EP03DistributedSellbotHQAI')

    def announceGenerate(self):
        DistributedEpisodeZoneAI.announceGenerate(self)
