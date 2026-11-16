from otp.ai.AIBaseGlobal import *
from direct.distributed.ClockDelta import *
from . import DistributedBossCogAI
from direct.directnotify import DirectNotifyGlobal
from . import DistributedSuitAI
from direct.fsm import FSM
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from toontown.toon import NPCToons
from toontown.suit import SellbotBossGlobals
from . import SuitDNA
import random


class DistributedSellbotArenaAI(DistributedBossCogAI.DistributedBossCogAI, FSM.FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedSellbotArenaAI')
    limitHitCount = 6
    numPies = ToontownGlobals.FullPies

    def __init__(self, air):
        DistributedBossCogAI.DistributedBossCogAI.__init__(self, air, 's')
        FSM.FSM.__init__(self, 'DistributedSellbotArenaAI')
        self.doobers = []
        self.winter = ToontownGlobals.WINTER_DECORATIONS in self.air.holidayManager.currentHolidays
        self.bossMaxDamage = ToontownGlobals.SellbotBossMaxDamage
        self.pieHitToonup = SellbotBossGlobals.PieToonup
        self.pieDamageMults = self.getDefaultPieDamageMult()
        self.hitCountDamage = SellbotBossGlobals.HitCountDamage
        self.recoverRate = 0
        self.recoverStartTime = 0
        self.bonusState = ToontownGlobals.BossArenaNoTeam
        self.suddenDeath = False

    def generateWithRequired(self, zoneId):
        self.numRentalDiguises, self.numNormalDiguises = self.countDisguises()
        self.__setCagedToonNpcId()
        DistributedBossCogAI.DistributedBossCogAI.generateWithRequired(self, zoneId)

    def delete(self):
        return DistributedBossCogAI.DistributedBossCogAI.delete(self)

    def getHoodId(self):
        return ToontownGlobals.SellbotHQ

    def getCagedToonNpcId(self):
        return self.cagedToonNpcId

    def __setCagedToonNpcId(self):
        if self.winter:
            self.cagedToonNpcId = random.choice(NPCToons.npcFriendsMinMaxStars(4, 5, winter=True))
            return

        if self.numRentalDiguises >= 4:
            self.cagedToonNpcId = random.choice(NPCToons.npcFriendsMinMaxStars(3, 3))
        else:
            if 1 <= self.numRentalDiguises <= 3:
                self.cagedToonNpcId = random.choice(NPCToons.npcFriendsMinMaxStars(3, 4))
            else:
                self.cagedToonNpcId = random.choice(NPCToons.npcFriendsMinMaxStars(3, 5))

    def setAttackCode(self, attackCode, avId=0):
        self.attackCode = attackCode
        self.attackAvId = avId
        if attackCode == ToontownGlobals.BossCogDizzy or attackCode == ToontownGlobals.BossCogDizzyNow:
            low = 20
            high = 5
            delayTime = self.progressValue(low, high)
            self.hitCount = 0
        else:
            if attackCode == ToontownGlobals.BossCogSlowDirectedAttack:
                delayTime = ToontownGlobals.BossCogAttackTimes.get(attackCode)
                delayTime += self.progressValue(10, 0)
            else:
                delayTime = ToontownGlobals.BossCogAttackTimes.get(attackCode)
                if delayTime is None:
                    return
        self.waitForNextAttack(delayTime)

    def magicWordHit(self, damage, avId):
        if self.attackCode != ToontownGlobals.BossCogDizzyNow:
            self.hitBossInsides()
        self.hitBoss(damage)

    def hitBoss(self):
        avId = self.air.getAvatarIdFromSender()
        if not self.validate(avId, avId in self.involvedToons, 'DistributedSellbotArenaAI.hitBoss from unknown avatar'):
            return

        team = self.getTeam(avId)
        bossDamage = ToontownGlobals.SellbotArenaPieDamages.get(team, 0) * self.pieDamageMults.get(team, 0)

        currState = self.getCurrentOrNextState()
        if currState != 'BattleOne':
            return

        if self.attackCode != ToontownGlobals.BossCogDizzyNow:
            return

        bossDamage = self.getBossDamage() + bossDamage
        if bossDamage > self.bossMaxDamage:
            bossDamage = self.bossMaxDamage
        elif bossDamage < -self.bossMaxDamage:
            bossDamage = -self.bossMaxDamage

        self.b_setBossDamage(bossDamage, 0, 0)

        if self.bossDamage >= self.bossMaxDamage or self.bossDamage <= -self.bossMaxDamage:
            self.setState('NearVictory')
        else:
            self.__recordHit()

    def hitBossInsides(self):
        avId = self.air.getAvatarIdFromSender()
        if not self.validate(avId, avId in self.involvedToons, 'hitBossInsides from unknown avatar'):
            return
        currState = self.getCurrentOrNextState()
        if currState != 'BattleOne':
            return
        self.bonusState = self.getTeam(avId)
        self.b_setAttackCode(ToontownGlobals.BossCogDizzyNow)
        self.b_setBossDamage(self.getBossDamage(), 0, 0)
        self.__adjustPieDamageMult()

    def hitToon(self, toonId):
        avId = self.air.getAvatarIdFromSender()
        if not self.validate(avId, avId != toonId, 'hitToon on self'):
            return
        if avId not in self.involvedToons or toonId not in self.involvedToons:
            return
        toon = self.air.doId2do.get(toonId)
        if toon:
            self.healToon(toon, self.pieHitToonup)

    def d_setPieDamageMult(self, teamAMult, teamBMult):
        self.sendUpdate('setPieDamageMult', [teamAMult, teamBMult])

    def getDefaultPieDamageMult(self):
        return {ToontownGlobals.BossArenaTeamA: 1,
                ToontownGlobals.BossArenaTeamB: 1}

    def __adjustPieDamageMult(self):
        self.pieDamageMults = self.getDefaultPieDamageMult()

        for team in (ToontownGlobals.BossArenaTeamA, ToontownGlobals.BossArenaTeamB):
            if team == self.bonusState:
                self.pieDamageMults[team] *= ToontownGlobals.SellbotArenaPieDmgMult
            if self.suddenDeath:
                self.pieDamageMults[team] *= ToontownGlobals.SellbotArenaSuddenDeathPieDmgMult

        self.d_setPieDamageMult(self.pieDamageMults[ToontownGlobals.BossArenaTeamA],
                                self.pieDamageMults[ToontownGlobals.BossArenaTeamB])

    def getDamageMultiplier(self):
        return SellbotBossGlobals.AttackMult

    def gotPies(self):
        avId = self.air.getAvatarIdFromSender()
        currState = self.getCurrentOrNextState()
        if currState != 'BattleOne' and currState != 'NearVictory':
            return
        if not self.validate(avId, avId in self.involvedToons, 'touchCage from unknown avatar'):
            return
        toon = self.air.doId2do.get(avId)
        if toon:
            toon.b_setNumPies(self.numPies)

    def finalPieSplat(self):
        if self.state != 'NearVictory':
            return
        self.b_setState('Victory')

    def doNextAttack(self, task):
        if self.paused:
            return

        if self.attackCode == ToontownGlobals.BossCogDizzyNow:
            attackCode = ToontownGlobals.BossCogRecoverDizzyAttack
            self.bonusState = ToontownGlobals.BossArenaNoTeam
        else:
            attackList = [ToontownGlobals.BossCogAreaAttack, ToontownGlobals.BossCogFrontAttack, ToontownGlobals.BossCogDirectedAttack,
                          ToontownGlobals.BossCogDirectedAttack, ToontownGlobals.BossCogDirectedAttack, ToontownGlobals.BossCogDirectedAttack]
            attackCode = random.choice(attackList)
        if attackCode == ToontownGlobals.BossCogAreaAttack:
            self.__doAreaAttack()
        else:
            if attackCode == ToontownGlobals.BossCogDirectedAttack:
                self.__doDirectedAttack()
            else:
                self.b_setAttackCode(attackCode)

    def __doAreaAttack(self):
        self.b_setAttackCode(ToontownGlobals.BossCogAreaAttack)
        if self.recoverRate:
            recoverMultiplier = 1.2
            newRecoverRate = min(200.0, self.recoverRate * recoverMultiplier)
        else:
            newRecoverRate = 2
        now = globalClock.getFrameTime()
        self.b_setBossDamage(self.getBossDamage(), newRecoverRate, now)

    def __doDirectedAttack(self):
        if self.nearToons:
            toonId = random.choice(self.nearToons)
            self.b_setAttackCode(ToontownGlobals.BossCogDirectedAttack, toonId)
        else:
            self.__doAreaAttack()

    def b_setBossDamage(self, bossDamage, recoverRate, recoverStartTime):
        self.d_setBossDamage(bossDamage, recoverRate, recoverStartTime)
        self.setBossDamage(bossDamage, recoverRate, recoverStartTime)

    def setBossDamage(self, bossDamage, recoverRate, recoverStartTime):
        self.bossDamage = bossDamage
        self.recoverRate = recoverRate
        self.recoverStartTime = recoverStartTime

    def getBossDamage(self):
        now = globalClock.getFrameTime()
        elapsed = now - self.recoverStartTime
        return int(self.bossDamage - self.recoverRate * elapsed / 60.0)

    def d_setBossDamage(self, bossDamage, recoverRate, recoverStartTime):
        timestamp = globalClockDelta.localToNetworkTime(recoverStartTime)
        self.sendUpdate('setBossDamage', [bossDamage, recoverRate, timestamp])

    def waitForNextStrafe(self, delay):
        currState = self.getCurrentOrNextState()
        if currState == 'BattleOne':
            taskName = self.uniqueName('NextStrafe')
            self.removeTask(taskName)
            self.addTask(self.doNextStrafe, taskName, delay = delay)

    def stopStrafes(self):
        taskName = self.uniqueName('NextStrafe')
        self.removeTask(taskName)

    def doNextStrafe(self, task):
        if self.attackCode != ToontownGlobals.BossCogDizzyNow:
            direction = random.choice([0, 1])
            self.sendUpdate('doStrafe', [direction])
        delayTime = 9
        self.waitForNextStrafe(delayTime)

    def __sendDooberIds(self):
        dooberIds = []
        for suit in self.doobers:
            dooberIds.append(suit.doId)

        self.sendUpdate('setDooberIds', [dooberIds])

    def d_cagedToonBattleOne(self, index, avId):
        self.sendUpdate('cagedToonBattleOne', [index, avId])

    def d_setTimer(self, endTime):
        endTime = globalClock.getRealTime() + endTime
        self.sendUpdate('setTimer', [globalClockDelta.localToNetworkTime(endTime)])

    def removeToon(self, avId):
        toon = self.air.doId2do.get(avId)
        if toon:
            toon.b_setNumPies(0)
        DistributedBossCogAI.DistributedBossCogAI.removeToon(self, avId)

    def enterOff(self):
        DistributedBossCogAI.DistributedBossCogAI.enterOff(self)
        self.__resetDoobers()

    def enterElevator(self):
        DistributedBossCogAI.DistributedBossCogAI.enterElevator(self)
        self.b_setBossDamage(0, 0, 0)

    def enterIntroduction(self):
        DistributedBossCogAI.DistributedBossCogAI.enterIntroduction(self)
        # self.__makeDoobers()
        self.b_setBossDamage(0, 0, 0)

    def exitIntroduction(self):
        DistributedBossCogAI.DistributedBossCogAI.exitIntroduction(self)
        self.__resetDoobers()

    def makeBattleOneBattles(self):
        pass

    def enterBattleOne(self):
        self.setPieType()
        self.b_setBossDamage(0, 0, 0)
        self.__adjustPieDamageMult()
        self.battleThreeStart = globalClock.getFrameTime()

        # In four minutes, announce that sudden death is starting soon.
        # This exists because some people don't pay attention to the timer,
        # and we also need to give that sense of urgency.
        self.addTask(self.__announceUpcomingSuddenDeath, self.uniqueName('announceUpcomingSuddenDeath'), 
                     delay = ToontownGlobals.SellbotArenaUpcomingSuddenDeathDuration, extraArgs = [])

        # In five minutes, begin sudden death
        self.addTask(self.__startSuddenDeath, self.uniqueName('startSuddenDeath'),
                     delay = ToontownGlobals.SellbotArenaSuddenDeathDuration, extraArgs = [])

        # Let our clients know about how much time we have until Sudden Death
        self.d_setTimer(ToontownGlobals.SellbotArenaSuddenDeathDuration)

        self.waitForNextAttack(5)
        self.waitForNextStrafe(9)
        self.cagedToonDialogIndex = 100
        self.__saySomethingLater()

    def __saySomething(self, task=None):
        index = None
        if len(self.involvedToons) == 0:
            return
        avId = random.choice(self.involvedToons)
        if self.cagedToonDialogIndex <= TTLocalizer.CagedToonBattleThreeMaxAdvice:
            index = self.cagedToonDialogIndex
            self.cagedToonDialogIndex += 1
        elif random.random() < 0.2:
            index = random.randrange(100, TTLocalizer.CagedToonBattleThreeMaxAdvice + 1)
        if index:
            self.d_cagedToonBattleOne(index, avId)
        self.__saySomethingLater()
        if task:
            return task.done

    def __saySomethingLater(self, delay=15):
        taskName = self.uniqueName('CagedToonSaySomething')
        self.removeTask(taskName)
        self.addTask(self.__saySomething, taskName, delay = delay)

    # TODO: Fill these in once we get some GUI to work with

    def __announceUpcomingSuddenDeath(self):
        """
        Tell our clients that sudden death is going to begin shortly.
        """
        # Announce that sudden death is going to begin soon
        # 

        # self.sendUpdate('', [])
        pass

    def __startSuddenDeath(self):
        """
        Activates sudden death and
        announces it to all clients.
        """

        self.suddenDeath = True
        self.__adjustPieDamageMult()

        # self.sendUpdate('', [])

    def exitBattleOne(self):
        self.stopAttacks()
        self.stopStrafes()
        taskNames = ('CagedToonSaySomething', 'announceUpcomingSuddenDeath', 'startSuddenDeath')
        for taskName in taskNames:
            self.removeTask(taskName)


    def enterNearVictory(self):
        pass

    def exitNearVictory(self):
        pass

    def enterVictory(self):
        self.barrier = self.beginBarrier('Victory', self.involvedToons, 10, self.__doneVictory)

    def __doneVictory(self, avIds):
        self.b_setState('Reward')

    def exitVictory(self):
        self.takeAwayPies()

    def enterFrolic(self):
        DistributedBossCogAI.DistributedBossCogAI.enterFrolic(self)
        self.b_setBossDamage(0, 0, 0)

    def __resetDoobers(self):
        for suit in self.doobers:
            suit.requestDelete()

        self.doobers = []

    def __makeDoobers(self):
        self.__resetDoobers()
        for i in range(8):
            suit = DistributedSuitAI.DistributedSuitAI(self.air, None)
            level = random.randrange(len(SuitDNA.suitsPerLevel))
            suit.dna = SuitDNA.SuitDNA()
            suit.dna.newSuitRandom(level=level, dept=self.dna.dept)
            suit.setLevel(level)
            suit.generateWithRequired(self.zoneId)
            self.doobers.append(suit)

        self.__sendDooberIds()

    def setPieType(self):
        for toonId in self.involvedToons:
            toon = self.air.doId2do.get(toonId)
            if toon:
                pieType = 4
                if self.winter:
                    pieType = 8
                toon.d_setPieType(pieType)

    def takeAwayPies(self):
        for toonId in self.involvedToons:
            toon = self.air.doId2do.get(toonId)
            if toon:
                toon.b_setNumPies(0)

    def __recordHit(self):
        self.hitCount += 1
        if self.hitCount < self.limitHitCount:
            return
        if self.bossDamage < 0:
            if self.bossDamage > -self.hitCountDamage:
                return
        elif self.bossDamage < self.hitCountDamage:
            return

        self.bonusState = ToontownGlobals.BossArenaNoTeam
        self.b_setAttackCode(ToontownGlobals.BossCogRecoverDizzyAttack)
        self.__adjustPieDamageMult()

    def setMode(self, mode):
        DistributedBossCogAI.DistributedBossCogAI.setMode(self, mode)

        self.bossMaxDamage = ToontownGlobals.SellbotBossMaxDamage
        self.pieHitToonup = SellbotBossGlobals.PieToonup
        self.pieDamageMults = self.getDefaultPieDamageMult()
        self.hitCountDamage = SellbotBossGlobals.HitCountDamage

    def zapToon(self, x, y, z, h, p, r, bpx, bpy, attackCode, timestamp):
        avId = self.air.getAvatarIdFromSender()
        if not self.validate(avId, avId in self.involvedToons, 'zapToon from unknown avatar'):
            return
        if attackCode in (ToontownGlobals.BossCogLawyerAttack, ToontownGlobals.BossCogLawyerAttack) and self.dna.dept != 'l':
            self.notify.warning('got lawyer attack but not in CJ boss battle')
            return
        toon = self.air.doId2do.get(avId)
        if toon:
            self.d_showZapToon(avId, x, y, z, h, p, r, attackCode, timestamp)
            currState = self.getCurrentOrNextState()
            if currState == 'BattleOne' and attackCode == ToontownGlobals.BossCogElectricFence:
                if bpy < 0 and abs(bpx / bpy) > 0.5:
                    if bpx < 0:
                        self.b_setAttackCode(ToontownGlobals.BossCogSwatRight)
                    else:
                        self.b_setAttackCode(ToontownGlobals.BossCogSwatLeft)
