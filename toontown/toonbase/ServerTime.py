from direct.interval.IntervalGlobal import Func

"""Base class that represents the current time on the server. Uses an interval to show it ticking in real time."""


class ServerTime:
    def __init__(self, hourCallback=None):
        self.hourCallback = hourCallback
        self.lastHour = -1
        self.lastMinute = -1
        self.ival = None

        self.setup()

    def setup(self):
        self.ival = self._createIval()
        self.ival.loop()

    def _createIval(self):
        return Func(self.updateTime)

    def cleanup(self):
        if self.ival:
            self.ival.finish()
            self.ival = None

    def updateTime(self):
        curServerDate = base.cr.toontownTimeManager.getCurServerDateTime()
        if self.hourCallback is not None:
            if curServerDate.hour != self.lastHour and self.lastHour != -1:
                self.lastHour = curServerDate.hour
                self.hourCallback(curServerDate.hour)

        # Returned so derived classes can use this
        return curServerDate