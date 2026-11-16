from direct.directnotify import DirectNotifyGlobal

from toontown.episodes.DistributedEpisodeZoneAI import DistributedEpisodeZoneAI


class EP03DistributedOakStreetAI(DistributedEpisodeZoneAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('EP03DistributedOakStreetAI')

    def announceGenerate(self):
        DistributedEpisodeZoneAI.announceGenerate(self)
