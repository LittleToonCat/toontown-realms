from direct.directnotify.DirectNotifyGlobal import directNotify

from .DistributedMicroGameAI import DistributedMicroGameAI
from toontown.hood.ZoneUtil import isDynamicZone
from toontown.quest.Quests import TROLLEY_QUEST_ID
from toontown.suit import DistributedSellbotBossAI, DistributedSellbotArenaAI, DistributedCashbotBossAI,\
    DistributedLawbotBossAI, DistributedBossbotBossAI, DistributedLawbotArenaAI
from toontown.toonbase import ToontownGlobals, TTLocalizer
from toontown.instancedgames import DistributedPropHuntGameAI


class BossPartyManagerAI(DistributedMicroGameAI):
    notify = directNotify.newCategory('BossPartyManagerAI')
    bossCogDict = {ToontownGlobals.BossPartySellbotBoss: DistributedSellbotBossAI.DistributedSellbotBossAI,
                   ToontownGlobals.BossPartySellbotBossHardcore: DistributedSellbotBossAI.DistributedSellbotBossAI,
                   ToontownGlobals.BossPartySellbotBossStormSellbot: DistributedSellbotBossAI.DistributedSellbotBossAI,
                   ToontownGlobals.BossPartySellbotBossWinter: DistributedSellbotBossAI.DistributedSellbotBossAI,
                   ToontownGlobals.BossPartySellbotBossArena: DistributedSellbotArenaAI.DistributedSellbotArenaAI,
                   ToontownGlobals.BossPartyCashbotBoss: DistributedCashbotBossAI.DistributedCashbotBossAI,
                   ToontownGlobals.BossPartyCashbotBossHardcore: DistributedCashbotBossAI.DistributedCashbotBossAI,
                   ToontownGlobals.BossPartyLawbotBoss: DistributedLawbotBossAI.DistributedLawbotBossAI,
                   ToontownGlobals.BossPartyLawbotBossHardcore: DistributedLawbotBossAI.DistributedLawbotBossAI,
                   ToontownGlobals.BossPartyLawbotBossArena: DistributedLawbotArenaAI.DistributedLawbotArenaAI,
                   ToontownGlobals.BossPartyBossbotBoss: DistributedBossbotBossAI.DistributedBossbotBossAI,
                   ToontownGlobals.BossPartyBossbotBossHardcore: DistributedBossbotBossAI.DistributedBossbotBossAI,

                   ToontownGlobals.BossPartyPropHunt: DistributedPropHuntGameAI.DistributedPropHuntGameAI}
    bossPartyNoPromoCheck = (ToontownGlobals.BossPartySellbotBossStormSellbot,
                             ToontownGlobals.BossPartySellbotBossArena, ToontownGlobals.BossPartyLawbotBossArena,
                             ToontownGlobals.BossPartyPropHunt)
    bossPartyComingSoon = (ToontownGlobals.BossPartySellbotBossArena, ToontownGlobals.BossPartyPropHunt)

    def __init__(self, air):
        DistributedMicroGameAI.__init__(self, air)
        self._duration = ToontownGlobals.DefaultBossPartyDuration
        self._bossCog = ToontownGlobals.BossPartySellbotBoss
        self._hoster = 0
        self._previousHoster = 0
        self._toons = []
        self._toonIds = []
        self._invited = []
        self._denied = []

    def delete(self):
        DistributedMicroGameAI.delete(self)

    def getName(self):
        return TTLocalizer.BossPartyHeader

    def b_setBossCog(self, bossCog):
        self.d_setBossCog(bossCog)
        self.setBossCog(bossCog)

    def getBossCog(self):
        return self._bossCog

    def setBossCog(self, bossCog):
        self._bossCog = bossCog

    def d_setBossCog(self, bossCog):
        self.sendUpdate('setBossCog', [bossCog])

    def b_setHoster(self, hoster):
        self.d_setHoster(hoster)
        self.setHoster(hoster)

    def getHoster(self):
        return self._hoster

    def setHoster(self, hoster):
        self._hoster = hoster

        if hoster:
            av = self.air.doId2do.get(hoster)
            self._toons.append((hoster, av.getDNAString(), av.getHat(), av.getGlasses()))
            self._toonIds.append(hoster)
            self.sendUpdate('updateToons', [self._toons, False])

    def d_setHoster(self, hoster):
        self.sendUpdate('setHoster', [hoster])

    def getPreviousHoster(self):
        return self._previousHoster

    def getDenied(self):
        return self._denied

    def setPreviousHoster(self, previousHoster):
        self._previousHoster = previousHoster

    def setupRules(self, flag, avId=None):
        pass

    def isActive(self):
        return self.getCurrentOrNextState() != 'Off'

    def enterOff(self):
        # Clear timer
        self.sendUpdate('sendStartTime', [ToontownGlobals.MicroGameTimerOff])

        DistributedMicroGameAI.enterOff(self)

    def enterStart(self):
        DistributedMicroGameAI.enterStart(self)

    def enterDone(self):
        self._cleanupTasks()
        taskMgr.doMethodLater(0.1, self.b_setState, self.uniqueName('enterNextState'), extraArgs=['Off'])

        previousHoster = self.getPreviousHoster()

        # If our hoster is gone when the party is starting, disband it
        if self._hoster:
            hoster = self.air.doId2do.get(self._hoster)
            if not hoster:
                self.disbandParty(previousHoster)
                return
        else:
            self.disbandParty(previousHoster)
            return

        # Begin our Boss if we have Toons willing to go
        if self._toons:
            # Create our Boss Instance
            zoneId = self.createBossOffice([x[0] for x in self._toons])

            # Send the Toons to the Boss
            self.startParty(zoneId)

            # Clear out the Toons and hoster for our next party
            self._toons = []
            self._toonIds = []
            self.b_setHoster(0)

        self.partyLeft()
        self._invited = []
        self._denied = []

    def isHoster(self, avId):
        return avId == self.getHoster()

    def gotInvite(self):
        avId = self.air.getAvatarIdFromSender()
        if not avId:
            return

        av = self.air.doId2do.get(avId)
        if not av:
            return

        if self.toonInParty(avId) and avId != self._hoster:
            self.notify.info('toon with avId of {} tried to confirm they were invited to a boss party but were already '
                             'subscribed to it!'.format(avId))
            return

        if av in self._invited:
            self.notify.info('toon with avId of {} tried to confirm they were invited to a boss party but was already '
                             'invited!'.format(avId))
            return

        if isDynamicZone(av.zoneId):
            self.notify.info('toon with avId of {} tried to confirm they were invited to a boss party but was in a '
                             'dynamic zone!'.format(avId))
            return

        if not self.hasPromotion(av, self._bossCog):
            self.notify.info('toon with avId of {} tried to confirm they were invited to a boss party but were not '
                             'ready for promotion!'.format(avId))
            return

        # The Toon got the invite successfully, so lock them and add to the invited list
        self._invited.append(av)
        if avId == self._hoster:
            av.b_setLocked(True, ToontownGlobals.LockedStateCagedExemption)

    def requestLeave(self):
        avId = self.air.getAvatarIdFromSender()
        if not avId:
            return

        av = self.air.doId2do.get(avId)
        if not av:
            return

        if self.isHoster(avId):
            self.disband(av)
        else:
            self.leaveParty(av)

    def disband(self, av):
        avId = av.doId

        # Run a bunch of checks to make sure this is a valid disband request
        if avId != self._hoster:
            self.notify.info('toon with avId of {} tried to disband a boss party but is not the owner!'.format(avId))
            return

        if not self.toonInParty(avId):
            self.notify.info('toon with avId of {} tried to disband a boss party but is not a member!!'.format(avId))
            return

        if av and isDynamicZone(av.zoneId):
            self.notify.info('toon with avId of {} tried to disband a boss party but was in a dynamic zone!'.format(
                avId))
            return

        # Disband the boss party
        self.setPreviousHoster(self.getHoster())
        self.b_setHoster(0)
        self.disbandParty(self.getPreviousHoster())

    def disbandParty(self, hosterAvId):
        for av in self._invited:
            if av:
                avId = av.getDoId()
                if avId in self._toonIds:
                    av.b_setLocked(False)
                    self.sendUpdateToAvatarId(avId, 'disbandParty', [hosterAvId])
                else:
                    av.d_removeNotificationsMatching("party_invite")
                avExitEvent = self.air.getAvatarExitEvent(avId)
                self.ignore(avExitEvent)
        self.setPreviousHoster(0)
        self._toons = []
        self._toonIds = []
        self._invited = []
        self._denied = []
        if self.isActive() and not taskMgr.hasTaskNamed(self.uniqueName('enterNextState')):
            self.b_setState('Off')
            self._startTimestamp = None

    def startParty(self, zoneId):
        for avId, _, _, _ in self._toons:
            if avId:
                av = self.air.doId2do.get(avId)
                if av:
                    av.b_setLocked(False)
                    if av in self._invited:
                        self._invited.remove(av)
                    self.sendUpdateToAvatarId(avId, 'startParty', [zoneId])
                    avExitEvent = self.air.getAvatarExitEvent(avId)
                    self.ignore(avExitEvent)

    def partyLeft(self):
        for av in self._invited:
            if av:
                avId = av.getDoId()
                av.d_removeNotificationsMatching("party_invite")
                avExitEvent = self.air.getAvatarExitEvent(avId)
                self.ignore(avExitEvent)

    def joinParty(self):
        avId = self.air.getAvatarIdFromSender()
        if not avId:
            return

        av = self.air.doId2do.get(avId)
        if not av:
            return

        if self.toonInParty(avId):
            self.notify.info('toon with avId of {} tried to join a boss party but was already subscribed to it!'
                             .format(avId))
            return

        if isDynamicZone(av.zoneId):
            self.notify.info('toon with avId of {} tried to join a boss party but was in a dynamic zone!'.format(avId))
            return

        if av not in self._invited:
            self.notify.info('toon with avId of {} tried to join a boss party but was never invited!'.format(avId))
            return

        limit = ToontownGlobals.BossPartyPlayerLimits.get(self._bossCog)
        if len(self._toons) >= limit:
            self.sendUpdateToAvatarId(avId, 'partyFull', [])
            return

        av.b_setLocked(True, ToontownGlobals.LockedStateCagedExemption)

        self._toons.append((avId, av.getDNAString(), av.getHat(), av.getGlasses()))
        self._toonIds.append(avId)
        ready = False
        if len(self._toons) == len(self._invited):
            ready = True
        self.sendUpdate('updateToons', [self._toons, ready])

        avExitEvent = self.air.getAvatarExitEvent(avId)
        self.acceptOnce(avExitEvent, self.handleAvatarExited, extraArgs=[av])

        # If this Toon makes our party full, remove all other Toons from the invite list
        if len(self._toons) == limit:
            for av in self._invited[:]:
                if av.getDoId() not in self._toons and av in self._invited:
                    av.d_removeNotificationsMatching("party_invite")
                    if av in self._invited:
                        self._invited.remove(av)

    def handleAvatarExited(self, av):
        DistributedMicroGameAI.handleAvatarExited(self, av)
        if av in self._invited:
            self._invited.remove(av)

        if self.toonInParty(av):
            self._toons.remove(self.toonInParty(av))

        avId = av.getDoId()
        if self.isHoster(avId):
            self.disband(av)
        else:
            self.leaveParty(av)

    def denyParty(self):
        avId = self.air.getAvatarIdFromSender()
        if not avId:
            return

        av = self.air.doId2do.get(avId)
        if not av:
            return

        if self.toonInParty(avId):
            self.notify.info('toon with avId of {} tried to deny a boss party invite but was already subscribed to it!'
                             .format(avId))
            return

        if isDynamicZone(av.zoneId):
            self.notify.info('toon with avId of {} tried to deny a boss party invite but was in a dynamic zone!'
                             .format(avId))
            return

        if av not in self._invited:
            self.notify.info('toon with avId of {} tried to deny a boss party invite but was never invited!'
                             .format(avId))
            return

        if av in self._invited:
            self._invited.remove(av)
        self._denied.append(av)
        ready = False
        if len(self._toons) == len(self._invited):
            ready = True
        self.sendUpdate('updateToons', [self._toons, ready])

    def leaveParty(self, av):
        avId = av.doId

        if not self.toonInParty(avId):
            self.notify.info('toon with avId of {} tried to leave a boss party but is not a member!!'.format(avId))
            return

        if av and isDynamicZone(av.zoneId):
            self.notify.info('toon with avId of {} tried to leave a boss party but was in a dynamic zone!'.format(avId))
            return

        av.b_setLocked(False)
        for toon in self._toons:
            if toon[0] == avId:
                self._toons.remove(toon)
        if av in self._invited:
            self._invited.remove(av)
        ready = False
        if len(self._toons) == len(self._invited):
            ready = True
        self.sendUpdate('updateToons', [self._toons, ready])

        avExitEvent = self.air.getAvatarExitEvent(avId)
        self.ignore(avExitEvent)

    def goNow(self):
        avId = self.air.getAvatarIdFromSender()
        if not avId:
            return

        av = self.air.doId2do.get(avId)
        if not av:
            return

        # Run a bunch of checks to make sure this is a valid disband request
        if avId != self._hoster:
            self.notify.info(
                'toon with avId of {} tried to ready a boss party but is not the owner!'.format(avId))
            return

        if not self.toonInParty(avId):
            self.notify.info(
                'toon with avId of {} tried to ready a boss party but is not a member!'.format(avId))
            return

        if isDynamicZone(av.zoneId):
            self.notify.info(
                'toon with avId of {} tried to ready a boss party but was in a dynamic zone!'.format(avId))
            return

        self.b_setState('Done')

    def createBossParty(self, bossCog):
        avId = self.air.getAvatarIdFromSender()
        if not avId:
            return

        av = self.air.doId2do.get(avId)
        if not av:
            return

        if not self.isValidBossParty(bossCog):
            return

        microGameMgr = self.air.microGameMgr
        if microGameMgr:
            microGame, isActive = microGameMgr.getActiveMicroGame(av.zoneId)
            if isActive:
                av.d_setSystemMessage(0, TTLocalizer.BossPartyCreateError + TTLocalizer.BossPartyErrorMicroGame)
                return

        if self.isActive():
            av.d_setSystemMessage(0, TTLocalizer.BossPartyCreateError + TTLocalizer.BossPartyErrorBossParty)
            return

        if isDynamicZone(av.zoneId):
            av.d_setSystemMessage(0, TTLocalizer.BossPartyCreateError + TTLocalizer.BossPartyErrorDynamicZone)
            return

        if not self.hasPromotion(av, bossCog):
            av.d_setSystemMessage(0, TTLocalizer.BossPartyCreateError + TTLocalizer.BossPartyErrorNoPromotion)
            return

        self.b_setBossCog(bossCog)
        self.b_setHoster(avId)
        self.b_setState('Start')

        avExitEvent = self.air.getAvatarExitEvent(avId)
        self.acceptOnce(avExitEvent, self.handleAvatarExited, extraArgs=[av])

    def toggleBoss(self, bossCog):
        avId = self.air.getAvatarIdFromSender()
        if not avId:
            return

        av = self.air.doId2do.get(avId)
        if not av:
            return

        if not self.isHoster(avId):
            return

        if not self.isValidBossParty(bossCog):
            return

        if not self.hasPromotion(av, bossCog):
            av.d_setSystemMessage(0, TTLocalizer.BossPartyToggleError + TTLocalizer.BossPartyErrorNoPromotion)
            return

        # Looks like we can change the Boss perfectly fine
        self.b_setBossCog(bossCog)

        # Make sure to update that across our clients
        self.sendUpdate('updateBossCog')

    def __isNPCFAComplete(self, av):
        """A copy of the checks ran in NPCForceAcknowledge. We run it here so we can determine if the toon will actually
        arrive at the boss since the toon is added to the boss before the teleport occurs."""
        questHistory = av.getQuestHistory()
        return questHistory not in ([], [1000], [101, 110]) or len(av.quests) != 1 or av.quests[0][0] != TROLLEY_QUEST_ID

    def createBossOffice(self, avIdList):
        # TEMPORARILY OVERRIDDEN TO FORCE PROP HUNT, WE ARE REWRITING THIS ANYWAY WITH NEW GUI
        bossZone = self.air.allocateZone()
        self.notify.info('Creating Instance: %s' % bossZone)
        if self._bossCog == ToontownGlobals.BossPartyPropHunt:
            bossCog = DistributedPropHuntGameAI.DistributedPropHuntGameAI(self.air)
            for avId in avIdList:
                if avId:
                    av = self.air.doId2do.get(avId)
                    if av and self.__isNPCFAComplete(av):
                        bossCog.addToon(avId)

            bossCog.generateWithRequired(bossZone)
            self.acceptOnce(bossCog.uniqueName('PartyGameDone'), self.destroyBossOffice, extraArgs=[bossCog])
            bossCog.b_setState('WaitForToons')
            return bossZone

        else:
            bossCog = self.bossCogDict[self._bossCog]
            bossCog = bossCog(self.air)

            for avId in avIdList:
                if avId:
                    av = self.air.doId2do.get(avId)
                    if av and self.__isNPCFAComplete(av):
                        bossCog.addToon(avId)

            bossCog.setMode(self._bossCog)
            bossCog.generateWithRequired(bossZone)
            self.acceptOnce(bossCog.uniqueName('BossDone'), self.destroyBossOffice, extraArgs=[bossCog])
            bossCog.b_setState('WaitForToons')
            return bossZone

    def destroyBossOffice(self, bossCog):
        bossZone = bossCog.zoneId
        self.notify.info('Destroying Instance: %s' % bossZone)
        bossCog.requestDelete()
        self.air.deallocateZone(bossZone)

    def getBossPartyCategory(self, index):
        for category, modes in ToontownGlobals.BossPartyCategories.items():
            if index in modes:
                return category

    def getAllBossParties(self):
        bossParties = []

        for mode in ToontownGlobals.BossPartyCategories:
            bossParties.extend(ToontownGlobals.BossPartyCategories[mode])

        return bossParties

    def isValidBossParty(self, index):
        return index in self.getAllBossParties()

    def hasPromotion(self, av, index):
        # Sometimes we don't want a promotion for the
        # just for fun stuff; example: LawbotArena
        if index in self.bossPartyNoPromoCheck:
            return True
        category = self.getBossPartyCategory(index)
        return av.readyForPromotion(ToontownGlobals.BossPartyPromotionInfo[category])

    def toonInParty(self, avId):
        """
        Convenience function to see if a toon is in the party. If so, will return the entry, if not, will return false
        :param avId: Avatar ID
        :return: If True: Toon tuple in party; if False: False
        """
        for toon in self._toons:
            if toon[0] == avId:
                return toon
        return False