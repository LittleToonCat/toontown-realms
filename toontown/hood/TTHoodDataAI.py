import random

from direct.directnotify import DirectNotifyGlobal

from toontown.toonbase import ToontownGlobals, ServerSettings
from toontown.safezone import DistributedTrolleyAI, DistributedTTStatueActivityAI
from toontown.safezone import TTTreasurePlannerAI
from toontown.classicchars import DistributedMickeyAI
from toontown.safezone import ButterflyGlobals
from toontown.safezone import DistributedSafezoneJukeboxAI

from . import HoodDataAI


class TTHoodDataAI(HoodDataAI.HoodDataAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('TTHoodDataAI')

    def __init__(self, air, zoneId=None):
        hoodId = ToontownGlobals.ToontownCentral
        if zoneId == None:
            zoneId = hoodId
        HoodDataAI.HoodDataAI.__init__(self, air, zoneId, hoodId)
        return

    def startup(self):
        HoodDataAI.HoodDataAI.startup(self)

        # Trolley
        trolley = DistributedTrolleyAI.DistributedTrolleyAI(self.air)
        trolley.generateWithRequired(self.zoneId)
        trolley.start()
        self.addDistObj(trolley)
        self.trolley = trolley
        if simbase.blinkTrolley:
            taskMgr.doMethodLater(0.5, self._deleteTrolley, 'deleteTrolley')

        # Treasure Planner
        self.treasurePlanner = TTTreasurePlannerAI.TTTreasurePlannerAI(self.zoneId)
        self.treasurePlanner.start()

        if self.air.disneyCharacters:
            # Classic Character
            self.classicChar = DistributedMickeyAI.DistributedMickeyAI(self.air)
            self.classicChar.generateWithRequired(self.zoneId)
            self.classicChar.start()
            self.addDistObj(self.classicChar)

        # Butterflies
        self.createButterflies(ButterflyGlobals.TTC)

        if self.air.jukebox:
            self.safezoneJukebox = DistributedSafezoneJukeboxAI.DistributedSafezoneJukeboxAI(self.air, -53.98, -89.42, 0.52, 187.0, self.zoneId)
            self.safezoneJukebox.generateWithRequired(self.zoneId)
            self.addDistObj(self.safezoneJukebox)

        if ServerSettings.SafezoneActivities.get():
            statuePositions = (
                (10, 124, 3.03, 240),
                (9, -128, 3.03, 294, 2003),  # PETE
                (94, -26, 4.03, 35, 20001),  # FLIPPY
                (-30, -85, 0.52, 6.7, 2005),  # LIBRARIAN LARRY
                (-140, -36, 0.52, 270),
                (-99.6, -77.5, 0.52, -40, 2006),  # CLARA
                (-65.5, -90.5, 0.52, 5, 2011),  # CLARK
                (-140, -26, 0.52, 270),
                (77, 164, 3.02, 180, 2004),
                (-133.3, 49.3, 0.52, 252, random.choice([2013, 2014, 2015])), # PET SHOP CLERKS
            )
            for pos in statuePositions:
                # if we have a 5th value, its a default npc id
                if len(pos) == 5:
                    statue = DistributedTTStatueActivityAI.DistributedTTStatueActivityAI(self.air, pos[4])
                else:
                    statue = DistributedTTStatueActivityAI.DistributedTTStatueActivityAI(self.air)
                statue.generateWithRequired(self.zoneId)
                statue.b_setXYZH(*pos[:4])
                self.addDistObj(statue)

        messenger.send('TTHoodSpawned', [self])

    def shutdown(self):
        HoodDataAI.HoodDataAI.shutdown(self)
        messenger.send('TTHoodDestroyed', [self])

    def _deleteTrolley(self, task):
        self.trolley.requestDelete()
        taskMgr.doMethodLater(0.5, self._createTrolley, 'createTrolley')
        return task.done

    def _createTrolley(self, task):
        trolley = DistributedTrolleyAI.DistributedTrolleyAI(self.air)
        trolley.generateWithRequired(self.zoneId)
        trolley.start()
        self.trolley = trolley
        taskMgr.doMethodLater(0.5, self._deleteTrolley, 'deleteTrolley')
        return task.done
