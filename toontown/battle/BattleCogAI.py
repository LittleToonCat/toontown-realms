from typing import Any, Dict, List, Tuple, Optional, Union
from direct.directnotify.DirectNotifyGlobal import directNotify
from toontown.battle.StatusEffect import StatusEffect
from toontown.battle.BattleBase import *
from toontown.battle.BattleCalculatorGlobals import *
from toontown.battle.BattleObjectAI import *
from toontown.battle import SuitBattleGlobals
from toontown.toon.DistributedToonAI import DistributedToonAI
import random, math

class CogAttack:

    def __init__(self):
        self.attackMultiplier: float = 1.0
        # self.accuracyMultiplier: float = 1.0

    def setAttackAttributes(self, damage: Dict[str, Any], accuracy: int, chance: int, behaviors: List[Dict[str, Any]]):
        self.damageDict = damage
        self.baseAccuracy: int = accuracy
        self.chance: int = chance
        self.behaviors: List[CogAttackBehavior] = []
        for behaviorDict in behaviors:
            self.behaviors.append(CogAttackBehavior(self, behaviorDict))

    def getAttackMultiplier(self) -> float:
        return self.attackMultiplier

    def getDamageDict(self) -> Dict[str, Any]:
        return self.damageDict

    def getAccuracy(self) -> int:
        return self.baseAccuracy

    def getChance(self) -> int:
        return self.chance

    def handleAttackUsed(self, attack: BattleAttack, targetDamageValues: List[Tuple[DistributedToonAI, int]]):
        for behavior in self.behaviors:
            behavior.handleAttackUsed(attack, targetDamageValues)
            if behavior.getAllowedActivations() == 0:
                behaviorIndex = self.behaviors.index(behavior)
                del self.behaviors[behaviorIndex]

    def handleRoundDone(self):
        for behavior in self.behaviors:
            behavior.handleRoundDone()

class CogAttackBehavior:

    def __init__(self, cogAttack: CogAttack, behaviorDict: Dict[str, Any]):
        DirectObject.__init__(self)
        self.cogAttack = cogAttack
        self._type: str = behaviorDict.get('type', 'NORMAL')
        self._value: Any = behaviorDict.get('value', 1.0)
        self._conditions = behaviorDict.get('conditions',
            ["and",
             {"type": "HITS",
              "operator": "EQUAL_TO",
              "value": 1}
            ]
        )
        self._rounds: int = behaviorDict.get('rounds', -1)
        self._allowedActivations: int = behaviorDict.get('allowed_activations', -1)
        self._reapplyWhileActive: bool = behaviorDict.get('reapply_while_active', False)
        self.activeRounds: int = -1
        self.hits: int = 0
        self.misses: int = 0
        self.usages: int = 0
        self.localAttackMultiplier: float = 1.0

    def getAllowedActivations(self) -> int:
        return self._allowedActivations

    def doNumberOperation(self, value1: float, operator: str, value2: float) -> bool:
        if operator == 'GREATER_THAN_OR_EQUAL_TO':
            return value1 >= value2
        elif operator == 'LESS_THAN_OR_EQUAL_TO':
            return value1 <= value2
        elif operator == 'EQUAL_TO':
           return value1 == value2
        elif operator == 'LESS_THAN':
            return value1 < value2
        elif operator == 'GREATER_THAN':
            return value1 > value2
        return False

    def canApply(self, condition) -> bool:
        if isinstance(condition, list):
            logicalOperator = condition[0].lower()
            if logicalOperator == 'and':
                return all(self.canApply(subCondition) for subCondition in condition[1:])
            elif logicalOperator == 'or':
                return any(self.canApply(subCondition) for subCondition in condition[1:])
            return False
        elif isinstance(condition, dict):
            _type: str = condition.get('type', 'HITS')
            _operator: str = condition.get('operator', 'EQUAL_TO')
            _value: Union[float, str] = condition.get('value', 1)
            if _type == 'HITS':
                return self.doNumberOperation(self.hits, _operator, _value)
            elif _type == 'MISSES':
                return self.doNumberOperation(self.misses, _operator, _value)
            elif _type == 'USAGES':
                return self.doNumberOperation(self.misses, _operator, _value)
        return False


    def handleAttackUsed(self, attack: BattleAttack, targetDamageValues: List[Tuple[DistributedToonAI, int]]):
        hitAtLeastOnce: bool = False
        for target in targetDamageValues:
            if target[1] > 0:
                hitAtLeastOnce = True
                break
        self.usages += 1
        if hitAtLeastOnce:
            self.hits += 1
        else:
            self.misses += 1
        # Apply the behavior if the conditions can be met.
        inactive = self.activeRounds <= 0 or self._reapplyWhileActive
        if inactive and self.canApply(self._conditions):
            self.usages = 0
            self.hits = 0
            self.misses = 0
            if self._allowedActivations > 0:
                self._allowedActivations -= 1
            if self._rounds > 0:
                self.activeRounds = self.rounds
            if self._type == 'DAMAGE_MULTIPLY':
                self.cogAttack.attackMultiplier *= self._value
                self.localAttackMultiplier *= self._value
            elif self._type == 'APPLY_STATUS_EFFECT':
                for target in targetDamageValues:
                    if target[1] > 0:
                        toon = target[0]
                        statusType = self._value.get('status_type', None)
                        chance = self._value.get('chance', 100)
                        applied = random.randint(0, 99) < chance
                        if statusType and applied and not toon.hasStatusEffect(statusType):
                            rounds = self._value.get('rounds', 1)
                            statusEffect = StatusEffect(statusType, rounds=rounds)
                            toon.addStatusEffect(statusEffect)
                            attack.getStatus()[toon.getDoId()] = statusType

    def handleRoundDone(self):
        if self.activeRounds > 0:
            self.activeRounds -= 1
            if self.activeRounds == 0:
                if self._type == 'DAMAGE_MULTIPLY':
                    self.cogAttack.attackMultiplier /=  self.localAttackMultiplier
                    self.localAttackMultiplier = 1.0

class BattleCogAI(BattleObjectAI):
    notify = directNotify.newCategory('BattleCogAI')

    def __init__(self, battle, distObj: DistributedSuitAI):
        BattleObjectAI.__init__(self, battle, distObj)
        self.roundsUnderAttackState: int = 0
        self.roundsUnderPreviousAttackState: int = 0
        self.attackers: Dict[int, Tuple[int, int, int]] = {}
        self.attacks: Dict[str, CogAttack] = {}
        self.attacksUsedThisRound: List[BattleAttack] = []
        self.attackQueue: int = 0
        self.numSuitsDied: int = 0
        self.setAttacks(distObj.getLevel() + 1)
        self.resetNextAttack()

    def listenForEvents(self):
        BattleObjectAI.listenForEvents(self)
        self.accept(BATTLE_MSG_INIT_ROUND % {'battleId': self.battle.getDoId()}, self.initRound)
        self.accept(BATTLE_MSG_PROCESS_BONUS % {'battleId': self.battle.getDoId()}, self.processBonuses)
        if self.distObj.hasStatusEffect('ttrealms:proactive'):
            self.accept(BATTLE_MSG_GEN_COG_ATTACK_FIRST % {'battleId': self.battle.getDoId()}, self.generateSuitAttacks)
        else:
            self.accept(BATTLE_MSG_GEN_COG_ATTACK % {'battleId': self.battle.getDoId()}, self.generateSuitAttacks)
        self.accept(BATTLE_MSG_REMOVE_ACTIVE_TOON_INDEX % {'battleId': self.battle.getDoId()}, self.removeActiveToonIndex)
        self.accept(BATTLE_MSG_RESET_NEXT_ATTACK % {'battleId': self.battle.getDoId()}, self.resetNextAttack)
        self.accept(BATTLE_MSG_COG_DIED % {'battleId': self.battle.getDoId()}, self.handleCogDied)
        self.accept(BATTLE_MSG_TRACK_USED % {'battleId': self.battle.getDoId()}, self.handleGagTrackUsed)
        self.accept(BATTLE_MSG_PASS_USED % {'battleId': self.battle.getDoId()}, self.handlePassUsed)

    def initRound(self):
        self.distObj.clearReviveFlag()
        self.attacksUsedThisRound = []
        self.resetNextAttack()
        self.attackers = {}
        self.hpBonus = {}
        self.kbBonus = {}
        if self.distObj.hasStatusEffect('ttrealms:reorganize'):
            self.battle.randomizeTrackOrderEveryRound = True
        if self.distObj.hasStatusEffect('ttrealms:gag_tax'):
            self.battle.gagTax = True

    def roundDone(self):
        for attack in list(self.attacks.values()):
            attack.handleRoundDone()
        self.roundsUnderAttackState += 1

    def setAttacks(self, level: int):
        level = str(level)
        battleAttributes = self.battle.air.datapackMgr.getCogBattleAttributes()[self.distObj.dna.name]
        for attackIdentifier, attributes in list(battleAttributes['attacks'].items()):

            def getDefaultDamage(attackAttributes) -> Dict[str, Any]:
                return attackAttributes.get('damage', {'type': 'FIXED', 'value': 4})

            def getDefaultAccuracy(attackAttributes) -> int:
                return attackAttributes.get('accuracy', 75)

            def getDefaultChance(attackAttributes) -> int:
                return attackAttributes.get('chance', 0)

            def getDefaultBehaviors(attackAttributes) -> List[Dict[str, Any]]:
                return attackAttributes.get('behaviors', [])

            if 'attributes_by_level' in attributes and level in attributes['attributes_by_level']:
                damage: Dict[str, Any] = attributes['attributes_by_level'][level].get('damage', getDefaultDamage(attributes))
                accuracy: int = attributes['attributes_by_level'][level].get('accuracy', getDefaultAccuracy(attributes))
                chance: int = attributes['attributes_by_level'][level].get('chance', getDefaultChance(attributes))
                behaviors: List[Dict[str, Any]] = attributes['attributes_by_level'][level].get('behaviors', getDefaultBehaviors(attributes))
            else:
                damage: Dict[str, Any] = getDefaultDamage(attributes)
                accuracy: int = getDefaultAccuracy(attributes)
                chance: int = getDefaultChance(attributes)
                behaviors: List[Dict[str, Any]] = getDefaultBehaviors(attributes)
            if attackIdentifier not in self.attacks:
                self.attacks[attackIdentifier] = CogAttack()
            self.attacks[attackIdentifier].setAttackAttributes(damage, accuracy, chance, behaviors)

    def getNextAttack(self) -> BattleAttack:
        attack = self.attacksUsedThisRound[self.nextAttack]
        self.nextAttack += 1
        return attack

    def resetNextAttack(self):
        self.nextAttack: int = 0

    def rememberToonAttack(self, toonId: int, atkTrack: int, atkLevel: int, damage: int):
        if not self.attackers:
            self.attackers = {toonId: (atkTrack, atkLevel, damage)}
        elif toonId not in self.attackers or self.attackers[toonId][2] <= damage:
            self.attackers[toonId] = (atkTrack, atkLevel, damage)

    def suitCanAttack(self):
        if self.distObj.getReviveTrack() is not None:
            return 0
        if self.distObj.getHP() <= 0:
            return 0
        if self.battleCalc.suitIsLured(self.distObj.getDoId()):
            return 0
        if self.distObj.hasStatusEffect('ttrealms:dormant'):
            return 0
        return 1

    def generateSuitAttacks(self):
        if self.distObj.hasStatusEffect('ttrealms:avenge'):
            if self.numSuitsDied > 3:
                attackCount = 4
            else:
                attackCount = 1 + self.numSuitsDied
        else:
            attackCount = 1
        if self.suitCanAttack():
            attackCount += self.attackQueue
            self.attackQueue = 0

        for i in range(attackCount):
            self.generateSuitAttack()
        if self.distObj.hasStatusEffect('ttrealms:extra_attack'):
            self.generateSuitAttack(alwaysHit = True)

    def getRandomCogAttack(self) -> Optional[str]:
        identifiers: List[str] = []
        weights: List[int] = []
        for atkIdentifier, attack in list(self.attacks.items()):
            chance = attack.getChance()
            if chance > 0:
                identifiers.append(atkIdentifier)
                weights.append(chance)
        if not identifiers:
            return None
        return random.choices(identifiers, weights = weights, k = 1)[0]

    def generateSuitAttack(self, alwaysHit: bool = False):
        attack = BattleAttack()

        if self.distObj not in self.battle.activeSuits:
            return
        if not self.suitCanAttack():
            return
        if self.battle.pendingSuits.count(self.distObj) > 0 or self.battle.joiningSuits.count(self.distObj) > 0:
            return
        atkType = self.getRandomCogAttack()
        if atkType is None:
            return

        attack.setAttackerId(self.distObj.getDoId())
        attack.setHp([-1] * len(self.battle.activeToons))
        attack.setTrack(atkType)
        attack.setTarget(self.__calcSuitTarget())
        if attack.getTarget() == -1:
            return

        targets = self.__createSuitTargetList(attack)
        allTargetsDead = 1
        for currTgt in targets:
            if self.battleCalc.getToonHp(currTgt) > 0:
                allTargetsDead = 0
                break

        if allTargetsDead:
            return

        self.__calcSuitAtkHp(attack, alwaysHit)

        self.attacksUsedThisRound.append(attack)
        self.battle.atkOrder.append(self.distObj.getDoId())
        self.battle.cogAttackTime += SUIT_ATTACK_TIME

    def __calcSuitTarget(self):
        if self.attackers and random.randint(0, 99) < 75:
            totalDamage = 0
            for currToon in list(self.attackers.keys()):
                totalDamage += self.attackers[currToon][2]

            dmgs = []
            for currToon in list(self.attackers.keys()):
                dmgs.append(self.attackers[currToon][2] / totalDamage * 100)

            dmgIdx = SuitBattleGlobals.pickFromFreqList(dmgs)
            if dmgIdx == None:
                toonId = self.__pickRandomToon()
            else:
                toonId = list(self.attackers.keys())[dmgIdx]
            if toonId == -1 or toonId not in self.battle.activeToons:
                return -1
            self.notify.debug('Suit attacking back at toon ' + str(toonId))
            return self.battle.activeToons.index(toonId)
        else:
            return self.__pickRandomToon()

    def __pickRandomToon(self):
        liveToons = []
        for currToon in self.battle.activeToons:
            if not self.battleCalc.combatantDead(currToon, toon=1):
                liveToons.append(self.battle.activeToons.index(currToon))

        if len(liveToons) == 0:
            self.notify.debug('No tgts avail. for suit ' + str(self.distObj.getDoId()))
            return -1
        chosen = random.choice(liveToons)
        self.notify.debug('Suit randomly attacking toon ' + str(self.battle.activeToons[chosen]))
        return chosen

    def __calcSuitAtkHp(self, attack: BattleAttack, alwaysHit: bool):
        targetList = self.__createSuitTargetList(attack)
        atkType = attack.getTrack()
        damageDict = self.attacks[atkType].getDamageDict()
        attackMult: float = self.attacks[atkType].getAttackMultiplier()
        targetDmgValues = []
        for currTarget in range(len(targetList)):
            toonId = targetList[currTarget]
            toon = self.battle.getToon(toonId)
            result = 0
            if toon and toon.getCogsAlwaysMiss():
                result = 0
            elif toon and toon.immortalMode:
                result = 1
            elif TOONS_TAKE_NO_DAMAGE:
                result = 0

            if toon and toon.getCogsAlwaysMiss():
                atkHit = 0
            elif toon and toon.immortalMode:
                atkHit = 0
            elif toon and toon.getCogsAlwaysHit():
                atkHit = 1
            elif alwaysHit:
                atkHit = 1
            elif self.distObj.hasStatusEffect('ttrealms:volcanic_cycle'):
                atkHit = 1
            else:
                atkHit = self.__suitAtkHit(attack)
                
            if atkHit:
                result = math.ceil(self.battleCalc.calcToonEnemyAttackDamage(damageDict, toon) * attackMult)
                # TODO: allow this to be defined by json
                if self.distObj.hasStatusEffect('ttrealms:bribed'):
                    result = math.ceil(result * 1.1)
                if self.distObj.hasStatusEffect('ttrealms:boiling_point'):
                    hp = self.distObj.getHP()
                    if hp > self.distObj.maxHP:
                        hp = self.distObj.maxHP
                    # Scales up to 3x the normal damage
                    healthPercentageMissing = 1 - (hp / self.distObj.maxHP)
                    result = math.ceil(result * (1 + (2 * healthPercentageMissing)))
                if self.distObj.hasStatusEffect('ttrealms:volcanic_cycle') and self.roundsUnderPreviousAttackState >= 1:
                    attackDamageMult = min(self.roundsUnderPreviousAttackState + 1, 4)
                    result *= attackDamageMult
                if self.distObj.hasStatusEffect('ttrealms:power_spot'):
                    powerSpotCount = self.battle.powerSpotCount - 1
                else:
                    powerSpotCount = self.battle.powerSpotCount
                if powerSpotCount >= 1:
                    result = math.ceil(result * pow(1.3, powerSpotCount))
                if result > 32767:
                    result = 32767
                elif result < -32768:
                    result = -32768
                targetDmgValues.append((toon, result))
            targetIndex = self.battle.activeToons.index(toonId)
            attack.getHp()[targetIndex] = result
            if atkHit and APPLY_HEALTH_ADJUSTMENTS:
                self.battleCalc.applyAttackDamageToToon(attack, targetIndex, toon)
        self.attacks[atkType].handleAttackUsed(attack, targetDmgValues)

    def __suitAtkHit(self, attack: BattleAttack):
        if self.battleCalc.suitsAlwaysHit:
            return 1
        elif self.battleCalc.suitsAlwaysMiss:
            return 0
        atkType = attack.getTrack()
        accuracy = self.attacks[atkType].getAccuracy()
        randChoice = random.randint(0, 99)
        if self.notify.getDebug():
            self.notify.debug('Suit attack rolled ' + str(randChoice) + ' to hit with an accuracy of ' + str(accuracy))
        if randChoice < accuracy:
            return 1
        return 0

    def __createSuitTargetList(self, attack: BattleAttack):
        targetList = []
        if attack.getTrack() == NO_ATTACK:
            self.notify.debug('No attack, no targets')
            return targetList
        debug = self.notify.getDebug()
        if not self.__suitAtkAffectsGroup(attack):
            targetList.append(self.battle.activeToons[attack.getTarget()])
            if debug:
                self.notify.debug('Suit attack is single target')
        else:
            if debug:
                self.notify.debug('Suit attack is group target')
            for currToon in self.battle.activeToons:
                if debug:
                    self.notify.debug('Suit attack will target toon' + str(currToon))
                targetList.append(currToon)

        return targetList

    def __suitAtkAffectsGroup(self, attack: BattleAttack):
        targetType = self.battle.air.datapackMgr.getCogAttackTargetType(attack.getTrack())
        return targetType != 'single'

    def bonusExists(self, hp: bool):
        if hp:
            bonusLen = len(self.hpBonus)
        else:
            bonusLen = len(self.kbBonus)

        return bonusLen > 1

    def addDmgBonus(self, hp: bool, track: int, attack: BattleAttack, dmg: int):
        if hp:
            bonusDict = self.hpBonus
        else:
            bonusDict = self.kbBonus
        if track in bonusDict:
            bonusDict[track].append([attack, dmg])
        else:
            bonusDict[track] = [[attack, dmg]]

    def processBonuses(self, track: int):
        self.processBonus(track, hp = False)
        self.processBonus(track, hp = True)

    def processBonus(self, track: int, hp: bool):
        if hp:
            bonusDict = self.hpBonus
        else:
            bonusDict = self.kbBonus

        i = self.battle.activeSuits.index(self.distObj)
        if track in bonusDict:
            if len(bonusDict[track]) > 1 or not hp and len(bonusDict[track]) > 0:
                totalDmgs = 0
                for currDmg in bonusDict[track]:
                    totalDmgs += currDmg[1]

                numDmgs = len(bonusDict[track])
                attack = bonusDict[track][numDmgs - 1][0]

                if hp:
                    attack.setHpBonus(math.ceil(totalDmgs * (getDmgBonus(numDmgs-1) * 0.01)))
                    if self.notify.getDebug():
                        self.notify.debug('Applying hp bonus to track ' + str(attack.getTrack()) + ' of ' + str(attack.getHpBonus()))
                elif len(attack.getKbBonus()) > i:
                    kbBonus = attack.getKbBonus()
                    kbBonus[i] = math.ceil(totalDmgs * 0.5)
                    if self.notify.getDebug():
                        self.notify.debug('Applying kb bonus to track ' + str(attack.getTrack()) + ' of ' + str(kbBonus[i]) + ' to target ' + str(i))
                else:
                    self.notify.warning('invalid index for knock back bonus: %d' % i)

    def removeActiveToonIndex(self, toonId: int):
        activeToonIdx = self.battle.activeToons.index(toonId)
        for atk in self.attacksUsedThisRound:
            if activeToonIdx < len(atk.getHp()):
                del atk.getHp()[activeToonIdx]
            else:
                self.notify.warning(f"suitAttack doesn't have an HP column for active toon index {activeToonIdx}")
            if toonId in atk.getStatus():
                del atk.getStatus()[toonId]

    def handleCogDied(self, diedId: int):
        if diedId != self.distObj.getDoId():
            self.numSuitsDied += 1

    def handleGagTrackUsed(self, trackId: int):
        if self.distObj.getHP() <= 0:
            return
        # TODO: use flag instead of the status
        if self.distObj.hasStatusEffect('ttrealms:frosty_reception') and trackId in (THROW, SQUIRT):
            attack: Optional[BattleAttack] = None
            for toonId, attackInfo in list(self.attackers.items()):
                atkTrack = attackInfo[0]
                if atkTrack == trackId and self.battleCalc.getToonHp(toonId) > 0:
                    if not attack:
                        attack = BattleAttack()
                        attack.setAttackerId(self.distObj.getDoId())
                        attack.setHp([-1] * len(self.battle.activeToons))
                        attack.setTrack('ttrealms:frosty_reception')
                    damage = attackInfo[2]
                    targetIndex = self.battle.activeToons.index(toonId)
                    attack.getHp()[targetIndex] = math.ceil(damage / 2)
                    toon = self.battle.getToon(toonId)
                    self.battleCalc.applyAttackDamageToToon(attack, targetIndex, toon)

            if attack:
                self.attacksUsedThisRound.append(attack)
                self.battle.atkOrder.append(self.distObj.getDoId())
                self.battle.cogAttackTime += SUIT_ATTACK_TIME
        if self.distObj.hasStatusEffect('ttrealms:steam_engine') and trackId == SQUIRT:
            for toonId, attackInfo in list(self.attackers.items()):
                atkTrack = attackInfo[0]
                if atkTrack == trackId:
                    if self.distObj.hasStatusEffect('ttrealms:dormant'):
                        if self.attackQueue < 3:
                            self.attackQueue += 1
                    else:
                        self.generateSuitAttack(alwaysHit = True)

    def handlePassUsed(self, attacks: List[BattleAttack]):
        if self.distObj.hasStatusEffect('ttrealms:retribution'):
            self.battleCalc.removeLured(self.distObj.getDoId())
            for attack in attacks:
                self.generateSuitAttack(alwaysHit = True)

    def getResistance(self, trackId: int) -> float:
        resistance = 1.0
        if self.distObj.hasStatusEffect('ttrealms:tax_evasion') and trackId != TRAP:
            maxSuitsDied = self.numSuitsDied
            if self.numSuitsDied >= 4:
                maxSuitsDied = 4
            # The attack will deal 0 damage to this Cog, meaning it will miss.
            # We calculate it here because we want Sound to hit the other Cogs.
            if random.random() <= 1 - (0.25 * maxSuitsDied):
                return 0
        if self.distObj.hasStatusEffect('ttrealms:fortification'):
            maxSuitsDied = self.numSuitsDied
            if self.numSuitsDied > 4:
                maxSuitsDied = 4
            # Cogs take 5% less damage for each cog that has died, up to 20% max.
            resistance -= 0.05 * maxSuitsDied
        if self.distObj.hasStatusEffect('ttrealms:steam_engine') and trackId == SQUIRT:
            # Squirt deals 10% more damage.
            resistance += 0.1
        if self.distObj.hasStatusEffect('ttrealms:volcanic_cycle') and self.roundsUnderAttackState >= 1 and self.distObj.hasStatusEffect('ttrealms:dormant'):
            resistance -= 0.3 * min(self.roundsUnderAttackState, 3)
        if self.distObj.hasStatusEffect('ttrealms:resistance_spot'):
            resistanceSpotCount = self.battle.resistanceSpotCount - 1
        else:
            resistanceSpotCount = self.battle.resistanceSpotCount
        if resistanceSpotCount >= 1:
            # For each Cog that has power spot aside from itself, grant +20% damage resistance
            resistance -= 0.20 * resistanceSpotCount
        if resistance <= 0:
            resistance = 0.01
        return resistance