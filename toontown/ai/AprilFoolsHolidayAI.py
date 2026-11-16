from .HolidayBaseAI import HolidayBaseAI
from direct.directnotify import DirectNotifyGlobal

from toontown.toon.DistributedNPCToonBaseAI import DistributedNPCToonBaseAI
from toontown.suit import SuitDNA

import random


class AprilFoolsHolidayAI(HolidayBaseAI):
    notify = DirectNotifyGlobal.directNotify.newCategory("AprilFoolsHolidayAI")

    def __init__(self, air, holidayId):
        HolidayBaseAI.__init__(self, air, holidayId)

    def start(self):
        HolidayBaseAI.start(self)
        for doId, do in list(self.air.doId2do.items()):
            if isinstance(do, DistributedNPCToonBaseAI):
                level = SuitDNA.getRandomSuitType(random.randrange(1, 8))
                dna = SuitDNA.SuitDNA()
                dna.newSuitRandom(level)
                do.sendUpdate('setCogIndex', [dna.name, level])

    def stop(self):
        HolidayBaseAI.stop(self)
        for doId, do in list(self.air.doId2do.items()):
            if isinstance(do, DistributedNPCToonBaseAI):
                do.sendUpdate('setCogIndex', ['', 0])
