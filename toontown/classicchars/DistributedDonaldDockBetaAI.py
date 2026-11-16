from .DistributedDonaldDockAI import DistributedDonaldDockAI
from direct.directnotify import DirectNotifyGlobal


class DistributedDonaldDockBetaAI(DistributedDonaldDockAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedDonaldDockBetaAI')

    def __init__(self, air):
        DistributedDonaldDockAI.__init__(self, air)

    def handleHolidays(self):
        self.CCChatter = 0
