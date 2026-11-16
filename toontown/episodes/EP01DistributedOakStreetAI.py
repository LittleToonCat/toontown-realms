from direct.directnotify import DirectNotifyGlobal

from toontown.episodes.DistributedEpisodeZoneAI import DistributedEpisodeZoneAI


class EP01DistributedOakStreetAI(DistributedEpisodeZoneAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedOakStreetAI')

    def announceGenerate(self):
        DistributedEpisodeZoneAI.announceGenerate(self)
