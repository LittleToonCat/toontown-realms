from direct.directnotify import DirectNotifyGlobal

from toontown.episodes.DistributedEpisodeZoneAI import DistributedEpisodeZoneAI


class EP04DistributedScene1AI(DistributedEpisodeZoneAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('ep04: Scene1AI')

    def announceGenerate(self):
        DistributedEpisodeZoneAI.announceGenerate(self)
