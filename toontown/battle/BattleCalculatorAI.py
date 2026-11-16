from typing import Optional, List, Dict, Any
from .BattleBase import *
from .DistributedBattleAI import *
from toontown.battle.StatusEffect import StatusEffect
from toontown.toonbase.ToontownBattleGlobals import *
from toontown.battle.BattleCalculatorGlobals import *
from toontown.battle.BattleWeatherGlobals import *
import random, math
from toontown.suit import DistributedSuitBaseAI
from . import BattleExperienceAI
from toontown.toon import NPCToons
from toontown.pets import PetTricks, DistributedPetProxyAI
from direct.showbase.PythonUtil import lerp

from ..toonbase import ServerSettings


class BattleCalculatorAI:
    TRAP_CONFLICT = -2
    CAP_HEALS = 1
    SUITS_UNLURED_IMMEDIATELY = 1
    CLEAR_MULTIPLE_TRAPS = 0
    KBBONUS_LURED_FLAG = 0
    KBBONUS_TGT_LURED = 1
    notify = DirectNotifyGlobal.directNotify.newCategory('BattleCalculatorAI')
    toonsAlwaysHit = simbase.config.GetBool('toons-always-hit', 0)
    toonsAlwaysMiss = simbase.config.GetBool('toons-always-miss', 0)
    toonsAlways5050 = simbase.config.GetBool('toons-always-5050', 0)
    suitsAlwaysHit = simbase.config.GetBool('suits-always-hit', 0)
    suitsAlwaysMiss = simbase.config.GetBool('suits-always-miss', 0)
    immortalSuits = simbase.config.GetBool('immortal-suits', 0)
    propAndOrganicBonusStack = simbase.config.GetBool('prop-and-organic-bonus-stack', 0)

    def __init__(self, battle, tutorialFlag=0):
        self.battle = battle
        self.currentlyLuredSuits = {}
        self.successfulLures = {}
        self.toonAtkOrder = []
        self.toonHPAdjusts = {}
        self.toonSkillPtsGained = {}
        self.traps = {}
        self.npcTraps = {}
        self.delayedUnlures = []
        self.__skillCreditMultiplier = 1
        self.tutorialFlag = tutorialFlag
        self.trainTrapTriggered = False

    def setSkillCreditMultiplier(self, mult):
        self.__skillCreditMultiplier = mult

    def getSkillCreditMultiplier(self):
        return self.__skillCreditMultiplier

    def cleanup(self):
        self.battle = None

    def __calcToonAtkHit(self, toonId, atkTargets):
        toon = self.battle.getToon(toonId)
        if len(atkTargets) == 0:
            return (0, 0)
        if toon.getInstaKill() or toon.getAlwaysHitSuits():
            return (1, 95)
        if self.tutorialFlag:
            return (1, 95)
        if self.toonsAlways5050:
            roll = random.randint(0, 99)
            if roll < 50:
                return (1, 95)
            else:
                return (0, 0)
        if self.toonsAlwaysMiss:
            return (0, 0)
        debug = self.notify.getDebug()
        attack = self.battle.toonAttacks[toonId]
        atkTrack, atkLevel = self.__getActualTrackLevel(attack)
        if atkTrack == NPCSOS:
            return (1, 95)
        if atkTrack == FIRE:
            cog = atkTargets[0]
            # TODO: INSTEAD CHECK IF THE COG HAS AN UNFIREABLE FLAG
            # TENURE WHEN ADDED/REMOVED SHOULD CHANGE THIS FLAG
            if cog.hasStatusEffect('ttrealms:tenure'):
                return (0, 0)
            return (1, 95)
        if self.toonsAlwaysHit:
            return (1, 95)
        if atkTrack == TRAP:
            if debug:
                self.notify.debug('Attack is a trap, so it hits regardless')
            attack.setAccBonus(False)
            return (1, 100)
        elif atkTrack == DROP and attack.getTrack() == NPCSOS:
            unluredSuits = 0
            for tgt in atkTargets:
                if not self.suitIsLured(tgt.getDoId()):
                    unluredSuits = 1

            if unluredSuits == 0:
                attack.setAccBonus(True)
                return (0, 0)
        elif atkTrack == DROP:
            allLured = True
            for i in range(len(atkTargets)):
                if self.suitIsLured(atkTargets[i].getDoId()):
                    pass
                else:
                    allLured = False

            if toon.getAlwaysHitSuits():
                return (1, 95)
            if allLured:
                attack.setAccBonus(True)
                return (0, 0)
        elif atkTrack == PETSOS:
            return self.__calculatePetTrickSuccess(attack)
        tgtDef = 0
        numLured = 0
        if atkTrack != HEAL:
            for currTarget in atkTargets:
                thisSuitDef = self.__targetDefense(currTarget, atkTrack)
                if debug:
                    self.notify.debug('Examining suit def for toon attack: ' + str(thisSuitDef))
                tgtDef = min(thisSuitDef, tgtDef)
                if self.suitIsLured(currTarget.getDoId()):
                    numLured += 1

        trackExp = self.__toonTrackExp(attack.getAttackerId(), atkTrack)
        for currOtherAtk in self.toonAtkOrder:
            if currOtherAtk != attack.getAttackerId():
                nextAttack = self.battle.toonAttacks[currOtherAtk]
                nextAtkTrack = self.__getActualTrack(nextAttack)
                if atkTrack == nextAtkTrack and attack.getTarget() == nextAttack.getTarget():
                    currTrackExp = self.__toonTrackExp(nextAttack.getAttackerId(), atkTrack)
                    if debug:
                        self.notify.debug('Examining toon track exp bonus: ' + str(currTrackExp))
                    trackExp = max(currTrackExp, trackExp)

        if debug:
            if atkTrack == HEAL:
                self.notify.debug('Toon attack is a heal, no target def used')
            else:
                self.notify.debug('Suit defense used for toon attack: ' + str(tgtDef))
            self.notify.debug('Toon track exp bonus used for toon attack: ' + str(trackExp))
        if attack.getTrack() == NPCSOS:
            randChoice = 0
        else:
            randChoice = random.randint(0, 99)
        propAcc = AvPropAccuracy[atkTrack][atkLevel]
        if atkTrack == LURE:
            treebonus = self.__toonCheckGagBonus(attack.getAttackerId(), atkTrack, atkLevel)
            propBonus = self.__checkPropBonus(atkTrack)
            if self.propAndOrganicBonusStack:
                propAcc = 0
                if treebonus:
                    self.notify.debug('using organic bonus lure accuracy')
                    propAcc += AvLureBonusAccuracy[atkLevel]
                if propBonus:
                    self.notify.debug('using prop bonus lure accuracy')
                    propAcc += AvLureBonusAccuracy[atkLevel]
            elif treebonus or propBonus:
                self.notify.debug('using oragnic OR prop bonus lure accuracy')
                propAcc = AvLureBonusAccuracy[atkLevel]
        attackAcc = propAcc + trackExp + tgtDef
        currAtk = self.toonAtkOrder.index(toonId)
        if currAtk > 0 and atkTrack != HEAL:
            prevAtkId = self.toonAtkOrder[currAtk - 1]
            prevAttack = self.battle.toonAttacks[prevAtkId]
            prevAtkTrack = self.__getActualTrack(prevAttack)
            lure = atkTrack == LURE and (not attackAffectsGroup(atkTrack, atkLevel,
             attack.getTrack()) and attack.getTarget() in self.successfulLures or attackAffectsGroup(atkTrack, atkLevel, attack.getTrack()))
            if atkTrack == prevAtkTrack and (attack.getTarget() == prevAttack.getTarget() or lure):
                if prevAttack.getAccBonus():
                    if debug:
                        self.notify.debug('DODGE: Toon attack track dodged')
                elif not prevAttack.getAccBonus():
                    if debug:
                        self.notify.debug('HIT: Toon attack track hit')
                attack.setAccBonus(prevAttack.getAccBonus())
                return (not attack.getAccBonus(), attackAcc)
        atkAccResult = attackAcc
        if debug:
            self.notify.debug('setting atkAccResult to %d' % atkAccResult)
        acc = attackAcc + self.__calcToonAccBonus(toonId)
        if atkTrack != LURE and atkTrack != HEAL:
            if atkTrack != DROP:
                if numLured == len(atkTargets):
                    if debug:
                        self.notify.debug('all targets are lured, attack hits')
                    attack.setAccBonus(False)
                    return (1, 100)
                else:
                    luredRatio = float(numLured) / float(len(atkTargets))
                    accAdjust = 100 * luredRatio
                    if accAdjust > 0 and debug:
                        self.notify.debug(str(numLured) + ' out of ' + str(len(atkTargets)) + ' targets are lured, so adding ' + str(accAdjust) + ' to attack accuracy')
                    acc += accAdjust
            elif numLured == len(atkTargets):
                if debug:
                    self.notify.debug('all targets are lured, attack misses')
                attack.setAccBonus(False)
                return (0, 0)
        if acc > MaxToonAcc:
            acc = MaxToonAcc
        if randChoice < acc:
            if debug:
                self.notify.debug('HIT: Toon attack rolled' + str(randChoice) + 'to hit with an accuracy of' + str(acc))
            attack.setAccBonus(False)
        else:
            if debug:
                self.notify.debug('MISS: Toon attack rolled' + str(randChoice) + 'to hit with an accuracy of' + str(acc))
            attack.setAccBonus(True)
        return (not attack.getAccBonus(), atkAccResult)

    def __toonTrackExp(self, toonId, track):
        toon = self.battle.getToon(toonId)
        if toon != None:
            toonExpLvl = toon.experience.getExpLevel(track)
            exp = getAttackExpPerTrack(toonExpLvl)
            if track == HEAL:
                exp = exp * 0.5
            self.notify.debug('Toon track exp: ' + str(toonExpLvl) + ' and resulting acc bonus: ' + str(exp))
            return exp
        else:
            return 0

    def __toonCheckGagBonus(self, toonId, track, level):
        toon = self.battle.getToon(toonId)
        if toon != None:
            return toon.checkGagBonus(track, level)
        else:
            return False

    def __checkPropBonus(self, track: int) -> bool:
        return self.battle.getInteractivePropTrackBonus() == track

    def __targetDefense(self, suit, atkTrack):
        if atkTrack == HEAL:
            return 0
        return simbase.air.datapackMgr.getCogGagAccuracyDecrement(suit.dna.name, suit.getLevel() + 1)

    def __createToonTargetList(self, attack: BattleAttack):
        atkTrack, atkLevel = self.__getActualTrackLevel(attack)
        targetList = []
        if atkTrack == NPCSOS:
            return targetList
        if not attackAffectsGroup(atkTrack, atkLevel, attack.getTrack()):
            if atkTrack == HEAL:
                target = attack.getTarget()
            else:
                target = self.battle.findSuit(attack.getTarget())
            if target != None:
                targetList.append(target)
        else:
            if atkTrack == HEAL or atkTrack == PETSOS:
                if simbase.air.wantSelfToonUp or attack.getTrack() == NPCSOS or atkTrack == PETSOS:
                    targetList = self.battle.activeToons
                else:
                    for currToon in self.battle.activeToons:
                        if attack.getAttackerId() != currToon:
                            targetList.append(currToon)

            else:
                targetList = self.battle.activeSuits
        return targetList

    def __prevAtkTrack(self, attackerId, toon=1):
        if toon:
            prevAtkIdx = self.toonAtkOrder.index(attackerId) - 1
            if prevAtkIdx >= 0:
                prevAttackerId = self.toonAtkOrder[prevAtkIdx]
                attack = self.battle.toonAttacks[prevAttackerId]
                return self.__getActualTrack(attack)
            else:
                return NO_ATTACK

    def getSuitTrapType(self, suitId):
        if suitId in self.traps:
            if self.traps[suitId][0] == self.TRAP_CONFLICT:
                return NO_TRAP
            else:
                return self.traps[suitId][0]
        else:
            return NO_TRAP

    def __suitTrapDamage(self, suitId):
        if suitId in self.traps:
            return self.traps[suitId][2]
        else:
            return 0

    def addTrainTrapForJoiningSuit(self, suitId):
        self.notify.debug('addTrainTrapForJoiningSuit suit=%d self.traps=%s' % (suitId, self.traps))
        trapInfoToUse = None
        for trapInfo in list(self.traps.values()):
            if trapInfo[0] == UBER_GAG_LEVEL_INDEX:
                trapInfoToUse = trapInfo
                break

        if trapInfoToUse:
            self.traps[suitId] = trapInfoToUse
        else:
            self.notify.warning('huh we did not find a train trap?')

    def __addSuitGroupTrap(self, suitId, trapLvl, attackerId, allSuits, npcDamage=0):
        if npcDamage == 0:
            if suitId in self.traps:
                if self.traps[suitId][0] != self.TRAP_CONFLICT:
                    self.traps[suitId][0] = self.TRAP_CONFLICT
                for suit in allSuits:
                    id = suit.doId
                    if id in self.traps:
                        self.traps[id][0] = self.TRAP_CONFLICT
                    else:
                        self.traps[id] = [
                         self.TRAP_CONFLICT, 0, 0]
            else:
                toon = self.battle.getToon(attackerId)
                organicBonus = toon.checkGagBonus(TRAP, trapLvl)
                propBonus = self.__checkPropBonus(TRAP)
                damage = getAvPropDamage(TRAP, trapLvl, toon.experience.getExp(TRAP), organicBonus, propBonus, self.propAndOrganicBonusStack)
                if self.itemIsCredit(TRAP, trapLvl):
                    self.traps[suitId] = [
                     trapLvl, attackerId, damage]
                else:
                    self.traps[suitId] = [trapLvl, 0, damage]
                self.notify.debug('calling __addLuredSuitsDelayed')
                self.__addLuredSuitsDelayed(attackerId, targetId=-1, ignoreDamageCheck=True)
        elif suitId in self.traps:
            if self.traps[suitId][0] == self.TRAP_CONFLICT:
                self.traps[suitId] = [
                 trapLvl, 0, npcDamage]
        elif not self.suitIsLured(suitId):
            self.traps[suitId] = [
             trapLvl, 0, npcDamage]

    def __addSuitTrap(self, suitId, trapLvl, attackerId, npcDamage=0):
        if npcDamage == 0:
            if suitId in self.traps:
                if self.traps[suitId][0] != self.TRAP_CONFLICT:
                    self.traps[suitId][0] = self.TRAP_CONFLICT
            else:
                toon = self.battle.getToon(attackerId)
                organicBonus = toon.checkGagBonus(TRAP, trapLvl)
                propBonus = self.__checkPropBonus(TRAP)
                damage = getAvPropDamage(TRAP, trapLvl, toon.experience.getExp(TRAP), organicBonus, propBonus, self.propAndOrganicBonusStack)
                if self.itemIsCredit(TRAP, trapLvl):
                    self.traps[suitId] = [
                     trapLvl, attackerId, damage]
                else:
                    self.traps[suitId] = [trapLvl, 0, damage]
        else:
            if suitId in self.traps:
                if self.traps[suitId][0] == self.TRAP_CONFLICT:
                    self.traps[suitId] = [
                     trapLvl, 0, npcDamage]
            else:
                if not self.suitIsLured(suitId):
                    self.traps[suitId] = [
                     trapLvl, 0, npcDamage]

    def __removeSuitTrap(self, suitId):
        if suitId in self.traps:
            del self.traps[suitId]

    def __clearTrapCreator(self, creatorId, suitId=None):
        if suitId == None:
            for currTrap in list(self.traps.keys()):
                if creatorId == self.traps[currTrap][1]:
                    self.traps[currTrap][1] = 0

        elif suitId in self.traps:
            self.traps[suitId][1] = 0

    def __trapCreator(self, suitId):
        if suitId in self.traps:
            return self.traps[suitId][1]
        else:
            return 0

    def __initTraps(self):
        self.trainTrapTriggered = False
        keysList = list(self.traps.keys())
        for currTrap in keysList:
            if self.traps[currTrap][0] == self.TRAP_CONFLICT:
                del self.traps[currTrap]

    def __calcToonAtkHp(self, toonId):
        attack = self.battle.toonAttacks[toonId]
        targetList = self.__createToonTargetList(attack)
        atkHit, atkAcc = self.__calcToonAtkHit(toonId, targetList)
        atkTrack, atkLevel, atkHp = self.__getActualTrackLevelHp(attack)
        if not atkHit and atkTrack != HEAL:
            return
        validTargetAvail = 0
        lureDidDamage = 0
        currLureId = -1
        for currTarget in range(len(targetList)):
            attackLevel = -1
            attackTrack = None
            attackDamage = 0
            toonTarget = 0
            targetLured = 0
            if atkTrack == HEAL or atkTrack == PETSOS:
                targetId = targetList[currTarget]
                toonTarget = 1
            else:
                targetId = targetList[currTarget].getDoId()
            if atkTrack == LURE:
                # TODO: add flag for lure immunity
                if targetList[currTarget].hasStatusEffect('ttrealms:volcanic_cycle'):
                    if not self.combatantDead(targetId, toon=toonTarget):
                        validTargetAvail = 1
                    continue
                if self.getSuitTrapType(targetId) == NO_TRAP:
                    if self.notify.getDebug():
                        self.notify.debug('Suit lured, but no trap exists')
                    if self.SUITS_UNLURED_IMMEDIATELY:
                        if not self.suitIsLured(targetId, prevRound=1):
                            if not self.combatantDead(targetId, toon=toonTarget):
                                validTargetAvail = 1
                            toon = self.battle.getToon(toonId)
                            cog = targetList[currTarget]
                            # TODO: INSTEAD CHECK IF THE COG HAS A LURE RESISTANCE
                            # TENURE WHEN ADDED/REMOVED SHOULD CHANGE THIS FLAG
                            if cog.hasStatusEffect('ttrealms:tenure'):
                                rounds = 1
                            elif cog.hasStatusEffect('ttrealms:bribed'):
                                rounds = 2
                            else:
                                rounds = getAvPropDamage(atkTrack, atkLevel, toon.experience.getExp(atkTrack), 0, 0, self.propAndOrganicBonusStack)
                            wakeupChance = 100 - atkAcc * 2
                            npcLurer = attack.getTrack() == NPCSOS
                            currLureId = self.__addLuredSuitInfo(targetId, -1, rounds, wakeupChance, toonId, atkLevel, lureId=currLureId, npc=npcLurer)
                            if self.notify.getDebug():
                                self.notify.debug('Suit lured for ' + str(rounds) + ' rounds max with ' + str(wakeupChance) + '% chance to wake up each round')
                            targetLured = 1
                else:
                    attackTrack = TRAP
                    if targetId in self.traps:
                        trapInfo = self.traps[targetId]
                        attackLevel = trapInfo[0]
                    else:
                        attackLevel = NO_TRAP
                    attackDamage = self.getToonAttackDamage(self.__suitTrapDamage(targetId), attackTrack, targetId)
                    trapCreatorId = self.__trapCreator(targetId)
                    if trapCreatorId > 0:
                        self.notify.debug('Giving trap EXP to toon ' + str(trapCreatorId))
                        self.__addAttackExp(attack, track=TRAP, level=attackLevel, attackerId=trapCreatorId)
                    self.__clearTrapCreator(trapCreatorId, targetId)
                    lureDidDamage = 1
                    if self.notify.getDebug():
                        self.notify.debug('Suit lured right onto a trap! (' + str(AvProps[attackTrack][attackLevel]) + ',' + str(attackLevel) + ')')
                    if not self.combatantDead(targetId, toon=toonTarget):
                        validTargetAvail = 1
                    targetLured = 1
                if not self.SUITS_UNLURED_IMMEDIATELY:
                    if not self.suitIsLured(targetId, prevRound=1):
                        if not self.combatantDead(targetId, toon=toonTarget):
                            validTargetAvail = 1
                        toon = self.battle.getToon(toonId)
                        cog = targetList[currTarget]
                        # TODO: INSTEAD CHECK IF THE COG HAS A LURE RESISTANCE
                        # TENURE WHEN ADDED/REMOVED SHOULD CHANGE THIS FLAG
                        if cog.hasStatusEffect('ttrealms:tenure'):
                            rounds = 1
                        elif cog.hasStatusEffect('ttrealms:bribed'):
                            rounds = 2
                        else:
                            rounds = getAvPropDamage(LURE, atkLevel, toon.experience.getExp(LURE), 0, 0, self.propAndOrganicBonusStack) 
                        wakeupChance = 100 - atkAcc * 2
                        npcLurer = attack.getTrack() == NPCSOS
                        currLureId = self.__addLuredSuitInfo(targetId, -1, rounds, wakeupChance, toonId, atkLevel, lureId=currLureId, npc=npcLurer)
                        if self.notify.getDebug():
                            self.notify.debug('Suit lured for ' + str(rounds) + ' rounds max with ' + str(wakeupChance) + '% chance to wake up each round')
                        targetLured = 1
                    if attackLevel != -1:
                        self.__addLuredSuitsDelayed(toonId, targetId)
                if targetLured and (targetId not in self.successfulLures or targetId in self.successfulLures and self.successfulLures[targetId][1] < atkLevel):
                    self.notify.debug('Adding target ' + str(targetId) + ' to successfulLures list')
                    self.successfulLures[targetId] = [
                     toonId, atkLevel, atkAcc, -1]
            else:
                if atkTrack == TRAP:
                    npcDamage = 0
                    if attack.getTrack() == NPCSOS:
                        npcDamage = atkHp
                    if self.CLEAR_MULTIPLE_TRAPS:
                        if self.getSuitTrapType(targetId) != NO_TRAP:
                            self.__clearAttack(toonId)
                            return
                    if atkLevel == UBER_GAG_LEVEL_INDEX:
                        self.__addSuitGroupTrap(targetId, atkLevel, toonId, targetList, npcDamage)
                        if self.suitIsLured(targetId):
                            self.notify.debug('Train Trap on lured suit %d, \n indicating with KBBONUS_COL flag' % targetId)
                            tgtPos = self.battle.activeSuits.index(targetList[currTarget])
                            attack.getKbBonus()[tgtPos] = self.KBBONUS_LURED_FLAG
                    else:
                        self.__addSuitTrap(targetId, atkLevel, toonId, npcDamage)
                elif self.suitIsLured(targetId) and atkTrack == SOUND:
                    self.notify.debug('Sound on lured suit, ' + 'indicating with KBBONUS_COL flag')
                    tgtPos = self.battle.activeSuits.index(targetList[currTarget])
                    attack.getKbBonus()[tgtPos] = self.KBBONUS_LURED_FLAG
                attackLevel = atkLevel
                attackTrack = atkTrack
                toon = self.battle.getToon(toonId)
                if attack.getTrack() == NPCSOS and lureDidDamage != 1 or attack.getTrack() == PETSOS:
                    attackDamage = self.getToonAttackDamage(atkHp, attackTrack, targetId)
                elif atkTrack == FIRE:
                    suit = self.battle.findSuit(targetId)
                    if suit:
                        costToFire = 1
                        abilityToFire = toon.getPinkSlips()
                        toon.removePinkSlips(costToFire)
                        if costToFire > abilityToFire:
                            commentStr = 'Toon attempting to fire a %s cost cog with %s pinkslips' % (costToFire, abilityToFire)
                            simbase.air.writeServerEvent('suspicious', toonId, commentStr)
                            dislId = toon.DISLid
                            simbase.air.banManager.ban(toonId, dislId, commentStr)
                            print('Not enough PinkSlips to fire cog - print a warning here')
                        else:
                            suit.skeleRevives = 0
                            attackDamage = suit.getHP()
                    else:
                        attackDamage = 0
                    bonus = 0
                else:
                    organicBonus = toon.checkGagBonus(attackTrack, attackLevel)
                    propBonus = self.__checkPropBonus(attackTrack)
                    attackDamage = getAvPropDamage(attackTrack, attackLevel, toon.experience.getExp(attackTrack), organicBonus, propBonus, self.propAndOrganicBonusStack)
                    attackDamage = self.getToonAttackDamage(attackDamage, attackTrack, targetId)
                if not self.combatantDead(targetId, toon=toonTarget):
                    if self.suitIsLured(targetId) and atkTrack == DROP and not toon.getAlwaysHitSuits():
                        self.notify.debug('not setting validTargetAvail, since drop on a lured suit')
                    else:
                        validTargetAvail = 1
            if attackLevel == -1 and not atkTrack == FIRE:
                result = LURE_SUCCEEDED
            elif atkTrack != TRAP:
                toon = self.battle.getToon(toonId)
                if toon and toon.getInstaKill() and atkTrack not in (HEAL, PETSOS):
                    targetSuit = self.battle.findSuit(targetId)
                    for target in targetList:
                        if target.getHP() > targetSuit.getHP():
                            targetSuit = target
                    attackDamage = targetSuit.getHP()
                result = attackDamage
                if atkTrack == HEAL:
                    if not self.__attackHasHit(attack, suit=0):
                        result = result * 0.2
                    if self.notify.getDebug():
                        self.notify.debug('toon does ' + str(result) + ' healing to toon(s)')
                else:
                    if self.suitIsLured(targetId) and atkTrack == DROP and not toon.getAlwaysHitSuits():
                        result = 0
                        self.notify.debug('setting damage to 0, since drop on a lured suit')
                    if self.notify.getDebug():
                        self.notify.debug('toon does ' + str(result) + ' damage to suit')
            else:
                result = 0
            if result != 0 or atkTrack == PETSOS:
                targets = self.__getToonTargets(attack)
                if targetList[currTarget] not in targets:
                    if self.notify.getDebug():
                        self.notify.debug('Target of toon is not accessible!')
                    continue
                targetIndex = targets.index(targetList[currTarget])
                if atkTrack == HEAL:
                    result = result / len(targetList)
                    if self.notify.getDebug():
                        self.notify.debug('Splitting heal among ' + str(len(targetList)) + ' targets')
                if targetId in self.successfulLures and atkTrack == LURE:
                    self.notify.debug('Updating lure damage to ' + str(result))
                    self.successfulLures[targetId][3] = result
                else:
                    attack.getHp()[targetIndex] = result
                if result > 0 and atkTrack != HEAL and atkTrack != DROP and atkTrack != PETSOS:
                    attackTrack = LURE
                    lureInfos = self.__getLuredExpInfo(targetId)
                    for currInfo in lureInfos:
                        if currInfo[3]:
                            self.notify.debug('Giving lure EXP to toon ' + str(currInfo[0]))
                            self.__addAttackExp(attack, track=attackTrack, level=currInfo[1], attackerId=currInfo[0])
                        self.__clearLurer(currInfo[0], lureId=currInfo[2])

        if lureDidDamage:
            if self.itemIsCredit(atkTrack, atkLevel):
                self.notify.debug('Giving lure EXP to toon ' + str(toonId))
                self.__addAttackExp(attack)
        if not validTargetAvail and self.__prevAtkTrack(toonId) != atkTrack:
            self.__clearAttack(toonId)

    def __getToonTargets(self, attack):
        track = self.__getActualTrack(attack)
        if track == HEAL or track == PETSOS:
            return self.battle.activeToons
        else:
            return self.battle.activeSuits

    def __attackHasHit(self, attack, suit=0):
        if suit == 1:
            for dmg in attack.getHp():
                if dmg > 0:
                    return 1

            return 0
        else:
            track = self.__getActualTrack(attack)
            return not attack.getAccBonus() and track != NO_ATTACK

    def __attackDamageForTgt(self, attack, tgtPos):
        return attack.getHp()[tgtPos]

    def __calcToonAccBonus(self, attackKey):
        numPrevHits = 0
        attackIdx = self.toonAtkOrder.index(attackKey)
        for currPrevAtk in range(attackIdx - 1, -1, -1):
            attack = self.battle.toonAttacks[attackKey]
            atkTrack, atkLevel = self.__getActualTrackLevel(attack)
            prevAttackKey = self.toonAtkOrder[currPrevAtk]
            prevAttack = self.battle.toonAttacks[prevAttackKey]
            prvAtkTrack, prvAtkLevel = self.__getActualTrackLevel(prevAttack)
            if self.__attackHasHit(prevAttack) and (attackAffectsGroup(prvAtkTrack, prvAtkLevel, prevAttack.getTrack()) or attackAffectsGroup(atkTrack, atkLevel, attack.getTrack()) or attack.getTarget() == prevAttack.getTarget()) and atkTrack != prvAtkTrack:
                numPrevHits += 1

        if numPrevHits > 0 and self.notify.getDebug():
            self.notify.debug('ACC BONUS: toon attack received accuracy ' + 'bonus of ' + str(self.AccuracyBonuses[numPrevHits]) + ' from previous attack by (' + str(attack.getAttackerId()) + ') which hit')
        return getAccBonus(numPrevHits)

    def __applyToonAttackDamages(self, attack: BattleAttack, hpbonus: bool = False, kbbonus: bool = False):
        totalDamages = 0
        if not APPLY_HEALTH_ADJUSTMENTS:
            return totalDamages
        track = self.__getActualTrack(attack)
        if track != NO_ATTACK and track != SOS and track != TRAP and track != NPCSOS:
            targets = self.__getToonTargets(attack)
            for position in range(len(targets)):
                damageDone = 0
                if hpbonus and targets[position] in self.__createToonTargetList(attack):
                    damageDone += attack.getHpBonus()
                if kbbonus and targets[position] in self.__createToonTargetList(attack) and attack.getKbBonus()[position] > 0:
                    damageDone += attack.getKbBonus()[position]
                damageDone += attack.getHp()[position]
                if damageDone <= 0 or self.immortalSuits:
                    continue
                if track == HEAL or track == PETSOS:
                    currTarget = targets[position]
                    if self.CAP_HEALS:
                        toonHp = self.getToonHp(currTarget)
                        toonMaxHp = self.__getToonMaxHp(currTarget)
                        if toonHp + damageDone > toonMaxHp:
                            damageDone = toonMaxHp - toonHp
                            attack.getHp()[position] = damageDone
                    self.toonHPAdjusts[currTarget] += damageDone
                    totalDamages = totalDamages + damageDone
                    continue
                currTarget = targets[position]
                if currTarget.reviveTrack == track:
                    return
                currTarget.setHP(currTarget.getHP() - damageDone)
                targetId = currTarget.getDoId()
                totalDamages = totalDamages + damageDone
                if currTarget.getHP() <= 0:
                    if currTarget.getSkeleRevives() >= 1:
                        currTarget.useSkeleRevive(track)
                        attack.setTgtRevive(attack.getTgtRevive() | 1 << position)
                        if currTarget.hasStatusEffect('ttrealms:reorganize'):
                            self.battle.setNewRoundSpeed(5.0)
                    else:
                        self.suitLeftBattle(currTarget)
                        attack.setTgtDied(attack.getTgtDied() | 1 << position)
                        if self.notify.getDebug():
                            self.notify.debug('Suit' + str(targetId) + 'bravely expired in combat')
                        self.battle.sendBattleMsg(BATTLE_MSG_COG_DIED, self.battle.getDoId(), [targetId])

        return totalDamages

    def combatantDead(self, avId, toon):
        if toon:
            if self.getToonHp(avId) <= 0:
                return 1
        else:
            suit = self.battle.findSuit(avId)
            if suit.getHP() <= 0:
                return 1
        return 0

    def __addAttackExp(self, attack, track = -1, level = -1, attackerId = -1):
        trk = -1
        lvl = -1
        id = -1
        if track != -1 and level != -1 and attackerId != -1:
            trk = track
            lvl = level
            id = attackerId
        elif self.__attackHasHit(attack):
            if self.notify.getDebug():
                self.notify.debug('Attack ' + repr(attack) + ' has hit')
            trk = attack.getTrack()
            lvl = attack.getLevel()
            id = attack.getAttackerId()
        if trk != -1 and trk != NPCSOS and trk != PETSOS and lvl != -1 and id != -1:
            expList = self.toonSkillPtsGained.get(id, None)
            if expList == None:
                expList = [0,
                 0,
                 0,
                 0,
                 0,
                 0,
                 0]
                self.toonSkillPtsGained[id] = expList
            expCap = ServerSettings.PerBattleGagExperienceLimit.get()
            expList[trk] = min(expCap, expList[trk] + (lvl + 1) * self.__skillCreditMultiplier)

    def __clearTgtDied(self, tgt, lastAtk, currAtk):
        position = self.battle.activeSuits.index(tgt)
        currAtkTrack = self.__getActualTrack(currAtk)
        lastAtkTrack = self.__getActualTrack(lastAtk)
        if currAtkTrack == lastAtkTrack and lastAtk.getTgtDied() & 1 << position and self.__attackHasHit(currAtk, suit=0):
            if self.notify.getDebug():
                self.notify.debug('Clearing suit died for ' + str(tgt.getDoId()) + ' at position ' + str(position) + ' from toon attack ' + str(lastAtk.getAttackerId()) + ' and setting it for ' + str(currAtk.getAttackerId()))
            lastAtk.setTgtDied(lastAtk.getTgtDied() ^ 1 << position)
            self.suitLeftBattle(tgt)
            currAtk.setTgtDied(currAtk.getTgtDied() | 1 << position)

    def __addDmgToBonuses(self, attackIndex: int, hp: bool = False):
        toonId = self.toonAtkOrder[attackIndex]
        attack = self.battle.toonAttacks[toonId]
        atkTrack = self.__getActualTrack(attack)
        if atkTrack == HEAL or atkTrack == PETSOS:
            return
        tgts = self.__createToonTargetList(attack)
        for currTgt in tgts:
            doId = currTgt.getDoId()
            tgtPos = self.battle.activeSuits.index(currTgt)
            dmg = self.__attackDamageForTgt(attack, tgtPos)
            if dmg <= 0:
                return
            if hp or self.suitIsLured(doId):
                battleObj = self.battle.getBattleObjects()[doId]
                battleObj.addDmgBonus(hp, atkTrack, attack, dmg)

    def __handleBonus(self, attackIdx, hp=1, track=None):
        attackerId = self.toonAtkOrder[attackIdx]
        attack = self.battle.toonAttacks[attackerId]
        atkTrack = self.__getActualTrack(attack)
        if hp:
            if atkTrack != LURE or atkTrack != FIRE:
                self.__addDmgToBonuses(attackIdx, hp = True)
        elif self.__knockBackAtk(attackerId, toon = True, track = track):
            self.__addDmgToBonuses(attackIdx)

    def __clearAttack(self, toonId, toon=1):
        if toon:
            if self.notify.getDebug():
                self.notify.debug('clearing out toon attack for toon ' + str(toonId) + '...')
            self.battle.resetToonAttack(toonId)
            longest = max(len(self.battle.activeToons), len(self.battle.activeSuits))
            taList = self.battle.toonAttacks
            for j in range(longest):
                taList[toonId].getHp().append(-1)
                taList[toonId].getKbBonus().append(-1)
        else:
            self.notify.warning('__clearAttack not implemented for suits!')

    def __postProcessToonTrack(self, attacks: List[BattleAttack]):
        self.notify.debug('__postProcessToonTrack')
        lastAttacks = []
        atkTrack: Optional[int] = None
        for attack in attacks:
            self.battle.atkOrder.append(attack.getAttackerId())
            atkTrack, atkLevel = self.__getActualTrackLevel(attack)
            if atkTrack != HEAL and atkTrack != SOS and atkTrack != NO_ATTACK and atkTrack != NPCSOS and atkTrack != PETSOS:
                targets = self.__createToonTargetList(attack)
                for currTgt in targets:
                    damageDone = self.__attackDamageForTgt(attack, self.battle.activeSuits.index(currTgt))
                    if damageDone > 0:
                        self.battle.battleObjects[currTgt.getDoId()].rememberToonAttack(attack.getAttackerId(), atkTrack, atkLevel, damageDone)
                    if atkTrack == TRAP:
                        if currTgt.doId in self.traps:
                            trapInfo = self.traps[currTgt.doId]
                            currTgt.battleTrap = trapInfo[0]
                    if currTgt.getHP() < 0:
                        if atkTrack != LURE:
                            for currLastAtk in lastAttacks:
                                self.__clearTgtDied(currTgt, currLastAtk, attack)

                    tgtId = currTgt.getDoId()
                    if tgtId in self.successfulLures and atkTrack == LURE:
                        lureInfo = self.successfulLures[tgtId]
                        self.notify.debug('applying lure data: ' + repr(lureInfo))
                        toonId = lureInfo[0]
                        lureAtk = self.battle.toonAttacks[toonId]
                        tgtPos = self.battle.activeSuits.index(currTgt)
                        if currTgt.doId in self.traps:
                            trapInfo = self.traps[currTgt.doId]
                            if trapInfo[0] == UBER_GAG_LEVEL_INDEX:
                                self.notify.debug('train trap triggered for %d' % currTgt.doId)
                                self.trainTrapTriggered = True
                        self.__removeSuitTrap(tgtId)
                        lureAtk.getKbBonus()[tgtPos] = self.KBBONUS_TGT_LURED
                        lureAtk.getHp()[tgtPos] = lureInfo[3]
                    elif self.suitIsLured(tgtId) and atkTrack == DROP:
                        self.notify.debug('Drop on lured suit, ' + 'indicating with KBBONUS_COL ' + 'flag')
                        tgtPos = self.battle.activeSuits.index(currTgt)
                        attack.getKbBonus()[tgtPos] = self.KBBONUS_LURED_FLAG

            damagesDone = self.__applyToonAttackDamages(attack, hpbonus = True,
                kbbonus = atkTrack != LURE and atkTrack != DROP and atkTrack != SOUND and atkTrack != FIRE)
            lastAttacks.append(attack)
            if self.itemIsCredit(atkTrack, atkLevel):
                if atkTrack == TRAP or atkTrack == LURE:
                    pass
                elif atkTrack == HEAL:
                    if damagesDone != 0:
                        self.__addAttackExp(attack)
                else:
                    self.__addAttackExp(attack)
        self.battle.sendBattleMsg(BATTLE_MSG_TRACK_USED, self.battle.getDoId(), [atkTrack])

    def __clearLuredSuitsByAttack(self, attack: BattleAttack, kbBonusReq = 0, targetId = -1):
        if self.notify.getDebug():
            self.notify.debug('__clearLuredSuitsByAttack')
        if targetId != -1 and self.suitIsLured(t.getDoId()):
            self.removeLured(t.getDoId())
        else:
            tgtList = self.__createToonTargetList(attack)
            for t in tgtList:
                battleObj = self.battle.getBattleObjects()[t.getDoId()]
                if self.suitIsLured(t.getDoId()) and (not kbBonusReq or battleObj.bonusExists(hp = 0)):
                    self.removeLured(t.getDoId())
                    if self.notify.getDebug():
                        self.notify.debug('Suit %d stepping from lured spot' % t.getDoId())
                else:
                    self.notify.debug('Suit ' + str(t.getDoId()) + ' not found in currently lured suits')

    def __clearLuredSuitsDelayed(self):
        if self.notify.getDebug():
            self.notify.debug('__clearLuredSuitsDelayed')
        for t in self.delayedUnlures:
            if self.suitIsLured(t):
                self.removeLured(t)
                if self.notify.getDebug():
                    self.notify.debug('Suit %d stepping back from lured spot' % t)
            else:
                self.notify.debug('Suit ' + str(t) + ' not found in currently lured suits')

        self.delayedUnlures = []

    def __addLuredSuitsDelayed(self, toonId, targetId = -1, ignoreDamageCheck = False):
        if self.notify.getDebug():
            self.notify.debug('__addLuredSuitsDelayed')
        if targetId != -1:
            self.delayedUnlures.append(targetId)
        else:
            attack = self.battle.toonAttacks[toonId]
            tgtList = self.__createToonTargetList(attack)
            for t in tgtList:
                if self.suitIsLured(t.getDoId()) and t.getDoId() not in self.delayedUnlures and (self.__attackDamageForTgt(attack, self.battle.activeSuits.index(t)) > 0 or ignoreDamageCheck):
                    self.delayedUnlures.append(t.getDoId())

    def __calculateToonAttacks(self):
        self.notify.debug('__calculateToonAttacks()')
        currTrack = None
        self.notify.debug('Traps: ' + str(self.traps))
        maxSuitLevel = 0
        for cog in self.battle.activeSuits:
            maxSuitLevel = max(maxSuitLevel, cog.getActualLevel())

        self.creditLevel = maxSuitLevel

        attacksOfSameTrack = []
        for toonId in self.toonAtkOrder:
            if self.combatantDead(toonId, toon=1):
                if self.notify.getDebug():
                    self.notify.debug("Toon %d is dead and can't attack" % toonId)
                continue
            toon = self.battle.getToon(toonId)
            if toon.hasStatusEffect('ttrealms:fear'):
                self.__clearAttack(toonId)
            attack = self.battle.toonAttacks[toonId]
            atkTrack = self.__getActualTrack(attack)
            lastAttack = self.toonAtkOrder.index(toonId) >= len(self.toonAtkOrder) - 1
            # Process the last track if it isn't the same as this track.
            if attacksOfSameTrack:
               lastTrack = attacksOfSameTrack[0].getTrack()
               if atkTrack != lastTrack:
                   self.battle.sendBattleMsg(BATTLE_MSG_PROCESS_BONUS, self.battle.getDoId(), [lastTrack])
                   self.__postProcessToonTrack(attacksOfSameTrack)
                   attacksOfSameTrack = []
            attacksOfSameTrack.append(attack)
            if atkTrack != NO_ATTACK and atkTrack != SOS and atkTrack != NPCSOS:
                if self.notify.getDebug():
                    self.notify.debug('Calculating attack for toon: %d' % toonId)
                if self.SUITS_UNLURED_IMMEDIATELY:
                    if currTrack and atkTrack != currTrack:
                        self.__clearLuredSuitsDelayed()
                currTrack = atkTrack
                self.__calcToonAtkHp(toonId)
                attackIdx = self.toonAtkOrder.index(toonId)
                self.__handleBonus(attackIdx, hp=0, track=atkTrack if attack.getTrack() == NPCSOS else None)
                self.__handleBonus(attackIdx, hp=1, track=atkTrack if attack.getTrack() == NPCSOS else None)
                unlureAttack = self.__attackHasHit(attack, suit=0) and self.__unlureAtk(toonId, toon=1)
                if unlureAttack:
                    if lastAttack:
                        self.__clearLuredSuitsByAttack(attack)
                    else:
                        self.__addLuredSuitsDelayed(toonId)
                if lastAttack:
                    self.__clearLuredSuitsDelayed()
            # No more attacks to process, process every stored attack left
            if lastAttack:
                self.battle.sendBattleMsg(BATTLE_MSG_PROCESS_BONUS, self.battle.getDoId(), [atkTrack])
                self.__postProcessToonTrack(attacksOfSameTrack)

        if self.trainTrapTriggered:
            for suit in self.battle.activeSuits:
                suitId = suit.doId
                self.__removeSuitTrap(suitId)
                suit.battleTrap = NO_TRAP
                self.notify.debug('train trap triggered, removing trap from %d' % suitId)

    def applyAttackDamageToToon(self, attack, targetIndex, toon):
        toonId = toon.getDoId()
        if toonId in self.toonHPAdjusts:
            toonHp = toon.getHp() + self.toonHPAdjusts[toonId]
            if toonHp - attack.getHp()[targetIndex] <= 0:
                attack.setTgtDied(attack.getTgtDied() | 1 << targetIndex)
            self.toonHPAdjusts[toonId] -= attack.getHp()[targetIndex]

    def __calculateStatusAttacks(self):
        allSuitsDead = True
        for suit in self.battle.activeSuits:
            if suit.getHP() > 0:
                allSuitsDead = False
                break
        if allSuitsDead:
            return

        for suit in self.battle.activeSuits:
            if suit.hasStatusEffect('ttrealms:volcanic_cycle') and suit.getHP() > 0:
                battleObj = self.battle.battleObjects[suit.getDoId()]
                if battleObj.roundsUnderAttackState >= 3:
                    if not suit.hasStatusEffect('ttrealms:dormant'):
                        status = 'ttrealms:dormant'
                    else:
                        status = None
                elif random.random() < 0.5:
                    status = 'ttrealms:dormant'
                else:
                    status = None

                attackTrack = None
                if status == 'ttrealms:dormant':
                    if not suit.hasStatusEffect('ttrealms:dormant'):
                        battleObj.roundsUnderPreviousAttackState = battleObj.roundsUnderAttackState
                        battleObj.roundsUnderAttackState = 0
                        statusEffect = StatusEffect('ttrealms:dormant', rounds = 4)
                        suit.addStatusEffect(statusEffect)
                    attackTrack = 'ttrealms:dormant_state'
                elif suit.hasStatusEffect('ttrealms:dormant'):
                    battleObj.roundsUnderPreviousAttackState = battleObj.roundsUnderAttackState
                    battleObj.roundsUnderAttackState = 0
                    suit.removeStatusEffect('ttrealms:dormant')
                    attackTrack = 'ttrealms:active_state'

                if attackTrack is not None:
                    atk = BattleAttack()
                    atk.setAttackerId(suit.getDoId())
                    if attackTrack == 'ttrealms:active_state':
                        for toonId in self.battle.activeToons:
                            toon = self.battle.getToon(toonId)
                            if toon:
                                damage = math.ceil(toon.getHp() / 7)
                            else:
                                damage = 7
                    else:
                        damage = 1
                    atk.setHp([damage] * len(self.battle.activeToons))
                    atk.setTrack(attackTrack)
                    battleObj.attacksUsedThisRound.append(atk)
                    self.battle.atkOrder.append(suit.getDoId())
                    self.battle.cogAttackTime += SUIT_ATTACK_TIME

        burnAttack: Optional[BattleAttack] = None
        hailAttack: Optional[BattleAttack] = None
        for toonId in self.battle.activeToons:
            toon = self.battle.getToon(toonId)
            if toon:
                activeToonIdx = self.battle.activeToons.index(toonId)
                # TODO: make more datapack driven
                # WEATHER SHOULD KEEP TRACK OF THE SOURCE COG THAT SPAWNED IT
                # IF A COG SPAWNED THE WEATHER, DAMAGE CAN BE INFLUENCED
                if self.battle.getWeather() == WEATHER_HAIL and (toon.hp + self.toonHPAdjusts[toonId] >= 1):
                    if hailAttack is None:
                        hailAttack = BattleAttack(track = 'ttrealms:hail')
                        hailAttack.setHp([-1] * len(self.battle.activeToons))
                    hailAttack.getHp()[activeToonIdx] = math.ceil(toon.getMaxHp() / 16)
                    self.applyAttackDamageToToon(hailAttack, activeToonIdx, toon)
                # TODO: INSTEAD CHECK IF THE TOON HAS A BURN FLAG
                # BURN WHEN ADDED/REMOVED SHOULD CHANGE THIS FLAG
                if toon.hasStatusEffect('ttrealms:burned') and (toon.hp + self.toonHPAdjusts[toonId] >= 1):
                    if burnAttack is None:
                        burnAttack = BattleAttack(track = 'ttrealms:burn')
                        burnAttack.setHp([-1] * len(self.battle.activeToons))
                    burnAttack.getHp()[activeToonIdx] = math.ceil(toon.getMaxHp() / 8) # temporary number, status should have dmg amount applied to it
                    self.applyAttackDamageToToon(burnAttack, activeToonIdx, toon)

        if hailAttack:
            atkId = self.battle.atkAllocator.allocate()
            self.battle.statusAttacks[atkId] = hailAttack
            self.battle.atkOrder.append(atkId)
            self.battle.cogAttackTime += SUIT_ATTACK_TIME
        if burnAttack:
            atkId = self.battle.atkAllocator.allocate()
            self.battle.statusAttacks[atkId] = burnAttack
            self.battle.atkOrder.append(atkId)
            self.battle.cogAttackTime += SUIT_ATTACK_TIME

    def __knockBackAtk(self, attackIndex, toon=1, track=None):
        if not track:
            track = self.battle.toonAttacks[attackIndex].getTrack()
        if toon and (track in (THROW, SQUIRT)):
            if self.notify.getDebug():
                self.notify.debug('attack is a knockback')
            return 1
        return 0

    def __unlureAtk(self, toonId, toon=1):
        attack = self.battle.toonAttacks[toonId]
        track = self.__getActualTrack(attack)
        if toon and (track == THROW or track == SQUIRT or track == SOUND):
            if self.notify.getDebug():
                self.notify.debug('attack is an unlure')
            return 1
        return 0

    def getToonHp(self, toonDoId):
        handle = self.battle.getToon(toonDoId)
        if handle != None and toonDoId in self.toonHPAdjusts:
            return handle.hp + self.toonHPAdjusts[toonDoId]
        else:
            return 0
        return

    def __getToonMaxHp(self, toonDoId):
        handle = self.battle.getToon(toonDoId)
        if handle != None:
            return handle.maxHp
        else:
            return 0
        return

    def __updateLureTimeouts(self):
        if self.notify.getDebug():
            self.notify.debug('__updateLureTimeouts()')
            self.notify.debug('Lured suits: ' + str(self.currentlyLuredSuits))
        noLongerLured = []
        for currLuredSuit in list(self.currentlyLuredSuits.keys()):
            self.__incLuredCurrRound(currLuredSuit)
            if self.__luredMaxRoundsReached(currLuredSuit) or self.__luredWakeupTime(currLuredSuit):
                noLongerLured.append(currLuredSuit)

        for currLuredSuit in noLongerLured:
            self.removeLured(currLuredSuit)

        if self.notify.getDebug():
            self.notify.debug('Lured suits: ' + str(self.currentlyLuredSuits))

    def __initRound(self):
        self.toonHPAdjusts = {}
        for t in self.battle.activeToons:
            self.toonHPAdjusts[t] = 0

        self.battle.sendBattleMsg(BATTLE_MSG_INIT_ROUND, self.battle.getDoId())

        self.toonAtkOrder = []
        attacks = findToonAttack(self.battle.activeToons, self.battle.toonAttacks, PETSOS)
        for atk in attacks:
            self.toonAtkOrder.append(atk.getAttackerId())

        attacks = findToonAttack(self.battle.activeToons, self.battle.toonAttacks, FIRE)
        for atk in attacks:
            self.toonAtkOrder.append(atk.getAttackerId())

        passAttacks = findToonAttack(self.battle.activeToons, self.battle.toonAttacks, PASS)
        if passAttacks:
            self.battle.sendBattleMsg(BATTLE_MSG_PASS_USED, self.battle.getDoId(), [passAttacks])

        for track in self.battle.getTrackOrder():
            attacks = findToonAttack(self.battle.activeToons, self.battle.toonAttacks, track)
            if track == TRAP:
                sortedTraps = []
                for atk in attacks:
                    if atk.getTrack() == TRAP:
                        sortedTraps.append(atk)

                for atk in attacks:
                    if atk.getTrack() == NPCSOS:
                        sortedTraps.append(atk)

                attacks = sortedTraps
            for atk in attacks:
                self.toonAtkOrder.append(atk.getAttackerId())

        specials = findToonAttack(self.battle.activeToons, self.battle.toonAttacks, NPCSOS)
        toonsHit = 0
        toonsMiss = 0
        cogsHit = 0
        cogsMiss = 0
        for special in specials:
            npc_track = NPCToons.getNPCTrack(special.getTarget())
            if npc_track == NPC_TOONS_HIT:
                self.toonsAlwaysHit = 1
                toonsHit = 1
                self.battle.atkOrder.append(special.getAttackerId())
            elif npc_track == NPC_TOONS_MISS:
                self.toonsAlwaysMiss = 1
                toonsMiss = 1
            elif npc_track == NPC_COGS_HIT:
                self.suitsAlwaysHit = 1
                cogsHit = 1
            elif npc_track == NPC_COGS_MISS:
                self.suitsAlwaysMiss = 1
                cogsMiss = 1
                self.battle.atkOrder.append(special.getAttackerId())
            elif npc_track == NPC_RESTOCK_GAGS:
                self.battle.atkOrder.append(special.getAttackerId())

        if self.notify.getDebug():
            self.notify.debug('Toon attack order: ' + str(self.toonAtkOrder))
            self.notify.debug('Active toons: ' + str(self.battle.activeToons))
            self.notify.debug('Toon attacks: ' + str(self.battle.toonAttacks))
            self.notify.debug('Active suits: ' + str(self.battle.activeSuits))

        self.__updateActiveToons()
        self.delayedUnlures = []
        self.__initTraps()

        self.successfulLures = {}
        return (
         toonsHit, toonsMiss, cogsHit, cogsMiss)

    def calculateRound(self):
        longest = max(len(self.battle.activeToons), len(self.battle.activeSuits))
        for t in self.battle.activeToons:
            for j in range(longest):
                self.battle.toonAttacks[t].getHp().append(-1)
                self.battle.toonAttacks[t].getKbBonus().append(-1)

        toonsHit, toonsMiss, cogsHit, cogsMiss = self.__initRound()
        for suit in self.battle.activeSuits:
            if suit.isGenerated():
                suit.b_setHP(suit.getHP())

        for suit in self.battle.activeSuits:
            if not hasattr(suit, 'dna'):
                self.notify.warning('a removed suit is in this battle!')
                return None

        self.battle.sendBattleMsg(BATTLE_MSG_GEN_COG_ATTACK_FIRST, self.battle.getDoId())

        self.__calculateToonAttacks()
        self.__updateLureTimeouts()

        self.battle.sendBattleMsg(BATTLE_MSG_GEN_COG_ATTACK, self.battle.getDoId())

        self.__calculateStatusAttacks()

        if toonsHit == 1:
            self.toonsAlwaysHit = 0
        if toonsMiss == 1:
            self.toonsAlwaysMiss = 0
        if cogsHit == 1:
            self.suitsAlwaysHit = 0
        if cogsMiss == 1:
            self.suitsAlwaysMiss = 0

    def toonLeftBattle(self, toonId):
        if self.notify.getDebug():
            self.notify.debug('toonLeftBattle()' + str(toonId))
        if toonId in self.toonSkillPtsGained:
            del self.toonSkillPtsGained[toonId]

        self.__clearTrapCreator(toonId)
        self.__clearLurer(toonId)

    def suitLeftBattle(self, suit):
        suitId = suit.getDoId()
        if self.notify.getDebug():
            self.notify.debug('suitLeftBattle(): ' + str(suitId))
        self.removeLured(suitId)
        self.__removeSuitTrap(suitId)

        removedStatuses = list(suit.statusEffects.keys())
        suit.clearStatusEffects()
        self.battle.handleStatusesRemoved(removedStatuses)

    def __updateActiveToons(self):
        if self.notify.getDebug():
            self.notify.debug('updateActiveToons()')

        for trap in list(self.traps.keys()):
            if self.traps[trap][1] not in self.battle.activeToons:
                self.notify.debug('Trap for toon ' + str(self.traps[trap][1]) + ' will no longer give exp')
                self.traps[trap][1] = 0

    def getSkillGained(self, toonId, track):
        return BattleExperienceAI.getSkillGained(self.toonSkillPtsGained, toonId, track)

    def getLuredSuits(self):
        luredSuits = list(self.currentlyLuredSuits.keys())
        self.notify.debug('Lured suits reported to battle: ' + repr(luredSuits))
        return luredSuits

    def suitIsLured(self, suitId, prevRound=0):
        inList = suitId in self.currentlyLuredSuits
        if prevRound:
            return inList and self.currentlyLuredSuits[suitId][0] != -1
        return inList

    def __findAvailLureId(self, lurerId):
        luredSuits = list(self.currentlyLuredSuits.keys())
        lureIds = []
        for currLured in luredSuits:
            lurerInfo = self.currentlyLuredSuits[currLured][3]
            lurers = list(lurerInfo.keys())
            for currLurer in lurers:
                currId = lurerInfo[currLurer][1]
                if currLurer == lurerId and currId not in lureIds:
                    lureIds.append(currId)

        lureIds.sort()
        currId = 1
        for currLureId in lureIds:
            if currLureId != currId:
                return currId
            currId += 1

        return currId

    def __addLuredSuitInfo(self, suitId, currRounds, maxRounds, wakeChance, lurer, lureLvl, lureId=-1, npc=0):
        if lureId == -1:
            availLureId = self.__findAvailLureId(lurer)
        else:
            availLureId = lureId
        if npc == 1:
            credit = 0
        else:
            credit = self.itemIsCredit(LURE, lureLvl)
        if suitId in self.currentlyLuredSuits:
            lureInfo = self.currentlyLuredSuits[suitId]
            if lurer not in lureInfo[3]:
                lureInfo[1] += maxRounds
                if wakeChance < lureInfo[2]:
                    lureInfo[2] = wakeChance
                lureInfo[3][lurer] = [
                 lureLvl, availLureId, credit]
        else:
            lurerInfo = {lurer: [lureLvl, availLureId, credit]}
            self.currentlyLuredSuits[suitId] = [
             currRounds, maxRounds, wakeChance, lurerInfo]
        self.notify.debug('__addLuredSuitInfo: currLuredSuits -> %s' % repr(self.currentlyLuredSuits))
        return availLureId

    def __getLurers(self, suitId):
        if self.suitIsLured(suitId):
            return list(self.currentlyLuredSuits[suitId][3].keys())
        return []

    def __getLuredExpInfo(self, suitId):
        returnInfo = []
        lurers = self.__getLurers(suitId)
        if len(lurers) == 0:
            return returnInfo
        lurerInfo = self.currentlyLuredSuits[suitId][3]
        for currLurer in lurers:
            returnInfo.append([currLurer, lurerInfo[currLurer][0], lurerInfo[currLurer][1], lurerInfo[currLurer][2]])

        return returnInfo

    def __clearLurer(self, lurerId, lureId=-1):
        luredSuits = list(self.currentlyLuredSuits.keys())
        for currLured in luredSuits:
            lurerInfo = self.currentlyLuredSuits[currLured][3]
            lurers = list(lurerInfo.keys())
            for currLurer in lurers:
                if currLurer == lurerId and (lureId == -1 or lureId == lurerInfo[currLurer][1]):
                    del lurerInfo[currLurer]

    def __setLuredMaxRounds(self, suitId, rounds):
        if self.suitIsLured(suitId):
            self.currentlyLuredSuits[suitId][1] = rounds

    def __setLuredWakeChance(self, suitId, chance):
        if self.suitIsLured(suitId):
            self.currentlyLuredSuits[suitId][2] = chance

    def __incLuredCurrRound(self, suitId):
        if self.suitIsLured(suitId):
            self.currentlyLuredSuits[suitId][0] += 1

    def removeLured(self, suitId):
        if self.suitIsLured(suitId):
            del self.currentlyLuredSuits[suitId]

    def __luredMaxRoundsReached(self, suitId):
        return self.suitIsLured(suitId) and self.currentlyLuredSuits[suitId][0] >= self.currentlyLuredSuits[suitId][1]

    def __luredWakeupTime(self, suitId):
        return self.suitIsLured(suitId) and self.currentlyLuredSuits[suitId][0] > 0 and random.randint(0, 99) < self.currentlyLuredSuits[suitId][2]

    def itemIsCredit(self, track, level):
        if track == PETSOS:
            return 0
        return level < self.creditLevel

    def __getActualTrack(self, toonAttack):
        if toonAttack.getTrack() == NPCSOS:
            track = NPCToons.getNPCTrack(toonAttack.getTarget())
            if track != None:
                return track
            else:
                self.notify.warning('No NPC with id: %d' % toonAttack.getTarget())
        return toonAttack.getTrack()

    def __getActualTrackLevel(self, toonAttack):
        if toonAttack.getTrack() == NPCSOS:
            track, level, hp = NPCToons.getNPCTrackLevelHp(toonAttack.getTarget())
            if track != None:
                return (track, level)
            else:
                self.notify.warning('No NPC with id: %d' % toonAttack.getTarget())
        return (
         toonAttack.getTrack(), toonAttack.getLevel())

    def __getActualTrackLevelHp(self, toonAttack):
        if toonAttack.getTrack() == NPCSOS:
            track, level, hp = NPCToons.getNPCTrackLevelHp(toonAttack.getTarget())
            if track != None:
                return (track, level, hp)
            else:
                self.notify.warning('No NPC with id: %d' % toonAttack.getTarget())
        else:
            if toonAttack.getTrack() == PETSOS:
                trick = toonAttack.getLevel()
                petProxyId = toonAttack.getTarget()
                trickId = toonAttack.getLevel()
                if simbase.air.nerfsMode:
                    healRange = PetTricks.TrickHealsNerfs[trickId]
                else:
                    healRange = PetTricks.TrickHeals[trickId]
                hp = 0
                if petProxyId in simbase.air.doId2do:
                    petProxy = simbase.air.doId2do[petProxyId]
                    if trickId < len(petProxy.trickAptitudes):
                        aptitude = petProxy.trickAptitudes[trickId]
                        hp = int(lerp(healRange[0], healRange[1], aptitude))
                else:
                    self.notify.warning('pet proxy: %d not in doId2do!' % petProxyId)
                return (toonAttack.getTrack(), toonAttack.getLevel(), hp)
        return (
         toonAttack.getTrack(), toonAttack.getLevel(), 0)

    def __calculatePetTrickSuccess(self, toonAttack):
        petProxyId = toonAttack.getTarget()
        if petProxyId not in simbase.air.doId2do:
            self.notify.warning('pet proxy %d not in doId2do!' % petProxyId)
            toonAttack.setAccBonus(True)
            return (0, 0)
        petProxy = simbase.air.doId2do[petProxyId]
        trickId = toonAttack.getLevel()
        toonAttack.setAccBonus(petProxy.attemptBattleTrick(trickId))
        if toonAttack.getAccBonus():
            return (0, 0)
        else:
            return (1, 100)

    def calcToonEnemyAttackDamage(self, damageDict: Dict[str, Any], toon) -> int:
        damageType = damageDict.get('type', 'FIXED')
        value = damageDict.get('value', 1)
        if damageType == 'FIXED':
            result = value
        elif damageType == 'TOON_MAX_HP_PERCENTAGE':
            result = (value / 100) * toon.getMaxHp()
        return math.ceil(result)

    def getToonAttackDamage(self, baseDamage: int, track: int, targetId: int) -> int:
        if track not in (HEAL, PETSOS):
            # Grab the Cog Battle Object
            battleObj = self.battle.getBattleObjects()[targetId]
            return math.ceil(baseDamage * battleObj.getResistance(track))
        return baseDamage