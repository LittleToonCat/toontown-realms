from direct.directnotify import DirectNotifyGlobal

from toontown.episodes.DistributedEpisodeZoneAI import DistributedEpisodeZoneAI


class EP01DistributedGyrosLabAI(DistributedEpisodeZoneAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedGyrosLabAI')

    def announceGenerate(self):
        DistributedEpisodeZoneAI.announceGenerate(self)
