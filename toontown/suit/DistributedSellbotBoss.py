from panda3d.core import *
from panda3d.toontown import *
from direct.interval.IntervalGlobal import *
from toontown.battle.BattleProps import *
from direct.distributed.ClockDelta import *
from direct.showbase.PythonUtil import Functor
from direct.gui.DirectGui import *
from direct.fsm import FSM
from direct.fsm import ClassicFSM, State
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals, ControlManager
from toontown.toonbase import ToontownBattleGlobals
from . import DistributedBossCog
from toontown.toonbase import TTLocalizer
from toontown.toonbase import EnvironmentManager
from . import SuitDNA
from toontown.battle import BattleBase
from direct.directutil import Mopath
from direct.showutil import Rope
from toontown.distributed import DelayDelete
from toontown.toon import NPCToons
from direct.task import Task
import random
import math
from toontown.coghq import CogDisguiseGlobals
from toontown.suit import SellbotBossGlobals
from toontown.battle import BattleParticles
from toontown.coghq import FlyingCogs
from toontown.coghq import HolidayVPMovie
from toontown.effects.FireworkShow import FireworkShow
import datetime
OneBossCog = None


class DistributedSellbotBoss(DistributedBossCog.DistributedBossCog, FSM.FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedSellbotBoss')
    cageHeights = [100, 81, 63, 44, 25, 18]

    def __init__(self, cr):
        DistributedBossCog.DistributedBossCog.__init__(self, cr)
        FSM.FSM.__init__(self, 'DistributedSellbotBoss')
        self.cagedToonNpcId = None
        self.doobers = []
        self.dooberRequest = None
        self.bossDamage = 0
        self.attackCode = None
        self.attackAvId = 0
        self.recoverRate = 0
        self.recoverStartTime = 0
        self.bossDamageMovie = None
        self.cagedToon = None
        self.cageShadow = None
        self.cageIndex = 0
        self.everThrownPie = 0
        self.pieTimestamp = None
        self.battleThreeMusicTime = 0
        self.insidesANodePath = None
        self.insidesBNodePath = None
        self.rampA = None
        self.rampB = None
        self.rampC = None
        self.strafeInterval = None
        self.onscreenMessage = None
        self.toonMopathInterval = []
        self.nerfed = ToontownGlobals.SELLBOT_NERF_HOLIDAY in base.cr.newsManager.getHolidayIdList()
        self.localToonPromoted = True
        self.resetMaxDamage()
        self.__nextPageMsg = None
        self.__donePageMsg = None
        return

    def announceGenerate(self):
        global OneBossCog
        DistributedBossCog.DistributedBossCog.announceGenerate(self)
        if self.winter:
            self.setName(TTLocalizer.HolidaySellbotBossName)
        else:
            self.setName(TTLocalizer.SellbotBossName)
        nameInfo = TTLocalizer.BossCogNameWithDept % {'name': self._name,
         'dept': SuitDNA.getDeptFullname(self.style.dept)}
        self.setDisplayName(nameInfo)
        self.cageDoorSfx = loader.loadSfx('phase_5/audio/sfx/CHQ_SOS_cage_door.ogg')
        self.cageLandSfx = loader.loadSfx('phase_9/audio/sfx/CHQ_SOS_cage_land.ogg')
        self.cageLowerSfx = loader.loadSfx('phase_5/audio/sfx/CHQ_SOS_cage_lower.ogg')
        if self.winter:
            self.piesRestockSfx = loader.loadSfx('phase_11/audio/sfx/LB_evidence_miss.ogg')
        else:
            self.piesRestockSfx = loader.loadSfx('phase_9/audio/sfx/CHQ_SOS_pies_restock.ogg')
        self.rampSlideSfx = loader.loadSfx('phase_9/audio/sfx/CHQ_VP_ramp_slide.ogg')
        self.strafeSfx = []
        for i in range(10):
            if self.winter:
                self.strafeSfx.append(loader.loadSfx('phase_6/audio/sfx/KART_getGag.ogg'))
            else:
                self.strafeSfx.append(loader.loadSfx('phase_3.5/audio/sfx/SA_shred.ogg'))

        if self.hardcore:
            self.fallSfx = loader.loadSfx('phase_4/audio/sfx/MG_sfx_vine_game_fall.ogg')
            self.landSfx = loader.loadSfx('phase_4/audio/sfx/target_impact_grunt1.ogg')

        render.setTag('pieCode', str(ToontownGlobals.PieCodeNotBossCog))
        insidesA = CollisionPolygon(Point3(4.0, -2.0, 5.0), Point3(-4.0, -2.0, 5.0), Point3(-4.0, -2.0, 0.5), Point3(4.0, -2.0, 0.5))
        insidesANode = CollisionNode('BossZap')
        insidesANode.addSolid(insidesA)
        insidesANode.setCollideMask(ToontownGlobals.PieBitmask | ToontownGlobals.WallBitmask)
        self.insidesANodePath = self.axle.attachNewNode(insidesANode)
        self.insidesANodePath.setTag('pieCode', str(ToontownGlobals.PieCodeBossInsides))
        self.insidesANodePath.stash()
        insidesB = CollisionPolygon(Point3(-4.0, 2.0, 5.0), Point3(4.0, 2.0, 5.0), Point3(4.0, 2.0, 0.5), Point3(-4.0, 2.0, 0.5))
        insidesBNode = CollisionNode('BossZap')
        insidesBNode.addSolid(insidesB)
        insidesBNode.setCollideMask(ToontownGlobals.PieBitmask | ToontownGlobals.WallBitmask)
        self.insidesBNodePath = self.axle.attachNewNode(insidesBNode)
        self.insidesBNodePath.setTag('pieCode', str(ToontownGlobals.PieCodeBossInsides))
        self.insidesBNodePath.stash()
        target = CollisionTube(0, -1, 4, 0, -1, 9, 3.5)
        targetNode = CollisionNode('BossZap')
        targetNode.addSolid(target)
        targetNode.setCollideMask(ToontownGlobals.PieBitmask)
        self.targetNodePath = self.pelvis.attachNewNode(targetNode)
        self.targetNodePath.setTag('pieCode', str(ToontownGlobals.PieCodeBossCog))
        shield = CollisionTube(0, 1, 4, 0, 1, 7, 3.5)
        shieldNode = CollisionNode('BossZap')
        shieldNode.addSolid(shield)
        shieldNode.setCollideMask(ToontownGlobals.PieBitmask | ToontownGlobals.CameraBitmask)
        shieldNodePath = self.pelvis.attachNewNode(shieldNode)
        disk = loader.loadModel('phase_9/models/char/bossCog-gearCollide')
        disk.find('**/+CollisionNode').setName('BossZap')
        disk.reparentTo(self.pelvis)
        disk.setZ(0.8)
        self.loadEnvironment()
        self.__makeCagedToon()
        self.__loadMopaths()
        if self.winter:
            localAvatar.chatMgr.chatInputSpeedChat.addWinterVPMenu()

        # Check to see if we fall out of the map in hardcore mode
        if self.hardcore:
            taskMgr.add(self.hasFallen, self.uniqueName('hasFallen'))

        if OneBossCog != None:
            self.notify.warning('Multiple BossCogs visible.')
        OneBossCog = self
        return

    def disable(self):
        global OneBossCog
        DistributedBossCog.DistributedBossCog.disable(self)

        if self.winter:
            taskName = self.uniqueName('flickerBulb')
            if taskMgr.hasTaskNamed(taskName):
                taskMgr.remove(taskName)

        self.request('Off')
        self.unloadEnvironment()
        self.__unloadMopaths()
        self.__cleanupCagedToon()
        self.__clearOnscreenMessage()
        taskMgr.remove(self.uniqueName('PieAdvice'))
        taskMgr.remove(self.uniqueName('hasFallen'))
        self.__cleanupStrafe()
        render.clearTag('pieCode')
        self.targetNodePath.detachNode()
        self.cr.relatedObjectMgr.abortRequest(self.dooberRequest)
        self.dooberRequest = None
        self.betweenBattleMusic.stop()
        self.promotionMusic.stop()
        self.stingMusic.stop()
        self.battleTwoMusic.stop()
        self.battleThreeMusic.stop()
        self.epilogueMusic.stop()
        while len(self.toonMopathInterval):
            toonMopath = self.toonMopathInterval[0]
            toonMopath.finish()
            toonMopath.destroy()
            self.toonMopathInterval.remove(toonMopath)

        if self.winter:
            localAvatar.chatMgr.chatInputSpeedChat.removeWinterVPMenu()

        if OneBossCog == self:
            OneBossCog = None
        self.__nextPageMsg = None
        self.__donePageMsg = None
        return

    def resetMaxDamage(self):
        if self.hardcore:
            self.bossMaxDamage = ToontownGlobals.SellbotBossMaxDamageHardcore
        elif base.cr.nerfsMode:
            self.bossMaxDamage = ToontownGlobals.SellbotBossMaxDamageNerfs
        elif self.nerfed:
            self.bossMaxDamage = ToontownGlobals.SellbotBossMaxDamageNerfed
        else:
            self.bossMaxDamage = ToontownGlobals.SellbotBossMaxDamage

    def d_hitBoss(self, bossDamage):
        self.sendUpdate('hitBoss', [bossDamage])

    def d_hitBossInsides(self):
        self.sendUpdate('hitBossInsides', [])

    def d_hitToon(self, toonId):
        self.sendUpdate('hitToon', [toonId])

    def setCagedToonNpcId(self, npcId):
        self.cagedToonNpcId = npcId

    def gotToon(self, toon):
        stateName = self.state
        if stateName == 'Elevator':
            self.placeToonInElevator(toon)

    def setDooberIds(self, dooberIds):
        self.doobers = []
        self.cr.relatedObjectMgr.abortRequest(self.dooberRequest)
        self.dooberRequest = self.cr.relatedObjectMgr.requestObjects(dooberIds, allCallback=self.__gotDoobers)

    def __gotDoobers(self, doobers):
        self.dooberRequest = None
        self.doobers = doobers
        return

    def setBossDamage(self, bossDamage, recoverRate, timestamp):
        recoverStartTime = globalClockDelta.networkToLocalTime(timestamp)
        self.bossDamage = bossDamage
        self.recoverRate = recoverRate
        self.recoverStartTime = recoverStartTime
        taskName = 'RecoverBossDamage'
        taskMgr.remove(taskName)
        if self.bossDamageMovie:
            if self.bossDamage >= self.bossMaxDamage:
                self.bossDamageMovie.resumeUntil(self.bossDamageMovie.getDuration())
            else:
                self.bossDamageMovie.resumeUntil(self.bossDamage * self.bossDamageToMovie)
                if self.recoverRate:
                    taskMgr.add(self.__recoverBossDamage, taskName)
        self.updateHealthBar()

    def getBossDamage(self):
        now = globalClock.getFrameTime()
        elapsed = now - self.recoverStartTime
        return max(self.bossDamage - self.recoverRate * elapsed / 60.0, 0)

    def __recoverBossDamage(self, task):
        self.bossDamageMovie.setT(self.getBossDamage() * self.bossDamageToMovie)
        return Task.cont

    def __makeCagedToon(self):
        if self.cagedToon:
            return
        self.cagedToon = NPCToons.createLocalNPC(self.cagedToonNpcId)
        self.cagedToon.addActive()
        self.cagedToon.reparentTo(self.cage)
        self.cagedToon.setPosHpr(0, -2, 0, 180, 0, 0)
        self.cagedToon.loop('neutral')
        self.__nextPageMsg = 'nextChatPage'
        self.__donePageMsg = 'doneChatPage'
        if hasattr(self.cagedToon, 'uniqueName'):
            self.__nextPageMsg = self.cagedToon.uniqueName(self.__nextPageMsg)
            self.__donePageMsg = self.cagedToon.uniqueName(self.__donePageMsg)
        touch = CollisionPolygon(Point3(-3.0382, 3.0382, -1), Point3(3.0382, 3.0382, -1), Point3(3.0382, -3.0382, -1), Point3(-3.0382, -3.0382, -1))
        touchNode = CollisionNode('Cage')
        touchNode.setCollideMask(ToontownGlobals.WallBitmask)
        touchNode.addSolid(touch)
        self.cage.attachNewNode(touchNode)

    def __cleanupCagedToon(self):
        if self.cagedToon:
            self.cagedToon.removeActive()
            self.cagedToon.delete()
            self.cagedToon = None
        return

    def __walkToonToPromotion(self, toonId, delay, mopath, track, delayDeletes):
        toon = base.cr.doId2do.get(toonId)
        if toon:
            destPos = toon.getPos()
            self.placeToonInElevator(toon)
            toon.wrtReparentTo(render)
            walkMopath = MopathInterval(mopath, toon)
            ival = Sequence(Wait(delay), Func(toon.suit.setPlayRate, 1, 'walk'), Func(toon.suit.loop, 'walk'), toon.posInterval(1, Point3(0, 90, 20)), ParallelEndTogether(walkMopath, toon.posInterval(2, destPos, blendType='noBlend')), Func(toon.suit.loop, 'neutral'))
            self.toonMopathInterval.append(walkMopath)
            track.append(ival)
            delayDeletes.append(DelayDelete.DelayDelete(toon, 'SellbotBoss.__walkToonToPromotion'))

    def __walkDoober(self, suit, delay, turnPos, track, delayDeletes):
        turnPos = Point3(*turnPos)
        turnPosDown = Point3(*ToontownGlobals.SellbotBossDooberTurnPosDown)
        if self.hardcore:
            pos = ToontownGlobals.SellbotBossDooberFlyPosHardcore
        else:
            pos = ToontownGlobals.SellbotBossDooberFlyPos
        flyPos = Point3(*pos)
        seq = Sequence(Func(suit.headsUp, turnPos), Wait(delay), Func(suit.loop, 'walk', 0), self.__walkSuitToPoint(suit, suit.getPos(), turnPos),
                       self.__walkSuitToPoint(suit, turnPos, turnPosDown))
        if self.hardcore:
            extendPos = Point3(*ToontownGlobals.SellbotBossDooberExtendPosHardcore)
            seq.append(Sequence(self.__walkSuitToPoint(suit, turnPosDown, extendPos), self.__walkSuitToPoint(suit, extendPos, flyPos)))
        else:
            seq.append(self.__walkSuitToPoint(suit, turnPosDown, flyPos))
        seq.append(Sequence(suit.beginSupaFlyMove(flyPos, 0, 'flyAway'), Func(suit.fsm.request, 'Off')))
        track.append(seq)
        delayDeletes.append(DelayDelete.DelayDelete(suit, 'SellbotBoss.__walkDoober'))

    def __walkSuitToPoint(self, node, fromPos, toPos):
        vector = Vec3(toPos - fromPos)
        distance = vector.length()
        if self.hardcore:
            speedMultiplier = 3.2
        else:
            speedMultiplier = 2
        time = distance / (ToontownGlobals.SuitWalkSpeed * speedMultiplier)
        return Sequence(Func(node.setPos, fromPos), Func(node.headsUp, toPos), node.posInterval(time, toPos))

    def __hideToons(self):
        for toonId in self.involvedToons:
            toon = self.cr.doId2do.get(toonId)
            if toon:
                toon.hide()

    def __showToons(self):
        for toonId in self.involvedToons:
            toon = self.cr.doId2do.get(toonId)
            if toon:
                toon.show()

    def makeIntroductionMovie(self, delayDeletes):
        track = Parallel()
        camera.reparentTo(render)
        camera.setPosHpr(0, 25, 30, 0, 0, 0)
        dooberTrack = Parallel()
        if self.doobers:
            self.__doobersToPromotionPosition(self.doobers[:4], self.battleANode)
            self.__doobersToPromotionPosition(self.doobers[4:], self.battleBNode)
            turnPosA = ToontownGlobals.SellbotBossDooberTurnPosA
            turnPosB = ToontownGlobals.SellbotBossDooberTurnPosB
            self.__walkDoober(self.doobers[0], 0, turnPosA, dooberTrack, delayDeletes)
            self.__walkDoober(self.doobers[1], 4, turnPosA, dooberTrack, delayDeletes)
            self.__walkDoober(self.doobers[2], 8, turnPosA, dooberTrack, delayDeletes)
            self.__walkDoober(self.doobers[3], 12, turnPosA, dooberTrack, delayDeletes)
            self.__walkDoober(self.doobers[7], 2, turnPosB, dooberTrack, delayDeletes)
            self.__walkDoober(self.doobers[6], 6, turnPosB, dooberTrack, delayDeletes)
            self.__walkDoober(self.doobers[5], 10, turnPosB, dooberTrack, delayDeletes)
            self.__walkDoober(self.doobers[4], 14, turnPosB, dooberTrack, delayDeletes)
        toonTrack = Parallel()
        self.__toonsToPromotionPosition(self.toonsA, self.battleANode)
        self.__toonsToPromotionPosition(self.toonsB, self.battleBNode)
        delay = 0
        for toonId in self.toonsA:
            self.__walkToonToPromotion(toonId, delay, self.toonsEnterA, toonTrack, delayDeletes)
            delay += 1

        for toonId in self.toonsB:
            self.__walkToonToPromotion(toonId, delay, self.toonsEnterB, toonTrack, delayDeletes)
            delay += 1

        toonTrack.append(Sequence(Wait(delay), self.closeDoors))
        self.rampA.request('extended')
        self.rampB.request('extended')
        self.rampC.request('retracted')
        self.clearChat()
        self.cagedToon.clearChat()
        if self.winter:
            promoteDoobers = TTLocalizer.HolidayBossCogPromoteDoobers
            doobersAway = TTLocalizer.HolidayBossCogDoobersAway[self.style.dept]
            welcomeToons = TTLocalizer.HolidayBossCogWelcomeToons
            promoteToons = TTLocalizer.HolidayBossCogPromoteToons
            rescueQuery = TTLocalizer.HolidayCagedToonRescueQuery
            discoverToons = TTLocalizer.HolidayBossCogDiscoverToons
            attackToons = TTLocalizer.HolidayBossCogAttackToons
        else:
            promoteDoobers = TTLocalizer.BossCogPromoteDoobers % SuitDNA.getDeptFullnameP(self.style.dept)
            doobersAway = TTLocalizer.BossCogDoobersAway[self.style.dept]
            welcomeToons = TTLocalizer.BossCogWelcomeToons
            promoteToons = TTLocalizer.BossCogPromoteToons % SuitDNA.getDeptFullnameP(self.style.dept)
            rescueQuery = TTLocalizer.CagedToonRescueQuery
            discoverToons = TTLocalizer.BossCogDiscoverToons
            attackToons = TTLocalizer.BossCogAttackToons
        interruptBoss = TTLocalizer.CagedToonInterruptBoss
        bossAnimTrack = Sequence(
            ActorInterval(self, 'Ff_speech', startTime=2, duration=10, loop=1),
            ActorInterval(self, 'ltTurn2Wave', duration=2),
            ActorInterval(self, 'wave', duration=4, loop=1),
            ActorInterval(self, 'ltTurn2Wave', startTime=2, endTime=0),
            ActorInterval(self, 'Ff_speech', duration=7, loop=1))
        track.append(bossAnimTrack)
        dialogTrack = Track(
            (0, Parallel(
                camera.posHprInterval(8, Point3(-22, -100, 35), Point3(-10, -13, 0), blendType='easeInOut'),
                IndirectInterval(toonTrack, 0, 18))),
            (5.6, Func(self.setChatAbsolute, promoteDoobers, CFSpeech)),
            (8, dooberTrack),
            (10, Sequence(
                Func(self.clearChat),
                Func(camera.setPosHpr, -23.1, 15.7, 17.2, -160, -1.9, 0))),
            (12, Func(self.setChatAbsolute, doobersAway, CFSpeech)),
            (16, Parallel(
                Func(self.clearChat),
                Func(camera.setPosHpr, -25, -99, 10, -14, 10, 0),
                IndirectInterval(toonTrack, 30))),
            (18, Func(self.setChatAbsolute, welcomeToons, CFSpeech)),
            (22, Func(self.setChatAbsolute, promoteToons, CFSpeech)),
            (22.2, Sequence(
                Func(self.cagedToon.nametag3d.setScale, 2),
                Func(self.cagedToon.setChatAbsolute, interruptBoss, CFSpeech),
                ActorInterval(self.cagedToon, 'wave'),
                Func(self.cagedToon.loop, 'neutral'))),
            (25, Sequence(
                Func(self.clearChat),
                Func(self.cagedToon.clearChat),
                Func(camera.setPosHpr, -12, -15, 27, -151, -15, 0),
                ActorInterval(self, 'Ff_lookRt'))),
            (27, Sequence(
                Func(self.cagedToon.setChatAbsolute, rescueQuery, CFSpeech),
                Func(camera.setPosHpr, -12, 48, 94, -26, 20, 0),
                ActorInterval(self.cagedToon, 'wave'),
                Func(self.cagedToon.loop, 'neutral'))),
            (31, Sequence(
                Func(self.__hideToons),
                Func(camera.setPosHpr, -22.72, -34, 8.73, -88, 30, 0),
                Func(self.setChatAbsolute, discoverToons, CFSpeech),
                Func(self.cagedToon.nametag3d.setScale, 1),
                Func(self.cagedToon.clearChat),
                ActorInterval(self, 'turn2Fb'))),
            (34, Sequence(
                Func(self.clearChat),
                Func(self.__showToons),
                self.loseCogSuits(self.toonsA, self.battleANode, (0, 18, 5, -180, 0, 0)),
                self.loseCogSuits(self.toonsB, self.battleBNode, (0, 18, 5, -180, 0, 0)))),
            (37, Sequence(
                self.toonNormalEyes(self.involvedToons),
                Func(camera.setPosHpr, -23.4, -145.6, 44.0, -10.0, -12.5, 0),
                Func(self.loop, 'Fb_neutral'),
                Func(self.rampA.request, 'retract'),
                Func(self.rampB.request, 'retract'),
                Parallel(self.backupToonsToBattlePosition(self.toonsA, self.battleANode),
                         self.backupToonsToBattlePosition(self.toonsB, self.battleBNode),
                         Sequence(
                             Wait(2),
                             Func(self.setChatAbsolute, attackToons, CFSpeech))))))
        track.append(dialogTrack)
        return Sequence(Func(self.stickToonsToFloor), track, Func(self.unstickToons), name=self.uniqueName('Introduction'))

    def __makeRollToBattleTwoMovie(self):
        startPos = Point3(ToontownGlobals.SellbotBossBattleOnePosHpr[0], ToontownGlobals.SellbotBossBattleOnePosHpr[1], ToontownGlobals.SellbotBossBattleOnePosHpr[2])
        if self.arenaSide:
            topRampPos = Point3(*ToontownGlobals.SellbotBossTopRampPosB)
            topRampTurnPos = Point3(*ToontownGlobals.SellbotBossTopRampTurnPosB)
            p3Pos = Point3(*ToontownGlobals.SellbotBossP3PosB)
        else:
            topRampPos = Point3(*ToontownGlobals.SellbotBossTopRampPosA)
            topRampTurnPos = Point3(*ToontownGlobals.SellbotBossTopRampTurnPosA)
            p3Pos = Point3(*ToontownGlobals.SellbotBossP3PosA)
        battlePos = Point3(ToontownGlobals.SellbotBossBattleTwoPosHpr[0], ToontownGlobals.SellbotBossBattleTwoPosHpr[1], ToontownGlobals.SellbotBossBattleTwoPosHpr[2])
        battleHpr = VBase3(ToontownGlobals.SellbotBossBattleTwoPosHpr[3], ToontownGlobals.SellbotBossBattleTwoPosHpr[4], ToontownGlobals.SellbotBossBattleTwoPosHpr[5])
        bossTrack = Sequence()
        bossTrack.append(Func(self.getGeomNode().setH, 180))
        bossTrack.append(Func(self.loop, 'Fb_neutral'))
        track, hpr = self.rollBossToPoint(startPos, None, topRampPos, None, 0)
        bossTrack.append(track)
        track, hpr = self.rollBossToPoint(topRampPos, hpr, topRampTurnPos, None, 0)
        bossTrack.append(track)
        track, hpr = self.rollBossToPoint(topRampTurnPos, hpr, p3Pos, None, 0)
        bossTrack.append(track)
        track, hpr = self.rollBossToPoint(p3Pos, hpr, battlePos, None, 0)
        bossTrack.append(track)
        return Sequence(bossTrack, Func(self.getGeomNode().setH, 0), name=self.uniqueName('BattleTwo'))

    def cagedToonMovieFunction(self, instruct, cageIndex):
        self.notify.debug('cagedToonMovieFunction()')
        if not (hasattr(self, 'cagedToon') and hasattr(self.cagedToon, 'nametag') and hasattr(self.cagedToon, 'nametag3d')):
            return
        if instruct == 1:
            self.cagedToon.nametag3d.setScale(2)
        elif instruct == 2:
            self.cagedToon.setChatAbsolute(TTLocalizer.CagedToonDrop[cageIndex], CFSpeech)
        elif instruct == 3:
            self.cagedToon.nametag3d.setScale(1)
        elif instruct == 4:
            self.cagedToon.clearChat()

    def makeEndOfBattleMovie(self, hasLocalToon):
        name = self.uniqueName('CageDrop')
        seq = Sequence(name=name)
        seq.append(Func(self.cage.setPos, self.cagePos[self.cageIndex]))
        if hasLocalToon:
            seq += [Func(camera.reparentTo, render),
             Func(camera.setPosHpr, self.cage, 0, -50, 0, 0, 0, 0),
             Func(self.hide)]
        seq += [Wait(0.5),
         Parallel(self.cage.posInterval(1, self.cagePos[self.cageIndex + 1], blendType='easeInOut'), SoundInterval(self.cageLowerSfx, duration=1)),
         Func(self.cagedToonMovieFunction, 1, self.cageIndex),
         Func(self.cagedToonMovieFunction, 2, self.cageIndex),
         Wait(3),
         Func(self.cagedToonMovieFunction, 3, self.cageIndex),
         Func(self.cagedToonMovieFunction, 4, self.cageIndex)]
        if hasLocalToon:
            seq += [Func(self.show),
             Func(camera.reparentTo, localAvatar),
             Func(camera.setPos, localAvatar.cameraPositions[0][0]),
             Func(camera.setHpr, 0, 0, 0)]
        self.cageIndex += 1
        return seq

    def __makeBossDamageMovie(self):
        startPos = Point3(ToontownGlobals.SellbotBossBattleTwoPosHpr[0], ToontownGlobals.SellbotBossBattleTwoPosHpr[1], ToontownGlobals.SellbotBossBattleTwoPosHpr[2])
        startHpr = Point3(*ToontownGlobals.SellbotBossBattleThreeHpr)
        if self.hardcore:
            bottomPos = Point3(*ToontownGlobals.SellbotBossBottomPosHardcore)
            deathPos = Point3(*ToontownGlobals.SellbotBossDeathPosHardcore)
        else:
            bottomPos = Point3(*ToontownGlobals.SellbotBossBottomPos)
            deathPos = Point3(*ToontownGlobals.SellbotBossDeathPos)
        self.setPosHpr(startPos, startHpr)
        bossTrack = Sequence()
        bossTrack.append(Func(self.loop, 'Fb_neutral'))
        track, hpr = self.rollBossToPoint(startPos, startHpr, bottomPos, None, 1)
        bossTrack.append(track)
        track, hpr = self.rollBossToPoint(bottomPos, startHpr, deathPos, None, 1)
        bossTrack.append(track)
        duration = bossTrack.getDuration()
        return bossTrack

    def __talkAboutPromotion(self, speech):
        if not self.localToonPromoted:
            pass
        elif self.prevCogSuitLevel < ToontownGlobals.MaxCogSuitLevel:
            speech += TTLocalizer.CagedToonPromotion
            newCogSuitLevel = localAvatar.getCogLevels()[CogDisguiseGlobals.dept2deptIndex(self.style.dept)]
            if newCogSuitLevel == ToontownGlobals.MaxCogSuitLevel:
                speech += TTLocalizer.CagedToonLastPromotion % (ToontownGlobals.MaxCogSuitLevel + 1)
            if newCogSuitLevel in ToontownGlobals.CogSuitHPLevels:
                speech += TTLocalizer.CagedToonHPBoost
        else:
            speech += TTLocalizer.CagedToonMaxed % (ToontownGlobals.MaxCogSuitLevel + 1)
        return speech

    def __makeCageOpenMovie(self):
        speech = TTLocalizer.CagedToonThankYou
        speech = self.__talkAboutPromotion(speech)
        name = self.uniqueName('CageOpen')
        seq = Sequence(Func(self.cage.setPos, self.cagePos[4]),
                       Func(self.cageDoor.setHpr, VBase3(0, 0, 0)),
                       Func(self.cagedToon.setPos, Point3(0, -2, 0)),
                       Parallel(
                           self.cage.posInterval(0.5, self.cagePos[5], blendType='easeOut'),
                           SoundInterval(self.cageLowerSfx, duration=0.5)),
                       Parallel(
                           self.cageDoor.hprInterval(0.5, VBase3(0, 90, 0), blendType='easeOut'),
                           Sequence(SoundInterval(self.cageDoorSfx), duration=0)),
                       Wait(0.2),
                       Func(self.cagedToon.loop, 'walk'),
                       self.cagedToon.posInterval(0.8, Point3(0, -6, 0)),
                       Func(self.cagedToon.setChatAbsolute, TTLocalizer.CagedToonYippee, CFSpeech),
                       ActorInterval(self.cagedToon, 'jump'),
                       Func(self.cagedToon.loop, 'neutral'),
                       Func(self.cagedToon.headsUp, localAvatar))

        dt = datetime.datetime.today()
        month = dt.month
        day = dt.day
        if self.winter and ((month == 12 and day in (24, 25, 31)) or (month == 1 and day == 1) or self.mode == ToontownGlobals.BossPartySellbotBossWinter):
            # Setup movie
            self.movie = HolidayVPMovie.HolidayVPMovie(self.getDoId())
            self.movie.load()
            self.movie.frame.hide()

            # Add caged Toon to movie
            dna = self.cagedToon.style.asTuple()
            cagedToon = self.movie.makeToonForGui(dna)
            self.movie.changeHead(cagedToon)
            self.movie.head.hide()
            self.movie.gameTitleText.setText(self.cagedToon.getName())

            # Fireworks show
            self.fireworkShow = FireworkShow(2)
            self.fireworkShow.reparentTo(self.geom)
            self.fireworkShow.setPos(0, -300, 0)

            # Background sleigh
            sleigh = loader.loadModel('phase_14.5/models/props/sleigh')
            sleigh.reparentTo(self.geom)
            sleigh.setPosHpr(248.65, -318.45, 2.35, 180.0, 0.0, -26.25)
            sleigh.setColorScale(1.0, 1.0, 1.0, 0.0)

            # Logo for dramatic effect
            loadingGui = loader.loadModel('phase_3/models/gui/loading-background')
            logo = loadingGui.find('**/logo').copyTo(aspect2dp.attachNewNode('holidayLogo'))
            logo.setPos(0.0, 0.0, 0.1)
            logo.setScale(0.7 * 1.25, 0.7 * 1.25, 0.7 * 1.25)
            logo.setColorScale(1.0, 1.0, 1.0, 0.0)
            loadingGui.removeNode()

            # Thank-you text
            year = datetime.datetime.today().year
            if month == 12:
                year += 1
            message = TTLocalizer.HolidayBossThanks.format(year)
            label = DirectLabel(parent=aspect2dp, relief=None, scale=0.1, pos=(0.0, 0.0, -0.30), text=message,
                                text_font=ToontownGlobals.getInterfaceFont(), text_fg=Vec4(1, 1, 1, 1), text_shadow=Vec4(0, 0, 0, 1))
            label.setColorScale(1.0, 1.0, 1.0, 0.0)

            # Remove flying Cogs
            if hasattr(self, 'flyingCogs') and self.flyingCogs:
                self.flyingCogs.delete()
                del self.flyingCogs

            seq.append(Sequence(Func(camera.setPosHpr, 0.0, 70.0, 45.0, -180.0, 0.0, 0.0), Func(self.movie.frame.show), Func(base.localAvatar.chatMgr.obscure, 1, 1),
                                Func(base.toggleNametags, False), Func(self.movie.head.show), Func(self.cagedToon.clearChat), Func(self.fireworkShow.begin, 0),
                                Parallel(LerpPosHprInterval(camera, 60.0, (0.0, -90.0, 10.0), (-180.0, 30.0, 0.0)),
                                         Sequence(Wait(10.0), Parallel(LerpPosInterval(sleigh, 50.0, (-224.67, -318.45, 186.45)),
                                                                       Sequence(LerpColorScaleInterval(sleigh, 5.0, (1.0, 1.0, 1.0, 1.0)),
                                                                                Wait(40.0), LerpColorScaleInterval(sleigh, 5.0, (1.0, 1.0, 1.0, 0.0)))),
                                                  Func(sleigh.removeNode)),
                                         Sequence(Wait(1.0), Func(self.movie.displayLine, cagedToon, TTLocalizer.HolidayCagedToonSpeech_1),
                                                  Wait(4.5), Func(self.movie.displayLine, cagedToon, TTLocalizer.HolidayCagedToonSpeech_2),
                                                  Wait(4.5), Func(self.movie.displayLine, cagedToon, TTLocalizer.HolidayCagedToonSpeech_3),
                                                  Wait(4.0), Func(self.movie.displayLine, cagedToon, TTLocalizer.HolidayCagedToonSpeech_4),
                                                  Wait(8.0), Func(self.movie.displayLine, cagedToon, TTLocalizer.HolidayCagedToonSpeech_5),
                                                  Wait(4.5), Func(self.movie.displayLine, cagedToon, TTLocalizer.HolidayCagedToonSpeech_6),
                                                  Wait(4.5), Func(self.movie.displayLine, cagedToon, TTLocalizer.HolidayCagedToonSpeech_7),
                                                  Wait(10.0), Func(self.movie.unload), Wait(5.0), Parallel(LerpColorScaleInterval(logo, 2.0, (1.0, 1.0, 1.0, 1.0)),
                                                                                                           LerpColorScaleInterval(label, 2.0, (1.0, 1.0, 1.0, 1.0))),
                                                  Wait(9.0), Parallel(LerpColorScaleInterval(logo, 2.0, (1.0, 1.0, 1.0, 0.0)),
                                                                      LerpColorScaleInterval(label, 2.0, (1.0, 1.0, 1.0, 0.0))),
                                                  Func(logo.removeNode), Func(label.destroy), Wait(1.0), Func(base.toggleNametags, True),
                                                  Func(base.localAvatar.chatMgr.obscure, 0, 0), Func(camera.reparentTo, localAvatar), Func(camera.setPos, 0, -9, 9),
                                                  Func(camera.lookAt, self.cagedToon, Point3(0, 0, 2), name=name), Func(self.__epilogueChatDone, 0)))))

        else:
            seq.append(Sequence(Func(camera.reparentTo, localAvatar),
                                Func(camera.setPos, 0, -9, 9),
                                Func(camera.lookAt, self.cagedToon, Point3(0, 0, 2), name=name),
                                Func(self.cagedToon.setLocalPageChat, speech, 0)))

        return seq

    def __showOnscreenMessage(self, text):
        if self.onscreenMessage:
            self.onscreenMessage.destroy()
            self.onscreenMessage = None
        self.onscreenMessage = DirectLabel(text=text, text_fg=VBase4(1, 1, 1, 1), text_align=TextNode.ACenter, relief=None, pos=(0, 0, 0.35), scale=0.1)
        return

    def __clearOnscreenMessage(self):
        if self.onscreenMessage:
            self.onscreenMessage.destroy()
            self.onscreenMessage = None
        return

    def __showWaitingMessage(self, task):
        self.__showOnscreenMessage(TTLocalizer.BuildingWaitingForVictors)

    def __placeCageShadow(self):
        if self.cageShadow == None:
            self.cageShadow = loader.loadModel('phase_3/models/props/drop_shadow')
            self.cageShadow.setPos(0, 77.9, 18)
            self.cageShadow.setColorScale(1, 1, 1, 0.6)
        self.cageShadow.reparentTo(render)
        return

    def __removeCageShadow(self):
        if self.cageShadow != None:
            self.cageShadow.detachNode()
        return

    def setCageIndex(self, cageIndex):
        self.cageIndex = cageIndex
        self.cage.setPos(self.cagePos[self.cageIndex])
        if self.cageIndex >= 4:
            self.__placeCageShadow()
        else:
            self.__removeCageShadow()

    def loadEnvironment(self):
        DistributedBossCog.DistributedBossCog.loadEnvironment(self)

        if self.hardcore:
            path = 'phase_9/models/cogHQ/BossRoomHQ2'
        else:
            path = 'phase_9/models/cogHQ/BossRoomHQ'
        self.geom = loader.loadModel(path)
        self.rampA = self.__findRamp('rampA', '**/west_ramp2')
        self.rampB = self.__findRamp('rampB', '**/west_ramp')
        self.rampC = self.__findRamp('rampC', '**/west_ramp1')
        self.cage = self.geom.find('**/cage')
        elevatorEntrance = self.geom.find('**/elevatorEntrance')
        elevatorEntrance.getChildren().detach()
        elevatorEntrance.setScale(1)
        elevatorModel = loader.loadModel('phase_9/models/cogHQ/cogHQ_elevator')
        elevatorModel.reparentTo(elevatorEntrance)
        self.setupElevator(elevatorModel)
        pos = self.cage.getPos()
        self.cagePos = []
        for height in self.cageHeights:
            self.cagePos.append(Point3(pos[0], pos[1], height))

        self.cageDoor = self.geom.find('**/cage_door')
        self.cage.setScale(1)
        self.rope = Rope.Rope(name='supportChain')
        self.rope.reparentTo(self.cage)
        self.rope.setup(2, ((self.cage, (0.15, 0.13, 16)), (self.geom, (0.23, 78, 120))))
        self.rope.ropeNode.setRenderMode(RopeNode.RMBillboard)
        self.rope.ropeNode.setUvMode(RopeNode.UVDistance)
        self.rope.ropeNode.setUvDirection(0)
        self.rope.ropeNode.setUvScale(0.8)
        self.rope.setTexture(self.cage.findTexture('hq_chain'))
        self.rope.setTransparency(1)
        self.promotionMusic = base.loader.loadMusic('phase_7/audio/bgm/encntr_suit_winning_indoor.ogg')
        self.betweenBattleMusic = base.loader.loadMusic('phase_9/audio/bgm/encntr_toon_winning.ogg')
        self.battleOneMusic = base.loader.loadMusic('phase_9/audio/bgm/ttrm_s_ara_bgm_encntr_sbhq_boss_round1.ogg')
        self.battleTwoMusic = base.loader.loadMusic('phase_9/audio/bgm/ttrm_s_ara_bgm_encntr_sbhq_boss_round2.ogg')
        self.battleThreeMusic = base.loader.loadMusic('phase_9/audio/bgm/ttrm_s_ara_bgm_encntr_sbhq_boss_round3.ogg')
        self.geom.reparentTo(render)

        hood = base.cr.playGame.hood
        # Christmas VP
        if self.winter:

            # Change up the music
            self.elevatorMusic = base.loader.loadMusic('phase_14.5/audio/bgm/tt_elevator_winter.ogg')
            self.promotionMusic = base.loader.loadMusic('phase_14.5/audio/bgm/encntr_suit_winning_indoor_winter.ogg')
            self.stingMusic = base.loader.loadMusic('phase_14.5/audio/bgm/encntr_suit_winning_indoor_winter.ogg')
            self.battleOneMusic = base.loader.loadMusic('phase_14.5/audio/bgm/encntr_general_bg_winter.ogg')
            self.betweenBattleMusic = base.loader.loadMusic('phase_14.5/audio/bgm/encntr_toon_winning_winter.ogg')
            self.battleTwoMusic = base.loader.loadMusic('phase_14.5/audio/bgm/encntr_suit_winning_indoor_winter.ogg')
            self.battleThreeMusic = base.loader.loadMusic('phase_14.5/audio/bgm/encntr_suit_winning_indoor_winter.ogg')
            self.epilogueMusic = base.loader.loadMusic('phase_14.5/audio/bgm/encntr_hall_of_fame_winter.ogg')

            # Darken the geometry
            self.geom.setColorScale(0.7, 0.7, 0.7, 1.0)

            # Make it snow
            snow = BattleParticles.loadParticleFile('snowdisk.ptf')
            snow.setPos(0, 0, 5)
            snowRender = self.geom.attachNewNode('snowRender')
            snowRender.setDepthWrite(0)
            snowRender.setBin('fixed', 1)
            EnvironmentManager.setDefaultParticle(snow)
            EnvironmentManager.setDefaultParticleRender(snowRender)
            EnvironmentManager.setActiveParticle(snow)
            EnvironmentManager.setActiveParticleRender(snowRender)

            # Add flying Cogs
            self.flyingCogs = FlyingCogs.FlyingCogs()
            self.flyingCogs.startFlying(self.getDoId() - len(self.involvedToons))

            # Add the sky
            sky = loader.loadModel('phase_14.5/models/props/HD_sky')
            sky.setTag('sky', 'Regular')
            sky.setScale(2.5)
            sky.reparentTo(camera)
            sky.setTransparency(TransparencyAttrib.MDual, 1)
            ce = CompassEffect.make(NodePath(), CompassEffect.PRot | CompassEffect.PZ)
            sky.node().setEffect(ce)
            hood.sky.removeNode()
            hood.sky = sky
            EnvironmentManager.enableEnvironment()
        else:
            hood.startSky()
            sky = hood.sky
        sky.setH(150)
        sky.setZ(-100)

    def unloadEnvironment(self):
        DistributedBossCog.DistributedBossCog.unloadEnvironment(self)
        self.geom.removeNode()
        del self.geom
        del self.cage
        self.rampA.requestFinalState()
        self.rampB.requestFinalState()
        self.rampC.requestFinalState()
        del self.rampA
        del self.rampB
        del self.rampC

        if self.winter:

            # Cleanup snow
            EnvironmentManager.unloadEnvironment()

            # Remove flying Cogs
            if hasattr(self, 'flyingCogs') and self.flyingCogs:
                self.flyingCogs.delete()
                del self.flyingCogs

            # Revert holiday sky to cog sky in-case we teleport back to it
            if hasattr(base.cr.playGame, 'hood') and base.cr.playGame.hood:
                base.cr.playGame.hood.endHolidaySky()
                base.cr.playGame.hood.fixCogSky()
        elif hasattr(base.cr.playGame, 'hood') and base.cr.playGame.hood:
            # Revert the sky H and Z back to normal in-case we teleport back to it
            sky = base.cr.playGame.hood.sky
            sky.setH(0)
            sky.setZ(0)

    def __loadMopaths(self):
        self.toonsEnterA = Mopath.Mopath()
        self.toonsEnterA.loadFile('phase_9/paths/bossBattle-toonsEnterA')
        self.toonsEnterA.fFaceForward = 1
        self.toonsEnterA.timeScale = 35
        self.toonsEnterB = Mopath.Mopath()
        self.toonsEnterB.loadFile('phase_9/paths/bossBattle-toonsEnterB')
        self.toonsEnterB.fFaceForward = 1
        self.toonsEnterB.timeScale = 35

    def __unloadMopaths(self):
        self.toonsEnterA.reset()
        self.toonsEnterB.reset()

    def __findRamp(self, name, path):
        ramp = self.geom.find(path)
        children = ramp.getChildren()
        animate = ramp.attachNewNode(name)
        children.reparentTo(animate)
        fsm = ClassicFSM.ClassicFSM(name, [
            State.State('extend',
                        Functor(self.enterRampExtend, animate),
                        Functor(self.exitRampExtend, animate), [
                            'extended',
                            'retract',
                            'retracted']),
         State.State('extended',
                     Functor(self.enterRampExtended, animate),
                     Functor(self.exitRampExtended, animate), [
                         'retract',
                         'retracted']),
         State.State('retract',
                     Functor(self.enterRampRetract, animate),
                     Functor(self.exitRampRetract, animate), [
                         'extend',
                         'extended',
                         'retracted']),
         State.State('retracted',
                     Functor(self.enterRampRetracted, animate),
                     Functor(self.exitRampRetracted, animate), [
                         'extend',
                         'extended']),
         State.State('off',
                     Functor(self.enterRampOff, animate),
                     Functor(self.exitRampOff, animate))],
         'off', 'off', onUndefTransition=ClassicFSM.ClassicFSM.DISALLOW)
        fsm.enterInitialState()
        return fsm

    def __loadSnowPiles(self):
        if self.hardcore:
            pileInfo = ToontownGlobals.HolidayVPSnowPilesHardcore
        else:
            pileInfo = ToontownGlobals.HolidayVPSnowPiles
        for pos in pileInfo:
            pile = loader.loadModel('phase_14.5/models/props/snow_pile_fuller')
            pile.reparentTo(self.geom)
            pile.setPos(*pos)
            index = pileInfo.index(pos)
            random.seed(self.getDoId() * index)
            pile.setH(random.randrange(0, 360))
            pile.setScale(2.0)

            sphere = CollisionSphere(0, 0, 0, 3)
            sphere.setTangible(0)
            node = CollisionNode('SnowPile')
            node.addSolid(sphere)
            mask = ToontownGlobals.WallBitmask | ToontownGlobals.GhostBitmask
            node.setIntoCollideMask(mask)
            pile.attachNewNode(node)

    def enterRampExtend(self, animate):
        intervalName = self.uniqueName('extend-%s' % animate.getName())
        adjustTime = 2.0 * animate.getX() / 18.0
        ival = Parallel(SoundInterval(self.rampSlideSfx, volume = 0.5), animate.posInterval(adjustTime, Point3(0, 0, 0), blendType='easeInOut', name=intervalName))
        ival.start()
        self.storeInterval(ival, intervalName)

    def exitRampExtend(self, animate):
        intervalName = self.uniqueName('extend-%s' % animate.getName())
        self.clearInterval(intervalName)

    def enterRampExtended(self, animate):
        animate.setPos(0, 0, 0)

    def exitRampExtended(self, animate):
        pass

    def enterRampRetract(self, animate):
        intervalName = self.uniqueName('retract-%s' % animate.getName())
        adjustTime = 2.0 * (18 - animate.getX()) / 18.0
        ival = Parallel(SoundInterval(self.rampSlideSfx, volume = 0.5), animate.posInterval(adjustTime, Point3(18, 0, 0), blendType='easeInOut', name=intervalName))
        ival.start()
        self.storeInterval(ival, intervalName)

    def exitRampRetract(self, animate):
        intervalName = self.uniqueName('retract-%s' % animate.getName())
        self.clearInterval(intervalName)

    def enterRampRetracted(self, animate):
        animate.setPos(18, 0, 0)

    def exitRampRetracted(self, animate):
        pass

    def enterRampOff(self, animate):
        pass

    def exitRampOff(self, animate):
        pass

    def enterOff(self):
        DistributedBossCog.DistributedBossCog.enterOff(self)
        if self.cagedToon:
            self.cagedToon.clearChat()
        if self.rampA:
            self.rampA.request('off')
        if self.rampB:
            self.rampB.request('off')
        if self.rampC:
            self.rampC.request('off')

    def enterWaitForToons(self):
        DistributedBossCog.DistributedBossCog.enterWaitForToons(self)
        self.geom.hide()
        self.cagedToon.removeActive()

    def exitWaitForToons(self):
        DistributedBossCog.DistributedBossCog.exitWaitForToons(self)
        self.geom.show()
        self.cagedToon.addActive()

    def enterElevator(self):
        DistributedBossCog.DistributedBossCog.enterElevator(self)
        self.rampA.request('extended')
        self.rampB.request('extended')
        self.rampC.request('retracted')
        self.setCageIndex(0)
        self.reparentTo(render)
        self.setPosHpr(*ToontownGlobals.SellbotBossBattleOnePosHpr)
        self.happy = 1
        self.raised = 1
        self.forward = 1
        self.doAnimate()
        self.cagedToon.removeActive()

        if self.winter:
            self.setHealthIndicator('back_light')
            self.__flickerBulb()

    def exitElevator(self):
        DistributedBossCog.DistributedBossCog.exitElevator(self)
        self.cagedToon.addActive()

    def enterIntroduction(self):
        self.reparentTo(render)
        self.setPosHpr(*ToontownGlobals.SellbotBossBattleOnePosHpr)
        self.stopAnimate()
        DistributedBossCog.DistributedBossCog.enterIntroduction(self)
        self.rampA.request('extended')
        self.rampB.request('extended')
        self.rampC.request('retracted')
        self.setCageIndex(0)
        base.playMusic(self.promotionMusic, looping=1, volume=0.9)

    def exitIntroduction(self):
        DistributedBossCog.DistributedBossCog.exitIntroduction(self)
        self.promotionMusic.stop()

    def enterBattleOne(self):
        DistributedBossCog.DistributedBossCog.enterBattleOne(self)
        self.reparentTo(render)
        self.setPosHpr(*ToontownGlobals.SellbotBossBattleOnePosHpr)
        self.clearChat()
        self.cagedToon.clearChat()
        self.rampA.request('retract')
        self.rampB.request('retract')
        self.rampC.request('retract')
        if self.battleA == None or self.battleB == None:
            cageIndex = 1
        else:
            cageIndex = 0
        self.setCageIndex(cageIndex)
        return

    def exitBattleOne(self):
        DistributedBossCog.DistributedBossCog.exitBattleOne(self)

    def enterRollToBattleTwo(self):
        self.disableToonCollision()
        self.releaseToons()
        if self.arenaSide:
            self.rampA.request('retract')
            self.rampB.request('extend')
        else:
            self.rampA.request('extend')
            self.rampB.request('retract')
        self.rampC.request('retract')
        self.reparentTo(render)
        self.setCageIndex(2)
        self.stickBossToFloor()
        intervalName = 'RollToBattleTwo'
        seq = Sequence(self.__makeRollToBattleTwoMovie(), Func(self.__onToPrepareBattleTwo), name=intervalName)
        seq.start()
        self.storeInterval(seq, intervalName)
        base.playMusic(self.betweenBattleMusic, looping=1, volume=0.9)
        self.__showEasyBarrels()
        taskMgr.doMethodLater(0.5, self.enableToonCollision, 'enableToonCollision')

    def __onToPrepareBattleTwo(self):
        self.disableToonCollision()
        self.unstickBoss()
        self.setPosHpr(*ToontownGlobals.SellbotBossBattleTwoPosHpr)
        self.doneBarrier('RollToBattleTwo')

    def exitRollToBattleTwo(self):
        self.unstickBoss()
        intervalName = 'RollToBattleTwo'
        self.clearInterval(intervalName)
        self.betweenBattleMusic.stop()

    def disableToonCollision(self):
        base.localAvatar.collisionsOff()

    def enableToonCollision(self, task):
        base.localAvatar.collisionsOn()

    def enterPrepareBattleTwo(self):
        self.cleanupIntervals()
        self.__hideEasyBarrels()
        self.controlToons()
        self.clearChat()
        self.cagedToon.clearChat()
        self.reparentTo(render)
        if self.arenaSide:
            self.rampA.request('retract')
            self.rampB.request('extend')
        else:
            self.rampA.request('extend')
            self.rampB.request('retract')
        self.rampC.request('retract')
        self.reparentTo(render)
        self.setCageIndex(2)
        camera.reparentTo(render)
        camera.setPosHpr(self.cage, 0, -17, 3.3, 0, 0, 0)
        self.hide()
        self.acceptOnce(self.__donePageMsg, self.__onToBattleTwo)
        self.cagedToon.setLocalPageChat(TTLocalizer.CagedToonPrepareBattleTwo, 1)
        base.playMusic(self.stingMusic, looping=0, volume=1.0)
        taskMgr.doMethodLater(0.5, self.enableToonCollision, 'enableToonCollision')

    def __onToBattleTwo(self, elapsed):
        self.doneBarrier('PrepareBattleTwo')
        taskMgr.doMethodLater(1, self.__showWaitingMessage, self.uniqueName('WaitingMessage'))

    def exitPrepareBattleTwo(self):
        self.show()
        taskMgr.remove(self.uniqueName('WaitingMessage'))
        if self.__donePageMsg is not None:
            self.ignore(self.__donePageMsg)
        self.__clearOnscreenMessage()
        self.stingMusic.stop()

    def enterBattleTwo(self):
        self.cleanupIntervals()
        mult = ToontownBattleGlobals.getBossBattleCreditMultiplier(2)
        localAvatar.inventory.setBattleCreditMultiplier(mult)
        self.reparentTo(render)
        self.setPosHpr(*ToontownGlobals.SellbotBossBattleTwoPosHpr)
        self.clearChat()
        self.cagedToon.clearChat()
        self.rampA.request('retract')
        self.rampB.request('retract')
        self.rampC.request('retract')
        self.releaseToons()
        self.toonsToBattlePosition(self.toonsA, self.battleANode)
        self.toonsToBattlePosition(self.toonsB, self.battleBNode)
        if self.battleA == None or self.battleB == None:
            cageIndex = 3
        else:
            cageIndex = 2
        self.setCageIndex(cageIndex)
        base.playMusic(self.battleTwoMusic, looping=1, volume=0.9)
        return

    def exitBattleTwo(self):
        intervalName = self.uniqueName('cageDrop')
        self.clearInterval(intervalName)
        self.cleanupBattles()
        self.battleTwoMusic.stop()
        localAvatar.inventory.setBattleCreditMultiplier(1)

    def enterPrepareBattleThree(self):
        self.cleanupIntervals()
        self.controlToons()
        self.clearChat()
        self.cagedToon.clearChat()
        self.reparentTo(render)
        self.rampA.request('retract')
        self.rampB.request('retract')
        self.rampC.request('extend')
        self.setCageIndex(4)
        camera.reparentTo(render)
        camera.setPosHpr(self.cage, 0, -17, 3.3, 0, 0, 0)
        self.hide()
        self.acceptOnce(self.__donePageMsg, self.__onToBattleThree)
        if self.winter:
            dialog = ControlManager.ControlManager.parseHotkeyString(TTLocalizer.HolidayCagedToonPrepareBattleThree)
        else:
            dialog = ControlManager.ControlManager.parseHotkeyString(TTLocalizer.CagedToonPrepareBattleThree)
        self.cagedToon.setLocalPageChat(dialog, 1)
        base.playMusic(self.betweenBattleMusic, looping=1, volume=0.9)

    def __onToBattleThree(self, elapsed):
        self.doneBarrier('PrepareBattleThree')
        taskMgr.doMethodLater(1, self.__showWaitingMessage, self.uniqueName('WaitingMessage'))

    def exitPrepareBattleThree(self):
        self.show()
        taskMgr.remove(self.uniqueName('WaitingMessage'))
        if self.__donePageMsg is not None:
            self.ignore(self.__donePageMsg)
        intervalName = 'PrepareBattleThree'
        self.clearInterval(intervalName)
        self.__clearOnscreenMessage()
        self.betweenBattleMusic.stop()

    def enterBattleThree(self):
        DistributedBossCog.DistributedBossCog.enterBattleThree(self)
        self.clearChat()
        self.cagedToon.clearChat()
        self.reparentTo(render)
        self.rampA.request('retract')
        self.rampB.request('retract')
        self.rampC.request('extend')
        self.setCageIndex(4)
        self.happy = 0
        self.raised = 1
        self.forward = 1
        self.doAnimate()
        if self.winter:
            self.__loadSnowPiles()
            self.__flickerBulb()
            self.accept('enterSnowPile', self.__touchedSnow)
        self.accept('enterCage', self.__touchedCage)
        self.accept('pieSplat', self.__pieSplat)
        self.accept('localPieSplat', self.__localPieSplat)
        self.accept('outOfPies', self.__outOfPies)
        self.accept('begin-pie', self.__foundPieButton)
        taskMgr.doMethodLater(30, self.__howToGetPies, self.uniqueName('PieAdvice'))
        self.stickBossToFloor()
        self.bossDamageMovie = self.__makeBossDamageMovie()
        bossDoneEventName = self.uniqueName('DestroyedBoss')
        self.bossDamageMovie.setDoneEvent(bossDoneEventName)
        self.acceptOnce(bossDoneEventName, self.__doneBattleThree)
        self.resetMaxDamage()
        self.bossDamageToMovie = self.bossDamageMovie.getDuration() / self.bossMaxDamage
        self.bossDamageMovie.setT(self.bossDamage * self.bossDamageToMovie)
        self.updateHealthBar()
        base.playMusic(self.battleThreeMusic, looping=1, volume=0.9)

    def __doneBattleThree(self):
        self.setState('NearVictory')
        self.unstickBoss()

    def exitBattleThree(self):
        DistributedBossCog.DistributedBossCog.exitBattleThree(self)
        bossDoneEventName = self.uniqueName('DestroyedBoss')
        self.ignore(bossDoneEventName)
        taskMgr.remove(self.uniqueName('StandUp'))
        if self.winter:
            self.ignore('enterSnowPile')
        self.ignore('enterCage')
        self.ignore('pieSplat')
        self.ignore('localPieSplat')
        self.ignore('outOfPies')
        self.ignore('begin-pie')
        self.__clearOnscreenMessage()
        taskMgr.remove(self.uniqueName('PieAdvice'))
        self.removeHealthBar()
        self.__removeCageShadow()
        self.bossDamageMovie.finish()
        self.bossDamageMovie = None
        self.unstickBoss()
        taskName = 'RecoverBossDamage'
        taskMgr.remove(taskName)
        self.battleThreeMusicTime = self.battleThreeMusic.getTime()
        self.battleThreeMusic.stop()
        return

    def enterNearVictory(self):
        self.cleanupIntervals()
        self.reparentTo(render)
        if self.hardcore:
            pos = ToontownGlobals.SellbotBossDeathPosHardcore
        else:
            pos = ToontownGlobals.SellbotBossDeathPos
        self.setPos(*pos)
        self.setHpr(*ToontownGlobals.SellbotBossBattleThreeHpr)
        self.clearChat()
        self.cagedToon.clearChat()
        self.setCageIndex(4)
        self.releaseToons(finalBattle=1)
        self.rampA.request('retract')
        self.rampB.request('retract')
        self.rampC.request('extend')
        if self.winter:
            self.accept('enterSnowPile', self.__touchedSnow)
        self.accept('enterCage', self.__touchedCage)
        self.accept('pieSplat', self.__finalPieSplat)
        self.accept('localPieSplat', self.__localPieSplat)
        self.accept('outOfPies', self.__outOfPies)
        self.happy = 0
        self.raised = 0
        self.forward = 1
        self.doAnimate()
        self.setDizzy(1)
        base.playMusic(self.battleThreeMusic, looping=1, volume=0.9, time=self.battleThreeMusicTime)

    def exitNearVictory(self):
        if self.winter:
            self.ignore('enterSnowPile')
        self.ignore('enterCage')
        self.ignore('pieSplat')
        self.ignore('localPieSplat')
        self.ignore('outOfPies')
        self.__clearOnscreenMessage()
        taskMgr.remove(self.uniqueName('PieAdvice'))
        taskMgr.remove(self.uniqueName('hasFallen'))
        self.__removeCageShadow()
        self.setDizzy(0)
        self.battleThreeMusicTime = self.battleThreeMusic.getTime()
        self.battleThreeMusic.stop()

    def enterVictory(self):
        self.cleanupIntervals()
        self.reparentTo(render)
        if self.hardcore:
            pos = ToontownGlobals.SellbotBossDeathPosHardcore
        else:
            pos = ToontownGlobals.SellbotBossDeathPos
        self.setPos(*pos)
        self.setHpr(*ToontownGlobals.SellbotBossBattleThreeHpr)
        self.clearChat()
        self.cagedToon.clearChat()
        self.setCageIndex(4)
        self.releaseToons(finalBattle=1)
        self.rampA.request('retract')
        self.rampB.request('retract')
        self.rampC.request('extend')
        self.happy = 0
        self.raised = 0
        self.forward = 1
        self.doAnimate('Fb_fall', now=1)
        self.acceptOnce(self.animDoneEvent, self.__continueVictory)
        base.playMusic(self.battleThreeMusic, looping=1, volume=0.9, time=self.battleThreeMusicTime)

    def __continueVictory(self):
        self.stopAnimate()
        self.stash()
        self.doneBarrier('Victory')

    def exitVictory(self):
        self.stopAnimate()
        self.unstash()
        self.__removeCageShadow()
        self.battleThreeMusicTime = self.battleThreeMusic.getTime()
        self.battleThreeMusic.stop()

    def enterReward(self):
        self.cleanupIntervals()
        self.clearChat()
        self.cagedToon.clearChat()
        self.stash()
        self.stopAnimate()
        self.setCageIndex(4)
        self.releaseToons(finalBattle=1)
        self.toMovieMode()
        self.rampA.request('retract')
        self.rampB.request('retract')
        self.rampC.request('extend')
        panelName = self.uniqueName('reward')
        from toontown.battle import RewardPanel
        self.rewardPanel = RewardPanel.RewardPanel(panelName)
        from toontown.battle import MovieToonVictory
        victory, camVictory, skipper = MovieToonVictory.doToonVictory(1, self.involvedToons, self.toonRewardIds, self.toonRewardDicts, self.deathList, self.rewardPanel, allowGroupShot=0, uberList=self.uberList, noSkip=True)
        ival = Sequence(Parallel(victory, camVictory), Func(self.__doneReward))
        intervalName = 'RewardMovie'
        delayDeletes = []
        for toonId in self.involvedToons:
            toon = self.cr.doId2do.get(toonId)
            if toon:
                delayDeletes.append(DelayDelete.DelayDelete(toon, 'SellbotBoss.enterReward'))

        ival.delayDeletes = delayDeletes
        ival.start()
        self.storeInterval(ival, intervalName)
        base.playMusic(self.battleThreeMusic, looping=1, volume=0.9, time=self.battleThreeMusicTime)

    def __doneReward(self):
        self.doneBarrier('Reward')
        self.toWalkMode()

    def exitReward(self):
        intervalName = 'RewardMovie'
        self.clearInterval(intervalName)
        self.unstash()
        self.rewardPanel.destroy()
        del self.rewardPanel
        self.__removeCageShadow()
        self.battleThreeMusicTime = 0
        self.battleThreeMusic.stop()

    def enterEpilogue(self):
        self.cleanupIntervals()
        self.clearChat()
        self.cagedToon.clearChat()
        self.stash()
        self.stopAnimate()
        self.setCageIndex(4)
        self.controlToons()
        self.rampA.request('retract')
        self.rampB.request('retract')
        self.rampC.request('extend')
        self.__arrangeToonsAroundCage()
        camera.reparentTo(render)
        camera.setPosHpr(-24, 52, 27.5, -53, -13, 0)
        intervalName = 'EpilogueMovie'
        seq = Sequence(self.__makeCageOpenMovie(), name=intervalName)
        seq.start()
        self.storeInterval(seq, intervalName)
        if not self.winter:
            self.accept(self.__nextPageMsg, self.__epilogueChatNext)
            self.accept(self.__donePageMsg, self.__epilogueChatDone)
        base.playMusic(self.epilogueMusic, looping=1, volume=0.9)

    def __epilogueChatNext(self, pageNumber, elapsed):
        if pageNumber == 2:
            if self.cagedToon.style.torso[1] == 'd':
                track = ActorInterval(self.cagedToon, 'curtsy')
            else:
                track = ActorInterval(self.cagedToon, 'bow')
            track = Sequence(track, Func(self.cagedToon.loop, 'neutral'))
            intervalName = 'EpilogueMovieToonAnim'
            self.storeInterval(track, intervalName)
            track.start()

    def __epilogueChatDone(self, elapsed):
        if self.winter and hasattr(self, 'fireworkShow') and self.fireworkShow:
            self.fireworkShow.cleanupShow()
            del self.fireworkShow

        self.cagedToon.setChatAbsolute(TTLocalizer.CagedToonGoodbye, CFSpeech)
        if self.__nextPageMsg is not None:
            self.ignore(self.__nextPageMsg)
        if self.__donePageMsg is not None:
            self.ignore(self.__donePageMsg)
        intervalName = 'EpilogueMovieToonAnim'
        self.clearInterval(intervalName)
        track = Sequence(Wait(0.5), Func(self.releaseToons), Wait(3.0), Func(self.cagedToon.clearChat))
        self.storeInterval(track, intervalName)
        track.start()

    def exitEpilogue(self):
        self.clearInterval('EpilogueMovieToonAnim')
        self.unstash()
        self.__removeCageShadow()
        self.epilogueMusic.stop()

    def __arrangeToonsAroundCage(self):
        radius = 15
        numToons = len(self.involvedToons)
        center = (numToons - 1) / 2.0
        for i in range(numToons):
            toon = base.cr.doId2do.get(self.involvedToons[i])
            if toon:
                angle = 270 - 15 * (i - center)
                radians = angle * math.pi / 180.0
                x = math.cos(radians) * radius
                y = math.sin(radians) * radius
                toon.setPos(self.cage, x, y, 0)
                toon.setZ(18.0)
                toon.headsUp(self.cage)

    def enterFrolic(self):
        DistributedBossCog.DistributedBossCog.enterFrolic(self)
        self.setPosHpr(*ToontownGlobals.SellbotBossBattleOnePosHpr)

    def doorACallback(self, isOpen):
        if self.insidesANodePath:
            if isOpen:
                self.insidesANodePath.unstash()
            else:
                self.insidesANodePath.stash()

    def doorBCallback(self, isOpen):
        if self.insidesBNodePath:
            if isOpen:
                self.insidesBNodePath.unstash()
            else:
                self.insidesBNodePath.stash()

    def __toonsToPromotionPosition(self, toonIds, battleNode):
        points = BattleBase.BattleBase.toonPoints[len(toonIds) - 1]
        for i in range(len(toonIds)):
            toon = base.cr.doId2do.get(toonIds[i])
            if toon:
                toon.reparentTo(render)
                pos, h = points[i]
                toon.setPosHpr(battleNode, pos[0], pos[1] + 10, pos[2], h, 0, 0)

    def __doobersToPromotionPosition(self, doobers, battleNode):
        points = BattleBase.BattleBase.toonPoints[len(doobers) - 1]
        for i in range(len(doobers)):
            suit = doobers[i]
            suit.fsm.request('neutral')
            suit.loop('neutral')
            pos, h = points[i]
            suit.setPosHpr(battleNode, pos[0], pos[1] + 10, pos[2], h, 0, 0)

    def __touchedCage(self, entry):
        self.sendUpdate('touchCage', [])
        if not self.winter:
            self.__clearOnscreenMessage()
            taskMgr.remove(self.uniqueName('PieAdvice'))
            base.playSfx(self.piesRestockSfx)
            if not self.everThrownPie:
                taskMgr.doMethodLater(30, self.__howToThrowPies, self.uniqueName('PieAdvice'))

    def __touchedSnow(self, entry):
        self.sendUpdate('touchSnow', [])
        self.__clearOnscreenMessage()
        taskMgr.remove(self.uniqueName('PieAdvice'))
        base.playSfx(self.piesRestockSfx)
        if not self.everThrownPie:
            taskMgr.doMethodLater(30, self.__howToThrowPies, self.uniqueName('PieAdvice'))

    def __outOfPies(self):
        if self.winter:
            self.__showOnscreenMessage(TTLocalizer.HolidayBossBattleNeedMorePies)
        else:
            self.__showOnscreenMessage(TTLocalizer.BossBattleNeedMorePies)
        taskMgr.doMethodLater(20, self.__howToGetPies, self.uniqueName('PieAdvice'))

    def __howToGetPies(self, task):
        if self.winter:
            self.__showOnscreenMessage(TTLocalizer.HolidayBossBattleHowToGetPies)
        else:
            self.__showOnscreenMessage(TTLocalizer.BossBattleHowToGetPies)

    def __howToThrowPies(self, task):
        if self.winter:
            dialog = ControlManager.ControlManager.parseHotkeyString(TTLocalizer.HolidayBossBattleHowToThrowPies,
                                                                     useGlyphs=True)
        else:
            dialog = ControlManager.ControlManager.parseHotkeyString(TTLocalizer.BossBattleHowToThrowPies,
                                                                     useGlyphs=True)
        self.__showOnscreenMessage(dialog)

    def __foundPieButton(self):
        self.everThrownPie = 1
        self.__clearOnscreenMessage()
        taskMgr.remove(self.uniqueName('PieAdvice'))

    def __pieSplat(self, toon, pieCode):
        if base.config.GetBool('easy-vp', 0):
            if not self.dizzy:
                pieCode = ToontownGlobals.PieCodeBossInsides
        if pieCode == ToontownGlobals.PieCodeBossInsides:
            if toon == localAvatar:
                self.d_hitBossInsides()
            self.flashRed()
        elif pieCode == ToontownGlobals.PieCodeBossCog:
            if toon == localAvatar:
                self.d_hitBoss(1)
            if self.dizzy:
                self.flashRed()
                self.doAnimate('hit', now=1)

    def __localPieSplat(self, pieCode, entry, timestamp32):
        if self.pieTimestamp == timestamp32:
            return

        self.pieTimestamp = timestamp32

        if pieCode != ToontownGlobals.PieCodeToon:
            return
        avatarDoId = entry.getIntoNodePath().getNetTag('avatarDoId')
        if avatarDoId == '':
            self.notify.warning('Toon %s has no avatarDoId tag.' % repr(entry.getIntoNodePath()))
            return
        doId = int(avatarDoId)
        if doId != localAvatar.doId:
            # Commenting this out for now, because we implemented the functionality to Toon up others with pies *outside* of just Boss Battles
            #self.d_hitToon(doId)
            return

    def __finalPieSplat(self, toon, pieCode):
        if pieCode != ToontownGlobals.PieCodeBossCog:
            return
        self.sendUpdate('finalPieSplat', [])
        self.ignore('pieSplat')

    def cagedToonBattleThree(self, index, avId):
        if self.winter:
            str = TTLocalizer.HolidayCagedToonBattleThree.get(index)
        else:
            str = TTLocalizer.CagedToonBattleThree.get(index)
        if index in (21, 100):
            str = ControlManager.ControlManager.parseHotkeyString(str)
        if str:
            toonName = ''
            if avId:
                toon = self.cr.doId2do.get(avId)
                if not toon:
                    self.cagedToon.clearChat()
                    return
                toonName = toon.getName()
            text = str % {'toon': toonName}
            self.cagedToon.setChatAbsolute(text, CFSpeech | CFTimeout)
        else:
            self.cagedToon.clearChat()

    def cleanupAttacks(self):
        self.__cleanupStrafe()

    def __cleanupStrafe(self):
        if self.strafeInterval:
            self.strafeInterval.finish()
            self.strafeInterval = None
        return

    def doStrafe(self, side, direction):
        gearRoot = self.rotateNode.attachNewNode('gearRoot')
        if side == 0:
            gearRoot.setPos(0, -7, 3)
            gearRoot.setHpr(180, 0, 0)
            door = self.doorA
        else:
            gearRoot.setPos(0, 7, 3)
            door = self.doorB
        gearRoot.setTag('attackCode', str(ToontownGlobals.BossCogStrafeAttack))
        if self.winter:
            gearModel = self.getPresent()
            gearModel.setScale(0.4)
        else:
            gearModel = self.getGearFrisbee()
            gearModel.setScale(0.1)
        t = self.getBossDamage() / self.bossMaxDamage
        gearTrack = Parallel()
        numGears = int(4 + 6 * t + 0.5)
        time = 5.0 - 4.0 * t
        if self.hardcore:
            time -= 1
        spread = 60 * math.pi / 180.0
        if direction == 1:
            spread = -spread
        dist = 50
        rate = time / numGears
        for i in range(numGears):
            node = gearRoot.attachNewNode(str(i))
            node.hide()
            node.setPos(0, 0, 0)
            gear = gearModel.instanceTo(node)
            angle = (float(i) / (numGears - 1) - 0.5) * spread
            x = dist * math.sin(angle)
            y = dist * math.cos(angle)
            h = random.uniform(-720, 720)
            gearTrack.append(Sequence(Wait(i * rate), Func(node.show), Parallel(node.posInterval(1, Point3(x, y, 0), fluid=1), node.hprInterval(1, VBase3(h, 0, 0), fluid=1), Sequence(SoundInterval(self.strafeSfx[i], volume=0.2, node=self), duration=0)), Func(node.detachNode)))

        seq = Sequence(Func(door.request, 'open'), Wait(0.7), gearTrack, Func(door.request, 'close'))
        self.__cleanupStrafe()
        self.strafeInterval = seq
        seq.start()

    def __showEasyBarrels(self):
        barrelNodes = hidden.findAllMatches('**/Distributed*Barrel-*')
        if not barrelNodes or barrelNodes.isEmpty():
            return
        if render.find('barrelsRootNode'):
            self.notify.warning('__showEasyBarrels(): barrelsRootNode already exists')
            return
        self.barrelsRootNode = render.attachNewNode('barrelsRootNode')
        self.barrelsRootNode.setPos(*SellbotBossGlobals.BarrelsStartPos)
        if self.arenaSide == 0:
            self.barrelsRootNode.setHpr(180, 0, 0)
        else:
            self.barrelsRootNode.setHpr(0, 0, 0)
        for i, barrelNode in enumerate(barrelNodes):
            barrel = base.cr.doId2do.get(int(barrelNode.getNetTag('doId')))
            SellbotBossGlobals.setBarrelAttr(barrel, barrel.entId)
            if hasattr(barrel, 'applyLabel'):
                barrel.applyLabel()
            barrel.setPosHpr(barrel.pos, barrel.hpr)
            barrel.reparentTo(self.barrelsRootNode)

        intervalName = 'MakeBarrelsAppear'
        seq = Sequence(LerpPosInterval(self.barrelsRootNode, 0.5, Vec3(*SellbotBossGlobals.BarrelsFinalPos), blendType='easeInOut'), name=intervalName)
        seq.start()
        self.storeInterval(seq, intervalName)

    def __hideEasyBarrels(self):
        if hasattr(self, 'barrelsRootNode'):
            self.barrelsRootNode.removeNode()
            intervalName = 'MakeBarrelsAppear'
            self.clearInterval(intervalName)

    def __flickerBulb(self):
        taskName = self.uniqueName('flickerBulb')
        if not taskMgr.hasTaskNamed(taskName):
            taskMgr.doMethodLater(1.4, self.colorBulb, taskName)
        else:
            taskMgr.remove(taskName)
            if self.healthIndicator:
                self.healthIndicator.setColor(1, 1, 1, 1)

    def toonPromoted(self, promoted):
        self.localToonPromoted = promoted

    def setMode(self, mode):
        DistributedBossCog.DistributedBossCog.setMode(self, mode)

        # If we're entering with Winter Mode, force enable it
        if mode == ToontownGlobals.BossPartySellbotBossWinter:
            self.winter = True
            self.setDNAString(self.getDNAString(), holiday=1)

        # If we're entering with Nerfed Mode (Storm Sellbot), force enable it
        if mode == ToontownGlobals.BossPartySellbotBossStormSellbot:
            self.nerfed = True

        if mode == ToontownGlobals.BossPartySellbotBossHardcore:
            self.hardcore = True

    def hasFallen(self, task):
        threshold = -52.5
        if base.localAvatar.getZ() < threshold:
            self.fallOut()
            return task.done

        return task.again

    def makeFallMovie(self, delayDeletes):
        for toonId in self.involvedToons:
            toon = base.cr.doId2do.get(toonId)
            if toon:
                delayDeletes.append(DelayDelete.DelayDelete(toon, 'SellbotBoss.makeFallMovie'))

        # Kills the Toon
        track = Sequence(Parallel(SoundInterval(self.fallSfx, node=base.localAvatar),
                                  ActorInterval(base.localAvatar, 'melt', startFrame=40),
                                  ActorInterval(base.localAvatar, 'jump-idle', partName='legs'),
                                  LerpPosInterval(base.localAvatar, 1.0, base.localAvatar.getPos() - Vec3(0, 0, 20))),
                         Wait(1.0),
                         Parallel(SoundInterval(self.landSfx, node=base.localAvatar),
                                  Func(base.localAvatar.d_squish, base.localAvatar.getHp()),
                                  Func(self.d_avatarExit)))
        return Sequence(Func(camera.wrtReparentTo, render), track)

    def fallOut(self):
        self.controlToons()
        NametagGlobals.setMasterArrowsOn(0)
        intervalName = 'FallOutMovie'
        delayDeletes = []
        seq = Sequence(self.makeFallMovie(delayDeletes), name=intervalName)
        seq.delayDeletes = delayDeletes
        seq.start()
        self.storeInterval(seq, intervalName)

