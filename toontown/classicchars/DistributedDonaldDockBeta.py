from .DistributedDonaldDock import DistributedDonaldDock
from direct.directnotify import DirectNotifyGlobal


class DistributedDonaldDockBeta(DistributedDonaldDock):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedDonaldDockBeta')

    def __init__(self, cr):
        DistributedDonaldDock.__init__(self, cr)

    def handleHolidays(self):
        self.CCChatter = 0
