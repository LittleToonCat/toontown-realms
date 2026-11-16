from panda3d.core import VBase3, Point3
from panda3d.toontown import *
from direct.interval.IntervalGlobal import *
from toontown.battle.BattleBase import FACEOFF_TAUNT_T, FLOOR_REWARD_TIMEOUT
from toontown.battle import DistributedBattle
from toontown.distributed import DelayDelete
from direct.directnotify import DirectNotifyGlobal
from otp.avatar import Emote
import random
from toontown.suit import SuitDNA, SuitTimings
from toontown.toonbase import ToontownGlobals
from toontown.toonbase.ToontownTypes import CogQuoteIndex

class DistributedLevelBattle(DistributedBattle.DistributedBattle):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedLevelBattle')

    def __init__(self, cr):
        DistributedBattle.DistributedBattle.__init__(self, cr)
        self.levelRequest = None
        self.levelBattle = 1

    def setLevelDoId(self, levelDoId):
        self.levelDoId = levelDoId

    def setBattleCellId(self, battleCellId):
        self.battleCellId = battleCellId

        def doPlacement(levelList, self = self):
            self.levelRequest = None
            self.level = levelList[0]
            spec = self.level.getBattleCellSpec(self.battleCellId)
            self.level.requestReparent(self, spec['parentEntId'])
            self.setPos(spec['pos'])
            print('spec = %s' % spec)
            print('h = %s' % spec.get('h'))
            self.wrtReparentTo(render)

        level = base.cr.doId2do.get(self.levelDoId)
        if level is None:
            self.notify.warning('level %s not in doId2do yet, battle %s will be mispositioned.' % self.levelDoId, self.doId)
            self.levelRequest = self.cr.relatedObjectMgr.requestObjects([self.levelDoId], doPlacement)
        else:
            doPlacement([level])

    def setPosition(self, *args):
        pass

    def makeSuitJoin(self, suit, ts):
        if suit.reserve:
            self.notify.debug('makeSuitJoin(%d)' % suit.doId)
            suit.setState('Battle')
            suit.showShadow()
            suit.showNametag3d()
            self.joiningSuits.append(suit)
            i = len(self.pendingSuits) + self.joiningSuits.index(suit)
            destPos, h = self.suitPendingPoints[i]
            destHpr = VBase3(h, 0, 0)
            startPos = destPos + Point3(0, 0, SuitTimings.fromSky * ToontownGlobals.SuitWalkSpeed)
            suit.setPos(self, startPos)
            suit.headsUp(self)
            flyIval = suit.beginSupaFlyMove(destPos, True, 'flyIn')
            track = Sequence(flyIval, self.createAdjustInterval(suit, destPos, destHpr),
                             Func(self._DistributedBattleBase__handleSuitJoinDone, suit, ts))
            if self.hasLocalToon():
                camera.reparentTo(self)
                if random.choice([0, 1]):
                    camera.setPosHpr(20, -4, 7, 60, 0, 0)
                else:
                    camera.setPosHpr(-20, -4, 7, -60, 0, 0)
            track.start(ts)
            track.delayDelete = DelayDelete.DelayDelete(suit, 'makeSuitJoin')
            trackName = self.taskName('to-pending-suit-%d' % suit.doId)
            self.storeInterval(track, trackName)
        else:
            DistributedBattle.DistributedBattle.makeSuitJoin(self, suit, ts)

    def setInitialSuitPos(self, x, y, z):
        self.initialSuitPos = Point3(x, y, z)

    def disable(self):
        if self.hasLocalToon():
            self.unlockLevelViz()
        if self.levelRequest is not None:
            self.cr.relatedObjectMgr.abortRequest(self.levelRequest)
            self.levelRequest = None
        DistributedBattle.DistributedBattle.disable(self)

    def delete(self):
        self.ignoreAll()
        DistributedBattle.DistributedBattle.delete(self)

    def handleBattleBlockerCollision(self):
        messenger.send(self.getCollisionName(), [None])

    def lockLevelViz(self):
        level = base.cr.doId2do.get(self.levelDoId)
        if level:
            level.lockVisibility(zoneId=self.zoneId)
        else:
            self.notify.warning("lockLevelViz: couldn't find level %s" % self.levelDoId)

    def unlockLevelViz(self):
        level = base.cr.doId2do.get(self.levelDoId)
        if level:
            level.unlockVisibility()
        else:
            self.notify.warning("unlockLevelViz: couldn't find level %s" % self.levelDoId)

    def onWaitingForJoin(self):
        self.lockLevelViz()

    def __faceOff(self, ts, name, callback):
        if len(self.suits) == 0:
            self.notify.warning('__faceOff(): no suits.')
            return
        if len(self.toons) == 0:
            self.notify.warning('__faceOff(): no toons.')
            return
        self.adjustWeather()
        toon = self.toons[0]
        point = self.toonPoints[0][0]
        toonPos = point[0]
        p = toon.getPos(self)
        toon.setPos(self, p[0], p[1], 0.0)
        toon.setShadowHeight(0)
        if len(self.suits) == 1:
            leaderIndex = 0
        elif self.bossBattle == 1:
            for suit in self.suits:
                if suit.boss:
                    leaderIndex = self.suits.index(suit)
                    break

        else:
            leaderIndex = random.randint(0, len(self.suits) - 1)

        delay = FACEOFF_TAUNT_T
        suitTrack = Parallel()
        suitLeader = None
        for suit in self.suits:
            suit.setState('Battle')
            suitIsLeader = 0
            oneSuitTrack = Sequence()
            oneSuitTrack.append(Func(suit.loop, 'neutral'))
            oneSuitTrack.append(Func(suit.headsUp, toonPos))
            if self.suits.index(suit) == leaderIndex:
                suitLeader = suit
                suitIsLeader = 1
                if self.bossBattle == 1 and self.levelDoId in base.cr.doId2do:
                    level = base.cr.doId2do[self.levelDoId]
                    dept = level.getCogTrack()
                    quoteTypeIndexBoss = CogQuoteIndex.FACEOFF_TAUNTS_FACILITY_BOSS
                    quoteTypeIndexBossMinion = CogQuoteIndex.FACEOFF_TAUNTS_FACILITY_BOSS_MINION
                    if suit.boss:
                        taunt = base.cr.dataPackMgr.getCogQuoteByDoId(suit.getStyleName(), quoteTypeIndexBoss, suit.doId)
                    else:
                        taunt = base.cr.dataPackMgr.getCogQuoteByDoId(suit.getStyleName(), quoteTypeIndexBossMinion, suit.doId)
                else:
                    taunt = base.cr.dataPackMgr.getCogQuoteByDoId(suit.getStyleName(), CogQuoteIndex.FACEOFF_TAUNTS, suit.doId)
                oneSuitTrack.append(Func(suit.setChatAbsolute, taunt, CFSpeech | CFTimeout))
            destPos, destHpr = self.getActorPosHpr(suit, self.suits)
            oneSuitTrack.append(Wait(delay))
            if suitIsLeader == 1:
                oneSuitTrack.append(Func(suit.clearChat))
            oneSuitTrack.append(self.createAdjustInterval(suit, destPos, destHpr))
            suitTrack.append(oneSuitTrack)

        suitHeight = suitLeader.getHeight()
        suitOffsetPnt = Point3(0, 0, suitHeight)
        toonTrack = Parallel()
        for toon in self.toons:
            oneToonTrack = Sequence()
            destPos, destHpr = self.getActorPosHpr(toon, self.toons)
            oneToonTrack.append(Wait(delay))
            oneToonTrack.append(self.createAdjustInterval(toon, destPos, destHpr, True))
            toonTrack.append(oneToonTrack)

        if self.hasLocalToon():
            MidTauntCamHeight = suitHeight * 0.66
            MidTauntCamHeightLim = suitHeight - 1.8
            if MidTauntCamHeight < MidTauntCamHeightLim:
                MidTauntCamHeight = MidTauntCamHeightLim
            TauntCamY = 18
            TauntCamX = 0
            TauntCamHeight = random.choice((MidTauntCamHeight, 1, 11))
            camTrack = Sequence()
            camTrack.append(Func(camera.reparentTo, suitLeader))
            camTrack.append(Func(base.camLens.setMinFov, self.camFOFov / (4. / 3.)))
            camTrack.append(Func(camera.setPos, TauntCamX, TauntCamY, TauntCamHeight))
            camTrack.append(Func(camera.lookAt, suitLeader, suitOffsetPnt))
            camTrack.append(Wait(delay))
            camTrack.append(Func(base.camLens.setMinFov, self.camFov / (4. / 3.)))
            camTrack.append(Func(camera.wrtReparentTo, self))
            camTrack.append(Func(camera.setPos, self.camFOPos))
            camTrack.append(Func(camera.lookAt, suit))
        mtrack = Parallel(suitTrack, toonTrack)
        if self.hasLocalToon():
            NametagGlobals.setMasterArrowsOn(0)
            mtrack = Parallel(mtrack, camTrack)
        done = Func(callback)
        track = Sequence(mtrack, done, name=name)
        track.start(ts)
        self.storeInterval(track, name)

    def enterFaceOff(self, ts):
        if len(self.toons) > 0 and base.localAvatar == self.toons[0]:
            Emote.globalEmote.disableAll(self.toons[0], 'dbattlelevel, enterFaceOff')
        self.delayDeleteMembers()
        self.__faceOff(ts, self.faceOffName, self.__handleFaceOffDone)

    def __handleFaceOffDone(self):
        self.notify.debug('FaceOff done')
        self.d_faceOffDone(base.localAvatar.doId)

    def exitFaceOff(self):
        self.notify.debug('exitFaceOff()')
        if len(self.toons) > 0 and base.localAvatar == self.toons[0]:
            Emote.globalEmote.releaseAll(self.toons[0], 'dbattlelevel, exitFaceOff')
        self.clearInterval(self.faceOffName)
        self._removeMembersKeep()

    def __playReward(self, ts, callback):
        toonTracks = Parallel()
        for toon in self.toons:
            toonTracks.append(
                Sequence(
                    Func(toon.playCalcTransformedAnim, 'victory'), 
                    Wait(FLOOR_REWARD_TIMEOUT), 
                    Func(toon.playCalcTransformedAnim, 'neutral')
                )
            )

        name = self.uniqueName('floorReward')
        track = Sequence(toonTracks, Func(callback), name=name)
        camera.setPos(0, 0, 1)
        camera.setHpr(180, 10, 0)
        self.storeInterval(track, name)
        track.start(ts)

    def enterReward(self, ts):
        self.notify.info('enterReward()')
        self.disableCollision()
        self.delayDeleteMembers()
        self.__playReward(ts, self.__handleFloorRewardDone)

    def __handleFloorRewardDone(self):
        pass

    def exitReward(self):
        self.notify.info('exitReward()')
        self.clearInterval(self.uniqueName('floorReward'))
        self._removeMembersKeep()
        NametagGlobals.setMasterArrowsOn(1)
        for toon in self.toons:
            toon.startSmooth()
