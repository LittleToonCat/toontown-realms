from direct.directnotify import DirectNotifyGlobal
from direct.interval.IntervalGlobal import Sequence, Wait, EventInterval
from .DistributedFireworkShowAI import DistributedFireworkShowAI
from .FireworkShow import fireworkShowMessages, fireworkShowTypes
from toontown.hood import ZoneUtil
from toontown.toonbase.ToontownGlobals import DonaldsDock, ToontownCentral, TheBrrrgh, MinniesMelodyland, DaisyGardens,\
    OutdoorZone, GoofySpeedway, DonaldsDreamland


class FireworkManagerAI:
    """
    Manages Fireworks holidays
    """

    notify = DirectNotifyGlobal.directNotify.newCategory('FireworkManagerAI')

    zoneToStyleDict = {
        # Donald's Dock
        DonaldsDock: 5,
        # Toontown Central
        ToontownCentral: 0,
        # The Brrrgh
        TheBrrrgh: 4,
        # Minnie's Melodyland
        MinniesMelodyland: 3,
        # Daisy Gardens
        DaisyGardens: 1,
        # Acorn Acres
        OutdoorZone: 0,
        # GS
        GoofySpeedway: 0,
        # Donald's Dreamland
        DonaldsDreamland: 2,
        }

    def __init__(self, air):
        self.air = air
        # Dict from zone to DistFireworkShow objects
        self.fireworkShows = {}
        self.waitTaskName = 'waitStartFireworkShows'

    def startAllShows(self, holidayId):
        for hood in self.air.hoods:
            showType = self.zoneToStyleDict.get(hood.canonicalHoodId)
            if showType is not None and (not ZoneUtil.isBetaPlaygroundZone(hood.canonicalHoodId)):
                self.startShow(holidayId, hood.zoneId, showType)

    def startShow(self, holidayId, zone, showType=-1):
        """
        Start a show of showType in this zone.
        Returns 1 if a show was successfully started.
        Warns and returns 0 if a show was already running in this zone.
        There can only be one show per zone.
        """
        if self.isShowRunning(zone):
            self.notify.warning("startShow: already running a show in zone: %s" % zone)
            return 0
        self.notify.debug("startShow: zone: %s showType: %s" % (zone, showType))
        # Create a show, passing ourselves in so it can tell us when
        # the show is over
        show = DistributedFireworkShowAI(self.air, self)
        show.generateWithRequired(zone)
        self.fireworkShows[zone] = show
        # Currently needed to support legacy fireworks
        if self.air.config.GetBool('want-old-fireworks', 0):
            show.d_startShow(showType, showType)
        else:
            show.d_startShow(holidayId, showType)

        # For the safezone jukebox
        messenger.send('fireworks-started-%s' % zone)

        # For the Periscope NPC
        showMessages = fireworkShowMessages.get(holidayId)
        Sequence(EventInterval('notifyFireworks', [showMessages['start']]), Wait(2.5),
                 EventInterval('notifyFireworks', [showMessages['instructions']])).start()

        # Success!
        return 1

    def stopShow(self, zone):
        """
        Stop a firework show in this zone.
        Returns 1 if it did stop a show, warns and returns 0 if there is not one
        """
        if not self.isShowRunning(zone):
            self.notify.warning("stopShow: no show running in zone: %s" % zone)
            return 0
        self.notify.debug("stopShow: zone: %s" % zone)
        show = self.fireworkShows[zone]
        showType = show.eventId
        del self.fireworkShows[zone]
        show.requestDelete()

        # For the safezone jukebox
        messenger.send('fireworks-finished-%s' % zone)

        # For the Periscope NPC
        if showType != fireworkShowTypes[1]:
            showMessages = fireworkShowMessages.get(showType)
            messenger.send('notifyFireworks', [showMessages['end']])

        # Success!
        return 1

    def stopAllShows(self):
        """
        Stop all firework shows this manager knows about in all zones.
        Returns number of shows stopped by this command.
        """
        numStopped = 0
        for zone, show in self.fireworkShows.items():
            self.notify.debug("stopAllShows: zone: %s" % zone)
            show.requestDelete()
            numStopped += 1
        self.fireworkShows.clear()
        return numStopped

    def isShowRunning(self, zone):
        """
        Is there currently a show running in this zone?
        """
        return zone in self.fireworkShows
