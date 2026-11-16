from direct.directnotify import DirectNotifyGlobal

from toontown.episodes.DistributedEpisodeZoneAI import DistributedEpisodeZoneAI


class EP03DistributedDaisyGardensAI(DistributedEpisodeZoneAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedDaisyGardensAI')

    def announceGenerate(self):
        DistributedEpisodeZoneAI.announceGenerate(self)
