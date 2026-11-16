from direct.directutil import Mopath
from direct.distributed.ClockDelta import *
from direct.fsm import FSM
from direct.gui.DirectGui import *
from direct.interval.IntervalGlobal import *
from direct.showutil import Rope
from panda3d.toontown import CFSpeech, CFTimeout

from otp.audio import AdaptiveMusic
from toontown.battle import BattleBase
from toontown.battle.BattleProps import *
from toontown.building import ElevatorConstants
from toontown.distributed import DelayDelete
from toontown.toon import NPCToons
from toontown.toonbase import TTLocalizer, ControlManager
from toontown.toonbase import ToontownGlobals
from toontown.toonbase.ToontownTimer import ToontownTimer
from . import DistributedBossCog
from . import SuitDNA
from ..instancedgames.InstancedGamesGUI import ToonPortrait

OneBossCog = None

TEAM_RED = 0
TEAM_BLUE = 1

BOSS_DONE_EVENT = 'DestroyedBoss'

class Ramp(FSM.FSM):
    defaultTransitions = {'Extend': ['Extended', 'Retract', 'Retracted'],
                          'Extended': ['Retract', 'Retracted'],
                          'Retract': ['Extend', 'Extended', 'Retracted'],
                          'Retracted': ['Extend', 'Extended']
                          }

    def __init__(self, name, animate, boss):
        FSM.FSM.__init__(self, name)
        self.boss = boss
        self.animate = animate

    def enterExtend(self):
        intervalName = self.boss.uniqueName('extend-%s' % self.animate.getName())
        adjustTime = 2.0 * self.animate.getX() / 18.0
        ival = Parallel(SoundInterval(self.boss.rampSlideSfx, node = self.animate),
                        self.animate.posInterval(adjustTime, Point3(0, 0, 0), blendType = 'easeInOut',
                                                 name = intervalName))
        ival.start()
        self.boss.storeInterval(ival, intervalName)

    def exitExtend(self):
        intervalName = self.boss.uniqueName('extend-%s' % self.animate.getName())
        self.boss.clearInterval(intervalName)

    def enterExtended(self):
        self.animate.setPos(0, 0, 0)

    def exitExtended(self):
        pass

    def enterRetract(self):
        intervalName = self.boss.uniqueName('retract-%s' % self.animate.getName())
        adjustTime = 2.0 * (18 - self.animate.getX()) / 18.0
        ival = Parallel(SoundInterval(self.boss.rampSlideSfx, node = self.animate),
                        self.animate.posInterval(adjustTime, Point3(18, 0, 0), blendType = 'easeInOut',
                                                 name = intervalName))
        ival.start()
        self.boss.storeInterval(ival, intervalName)

    def exitRetract(self):
        intervalName = self.boss.uniqueName('retract-%s' % self.animate.getName())
        self.boss.clearInterval(intervalName)

    def enterRetracted(self):
        self.animate.setPos(18, 0, 0)

    def exitRetracted(self):
        pass

    def enterOff(self):
        pass

    def exitOff(self):
        pass


class DistributedSellbotArena(DistributedBossCog.DistributedBossCog, FSM.FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedSellbotArena')
    cageHeights = [100, 81, 63, 44, 25, 18]

    def __init__(self, cr):
        DistributedBossCog.DistributedBossCog.__init__(self, cr)
        FSM.FSM.__init__(self, 'DistributedSellbotArena')
        self.timer = ToontownTimer()
        self.timer.hide()
        self.timer.posBelowTopRightCorner()
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
        self.pieDamageMult = {ToontownGlobals.BossArenaTeamA: 1,
                              ToontownGlobals.BossArenaTeamB: 1}
        self.battleOneMusicTime = 0
        self.insidesANodePath = None
        self.insidesBNodePath = None
        self.targetNodePath = None
        self.rampC = None
        self.strafeInterval = None
        self.onscreenMessage = None
        self.toonMopathInterval = []
        self.nerfed = ToontownGlobals.SELLBOT_NERF_HOLIDAY in base.cr.newsManager.getHolidayIdList()
        self.resetMaxDamage()
        self.isWinning = None
        self.__nextPageMsg = None
        self.__donePageMsg = None
        self.wantBackAttack = True

    def announceGenerate(self):
        global OneBossCog
        DistributedBossCog.DistributedBossCog.announceGenerate(self)
        self.setName(TTLocalizer.SellbotBossName)
        nameInfo = TTLocalizer.BossCogNameWithDept % {'name': self._name,
                                                      'dept': SuitDNA.getDeptFullname(self.style.dept)
                                                      }
        self.setDisplayName(nameInfo)
        self.cageDoorSfx = loader.loadSfx('phase_5/audio/sfx/CHQ_SOS_cage_door.ogg')
        self.cageLandSfx = loader.loadSfx('phase_9/audio/sfx/CHQ_SOS_cage_land.ogg')
        self.cageLowerSfx = loader.loadSfx('phase_5/audio/sfx/CHQ_SOS_cage_lower.ogg')
        self.piesRestockSfx = loader.loadSfx('phase_9/audio/sfx/CHQ_SOS_pies_restock.ogg')
        self.rampSlideSfx = loader.loadSfx('phase_9/audio/sfx/CHQ_VP_ramp_slide.ogg')
        self.strafeSfx = []
        for i in range(10):
            self.strafeSfx.append(loader.loadSfx('phase_3.5/audio/sfx/SA_shred.ogg'))

        render.setTag('pieCode', str(ToontownGlobals.PieCodeNotBossCog))
        insidesA = CollisionPolygon(Point3(4.0, -2.0, 5.0), Point3(-4.0, -2.0, 5.0), Point3(-4.0, -2.0, 0.5),
                                    Point3(4.0, -2.0, 0.5))
        insidesANode = CollisionNode('BossZap')
        insidesANode.addSolid(insidesA)
        insidesANode.setCollideMask(ToontownGlobals.PieBitmask | ToontownGlobals.WallBitmask)
        self.insidesANodePath = self.axle.attachNewNode(insidesANode)
        self.insidesANodePath.setTag('pieCode', str(ToontownGlobals.PieCodeBossInsides))
        self.insidesANodePath.stash()
        insidesB = CollisionPolygon(Point3(-4.0, 2.0, 5.0), Point3(4.0, 2.0, 5.0), Point3(4.0, 2.0, 0.5),
                                    Point3(-4.0, 2.0, 0.5))
        insidesBNode = CollisionNode('BossZap')
        insidesBNode.addSolid(insidesB)
        insidesBNode.setCollideMask(ToontownGlobals.PieBitmask | ToontownGlobals.WallBitmask)
        self.insidesBNodePath = self.axle.attachNewNode(insidesBNode)
        self.insidesBNodePath.setTag('pieCode', str(ToontownGlobals.PieCodeBossInsides))
        self.insidesBNodePath.stash()
        disk = loader.loadModel('phase_9/models/char/bossCog-gearCollide')
        disk.find('**/+CollisionNode').setName('BossZap')
        disk.reparentTo(self.pelvis)
        disk.setZ(0.8)
        self.loadEnvironment()
        self.__makeCagedToon()
        self.__loadMopaths()

        if OneBossCog:
            self.notify.warning('Multiple BossCogs visible.')
        OneBossCog = self

        self.bossDoneEvent = self.uniqueName(BOSS_DONE_EVENT)

    def disable(self):
        global OneBossCog
        DistributedBossCog.DistributedBossCog.disable(self)

        self.request('Off')
        self.timer.destroy()
        self.unloadEnvironment()
        self.__unloadMopaths()
        self.__cleanupCagedToon()
        self.__clearOnscreenMessage()
        taskMgr.remove(self.uniqueName('PieAdvice'))
        self.__cleanupStrafe()
        render.clearTag('pieCode')
        if self.targetNodePath:
            self.targetNodePath.detachNode()
        self.cr.relatedObjectMgr.abortRequest(self.dooberRequest)
        self.dooberRequest = None
        self.promotionMusic.stop()
        self.battleOneMusic.stop()
        self.epilogueMusic.stop()
        while len(self.toonMopathInterval):
            toonMopath = self.toonMopathInterval[0]
            toonMopath.finish()
            toonMopath.destroy()
            self.toonMopathInterval.remove(toonMopath)

        if OneBossCog == self:
            OneBossCog = None
        self.__nextPageMsg = None
        self.__donePageMsg = None

    def setToonIds(self, involvedToons, toonsA, toonsB):
        DistributedBossCog.DistributedBossCog.setToonIds(self, involvedToons, toonsA, toonsB)

        if base.localAvatar.doId in toonsA:
            target = CollisionTube(0, 1, 4, 0, 1, 7, 3.5)
            shield = CollisionTube(0, -1, 4, 0, -1, 9, 3.5)
        else:
            target = CollisionTube(0, -1, 4, 0, -1, 9, 3.5)
            shield = CollisionTube(0, 1, 4, 0, 1, 7, 3.5)

        targetNode = CollisionNode('BossZap')
        targetNode.addSolid(target)
        targetNode.setCollideMask(ToontownGlobals.PieBitmask)
        self.targetNodePath = self.pelvis.attachNewNode(targetNode)
        self.targetNodePath.setTag('pieCode', str(ToontownGlobals.PieCodeBossCog))

        shieldNode = CollisionNode('BossZap')
        shieldNode.addSolid(shield)
        shieldNode.setCollideMask(ToontownGlobals.PieBitmask | ToontownGlobals.CameraBitmask)
        shieldNodePath = self.pelvis.attachNewNode(shieldNode)

    def resetMaxDamage(self):
        self.bossMaxDamage = ToontownGlobals.SellbotBossMaxDamage

    def d_hitBoss(self):
        self.sendUpdate('hitBoss', [])

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
        self.dooberRequest = self.cr.relatedObjectMgr.requestObjects(dooberIds, allCallback = self.__gotDoobers)

    def __gotDoobers(self, doobers):
        self.dooberRequest = None
        self.doobers = doobers

    def setBossDamage(self, bossDamage, recoverRate, timestamp):
        self.notify.info("setBossDamage: {}".format(bossDamage))

        recoverStartTime = globalClockDelta.networkToLocalTime(timestamp)
        lastBossDamage = self.bossDamage
        self.bossDamage = bossDamage
        self.recoverRate = recoverRate
        self.recoverStartTime = recoverStartTime
        taskName = 'RecoverBossDamage'
        taskMgr.remove(taskName)
        if self.bossDamageMovie:
            # Support for hitting him both directions
            if self.bossDamage >= self.bossMaxDamage or self.bossDamage <= self.bossMaxDamage:

                # self.bossDamageMovie.resumeUntil(self.bossDamageMovie.getDuration())
                duration = self.bossDamageMovie.getDuration() / 2 + (self.bossDamage * self.bossDamageToMovie / 2)
                if duration - self.bossDamageMovie.getT() != 0:
                    if self.bossDamage < lastBossDamage:
                        startT = duration
                        endT = self.bossDamageMovie.getT()

                        self.bossDamageMovie.start(startT = startT, endT = endT, playRate = -1)
                    else:
                        startT = self.bossDamageMovie.getT()
                        endT = duration

                        self.bossDamageMovie.start(startT = startT, endT = endT, playRate = 1)

                    # If Team B won or Team A won...
                    if self.bossDamage >= self.bossMaxDamage or self.bossDamage <= -self.bossMaxDamage:
                        delay = endT - startT

                        # Allow the NearVictory state to activate.
                        # This will make the VP fall off, and allow the game to end.
                        self.addTask(self.__doneBattleOne, self.bossDoneEvent, 
                                     delay = delay, extraArgs = [])

                if self.recoverRate:
                    taskMgr.add(self.__recoverBossDamage, taskName)
        self.updateHealthBar()
        if hasattr(self, 'progressBarIcon'):
            self.progressBarIcon.setX(self.bossDamage / 80.)

        if self.__getWinningTeam() == self.__getTeam():
            self.battleMusic.changeMix(AdaptiveMusic.FULL_A)
        else:
            self.battleMusic.changeMix(AdaptiveMusic.FULL_B)

    def getBossDamage(self):
        now = globalClock.getFrameTime()
        elapsed = now - self.recoverStartTime
        return self.bossDamage - self.recoverRate * elapsed / 60.0

    def setPieDamageMult(self, teamAMult, teamBMult):
        self.pieDamageMult[ToontownGlobals.BossArenaTeamA] = teamAMult
        self.pieDamageMult[ToontownGlobals.BossArenaTeamB] = teamBMult

    def getPieDamageMult(self):
        return self.pieDamageMult

    def __getWinningTeam(self):
        if self.bossDamage < 0:
            return TEAM_RED
        elif self.bossDamage > 0:
            return TEAM_BLUE
        else:
            return None

    def __getTeam(self):
        if base.localAvatar.doId in self.toonsA:
            return TEAM_RED
        elif base.localAvatar.doId in self.toonsB:
            return TEAM_BLUE
        else:
            return None

    def __recoverBossDamage(self, task):
        self.bossDamageMovie.setT(self.getBossDamage() * self.bossDamageToMovie)
        return task.cont

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
        touch = CollisionPolygon(Point3(-3.0382, 3.0382, -1), Point3(3.0382, 3.0382, -1), Point3(3.0382, -3.0382, -1),
                                 Point3(-3.0382, -3.0382, -1))
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
            ival = Sequence(Wait(delay), Func(toon.suit.setPlayRate, 1, 'walk'), Func(toon.suit.loop, 'walk'),
                            toon.posInterval(1, Point3(0, 90, 20)),
                            ParallelEndTogether(walkMopath, toon.posInterval(2, destPos, blendType = 'noBlend')),
                            Func(toon.suit.loop, 'neutral'))
            self.toonMopathInterval.append(walkMopath)
            track.append(ival)
            delayDeletes.append(DelayDelete.DelayDelete(toon, 'SellbotArena.__walkToonToPromotion'))

    def __walkDoober(self, suit, delay, turnPos, track, delayDeletes):
        turnPos = Point3(*turnPos)
        turnPosDown = Point3(*ToontownGlobals.SellbotBossDooberTurnPosDown)
        pos = ToontownGlobals.SellbotBossDooberFlyPos
        flyPos = Point3(*pos)
        seq = Sequence(Func(suit.headsUp, turnPos), Wait(delay), Func(suit.loop, 'walk', 0),
                       self.__walkSuitToPoint(suit, suit.getPos(), turnPos),
                       self.__walkSuitToPoint(suit, turnPos, turnPosDown))
        seq.append(self.__walkSuitToPoint(suit, turnPosDown, flyPos))
        seq.append(Sequence(suit.beginSupaFlyMove(flyPos, 0, 'flyAway'), Func(suit.fsm.request, 'Off')))
        track.append(seq)
        delayDeletes.append(DelayDelete.DelayDelete(suit, 'SellbotArena.__walkDoober'))

    def __walkSuitToPoint(self, node, fromPos, toPos):
        vector = Vec3(toPos - fromPos)
        distance = vector.length()
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
        track = Parallel(
                self.closeDoors, self.loseCogSuits(self.involvedToons, self.cage, (0, -17, 3.3, 0, 0, 0)),
                Sequence(
                        Func(self.cagedToon.setChatAbsolute,
                             'Hello. This cutscene has been shortened for testing. Have fun.',
                             CFSpeech | CFTimeout),
                        Wait(2),
                        Sequence(
                                Parallel(
                                        LerpColorScaleInterval(aspect2d, 0.2, VBase4(1.0, 1.0, 1.0, 0.0)),
                                        LerpPosInterval(self.introScreenLeft, 0.5, Vec3(0, 0, 0),
                                                        startPos = Vec3(0, 0, 10), blendType = 'easeIn'),
                                        LerpPosInterval(self.introScreenRight, 0.5, Vec3(0, 0, 0),
                                                        startPos = Vec3(0, 0, -10), blendType = 'easeIn')),
                                Parallel(
                                        Func(self.introSplitSeparator.show),
                                        LerpScaleInterval(self.introSplitSeparator, 0.6, Vec3(0.02, 1.0, 3.0),
                                                          startScale = Vec3(0.02, 1.0, 0.001), blendType = 'easeOut'),
                                        LerpColorScaleInterval(self.introVersus, 0.2, VBase4(1.0, 1.0, 1.0, 1.0)),
                                ),
                                Wait(5),
                                Parallel(
                                        LerpColorScaleInterval(aspect2d, 0.2, VBase4(1.0, 1.0, 1.0, 1.0)),
                                        LerpPosInterval(self.introScreenLeft, 0.5, Vec3(0, 0, 10),
                                                        blendType = 'easeIn'),
                                        LerpPosInterval(self.introScreenRight, 0.5, Vec3(0, 0, -10),
                                                        blendType = 'easeIn'),
                                        LerpScaleInterval(self.introSplitSeparator, 0.2, Vec3(0.02, 1.0, 0.001),
                                                          blendType = 'easeIn'),
                                        LerpColorScaleInterval(self.introVersus, 0.2,
                                                               VBase4(1.0, 1.0, 1.0, 0.0))),
                                Func(self.introSplitSeparator.hide)
                        )
                ),
        )
        '''
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
        self.clearChat()
        self.cagedToon.clearChat()
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
                Func(camera.setPosHpr, -23.1, 15.7, 17.2, -160, -2.4, 0))),
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
                Func(camera.setPosHpr, -22.72, -35.09, 8.73, -88, 25, 0),
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
                Parallel(self.backupToonsToBattlePosition(self.toonsA, self.battleANode),
                         self.backupToonsToBattlePosition(self.toonsB, self.battleBNode),
                         Sequence(
                             Wait(2),
                             Func(self.setChatAbsolute, attackToons, CFSpeech),
                                 Sequence(
                                         Parallel(
                                                 LerpColorScaleInterval(aspect2d, 0.2, VBase4(1.0, 1.0, 1.0, 0.0)),
                                                 LerpPosInterval(self.introScreenLeft, 0.5, Vec3(0, 0, 0),
                                                                 startPos = Vec3(0, 0, 10), blendType = 'easeIn'),
                                                 LerpPosInterval(self.introScreenRight, 0.5, Vec3(0, 0, 0),
                                                                 startPos = Vec3(0, 0, -10), blendType = 'easeIn')),
                                         LerpColorScaleInterval(self.introVersus, 0.2, VBase4(1.0, 1.0, 1.0, 1.0)),
                                         Wait(5),
                                         Parallel(
                                                 LerpColorScaleInterval(aspect2d, 0.2, VBase4(1.0, 1.0, 1.0, 1.0)),
                                                 LerpPosInterval(self.introScreenLeft, 0.5, Vec3(0, 0, 10),
                                                                 blendType = 'easeIn'),
                                                 LerpPosInterval(self.introScreenRight, 0.5, Vec3(0, 0, -10),
                                                                 blendType = 'easeIn'),
                                                 LerpColorScaleInterval(self.introVersus, 0.2,
                                                                        VBase4(1.0, 1.0, 1.0, 0.0))),
                                 )
                         )))))
        track.append(dialogTrack)
        '''
        return Sequence(Func(self.stickToonsToFloor), track, Func(self.unstickToons),
                        name = self.uniqueName('Introduction'))

    def __makeBossDamageMovie(self):
        # startPos = Point3(ToontownGlobals.SellbotBossBattleTwoPosHpr[0],
        # ToontownGlobals.SellbotBossBattleTwoPosHpr[1], ToontownGlobals.SellbotBossBattleTwoPosHpr[2])
        # startHpr = Point3(*ToontownGlobals.SellbotBossBattleThreeHpr)

        # The V.P. starts out at the end of Team B's side
        startPos = Vec3(*ToontownGlobals.SellbotArenaTeamBDeathPos)
        startHpr = Vec3(*ToontownGlobals.SellbotArenaBattleOneHpr)
        self.setPosHpr(startPos, startHpr)

        bottomTeamBPos = Vec3(*ToontownGlobals.SellbotArenaTeamBBottomPos)
        centerPos = Vec3(*ToontownGlobals.SellbotArenaCenterPos)
        bottomTeamAPos = Vec3(*ToontownGlobals.SellbotArenaTeamABottomPos)
        deathTeamAPos = Vec3(*ToontownGlobals.SellbotArenaTeamADeathPos)

        # Create an empty interval and loop neutral animation
        bossTrack = Sequence(name = 'VPDamageTrack')
        bossTrack.append(Func(self.loop, 'Fb_neutral'))

        # Move us up to the bottom position
        track, hpr = self.rollBossToPoint(startPos, startHpr, bottomTeamBPos, None, 1)
        bossTrack.append(track)

        # Move us up to the center position
        track, hpr = self.rollBossToPoint(bottomTeamBPos, startHpr, centerPos, None, 1)
        bossTrack.append(track)

        # Move us down to Team A's bottom position
        track, hpr = self.rollBossToPoint(centerPos, startHpr, bottomTeamAPos, None, 1)
        bossTrack.append(track)

        # Move us down to Team A's death position
        track, hpr = self.rollBossToPoint(bottomTeamAPos, startHpr, deathTeamAPos, None, 1)
        bossTrack.append(track)

        return bossTrack

    def __talkAboutPromotion(self, speech):
        # Maybe do something here if we keep epilogue movie but maybe not
        return speech

    def __makeCageOpenMovie(self):
        speech = TTLocalizer.CagedToonThankYou
        speech = self.__talkAboutPromotion(speech)
        name = self.uniqueName('CageOpen')
        seq = Sequence(Func(self.cage.setPos, self.cagePos[4]),
                       Func(self.cageDoor.setHpr, VBase3(0, 0, 0)),
                       Func(self.cagedToon.setPos, Point3(0, -2, 0)),
                       Parallel(
                               self.cage.posInterval(0.5, self.cagePos[5], blendType = 'easeOut'),
                               SoundInterval(self.cageLowerSfx, duration = 0.5)),
                       Parallel(
                               self.cageDoor.hprInterval(0.5, VBase3(0, 90, 0), blendType = 'easeOut'),
                               Sequence(SoundInterval(self.cageDoorSfx), duration = 0)),
                       Wait(0.2),
                       Func(self.cagedToon.loop, 'walk'),
                       self.cagedToon.posInterval(0.8, Point3(0, -6, 0)),
                       Func(self.cagedToon.setChatAbsolute, TTLocalizer.CagedToonYippee, CFSpeech),
                       ActorInterval(self.cagedToon, 'jump'),
                       Func(self.cagedToon.loop, 'neutral'),
                       Func(self.cagedToon.headsUp, localAvatar))

        seq.append(Sequence(Func(camera.reparentTo, localAvatar),
                            Func(camera.setPos, 0, -9, 9),
                            Func(camera.lookAt, self.cagedToon, Point3(0, 0, 2), name = name),
                            Func(self.cagedToon.setLocalPageChat, speech, 0)))

        return seq

    def __showOnscreenMessage(self, text):
        if self.onscreenMessage:
            self.onscreenMessage.destroy()
            self.onscreenMessage = None
        self.onscreenMessage = DirectLabel(text = text, text_fg = VBase4(1, 1, 1, 1), text_align = TextNode.ACenter,
                                           relief = None, pos = (0, 0, 0.35), scale = 0.1)

    def __clearOnscreenMessage(self):
        if self.onscreenMessage:
            self.onscreenMessage.destroy()
            self.onscreenMessage = None

    def __showWaitingMessage(self, task):
        self.__showOnscreenMessage(TTLocalizer.BuildingWaitingForVictors)
        return task.done

    def __placeCageShadow(self):
        if not self.cageShadow:
            self.cageShadow = loader.loadModel('phase_3/models/props/drop_shadow')
            self.cageShadow.setPos(0, 77.9, 18)
            self.cageShadow.setColorScale(1, 1, 1, 0.6)
        self.cageShadow.reparentTo(render)

    def __removeCageShadow(self):
        if self.cageShadow:
            self.cageShadow.detachNode()

    def setCageIndex(self, cageIndex):
        self.cageIndex = cageIndex
        self.cage.setPos(self.cagePos[self.cageIndex])
        if self.cageIndex >= 4:
            self.__placeCageShadow()
        else:
            self.__removeCageShadow()

    def loadEnvironment(self):
        DistributedBossCog.DistributedBossCog.loadEnvironment(self)

        path = 'phase_14.5/models/modules/ttoff_m_ara_mg_sbsd_arena'
        self.geom = loader.loadModel(path)
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
        self.rope = Rope.Rope(name = 'supportChain')
        self.rope.reparentTo(self.cage)
        self.rope.setup(2, ((self.cage, (0.15, 0.13, 16)), (self.geom, (0.23, 78, 120))))
        self.rope.ropeNode.setRenderMode(RopeNode.RMBillboard)
        self.rope.ropeNode.setUvMode(RopeNode.UVDistance)
        self.rope.ropeNode.setUvDirection(0)
        self.rope.ropeNode.setUvScale(0.8)
        self.rope.ropeNode.setNumSubdiv(6)
        self.rope.setTexture(loader.loadTexture('phase_14.5/maps/ttoff_t_mg_sbsd_arena_cageChain.png'))
        self.rope.setTransparency(1)
        self.promotionMusic = base.loader.loadMusic('phase_7/audio/bgm/encntr_suit_winning_indoor.ogg')

        # Change this up probably
        self.battleOneMusic = base.loader.loadMusic('phase_7/audio/bgm/encntr_suit_winning_indoor.ogg')

        self.battleMusic = AdaptiveMusic.AdaptiveMusic('phase_14.5/audio/bgm/ttoff_s_ara_mg_sbsd_winning.ogg',
                                                       'phase_14.5/audio/bgm/ttoff_s_ara_mg_sbsd_losing.ogg')

        self.geom.reparentTo(render)
        # Set up the VP sky
        hood = base.cr.playGame.hood
        hood.startSky()
        sky = hood.sky
        sky.setH(150)
        sky.setZ(-100)

    def placeToonInElevator(self, toon):
        self.putToonInCogSuit(toon)
        toonIndex = self.involvedToons.index(toon.doId)
        toon.reparentTo(self.elevatorModel)
        toon.setPos(*ElevatorConstants.ArenaElevatorPoints[toonIndex])
        toon.setHpr(180, 0, 0)
        toon.suit.loop('neutral')

    def unloadEnvironment(self):
        DistributedBossCog.DistributedBossCog.unloadEnvironment(self)
        self.geom.removeNode()
        del self.geom
        del self.cage
        self.rampC.cleanup()
        del self.rampC

        # Revert the cog hq sky back to normal
        if hasattr(base.cr.playGame, 'hood') and base.cr.playGame.hood:
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
        return Ramp(name, animate, self)

    def enterOff(self):
        DistributedBossCog.DistributedBossCog.enterOff(self)
        if self.cagedToon:
            self.cagedToon.clearChat()
        if self.rampC:
            self.rampC.request('Off')

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
        self.rampC.request('Retracted')
        self.setCageIndex(0)
        self.reparentTo(render)
        self.setPosHpr(*ToontownGlobals.SellbotBossBattleOnePosHpr)
        self.happy = 1
        self.raised = 1
        self.forward = 1
        self.doAnimate()
        self.cagedToon.removeActive()

    def exitElevator(self):
        DistributedBossCog.DistributedBossCog.exitElevator(self)
        self.cagedToon.addActive()

    def enterIntroduction(self):
        w, h = base.win.getSize()
        # Create two buffers for each side of the screen
        self.introLBuffer = base.win.makeTextureBuffer("sbsd_intro_LBuffer", w, h)  # type: GraphicsOutput
        self.introRBuffer = base.win.makeTextureBuffer("sbsd_intro_SBuffer", w, h)  # type: GraphicsOutput
        # For each buffer, make an actual camera
        self.introLCam = base.makeCamera(self.introLBuffer, aspectRatio = 1.0, displayRegion = (0, 0.6, 0, 1))
        self.introRCam = base.makeCamera(self.introRBuffer, aspectRatio = 1.0, displayRegion = (0.4, 1, 0, 1))
        self.introLCam.node().getLens().setMinFov(60)
        self.introRCam.node().getLens().setMinFov(60)

        self.introLCam.reparentTo(render)
        self.introLCam.setPosHpr(-10, -75, 3, 55, 20, 0)

        self.introRCam.reparentTo(render)
        self.introRCam.setPosHpr(10, -75, 3, -55, 20, 0)

        # this is the actual model itself
        self.introScreen = loader.loadModel('phase_14.5/models/gui/ttoff_m_gui_mg_sbsd_splitScreen.bam')
        self.introScreen.reparentTo(render2dp)

        self.introScreen.setScale(1./4.5)  # i need to fix model itself lol
        self.introScreenLeft = self.introScreen.find('**/SPLIT_L')
        self.introScreenRight = self.introScreen.find('**/SPLIT_R')
        self.introScreenLeft.setPos(0, 0, 10)
        self.introScreenRight.setPos(0, 0, -10)

        # take the texture from the buffer and put it on the thingy
        self.introScreenLeft.setTexture(self.introLBuffer.getTexture(), 1)
        self.introScreenRight.setTexture(self.introRBuffer.getTexture(), 1)

        sbsdGui = loader.loadModel('phase_14.5/models/gui/ttoff_m_gui_mg_sbsd.bam')
        self.introVersus = sbsdGui.find('**/ttoff_t_gui_mg_sbsd_introVersus')
        self.introSplitSeparator = sbsdGui.find('**/ttoff_t_gui_mg_sbsd_introSplit')
        self.introSplitSeparator.reparentTo(render2dp)
        self.introSplitSeparator.setR(10.6)
        self.introSplitSeparator.hide()
        self.introVersus.reparentTo(aspect2dp)
        self.introVersus.setScale(0.6, 1.0, 0.3)
        self.introVersus.setColorScale(1.0, 1.0, 1.0, 0.0)
        sbsdGui.removeNode()
        self.reparentTo(render)
        self.setPosHpr(*ToontownGlobals.SellbotBossBattleOnePosHpr)
        self.stopAnimate()
        DistributedBossCog.DistributedBossCog.enterIntroduction(self)
        self.setCageIndex(0)
        base.playMusic(self.promotionMusic, looping = 1, volume = 0.9)

    def exitIntroduction(self):
        DistributedBossCog.DistributedBossCog.exitIntroduction(self)
        base.graphicsEngine.removeWindow(self.introLBuffer)
        base.graphicsEngine.removeWindow(self.introRBuffer)
        self.introLCam.removeNode()
        self.introRCam.removeNode()
        self.introScreen.removeNode()
        self.introVersus.removeNode()
        self.introSplitSeparator.removeNode()
        self.promotionMusic.stop()

    def disableToonCollision(self):
        base.localAvatar.collisionsOff()

    def enableToonCollision(self, task = None):
        base.localAvatar.collisionsOn()
        if task:
            return task.done

    def enterBattleOne(self):
        # We're not calling the superclass's enterBattleOne
        # because toonsToBattlePosition isn't necessary here
        # (in fact, it actually breaks since there can be more
        # than 8 toons)
        self.cleanupIntervals()
        self.releaseToons()

        self.clearChat()
        self.cagedToon.clearChat()
        self.reparentTo(render)
        self.rampC.request('Extend')
        self.setCageIndex(4)
        self.happy = 0
        self.raised = 1
        self.forward = 1
        self.doAnimate()

        self.__gotPies()

        self.accept('pieSplat', self.__pieSplat)
        self.accept('begin-pie', self.__foundPieButton)
        self.stickBossToFloor()

        self.bossDamageMovie = self.__makeBossDamageMovie()

        self.resetMaxDamage()

        # If max damage is 100 and duration is 100, bossDamageToMovie would be 1
        # Therefore the interval would go forward 1 second for every damage he takes
        bossDamageDuration = self.bossDamageMovie.getDuration()
        self.bossDamageToMovie = bossDamageDuration / self.bossMaxDamage

        initialDuration = bossDamageDuration / 2 + (self.bossDamage * self.bossDamageToMovie / 2)
        self.bossDamageMovie.setT(initialDuration)

        self.updateHealthBar()
        # base.playMusic(self.battleOneMusic, looping=1, volume=0.9)
        self.battleMusic.play(looping = 1)
        self.battleMusic.setMix(1.0)

        # Create the UI (All textures are very placeholder rn)
        gui = loader.loadModel('phase_14.5/models/gui/ttoff_m_gui_mg_sbsd')
        self.progressBarRoot = base.a2dTopCenter.attachNewNode('progressBarRoot')
        self.progressBarRoot.setPos(0.0, 0, -0.35)
        self.progressBarRoot.setScale(0.2)
        self.progressBar = gui.find('**/*gui_mg_sbsd_progressBar')
        self.progressBar.setScale(3, 1, 3 / 16.)
        self.progressBar.reparentTo(self.progressBarRoot)
        bookGui = loader.loadModel('phase_3.5/models/gui/stickerbook_gui')
        self.progressBarIcon = bookGui.find('**/BossHead3Icon')
        self.progressBarIcon.setScale(0.55)
        self.progressBarIcon.setZ(0.15)
        self.progressBarIcon.reparentTo(self.progressBarRoot)

        self.teamDisplayBackground = gui.find('**/*ttoff_t_gui_mg_sbsd_teamHudIcon')  # rename this to teamHudBg
        self.teamDisplayBackground.reparentTo(base.a2dTopLeft)
        self.teamDisplayBackground.setPos(0.2, 0, -0.7)
        self.teamDisplayBackground.setScale(0.2)

        if base.localAvatar.doId in self.toonsA:
            ico = gui.find('**/*gui_mg_sbsd_teamIconRed')
        else:
            ico = gui.find('**/*gui_mg_sbsd_teamIconBlue')

        ico.reparentTo(self.teamDisplayBackground)
        ico.setZ(0.1)
        ico.setScale(0.4)
        gui.removeNode()
        bookGui.removeNode()

        self.headerFrame = DirectFrame(parent = base.a2dTopCenter, pos = (0.0, 0.0, -0.1))

        self.headerToonIcons = {}

        for index, avId in enumerate(self.toonsA):
            toon = self.getToon(avId)
            icn = ToonPortrait(toon, 0)
            icn.reparentTo(base.a2dTopCenter)
            icn.setZ(-0.075)
            icn.setX(-0.2 - (0.2*index))
            self.headerToonIcons[avId] = icn

        for index, avId in enumerate(self.toonsB):
            toon = self.getToon(avId)
            icn = ToonPortrait(toon, 1)
            icn.reparentTo(base.a2dTopCenter)
            icn.setZ(-0.075)
            icn.setX(+0.2 + (0.2*index))
            self.headerToonIcons[avId] = icn

    def __doneBattleOne(self):
        self.setState('NearVictory')
        self.unstickBoss()

    def exitBattleOne(self):
        DistributedBossCog.DistributedBossCog.exitBattleOne(self)
        self.removeTask(self.bossDoneEvent)
        taskMgr.remove(self.uniqueName('StandUp'))
        self.ignore('pieSplat')
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
        self.battleMusic.stop()
        del self.battleMusic
        self.progressBarRoot.removeNode()
        self.teamDisplayBackground.removeNode()
        del self.progressBarRoot
        del self.teamDisplayBackground

    def enterNearVictory(self):
        self.cleanupIntervals()
        self.reparentTo(render)
        if self.bossDamage >= self.bossMaxDamage:
            pos = ToontownGlobals.SellbotArenaTeamADeathPos
        else:
            pos = ToontownGlobals.SellbotArenaTeamBDeathPos
        self.setPos(*pos)
        self.clearChat()
        self.cagedToon.clearChat()
        self.setCageIndex(4)
        self.releaseToons(finalBattle = 1)
        self.accept('pieSplat', self.__finalPieSplat)
        self.happy = 0
        self.raised = 0
        self.forward = 1
        self.doAnimate()
        self.setDizzy(1)
        base.playMusic(self.battleOneMusic, looping = 1, volume = 0.9, time = self.battleOneMusicTime)

    def exitNearVictory(self):
        self.ignore('pieSplat')
        self.__clearOnscreenMessage()
        taskMgr.remove(self.uniqueName('PieAdvice'))

        self.__removeCageShadow()
        self.setDizzy(0)
        self.battleOneMusicTime = self.battleOneMusic.getTime()
        self.battleOneMusic.stop()

    def enterVictory(self):
        self.cleanupIntervals()

        self.reparentTo(render)
        if self.bossDamage >= self.bossMaxDamage:
            pos = ToontownGlobals.SellbotArenaTeamADeathPos
        else:
            pos = ToontownGlobals.SellbotArenaTeamBDeathPos
            # the animation will just clip through the floor if we don't flip the vp around
            self.setH(-90)
        self.setPos(*pos)
        self.clearChat()
        self.cagedToon.clearChat()
        self.setCageIndex(4)
        self.releaseToons(finalBattle = 1)
        self.happy = 0
        self.raised = 0
        self.forward = 1
        self.doAnimate('Fb_fall', now = 1)
        self.acceptOnce(self.animDoneEvent, self.__continueVictory)
        base.playMusic(self.battleOneMusic, looping = 1, volume = 0.9, time = self.battleOneMusicTime)

    def __continueVictory(self):
        self.stopAnimate()
        self.stash()
        self.doneBarrier('Victory')

    def exitVictory(self):
        self.stopAnimate()
        self.unstash()
        self.__removeCageShadow()
        self.battleOneMusicTime = self.battleOneMusic.getTime()
        self.battleOneMusic.stop()

    def enterReward(self):
        self.cleanupIntervals()
        self.clearChat()
        self.cagedToon.clearChat()
        self.stash()
        self.stopAnimate()
        self.setCageIndex(4)
        self.releaseToons(finalBattle = 1)
        self.toMovieMode()
        intervalName = 'RewardMovie'
        delayDeletes = []
        toonIval = Parallel()
        for toonId in self.involvedToons:
            toon = self.cr.doId2do.get(toonId)
            if toon:
                toonIval.append(ActorInterval(toon, 'victory'))
                delayDeletes.append(DelayDelete.DelayDelete(toon, 'SellbotArena.enterReward'))
        ival = Sequence(toonIval, Func(self.__doneReward))

        ival.delayDeletes = delayDeletes
        ival.start()
        self.storeInterval(ival, intervalName)
        base.playMusic(self.battleOneMusic, looping = 1, volume = 0.9, time = self.battleOneMusicTime)

    def __doneReward(self):
        self.doneBarrier('Reward')
        self.toWalkMode()

    def exitReward(self):
        intervalName = 'RewardMovie'
        self.clearInterval(intervalName)
        self.unstash()
        self.__removeCageShadow()
        self.battleOneMusicTime = 0
        self.battleOneMusic.stop()

    def enterEpilogue(self):
        self.cleanupIntervals()
        self.clearChat()
        self.cagedToon.clearChat()
        self.stash()
        self.stopAnimate()
        self.setCageIndex(4)
        self.controlToons()
        self.__arrangeToonsAroundCage()
        camera.reparentTo(render)
        camera.setPosHpr(-24, 52, 27.5, -53, -13, 0)
        intervalName = 'EpilogueMovie'
        seq = Sequence(self.__makeCageOpenMovie(), name = intervalName)
        seq.start()
        self.storeInterval(seq, intervalName)
        self.accept(self.__nextPageMsg, self.__epilogueChatNext)
        self.accept(self.__donePageMsg, self.__epilogueChatDone)
        base.playMusic(self.epilogueMusic, looping = 1, volume = 0.9)

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
        self.cagedToon.setChatAbsolute(TTLocalizer.CagedToonGoodbye, CFSpeech)
        if self.__nextPageMsg is not None:
            self.ignore(self.__nextPageMsg)
        if self.__donePageMsg is not None:
            self.ignore(self.__donePageMsg)
        intervalName = 'EpilogueMovieToonAnim'
        self.clearInterval(intervalName)
        track = Parallel(Sequence(ActorInterval(self.cagedToon, 'wave'), Func(self.cagedToon.loop, 'neutral')),
                         Sequence(Wait(0.5), Func(self.localToonToSafeZone)))
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

    def __gotPies(self):
        self.sendUpdate('gotPies', [])
        self.__clearOnscreenMessage()
        taskMgr.remove(self.uniqueName('PieAdvice'))
        base.playSfx(self.piesRestockSfx)
        if not self.everThrownPie:
            taskMgr.doMethodLater(30, self.__howToThrowPies, self.uniqueName('PieAdvice'))

    def __howToThrowPies(self, task):
        dialog = ControlManager.ControlManager.parseHotkeyString(TTLocalizer.BossBattleHowToThrowPies, useGlyphs=True)
        self.__showOnscreenMessage(dialog)
        return task.done

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
                self.d_hitBoss()
            if self.dizzy:
                self.flashRed()
                self.doAnimate('hit', now = 1)

    def __finalPieSplat(self, toon, pieCode):
        if pieCode != ToontownGlobals.PieCodeBossCog:
            return
        self.sendUpdate('finalPieSplat', [])
        self.ignore('pieSplat')

    def cagedToonBattleOne(self, index, avId):
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

    def setTimer(self, endTime):
        endTime = globalClockDelta.networkToLocalTime(endTime)
        timeLeft = int(endTime - globalClock.getRealTime())
        if timeLeft > 0:
            self.timer.show()
            self.timer.countdown(timeLeft, self.__timerExpired)
        else:
            self.timer.hide()

    def __timerExpired(self):
        self.timer.reset()
        self.timer.hide()

    def cleanupAttacks(self):
        self.__cleanupStrafe()

    def __cleanupStrafe(self):
        if self.strafeInterval:
            self.strafeInterval.finish()
            self.strafeInterval = None
        return

    def doStrafe(self, direction):
        multiStrafe = Parallel()

        # We want both sides to open whenever we strafe
        for x in range(2):
            gearRoot = self.rotateNode.attachNewNode('gearRoot')
            if x == 0:
                gearRoot.setPos(0, -7, 3)
                gearRoot.setHpr(180, 0, 0)
                door = self.doorA
            else:
                gearRoot.setPos(0, 7, 3)
                door = self.doorB
            gearRoot.setTag('attackCode', str(ToontownGlobals.BossCogStrafeAttack))
            gearModel = self.getGearFrisbee()
            gearModel.setScale(0.1)
            t = abs(self.getBossDamage()) / self.bossMaxDamage
            gearTrack = Parallel()
            numGears = int(4 + 6 * t + 0.5)
            time = 5.0 - 4.0 * t
            spread = 60 * math.pi / 180.0
            if direction == 1:
                spread = -spread
            dist = 50
            rate = time / numGears
            for i in range(numGears):
                node = gearRoot.attachNewNode(str(i))
                node.hide()
                node.setPos(0, 0, 0)
                angle = (float(i) / (numGears - 1) - 0.5) * spread
                x = dist * math.sin(angle)
                y = dist * math.cos(angle)
                h = random.uniform(-720, 720)
                gearTrack.append(
                        Sequence(Wait(i * rate), Func(node.show),
                                 Parallel(node.posInterval(1, Point3(x, y, 0), fluid = 1),
                                          node.hprInterval(1, VBase3(h, 0, 0), fluid = 1),
                                          Sequence(SoundInterval(self.strafeSfx[i],
                                                                 volume = 0.2,
                                                                 node = self),
                                                   duration = 0)),
                                 Func(node.detachNode)))

            seq = Sequence(Func(door.request, 'open'), Wait(0.7), gearTrack, Func(door.request, 'close'))
            multiStrafe.append(seq)

        self.__cleanupStrafe()
        self.strafeInterval = multiStrafe
        self.strafeInterval.start()

    def getToon(self, avId):  # type: (int)->DistributedToon
        if avId in self.cr.doId2do:
            return self.cr.doId2do[avId]