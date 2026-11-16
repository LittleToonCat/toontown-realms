from direct.directnotify import DirectNotifyGlobal
from . import HoodDataAI
from toontown.toonbase import ToontownGlobals
from toontown.safezone import DistributedTrolleyAI
from toontown.safezone import DLTreasurePlannerAI, DDLOTreasurePlannerAI
from toontown.classicchars import DistributedDonaldAI
from toontown.safezone import ButterflyGlobals

class DLHoodDataAI(HoodDataAI.HoodDataAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DLHoodDataAI')

    def __init__(self, air, zoneId=None):
        hoodId = ToontownGlobals.DonaldsDreamland
        if zoneId == None:
            zoneId = hoodId
        HoodDataAI.HoodDataAI.__init__(self, air, zoneId, hoodId)

    def startup(self):
        HoodDataAI.HoodDataAI.startup(self)
        trolley = DistributedTrolleyAI.DistributedTrolleyAI(self.air)
        trolley.generateWithRequired(self.zoneId)
        trolley.start()
        self.addDistObj(trolley)

        self.treasurePlanner = DLTreasurePlannerAI.DLTreasurePlannerAI(self.zoneId)
        self.treasurePlanner.start()

        self.outcoveTreasurePlanner = DDLOTreasurePlannerAI.DDLOTreasurePlannerAI(ToontownGlobals.DreamyDriveOutcove)
        self.outcoveTreasurePlanner.start()

        if self.air.disneyCharacters:
            self.classicChar = DistributedDonaldAI.DistributedDonaldAI(self.air)
            #self.classicChar = DistributedDonaldDreamDayAI.DistributedDonaldDreamDayAI(self.air)
            self.classicChar.generateWithRequired(self.zoneId)
            self.classicChar.start()
            self.addDistObj(self.classicChar)

    def shutdown(self):
        self.outcoveTreasurePlanner.stop()
        self.outcoveTreasurePlanner.deleteAllTreasuresNow()
        del self.outcoveTreasurePlanner

        HoodDataAI.HoodDataAI.shutdown(self)