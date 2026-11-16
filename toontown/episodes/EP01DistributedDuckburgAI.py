from direct.directnotify import DirectNotifyGlobal

from toontown.episodes.DistributedEpisodeZoneAI import DistributedEpisodeZoneAI


class EP01DistributedDuckburgAI(DistributedEpisodeZoneAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedDuckburgAI')

    def announceGenerate(self):
        DistributedEpisodeZoneAI.announceGenerate(self)
