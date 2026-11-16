import datetime

from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI

from toontown.toonbase import ToontownGlobals

import os, json

# If we don't have a config directory, make it
if not os.path.exists('config/'):
    os.mkdir('config/')

holidayDefaults = '''{"1": [[6, 30, 0, 0], [7, 15, 23, 59]],
                      "2": [[12, 31, 0, 0], [1, 6, 23, 59]],
                      "4": [[12, 1, 0, 0], [1, 4, 23, 59]],
                      "9": [[10, 31, 0, 0], [10, 31, 23, 59]],
                      "13": [[10, 25, 0, 0], [11, 1, 23, 59]],
                      "26": [[10, 25, 0, 0], [11, 1, 23, 59]],
                      "27": [[10, 25, 0, 0], [11, 1, 23, 59]],
                      "29": [[4, 1, 0, 0], [4, 11, 23, 59]],
                      "57": [[12, 16, 0, 0], [1, 4, 23, 59]],
                      "59": [[2, 9, 0, 0], [2, 16, 23, 59]],
                      "60": [[3, 23, 0, 0], [4, 11, 23, 59]],
                      "105": [[3, 14, 0, 0], [3, 20, 23, 59]],
                      "113": [[6, 6, 0, 0], [6, 14, 23, 59]],
                      "114": [[6, 6, 0, 0], [6, 14, 23, 59]],
                      "115": [[6, 6, 0, 0], [6, 14, 23, 59]],
                      "124": [[3, 15, 0, 0], [3, 15, 23, 59]],
                      "125": [[4, 15, 0, 0], [4, 15, 23, 59]],
                      "126": [[5, 28, 0, 0], [5, 28, 23, 59]],
                      "127": [[10, 31, 0, 0], [10, 31, 23, 59]],
                      "128": [[4, 1, 0, 0], [4, 1, 23, 59]]}'''

# If holiday.json doesn't exist, make it
if not os.path.isfile('config/holidays.json'):
    with open('config/holidays.json', 'w') as data:
        data.write(holidayDefaults)
        data.close()

# Now load the data from spellbook.json
with open('config/holidays.json') as data:
    yearlyHolidays = json.load(data)


class NewsManagerAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('NewsManagerAI')

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)
        self.weeklyCalendarHolidays = []
        self.yearlyCalendarHolidays = []
        self.oncelyCalendarHolidays = []
        self.relativelyCalendarHolidays = []
        self.multipleStartHolidays = []
        self.forcedHolidays = []

    def announceGenerate(self):
        DistributedObjectAI.announceGenerate(self)

        # Setup our weekly calendar holidays.
        self.setupWeeklyCalendarHolidays()

        # Setup our yearly calendar holidays.
        self.setupYearlyCalendarHolidays()

        # Setup our forced holidays from the config.
        self.setupForcedHolidays()

        # Setup our weekly calendar holiday task.
        taskMgr.add(self.__weeklyCalendarHolidayTask, self.uniqueName('weekly-calendar-holiday-task'))

        # Handle avatars entering the district.
        self.accept('avatarEntered', self.handleAvatarEntered)

    def delete(self):
        DistributedObjectAI.delete(self)
        taskMgr.remove(self.uniqueName('silly-saturday-task'))
        taskMgr.remove(self.uniqueName('start-silly-saturday-bingo'))
        taskMgr.remove(self.uniqueName('start-silly-saturday-circuit'))
        taskMgr.remove(self.uniqueName('start-weekly-calendar-holiday'))

    def handleAvatarEntered(self, avatar):
        if self.air.suitInvasionManager.getInvading():
            # Let this poor avatar who just came in the game know that there
            # is a Cog Invasion taking place
            cogList, special, virtual, mega = self.air.suitInvasionManager.getCogType()
            numRemaining = self.air.suitInvasionManager.getNumCogsRemaining()
            self.sendAvatarInvasionStatus(avatar.getDoId(), cogList, numRemaining, special, virtual, mega)

        if self.air.holidayManager.isHolidayRunning(ToontownGlobals.SILLY_SATURDAY_BINGO) or \
                self.air.holidayManager.isHolidayRunning(ToontownGlobals.SILLY_SATURDAY_CIRCUIT) or \
                self.air.holidayManager.isHolidayRunning(ToontownGlobals.SILLY_SATURDAY_TROLLEY) or \
                self.air.holidayManager.isHolidayRunning(ToontownGlobals.ROAMING_TRIALER_WEEKEND):
            self.sendUpdateToAvatarId(avatar.getDoId(), 'holidayNotify', [])

        # If we are not permanently muted ...
        # send a status update letting know when our mute expires.
        if hasattr(avatar, 'muted') and avatar.mutedMinutes:
            muted, minutes = avatar.getMuted()
            avatar.sendMutedSystemMessage(muted, minutes)

    def setupWeeklyCalendarHolidays(self):
        # Get our current list of weekly calendar holidays.
        weeklyCalendarHolidays = self.getWeeklyCalendarHolidays()[:]

        # These are the weekly events that run consistently each week.
        weeklyEvents = [
            # [holidayId, weekday]
            [ToontownGlobals.CIRCUIT_RACING, 0],  # Grand Prix Mondays
            [ToontownGlobals.FISH_BINGO_NIGHT, 2],  # Fish Bingo Wednesdays
            [ToontownGlobals.TROLLEY_HOLIDAY, 3],   # Trolley Track Thursdays
            [ToontownGlobals.SILLY_SATURDAY, 5]  # Silly Saturdays
        ]

        if simbase.config.GetBool('want-random-black-cat-day', False):
            # Black Cat Day (this will only start if day is a Friday the 13th)
            weeklyEvents.append([ToontownGlobals.SPOOKY_BLACK_CAT, 4])

        # If an event from weeklyEvents doesn't already exist in weeklyCalendarHolidays, add it.
        for weeklyEvent in weeklyEvents:
            if weeklyEvent not in weeklyCalendarHolidays:
                weeklyCalendarHolidays.append(weeklyEvent)

        self.b_setWeeklyCalendarHolidays(weeklyCalendarHolidays)

    def setupYearlyCalendarHolidays(self):
        # Get our current list of yearly calendar holidays.
        yearlyCalendarHolidays = self.getYearlyCalendarHolidays()[:]

        # If an event from yearlyEvents doesn't already exist in yearlyCalendarHolidays, add it.
        for yearlyEvent in yearlyHolidays:
            dates = yearlyHolidays.get(yearlyEvent)
            event = [int(yearlyEvent), dates[0], dates[1]]
            if event not in yearlyCalendarHolidays:
                yearlyCalendarHolidays.append(event)

        self.b_setYearlyCalendarHolidays(yearlyCalendarHolidays)

    def setupForcedHolidays(self):
        # These holidays are defined in the PRC configuration, (normally used for debugging.)
        holidays = simbase.config.GetString('active-holidays', '')
        if holidays != '':
            for holiday in holidays.split(', '):
                holidayId = int(holiday)
                self.forcedHolidays.append(holidayId)

    def __weeklyCalendarHolidayTask(self, task):
        # If needed, these will hold the holiday IDs for holidays that we want to start and/or end.
        holidaysToStart = []
        holidaysToEnd = []

        # Add any forced holidays to holidaysToStart if defined (either defined from configuration,
        # or fired later on with magic words.)
        holidaysToStart += self.forcedHolidays

        # Get our current list of weekly calendar holidays.
        weeklyCalendarHolidays = self.getWeeklyCalendarHolidays()[:]

        # Get our current list of yearly calender holidays.
        yearlyCalendarHolidays = self.getYearlyCalendarHolidays()[:]

        # Get our current day of the week.
        currentWeekday = self.air.toontownTimeManager.getCurServerDateTime().now(
            tz=self.air.toontownTimeManager.serverTimeZone).weekday()

        # We will now loop through all of our weekly calendar holidays.
        for weeklyCalendarHoliday in weeklyCalendarHolidays:
            # If this particular holiday is Silly Saturday, perform some special logic.
            '''if weeklyCalendarHoliday[0] == ToontownGlobals.SILLY_SATURDAY_BINGO:
                # Check if the current day of the week matches the desired day of the week.
                if currentWeekday == weeklyCalendarHoliday[1]:
                    # Silly Saturday Holiday manager takes care of this all
                    # It does, so let's get the current hour.
                    currentHour = self.air.toontownTimeManager.getCurServerDateTime().now(
                        tz=self.air.toontownTimeManager.serverTimeZone).hour

                    # Silly Saturday events rotate every two hours. Fish Bingo starts first at midnight for two hours,
                    # then Grand Prix, then the cycle repeats until the end of Saturday. Let's see if we should run
                    # Fish Bingo.
                    if not ((currentHour // 2) % 12) % 2:
                        # It's time for Fish Bingo! Let's see if it's already running.
                        if not self.air.holidayManager.isHolidayRunning(ToontownGlobals.SILLY_SATURDAY_BINGO):
                            # Looks like Fish Bingo isn't currently running! Now let's check to see if the Grand Prix
                            # is currently running or not.
                            if self.air.holidayManager.isHolidayRunning(ToontownGlobals.SILLY_SATURDAY_CIRCUIT):
                                # The Grand Prix is currently running. In that case, we want to end the Grand Prix,
                                # then wait 5 seconds before starting Fish Bingo.
                                self.air.holidayManager.endHoliday(ToontownGlobals.SILLY_SATURDAY_CIRCUIT)
                                taskMgr.doMethodLater(5, self.air.holidayManager.startHoliday,
                                                      self.uniqueName('start-silly-saturday-bingo'),
                                                      extraArgs=[ToontownGlobals.SILLY_SATURDAY_BINGO], appendTask=True)
                            else:
                                # The Grand Prix is currently not running. In that case, we can just go ahead and
                                # start Fish Bingo.
                                self.air.holidayManager.startHoliday(ToontownGlobals.SILLY_SATURDAY_BINGO)
                    else:
                        # It's time for the Grand Prix! Let's see if it's already running.
                        if not self.air.holidayManager.isHolidayRunning(ToontownGlobals.SILLY_SATURDAY_CIRCUIT):
                            # Looks like the Grand Prix isn't currently running! Now let's check to see if
                            # Fish Bingo is currently running or not.
                            if self.air.holidayManager.isHolidayRunning(ToontownGlobals.SILLY_SATURDAY_BINGO):
                                # Fish Bingo is currently running. In that case, we want to end Fish Bingo, then wait
                                # 5 seconds before starting the Grand Prix.
                                self.air.holidayManager.endHoliday(ToontownGlobals.SILLY_SATURDAY_BINGO)
                                taskMgr.doMethodLater(5, self.air.holidayManager.startHoliday,
                                                      self.uniqueName('start-silly-saturday-circuit'),
                                                      extraArgs=[ToontownGlobals.SILLY_SATURDAY_CIRCUIT],
                                                      appendTask=True)
                            else:
                                # Fish Bingo is currently not running. In that case, we can just go ahead and start
                                # the Grand Prix.
                                self.air.holidayManager.startHoliday(ToontownGlobals.SILLY_SATURDAY_CIRCUIT)

                    # Silly Saturday management is all done, time to do some other stuff now.
                    continue
                else:
                    # It does not, so we want to end any Silly Saturday holidays if they are still running.
                    # Let's check if Fish Bingo is currently running.
                    if self.air.holidayManager.isHolidayRunning(ToontownGlobals.SILLY_SATURDAY_BINGO):
                        # It is, so we will now end Fish Bingo.
                        self.air.holidayManager.endHoliday(ToontownGlobals.SILLY_SATURDAY_BINGO)

                    # Now let's check if the Grand Prix is currently running.
                    if self.air.holidayManager.isHolidayRunning(ToontownGlobals.SILLY_SATURDAY_CIRCUIT):
                        # It is, so we will now end the Grand Prix.
                        self.air.holidayManager.endHoliday(ToontownGlobals.SILLY_SATURDAY_CIRCUIT)
            else:
                # We've landed on a holiday other than Silly Saturday! These are a lot more straightforward.
                # Check if the current day of the week matches the desired day of the week.
                if currentWeekday == weeklyCalendarHoliday[1]:
                    # It does, so let's check if this holiday is currently running or not.
                    if not self.air.holidayManager.isHolidayRunning(weeklyCalendarHoliday[0]):
                        # It is not, so we will add it to holidaysToStart.
                        holidaysToStart.append(weeklyCalendarHoliday[0])
                else:
                    # It does not, so we want to end the holiday, so let's check if it's currently running or not.
                    if self.air.holidayManager.isHolidayRunning(weeklyCalendarHoliday[0]):
                        # It is, so we will add it to holidaysToEnd.
                        holidaysToEnd.append(weeklyCalendarHoliday[0])'''

            if currentWeekday == weeklyCalendarHoliday[1]:
                # Don't do anything if the Friday of a Black Cat holiday is not a 13th
                if weeklyCalendarHoliday[0] == ToontownGlobals.SPOOKY_BLACK_CAT:
                    if not datetime.date.today().day == 13:
                        continue
                # It does, so let's check if this holiday is currently running or not.
                if not self.air.holidayManager.isHolidayRunning(weeklyCalendarHoliday[0]):
                    # It is not, so we will add it to holidaysToStart.
                    holidaysToStart.append(weeklyCalendarHoliday[0])
            else:
                # It does not, so we want to end the holiday, so let's check if it's currently running or not.
                if self.air.holidayManager.isHolidayRunning(weeklyCalendarHoliday[0]):
                    # It is, so we will add it to holidaysToEnd.
                    holidaysToEnd.append(weeklyCalendarHoliday[0])

        # Get the current datetime for yearly holiday comparision.
        currentTime = self.air.toontownTimeManager.getCurServerDateTime().now(
            tz=self.air.toontownTimeManager.serverTimeZone)
        # We will now loop through all of our yearly calendar holidays.
        for yearlyCalendarHoliday in yearlyCalendarHolidays:
            # Get the start month, day, hour, and minute of the holiday.
            startMonth, startDay, startHour, startMinute = yearlyCalendarHoliday[1]
            # Create a startDate for comparision.
            startDate = datetime.datetime(year=currentTime.year, month=startMonth, day=startDay,
                                          hour=startHour, minute=startMinute,
                                          second=0, tzinfo=self.air.toontownTimeManager.serverTimeZone)
            # Check if the current time has past the start holiday date.
            if currentTime > startDate:
                # It has, now check if it's past the end holiday date.
                endMonth, endDay, endHour, endMinute = yearlyCalendarHoliday[2]
                # Create a endDate for comparision.
                endDate = datetime.datetime(year=currentTime.year, month=endMonth, day=endDay,
                                            hour=endHour, minute=endMinute,
                                            second=0, tzinfo=self.air.toontownTimeManager.serverTimeZone)
                # Before we compare the two dates, check if it's a winter holiday we're dealing with,
                # and if the current month is December...
                if currentTime.month == 12 and yearlyCalendarHoliday[0] in \
                [ToontownGlobals.WINTER_DECORATIONS, ToontownGlobals.WINTER_CAROLING, ToontownGlobals.NEWYEARS_FIREWORKS]:
                    # It is.  So we need to create a new endDate, because it is set to end after the new year,
                    # If we don't do this, the holiday would most likely never start at all.
                    endDate = datetime.datetime(year=currentTime.year + 1, month=endMonth, day=endDay,
                                                hour=endHour, minute=endMinute,
                                                second=0, tzinfo=self.air.toontownTimeManager.serverTimeZone)
                # Check if it current time has passed the endDate.
                if currentTime > endDate:
                    # It has, we want to end the holiday, let's check if it's currently running or not.
                    if self.air.holidayManager.isHolidayRunning(yearlyCalendarHoliday[0]):
                        # It is, so we will add it to holidaysToEnd.
                        holidaysToEnd.append(yearlyCalendarHoliday[0])
                else:
                    # It has not, that must mean the the holiday must begin.  Let's check if it's currently running or not.
                    if not self.air.holidayManager.isHolidayRunning(yearlyCalendarHoliday[0]):
                        # It does not, so we will add it to holidaysToStart.
                        holidaysToStart.append(yearlyCalendarHoliday[0])
            else:
                # It has not, the time is too early to start that particular holiday, let's end it.
                # Check if it's currently running or not.
                if self.air.holidayManager.isHolidayRunning(yearlyCalendarHoliday[0]):
                    # It is, so we will add it to holidaysToEnd.
                    holidaysToEnd.append(yearlyCalendarHoliday[0])

        # We will now loop through all of our holidays that we want to end.
        for holidayToEnd in holidaysToEnd:
            # Check if the holiday is forced-started.
            if holidayToEnd in self.forcedHolidays:
                # It is, ignore, and continue on.
                continue
            # Let's check if this holiday is currently running or not.
            if self.air.holidayManager.isHolidayRunning(holidayToEnd):
                # It is, so let's end it.
                self.air.holidayManager.endHoliday(holidayToEnd)

        # We will now loop through all of our holidays that we want to start.
        for holidayToStart in holidaysToStart:
            # Let's check if this holiday is currently running or not.
            if not self.air.holidayManager.isHolidayRunning(holidayToStart):
                # It is not, so let's check if holidaysToEnd is not empty. If it isn't, then that means we just ended
                # one or more holidays. If this is the case, we want to delay the new holidays starting by 5 seconds.
                if holidaysToEnd:
                    # holidaysToEnd is not empty, so delay the holidays starting by 5 seconds.
                    taskMgr.doMethodLater(5, self.air.holidayManager.startHoliday,
                                          self.uniqueName('start-weekly-calendar-holiday'), extraArgs=[holidayToStart],
                                          appendTask=True)
                else:
                    # holidaysToEnd is empty, so we can just start the new holidays right away.
                    self.air.holidayManager.startHoliday(holidayToStart)

        self.sendUpdate('newsManagerDone', [])

        # We want this task to run again at midnight. We'll calculate the seconds until midnight, then
        # delay the task from running again until then.
        tomorrow = self.air.toontownTimeManager.getCurServerDateTime().now(
            tz=self.air.toontownTimeManager.serverTimeZone) + datetime.timedelta(1)
        midnight = datetime.datetime(year=tomorrow.year, month=tomorrow.month, day=tomorrow.day, hour=0, minute=0,
                                     second=0, tzinfo=self.air.toontownTimeManager.serverTimeZone)
        secondsUntilMidnight = (midnight - self.air.toontownTimeManager.getCurServerDateTime().now(
            tz=self.air.toontownTimeManager.serverTimeZone)).seconds
        task.delayTime = secondsUntilMidnight
        return task.again

    def setWeeklyCalendarHolidays(self, weeklyCalendarHolidays):
        self.weeklyCalendarHolidays = weeklyCalendarHolidays

    def d_setWeeklyCalendarHolidays(self, weeklyCalendarHolidays):
        self.sendUpdate('setWeeklyCalendarHolidays', [weeklyCalendarHolidays])

    def b_setWeeklyCalendarHolidays(self, weeklyCalendarHolidays):
        self.setWeeklyCalendarHolidays(weeklyCalendarHolidays)
        self.d_setWeeklyCalendarHolidays(weeklyCalendarHolidays)

    def getWeeklyCalendarHolidays(self):
        return self.weeklyCalendarHolidays

    def setYearlyCalendarHolidays(self, yearlyCalendarHolidays):
        self.yearlyCalendarHolidays = yearlyCalendarHolidays

    def d_setYearlyCalendarHolidays(self, yearlyCalendarHolidays):
        self.sendUpdate('setYearlyCalendarHolidays', [yearlyCalendarHolidays])

    def b_setYearlyCalendarHolidays(self, yearlyCalendarHolidays):
        self.setYearlyCalendarHolidays(yearlyCalendarHolidays)
        self.d_setYearlyCalendarHolidays(yearlyCalendarHolidays)

    def getYearlyCalendarHolidays(self):
        return self.yearlyCalendarHolidays

    def setOncelyCalendarHolidays(self, oncelyCalendarHolidays):
        self.oncelyCalendarHolidays = oncelyCalendarHolidays

    def d_setOncelyCalendarHolidays(self, oncelyCalendarHolidays):
        self.sendUpdate('setOncelyCalendarHolidays', [oncelyCalendarHolidays])

    def b_setOncelyCalendarHolidays(self, oncelyCalendarHolidays):
        self.setOncelyCalendarHolidays(oncelyCalendarHolidays)
        self.d_setOncelyCalendarHolidays(oncelyCalendarHolidays)

    def getOncelyCalendarHolidays(self):
        return self.oncelyCalendarHolidays

    def setRelativelyCalendarHolidays(self, relativelyCalendarHolidays):
        self.relativelyCalendarHolidays = relativelyCalendarHolidays

    def d_setRelativelyCalendarHolidays(self, relativelyCalendarHolidays):
        self.sendUpdate('setRelativelyCalendarHolidays', [relativelyCalendarHolidays])

    def b_setRelativelyCalendarHolidays(self, relativelyCalendarHolidays):
        self.setRelativelyCalendarHolidays(relativelyCalendarHolidays)
        self.d_setRelativelyCalendarHolidays(relativelyCalendarHolidays)

    def getRelativelyCalendarHolidays(self):
        return self.relativelyCalendarHolidays

    def setMultipleStartHolidays(self, multipleStartHolidays):
        self.multipleStartHolidays = multipleStartHolidays

    def d_setMultipleStartHolidays(self, multipleStartHolidays):
        self.sendUpdate('setMultipleStartHolidays', [multipleStartHolidays])

    def b_setMultipleStartHolidays(self, multipleStartHolidays):
        self.setMultipleStartHolidays(multipleStartHolidays)
        self.d_setMultipleStartHolidays(multipleStartHolidays)

    def getMultipleStartHolidays(self):
        return self.multipleStartHolidays

    def invasionBegin(self, cogType, numRemaining, special, virtual, mega):
        self.d_setInvasionStatus(ToontownGlobals.SuitInvasionBegin, cogType, numRemaining, special, virtual, mega)

    def invasionEnd(self, cogType, numRemaining, special, virtual, mega):
        self.d_setInvasionStatus(ToontownGlobals.SuitInvasionEnd, cogType, numRemaining, special, virtual, mega)

    def invasionUpdate(self, cogType, numRemaining, special, virtual, mega):
        # Broadcast an invasion update to all players
        self.d_setInvasionStatus(ToontownGlobals.SuitInvasionUpdate, cogType, numRemaining, special, virtual, mega)

    def sendAvatarInvasionStatus(self, avId, cogList, numRemaining, special, virtual, mega):
        # Send an invasion update to only one avatar
        self.sendUpdateToAvatarId(avId, "setInvasionStatus",
                                  [ToontownGlobals.SuitInvasionBulletin, cogList, numRemaining, special, virtual, mega])

    def d_setInvasionStatus(self, msgType, cogType, numRemaining, special, virtual, mega):
        # This exists for the periscope NPC type to play unique animations for invasion messages
        messenger.send('invasionStatusMessage', [cogType, special, virtual, msgType, mega])

        self.sendUpdate("setInvasionStatus", [msgType, cogType, numRemaining, special, virtual, mega])

    def d_setOnlineStatus(self, online, doId, name):
        self.sendUpdate('setOnlineStatus', [online, doId, name])

    def d_setHolidayIdList(self, holidayIdList):
        self.sendUpdate('setHolidayIdList', [holidayIdList])

    def bingoStart(self):
        self.sendUpdate('setBingoStart')

    def bingoEnd(self):
        self.sendUpdate('setBingoEnd')

    def pokerStart(self):
        self.sendUpdate('setPokerStart')

    def pokerEnd(self):
        self.sendUpdate('setPokerEnd')

    def circuitRaceStart(self):
        self.sendUpdate('setCircuitRaceStart')

    def circuitRaceEnd(self):
        self.sendUpdate('setCircuitRaceEnd')

    def d_setExpSettings(self, mult, cap):
        self.sendUpdate('setExpSettings', [mult, cap])

    def trolleyHolidayStart(self):
        self.sendUpdate('setTrolleyHolidayStart')

    def trolleyHolidayEnd(self):
        self.sendUpdate('setTrolleyHolidayEnd')

    def trolleyWeekendStart(self):
        self.sendUpdate('setTrolleyWeekendStart')

    def trolleyWeekendEnd(self):
        self.sendUpdate('setTrolleyWeekendEnd')

    def d_notifyHardcoreBossWon(self, numToons, dept):
        self.sendUpdate('notifyHardcoreBossWon', [numToons, dept])
