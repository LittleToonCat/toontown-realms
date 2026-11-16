from direct.directnotify import DirectNotifyGlobal

from toontown.episodes.DistributedEpisodeZoneAI import DistributedEpisodeZoneAI


class EP00DistributedTestingGroundsAI(DistributedEpisodeZoneAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('EP00DistributedTestingGroundsAI')

    def announceGenerate(self):
        DistributedEpisodeZoneAI.announceGenerate(self)
