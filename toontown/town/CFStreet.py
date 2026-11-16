from direct.task.Task import Task
from panda3d.core import TransparencyAttrib, NodePath, CompassEffect
from panda3d.toontown import NametagGlobals

from otp.distributed.TelemetryLimiter import RotationLimitToH, TLGatherAllAvs
from toontown.toon.Toon import teleportDebug
from toontown.toonbase import ToontownGlobals
from . import Street
from ..hood import SkyUtil


class CFStreet(Street.Street):

    def __init__(self, loader, parentFSM, doneEvent):
        Street.Street.__init__(self, loader, parentFSM, doneEvent)
        self.sky = self.loader.hood.sky
        self.skyFile = 'phase_3.5/models/props/TT_sky'

    def load(self):
        Street.Street.load(self)

    def unload(self):
        Street.Street.unload(self)

    def hideAllVisibles(self):
        if base.localAvatar.zoneId == ToontownGlobals.SellbotHQFuture:
            return
        Street.Street.hideAllVisibles(self)

    def showAllVisibles(self):
        if base.localAvatar.zoneId == ToontownGlobals.SellbotHQFuture:
            return
        Street.Street.showAllVisibles(self)

    def enterZone(self, newZone):
        if base.localAvatar.zoneId == ToontownGlobals.SellbotHQFuture:
            return
        Street.Street.enterZone(self, newZone)

    def doEnterZone(self, newZoneId):
        if base.localAvatar.zoneId == ToontownGlobals.SellbotHQFuture:
            return
        Street.Street.doEnterZone(self, newZoneId)

    def exit(self, visibilityFlag = 1):
        Street.Street.exit(self, visibilityFlag)
        messenger.send('exitSafeZone')
