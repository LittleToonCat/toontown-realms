from direct.directnotify import DirectNotifyGlobal

from toontown.episodes.DistributedEpisodeZoneAI import DistributedEpisodeZoneAI


class EP04DistributedScene2AI(DistributedEpisodeZoneAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('ep04: Scene2AI')

    def announceGenerate(self):
        DistributedEpisodeZoneAI.announceGenerate(self)
