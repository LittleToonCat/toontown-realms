from typing import List, Tuple
from panda3d.core import *
from panda3d.toontown import *
from direct.interval.IntervalGlobal import *
from direct.distributed.ClockDelta import *
from direct.directtools.DirectGeometry import CLAMP
from direct.gui.DirectWaitBar import DirectWaitBar
from direct.controls.ControlManager import CollisionHandlerRayStart
from direct.directnotify import DirectNotifyGlobal
from direct.task import Task
from otp.otpbase import OTPGlobals
from otp.avatar import DistributedAvatar
from random import choice
from toontown.battle.BattleBase import PIE_DMG_DICT
from toontown.battle import BattleProps, BattleParticles, MovieUtil, MovieFire
from toontown.distributed import DelayDelete
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import ToontownBattleGlobals
from toontown.toonbase import TTLocalizer
from toontown.toonbase.ToontownTypes import CogQuoteIndex
from direct.fsm import ClassicFSM
from direct.fsm import State
from . import Suit
from . import SuitBase
from . import SuitDNA
from . import DistributedSuitPlanner

class DistributedSuitBase(DistributedAvatar.DistributedAvatar, Suit.Suit, SuitBase.SuitBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedSuitBase')

    def __init__(self, cr):
        try:
            self.DistributedSuitBase_initialized
            return
        except:
            self.DistributedSuitBase_initialized = 1

        DistributedAvatar.DistributedAvatar.__init__(self, cr)
        Suit.Suit.__init__(self)
        SuitBase.SuitBase.__init__(self)
        self.activeShadow = 0
        self.virtual = 0
        self.battleDetectName = None
        self.cRay = None
        self.cRayNode = None
        self.cRayNodePath = None
        self.cRayBitMask = None
        self.lifter = None
        self.cTrav = None
        self.sp = None
        self.fsm = None
        self.reparentTo(hidden)
        self.loop('neutral')
        self.skeleRevives = 0
        self.maxSkeleRevives = 0
        self.topBrass: bool = False
        self.explodeTrack = False
        self.reviveTrack = False
        self.cannonTrack = False
        self.collPie = False
        self.collPieNode = False
        self.activeIntervals = {}
        self.statusEffects: List[Tuple[int, int]] = []

    def setVirtual(self, isVirtual):
        self.virtual = isVirtual
        if self.virtual:
            self.makeVirtual()

    def getVirtual(self):
        return self.virtual

    def setSkeleRevives(self, num):
        if num == None:
            num = 0
        self.skeleRevives = num
        self.isSkeleRevive = 1
        if num > self.maxSkeleRevives:
            self.maxSkeleRevives = num
        self.setNameInfo()

    def setTopBrass(self, topBrass: bool):
        self.topBrass = topBrass
        if self.topBrass:
            self.setNameInfo()

    def getTopBrass(self) -> bool:
        return self.topBrass

    def setNameInfo(self):
        level: str = str(self.getActualLevel())
        if self.getSkeleRevives() > 0:
            level += TTLocalizer.SkeleRevivePostFix
        if self.getTopBrass():
            level += TTLocalizer.TopBrassPostFix
        nameInfo = TTLocalizer.SuitBaseNameWithLevel % {'name': self._name,
             'dept': self.getStyleDept(),
             'level': level}
        self.setDisplayName(nameInfo)

    def getSkeleRevives(self):
        return self.skeleRevives

    def getMaxSkeleRevives(self):
        return self.maxSkeleRevives

    def generate(self):
        DistributedAvatar.DistributedAvatar.generate(self)

    def disable(self):
        if self.reviveTrack:
            self.clearInterval(self.uniqueName('reviveSeq'))
            self.reviveTrack = False
        if self.explodeTrack:
            self.clearInterval(self.uniqueName('explodeSeq'))
            self.explodeTrack = False
        if self.cannonTrack:
            self.clearInterval(self.uniqueName('cannonSeq'))
            self.cannonTrack = False
        self.notify.debug(f'{self.getDoId()}: disabling')
        self.ignoreAll()
        self.__removeCollisionData()
        self.cleanupLoseActor()
        self.stop()
        taskMgr.remove(self.uniqueName('blink-task'))
        DistributedAvatar.DistributedAvatar.disable(self)

    def delete(self):
        try:
            self.DistributedSuitBase_deleted
        except:
            self.DistributedSuitBase_deleted = 1
            self.notify.debug(f'{self.getDoId()}: deleting')
            del self.dna
            del self.sp
            DistributedAvatar.DistributedAvatar.delete(self)
            Suit.Suit.delete(self)
            SuitBase.SuitBase.delete(self)

    def setDNAString(self, dnaString):
        Suit.Suit.setDNAString(self, dnaString)

    def setDNA(self, dna):
        Suit.Suit.setDNA(self, dna)

    def getMaxHP(self):
        return self.maxHP

    def setMaxHP(self, maxHP):
        self.maxHP = maxHP

    def getHP(self):
        return self.currHP

    def setHP(self, hp):
        self.currHP = hp

    def getDialogueArray(self):
        return Suit.Suit.getDialogueArray(self)

    def __removeCollisionData(self):
        self.enableRaycast(0)
        self.cRay = None
        self.cRayNode = None
        self.cRayNodePath = None
        self.lifter = None
        self.cTrav = None
        return

    def setHeight(self, height):
        Suit.Suit.setHeight(self, height)

    def getRadius(self):
        return Suit.Suit.getRadius(self)

    def setLevelDist(self, level):
        if self.notify.getDebug():
            self.notify.debug(f'Got level {level} from server for suit {self.getDoId()}')
        self.setLevel(level)

    def enableBattleDetect(self, name, handler):
        if self.collTube:
            # Battle Collision
            self.battleDetectName = self.taskName(name)
            self.collNode = CollisionNode(self.battleDetectName)
            self.collNode.addSolid(self.collTube)
            self.collNodePath = self.attachNewNode(self.collNode)
            self.collNode.setCollideMask(ToontownGlobals.WallBitmask)
            self.accept(f'enter{self.battleDetectName}', handler)

            # Pie Collision
            capsule = CollisionCapsule(0, 0, self.height - 1, 0, 0, 0, 2)
            self.collPie = CollisionNode(str(self.doId))
            self.collPie.addSolid(capsule)
            self.collPie.setCollideMask(ToontownGlobals.PieBitmask)
            self.collPieNode = self.attachNewNode(self.collPie)
            self.collPieNode.setTag('pieCode', str(self.doId))
            self.accept('localPieSplat', self.__localPieSplat)
        return Task.done

    def disableBattleDetect(self):
        self.ignore('localPieSplat')
        if self.battleDetectName:
            self.ignore(f'enter{self.battleDetectName}')
            self.battleDetectName = None
        if self.collNodePath:
            self.collNodePath.removeNode()
            self.collNodePath = None
        if self.collPieNode:
            del self.collPie
            self.collPieNode.removeNode()
            self.collPieNode = False
        return

    def ignorePie(self):
        self.ignore('localPieSplat')

    def __localPieSplat(self, pieCode, entry, timestamp32):
        if pieCode == self.doId:
            self.sendUpdate('handleHit', [])
        
    def showDamage(self, dmg):
        self.corpMedallion.hide()
        self.healthBar.show()
        self.updateHealthBar(subtractHp = False)
        self.showHpText(-dmg)

    def damageSuit(self, dmg, roll):
        if roll == 2:
            quotes = base.cr.dataPackMgr.getCogQuotesByType(self.getStyleName(), CogQuoteIndex.FACEOFF_TAUNTS)
            self.setChatAbsolute(choice(quotes), CFSpeech | CFTimeout)
        self.showDamage(dmg)

    def doExplode(self, dmg, timestamp):
        self.disableBodyCollisions()

        intervalName = self.uniqueName('explodeSeq')
        if intervalName in self.activeIntervals:
            return
            
        quotes = base.cr.dataPackMgr.getCogQuotesByType(self.getStyleName(), CogQuoteIndex.COG_ACTION_PROP_EXPLODE_DIAL)
        self.explodeTrack = Parallel(
            Func(self.setChatAbsolute, choice(quotes), CFSpeech | CFTimeout),
            Func(self.showDamage, dmg),
            Sequence(
                Wait(2),
                MovieUtil.createSuitDeathTrack(self, self, render)
            ),
            name = intervalName
        )
        ts = globalClockDelta.localElapsedTime(timestamp)
        self.explodeTrack.start(ts)
        self.storeInterval(self.explodeTrack, intervalName)

    def doRevive(self, dmg, timestamp):
        self.ignorePie()

        intervalName = self.uniqueName('reviveSeq')
        if intervalName in self.activeIntervals:
            return

        explodeSfx = base.loader.loadSfx('phase_3.5/audio/sfx/ENC_cogfall_apart.ogg')
        suitPos, suitHpr = Point3(*self.getPos()), self.getHpr()
        explodePoint = Point3(suitPos.getX(), suitPos.getY(), suitPos.getZ() + self.height - 0.2)
        loseActor = self.getLoseActor()

        gearPart = BattleParticles.createParticleEffect('GearExplosion', numParticles = 20)
        bigGearPart = BattleParticles.createParticleEffect('BigGearExplosion', numParticles = 30)

        gearPart.setDepthWrite(False)
        bigGearPart.setDepthWrite(False)
        gearPart.setPos(explodePoint)
        bigGearPart.setPos(explodePoint)
        
        quotes = base.cr.dataPackMgr.getCogQuotesByType(self.getStyleName(), CogQuoteIndex.COG_ACTION_PROP_EXPLODE_DIAL)
        self.reviveTrack = Parallel(
            Func(self.showDamage, dmg),
            Sequence(
                Func(MovieUtil.insertReviveSuit, self, loseActor, render, suitPos, suitHpr),
                ActorInterval(loseActor, 'lose', startTime = 5.7, endTime = 6),
                Func(MovieUtil.removeReviveSuit, self, loseActor),
                Func(self.setChatAbsolute, choice(quotes), CFSpeech | CFTimeout),
                Func(self.updateHealthBar),
                Wait(0.2),
                Func(self.accept, 'localPieSplat', self.__localPieSplat)
            ),
            ParticleInterval(gearPart, render, worldRelative = 0, duration = 0.5, cleanup = True),
            ParticleInterval(bigGearPart, render, worldRelative = 0, duration = 0.5, cleanup = True),
            MovieUtil.createKapowExplosionTrack(render, explodePoint, 2.5),
            SoundInterval(explodeSfx, node = self, volume = 0.5),
            name = intervalName
        )
        ts = globalClockDelta.localElapsedTime(timestamp)
        self.reviveTrack.start(ts)
        self.storeInterval(self.reviveTrack, intervalName)

    def fireCog(self, timestamp):
        self.disableBodyCollisions()

        intervalName = self.uniqueName('cannonSeq')
        if intervalName in self.activeIntervals:
            return

        quotes = base.cr.dataPackMgr.getCogQuotesByType(self.getStyleName(), CogQuoteIndex.COG_FIRE_DIAL)
        self.cannonTrack = Parallel(
            Func(self.setChatAbsolute, choice(quotes), CFSpeech | CFTimeout),
            Func(self.showDamage, self.getMaxHP()),
            MovieUtil.createSuitStunInterval(self, 0.3, 1.3),
            MovieFire.getCannonIval(self),
            name = intervalName
        )
        ts = globalClockDelta.localElapsedTime(timestamp)
        self.cannonTrack.start(ts)
        self.storeInterval(self.cannonTrack, intervalName)

    def storeInterval(self, interval, name):
        if name in self.activeIntervals:
            name = name + str(len(list(self.activeIntervals.keys())))
        self.activeIntervals[name] = interval

    def clearInterval(self, name, finish = 1):
        if name in self.activeIntervals:
            ival = self.activeIntervals[name]
            if finish:
                ival.finish()
            else:
                ival.pause()
            if name in self.activeIntervals:
                DelayDelete.cleanupDelayDeletes(ival)
                del self.activeIntervals[name]
        else:
            self.notify.debug(f'interval {name} already cleared')

    def enableRaycast(self, enable = 1):
        if not self.cTrav or not hasattr(self, 'cRayNode') or not self.cRayNode:
            return
        self.cTrav.removeCollider(self.cRayNodePath)
        if enable:
            if self.notify.getDebug():
                self.notify.debug('enabling raycast')
            self.cTrav.addCollider(self.cRayNodePath, self.lifter)
        elif self.notify.getDebug():
            self.notify.debug('disabling raycast')

    def setBrushOff(self, seed):
        self.setChatAbsolute(base.cr.dataPackMgr.getBrushOffText(self.getStyleName(), seed), CFSpeech | CFTimeout)

    def initializeBodyCollisions(self, collIdStr):
        DistributedAvatar.DistributedAvatar.initializeBodyCollisions(self, collIdStr)
        if not self.ghostMode:
            self.collNode.setCollideMask(self.collNode.getIntoCollideMask() | ToontownGlobals.PieBitmask)
        self.cRay = CollisionRay(0.0, 0.0, CollisionHandlerRayStart, 0.0, 0.0, -1.0)
        self.cRayNode = CollisionNode(self.taskName('cRay'))
        self.cRayNode.addSolid(self.cRay)
        self.cRayNodePath = self.attachNewNode(self.cRayNode)
        self.cRayNodePath.hide()
        self.cRayBitMask = ToontownGlobals.FloorBitmask
        self.cRayNode.setFromCollideMask(self.cRayBitMask)
        self.cRayNode.setIntoCollideMask(BitMask32.allOff())
        self.lifter = CollisionHandlerFloor()
        self.lifter.setOffset(ToontownGlobals.FloorOffset)
        self.lifter.setReach(6.0)
        self.lifter.setMaxVelocity(8.0)
        self.lifter.addCollider(self.cRayNodePath, self)
        self.cTrav = base.cTrav

    def disableBodyCollisions(self):
        self.disableBattleDetect()
        self.enableRaycast(0)
        if self.cRayNodePath:
            self.cRayNodePath.removeNode()
        if hasattr(self, 'cRayNode'):
            del self.cRayNode
        if hasattr(self, 'cRay'):
            del self.cRay
        if hasattr(self, 'lifter'):
            del self.lifter

    def denyBattle(self):
        self.notify.debug('denyBattle()')
        place = self.cr.playGame.getPlace()
        if place.fsm.getCurrentState().getName() == 'WaitForBattle':
            place.setState('walk')
        self.resumePath(self.pathState)

    def makePathTrack(self, nodePath, posPoints, velocity, name):
        track = Sequence(name=name)
        restOfPosPoints = posPoints[1:]
        for pointIndex in range(len(posPoints) - 1):
            startPoint = posPoints[pointIndex]
            endPoint = posPoints[pointIndex + 1]
            track.append(Func(nodePath.headsUp, endPoint[0], endPoint[1], endPoint[2]))
            distance = Vec3(endPoint - startPoint).length()
            duration = distance / velocity
            track.append(LerpPosInterval(nodePath, duration=duration, pos=Point3(endPoint), startPos=Point3(startPoint)))

        return track

    def setState(self, state):
        if self.fsm == None:
            return 0
        if self.fsm.getCurrentState().getName() == state:
            return 0
        return self.fsm.request(state)

    def subclassManagesParent(self):
        return 0

    def enterOff(self, *args):
        self.hideNametag3d()
        self.hideNametag2d()
        if not self.subclassManagesParent():
            self.setParent(ToontownGlobals.SPHidden)

    def exitOff(self):
        if not self.subclassManagesParent():
            self.setParent(ToontownGlobals.SPRender)
        self.showNametag3d()
        self.showNametag2d()
        self.loop('neutral', 0)

    def enterBattle(self):
        self.loop('neutral', 0)
        self.disableBattleDetect()
        self.hideCorpMedallion()
        self.healthBar.show()
        if isinstance(self.healthBar, DirectWaitBar):
            self.healthBar['range'] = self.maxHP
            self.healthBar['value'] = self.currHP
        if self.currHP != self.maxHP:
            self.updateHealthBar()

    def exitBattle(self):
        self.healthBar.hide()
        self.showCorpMedallion()
        self.currHP = self.maxHP
        self.interactivePropTrackBonus = -1

    def enterWaitForBattle(self):
        self.loop('neutral', 0)

    def exitWaitForBattle(self):
        pass

    def setSkelecog(self, flag):
        SuitBase.SuitBase.setSkelecog(self, flag)
        if flag:
            Suit.Suit.makeSkeleton(self)

    def getAvIdName(self):
        try:
            level = self.getActualLevel()
        except:
            level = '???'

        return f'{self.getName()}\n{self.doId}\nLevel {level}'
        
    # Do NOT remove these or you'll be calling DistributedAvatar's methods instead
        
    def showHpText(self, number, bonus = 0, scale = 1, attackTrack = -1):
        Suit.Suit.showHpText(self, number, bonus, scale, attackTrack)

    def hideHpText(self):
        Suit.Suit.hideHpText(self)
