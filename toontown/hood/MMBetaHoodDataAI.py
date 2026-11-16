from direct.directnotify import DirectNotifyGlobal
from direct.task import Task

from toontown.classicchars import DistributedBetaMinnieAI
from toontown.safezone import DistributedTrolleyAI
from toontown.safezone import DistributedMMPianoAI
from toontown.safezone import MMTreasurePlannerAI
from toontown.toonbase import ToontownGlobals

from . import HoodDataAI


class MMBetaHoodDataAI(HoodDataAI.HoodDataAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('MMBetaHoodDataAI')

    def __init__(self, air, zoneId=None):
        hoodId = ToontownGlobals.MinniesMelodylandBeta
        if zoneId == None:
            zoneId = hoodId
        HoodDataAI.HoodDataAI.__init__(self, air, zoneId, hoodId)
        return

    def startup(self):
        HoodDataAI.HoodDataAI.startup(self)
        trolley = DistributedTrolleyAI.DistributedTrolleyAI(self.air)
        trolley.setBeta(True)
        trolley.generateWithRequired(self.zoneId)
        trolley.start()
        self.addDistObj(trolley)

        self.treasurePlanner = MMTreasurePlannerAI.MMTreasurePlannerAI(self.zoneId)
        self.treasurePlanner.start()

        self.classicChar = DistributedBetaMinnieAI.DistributedBetaMinnieAI(self.air)
        self.classicChar.generateWithRequired(self.zoneId)
        self.classicChar.start()
        self.addDistObj(self.classicChar)

        piano = DistributedMMPianoAI.DistributedMMPianoAI(self.air)
        piano.generateWithRequired(self.zoneId)
        self.addDistObj(piano)

    def _deleteTrolley(self, task):
        self.trolley.requestDelete()
        taskMgr.doMethodLater(0.5, self._createTrolley, 'createTrolley')
        return Task.done

    def _createTrolley(self, task):
        trolley = DistributedTrolleyAI.DistributedTrolleyAI(self.air)
        trolley.setBeta(True)
        trolley.generateWithRequired(self.zoneId)
        trolley.start()
        self.trolley = trolley
        taskMgr.doMethodLater(0.5, self._deleteTrolley, 'deleteTrolley')
        return Task.done
