"""Time related utility functions and classes."""
from datetime import datetime
from datetime import timedelta
from datetime import tzinfo

from toontown.parties import ToontownTimeManager
from direct.directnotify.DirectNotifyGlobal import *


LOCAL_TIMEZONE = ToontownTimeManager.ToontownTimeZone()
UTC_TIMEZONE = ToontownTimeManager.UTC()


def toDateTime(year, month, day, hour=0, minute=0, second=0, microsecond=0, utc=False, tz=None):
    """
    Generate a datetime object.
    :param year: datetime year; default: this year
    :param month: datetime month; default: this month
    :param day: datetime day; default: this day
    :param hour: datetime hour; default: 0
    :param minute: datetime minute; default: 0
    :param second: datetime second; default: 0
    :param microsecond: datetime microsecond; default: 0
    :param utc: Whether to use UTC or not; default: False
    :param tz: the tzinfo to use for the datetime object, if not using utc=True; default: LOCAL_TIMEZONE if None or invalid
    :return:    the generated datetime object
    """
    if utc:
        return datetime(year, month, day, hour, minute, second, microsecond, UTC_TIMEZONE)
    elif tz is not None and isinstance(tz, tzinfo):
        return datetime(year, month, day, hour, minute, second, microsecond, tz)
    else:
        return datetime(year, month, day, hour, minute, second, microsecond, LOCAL_TIMEZONE)


class DateTime(object):
    """Class that allows for easier datetime manipulations."""
    notify = directNotify.newCategory('DateTime')

    def __init__(self, utc=False):
        """
        Class for constructing a Time object.
        :param utc: Whether to use the UTC timezone or not; default: False
        """
        # set defaults
        self.__tz = UTC_TIMEZONE
        self.__utc = True
        # now, set stuff based on init params
        self.utc = utc

    def _datetime(self, year, month, day, hour=0, minute=0, second=0, microsecond=0):
        """
        Generates a new datetime object.
        :param year: datetime year
        :param month: datetime month
        :param day: datetime day
        :param hour: datetime hour
        :param minute: datetime minute
        :param second: datetime second
        :param microsecond: datetime microsecond
        :return: The generated datetime object
        """
        # we cheat a bit here, but that's alright by me...
        return toDateTime(year, month, day, hour, minute, second, microsecond, tz=self.tz)

    def now(self):
        """
        Return datetime object for now.
        :return: The datetime object for now
        """
        return datetime.now(self.tz)

    @property
    def tz(self):
        """
        Return timezone object.
        :return: the timezone object we are using
        """
        return self.__tz

    @tz.setter
    def tz(self, tz):
        """
        Set timezone object.
        :param tz: The timezone object to now use
        :return:
        """
        if not isinstance(tz, tzinfo):
            self.notify.error("tz must be a valid tzinfo subclass; see 'https://docs.python.org/2/library/" +
                              "datetime.html#datetime.tzinfo'.")
        if self.tz != tz:
            tmp = datetime.now(tz)
            if self.utc and tmp.tzinfo != 'UTC':
                self.__utc = False
            elif not self.utc and tmp.tzinfo == 'UTC':
                self.__utc = True
            self.__tz = tz

    @property
    def utc(self):
        """
        Returns whether we are using UTC or not.
        :return:    True/False (see above)
        """
        return self.__utc

    @utc.setter
    def utc(self, utc):
        """
        Sets the timezone to UTC if True, LOCAL_TIMEZONE if False
        :param utc: Bool that sets timezone, as stated above.
        :return:
        """
        if not isinstance(utc, bool):
            self.notify.error('utc must be of type bool!')
        self.__utc = utc
        if self.__utc:
            self.tz = UTC_TIMEZONE
        else:
            self.tz = LOCAL_TIMEZONE

    @property
    def day(self):
        """
        Return current day.
        :return: current day in range (1-31)
        """
        return self.now().day

    @property
    def year(self):
        """
        Return current year.
        :return: current day in range (0-9999)
        """
        return self.now().year

    @property
    def month(self):
        """
        Return current month.
        :return: current month in range (1-12)
        """
        return self.now().month

    @property
    def hour(self):
        """
        Return current hour.
        :return: current hour in range (0-23)
        """
        return self.now().hour

    @property
    def minutes(self):
        """
        Return current day.
        :return: current day in range (0-59)
        """
        return self.now().minute

    @property
    def seconds(self):
        """
        Return current seconds.
        :return: current seconds in range (0-59)
        """
        return self.now().second

    @property
    def microseconds(self):
        """
        Return current microseconds.
        :return: current microseconds in range (0-999999)
        """
        return self.now().microsecond


class EpochTime(DateTime):
    """Class that holds all utility functions for epoch time manipulation."""
    notify = directNotify.newCategory('EpochTime')

    def now(self):
        """
        Return current time in seconds since epoch.
        :return: float of above
        """
        return self.__calc_epoch(DateTime.now(self))

    def timestamp(self, year=None, month=None, day=None, hour=0, minute=0, second=0, microsecond=0):
        """
        Return timestamp calculated with args passed in; default: start of today.
        :param year:
        :param month:
        :param day:
        :param hour:
        :param minute:
        :param second:
        :param microsecond:
        :return:
        """
        if year is None:
            year = self.year
        if month is None:
            month = self.month
        if day is None:
            day = self.day
        dt = self._datetime(year, month, day, hour, minute, second, microsecond)
        return self.__calc_epoch(dt)

    def __calc_epoch(self, dt):
        """
        Calculate epoch time via datetime difference calculation.
        :param dt: The datetime object for calculating epoch time.
        :return:
        """
        epoch = self.epoch()
        if not isinstance(dt, datetime):
            self.notify.error('dt must be a datetime object.')
        if dt.tzname != 'UTC':
            dt = dt.astimezone(UTC_TIMEZONE)
        if dt < epoch:
            self.notify.error('datetime object must be greater than or equal to epoch time.')
        return (dt - epoch).total_seconds()

    @staticmethod
    def epoch():
        """
        Return datetime object for epoch.
        :return: The epoch datetime object
        """
        # again, we cheat a bit here, but oh well...
        return toDateTime(1970, 1, 1, 0, 0, 0, 0, utc=True)

    @property
    def dayRange(self):
        """
        Return start of today and start of tomorrow in seconds.
        :return: (start of today, start of tomorrow)
        """
        now = DateTime.now(self)
        # set to start of day
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        return self.__calc_epoch(today), self.__calc_epoch(tomorrow)

    @property
    def weekRange(self):
        """
        Return start of week and start of next week in seconds.
        :return: (start of this week, start of next week)
        """
        now = DateTime.now(self)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=7)
        return self.__calc_epoch(start), self.__calc_epoch(end)

    @property
    def monthRange(self):
        """
        Return start of month and start of next month in seconds.
        :return: (start of month, start of next month)
        """
        now = DateTime.now(self)
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            end = start.replace(month=1, year=now.year+1)
        else:
            end = start.replace(month=now.month+1)
        return self.__calc_epoch(start), self.__calc_epoch(end)

    @property
    def yearRange(self):
        """
        Return start of year and start of next year in seconds.
        :return: (start of year, start of next year)
        """
        now = DateTime.now(self)
        start = now.replace(day=1, month=1, hour=0, minute=0, second=0, microsecond=0)
        end = start.replace(year=now.year+1)
        return self.__calc_epoch(start), self.__calc_epoch(end)


__all__ = ['toDateTime', 'DateTime', 'EpochTime']
