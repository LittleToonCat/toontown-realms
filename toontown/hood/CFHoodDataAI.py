from direct.directnotify import DirectNotifyGlobal

from toontown.toonbase import ToontownGlobals
from . import HoodDataAI


class CFHoodDataAI(HoodDataAI.HoodDataAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('CFHoodDataAI')

    def __init__(self, air, zoneId = None):
        hoodId = ToontownGlobals.ToontownSkies
        if zoneId is None:
            zoneId = hoodId
        super(CFHoodDataAI, self).__init__(air, zoneId, hoodId)
