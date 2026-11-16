from toontown.building.DistributedDoorAI import DistributedDoorAI
from direct.directnotify.DirectNotifyGlobal import directNotify


class DistributedEpisodeDoorAI(DistributedDoorAI):
    # NOTE: add any additional required data if needed
    notify = directNotify.newCategory('DistributedEpisodeDoorAI')

    def __init__(self, air, blockNumber, doorType, zoneId, doorIndex=0, lockValue=0, swing=3):
        DistributedDoorAI.__init__(self, air=air, blockNumber=blockNumber, doorType=doorType, doorIndex=doorIndex,
                                   lockValue=lockValue, swing=swing)
        # not entirely sure why other code manually sets zoneId, so I guess we'll do it here instead
        self.zoneId = zoneId
