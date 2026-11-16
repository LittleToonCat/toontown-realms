from direct.directnotify import DirectNotifyGlobal
from toontown.classicchars.DistributedDonaldAI import DistributedDonaldAI
from toontown.toonbase import ToontownGlobals


class DistributedDonaldDreamDayAI(DistributedDonaldAI):
    notify = DirectNotifyGlobal.directNotify.newCategory("DistributedDonaldDreamDayAI")

    def walkSpeed(self):
        return ToontownGlobals.BetaDonaldSpeed
