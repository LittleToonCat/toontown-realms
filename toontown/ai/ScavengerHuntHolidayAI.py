import time
from direct.directnotify import DirectNotifyGlobal

from toontown.toonbase import ToontownGlobals

from .HolidayBaseAI import HolidayBaseAI
from .DistributedTrickOrTreatTargetAI import DistributedTrickOrTreatTargetAI
from .DistributedWinterCarolingTargetAI import DistributedWinterCarolingTargetAI

from copy import deepcopy


TrickOrTreatTargets = [
    2649, # All Fun And Games Shop (Silly Street)
    1834, # Rudderly Ridiculous! (Lighthouse Lane)
    5620, # Rake It Inn (Elm Street)
    4835, # Ursatz for Really Kool Katz! (Tenor Terrace)
    3707, # Snowplace Like Home (Sleet Street)
    9619, # Relax To The Max (Lullaby Lane)
]

CarolingTargets = [
    2659, # Joy Buzzers to the World (Silly Street)
    1707, # Gifts With a Porpoise (Seaweed Street)
    5626, # Pine Needle Crafts (Elm Street)
    4614, # Shave and a Haircut for a Song (Alto Avenue)
    3828, # Snowman's Land (Polar Place)
    9720, # Talking In Your Sleep Voice Training (Pajama Place)
]

RewardMoney = ToontownGlobals.TOT_REWARD_JELLYBEAN_AMOUNT

EffectDuration = 10080 # One week


class ScavengerHuntHolidayAI(HolidayBaseAI):
    notify = DirectNotifyGlobal.directNotify.newCategory("ScavengerHuntHolidayAI")

    def __init__(self, air, holidayId, holidayYear):
        HolidayBaseAI.__init__(self, air, holidayId)
        self.targets = []
        self.targetZones = []
        self.holidayYear = holidayYear

    def start(self):
        HolidayBaseAI.start(self)
        if self.holidayId in (ToontownGlobals.TRICK_OR_TREAT, ToontownGlobals.SPOOKY_TRICK_OR_TREAT):
            self.targetZones = TrickOrTreatTargets
            targetCtl = DistributedTrickOrTreatTargetAI
        elif self.holidayId in (ToontownGlobals.WINTER_CAROLING, ToontownGlobals.WACKY_WINTER_CAROLING):
            self.targetZones = CarolingTargets
            targetCtl = DistributedWinterCarolingTargetAI
        else:
            self.notify.warning("Don't know which Hunt target to use for holiday {}!".format(self.holidayId))
            return

        for zoneId in self.targetZones:
            targetMgr = targetCtl(self.air, self)
            targetMgr.generateWithRequired(zoneId)
            self.targets.append(targetMgr)

    def attemptScavengerHunt(self, toon, zoneId):
        ourYear = self.holidayYear
        data = toon.getScavengerProgress(pickled=False)[self.holidayId]
        self.notify.debug('Data acquired for Toon {}({}): {}'.format(toon.getName(), toon.doId, data))
        qYear, qGoals = data[0], deepcopy(data[1])
        if qYear != ourYear:
            # reset qGuals if progress year isn't the same as ours
            qGoals = list()
            self.notify.debug('AvId {}: last progress year was {}; resetting progress'.format(toon.doId, qYear))
        if zoneId not in qGoals:
            self.notify.debug('AvId {}: Adding zone {} to goals.'.format(toon.doId, zoneId))
            toon.addMoney(RewardMoney)
            if self.holidayId in [ToontownGlobals.TRICK_OR_TREAT, ToontownGlobals.SPOOKY_TRICK_OR_TREAT]:
                toon.sendUpdate('trickOrTreatTargetMet', [RewardMoney])
            elif self.holidayId in [ToontownGlobals.WINTER_CAROLING, ToontownGlobals.WACKY_WINTER_CAROLING]:
                toon.sendUpdate('winterCarolingTargetMet', [RewardMoney])

            qGoals.append(zoneId)
            toon.b_setScavengerProgress(self.holidayId, ourYear, deepcopy(qGoals))

        if set(self.targetZones) == set(qGoals):
            self.notify.debug('AvId {}: Scavenger hunt complete! (Re)assigning cheesy effect!'.format(toon.doId))
            expireTime = int(time.time() / 60 + 0.5) + EffectDuration
            if self.holidayId in (ToontownGlobals.TRICK_OR_TREAT, ToontownGlobals.SPOOKY_TRICK_OR_TREAT):
                toon.b_setCheesyEffect(ToontownGlobals.CEPumpkin, 0, expireTime)
            elif self.holidayId in (ToontownGlobals.WINTER_CAROLING, ToontownGlobals.WACKY_WINTER_CAROLING):
                toon.b_setCheesyEffect(ToontownGlobals.CESnowMan, 0, expireTime)

    def stop(self):
        HolidayBaseAI.stop(self)

        for targetMgr in self.targets:
            targetMgr.requestDelete()
        self.targets = []
