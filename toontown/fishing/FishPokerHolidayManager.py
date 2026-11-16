from direct.directnotify.DirectNotifyGlobal import directNotify
from toontown.ai.HolidayBaseAI import HolidayBaseAI


class FishPokerHolidayManager(HolidayBaseAI):
    notify = directNotify.newCategory('FishPokerHolidayManager')

    def __init__(self, air, holidayId):
        HolidayBaseAI.__init__(self, air, holidayId)

    def start(self):
        self.air.fishPokerManager.start()

    def stop(self):
        self.air.fishPokerManager.stop()
