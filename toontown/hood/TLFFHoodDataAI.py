from direct.directnotify import DirectNotifyGlobal

from toontown.safezone import DistributedTrolleyAI
from toontown.toonbase import ToontownGlobals
from . import HoodDataAI
from ..estate.DistributedHouseAI import DistributedHouseAI

from toontown.safezone import DistributedPicnicBasketAI

PICNIC_BASKET_POSITIONS = [
    (81, 7, 0.026, 0, 0, 0),
    (52, 46, 0.026, 40, 0, 0),
    (45, -8, 0.026, 60, 0, 0)
]


class TLFFHoodDataAI(HoodDataAI.HoodDataAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('TLFFHoodDataAI')

    def __init__(self, air, zoneId = None):
        hoodId = ToontownGlobals.ToonLandFunnyFarm
        if zoneId == None:
            zoneId = hoodId
        self.picnicTables = []
        super().__init__(air, zoneId, hoodId)

    def startup(self):
        super().startup()

        # TODO (maybe):
        # trolley = DistributedTrolleyAI.DistributedTrolleyAI(self.air)
        # trolley.generateWithRequired(self.zoneId)
        # trolley.start()
        # self.addDistObj(trolley)

        # ALSO TODO:
        # self.treasurePlanner = TLFFTreasurePlannerAI.TLFFTreasurePlannerAI(self.zoneId)
        # self.treasurePlanner.start()
        for pos in PICNIC_BASKET_POSITIONS:
            picnicTable = DistributedPicnicBasketAI.DistributedPicnicBasketAI(self.air, PICNIC_BASKET_POSITIONS.index(pos)+1, *pos)
            picnicTable.generateWithRequired(self.zoneId)
            picnicTable.start()
            self.addDistObj(picnicTable)

    def __createFakeHouse(self, index):
        house = DistributedHouseAI(self.air, (index + 1) << 20, 0, self.zoneId, index)
