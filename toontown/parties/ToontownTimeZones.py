from datetime import tzinfo, datetime, timedelta


class ToontownTimeZone(tzinfo):
    """
    A simple implementation of US/Pacific time (UTC-08:00) that is only able to calculate
    correct DST for dates post-2006, which is perfectly acceptable for our use case.
    """
    offset = -8
    dstBegin = datetime(1, 3, 14, 2)  # DST begins on the second Sunday of March.
    dstEnd = datetime(1, 11, 7, 1)  # DST ends on the first Sunday of November.
    names = ('PST', 'PDT')

    @staticmethod
    def forwardToSunday(dt):
        daysToGo = 6 - dt.weekday()
        if daysToGo:
            dt += timedelta(daysToGo)

        return dt

    def dst(self, dt):
        # Determine if DST is active for the dt.
        beginning = self.forwardToSunday(self.dstBegin.replace(year = dt.year))
        ending = self.forwardToSunday(self.dstEnd.replace(year = dt.year))
        if beginning <= dt.replace(tzinfo = None) < ending:
            return timedelta(hours = 1)
        else:
            return timedelta(0)

    def utcoffset(self, dt):
        offset = timedelta(hours = self.offset)
        offset += self.dst(dt)
        return offset

    def tzname(self, dt):
        standardName, dstName = self.names
        if self.dst(dt):
            return dstName
        else:
            return standardName


class USEasternTimeZone(ToontownTimeZone):
    offset = -5
    names = ('EST', 'EDT')


class USCentralTimeZone(ToontownTimeZone):
    offset = -6
    names = ('CST', 'CDT')


class USMountainTimeZone(ToontownTimeZone):
    offset = -7
    names = ('MST', 'MDT')


class USPacificTimeZone(ToontownTimeZone):
    offset = -7
    names = ('PST', 'PDT')


class BritishTimeZone(ToontownTimeZone):
    dstBegin = datetime(1, 3, 28, 2)
    dstEnd = datetime(1, 10, 31, 1)
    offset = 1
    names = ('BST', 'BDT')