# NOTE: This is our own code for FireworkManagerAI before we replaced it with
# the original Disney code.  This is left for archival purposes.

import random
from direct.directnotify import DirectNotifyGlobal
from direct.interval.IntervalGlobal import Sequence, Wait, EventInterval

from toontown.toonbase import ToontownGlobals
from . import FireworkShows
from .FireworkShow import fireworkShowMessages, fireworkShowTypes
from .DistributedFireworkShowAI import DistributedFireworkShowAI


class FireworkManagerAI:
    notify = DirectNotifyGlobal.directNotify.newCategory('FireworkHolidayAI')

    def __init__(self, air):
        self.air = air
        self.zoneToShow = {}  # zoneId: FireworkShowAI
        # This is used purely to not send more than one event message when finishing every show
        self.finishedShow = False

    def startShow(self, showType):
        if self.isShowRunning():
            self.notify.warning("startShow called when show is already running!")
            return

        self.finishedShow = False

        if showType != fireworkShowTypes[1]:
            showMessages = fireworkShowMessages.get(showType)
            Sequence(EventInterval('notifyFireworks', [showMessages['start']]), Wait(2.5),
                     EventInterval('notifyFireworks', [showMessages['instructions']])).start()

        for hood in self.air.hoods:
            if hood.zoneId in (ToontownGlobals.SellbotHQ, ToontownGlobals.CashbotHQ,
                               ToontownGlobals.LawbotHQ, ToontownGlobals.BossbotHQ):
                return

            fireworkShow = DistributedFireworkShowAI(self.air, self)
            fireworkShow.generateWithRequired(hood.zoneId)

            if showType in FireworkShows.shows:
                style = random.randint(0, len(FireworkShows.shows[showType]) - 1)
            else:
                style = 0
            fireworkShow.d_startShow(showType, style)

            self.zoneToShow[hood.zoneId] = fireworkShow

    def stopShow(self, zoneId):
        fireworkShow = self.zoneToShow.get(zoneId)
        if not fireworkShow:
            # Non-existent firework show???
            return

        if not self.finishedShow:
            self.finishedShow = True
            showType = fireworkShow.eventId
            if showType != fireworkShowTypes[1]:
                showMessages = fireworkShowMessages.get(showType)
                messenger.send('notifyFireworks', [showMessages['end']])

        fireworkShow.requestDelete()
        del self.zoneToShow[zoneId]

    def isShowRunning(self):
        # True if FireworkShowAI is present, False otherwise.
        return self.zoneToShow
