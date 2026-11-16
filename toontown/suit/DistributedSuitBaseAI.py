from typing import Any, Dict, Optional
from otp.ai.AIBaseGlobal import *
from otp.avatar import DistributedAvatarAI
from toontown.battle.StatusEffect import StatusEffect
from otp.otpbase import OTPLocalizer
from . import CogFlags, SuitPlannerBase, SuitBase, SuitDNA
from direct.directnotify import DirectNotifyGlobal
from direct.distributed.ClockDelta import globalClockDelta
from toontown.battle.BattleBase import PIE_DMG_DICT
from random import randint, choice

CANNON_IVAL_DUR = 7.5
EXPLODE_IVAL_DUR = 8.5

class DistributedSuitBaseAI(DistributedAvatarAI.DistributedAvatarAI, SuitBase.SuitBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedSuitBaseAI')

    def __init__(self, air, suitPlanner):
        DistributedAvatarAI.DistributedAvatarAI.__init__(self, air)
        SuitBase.SuitBase.__init__(self)
        self.sp = suitPlanner
        self.maxHP = 10
        self.currHP = 10
        self.zoneId = 0
        self.dna = None
        self.virtual = 0
        self.skeleRevives = 0
        self.maxSkeleRevives = 0
        self.topBrass: bool = False
        self.reviveTrack: Optional[int] = None
        self.buildingHeight = None

    def delete(self):
        if hasattr(self, 'doId'):
            self.removeAllTasks()
        self.sp = None
        del self.dna
        DistributedAvatarAI.DistributedAvatarAI.delete(self)

    def requestRemoval(self):
        if self.sp != None:
            self.sp.removeSuit(self)
        else:
            self.requestDelete()

    def setLevel(self, lvl=None):
        if not lvl:
            lvl = 1
        self.level = lvl - 1
        self.notify.debug(f'Assigning level {self.level}')
        if hasattr(self, 'doId'):
            self.d_setLevelDist(self.level)

        hp = self.air.datapackMgr.getCogHP(self.dna.name, self.level + 1)
        self.setMaxHP(hp)
        self.currHP = hp

        # temporary possible None return type
        # we want this to be bool only
        # BUT we don't have support for default values yet, and we need to keep in mind
        # we want support for multiple attributes in one flag, and need to validate ALL the attributes when the flag is processed.
        topBrass: bool | None = self.air.datapackMgr.getFlag(self.dna.name, CogFlags.FL_TOP_BRASS)
        if topBrass is not None:
            self.setTopBrass(topBrass)

        statusEffectList = self.air.datapackMgr.getStatusEffectsList(self.dna.name)
        for effectInfo in statusEffectList:
            effectName: str = effectInfo[0]
            attributes: Dict[str, Any] = effectInfo[1]
            statusEffect = StatusEffect(effectName, rounds = attributes.get('rounds', -1))
            self.addStatusEffect(statusEffect)

    def getLevelDist(self):
        return self.getLevel()

    def d_setLevelDist(self, level):
        self.sendUpdate('setLevelDist', [level])

    def setupSuitDNA(self, level, type, track, extraSuit=None):
        dna = SuitDNA.SuitDNA()
        if not extraSuit:
            dna.newSuitRandom(type, track)
        else:
            dna.newSuit(extraSuit)
        self.dna = dna
        self.track = track
        self.setLevel(level)

    def getDNAString(self):
        if self.dna:
            return self.dna.makeNetString()
        else:
            self.notify.debug(f'No dna has been created for suit {self.getDoId()}!')
            return ''

    def b_setBrushOff(self, index):
        self.setBrushOff(index)
        self.d_setBrushOff(index)

    def d_setBrushOff(self, index):
        self.sendUpdate('setBrushOff', [index])

    def setBrushOff(self, index):
        pass

    def d_denyBattle(self, toonId):
        self.sendUpdateToAvatarId(toonId, 'denyBattle', [])

    def b_setSkeleRevives(self, num):
        if num == None:
            num = 0
        self.setSkeleRevives(num)
        self.d_setSkeleRevives(self.getSkeleRevives())

    def d_setSkeleRevives(self, num):
        self.sendUpdate('setSkeleRevives', [num])

    def getSkeleRevives(self):
        return self.skeleRevives

    def setSkeleRevives(self, num):
        if num == None:
            num = 0
        self.skeleRevives = num
        if num > self.maxSkeleRevives:
            self.maxSkeleRevives = num

    def getMaxSkeleRevives(self):
        return self.maxSkeleRevives

    def useSkeleRevive(self, track = None):
        self.skeleRevives -= 1
        self.b_setHP(self.maxHP)
        self.reviveTrack = track

    def clearReviveFlag(self):
        self.reviveTrack = None

    def getReviveTrack(self) -> Optional[int]:
        return self.reviveTrack

    def setTopBrass(self, topBrass: bool):
        self.topBrass = topBrass

    def getTopBrass(self) -> bool:
        return self.topBrass

    def getHP(self):
        return self.currHP

    def setHP(self, hp):
        self.currHP = hp

    def b_setHP(self, hp):
        self.setHP(hp)
        self.d_setHP(hp)

    def d_setHP(self, hp):
        self.sendUpdate('setHP', [hp])

    def setMaxHP(self, maxHP):
        self.maxHP = maxHP

    def getMaxHP(self):
        return self.maxHP

    def releaseControl(self):
        return None

    def getDeathEvent(self):
        return f'cogDead-{self.doId}'

    def resume(self):
        self.notify.debug(f'resume, hp={self.currHP}')
        if self.currHP <= 0:
            messenger.send(self.getDeathEvent())
            self.requestRemoval()

    def prepareToJoinBattle(self):
        pass

    def b_setSkelecog(self, flag):
        self.setSkelecog(flag)
        self.d_setSkelecog(flag)

    def setSkelecog(self, flag):
        SuitBase.SuitBase.setSkelecog(self, flag)

    def d_setSkelecog(self, flag):
        self.sendUpdate('setSkelecog', [flag])

    def isForeman(self):
        return 0

    def isSupervisor(self):
        return 0

    def b_setVirtual(self, isVirtual):
        self.setVirtual(isVirtual)
        self.d_setVirtual(isVirtual)

    def d_setVirtual(self, isVirtual):
        self.sendUpdate('setVirtual', [isVirtual])

    def setVirtual(self, isVirtual):
        self.virtual = isVirtual

    def getVirtual(self):
        return self.virtual

    def isVirtual(self):
        return self.getVirtual()

    def useReviveTask(self, task):
        self.useSkeleRevive()

    def deleteCogTask(self, task):
        self.requestRemoval()

    def handleHit(self):
        """
        Calculates the damage dealt, which action prop was thrown,
        which death animation to play, and network timestamp 
        for the death animation startTime.
        """

        # Get the toon who threw the action prop
        toonId = self.air.getAvatarIdFromSender()
        toon = self.air.doId2do.get(toonId)
        if toon is None:
            return

        # Get our timestamp
        timestamp = globalClockDelta.getRealNetworkTime()

        # Calculate our damage
        if toon.getInstaKill() or toon.pieType == 9:
            dmg = self.getHP()
        else:
            dmg = PIE_DMG_DICT.get(toon.pieType)
        self.b_setHP(self.getHP() - dmg)

        # The cog is dead!
        if self.getHP() <= 0:

            # The toon threw a pink slip. Fire the cog!
            if toon.pieType == 9:
                self.sendUpdate('fireCog', [timestamp])
                self.doMethodLater(CANNON_IVAL_DUR, self.deleteCogTask, self.uniqueName('delCogTask'))
                self.b_setPathState(5)
            else:
                # The cog was a v2.0. Make it a skelecog!
                if self.skeleRevives:
                    self.sendUpdate('doRevive', [dmg, timestamp])
                    self.doMethodLater(0, self.useReviveTask, self.uniqueName('reviveTask'))
                else:
                    # Just a normal cog. Kill it.
                    self.sendUpdate('doExplode', [dmg, timestamp])
                    self.doMethodLater(EXPLODE_IVAL_DUR, self.deleteCogTask, self.uniqueName('delCogTask'))
                    self.b_setPathState(5)
        else:
            # The cog isn't dead yet. Damage the suit!
            roll = randint(0, 2)
            self.sendUpdate('damageSuit', [dmg, roll])

