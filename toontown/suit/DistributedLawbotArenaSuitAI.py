from direct.distributed.ClockDelta import *
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State

from otp.ai.AIBaseGlobal import *

from toontown.suit import SuitDNA
from toontown.toonbase import ToontownGlobals

from . import DistributedSuitBaseAI

import random


class DistributedLawbotArenaSuitAI(DistributedSuitBaseAI.DistributedSuitBaseAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedLawbotArenaSuitAI')

    def __init__(self, air, suitPlanner, boss, team):
        DistributedSuitBaseAI.DistributedSuitBaseAI.__init__(self, air, suitPlanner)

        self.stunned = False
        self.timeToRelease = 3.15
        self.timeProsecuteStarted = 0
        self.boss = boss
        self.team = team
        self.mode = ToontownGlobals.LawbotArenaProsecutingBoth
        self.bonus = False

        # Lawyer FSM
        self.fsm = ClassicFSM.ClassicFSM('DistributedLawbotArenaSuitAI',
                                         [State.State('Off', self.enterOff, self.exitOff, ['neutral']),
                                          State.State('neutral', self.enterNeutral, self.exitNeutral, ['PreThrowProsecute', 'PreThrowAttack', 'Stunned']),
                                          State.State('PreThrowProsecute', self.enterPreThrowProsecute, self.exitPreThrowProsecute, ['PostThrowProsecute', 'neutral', 'Stunned']),
                                          State.State('PostThrowProsecute', self.enterPostThrowProsecute, self.exitPostThrowProsecute, ['neutral', 'Stunned']),
                                          State.State('PreThrowAttack', self.enterPreThrowAttack, self.exitPreThrowAttack, ['PostThrowAttack', 'neutral', 'Stunned']),
                                          State.State('PostThrowAttack', self.enterPostThrowAttack, self.exitPostThrowAttack, ['neutral', 'Stunned']),
                                          State.State('Stunned', self.enterStunned, self.exitStunned, ['neutral'])],
                                         'Off', 'Off')
        self.fsm.enterInitialState()

    def delete(self):
        self.notify.debug('delete %s' % self.doId)
        self.ignoreAll()
        DistributedSuitBaseAI.DistributedSuitBaseAI.delete(self)

        self.notify.debug('setting self.boss to None')
        self.boss = None

        taskName = self.uniqueName('ProsecutionHealsBoss')
        if taskMgr.hasTaskNamed(taskName):
            self.notify.debug('still has task %s' % taskName)
        taskMgr.remove(taskName)

        taskName = self.uniqueName('unstun')
        if taskMgr.hasTaskNamed(taskName):
            self.notify.debug('still has task %s' % taskName)
        taskMgr.remove(taskName)

        self.fsm = None
        return

    def getPosHpr(self):
        return (self.getX(), self.getY(), self.getZ(), self.getH(), self.getP(), self.getR())

    def getConfrontPosHpr(self):
        return (self.confrontPos, self.confrontHpr)

    def getTeam(self):
        return self.team

    def b_setMode(self, mode):
        self.setMode(mode)
        self.d_setMode(mode)

    def d_setMode(self, mode):
        self.sendUpdate('setMode', [mode])

    def setMode(self, mode):
        self.mode = mode

    def getMode(self):
        return self.mode

    def setHP(self, hp):
        self.currHP = hp

    def setLevel(self, lvl=None):
        self.level = lvl# - attributes['level'] - 1
        if hasattr(self, 'doId'):
            self.d_setLevelDist(self.level)

    def doNextAttack(self, lawbotBoss):
        # If we're stunned, don't do anything
        if self.stunned:
            return

        mode = self.getMode()
        if mode == ToontownGlobals.LawbotArenaProsecutingBoth:
            # The chance of attacking vs prosecuting
            chanceToDoAttack = ToontownGlobals.LawbotBossLawyerChanceToAttack
            action = random.randrange(1, 101)

            # Prosecute, aka hit the pan
            if action > chanceToDoAttack:
                self.doProsecutePan()
            # Attack, aka hit a Toon
            else:
                self.doProsecuteToon(lawbotBoss)
        elif mode == ToontownGlobals.LawbotArenaProsecutingToons:
            self.doProsecuteToon(lawbotBoss)
        elif mode == ToontownGlobals.LawbotArenaProsecutingBoss:
            self.doProsecutePan()

    def doProsecutePan(self):
        self.timeProsecuteStarted = globalClockDelta.getRealNetworkTime()
        self.d_doProsecute()
        taskName = self.uniqueName('ProsecutionHealsBoss')
        duration = 5.65
        taskMgr.doMethodLater(duration, self.__prosecutionHit, taskName)

    def doProsecuteToon(self, lawbotBoss):
        # If there aren't any Toons, prosecute the pan instead
        if not lawbotBoss.involvedToons:
            self.doProsecutePan()
            return

        # Add some check later on so that the lawyers only target the opposing side's Toons
        team = self.getTeam()
        if team == ToontownGlobals.BossArenaTeamA:
            enemyTeam = self.boss.toonsB
        elif team == ToontownGlobals.BossArenaTeamB:
            enemyTeam = self.boss.toonsA
        else:
            self.doProsecutePan()
            return

        if not enemyTeam:
            self.doProsecutePan()
            return

        # Grab a random Toon to attack
        toonToAttackId = random.choice(enemyTeam)
        toon = self.air.doId2do.get(toonToAttackId)

        # If for whatever reason our target doesn't exist, prosecute instead
        if not toon:
            self.doProsecutePan()
            return

        # Get the position of the attack, and execute it
        toonPos = toon.getPos()
        z2 = toonPos[2] + 1.3
        toonPos = Point3(toonPos.getX(), toonPos.getY(), 0)
        lawyerPos = self.getPos()
        lawyerPos = Point3(self.getPos().getX(), self.getPos().getY(), 0)
        dirVector = toonPos - lawyerPos
        dirVector.normalize()
        dirVector *= 200
        destPos = Point3(lawyerPos[0] + dirVector[0], lawyerPos[1] + dirVector[1], lawyerPos[2] + dirVector[2] + 1.3)
        self.d_doAttack(lawyerPos[0], lawyerPos[1], lawyerPos[2], destPos[0], destPos[1], destPos[2])

    def __prosecutionHit(self, extraArg):
        # If our prosecution hasn't been interrupted, then "heal" the Boss
        if not self.boss:
            return

        # A lawyer's damage is equal its level
        damage = self.getLevel() + 1

        team = self.getTeam()
        if team == ToontownGlobals.BossArenaTeamB:
            self.boss.healBoss(damage, True)
        elif team == ToontownGlobals.BossArenaTeamA:
            self.boss.hitBoss(damage, True)

    def d_doProsecute(self):
        self.sendUpdate('doProsecute', [])

    def d_doAttack(self, x1, y1, z1, x2, y2, z2):
        self.sendUpdate('doAttack', [x1, y1, z1, x2, y2, z2])

    def hitByToon(self):
        toonId = self.air.getAvatarIdFromSender()

        # If we're on the same team then add to the lawyer's EXP
        if self.getTeam() == self.boss.getTeam(toonId):
            # Give the lawyer a predetermined amount of EXP, but double it if we have a bonus state going on
            exp = ToontownGlobals.LawbotArenaLawyerExp

            # If sudden death is active, increase the amount of exp given to a lawyer
            exp *= self.boss.suddenDealthMultiplier

            hp = self.getHP() + exp
            maxHp = self.getMaxHp()
            # If our "exp" is equal to or greater than our max "exp", promote the lawyer
            if hp >= maxHp:
                level = self.getLevel() + 1
                # Max levels that lawyers can be.
                maxLevel = 40
                # We're already level 12, so we cannot level up any higher
                if level > maxLevel:
                    if self.getHP() < maxHp:
                        self.b_setHP(maxHp)
                    return
                # If we havent yet surpassed out suitType's level, just level us up normally
                elif level <= maxLevel:
                    self.setLevel(level)
                hp = 0
                maxHp = (level + 2) * (level + 3)
                self.b_setMaxHp(maxHp)
            self.b_setHP(hp)
            return

        if not self.stunned:
            curTime = globalClockDelta.getRealNetworkTime()
            deltaTime = curTime - self.timeProsecuteStarted
            deltaTime /= 100.0
            self.notify.debug('deltaTime = %f, curTime=%f, prosecuteStarted=%f' % (deltaTime, curTime, self.timeProsecuteStarted))

            # We were stunned in the middle of a prosecution, so cancel it
            if deltaTime < self.timeToRelease:
                taskName = self.uniqueName('ProsecutionHealsBoss')
                taskMgr.remove(taskName)

            # Display the stun on the client and set stun flag to true
            self.sendUpdate('doStun', [])
            self.setStun(True)

            # Default stun duration
            duration = ToontownGlobals.LawbotArenaLawyerStunTime

            # Unstun Task
            taskName = self.uniqueName('unstun')
            taskMgr.doMethodLater(duration, self.unStun, taskName)

            # Check to see if enough lawyers have been stunned to activate a bonus state
            if self.boss:
                self.boss.checkForBonusState()

    def setStun(self, val):
        self.stunned = val

    def unStun(self, taskName):
        self.setStun(False)

    def enterPreThrowProsecute(self):
        pass

    def exitPreThrowProsecute(self):
        pass

    def enterPostThrowProsecute(self):
        pass

    def exitPostThrowProsecute(self):
        pass

    def enterPreThrowAttack(self):
        pass

    def exitPreThrowAttack(self):
        pass

    def enterPostThrowAttack(self):
        pass

    def exitPostThrowAttack(self):
        pass

    def enterStunned(self):
        pass

    def exitStunned(self):
        pass

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    def enterNeutral(self):
        pass

    def exitNeutral(self):
        pass
