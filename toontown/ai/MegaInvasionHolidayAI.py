from direct.directnotify.DirectNotifyGlobal import directNotify
from toontown.toonbase import ToontownGlobals

from toontown.ai.HolidayBaseAI import HolidayBaseAI


_holidayId2Cog = {
    # holiday ID: suit type, skeleton
    ToontownGlobals.MEGAINVASION_IDES_OF_MARCH: ('bs', False),
    ToontownGlobals.MEGAINVASION_TAX_DAY: ('nc', False),
    ToontownGlobals.MEGAINVASION_MEMORIAL_DAY: ('mh', False),
    ToontownGlobals.MEGAINVASION_HALLOWEEN: ('b', False),
}


class MegaInvasionHolidayMgrAI(HolidayBaseAI):
    notify = directNotify.newCategory('MegaInvasionHolidayMgrAI')

    def start(self):
        if self.holidayId in _holidayId2Cog:
            if self.air.suitInvasionManager.getInvading():
                if self.air.suitInvasionManager.mega:
                    # don't run if we're already running a mega-invasion
                    self.notify.warning("A Mega-Invasion is already running!")
                    return
                self.air.suitInvasionManager.stopInvasion()

            self.air.suitInvasionManager.startInvasion(_holidayId2Cog[self.holidayId][0],
                                                       1000000,  # cog count doesn't matter
                                                       _holidayId2Cog[self.holidayId][1],
                                                       False, True)
            self.notify.debug("Started Mega-Invasion")

    def stop(self):
        if self.air.suitInvasionManager.getInvading() and self.air.suitInvasionManager.mega:
            # only stop a mega-invasion
            self.air.suitInvasionManager.stopInvasion()
