from .HolidayBaseAI import HolidayBaseAI
from direct.directnotify import DirectNotifyGlobal

from toontown.toonbase import ToontownGlobals, ServerSettings


class HolidayPropsAI(HolidayBaseAI):
    notify = DirectNotifyGlobal.directNotify.newCategory("HolidayPropsAI")

    def __init__(self, air, holidayId):
        HolidayBaseAI.__init__(self, air, holidayId)

    def start(self):
        HolidayBaseAI.start(self)
        for hood in self.air.hoods:
            if self.holidayId == ToontownGlobals.HALLOWEEN_PROPS:
                if not hasattr(hood, 'pumpkins'):
                    hood.createHalloweenProps()
            elif self.holidayId == ToontownGlobals.WINTER_DECORATIONS and not ServerSettings.YearRoundPresentTreasures.get():
                hood.createWinterProps()

    def stop(self):
        HolidayBaseAI.stop(self)
        for hood in self.air.hoods:
            if self.holidayId == ToontownGlobals.HALLOWEEN_PROPS:
                if hasattr(hood, 'pumpkins'):
                    hood.cleanupHalloweenProps()
            elif self.holidayId == ToontownGlobals.WINTER_DECORATIONS and not ServerSettings.YearRoundPresentTreasures.get():
                hood.cleanupWinterProps()