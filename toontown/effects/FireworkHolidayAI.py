import datetime
from direct.directnotify import DirectNotifyGlobal

from toontown.ai.HolidayBaseAI import HolidayBaseAI


class FireworkHolidayAI(HolidayBaseAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('FireworkHolidayAI')

    def __init__(self, air, holidayId):
        HolidayBaseAI.__init__(self, air, holidayId)
        self.showTask = None

    def start(self):
        if config.GetBool('want-quick-fireworks', False):
            self.__startShow()
        else:
            currentMinute = self.air.toontownTimeManager.getCurServerDateTime().now(tz=self.air.toontownTimeManager.serverTimeZone).minute
            if currentMinute == 0:
                # Holiday started right on top of the hour, start the show!
                self.__startShow()

        self.showTask = taskMgr.doMethodLater(self.__getSecondsTillHour(), self.__startShow, 'hourly-fireworks')

    def stop(self):
        taskMgr.remove(self.showTask)

    def __startShow(self, task=None):
        self.air.fireworkManager.startAllShows(self.holidayId)
        if task:
            task.delayTime = self.__getSecondsTillHour()
            self.notify.debug("Waiting %s seconds until next show" % (task.delayTime))
            return task.again

    def __getSecondsTillHour(self):
        if config.GetBool('want-quick-fireworks', False):
            return 60 * 3
        # Get the current epoch relative to the server's time zone.
        delta = datetime.timedelta(hours=1)
        now = datetime.datetime.now(tz=self.air.toontownTimeManager.serverTimeZone)
        hour = (now + delta).replace(microsecond=0, second=0, minute=0)
        seconds = (hour - now).seconds

        return seconds
