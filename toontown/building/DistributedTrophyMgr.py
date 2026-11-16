from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import TTLocalizer

from toontown.quest.QuestPoster import QuestPoster

class DistributedTrophyMgr(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedTrophyMgr')
    neverDisable = 1

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)

    def generate(self):
        if base.cr.trophyManager != None:
            base.cr.trophyManager.delete()
        base.cr.trophyManager = self
        DistributedObject.DistributedObject.generate(self)

    def disable(self):
        base.cr.trophyManager = None
        DistributedObject.DistributedObject.disable(self)

    def delete(self):
        base.cr.trophyManager = None
        DistributedObject.DistributedObject.delete(self)

    def d_requestTrophyScore(self):
        self.sendUpdate('requestTrophyScore', [])

    def receiveRemoveTrophyNotification(self, dept: str, numFloors: int, streetZoneId: int, interiorZoneId: int, isCogdo: bool):
        if isCogdo:
            if dept == 'l':
                icon = loader.loadModel('phase_5/models/cogdominium/tt_m_ara_cbe_fieldOfficeLegalEagle')
            else:
                icon = loader.loadModel('phase_5/models/cogdominium/tt_m_ara_cbe_fieldOfficeMoverShaker')
        else:
            if dept == 'c':
                icon = loader.loadModel('phase_4/models/modules/suit_landmark_corp')
            elif dept == 'l':
                icon = loader.loadModel('phase_4/models/modules/suit_landmark_legal')
            elif dept == 'm':
                icon = loader.loadModel('phase_4/models/modules/suit_landmark_money')
            else:
                icon = loader.loadModel('phase_4/models/modules/suit_landmark_sales')
        # Attach an elevator to the building model
        QuestPoster.loadElevator(self, icon, numFloors, isCogdo)
        icon.setH(180)

        buildingTitle = TTLocalizer.zone2TitleDict.get(interiorZoneId, [TTLocalizer.ToonBuilding])[0].replace('\x03', '')
        if not buildingTitle:
            buildingTitle = TTLocalizer.ToonBuilding
        base.localAvatar.sendNotification(
                title = TTLocalizer.NotificationTitleBuildingRetaken.format(numFloors),
                body = TTLocalizer.NotificationBodyBuildingRetaken.format(buildingTitle, TTLocalizer.GlobalStreetNames[streetZoneId][2]),
                icon = icon,
                id = "building_retaken"
        )