from .HolidayBaseAI import HolidayBaseAI
from direct.directnotify import DirectNotifyGlobal

from toontown.ai import DistributedSillyMeterMgrAI
from toontown.toonbase import ToontownGlobals

from datetime import datetime

NUM_PHASES = 15


class SillyMeterHolidayAI(HolidayBaseAI):
    notify = DirectNotifyGlobal.directNotify.newCategory("SillyMeterHolidayAI")

    def __init__(self, air, holidayId, startTime, endTime):
        HolidayBaseAI.__init__(self, air, holidayId)
        self.sillyMeterMgr = None
        self.dates = self.calculateDates(startTime, endTime)

    def start(self):
        HolidayBaseAI.start(self)
        self.sillyMeterMgr = DistributedSillyMeterMgrAI.DistributedSillyMeterMgrAI(self.air, True, NUM_PHASES, 0,
                                                                                   self.dates)
        self.sillyMeterMgr.generateWithRequired(ToontownGlobals.ToonHall)

        taskMgr.add(self.checkPhase, 'checkPhase')

    def calculateDates(self, startTime, endTime):
        curYear = datetime.now().year

        startDate = datetime(curYear, startTime[0], startTime[1], startTime[2], startTime[3], 0,
                             tzinfo=self.air.toontownTimeManager.serverTimeZone)
        endDate = datetime(curYear, endTime[0], endTime[1], endTime[2], endTime[3], 0,
                           tzinfo=self.air.toontownTimeManager.serverTimeZone)

        # Get all phase dates by dividing the event's total length by the number of phases
        length = endDate - startDate
        self.phaseDuration = length / NUM_PHASES
        dates = []
        phaseTime = startDate
        for i in range(NUM_PHASES):
            dates.append((phaseTime.year, phaseTime.month, phaseTime.day, phaseTime.hour, phaseTime.minute,
                          phaseTime.second))
            phaseTime += self.phaseDuration
        return dates

    def checkPhase(self, task):
        currentTime = self.air.toontownTimeManager.getCurServerDateTime().now(
            tz=self.air.toontownTimeManager.serverTimeZone)
        try:
            year, month, day, hour, min, sec = self.sillyMeterMgr.getDates()[self.sillyMeterMgr.getCurPhase() + 1]
            nextPhaseTime = datetime(year, month, day, hour, min, sec,
                                     tzinfo=self.air.toontownTimeManager.serverTimeZone)
        except IndexError:
            try:
                year, month, day, hour, min, sec = self.sillyMeterMgr.getDates()[self.sillyMeterMgr.getCurPhase()]
                nextPhaseTime = datetime(year, month, day, hour, min, sec,
                                         tzinfo=self.air.toontownTimeManager.serverTimeZone) + self.phaseDuration
            except IndexError:
                # Holiday has most likely been started outside the normal time. No need to run this task.
                return task.done

        if nextPhaseTime <= currentTime:
            try:
                self.sillyMeterMgr.b_setCurPhase(self.sillyMeterMgr.getCurPhase() + 1)
            except IndexError:
                # We've reached the end of the dates. Time to end.
                return task.done

        return task.again

    def stop(self):
        HolidayBaseAI.stop(self)

        taskMgr.remove('checkPhase')

        self.sillyMeterMgr.requestDelete()
        self.sillyMeterMgr = None
