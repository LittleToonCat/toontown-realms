from direct.directnotify import DirectNotifyGlobal
from direct.distributed.ClockDelta import *
from direct.fsm import FSM

from otp.ai.AIBaseGlobal import *

from toontown.battle import BattleExperienceAI
from toontown.coghq import DistributedLawbotBossGavelAI
from toontown.suit import DistributedLawbotArenaSuitAI
from toontown.toonbase import ToontownGlobals, TTLocalizer, ToontownBattleGlobals

from . import SuitDNA, DistributedBossCogAI

import random

# This list attempts to get at least a Toon from every playground.
# WITNESS TOON A, WITNESS TOON (B)
NPCToonPairs = [
  # Flippy, Lil Oldman
  (2001, 3112),
  # Clerk Clark, Clerk Clara
  (2006, 2011),
  # Clerk Will, Sheila Squid, Atty
  (1001, 1115),
  # Judge McIntosh, Samantha Spade
  (5311, 5208),
  # Julius Wheezer, Detective Dirge
  (4230, 4212),
  # Gus Gooseburger, Chicken Boy
  (3106, 3110),
  # Shorty Fuse, Lawful Linda
  (2222, 9217)
]

class DistributedLawbotArenaAI(DistributedBossCogAI.DistributedBossCogAI, FSM.FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedLawbotArenaAI')
    limitHitCount = 6
    hitCountDamage = 35

    def __init__(self, air):
        DistributedBossCogAI.DistributedBossCogAI.__init__(self, air, 'l')
        FSM.FSM.__init__(self, 'DistributedLawbotArenaAI')

        # Team A's lawyers
        self.lawyersA = []

        # Team B's lawyers
        self.lawyersB = []

        # Gavel obstacles
        self.gavels = None

        # The amount of health an evidence Toon-ups for
        self.toonupValue = 1

        # The amount of "damage" that has to be done to the scale before Team A wins
        self.bossMaxDamage = ToontownGlobals.LawbotArenaMaxDamage

        # The current amount of "damage" done to the scale. It starts out halfway between 0 and the max damage
        self.bossDamage = ToontownGlobals.LawbotArenaInitialDamage

        # Keeps track of whether the evidence bonus is active. -1 is disabled, 0 is Team A, and 1 is Team B
        self.bonusState = ToontownGlobals.BossArenaNoTeam

        # Keeps track of when the evidence bonus began
        self.bonusTimeStarted = 0

        self.lastAreaAttackTime = 0

        # Sudden death damage multiplier
        self.suddenDealthMultiplier = 1.0

        self.hardcore = True

        npcPair = random.choice(NPCToonPairs)
        self.witnessToonAId, self.witnessToonBId = npcPair[0], npcPair[1]

    def delete(self):
        # Cleanup any objects (such as the pan) generated in BattleOne
        self.__deleteBattleOneObjects()

        # Remove the evidence bonus task if it's active
        taskName = self.uniqueName('clearBonus')
        taskMgr.remove(taskName)

        # Run the delete functions from the parent class
        return DistributedBossCogAI.DistributedBossCogAI.delete(self)

    def getHoodId(self):
        # We're in Lawbot Headquarters
        return ToontownGlobals.LawbotHQ

    def getWitnessToonIds(self):
        return self.witnessToonAId, self.witnessToonBId

    def divideToons(self):
        # Divide the Toons up into random teams. We shouldn't have any looseToons unless ~setZone is used
        self.toonsA, self.toonsB, loose = self.__randomDivide()
        self.looseToons += loose

        # Inform the clients about all the Toons in the battle
        self.sendToonIds()

    def __randomDivide(self):
        # Grab our Toons and shuffle them
        toons = self.involvedToons[:]
        random.shuffle(toons)

        # There can only be 16 Toons in this instance
        numToons = min(len(toons), 16)

        # Calculate how many Toons should be in toonsA and toonsB
        if numToons < 8:
            numToonsB = int(numToons / 2)
        else:
            numToonsB = int((numToons + random.choice([0, 1])) / 2)
        teamA = toons[numToonsB:numToons]
        teamB = toons[:numToonsB]
        loose = toons[numToons:]

        # Return the calculations
        return (teamA, teamB, loose)

    def setLawyerMode(self, state, lawyerId):
        lawyer = self.air.doId2do.get(lawyerId)
        if not lawyer:
            return

        if not ToontownGlobals.LawbotArenaProsecutingBoth <= state <= ToontownGlobals.LawbotArenaProsecutingBoss:
            return

        lawyer.b_setMode(state)

    def hitBoss(self, bossDamage, lawyer=False):
        if not lawyer:
            # Make sure the Toon is in the battle
            avId = self.air.getAvatarIdFromSender()
            if not self.validate(avId, avId in self.involvedToons, 'hitBoss from unknown avatar'):
                return

            # Only allow Toons from toonsA to hit the defense pan
            if avId not in self.toonsA:
                return

            # If the bonus is active, double the damage made to the pan
            if self.bonusState == ToontownGlobals.BossArenaTeamA:
                bossDamage *= ToontownGlobals.LawbotBossBonusWeightMultiplier

        # The pan can only be hit in BattleOne
        currState = self.getCurrentOrNextState()
        if currState != 'BattleOne':
            return

        # If sudden death is active, increase damage made to the pan
        bossDamage *= self.suddenDealthMultiplier

        # Calculate and set the boss damage after the pan hit
        bossDamage = min(self.getBossDamage() + bossDamage, self.bossMaxDamage)
        self.b_setBossDamage(bossDamage)

        # If the scale has more damage points than the max, enter Victory state
        if self.bossDamage >= self.bossMaxDamage:
            self.b_setState('Victory')
        # Otherwise just show the hit
        else:
            self.__recordHit()

    def healBoss(self, bossHeal, lawyer=False):
        if not lawyer:
            # Make sure the Toon is in the battle
            avId = self.air.getAvatarIdFromSender()
            if not self.validate(avId, avId in self.involvedToons, 'hitBoss from unknown avatar'):
                return

            # Only allow Toons from toonsB to hit the defense pan
            if avId not in self.toonsB:
                return
            # If the bonus is active, double the damage made to the pan
            if self.bonusState == ToontownGlobals.BossArenaTeamB:
                bossHeal *= ToontownGlobals.LawbotBossBonusWeightMultiplier

        # The pan can only be hit in BattleOne
        currState = self.getCurrentOrNextState()
        if currState != 'BattleOne':
            return

        # If sudden death is active, increase damage made to the pan
        bossHeal *= self.suddenDealthMultiplier

        # Calculate and set the boss damage after the pan hit
        bossDamage = -bossHeal
        bossDamage = min(self.getBossDamage() + bossDamage, self.bossMaxDamage)
        bossDamage = max(bossDamage, 0)
        self.b_setBossDamage(bossDamage)

        # If the scale has 0 damage points, enter Defeat state
        if self.bossDamage == 0:
            self.b_setState('Defeat')
        # Otherwise just show the hit
        else:
            self.__recordHit()

    def hitToon(self, toonId):
        # Get the avId of the Toon attempting to hit another Toon
        avId = self.air.getAvatarIdFromSender()

        # You aren't allowed to Toon-up yourself
        if not self.validate(avId, avId != toonId, 'hitToon on self'):
            return

        # This person isn't involved in the battle
        if avId not in self.involvedToons or toonId not in self.involvedToons:
            return

        # If their DistributedObject still exists, go ahead and heal the Toon
        toon = self.air.doId2do.get(toonId)
        if toon:
            self.healToon(toon, self.toonupValue)
            self.sendUpdate('toonGotHealed', [toonId])

    def touchWitnessStand(self):
        # Get the avId of the Toon touching the witness stand
        avId = self.air.getAvatarIdFromSender()

        # Make sure we're in BattleOne
        currState = self.getCurrentOrNextState()
        if currState != 'BattleOne':
            return

        # Only Toons involved in the battle can get evidence
        if not self.validate(avId, avId in self.involvedToons, 'touchCage from unknown avatar'):
            return

        # Give the Toon their evidence
        toon = simbase.air.doId2do.get(avId)
        if toon:
            toon.b_setNumPies(self.numPies)
            toon.__touchedCage = 1

    def doTaunt(self):
        # Only taunt in BattleOne
        if not self.state == 'BattleOne':
            return

        # Get a random taunt
        tauntIndex = random.randrange(len(TTLocalizer.LawbotBossTaunts))
        extraInfo = 0
        if tauntIndex == 0 and self.involvedToons:
            extraInfo = random.randrange(len(self.involvedToons))
        self.sendUpdate('setTaunt', [tauntIndex, extraInfo])

    def waitForNextAttack(self, delayTime):
        currState = self.getCurrentOrNextState()

        # If we're in BattleOne, do another attack after a certain amount of time
        if currState == 'BattleOne':
            taskName = self.uniqueName('NextAttack')
            taskMgr.remove(taskName)
            taskMgr.doMethodLater(delayTime, self.doNextAttack, taskName)

    def doNextAttack(self, task):
        for lawyer in self.lawyersA:
            lawyer.doNextAttack(self)

        for lawyer in self.lawyersB:
            lawyer.doNextAttack(self)

        self.waitForNextAttack(ToontownGlobals.LawbotBossLawyerCycleTime + 0.5)
        timeSinceLastAttack = globalClock.getFrameTime() - self.lastAreaAttackTime
        allowedByTime = 15 < timeSinceLastAttack or self.lastAreaAttackTime == 0
        doAttack = random.randrange(1, 101)
        self.notify.debug('allowedByTime=%d doAttack=%d' % (allowedByTime, doAttack))
        if doAttack <= ToontownGlobals.LawbotBossChanceToDoAreaAttack and allowedByTime:
            self.__doAreaAttack()
            self.lastAreaAttackTime = globalClock.getFrameTime()
        else:
            chanceToDoTaunt = ToontownGlobals.LawbotBossChanceForTaunt
            action = random.randrange(1, 101)
            if action <= chanceToDoTaunt:
                self.doTaunt()
                pass

    def __doAreaAttack(self):
        self.b_setAttackCode(ToontownGlobals.BossCogAreaAttack)

    def b_setBossDamage(self, bossDamage):
        self.d_setBossDamage(bossDamage)
        self.setBossDamage(bossDamage)

    def setBossDamage(self, bossDamage):
        self.bossDamage = bossDamage

    def getBossDamage(self):
        return self.bossDamage

    def d_setBossDamage(self, bossDamage):
        self.sendUpdate('setBossDamage', [bossDamage])

    def __sendLawyerIds(self):
        lawyers = []

        for lawyer in self.lawyersA:
            lawyers.append(lawyer.doId)

        for lawyer in self.lawyersB:
            lawyers.append(lawyer.doId)

        self.sendUpdate('setLawyerIds', [lawyers])

    def removeToon(self, avId):
        toon = simbase.air.doId2do.get(avId)
        if toon:
            toon.b_setNumPies(0)
        DistributedBossCogAI.DistributedBossCogAI.removeToon(self, avId)

    def enterOff(self):
        self.notify.debug('enterOff')
        DistributedBossCogAI.DistributedBossCogAI.enterOff(self)
        self.__deleteBattleOneObjects()
        self.__resetLawyers()

    def enterElevator(self):
        self.notify.debug('enterElevator')
        DistributedBossCogAI.DistributedBossCogAI.enterElevator(self)
        self.b_setBossDamage(ToontownGlobals.LawbotArenaInitialDamage)

    def enterIntroduction(self):
        self.notify.debug('enterIntroduction')
        self.barrier = self.beginBarrier('Introduction', self.involvedToons, 90, self.doneIntroduction)
        self.b_setBossDamage(ToontownGlobals.LawbotArenaInitialDamage)

        # Generate lawyers
        self.__makeLawyers()

    def exitIntroduction(self):
        self.notify.debug('exitIntroduction')
        DistributedBossCogAI.DistributedBossCogAI.exitIntroduction(self)

    def makeBattleOneBattles(self):
        pass

    def enterBattleOne(self):
        self.battleThreeTimeStarted = globalClock.getFrameTime()

        # Not sure how many gavels should be on the field yet
        self.numGavels = 6

        # 1 toon-up per evidence
        self.toonupValue = 1

        # Make the necessary objects
        self.__makeBattleOneObjects()
        self.numPies = 100
        self.resetBattles()
        self.setPieType()

        # Start the scales off even
        self.b_setBossDamage(ToontownGlobals.LawbotArenaInitialDamage)

        self.battleThreeStart = globalClock.getFrameTime()
        for toonId in self.involvedToons:
            toon = simbase.air.doId2do.get(toonId)
            if toon:
                toon.__touchedCage = 0

        # Enable the gavels
        for aGavel in self.gavels:
            aGavel.turnOn()

        # In fifteen minutes, begin sudden death
        taskMgr.doMethodLater(ToontownGlobals.LawbotArenaSuddenDeathDuration, self.startSuddenDeath, self.uniqueName('startSuddenDeath'), extraArgs=[])

        self.waitForNextAttack(5)

    def __makeBattleOneObjects(self):
        if self.gavels == None:
            self.gavels = []
            for index in range(self.numGavels):
                gavel = DistributedLawbotBossGavelAI.DistributedLawbotBossGavelAI(self.air, self, index)
                gavel.generateWithRequired(self.zoneId)
                self.gavels.append(gavel)

    def __deleteBattleOneObjects(self):
        if self.gavels != None:
            for gavel in self.gavels:
                gavel.requestDelete()

            self.gavels = None
        return

    def startSuddenDeath(self):
        # Start sudden death with a base multiplier
        self.suddenDealthMultiplier = ToontownGlobals.LawbotArenaSuddenDeathInitialMultiplier
        self.sendUpdate('increaseSuddenDeath', [self.suddenDealthMultiplier])

        # Every so often increase the multiplier
        taskMgr.doMethodLater(ToontownGlobals.LawbotArenaSuddenDeathOvertimeDuration, self.increaseSuddenDeath, self.uniqueName('increaseSuddenDeath'))

    def increaseSuddenDeath(self, task):
        self.suddenDealthMultiplier += ToontownGlobals.LawbotArenaSuddenDeathOvertimeMultiplier
        self.sendUpdate('increaseSuddenDeath', [self.suddenDealthMultiplier])
        return task.again

    def exitBattleOne(self):
        self.stopAttacks()
        self.__resetLawyers()
        self.__deleteBattleOneObjects()

        taskNames = ('startSuddenDeath', 'increaseSuddenDeath')
        for taskName in taskNames:
            uniqueTaskName = self.uniqueName(taskName)
            if taskMgr.hasTaskNamed(uniqueTaskName):
                taskMgr.remove(uniqueTaskName)

    def enterVictory(self):
        self.resetBattles()
        self.barrier = self.beginBarrier('Victory', self.involvedToons, 30, self.__doneVictory)
        return

    def __doneVictory(self, avIds):
        for toonId in self.involvedToons:
            toon = self.air.doId2do.get(toonId)
            if toon:
                toon.b_setHp(0)

    def exitVictory(self):
        self.takeAwayPies()

    def enterDefeat(self):
        self.resetBattles()
        self.barrier = self.beginBarrier('Defeat', self.involvedToons, 30, self.__doneDefeat)

    def __doneDefeat(self, avIds):
        for toonId in self.involvedToons:
            toon = self.air.doId2do.get(toonId)
            if toon:
                toon.b_setHp(0)

    def exitDefeat(self):
        self.takeAwayPies()

    def setPieType(self):
        for toonId in self.involvedToons:
            toon = simbase.air.doId2do.get(toonId)
            if toon:
                toon.d_setPieType(ToontownBattleGlobals.MAX_TRACK_INDEX + 1)

    def takeAwayPies(self):
        for toonId in self.involvedToons:
            toon = simbase.air.doId2do.get(toonId)
            if toon:
                toon.b_setNumPies(0)

    def __recordHit(self):
        now = globalClock.getFrameTime()
        self.hitCount += 1
        if self.hitCount < self.limitHitCount or self.bossDamage < self.hitCountDamage:
            return

    def __resetLawyers(self):
        # Cleanup all Team A lawyers
        for lawyer in self.lawyersA:
            lawyer.requestDelete()

        self.lawyersA = []

        # Cleanup all Team B lawyers
        for lawyer in self.lawyersB:
            lawyer.requestDelete()

        self.lawyersB = []

    def __makeLawyers(self):
        self.__resetLawyers()

        availableCogs = list(self.air.datapackMgr.getCogBattleAttributes().keys())
        # Defense Lawyers
        for i in range(8):
            suit = DistributedLawbotArenaSuitAI.DistributedLawbotArenaSuitAI(self.air, None, self, ToontownGlobals.BossArenaTeamA)
            suit.dna = SuitDNA.SuitDNA()
            # All lawyers will begin as Bottom Feeders, but can be upgraded later on
            suit.dna.newSuit(random.choice(availableCogs))
            suit.setPosHpr(*ToontownGlobals.LawbotArenaLawyerPosHprs[i + 8])
            # Starting exp is 0, and max exp is 6
            suit.setHP(0)
            suit.generateWithRequired(self.zoneId)
            # Set the level AFTER genering the DO
            suit.b_setMaxHp(6)
            suit.setLevel(1)
            self.lawyersA.append(suit)

        # Prosecution Lawyers
        for i in range(8):
            suit = DistributedLawbotArenaSuitAI.DistributedLawbotArenaSuitAI(self.air, None, self, ToontownGlobals.BossArenaTeamB)
            suit.dna = SuitDNA.SuitDNA()
            suit.dna.newSuit(random.choice(availableCogs))
            suit.setPosHpr(*ToontownGlobals.LawbotArenaLawyerPosHprs[i])
            # Starting exp is 0, and max exp is 6
            suit.setHP(0)
            suit.generateWithRequired(self.zoneId)
            # Set the level AFTER generating the DO
            suit.b_setMaxHp(6)
            suit.setLevel(1)
            self.lawyersB.append(suit)

        self.__sendLawyerIds()

    def clearBonus(self, taskName):
        if self and hasattr(self, 'bonusState'):
            self.bonusState = ToontownGlobals.BossArenaNoTeam

        self.sendUpdate('enteredBonusState', [ToontownGlobals.BossArenaNoTeam])

    def startBonusState(self, team):
        self.notify.debug('startBonusState')
        self.bonusTimeStarted = globalClock.getFrameTime()
        self.bonusState = team

        taskMgr.doMethodLater(ToontownGlobals.LawbotBossBonusDuration, self.clearBonus, self.uniqueName('clearBonus'))
        self.sendUpdate('enteredBonusState', [team])

    def areAllLawyersStunned(self):
        teamA = True
        teamB = True

        # Check to see if Team A's lawyers are stunned
        for lawyer in self.lawyersA:
            if not lawyer.stunned:
                # Guess not all of them are stunned
                teamB = False
                break

        # Check to see if Team B's lawyers are stunned
        for lawyer in self.lawyersB:
            if not lawyer.stunned:
                # Guess not all of them are stunned
                teamA = False
                break

        # Why would both teams get a bonus at the same time?
        if teamA and teamB:
            return

        if teamA:
            return ToontownGlobals.BossArenaTeamA
        elif teamB:
            return ToontownGlobals.BossArenaTeamB
        else:
            return ToontownGlobals.BossArenaNoTeam

    def checkForBonusState(self):
        # A bonus state is already active
        if self.bonusState != ToontownGlobals.BossArenaNoTeam:
            return

        # If no team has a bonus, why give it to them?
        lawyersStunned = self.areAllLawyersStunned()
        # don't use `not lawyersStunned`; what happens if lawyersStynned == 0?
        if lawyersStunned is None or lawyersStunned == ToontownGlobals.BossArenaNoTeam:
            return

        # Start the bonus state
        curTime = globalClock.getFrameTime()
        delta = curTime - self.bonusTimeStarted
        if ToontownGlobals.LawbotBossBonusWaitTime < delta:
            self.startBonusState(lawyersStunned)

    def zapToon(self, x, y, z, h, p, r, bpx, bpy, attackCode, timestamp):
        avId = self.air.getAvatarIdFromSender()
        if not self.validate(avId, avId in self.involvedToons, 'zapToon from unknown avatar'):
            return
        if attackCode in (ToontownGlobals.BossCogLawyerAttack, ToontownGlobals.BossCogLawyerAttack) and self.dna.dept != 'l':
            self.notify.warning('got lawyer attack but not in CJ boss battle')
            return
        toon = simbase.air.doId2do.get(avId)
        if toon:
            self.d_showZapToon(avId, x, y, z, h, p, r, attackCode, timestamp)
            currState = self.getCurrentOrNextState()
            if currState == 'BattleOne' and attackCode == ToontownGlobals.BossCogElectricFence:
                if bpy < 0 and abs(bpx / bpy) > 0.5:
                    if bpx < 0:
                        self.b_setAttackCode(ToontownGlobals.BossCogSwatRight)
                    else:
                        self.b_setAttackCode(ToontownGlobals.BossCogSwatLeft)
