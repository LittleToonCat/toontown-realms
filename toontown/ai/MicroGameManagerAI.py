from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.showbase.DirectObject import DirectObject
from .MicroGameManagerImports import *
from toontown.hood.ZoneUtil import getCanonicalBranchZone


class MicroGameManagerAI(DirectObject):
    notify = directNotify.newCategory('MicroGameManagerAI')
    microGameTypes = [DistributedPieBlitzAI, DistributedHideAndSeekAI]

    def __init__(self, air):
        DirectObject.__init__(self)
        self.microGames = {}
        self.air = air

    def startMicroGame(self, zoneId, gameType):
        microGame, isActive = self.getActiveMicroGame(zoneId)
        if isActive:
            self.notify.warning('Micro game already active in zone %d: %s!' % (zoneId, microGame.getName()))
            return
        zoneId = getCanonicalBranchZone(zoneId)
        self.air.writeServerEvent('micro-game', zoneId=zoneId, info='A Micro Game was started in this zone.')
        self.microGames[zoneId] = self.microGameTypes[gameType](self.air)
        self.microGames[zoneId].generateWithRequired(zoneId)
        return self.microGames[zoneId]

    def getActiveMicroGame(self, zoneId):
        zoneId = getCanonicalBranchZone(zoneId)
        microGame = self.microGames.get(zoneId)
        return microGame, microGame is not None and microGame.isActive()

    def toonLeaveOldZone(self, doId, zoneId):
        try:
            zoneId = getCanonicalBranchZone(zoneId)
        except TypeError:
            # This case only happens while the toon is logging in
            return
        microGame = self.microGames.get(zoneId)
        av = self.air.doId2do.get(doId)
        if microGame and av:
            microGame.handleAvatarExited(av)

    def toonSetNewZone(self, doId, zoneId):
        try:
            zoneId = getCanonicalBranchZone(zoneId)
        except TypeError:
            # This case only happens while the toon is logging in
            return
        microGame = self.microGames.get(zoneId)
        av = self.air.doId2do.get(doId)
        if microGame and av:
            microGame.handleAvatarEntered(av)
