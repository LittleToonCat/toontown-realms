import math
from typing import Dict, List, Tuple, Union, Optional
from otp.ai.AIBase import *
from direct.distributed.ClockDelta import *
from .BattleBase import *
from . import BattleCalculatorAI
from .BattleCalculatorGlobals import *
from toontown.battle.StatusEffect import StatusEffect
from toontown.toonbase.ToontownBattleGlobals import *
from .BattleWeatherGlobals import *
from panda3d.core import *
from . import BattleExperienceAI
from direct.distributed import DistributedObjectAI
from direct.fsm import ClassicFSM, State
from direct.task import Task
from direct.directnotify import DirectNotifyGlobal
from toontown.toon.DistributedToonAI import DistributedToonAI
from toontown.toon import InventoryBase
from toontown.toonbase import ToontownGlobals, ServerSettings
import random
from toontown.toon import NPCToons
from toontown.pets import DistributedPetProxyAI
from toontown.safezone.SafeZoneManagerAI import HealFrequency
from toontown.hood import ZoneUtil
from toontown.suit.DistributedSuitAI import DistributedSuitAI
from .BattleToonAI import BattleToonAI
from .BattleCogAI import BattleCogAI

class DistributedBattleBaseAI(DistributedObjectAI.DistributedObjectAI, BattleBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBattleBaseAI')

    def __init__(self, air, zoneId, finishCallback = None, maxSuits = 4, bossBattle = 0, tutorialFlag = 0, interactivePropTrackBonus = -1):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.serialNum = 0
        self.zoneId = zoneId
        self.maxSuits = maxSuits
        self.setBossBattle(bossBattle)
        self.tutorialFlag = tutorialFlag
        self.interactivePropTrackBonus = interactivePropTrackBonus
        self.finishCallback = finishCallback
        self.avatarExitEvents = []
        self.responses = {}
        self.adjustingResponses = {}
        self.joinResponses = {}
        self.adjustingSuits = []
        self.adjustingToons = []
        self.numSuitsEver = 0
        BattleBase.__init__(self)
        self.streetBattle = 1
        self.pos = Point3(0, 0, 0)
        self.initialSuitPos = Point3(0, 0, 0)
        self.toonExp = {}
        self.toonOrigQuests = {}
        self.toonItems = {}
        self.toonOrigMerits = {}
        self.toonMerits = {}
        self.toonParts = {}
        self.battleCalc = BattleCalculatorAI.BattleCalculatorAI(self, tutorialFlag)
        mult = 1 * ServerSettings.GagExperienceMultiplier.get()
        if self.air.suitInvasionManager.getInvading():
            mult *= getInvasionMultiplier()
        if self.air.holidayManager.isMoreXpHolidayRunning():
            mult *= getMoreXpHolidayMultiplier()
        self.battleCalc.setSkillCreditMultiplier(mult)
        self.fsm = None
        self.statusAttacks: Dict[int, BattleAttack] = {}
        self.clearAttacks()
        self.ignoreFaceOffDone = 0
        self.needAdjust = 0
        self.movieHasBeenMade = 0
        self.movieHasPlayed = 0
        self.rewardHasPlayed = 0
        self.movieRequested = 0
        self.ignoreResponses = 0
        self.ignoreAdjustingResponses = 0
        self.taskNames = []
        self.exitedToons = []
        self.suitsKilled = []
        self.suitsKilledThisBattle = []
        self.suitsKilledPerFloor = []
        self.suitsEncountered = []
        self.newToons = []
        self.newSuits = []
        self.numNPCAttacks = 0
        self.npcAttacks = {}
        self.pets = {}
        self.battleObjects: Dict[int, Union[BattleToonAI, BattleCogAI]] = {}
        self.fsm = ClassicFSM.ClassicFSM('DistributedBattleAI', [State.State('FaceOff', self.enterFaceOff, self.exitFaceOff, ['WaitForInput', 'Resume']),
         State.State('WaitForJoin', self.enterWaitForJoin, self.exitWaitForJoin, ['WaitForInput', 'ReservesJoining', 'Resume']),
         State.State('ReservesJoining', self.enterReservesJoining, self.exitReservesJoining, ['WaitForJoin', 'Resume']),
         State.State('WaitForInput', self.enterWaitForInput, self.exitWaitForInput, ['MakeMovie', 'Resume']),
         State.State('MakeMovie', self.enterMakeMovie, self.exitMakeMovie, ['PlayMovie', 'Resume']),
         State.State('PlayMovie', self.enterPlayMovie, self.exitPlayMovie, ['FaceOff', 'WaitForJoin', 'ReservesJoining', 'Reward', 'Resume']),
         State.State('Reward', self.enterReward, self.exitReward, ['Resume']),
         State.State('Resume', self.enterResume, self.exitResume, []),
         State.State('Off', self.enterOff, self.exitOff, ['FaceOff', 'WaitForJoin', 'ReservesJoining'])], 'Off', 'Off')
        self.joinableFsm = ClassicFSM.ClassicFSM('Joinable', [State.State('Joinable', self.enterJoinable, self.exitJoinable, ['Unjoinable']), State.State('Unjoinable', self.enterUnjoinable, self.exitUnjoinable, ['Joinable'])], 'Unjoinable', 'Unjoinable')
        self.joinableFsm.enterInitialState()
        self.runableFsm = ClassicFSM.ClassicFSM('Runable', [State.State('Runable', self.enterRunable, self.exitRunable, ['Unrunable']), State.State('Unrunable', self.enterUnrunable, self.exitUnrunable, ['Runable'])], 'Unrunable', 'Unrunable')
        self.runableFsm.enterInitialState()
        self.adjustFsm = ClassicFSM.ClassicFSM('Adjust', [State.State('Adjusting', self.enterAdjusting, self.exitAdjusting, ['NotAdjusting', 'Adjusting']), State.State('NotAdjusting', self.enterNotAdjusting, self.exitNotAdjusting, ['Adjusting'])], 'NotAdjusting', 'NotAdjusting')
        self.adjustFsm.enterInitialState()
        self.fsm.enterInitialState()
        self.startTime = globalClock.getRealTime()
        self.adjustingTimer = Timer()
        self.roundTime = CLIENT_INPUT_TIMEOUT
        self.roundSpeed: float = 1.0
        self.newRoundSpeed: Optional[float] = None
        self.atkAllocator = UniqueIdAllocator(0, 20)
        self.weather: int = WEATHER_NORMAL
        self.trackOrder: List[int] = DEFAULT_TRACK_ORDER
        self.powerSpotCount: int = 0
        self.resistanceSpotCount: int = 0

    def clearAttacks(self):
        self.cogAttackTime: int = SUIT_ATTACK_TIME
        self.atkOrder: List[int] = []
        self.toonAttacks: Dict[int, BattleAttack] = {}
        self.randomizeTrackOrderEveryRound: bool = False
        self.gagTax: bool = False
        for atkId in list(self.statusAttacks.keys()):
            self.atkAllocator.free(atkId)
        self.statusAttacks = {}

    def requestDelete(self):
        if hasattr(self, 'fsm'):
            self.fsm.request('Off')
        self.__removeTaskName(self.uniqueName('make-movie'))
        DistributedObjectAI.DistributedObjectAI.requestDelete(self)

    def delete(self):
        self.notify.debug('deleting battle')
        self.fsm.request('Off')
        self.ignoreAll()
        self.__removeAllTasks()
        del self.fsm
        del self.joinableFsm
        del self.runableFsm
        del self.adjustFsm
        self.__cleanupJoinResponses()
        self.timer.stop()
        del self.timer
        self.adjustingTimer.stop()
        del self.adjustingTimer
        self.battleCalc.cleanup()
        del self.battleCalc
        for suit in self.suits:
            del suit.battleTrap

        del self.finishCallback
        for petProxy in list(self.pets.values()):
            petProxy.requestDelete()
        for battleObj in list(self.battleObjects.values()):
            if isinstance(battleObj, BattleToonAI) and not battleObj.distObj.isDeleted():
                battleObj.distObj.clearStatusEffects()
            battleObj.destroy()
        del self.battleObjects

        DistributedObjectAI.DistributedObjectAI.delete(self)

    def pause(self):
        self.timer.stop()
        self.adjustingTimer.stop()

    def unpause(self):
        self.timer.resume()
        self.adjustingTimer.resume()

    def abortBattle(self):
        self.notify.debug('%s.abortBattle() called.' % self.doId)
        toonsCopy = self.toons[:]
        for toonId in toonsCopy:
            self.__removeToon(toonId)
            if self.fsm.getCurrentState().getName() in ['PlayMovie', 'MakeMovie']:
                self.exitedToons.append(toonId)

        self.d_setMembers()
        self.b_setState('Resume')
        self.__removeAllTasks()
        self.timer.stop()
        self.adjustingTimer.stop()

    def findSuit(self, id):
        for s in self.suits:
            if s.doId == id:
                return s

        return None

    def __removeTaskName(self, name):
        if self.taskNames.count(name):
            self.taskNames.remove(name)
            self.notify.debug('removeTaskName() - %s' % name)
            taskMgr.remove(name)

    def __removeAllTasks(self):
        for n in self.taskNames:
            self.notify.debug('removeAllTasks() - %s' % n)
            taskMgr.remove(n)

        self.taskNames = []

    def __removeToonTasks(self, toonId):
        name = self.taskName('running-toon-%d' % toonId)
        self.__removeTaskName(name)
        name = self.taskName('to-pending-av-%d' % toonId)
        self.__removeTaskName(name)

    def getLevelDoId(self):
        return 0

    def getBattleCellId(self):
        return 0

    def getPosition(self):
        self.notify.debug('getPosition() - %s' % self.pos)
        return [self.pos[0], self.pos[1], self.pos[2]]

    def getInitialSuitPos(self):
        return [self.initialSuitPos[0], self.initialSuitPos[1], self.initialSuitPos[2]]

    def setBossBattle(self, bossBattle):
        self.bossBattle = bossBattle

    def getBossBattle(self):
        return self.bossBattle

    def b_setState(self, state):
        self.notify.debug('network:setState(%s)' % state)
        stime = globalClock.getRealTime() + SERVER_BUFFER_TIME
        self.sendUpdate('setState', [state, globalClockDelta.localToNetworkTime(stime)])
        self.setState(state)

    def setState(self, state):
        self.fsm.request(state)

    def getState(self):
        return [self.fsm.getCurrentState().getName(), globalClockDelta.getRealNetworkTime()]

    def d_setMembers(self):
        self.notify.debug('network:setMembers()')
        self.sendUpdate('setMembers', self.getMembers())

    def getMembers(self):
        suits = []
        for s in self.suits:
            suits.append(s.doId)

        joiningSuits = ''
        for s in self.joiningSuits:
            joiningSuits += str(suits.index(s.doId))

        pendingSuits = ''
        for s in self.pendingSuits:
            pendingSuits += str(suits.index(s.doId))

        activeSuits = ''
        for s in self.activeSuits:
            activeSuits += str(suits.index(s.doId))

        luredSuits = ''
        for s in self.luredSuits:
            luredSuits += str(suits.index(s.doId))

        suitTraps = ''
        for s in self.suits:
            if s.battleTrap == NO_TRAP:
                suitTraps += '9'
            elif s.battleTrap == BattleCalculatorAI.BattleCalculatorAI.TRAP_CONFLICT:
                suitTraps += '9'
            else:
                suitTraps += str(s.battleTrap)

        toons = []
        for t in self.toons:
            toons.append(t)

        joiningToons = ''
        for t in self.joiningToons:
            joiningToons += str(toons.index(t))

        pendingToons = ''
        for t in self.pendingToons:
            pendingToons += str(toons.index(t))

        activeToons = ''
        for t in self.activeToons:
            activeToons += str(toons.index(t))

        runningToons = ''
        for t in self.runningToons:
            runningToons += str(toons.index(t))

        self.notify.debug('getMembers() - suits: %s joiningSuits: %s pendingSuits: %s activeSuits: %s luredSuits: %s suitTraps: %s toons: %s joiningToons: %s pendingToons: %s activeToons: %s runningToons: %s' % (suits,
         joiningSuits,
         pendingSuits,
         activeSuits,
         luredSuits,
         suitTraps,
         toons,
         joiningToons,
         pendingToons,
         activeToons,
         runningToons))
        return [suits,
         joiningSuits,
         pendingSuits,
         activeSuits,
         luredSuits,
         suitTraps,
         toons,
         joiningToons,
         pendingToons,
         activeToons,
         runningToons,
         globalClockDelta.getRealNetworkTime()]

    def d_setPosition(self, x, y, z):
        self.sendUpdate('setPosition', [x, y, z])

    def d_adjust(self):
        self.notify.debug('network:adjust()')
        self.sendUpdate('adjust', [globalClockDelta.getRealNetworkTime()])

    def getInteractivePropTrackBonus(self):
        return self.interactivePropTrackBonus

    def getZoneId(self):
        return self.zoneId

    def getTaskZoneId(self):
        return self.zoneId

    def d_setMovie(self):
        self.notify.debug('network:setMovie()')
        self.sendUpdate('setMovie', [self.getMovie()])
        self.__updateEncounteredCogs()

    def getMovie(self):
        suitIds = []
        for s in self.activeSuits:
            suitIds.append(s.doId)

        attacks = []
        for doId in self.atkOrder:
            if doId in self.toonAttacks:
                ta = self.toonAttacks[doId]
                index = -1
                id = ta.getAttackerId()
                if id != -1:
                    index = self.activeToons.index(id)
                track = ta.getTrack()
                if (track == NO_ATTACK or attackAffectsGroup(track, ta.getLevel())) and track != NPCSOS and track != PETSOS:
                    target = -1
                    if track == HEAL:
                        if ta.getLevel() == 1:
                            ta.setHpBonus(random.randint(0, 10000))
                elif track == SOS or track == NPCSOS or track == PETSOS:
                    target = ta.getTarget()
                elif track == HEAL:
                    if self.activeToons.count(ta.getTarget()) != 0:
                        target = self.activeToons.index(ta.getTarget())
                    else:
                        target = -1
                elif suitIds.count(ta.getTarget()) != 0:
                    target = suitIds.index(ta.getTarget())
                else:
                    target = -1
                attacks.append((AVTYPE_TOON, index, str(track), ta.getLevel(), target, ta.getHp(), [], ta.getAccBonus(),
                                ta.getHpBonus(), ta.getKbBonus(), ta.getTgtDied(), ta.getTgtRevive(), ta.getTaunt()))
            elif doId in suitIds:
                battleObj = self.getBattleObjects()[doId]
                atk = battleObj.getNextAttack()
                attackerId = atk.getAttackerId()
                if attackerId == -1:
                    continue
                suitIndex = suitIds.index(attackerId)
                if not atk.getTrack():
                    targetIndex = -1
                else:
                    targetIndex = atk.getTarget()
                atk.setTaunt('')
                if atk.getTrack():
                    atk.setTaunt(self.air.datapackMgr.getCogAttackQuote(atk.getTrack()))
                attacks.append((AVTYPE_SUIT, suitIndex, atk.getTrack(), atk.getLevel(), targetIndex, atk.getHp(), 
                                atk.getStatusList(), atk.getAccBonus(), atk.getHpBonus(), atk.getKbBonus(), atk.getTgtDied(),
                                atk.getTgtRevive(), atk.getTaunt()))
            elif doId in self.statusAttacks:
                atk = self.statusAttacks[doId]
                allTargetsGone = True
                for hp in atk.getHp():
                    if hp > -1:
                        allTargetsGone = False
                        break
                if allTargetsGone:
                    return
                attacks.append((AVTYPE_STATUS, NO_ID, atk.getTrack(), atk.getLevel(), atk.getTarget(), atk.getHp(), 
                                [], atk.getAccBonus(), atk.getHpBonus(), atk.getKbBonus(), atk.getTgtDied(), atk.getTgtRevive(),
                                atk.getTaunt()))
        self.sendBattleMsg(BATTLE_MSG_RESET_NEXT_ATTACK, self.getDoId())
        return (self.movieHasBeenMade, self.activeToons, suitIds, attacks)

    def resetToonAttack(self, toonId: int, track: int = NO_ID, level: int = -1, target: int = -1):
        if toonId in self.toonAttacks:
            self.toonAttacks[toonId].resetAttack(toonId, track, level, target)
            return self.toonAttacks[toonId]
        self.toonAttacks[toonId] = BattleAttack(toonId, track, level, target)
        return self.toonAttacks[toonId]

    def d_setChosenToonAttacks(self):
        self.notify.debug('network:setChosenToonAttacks()')
        self.sendUpdate('setChosenToonAttacks', self.getChosenToonAttacks())

    def getChosenToonAttacks(self):
        ids = []
        tracks = []
        levels = []
        amounts = []
        targets = []
        for t in self.activeToons:
            if t in self.toonAttacks:
                ta = self.toonAttacks[t]
            else:
                ta = self.resetToonAttack(t)
            track = ta.getTrack()
            level = ta.getLevel()
            toon = self.getToon(t)
            if not toon or track == -1:
                amount = 0
            elif track in [HEAL, TRAP, LURE, SOUND, THROW, SQUIRT, DROP]:
                amount = toon.inventory.numItem(track, level)
            elif track == NPCSOS:
                npcId = ta.getTarget()
                npcFriendsDict = toon.getNPCFriendsDict()
                if npcId in npcFriendsDict:
                    amount = npcFriendsDict[npcId]
                else:
                    amount = 0
            elif track == FIRE:
                amount = toon.getPinkSlips()
            else:
                amount = 0
            ids.append(t)
            tracks.append(track)
            levels.append(level)
            amounts.append(amount)
            targets.append(ta.getTarget())

        return [ids,
         tracks,
         levels,
         amounts,
         targets]

    def handleStatusesRemoved(self, statusesRemoved: List[str]):
        for status in statusesRemoved:
            if status in ('ttrealms:cold_environment, ttrealms:volcanic_environment'):
                weather = WEATHER_NORMAL
                for activeSuit in self.activeSuits:
                   if activeSuit.getHP() > 0 and activeSuit.hasStatusEffect('ttrealms:cold_environment'):
                       weather = WEATHER_HAIL
                       break
                   elif weather == WEATHER_NORMAL and activeSuit.getHP() > 0 and activeSuit.hasStatusEffect('ttrealms:volcanic_environment'):
                       weather = WEATHER_ASH
                if weather != self.getWeather():
                    self.b_setWeather(weather)
            if status == 'ttrealms:under_pressure':
                revertBattleSpeed: bool = True
                for activeSuit in self.activeSuits:
                    if activeSuit.getHP() > 0 and activeSuit.hasStatusEffect('ttrealms:under_pressure'):
                        revertBattleSpeed = False
                        break
                if revertBattleSpeed:
                    # We will update the battle speed at the end of the round.
                    self.setNewRoundSpeed(1.0)
            if status == 'ttrealms:reorganize':
                revertTrackOrder = True
                for activeSuit in self.activeSuits:
                    if activeSuit.getHP() > 0 and activeSuit.hasStatusEffect('ttrealms:reorganize'):
                        randomizeTrackOrder = False
                        break
                if revertTrackOrder:
                    # the battle will revert the tracks at the end of the movie
                    self.randomizeTrackOrderEveryRound = False
            if status == 'ttrealms:power_spot':
                self.powerSpotCount -= 1
            if status == 'ttrealms:resistance_spot':
                self.resistanceSpotCount -= 1

    def d_setBattleExperience(self):
        self.notify.debug('network:setBattleExperience()')
        self.sendUpdate('setBattleExperience', self.getBattleExperience())

    def getBattleExperience(self):
        returnValue = BattleExperienceAI.getBattleExperience(4, self.activeToons, self.toonExp, self.battleCalc.toonSkillPtsGained, self.toonOrigQuests, self.toonItems, self.toonOrigMerits, self.toonMerits, self.toonParts, self.suitsKilled, self.helpfulToons)
        return returnValue

    def getToonUberStatus(self):
        fieldList = []
        uberIndex = LAST_REGULAR_GAG_LEVEL + 1
        for toon in self.activeToons:
            toonList = []
            for trackIndex in range(MAX_TRACK_INDEX):
                toonList.append(toon.inventory.numItem(track, uberIndex))

            fieldList.append(encodeUber(toonList))

        return fieldList

    def addSuit(self, suit):
        self.notify.debug('addSuit(%d)' % suit.doId)
        self.newSuits.append(suit)
        self.suits.append(suit)
        suit.battleTrap = NO_TRAP
        self.numSuitsEver += 1

    def applyEnvironmentStatusEffects(self, suitList = None):
        self.powerSpotCount = 0
        self.resistanceSpotCount = 0
        briberySuits: List[DistributedSuitAI] = []
        if not suitList:
            suitList = self.activeSuits
        for suit in suitList:
            if suit.hasStatusEffect('ttrealms:cold_environment') and self.getWeather() != WEATHER_HAIL:
                # We joined the battle.
                if hasattr(self, 'doId'):
                    self.b_setWeather(WEATHER_HAIL)
                # This is a first encounter with the Cog.
                else:
                    self.setWeather(WEATHER_HAIL)
            if suit.hasStatusEffect('ttrealms:volcanic_environment') and self.getWeather() == WEATHER_NORMAL:
                # We joined the battle.
                if hasattr(self, 'doId'):
                    self.b_setWeather(WEATHER_ASH)
                # This is a first encounter with the Cog.
                else:
                    self.setWeather(WEATHER_ASH)
            if suit.hasStatusEffect('ttrealms:under_pressure'):
                if self.getRoundSpeed() < 4.0:
                    if hasattr(self, 'doId'):
                        self.b_setRoundSpeed(4.0)
                    else:
                        self.setRoundSpeed(4.0)
            if suit.hasStatusEffect('ttrealms:bribery'):
                briberySuits.append(suit)
            if suit.hasStatusEffect('ttrealms:power_spot'):
                self.powerSpotCount += 1
            if suit.hasStatusEffect('ttrealms:resistance_spot'):
                self.resistanceSpotCount += 1
        for briberySuit in briberySuits:
            for suit in suitList:
                if suit != briberySuit and not suit.hasStatusEffect('ttrealms:bribed'): 
                    statusEffect = StatusEffect('ttrealms:bribed', -1)
                    suit.addStatusEffect(statusEffect)
                    suit.d_setStatusEffects()
                    oldHP = suit.getHP()
                    suit.b_setHP(math.ceil(oldHP * 1.25))
                    suit.sendUpdate('showDamage', [-(suit.getHP() - oldHP)])

    def addInitialSuits(self, suits: List[DistributedSuitAI]):
        for suit in suits:
            self.addSuit(suit)
        self.applyEnvironmentStatusEffects(suits)

    def addBattleObject(self, obj: Union[DistributedToonAI, DistributedSuitAI], isSuit: bool = False):
        if isSuit:
            self.activeSuits.append(obj)
            battleObj = BattleCogAI(self, obj)
        else:
            self.activeToons.append(obj.getDoId())
            battleObj = BattleToonAI(self, obj)
        self.battleObjects[obj.getDoId()] = battleObj

    def getBattleObjects(self) -> Dict[int, Union[DistributedToonAI, DistributedSuitAI]]:
        return self.battleObjects

    def __joinSuit(self, suit):
        self.joiningSuits.append(suit)
        toPendingTime = self.getTrueRoundTime() + SERVER_BUFFER_TIME
        taskName = self.taskName('to-pending-av-%d' % suit.doId)
        self.__addJoinResponse(suit.doId, taskName)
        self.taskNames.append(taskName)
        taskMgr.doMethodLater(toPendingTime, self.__serverJoinDone, taskName, extraArgs=(suit.doId, taskName))

    def __serverJoinDone(self, avId, taskName):
        self.notify.debug('join for av: %d timed out on server' % avId)
        self.__removeTaskName(taskName)
        self.__makeAvPending(avId)
        return Task.done

    def __makeAvPending(self, avId):
        self.notify.debug('__makeAvPending(%d)' % avId)
        self.__removeJoinResponse(avId)
        self.__removeTaskName(self.taskName('to-pending-av-%d' % avId))
        if self.toons.count(avId) > 0:
            self.joiningToons.remove(avId)
            self.pendingToons.append(avId)
        else:
            suit = self.findSuit(avId)
            if suit != None:
                if not suit.isEmpty():
                    if not self.joiningSuits.count(suit) == 1:
                        self.notify.warning('__makeAvPending(%d) in zone: %d' % (avId, self.zoneId))
                        self.notify.warning('toons: %s' % self.toons)
                        self.notify.warning('joining toons: %s' % self.joiningToons)
                        self.notify.warning('pending toons: %s' % self.pendingToons)
                        self.notify.warning('suits: %s' % self.suits)
                        self.notify.warning('joining suits: %s' % self.joiningSuits)
                        self.notify.warning('pending suits: %s' % self.pendingSuits)
                    self.joiningSuits.remove(suit)
                    self.pendingSuits.append(suit)
            else:
                self.notify.warning('makeAvPending() %d not in toons or suits' % avId)
                return
        self.d_setMembers()
        self.needAdjust = 1
        self.__requestAdjust()
        return

    def suitRequestJoin(self, suit):
        self.notify.debug('suitRequestJoin(%d)' % suit.getDoId())
        if self.suitCanJoin():
            self.addSuit(suit)
            self.__joinSuit(suit)
            self.d_setMembers()
            suit.prepareToJoinBattle()
            return 1
        else:
            self.notify.warning('suitRequestJoin() - not joinable - joinable state: %s max suits: %d' % (self.joinableFsm.getCurrentState().getName(), self.maxSuits))
            return 0

    def addToon(self, avId):
        self.notify.debug('addToon(%d)' % avId)
        toon = self.getToon(avId)
        if toon == None:
            return 0
        toon.stopToonUp()
        event = simbase.air.getAvatarExitEvent(avId)
        self.avatarExitEvents.append(event)
        self.accept(event, self.__handleUnexpectedExit, extraArgs=[avId])
        event = 'inSafezone-%s' % avId
        self.avatarExitEvents.append(event)
        self.accept(event, self.__handleSuddenExit, extraArgs=[avId, 0])
        self.newToons.append(avId)
        self.toons.append(avId)
        toon = simbase.air.doId2do.get(avId)
        if toon:
            # Wait if the DistributedObject still needs to generate
            if hasattr(self, 'doId'):
                waitTime = 0
            else:
                waitTime = 1
            taskMgr.doMethodLater(waitTime, self.__setAvBattleId, 'setAvBattleId', extraArgs=[toon])
        if self.fsm != None and self.fsm.getCurrentState().getName() == 'PlayMovie':
            self.responses[avId] = 1
        else:
            self.responses[avId] = 0
        self.adjustingResponses[avId] = 0
        if avId not in self.toonExp:
            p = []
            for t in Tracks:
                p.append(toon.experience.getExp(t))

            self.toonExp[avId] = p
        if avId not in self.toonOrigMerits:
            self.toonOrigMerits[avId] = toon.cogMerits[:]
        if avId not in self.toonMerits:
            self.toonMerits[avId] = [0,
             0,
             0,
             0]
        if avId not in self.toonOrigQuests:
            flattenedQuests = []
            for quest in toon.quests:
                flattenedQuests.extend(quest)

            self.toonOrigQuests[avId] = flattenedQuests
        if avId not in self.toonItems:
            self.toonItems[avId] = ([], [])
        return 1

    def __setAvBattleId(self, toon):
        toon.b_setBattleId(self.doId)
        # For boarding groups
        messageToonAdded = 'Battle adding toon %s' % self.doId
        messenger.send(messageToonAdded, [self.doId])

    def __joinToon(self, avId, pos):
        self.joiningToons.append(avId)
        toPendingTime = self.getRoundTime() + SERVER_BUFFER_TIME
        taskName = self.taskName('to-pending-av-%d' % avId)
        self.__addJoinResponse(avId, taskName, toon=1)
        taskMgr.doMethodLater(toPendingTime, self.__serverJoinDone, taskName, extraArgs=(avId, taskName))
        self.taskNames.append(taskName)

    def __updateEncounteredCogs(self):
        for toon in self.activeToons:
            if toon in self.newToons:
                for suit in self.activeSuits:
                    if hasattr(suit, 'dna'):
                        self.suitsEncountered.append({'type': suit.dna.name,
                         'activeToons': self.activeToons[:]})
                    else:
                        self.notify.warning('Suit has no DNA in zone %s: toons involved = %s' % (self.zoneId, self.activeToons))
                        return

                self.newToons.remove(toon)

        for suit in self.activeSuits:
            if suit in self.newSuits:
                if hasattr(suit, 'dna'):
                    self.suitsEncountered.append({'type': suit.dna.name,
                     'activeToons': self.activeToons[:]})
                else:
                    self.notify.warning('Suit has no DNA in zone %s: toons involved = %s' % (self.zoneId, self.activeToons))
                    return
                self.newSuits.remove(suit)

    def __makeToonRun(self, toonId, updateAttacks):
        self.activeToons.remove(toonId)
        self.battleObjects[toonId].destroy()
        del self.battleObjects[toonId]
        self.toonGone = 1
        self.runningToons.append(toonId)
        taskName = self.taskName('running-toon-%d' % toonId)
        taskMgr.doMethodLater(TOON_RUN_T, self.__serverRunDone, taskName, extraArgs=(toonId, updateAttacks, taskName))
        self.taskNames.append(taskName)

    def __serverRunDone(self, toonId, updateAttacks, taskName):
        self.notify.debug('run for toon: %d timed out on server' % toonId)
        self.__removeTaskName(taskName)
        self.__removeToon(toonId)
        self.d_setMembers()
        if len(self.toons) == 0:
            self.notify.debug('last toon is gone - battle is finished')
            self.b_setState('Resume')
        else:
            if updateAttacks == 1:
                self.d_setChosenToonAttacks()
            self.needAdjust = 1
            self.__requestAdjust()
        return Task.done

    def __requestAdjust(self):
        if not self.fsm:
            return
        cstate = self.fsm.getCurrentState().getName()
        if cstate == 'WaitForInput' or cstate == 'WaitForJoin':
            if self.adjustFsm.getCurrentState().getName() == 'NotAdjusting':
                if self.needAdjust == 1:
                    self.d_adjust()
                    self.adjustingSuits = []
                    for s in self.pendingSuits:
                        self.adjustingSuits.append(s)

                    self.adjustingToons = []
                    for t in self.pendingToons:
                        self.adjustingToons.append(t)

                    self.adjustFsm.request('Adjusting')
                else:
                    self.notify.debug('requestAdjust() - dont need to')
            else:
                self.notify.debug('requestAdjust() - already adjusting')
        else:
            self.notify.debug('requestAdjust() - in state: %s' % cstate)

    def __handleUnexpectedExit(self, avId):
        disconnectCode = self.air.getAvatarDisconnectReason(avId)
        self.notify.warning('toon: %d exited unexpectedly, reason %d' % (avId, disconnectCode))
        userAborted = disconnectCode == ToontownGlobals.DisconnectCloseWindow
        self.__handleSuddenExit(avId, userAborted)

    def __handleSuddenExit(self, avId, userAborted):
        self.__removeToon(avId, userAborted=userAborted)
        if self.fsm.getCurrentState().getName() == 'PlayMovie' or self.fsm.getCurrentState().getName() == 'MakeMovie':
            self.exitedToons.append(avId)
        self.d_setMembers()
        if len(self.toons) == 0:
            self.notify.debug('last toon is gone - battle is finished')
            self.__removeAllTasks()
            self.timer.stop()
            self.adjustingTimer.stop()
            self.b_setState('Resume')
        else:
            self.needAdjust = 1
            self.__requestAdjust()

    def __removeSuit(self, suit):
        self.notify.debug('__removeSuit(%d)' % suit.doId)
        self.suits.remove(suit)
        self.activeSuits.remove(suit)
        if self.luredSuits.count(suit) == 1:
            self.luredSuits.remove(suit)
        if suit.doId in self.battleObjects:
            self.battleObjects[suit.doId].destroy()
            del self.battleObjects[suit.doId]
        self.suitGone = 1
        del suit.battleTrap

    def __removeToon(self, toonId, userAborted = 0):
        self.notify.debug('__removeToon(%d)' % toonId)
        if self.toons.count(toonId) == 0:
            return
        self.battleCalc.toonLeftBattle(toonId)
        self.__removeToonTasks(toonId)
        self.toons.remove(toonId)
        if self.joiningToons.count(toonId) == 1:
            self.joiningToons.remove(toonId)
        if self.pendingToons.count(toonId) == 1:
            self.pendingToons.remove(toonId)
        if self.activeToons.count(toonId) == 1:
            activeToonIdx = self.activeToons.index(toonId)
            self.notify.debug('removing activeToons[%d], updating cog attacks ATK_HP_COL to match' % activeToonIdx)
            self.sendBattleMsg(BATTLE_MSG_REMOVE_ACTIVE_TOON_INDEX, self.getDoId(), [toonId])
            for atk in list(self.statusAttacks.values()):
                if activeToonIdx < len(atk.getHp()):
                    del atk.getHp()[activeToonIdx]

            self.activeToons.remove(toonId)
            if toonId in self.battleObjects:
                if not self.battleObjects[toonId].distObj.isDeleted():
                    self.battleObjects[toonId].distObj.clearStatusEffects()
                self.battleObjects[toonId].destroy()
                del self.battleObjects[toonId]
        if self.runningToons.count(toonId) == 1:
            self.runningToons.remove(toonId)
        if self.adjustingToons.count(toonId) == 1:
            self.notify.warning('removeToon() - toon: %d was adjusting!' % toonId)
            self.adjustingToons.remove(toonId)
        self.toonGone = 1
        if toonId in self.pets:
            self.pets[toonId].requestDelete()
            del self.pets[toonId]
        self.__removeResponse(toonId)
        self.__removeAdjustingResponse(toonId)
        self.__removeJoinResponses(toonId)
        event = simbase.air.getAvatarExitEvent(toonId)
        self.avatarExitEvents.remove(event)
        self.ignore(event)
        event = 'inSafezone-%s' % toonId
        self.avatarExitEvents.remove(event)
        self.ignore(event)
        toon = simbase.air.doId2do.get(toonId)
        if toon:
            # This is a case in Outskirts because battles are in the playground
            if ZoneUtil.getToonWhereName(self.zoneId) == 'playground':
                toon.startToonUp(HealFrequency)
            toon.b_setBattleId(0)
            messageToonReleased = 'Battle releasing toon %s' % toon.doId
            messenger.send(messageToonReleased, [toon.doId])
        if not userAborted:
            toon = self.getToon(toonId)
            if toon != None:
                toon.hpOwnedByBattle = 0
                toon.d_setHp(toon.hp)
                toon.d_setInventory(toon.inventory.makeNetString())
                self.air.cogPageManager.toonEncounteredCogs(toon, self.suitsEncountered, self.getTaskZoneId())
        elif len(self.suits) > 0 and not self.streetBattle:
            self.notify.info('toon %d aborted non-street battle; clearing inventory and hp.' % toonId)
            toon = DistributedToonAI(self.air)
            toon.doId = toonId
            empty = InventoryBase.InventoryBase(toon)
            toon.b_setInventory(empty.makeNetString())
            toon.b_setHp(0)
            self.notify.info('killing mem leak from temporary DistributedToonAI %d' % toonId)
            toon.deleteDummy()

    def getToon(self, toonId):
        if toonId in self.air.doId2do:
            return self.air.doId2do[toonId]
        else:
            self.notify.warning('getToon() - toon: %d not in repository!' % toonId)
        return None

    def toonRequestRun(self):
        toonId = self.air.getAvatarIdFromSender()
        if self.ignoreResponses == 1:
            self.notify.debug('ignoring response from toon: %d' % toonId)
            return
        self.notify.debug('toonRequestRun(%d)' % toonId)
        if not self.isRunable():
            self.notify.warning('toonRequestRun() - not runable')
            return
        updateAttacks = 0
        if self.activeToons.count(toonId) == 0:
            self.notify.warning('toon tried to run, but not found in activeToons: %d' % toonId)
            return
        for toon in self.activeToons:
            if toon in self.toonAttacks:
                ta = self.toonAttacks[toon]
                track = ta.getTrack()
                level = ta.getLevel()
                if ta.getTarget() == toonId or not self.air.wantSelfToonUp and track == HEAL and \
                        attackAffectsGroup(track, level) and len(self.activeToons) <= 2:
                    healerId = ta.getAttackerId()
                    self.notify.debug('resetting toon: %ds attack' % healerId)
                    self.resetToonAttack(toon, track = UN_ATTACK)
                    self.responses[healerId] = 0
                    updateAttacks = 1

        self.__makeToonRun(toonId, updateAttacks)
        self.d_setMembers()
        self.needAdjust = 1
        self.__requestAdjust()

    def toonRequestJoin(self, x, y, z):
        toonId = self.air.getAvatarIdFromSender()
        self.notify.debug('toonRequestJoin(%d)' % toonId)
        self.signupToon(toonId, x, y, z)

    def toonDied(self):
        toonId = self.air.getAvatarIdFromSender()
        self.notify.debug('toonDied(%d)' % toonId)
        if toonId in self.toons:
            toon = self.getToon(toonId)
            if toon:
                toon.hp = -1
                if ServerSettings.ClearGagInventoryOnDeath.get():
                    toon.inventory.zeroInv(1)
                if ServerSettings.ClearBossRewardInventoryOnDeath.get():
                    toon.b_setPinkSlips(0)
                    toon.b_setCogSummonsEarned([0] * 32)
                    toon.b_setResistanceMessages([])
                    toon.b_setNPCFriendsDict([])
                self.__handleSuddenExit(toonId, 0)

    def signupToon(self, toonId, x, y, z):
        if self.toons.count(toonId):
            return
        if self.toonCanJoin():
            if self.addToon(toonId):
                self.__joinToon(toonId, Point3(x, y, z))
                self.d_setMembers()
        else:
            self.notify.warning('toonRequestJoin() - not joinable')
            self.d_denyLocalToonJoin(toonId)

    def d_denyLocalToonJoin(self, toonId):
        self.notify.debug('network: denyLocalToonJoin(%d)' % toonId)
        self.sendUpdateToAvatarId(toonId, 'denyLocalToonJoin', [])

    def resetResponses(self):
        self.responses = {}
        for t in self.toons:
            self.responses[t] = 0

        self.ignoreResponses = 0

    def allToonsResponded(self):
        for t in self.toons:
            if self.responses[t] == 0:
                return 0

        self.ignoreResponses = 1
        return 1

    def __allPendingActiveToonsResponded(self):
        for t in self.pendingToons + self.activeToons:
            if self.responses[t] == 0:
                return 0

        self.ignoreResponses = 1
        return 1

    def __allActiveToonsResponded(self):
        for t in self.activeToons:
            if self.responses[t] == 0:
                return 0

        self.ignoreResponses = 1
        return 1

    def __removeResponse(self, toonId):
        del self.responses[toonId]
        if self.ignoreResponses == 0 and len(self.toons) > 0:
            currStateName = self.fsm.getCurrentState().getName()
            if currStateName == 'WaitForInput':
                if self.__allActiveToonsResponded():
                    self.notify.debug('removeResponse() - dont wait for movie')
                    self.__requestMovie()
            elif currStateName == 'PlayMovie':
                if self.__allPendingActiveToonsResponded():
                    self.notify.debug('removeResponse() - surprise movie done')
                    self.__movieDone()
            elif currStateName == 'Reward' or currStateName == 'BuildingReward':
                if self.__allActiveToonsResponded():
                    self.notify.debug('removeResponse() - surprise reward done')
                    self.handleRewardDone()

    def __resetAdjustingResponses(self):
        self.adjustingResponses = {}
        for t in self.toons:
            self.adjustingResponses[t] = 0

        self.ignoreAdjustingResponses = 0

    def __allAdjustingToonsResponded(self):
        for t in self.toons:
            if self.adjustingResponses[t] == 0:
                return 0

        self.ignoreAdjustingResponses = 1
        return 1

    def __removeAdjustingResponse(self, toonId):
        if toonId in self.adjustingResponses:
            del self.adjustingResponses[toonId]
            if self.ignoreAdjustingResponses == 0 and len(self.toons) > 0:
                if self.__allAdjustingToonsResponded():
                    self.__adjustDone()

    def __addJoinResponse(self, avId, taskName, toon = 0):
        if toon == 1:
            for jr in list(self.joinResponses.values()):
                jr[avId] = 0

        self.joinResponses[avId] = {}
        for t in self.toons:
            self.joinResponses[avId][t] = 0

        self.joinResponses[avId]['taskName'] = taskName

    def __removeJoinResponses(self, avId):
        self.__removeJoinResponse(avId)
        removedOne = 0
        for j in list(self.joinResponses.values()):
            if avId in j:
                del j[avId]
                removedOne = 1

        if removedOne == 1:
            for t in self.joiningToons:
                if self.__allToonsRespondedJoin(t):
                    self.__makeAvPending(t)

    def __removeJoinResponse(self, avId):
        if avId in self.joinResponses:
            taskMgr.remove(self.joinResponses[avId]['taskName'])
            del self.joinResponses[avId]

    def __allToonsRespondedJoin(self, avId):
        jr = self.joinResponses[avId]
        for t in self.toons:
            if jr[t] == 0:
                return 0

        return 1

    def __cleanupJoinResponses(self):
        for jr in list(self.joinResponses.values()):
            taskMgr.remove(jr['taskName'])
            del jr

    def adjustDone(self):
        toonId = self.air.getAvatarIdFromSender()
        if self.ignoreAdjustingResponses == 1:
            self.notify.debug('adjustDone() - ignoring toon: %d' % toonId)
            return
        elif self.adjustFsm.getCurrentState().getName() != 'Adjusting':
            self.notify.warning('adjustDone() - in state %s' % self.fsm.getCurrentState().getName())
            return
        elif self.toons.count(toonId) == 0:
            self.notify.warning('adjustDone() - toon: %d not in toon list' % toonId)
            return
        self.adjustingResponses[toonId] += 1
        self.notify.debug('toon: %d done adjusting' % toonId)
        if self.__allAdjustingToonsResponded():
            self.__adjustDone()

    def timeout(self):
        toonId = self.air.getAvatarIdFromSender()
        if self.ignoreResponses == 1:
            self.notify.debug('timeout() - ignoring toon: %d' % toonId)
            return
        elif self.fsm.getCurrentState().getName() != 'WaitForInput':
            self.notify.warning('timeout() - in state: %s' % self.fsm.getCurrentState().getName())
            return
        elif self.toons.count(toonId) == 0:
            self.notify.warning('timeout() - toon: %d not in toon list' % toonId)
            return
        self.resetToonAttack(toonId, track = PASS)
        self.d_setChosenToonAttacks()
        self.responses[toonId] += 1
        self.notify.debug('toon: %d timed out' % toonId)
        if self.__allActiveToonsResponded():
            self.__requestMovie(timeout=1)

    def movieDone(self):
        toonId = self.air.getAvatarIdFromSender()
        if self.ignoreResponses == 1:
            #self.notify.debug('movieDone() - ignoring toon: %d' % toonId)
            return
        elif self.fsm.getCurrentState().getName() != 'PlayMovie':
            #self.notify.warning('movieDone() - in state %s' % self.fsm.getCurrentState().getName())
            return
        elif self.toons.count(toonId) == 0:
            #self.notify.warning('movieDone() - toon: %d not in toon list' % toonId)
            return
        self.responses[toonId] += 1
        self.notify.debug('toon: %d done with movie' % toonId)
        if self.__allPendingActiveToonsResponded():
            self.__movieDone()
        else:
            self.timer.stop()
            self.timer.startCallback(TIMEOUT_PER_USER, self.__serverMovieDone)

    def rewardDone(self):
        toonId = self.air.getAvatarIdFromSender()
        stateName = self.fsm.getCurrentState().getName()
        if self.ignoreResponses == 1:
            self.notify.debug('rewardDone() - ignoring toon: %d' % toonId)
            return
        elif stateName not in ('Reward', 'BuildingReward', 'FactoryReward', 'MintReward', 'StageReward', 'CountryClubReward'):
            self.notify.warning('rewardDone() - in state %s' % stateName)
            return
        elif self.toons.count(toonId) == 0:
            self.notify.warning('rewardDone() - toon: %d not in toon list' % toonId)
            return
        self.responses[toonId] += 1
        self.notify.debug('toon: %d done with reward' % toonId)
        if self.__allActiveToonsResponded():
            self.handleRewardDone()
        else:
            self.timer.stop()
            self.timer.startCallback(TIMEOUT_PER_USER, self.serverRewardDone)

    def assignRewards(self):
        if self.rewardHasPlayed == 1:
            self.notify.debug('handleRewardDone() - reward has already played')
            return
        self.rewardHasPlayed = 1
        BattleExperienceAI.assignRewards(self.activeToons, self.battleCalc.toonSkillPtsGained, self.suitsKilled, self.getTaskZoneId(), self.helpfulToons)

    def joinDone(self, avId):
        toonId = self.air.getAvatarIdFromSender()
        if self.toons.count(toonId) == 0:
            self.notify.warning('joinDone() - toon: %d not in toon list' % toonId)
            return
        if avId not in self.joinResponses:
            self.notify.debug('joinDone() - no entry for: %d - ignoring: %d' % (avId, toonId))
            return
        jr = self.joinResponses[avId]
        if toonId in jr:
            jr[toonId] += 1
        self.notify.debug('client with localToon: %d done joining av: %d' % (toonId, avId))
        if self.__allToonsRespondedJoin(avId):
            self.__makeAvPending(avId)

    def requestAttack(self, track, level, av):
        toonId = self.air.getAvatarIdFromSender()
        if self.ignoreResponses == 1:
            self.notify.debug('requestAttack() - ignoring toon: %d' % toonId)
            return
        elif self.fsm.getCurrentState().getName() != 'WaitForInput':
            self.notify.warning('requestAttack() - in state: %s' % self.fsm.getCurrentState().getName())
            return
        elif self.activeToons.count(toonId) == 0:
            self.notify.warning('requestAttack() - toon: %d not in toon list' % toonId)
            return
        self.notify.debug('requestAttack(%d, %d, %d, %d)' % (toonId,
         track,
         level,
         av))
        toon = self.getToon(toonId)
        if toon == None:
            self.notify.warning('requestAttack() - no toon: %d' % toonId)
            return
        # TODO: CHECK IF THE BATTLE TOON IS UNABLE TO ATTACK DUE TO A STATUS EFFECT
        #       THIS ASSUMES THE STATUS EFFECT IS CALLED THIS
        if toon.hasStatusEffect('ttrealms:frozen') and track not in (SOS, PASS):
            return
        validResponse = 1
        if track == SOS:
            self.notify.debug('toon: %d calls for help' % toonId)
            self.air.writeServerEvent('friendSOS', toonId, '%s' % av)
            self.resetToonAttack(toonId, track = SOS, target = av)
        elif track == NPCSOS:
            self.notify.debug('toon: %d calls for help' % toonId)
            self.air.writeServerEvent('NPCSOS', toonId, '%s' % av)
            toon = self.getToon(toonId)
            if toon == None:
                return
            if av in toon.NPCFriendsDict:
                npcCollision = 0
                if av in self.npcAttacks:
                    callingToon = self.npcAttacks[av]
                    if self.activeToons.count(callingToon) == 1:
                        self.resetToonAttack(toonId, track = PASS)
                        npcCollision = 1
                if npcCollision == 0:
                    self.resetToonAttack(toonId, track = NPCSOS, level = 5, target = av)
                    self.numNPCAttacks += 1
                    self.npcAttacks[av] = toonId
        elif track == PETSOS:
            self.notify.debug('toon: %d calls for pet: %d' % (toonId, av))
            self.air.writeServerEvent('PETSOS', toonId, '%s' % av)
            toon = self.getToon(toonId)
            if toon == None:
                return
            if not self.validate(toonId, level in toon.petTrickPhrases, 'requestAttack: invalid pet trickId: %s' % level):
                return
            self.resetToonAttack(toonId, track = PETSOS, level = level, target = av)
        elif track == UN_ATTACK:
            self.notify.debug('toon: %d changed its mind' % toonId)
            self.resetToonAttack(toonId)
            if toonId in self.responses:
                self.responses[toonId] = 0
            validResponse = 0
        elif track == PASS:
            self.resetToonAttack(toonId)
        elif track == FIRE:
            self.resetToonAttack(toonId, track = FIRE, target = av)
        else:
            if not self.validate(toonId, track >= 0 and track <= MAX_TRACK_INDEX, 'requestAttack: invalid track %s' % track):
                return
            if not self.validate(toonId, level >= 0 and level <= MAX_LEVEL_INDEX, 'requestAttack: invalid level %s' % level):
                return
            if toon.inventory.numItem(track, level) == 0:
                self.notify.warning('requestAttack() - toon has no item track:                     %d level: %d' % (track, level))
                self.resetToonAttack(toonId)
                return
            if track == HEAL:
                if self.runningToons.count(av) == 1 or not self.air.wantSelfToonUp and \
                        attackAffectsGroup(track, level) and len(self.activeToons) < 2:
                    self.resetToonAttack(toonId, track = UN_ATTACK)
                    validResponse = 0
                else:
                    self.resetToonAttack(toonId, track = track, level = level, target = av)
            else:
                self.resetToonAttack(toonId, track = track, level = level, target = av)
                if av == -1 and not attackAffectsGroup(track, level):
                    validResponse = 0
        self.d_setChosenToonAttacks()
        if validResponse == 1:
            self.responses[toonId] += 1
        self.notify.debug('toon: %d chose an attack' % toonId)
        if self.__allActiveToonsResponded():
            self.__requestMovie()

    def requestPetProxy(self, av):
        toonId = self.air.getAvatarIdFromSender()
        if self.ignoreResponses == 1:
            self.notify.debug('requestPetProxy() - ignoring toon: %d' % toonId)
            return
        elif self.fsm.getCurrentState().getName() != 'WaitForInput':
            self.notify.warning('requestPetProxy() - in state: %s' % self.fsm.getCurrentState().getName())
            return
        elif self.activeToons.count(toonId) == 0:
            self.notify.warning('requestPetProxy() - toon: %d not in toon list' % toonId)
            return
        self.notify.debug('requestPetProxy(%s, %s)' % (toonId, av))
        toon = self.getToon(toonId)
        if toon == None:
            self.notify.warning('requestPetProxy() - no toon: %d' % toonId)
            return
        petId = toon.getPetId()
        zoneId = self.zoneId
        if petId == av:
            if toonId not in self.pets:

                def handleGetPetProxy(success, pet, petId = petId, zoneId = zoneId, toonId = toonId):
                    if success:
                        petProxy = DistributedPetProxyAI.DistributedPetProxyAI(self.air)
                        petProxy.setOwnerId(pet.getOwnerId())
                        petProxy.setPetName(pet.getPetName())
                        petProxy.setTraitSeed(pet.getTraitSeed())
                        petProxy.setSafeZone(pet.getSafeZone())
                        petProxy.setForgetfulness(pet.getForgetfulness())
                        petProxy.setBoredomThreshold(pet.getBoredomThreshold())
                        petProxy.setRestlessnessThreshold(pet.getRestlessnessThreshold())
                        petProxy.setPlayfulnessThreshold(pet.getPlayfulnessThreshold())
                        petProxy.setLonelinessThreshold(pet.getLonelinessThreshold())
                        petProxy.setSadnessThreshold(pet.getSadnessThreshold())
                        petProxy.setFatigueThreshold(pet.getFatigueThreshold())
                        petProxy.setHungerThreshold(pet.getHungerThreshold())
                        petProxy.setConfusionThreshold(pet.getConfusionThreshold())
                        petProxy.setExcitementThreshold(pet.getExcitementThreshold())
                        petProxy.setAngerThreshold(pet.getAngerThreshold())
                        petProxy.setSurpriseThreshold(pet.getSurpriseThreshold())
                        petProxy.setAffectionThreshold(pet.getAffectionThreshold())
                        petProxy.setHead(pet.getHead())
                        petProxy.setEars(pet.getEars())
                        petProxy.setNose(pet.getNose())
                        petProxy.setTail(pet.getTail())
                        petProxy.setBodyTexture(pet.getBodyTexture())
                        petProxy.setColor(pet.getColor())
                        petProxy.setColorScale(pet.getColorScale())
                        petProxy.setEyeColor(pet.getEyeColor())
                        petProxy.setGender(pet.getGender())
                        petProxy.setLastSeenTimestamp(pet.getLastSeenTimestamp())
                        petProxy.setBoredom(pet.getBoredom())
                        petProxy.setRestlessness(pet.getRestlessness())
                        petProxy.setPlayfulness(pet.getPlayfulness())
                        petProxy.setLoneliness(pet.getLoneliness())
                        petProxy.setSadness(pet.getSadness())
                        petProxy.setAffection(pet.getAffection())
                        petProxy.setHunger(pet.getHunger())
                        petProxy.setConfusion(pet.getConfusion())
                        petProxy.setExcitement(pet.getExcitement())
                        petProxy.setFatigue(pet.getFatigue())
                        petProxy.setAnger(pet.getAnger())
                        petProxy.setSurprise(pet.getSurprise())
                        petProxy.setTrickAptitudes(pet.getTrickAptitudes())
                        pet.requestDelete()

                        def handlePetDeleted(task):
                            petProxy.doNotDeallocateChannel = True
                            petProxy.generateWithRequiredAndId(petId, self.air.districtId, self.zoneId)
                            petProxy.broadcastDominantMood()
                            self.pets[toonId] = petProxy
                            return task.done

                        self.acceptOnce(self.air.getAvatarExitEvent(petId),
                                        lambda: taskMgr.doMethodLater(0, handlePetDeleted,
                                                                      self.uniqueName('pet-%s-deleted' % petId)))
                    else:
                        self.notify.warning('error generating petProxy: %s' % petId)

                self.getPetProxyObject(petId, handleGetPetProxy)
        return

    def suitCanJoin(self):
        return len(self.suits) < self.maxSuits and self.isJoinable()

    def toonCanJoin(self):
        return len(self.toons) < 4 and self.isJoinable()

    def __requestMovie(self, timeout = 0):
        if self.adjustFsm.getCurrentState().getName() == 'Adjusting':
            self.notify.debug('__requestMovie() - in Adjusting')
            self.movieRequested = 1
        else:
            movieDelay = 0
            if len(self.activeToons) == 0:
                self.notify.warning('only pending toons left in battle %s, toons = %s' % (self.doId, self.toons))
            elif len(self.activeSuits) == 0:
                self.notify.warning('only pending suits left in battle %s, suits = %s' % (self.doId, self.suits))
            elif len(self.activeToons) > 1 and not timeout:
                movieDelay = 1
            self.fsm.request('MakeMovie')
            if movieDelay:
                taskMgr.doMethodLater(0.8, self.__makeMovie, self.uniqueName('make-movie'))
                self.taskNames.append(self.uniqueName('make-movie'))
            else:
                self.__makeMovie()

    def __makeMovie(self, task = None):
        self.notify.debug('makeMovie()')
        if self._DOAI_requestedDelete:
            self.notify.warning('battle %s requested delete, then __makeMovie was called!' % self.doId)
            if hasattr(self, 'levelDoId'):
                self.notify.warning('battle %s in level %s' % (self.doId, self.levelDoId))
            return
        self.__removeTaskName(self.uniqueName('make-movie'))
        if self.movieHasBeenMade == 1:
            self.notify.debug('__makeMovie() - movie has already been made')
            return
        self.movieRequested = 0
        self.movieHasBeenMade = 1
        self.movieHasPlayed = 0
        self.rewardHasPlayed = 0
        for t in self.activeToons:
            if t not in self.toonAttacks:
                self.resetToonAttack(t)
            attack = self.toonAttacks[t]
            if attack.getTrack() == PASS or attack.getTrack() == UN_ATTACK or attack.getTarget() == -1:
                self.resetToonAttack(t, track = PASS)
            if self.toonAttacks[t].getTrack() != NO_ATTACK:
                self.addHelpfulToon(t)

        self.battleCalc.calculateRound()
        for t in self.activeToons:
            self.sendEarnedExperience(t)
            toon = self.getToon(t)
            if toon != None:
                toon.hpOwnedByBattle = 1

        self.d_setMovie()
        self.b_setState('PlayMovie')
        return Task.done

    def sendEarnedExperience(self, toonId):
        toon = self.getToon(toonId)
        if toon != None:
            expList = self.battleCalc.toonSkillPtsGained.get(toonId, None)
            if expList == None:
                toon.d_setEarnedExperience([])
            else:
                roundList = []
                for exp in expList:
                    roundList.append(int(exp + 0.5))

                toon.d_setEarnedExperience(roundList)
        return

    def enterOff(self):
        return None

    def exitOff(self):
        return None

    def enterFaceOff(self):
        return None

    def exitFaceOff(self):
        return None

    def enterWaitForJoin(self):
        self.notify.debug('enterWaitForJoin()')
        if len(self.activeSuits) > 0:
            self.b_setState('WaitForInput')
        else:
            self.notify.debug('enterWaitForJoin() - no active suits')
            self.runableFsm.request('Runable')
            self.resetResponses()
            self.__requestAdjust()
        return None

    def exitWaitForJoin(self):
        return None

    def enterReservesJoining(self, ts = 0):
        self.beginBarrier('ReservesJoining', self.toons, 15, self.__doneReservesJoining)

    def __doneReservesJoining(self, avIds):
        self.b_setState('WaitForJoin')

    def exitReservesJoining(self):
        pass

    def setRoundTime(self, roundTime):
        self.roundTime = roundTime

    def d_setRoundTime(self, roundTime):
        self.sendUpdate('setRoundTime', [roundTime])

    def b_setRoundTime(self, roundTime):
        self.setRoundTime(roundTime)
        self.d_setRoundTime(roundTime)

    def getRoundTime(self):
        return self.roundTime

    def setRoundSpeed(self, roundSpeed: float):
        self.roundSpeed = roundSpeed

    def d_setRoundSpeed(self, roundSpeed: float):
        self.sendUpdate('setRoundSpeed', [roundSpeed])
        self.setNewRoundSpeed()

    def b_setRoundSpeed(self, roundSpeed: float):
        self.setRoundSpeed(roundSpeed)
        self.d_setRoundSpeed(roundSpeed)

    def getRoundSpeed(self) -> float:
        return self.roundSpeed

    def setNewRoundSpeed(self, newRoundSpeed: Optional[float] = None):
        self.newRoundSpeed = newRoundSpeed

    def getNewRoundSpeed(self) -> Optional[float]:
        return self.newRoundSpeed

    def getTrueRoundTime(self) -> float:
        return self.getRoundTime() / self.getRoundSpeed()

    def setWeather(self, weather: int):
        self.weather = weather

    def d_setWeather(self, weather: int):
        self.sendUpdate('setWeather', [weather])

    def b_setWeather(self, weather: int):
        self.setWeather(weather)
        self.d_setWeather(weather)

    def getWeather(self) -> int:
        return self.weather

    # TODO: in the event that a cog has a different weather effect and we are removing a weather effect,
    #       set the battle weather to that weather type instead
    #       we don't have to worry about that for now.
    def attemptRemoveWeather(self, suit: Optional[DistributedSuitAI] = None):
        removeWeather: bool = True
        if suit is not None:
            for activeSuit in self.activeSuits:
               if activeSuit.getDoId() != suit.getDoId():
                   if self.getWeather() == WEATHER_HAIL and activeSuit.getHP() > 0 and activeSuit.hasStatusEffect('ttrealms:cold_environment'):
                       removeWeather = False
                       break
        if removeWeather:
            self.b_setWeather(WEATHER_NORMAL)

    def d_randomizeTrackOrder(self):
        tracks: List[int] = [HEAL_TRACK, TRAP_TRACK, SOUND_TRACK, THROW_TRACK, SQUIRT_TRACK, DROP_TRACK]
        trackOrder: List[int] = []
        while tracks != []:
            chosenTrack = random.choice(tracks)
            if chosenTrack == TRAP_TRACK:
                tracks.append(LURE_TRACK)
            tracks.remove(chosenTrack)
            trackOrder.append(chosenTrack)
        self.b_setTrackOrder(trackOrder)

    def setTrackOrder(self, trackOrder: List[int]):
        self.trackOrder = trackOrder

    def d_setTrackOrder(self, trackOrder: List[int]):
        self.sendUpdate('setTrackOrder', [trackOrder])

    def b_setTrackOrder(self, trackOrder: List[int]):
        self.setTrackOrder(trackOrder)
        self.d_setTrackOrder(trackOrder)

    def getTrackOrder(self) -> List[int]:
        return self.trackOrder

    def enterWaitForInput(self):
        self.notify.debug('enterWaitForInput()')
        self.joinableFsm.request('Joinable')
        self.runableFsm.request('Runable')
        self.resetResponses()
        self.__requestAdjust()
        if not self.tutorialFlag:
            self.timer.startCallback(self.getTrueRoundTime() + SERVER_BUFFER_TIME, self.__serverTimedOut)
        self.npcAttacks = {}
        for toonId in self.toons:
            toon = self.air.doId2do.get(toonId)
            if toon.getImmortalMode():
                toon.toonUp(toon.maxHp)
            if bboard.get('autoRestock-%s' % toonId, False):
                if toon is not None:
                    toon.doRestock(0)

        return

    def exitWaitForInput(self):
        self.npcAttacks = {}
        self.timer.stop()
        return None

    def __serverTimedOut(self):
        self.notify.debug('wait for input timed out on server')
        self.ignoreResponses = 1
        self.__requestMovie(timeout=1)

    def enterMakeMovie(self):
        self.notify.debug('enterMakeMovie()')
        self.runableFsm.request('Unrunable')
        self.resetResponses()
        return None

    def exitMakeMovie(self):
        return None

    def enterPlayMovie(self):
        self.notify.debug('enterPlayMovie()')
        self.joinableFsm.request('Joinable')
        self.runableFsm.request('Unrunable')
        self.resetResponses()
        movieTime = TOON_ATTACK_TIME * (len(self.activeToons) + self.numNPCAttacks) + self.cogAttackTime + SERVER_BUFFER_TIME
        self.numNPCAttacks = 0
        self.notify.debug('estimated upper bound of movie time: %f' % movieTime)
        self.timer.startCallback(movieTime, self.__serverMovieDone)

    def __serverMovieDone(self):
        self.notify.debug('movie timed out on server')
        self.ignoreResponses = 1
        self.__movieDone()

    def serverRewardDone(self):
        self.notify.debug('reward timed out on server')
        self.ignoreResponses = 1
        self.handleRewardDone()

    def handleRewardDone(self):
        self.b_setState('Resume')

    def exitPlayMovie(self):
        self.timer.stop()
        return None

    def handleToonHpDict(self, attack: BattleAttack, hpDict: Dict[int, Tuple[int, int, int]]):
        hps = attack.getHp()
        targetType = self.air.datapackMgr.getCogAttackTargetType(attack.getTrack())
        if targetType == 'group':
            for activeToon in self.activeToons:
                toon = self.getToon(activeToon)
                if toon != None:
                    targetIndex = self.activeToons.index(activeToon)
                    toonDied = attack.getTgtDied() & 1 << targetIndex
                    if targetIndex >= len(hps):
                        self.notify.warning('DAMAGE: toon %s is no longer in battle!' % activeToon)
                    else:
                        hp = hps[targetIndex]
                        if hp > 0:
                            self.notify.debug('DAMAGE: toon: %d hit for dmg: %d' % (activeToon, hp))
                            if toonDied != 0:
                                hpDict[toon.doId][2] = 1
                            hpDict[toon.doId][1] += hp

        elif targetType == 'single':
            targetIndex = attack.getTarget()
            if targetIndex >= len(self.activeToons):
                self.notify.warning('movieDone() - toon: %d gone!' % targetIndex)
                return
            toonId = self.activeToons[targetIndex]
            toon = self.getToon(toonId)
            toonDied = attack.getTgtDied() & 1 << targetIndex
            if targetIndex >= len(hps):
                self.notify.warning('DAMAGE: toon %s is no longer in battle!' % toonId)
            else:
                hp = hps[targetIndex]
                if hp > 0:
                    self.notify.debug('DAMAGE: toon: %d hit for dmg: %d' % (toonId, hp))
                    if toonDied != 0:
                        hpDict[toon.doId][2] = 1
                    hpDict[toon.doId][1] += hp

    def __movieDone(self):
        self.notify.debug('__movieDone() - movie is finished')
        if self.movieHasPlayed == 1:
            self.notify.debug('__movieDone() - movie had already finished')
            return
        self.movieHasBeenMade = 0
        self.movieHasPlayed = 1
        self.ignoreResponses = 1
        needUpdate = 0
        toonHpDict = {}
        for toon in self.activeToons:
            toonHpDict[toon] = [0, 0, 0]
            actualToon = self.getToon(toon)
            self.notify.debug('BEFORE ROUND: toon: %d hp: %d' % (toon, actualToon.hp))

        deadSuits = []
        trapDict = {}
        suitsLuredOntoTraps = []
        npcTrapAttacks = []
        for doId in self.atkOrder:
            if doId in self.toonAttacks:
                attack = self.toonAttacks[doId]
                track = attack.getTrack()
                npc_level = None
                if track == NPCSOS:
                    track, npc_level, npc_hp = NPCToons.getNPCTrackLevelHp(attack.getTarget())
                    if track == None:
                        track = NPCSOS
                    elif track == TRAP:
                        npcTrapAttacks.append(attack)
                        toon = self.getToon(attack.getAttackerId())
                        av = attack.getTarget()
                        if toon != None and av in toon.NPCFriendsDict:
                            toon.NPCFriendsDict[av] -= 1
                            if toon.NPCFriendsDict[av] <= 0:
                                del toon.NPCFriendsDict[av]
                            toon.d_setNPCFriendsDict(toon.NPCFriendsDict)
                        continue
                if track != NO_ATTACK:
                    toonId = attack.getAttackerId()
                    level = attack.getLevel()
                    if npc_level != None:
                        level = npc_level
                    if attack.getTrack() == NPCSOS:
                        toon = self.getToon(toonId)
                        av = attack.getTarget()
                        if toon != None and av in toon.NPCFriendsDict:
                            toon.NPCFriendsDict[av] -= 1
                            if toon.NPCFriendsDict[av] <= 0:
                                del toon.NPCFriendsDict[av]
                            toon.d_setNPCFriendsDict(toon.NPCFriendsDict)
                    elif track == PETSOS:
                        pass
                    elif track == FIRE:
                        pass
                    elif track != SOS:
                        toon = self.getToon(toonId)
                        if toon != None and not toon.getUnlimitedGags():
                            check = toon.inventory.useItem(track, level)
                            # Use the item again if the gag tax is active.
                            if self.gagTax:
                                toon.inventory.useItem(track, level)
                            if check == -1:
                                self.air.writeServerEvent('suspicious', toonId, 'Toon generating movie for non-existant gag track %s level %s' % (track, level))
                                self.notify.warning('generating movie for non-existant gag track %s level %s! avId: %s' % (track, level, toonId))
                            toon.d_setInventory(toon.inventory.makeNetString())
                    hps = attack.getHp()
                    if track == SOS:
                        self.notify.debug('toon: %d called for help' % toonId)
                    elif track == NPCSOS:
                        self.notify.debug('toon: %d called for help' % toonId)
                    elif track == PETSOS:
                        self.notify.debug('toon: %d called for pet' % toonId)
                        for i in range(len(self.activeToons)):
                            toon = self.getToon(self.activeToons[i])
                            if toon != None:
                                if i < len(hps):
                                    hp = hps[i]
                                    if hp > 0:
                                        toonHpDict[toon.doId][0] += hp
                                    self.notify.debug('pet heal: toon: %d healed for hp: %d' % (toon.doId, hp))
                                else:
                                    self.notify.warning('Invalid targetIndex %s in hps %s.' % (i, hps))

                    elif track == NPC_RESTOCK_GAGS:
                        for at in self.activeToons:
                            toon = self.getToon(at)
                            if toon != None:
                                toon.inventory.NPCMaxOutInv(npc_level)
                                toon.d_setInventory(toon.inventory.makeNetString())

                    elif track == HEAL:
                        if levelAffectsGroup(HEAL, level):
                            for i in range(len(self.activeToons)):
                                at = self.activeToons[i]
                                if attack.getTrack() != NPCSOS and (at == toonId and not self.air.wantSelfToonUp):
                                    continue
                                toon = self.getToon(at)
                                if toon != None:
                                    if i < len(hps):
                                        hp = hps[i]
                                    else:
                                        self.notify.warning('Invalid targetIndex %s in hps %s.' % (i, hps))
                                        hp = 0
                                    toonHpDict[toon.doId][0] += hp
                                    self.notify.debug('HEAL: toon: %d healed for hp: %d' % (toon.doId, hp))

                        else:
                            targetId = attack.getTarget()
                            toon = self.getToon(targetId)
                            if toon != None and targetId in self.activeToons:
                                targetIndex = self.activeToons.index(targetId)
                                if targetIndex < len(hps):
                                    hp = hps[targetIndex]
                                else:
                                    self.notify.warning('Invalid targetIndex %s in hps %s.' % (targetIndex, hps))
                                    hp = 0
                                toonHpDict[toon.doId][0] += hp
                    elif attackAffectsGroup(track, level, attack.getTrack()):
                        for suit in self.activeSuits:
                            targetIndex = self.activeSuits.index(suit)
                            if targetIndex < 0 or targetIndex >= len(hps):
                                self.notify.warning('Got attack (%s, %s) on target suit %s, but hps has only %s entries: %s' % (track,
                                 level,
                                 targetIndex,
                                 len(hps),
                                 hps))
                            else:
                                hp = hps[targetIndex]
                                if hp > 0 and track == LURE:
                                    if suit.battleTrap == UBER_GAG_LEVEL_INDEX:
                                        pass
                                    suit.battleTrap = NO_TRAP
                                    needUpdate = 1
                                    if suit.doId in trapDict:
                                        del trapDict[suit.doId]
                                    if suitsLuredOntoTraps.count(suit) == 0:
                                        suitsLuredOntoTraps.append(suit)
                                if track == TRAP:
                                    targetId = suit.doId
                                    if targetId in trapDict:
                                        trapDict[targetId].append(attack)
                                    else:
                                        trapDict[targetId] = [attack]
                                    needUpdate = 1
                                died = attack.getTgtDied() & 1 << targetIndex
                                if died != 0:
                                    if deadSuits.count(suit) == 0:
                                        deadSuits.append(suit)

                    else:
                        targetId = attack.getTarget()
                        target = self.findSuit(targetId)
                        if target != None:
                            targetIndex = self.activeSuits.index(target)
                            if targetIndex < 0 or targetIndex >= len(hps):
                                self.notify.warning('Got attack (%s, %s) on target suit %s, but hps has only %s entries: %s' % (track,
                                 level,
                                 targetIndex,
                                 len(hps),
                                 hps))
                            else:
                                hp = hps[targetIndex]
                                if track == TRAP:
                                    if targetId in trapDict:
                                        trapDict[targetId].append(attack)
                                    else:
                                        trapDict[targetId] = [attack]
                                if hp > 0 and track == LURE:
                                    oldBattleTrap = target.battleTrap
                                    if oldBattleTrap == UBER_GAG_LEVEL_INDEX:
                                        pass
                                    target.battleTrap = NO_TRAP
                                    needUpdate = 1
                                    if target.doId in trapDict:
                                        del trapDict[target.doId]
                                    if suitsLuredOntoTraps.count(target) == 0:
                                        suitsLuredOntoTraps.append(target)
                                    if oldBattleTrap == UBER_GAG_LEVEL_INDEX:
                                        for otherSuit in self.activeSuits:
                                            if not otherSuit == target:
                                                otherSuit.battleTrap = NO_TRAP
                                                if otherSuit.doId in trapDict:
                                                    del trapDict[otherSuit.doId]

                                died = attack.getTgtDied() & 1 << targetIndex
                                if died != 0:
                                    if deadSuits.count(target) == 0:
                                        deadSuits.append(target)
            elif self.findSuit(doId) is not None:
                attack = self.getBattleObjects()[doId].getNextAttack()
                if attack != NO_ATTACK:
                    suitId = attack.getAttackerId()
                    suit = self.findSuit(suitId)
                    if suit == None:
                        self.notify.warning('movieDone() - suit: %d is gone!' % suitId)
                        continue
                    if not (hasattr(suit, 'dna') and suit.dna):
                        toonId = self.air.getAvatarIdFromSender()
                        self.notify.warning('_movieDone avoiding crash, sender=%s but suit has no dna' % toonId)
                        self.air.writeServerEvent('suspicious', toonId, '_movieDone avoiding crash, suit has no dna')
                        continue
                    self.handleToonHpDict(attack, toonHpDict)
            elif doId in self.statusAttacks:
                attack = self.statusAttacks[doId]
                self.handleToonHpDict(attack, toonHpDict)

        self.exitedToons = []
        for suitKey in list(trapDict.keys()):
            attackList = trapDict[suitKey]
            attack = attackList[0]
            target = self.findSuit(attack.getTarget())
            if attack.getLevel() == UBER_GAG_LEVEL_INDEX:
                targetId = suitKey
                target = self.findSuit(targetId)
            if len(attackList) == 1:
                if suitsLuredOntoTraps.count(target) == 0:
                    self.notify.debug('movieDone() - trap set')
                    target.battleTrap = attack.getLevel()
                    needUpdate = 1
                else:
                    target.battleTrap = NO_TRAP
            else:
                self.notify.debug('movieDone() - traps collided')
                if target != None:
                    target.battleTrap = NO_TRAP

        if self.battleCalc.trainTrapTriggered:
            self.notify.debug('Train trap triggered, clearing all traps')
            for otherSuit in self.activeSuits:
                self.notify.debug('suit =%d, oldBattleTrap=%d' % (otherSuit.doId, otherSuit.battleTrap))
                otherSuit.battleTrap = NO_TRAP

        currLuredSuits = self.battleCalc.getLuredSuits()
        if len(self.luredSuits) == len(currLuredSuits):
            for suit in self.luredSuits:
                if currLuredSuits.count(suit.doId) == 0:
                    needUpdate = 1
                    break

        else:
            needUpdate = 1
        self.luredSuits = []
        for i in currLuredSuits:
            suit = self.air.doId2do[i]
            self.luredSuits.append(suit)
            self.notify.debug('movieDone() - suit: %d is lured' % i)

        for attack in npcTrapAttacks:
            track, level, hp = NPCToons.getNPCTrackLevelHp(attack.getTarget())
            for suit in self.activeSuits:
                if self.luredSuits.count(suit) == 0 and suit.battleTrap == NO_TRAP:
                    suit.battleTrap = level

            needUpdate = 1

        for suit in deadSuits:
            self.notify.debug('removing dead suit: %d' % suit.doId)
            if suit.isDeleted():
                self.notify.debug('whoops, suit %d is deleted.' % suit.doId)
            else:
                # In an instance where we are processing Cogs defeated at the end instead of rewarding every X floors,
                # we do not want 200+ cogs sent over the AI
                # Toontown at max usually has like 80 cogs
                if len(self.suitsKilled) < 200:
                    self.notify.debug('suit had revives? %d' % suit.getMaxSkeleRevives())
                    encounter = {'type': suit.dna.name,
                     'level': suit.getActualLevel(),
                     'track': suit.dna.dept,
                     'isSkelecog': suit.getSkelecog(),
                     'isForeman': suit.isForeman(),
                     'isVP': 0,
                     'isCFO': 0,
                     'isCJ': 0,
                     'isCEO': 0,
                     'isSupervisor': suit.isSupervisor(),
                     'isVirtual': suit.isVirtual(),
                     'hasRevives': suit.getMaxSkeleRevives(),
                     'activeToons': self.activeToons[:]}
                    self.suitsKilled.append(encounter)
                    self.suitsKilledThisBattle.append(encounter)
            self.__removeSuit(suit)
            needUpdate = 1
            suit.resume()

        lastActiveSuitDied = 0
        if len(self.activeSuits) == 0 and len(self.pendingSuits) == 0:
            lastActiveSuitDied = 1

        deadToons = []
        for activeToon in self.activeToons:
            hp = toonHpDict[activeToon]
            toon = self.getToon(activeToon)
            if toon != None:
                self.notify.debug('AFTER ROUND: currtoonHP: %d toonMAX: %d hheal: %d damage: %d' % (toon.hp,
                 toon.maxHp,
                 hp[0],
                 hp[1]))
                toon.hpOwnedByBattle = 0
                hpDelta = hp[0] - hp[1]
                if hpDelta >= 0:
                    toon.toonUp(hpDelta, quietly=1)
                else:
                    toon.takeDamage(-hpDelta, quietly=1)
                if toon.hp <= 0:
                    self.notify.debug('movieDone() - toon: %d was killed' % activeToon)
                    toon.inventory.zeroInv(1)
                    deadToons.append(activeToon)
                else:
                    toon.decStatusEffectRounds()
                self.notify.debug('AFTER ROUND: toon: %d setHp: %d' % (toon.doId, toon.hp))

        for deadToon in deadToons:
            self.__removeToon(deadToon)
            needUpdate = 1

        for suit in self.activeSuits:
            removedStatuses = suit.decStatusEffectRounds()
            self.handleStatusesRemoved(removedStatuses)
            self.getBattleObjects()[suit.getDoId()].roundDone()
        if self.getNewRoundSpeed() is not None:
            self.b_setRoundSpeed(self.getNewRoundSpeed())
        if self.randomizeTrackOrderEveryRound:
            self.d_randomizeTrackOrder()
        elif self.getTrackOrder() != DEFAULT_TRACK_ORDER:
            self.b_setTrackOrder(DEFAULT_TRACK_ORDER)
        self.clearAttacks()
        self.d_setMovie()
        self.d_setChosenToonAttacks()
        self.localMovieDone(needUpdate, deadToons, deadSuits, lastActiveSuitDied)

    def enterResume(self):
        for suit in self.suits:
            self.notify.info('battle done, resuming suit: %d' % suit.doId)
            if suit.isDeleted():
                self.notify.info('whoops, suit %d is deleted.' % suit.doId)
            else:
                suit.resume()

        self.suits = []
        self.joiningSuits = []
        self.pendingSuits = []
        self.adjustingSuits = []
        self.activeSuits = []
        self.luredSuits = []
        for toonId in self.toons:
            toon = simbase.air.doId2do.get(toonId)
            if toon:
                toon.b_setBattleId(0)
                messageToonReleased = 'Battle releasing toon %s' % toon.doId
                messenger.send(messageToonReleased, [toon.doId])

        for exitEvent in self.avatarExitEvents:
            self.ignore(exitEvent)

        eventMsg = {}
        for encounter in self.suitsKilledThisBattle:
            cog = encounter['type']
            level = encounter['level']
            msgName = '%s%s' % (cog, level)
            if encounter['isSkelecog']:
                msgName += '+'
            if msgName in eventMsg:
                eventMsg[msgName] += 1
            else:
                eventMsg[msgName] = 1

        msgText = ''
        for msgName, count in list(eventMsg.items()):
            if msgText != '':
                msgText += ','
            msgText += '%s%s' % (count, msgName)

        self.air.writeServerEvent('battleCogsDefeated', self.doId, '%s|%s' % (msgText, self.getTaskZoneId()))

    def exitResume(self):
        pass

    def isJoinable(self):
        return self.joinableFsm.getCurrentState().getName() == 'Joinable'

    def enterJoinable(self):
        self.notify.debug('enterJoinable()')

    def exitJoinable(self):
        pass

    def enterUnjoinable(self):
        self.notify.debug('enterUnjoinable()')

    def exitUnjoinable(self):
        pass

    def isRunable(self):
        return self.runableFsm.getCurrentState().getName() == 'Runable'

    def enterRunable(self):
        self.notify.debug('enterRunable()')

    def exitRunable(self):
        pass

    def enterUnrunable(self):
        self.notify.debug('enterUnrunable()')

    def exitUnrunable(self):
        pass

    def __estimateAdjustTime(self):
        self.needAdjust = 0
        adjustTime = 0
        if len(self.pendingSuits) > 0 or self.suitGone == 1:
            self.suitGone = 0
            pos0 = self.suitPendingPoints[0][0]
            pos1 = self.suitPoints[0][0][0]
            adjustTime = self.calcSuitMoveTime(pos0, pos1)
        if len(self.pendingToons) > 0 or self.toonGone == 1:
            self.toonGone = 0
            if adjustTime == 0:
                pos0 = self.toonPendingPoints[0][0]
                pos1 = self.toonPoints[0][0][0]
                adjustTime = self.calcToonMoveTime(pos0, pos1)
        return adjustTime

    def enterAdjusting(self):
        self.notify.debug('enterAdjusting()')
        self.timer.stop()
        self.__resetAdjustingResponses()
        self.adjustingTimer.startCallback(self.__estimateAdjustTime() + SERVER_BUFFER_TIME, self.__serverAdjustingDone)

    def __serverAdjustingDone(self):
        if self.needAdjust == 1:
            self.adjustFsm.request('NotAdjusting')
            self.__requestAdjust()
        else:
            self.notify.debug('adjusting timed out on the server')
            self.ignoreAdjustingResponses = 1
            self.__adjustDone()

    def exitAdjusting(self):
        currStateName = self.fsm.getCurrentState().getName()
        if currStateName == 'WaitForInput':
            self.timer.restart()
        elif currStateName == 'WaitForJoin':
            self.b_setState('WaitForInput')
        self.adjustingTimer.stop()

    def __addTrainTrapForNewSuits(self):
        hasTrainTrap = False
        trapInfo = None
        for otherSuit in self.activeSuits:
            if otherSuit.battleTrap == UBER_GAG_LEVEL_INDEX:
                hasTrainTrap = True

        if hasTrainTrap:
            for curSuit in self.activeSuits:
                if not curSuit.battleTrap == UBER_GAG_LEVEL_INDEX:
                    oldBattleTrap = curSuit.battleTrap
                    curSuit.battleTrap = UBER_GAG_LEVEL_INDEX
                    self.battleCalc.addTrainTrapForJoiningSuit(curSuit.doId)
                    self.notify.debug('setting traintrack trap for joining suit %d oldTrap=%s' % (curSuit.doId, oldBattleTrap))

    def __adjustDone(self):
        for s in self.adjustingSuits:
            self.pendingSuits.remove(s)
            self.addBattleObject(s, True)
        if self.adjustingSuits:
            self.applyEnvironmentStatusEffects()

        self.adjustingSuits = []
        for toon in self.adjustingToons:
            if self.pendingToons.count(toon) == 1:
                self.pendingToons.remove(toon)
            else:
                self.notify.warning('adjustDone() - toon: %d not pending!' % toon.doId)
            if self.activeToons.count(toon) == 0:
                self.addBattleObject(self.getToon(toon))
                self.ignoreResponses = 0
                self.sendEarnedExperience(toon)
            else:
                self.notify.warning('adjustDone() - toon: %d already active!' % toon.doId)

        self.adjustingToons = []
        self.__addTrainTrapForNewSuits()
        self.d_setMembers()
        self.adjustFsm.request('NotAdjusting')
        if self.needAdjust == 1:
            self.notify.debug('__adjustDone() - need to adjust again')
            self.__requestAdjust()

    def enterNotAdjusting(self):
        self.notify.debug('enterNotAdjusting()')
        if self.movieRequested == 1:
            if len(self.activeToons) > 0 and self.__allActiveToonsResponded():
                self.__requestMovie()

    def exitNotAdjusting(self):
        pass

    def getPetProxyObject(self, petId, callback):
        doneEvent = 'generate-%d' % petId

        def handlePetProxyRead(pet):
            callback(1, pet)

        self.air.sendActivate(petId, self.air.districtId, 0)
        self.acceptOnce(doneEvent, handlePetProxyRead)

    def _getNextSerialNum(self):
        num = self.serialNum
        self.serialNum += 1
        return num

    def sendBattleMsg(self, msg: str, identifier: int, extraArgs = []):
        messenger.send(msg % {'doId': identifier, 'battleId': identifier}, extraArgs)
