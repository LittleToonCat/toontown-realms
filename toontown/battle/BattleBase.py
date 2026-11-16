from typing import Dict, List, Tuple, Union
from panda3d.core import *
from toontown.toonbase.ToontownBattleGlobals import *
from direct.task.Timer import *
import math
from direct.directnotify import DirectNotifyGlobal
from toontown.toon import NPCToons
from toontown.toonbase import TTLocalizer
from otp.otpbase.PythonUtil import cmp_to_key
AVTYPE_TOON = 0
AVTYPE_SUIT = 1
AVTYPE_STATUS = 2
# this is what the client uses to get battle attack values
ATK_AVTYPE_COL = 0
ATK_ID_COL = 1
ATK_TRACK_COL = 2
ATK_LVL_COL = 3
ATK_TGT_COL = 4
ATK_HP_COL = 5
ATK_STATUS_COL = 6
ATK_ACCBONUS_COL = 7
ATK_HPBONUS_COL = 8
ATK_KBBONUS_COL = 9
ATK_TGT_DIED_COL = 10
ATK_TGT_REVIVE_COL = 11
ATK_TAUNT_COL = 12

NO_ID = -1
NO_ATTACK = -1
UN_ATTACK = -2
PASS_ATTACK = -3
NO_TRAP = -1
LURE_SUCCEEDED = -1
PASS = 98
SOS = 99
NPCSOS = 97
PETSOS = 96
FIRE = 100
HEAL = HEAL_TRACK
TRAP = TRAP_TRACK
LURE = LURE_TRACK
SOUND = SOUND_TRACK
THROW = THROW_TRACK
SQUIRT = SQUIRT_TRACK
DROP = DROP_TRACK
TOON_ATTACK_TIME = 14.0
SUIT_ATTACK_TIME = 12.0
TOON_TRAP_DELAY = 0.8
TOON_SOUND_DELAY = 1.0
TOON_THROW_DELAY = 0.5
TOON_THROW_SUIT_DELAY = 1.0
TOON_SQUIRT_DELAY = 0.5
TOON_SQUIRT_SUIT_DELAY = 1.0
TOON_DROP_DELAY = 0.8
TOON_DROP_SUIT_DELAY = 1.0
TOON_RUN_T = 3.3
TIMEOUT_PER_USER = 5
TOON_FIRE_DELAY = 0.5
TOON_FIRE_SUIT_DELAY = 1.0
REWARD_TIMEOUT = 120
FLOOR_REWARD_TIMEOUT = 4
BUILDING_REWARD_TIMEOUT = 300
PIE_DMG_DICT = {0: 6,
                1: 12,
                2: 17,
                3: 27,
                4: 40,
                5: 100,
                6: 120,
                7: 10,
                8: 15}

try:
    CLIENT_INPUT_TIMEOUT = base.config.GetFloat('battle-input-timeout', TTLocalizer.BBbattleInputTimeout)
except:
    CLIENT_INPUT_TIMEOUT = simbase.config.GetFloat('battle-input-timeout', TTLocalizer.BBbattleInputTimeout)

def levelAffectsGroup(track, level):
    return attackAffectsGroup(track, level)


def attackAffectsGroup(track, level, type = None):
    if track == NPCSOS or type == NPCSOS or track == PETSOS or type == PETSOS:
        return 1
    elif track >= 0 and track <= DROP_TRACK:
        return AvPropTargetCat[AvPropTarget[track]][level]
    else:
        return 0

def findToonAttack(toons, attacks, track):
    foundAttacks = []
    for t in toons:
        if t in attacks:
            attack = attacks[t]
            local_track = attack.getTrack()
            if track != NPCSOS and attack.getTrack() == NPCSOS:
                local_track = NPCToons.getNPCTrack(attack.getTarget())
            if local_track == track:
                if local_track == FIRE:
                    canFire = 1
                    for attackCheck in foundAttacks:
                        if attackCheck.getTarget() == attack.getTarget():
                            canFire = 0

                    if canFire:
                        foundAttacks.append(attack)
                else:
                    foundAttacks.append(attack)

    def compFunc(a, b):
        if a.getLevel() > b.getLevel():
            return 1
        elif a.getLevel() < b.getLevel():
            return -1
        return 0

    foundAttacks.sort(key=cmp_to_key(compFunc))
    return foundAttacks


SERVER_BUFFER_TIME = 2.0

FACEOFF_TAUNT_T = 3.5
FACEOFF_LOOK_AT_PROP_T = 2
FACEOFF_LOOK_AT_PROP_T_RETRO = 6
ELEVATOR_T = 4.0
BATTLE_SMALL_VALUE = 1e-07
MAX_EXPECTED_DISTANCE_FROM_BATTLE = 50.0

class BattleAttack:

    def __init__(self, attackerId: int = NO_ID, track: Union[int, str] = NO_ATTACK, level: int = -1, target: int = -1):
        self.resetAttack(attackerId, track, level, target)

    def resetAttack(self, attackerId: int = NO_ID, track: int = NO_ATTACK, level: int = -1, target: int = -1):
        self.setAttackerId(attackerId)
        self.setTrack(track)
        self.setLevel(level)
        self.setTarget(target)
        self.setHp([])
        self.setStatus({})
        self.setAccBonus(False)
        self.setHpBonus(0)
        self.kbBonus: List[int] = []
        self.setTgtDied(0)
        self.setTgtRevive(0)
        self.setTaunt('')   

    def setAttackerId(self, attackerId: int):
        self.attackerId = attackerId

    def getAttackerId(self) -> int:
        return self.attackerId

    # TODO: get rid of all int cases
    def setTrack(self, track: Union[int, str]):
        self.track = track

    def getTrack(self) -> Union[int, str]:
        return self.track

    def setLevel(self, level: int):
        self.level = level

    def getLevel(self) -> int:
        return self.level

    def setTarget(self, target: int):
        self.target = target

    def getTarget(self) -> int:
        return self.target

    def setHp(self, hp: List[int]):
        self.hp = hp

    def getHp(self) -> List[int]:
        return self.hp

    def setStatus(self, status: Dict[int, int]):
        self.status = status

    def getStatus(self) -> Dict[int, int]:
        return self.status

    def getStatusList(self) -> List[Tuple[int, int]]:
        statusList = []
        for tgtId, effectId in list(self.getStatus().items()):
           statusList.append((tgtId, effectId))
        return statusList

    def setAccBonus(self, accBonus: int):
        self.accBonus = accBonus

    def getAccBonus(self) -> bool:
        return self.accBonus

    def setHpBonus(self, hpBonus: int):
        self.hpBonus = hpBonus

    def getHpBonus(self) -> int:
        return self.hpBonus

    def getKbBonus(self) -> List[int]:
        return self.kbBonus

    def setTgtDied(self, tgtDied: int):
        self.tgtDied = tgtDied

    def getTgtDied(self) -> int:
        return self.tgtDied

    def setTgtRevive(self, tgtRevive: int):
        self.tgtRevive = tgtRevive

    def getTgtRevive(self) -> int:
        return self.tgtRevive

    def setTaunt(self, taunt: str):
        self.taunt = taunt

    def getTaunt(self) -> str:
        return self.taunt

class BattleBase:
    notify = DirectNotifyGlobal.directNotify.newCategory('BattleBase')

    # Where the Cogs stand in a battle
    suitPoints = (
        # One Cog
        ((Point3(0, 5, 0), 179),),

        # Two Cogs
        ((Point3(2, 5.3, 0), 170), (Point3(-2, 5.3, 0), 180)),

        # Three Cogs
        ((Point3(4, 5.2, 0), 170), (Point3(0, 6, 0), 179), (Point3(-4, 5.2, 0), 190)),

        # Four Cogs
        ((Point3(6, 4.4, 0), 160), (Point3(2, 6.3, 0), 170), (Point3(-2, 6.3, 0), 190), (Point3(-6, 4.4, 0), 200)),

        # Five Cogs
        ((Point3(8, 5.4, 0), 163), (Point3(4, 6.2, 0), 170), (Point3(0, 7, 0), 179), (Point3(-4, 6.2, 0), 190),
         (Point3(-8, 5.4, 0), 197)),

        # Six Cogs
        ((Point3(10, 4.4, 0), 155), (Point3(6, 5.4, 0), 160), (Point3(2, 7.3, 0), 170), (Point3(-2, 7.3, 0), 190),
         (Point3(-6, 5.4, 0), 200), (Point3(-10, 4.4, 0), 205)),

        # Seven Cogs
        ((Point3(12, 5.0, 0), 158),(Point3(8, 6.4, 0), 163), (Point3(4, 7.2, 0), 170), (Point3(0, 8, 0), 179),
         (Point3(-4, 7.2, 0), 190), (Point3(-8, 6.4, 0), 197), (Point3(-12, 5.0, 0), 203)),

        # Eight Cogs
        ((Point3(14, 3.6, 0), 150), (Point3(10, 5.4, 0), 155), (Point3(6, 6.4, 0), 160), (Point3(2, 8.3, 0), 170),
         (Point3(-2, 8.3, 0), 190), (Point3(-6, 6.4, 0), 200), (Point3(-10, 5.4, 0), 205), (Point3(-14, 3.6, 0), 210))
    )

    # Where the Cogs stand when they are waiting to join a battle
    suitPendingPoints = (
        # First Cog
        (Point3(-4, 8.2, 0), 190),

        # Second Cog
        (Point3(0, 9, 0), 179),

        # Third Cog
        (Point3(4, 8.2, 0), 170),

        # Fourth Cog
        (Point3(8, 3.2, 0), 160),

        # Fifth Cog
        (Point3(8.5, 7.2, 0), 165),

        # Sixth Cog
        (Point3(4.3, 11.2, 0), 170),

        # Seventh Cog
        (Point3(0, 12, 0), 179),

        # Eigth Cog
        (Point3(-4.3, 11.2, 0), 170)
    )
    toonPoints = (((Point3(0, -6, 0), 0),),
     ((Point3(1.5, -6.5, 0), 5), (Point3(-1.5, -6.5, 0), -5)),
     ((Point3(3, -6.75, 0), 5), (Point3(0, -7, 0), 0), (Point3(-3, -6.75, 0), -5)),
     ((Point3(4.5, -7, 0), 10),
      (Point3(1.5, -7.5, 0), 5),
      (Point3(-1.5, -7.5, 0), -5),
      (Point3(-4.5, -7, 0), -10)))
    toonPendingPoints = ((Point3(-3, -8, 0), -5),
     (Point3(0, -9, 0), 0),
     (Point3(3, -8, 0), 5),
     (Point3(5.5, -5.5, 0), 20))
    posA = Point3(0, 10, 0)
    posB = Point3(-7.071, 7.071, 0)
    posC = Point3(-10, 0, 0)
    posD = Point3(-7.071, -7.071, 0)
    posE = Point3(0, -10, 0)
    posF = Point3(7.071, -7.071, 0)
    posG = Point3(10, 0, 0)
    posH = Point3(7.071, 7.071, 0)
    allPoints = (posA,
     posB,
     posC,
     posD,
     posE,
     posF,
     posG,
     posH)
    toonCwise = [posA,
     posB,
     posC,
     posD,
     posE]
    toonCCwise = [posH,
     posG,
     posF,
     posE]
    suitCwise = [posE,
     posF,
     posG,
     posH,
     posA]
    suitCCwise = [posD,
     posC,
     posB,
     posA]
    suitSpeed = 4.8
    toonSpeed = 8.0

    def __init__(self):
        self.pos = Point3(0, 0, 0)
        self.initialSuitPos = Point3(0, 1, 0)
        self.timer = Timer()
        self.resetLists()

    def resetLists(self):
        self.suits = []
        self.pendingSuits = []
        self.joiningSuits = []
        self.activeSuits = []
        self.luredSuits = []
        self.suitGone = 0
        self.toons = []
        self.joiningToons = []
        self.pendingToons = []
        self.activeToons = []
        self.runningToons = []
        self.toonGone = 0
        self.helpfulToons = []

    def calcFaceoffTime(self, centerpos, suitpos):
        facing = Vec3(centerpos - suitpos)
        facing.normalize()
        suitdest = Point3(centerpos - Point3(facing * 6.0))
        dist = Vec3(suitdest - suitpos).length()
        return dist / BattleBase.suitSpeed

    def calcSuitMoveTime(self, pos0, pos1):
        dist = Vec3(pos0 - pos1).length()
        return dist / BattleBase.suitSpeed

    def calcToonMoveTime(self, pos0, pos1):
        dist = Vec3(pos0 - pos1).length()
        return dist / BattleBase.toonSpeed

    def buildJoinPointList(self, avPos, destPos, toon = 0):
        minDist = 999999.0
        nearestP = None
        for p in BattleBase.allPoints:
            dist = Vec3(avPos - p).length()
            if dist < minDist:
                nearestP = p
                minDist = dist

        self.notify.debug('buildJoinPointList() - avp: %s nearp: %s' % (avPos, nearestP))
        dist = Vec3(avPos - destPos).length()
        if dist < minDist:
            self.notify.debug('buildJoinPointList() - destPos is nearest')
            return []
        if toon == 1:
            if nearestP == BattleBase.posE:
                self.notify.debug('buildJoinPointList() - posE')
                plist = [BattleBase.posE]
            elif BattleBase.toonCwise.count(nearestP) == 1:
                self.notify.debug('buildJoinPointList() - clockwise')
                index = BattleBase.toonCwise.index(nearestP)
                plist = BattleBase.toonCwise[index + 1:]
            else:
                self.notify.debug('buildJoinPointList() - counter-clockwise')
                index = BattleBase.toonCCwise.index(nearestP)
                plist = BattleBase.toonCCwise[index + 1:]
        elif nearestP == BattleBase.posA:
            self.notify.debug('buildJoinPointList() - posA')
            plist = [BattleBase.posA]
        elif BattleBase.suitCwise.count(nearestP) == 1:
            self.notify.debug('buildJoinPointList() - clockwise')
            index = BattleBase.suitCwise.index(nearestP)
            plist = BattleBase.suitCwise[index + 1:]
        else:
            self.notify.debug('buildJoinPointList() - counter-clockwise')
            index = BattleBase.suitCCwise.index(nearestP)
            plist = BattleBase.suitCCwise[index + 1:]
        self.notify.debug('buildJoinPointList() - plist: %s' % plist)
        return plist

    def addHelpfulToon(self, toonId):
        if toonId not in self.helpfulToons:
            self.helpfulToons.append(toonId)
