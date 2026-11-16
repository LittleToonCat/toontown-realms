from direct.directnotify import DirectNotifyGlobal

from toontown.episodes.DistributedEpisodeZoneAI import DistributedEpisodeZoneAI


class EP04DistributedScene3AI(DistributedEpisodeZoneAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('ep04: Scene3AI')

    def announceGenerate(self):
        DistributedEpisodeZoneAI.announceGenerate(self)
