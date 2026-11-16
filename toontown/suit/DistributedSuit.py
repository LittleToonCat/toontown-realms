from direct.distributed.ClockDelta import *
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State
from direct.gui.OnscreenText import OnscreenText
from direct.interval.IntervalGlobal import *
from direct.task import Task

import math
from otp.otpbase.PythonUtil import bound
from panda3d.core import *
from panda3d.toontown import *
from toontown.battle import MovieUtil
from toontown.distributed.DelayDeletable import DelayDeletable
from toontown.toonbase import TTLocalizer, ToontownGlobals, ClientSettings, HotkeySettings, ControlManager

from . import DistributedSuitBase
from . import SuitTimings

STAND_OUTSIDE_DOOR = 2.5
BATTLE_IGNORE_TIME = 6
BATTLE_WAIT_TIME = 3
CATCHUP_SPEED_MULTIPLIER = 3
ALLOW_BATTLE_DETECT = 1


class DistributedSuit(DistributedSuitBase.DistributedSuitBase, DelayDeletable):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedSuit')
    ENABLE_EXPANDED_NAME = 0

    def __init__(self, cr):
        try:
            self.DistributedSuit_initialized
            return
        except:
            self.DistributedSuit_initialized = 1

        DistributedSuitBase.DistributedSuitBase.__init__(self, cr)
        self.spDoId = None
        self.pathEndpointStart = 0
        self.pathEndpointEnd = 0
        self.minPathLen = 0
        self.maxPathLen = 0
        self.pathPositionIndex = 0
        self.pathPositionTimestamp = 0.0
        self.pathState = 0
        self.path = None
        self.localPathState = 0
        self.currentLeg = -1
        self.pathStartTime = 0.0
        self.legList = None
        self.initState = None
        self.finalState = None
        self.buildingSuit = 0
        self.fsm = ClassicFSM.ClassicFSM('DistributedSuit', [
            State.State('Off',
                        self.enterOff,
                        self.exitOff, [
                            'FromSky',
                            'FromSuitBuilding',
                            'Walk',
                            'Battle',
                            'neutral',
                            'ToToonBuilding',
                            'ToSuitBuilding',
                            'ToCogHQ',
                            'FromCogHQ',
                            'ToSky',
                            'FlyAway',
                            'DanceThenFlyAway',
                            'WalkToStreet',
                            'WalkFromStreet',
                            'PieSplat']),
         State.State('FromSky',
                     self.enterFromSky,
                     self.exitFromSky, [
                         'Walk',
                         'Battle',
                         'neutral',
                         'ToSky',
                         'WalkFromStreet']),
         State.State('FromSuitBuilding',
                     self.enterFromSuitBuilding,
                     self.exitFromSuitBuilding, [
                         'WalkToStreet',
                         'Walk',
                         'Battle',
                         'neutral',
                         'ToSky']),
         State.State('WalkToStreet',
                     self.enterWalkToStreet,
                     self.exitWalkToStreet, [
                         'Walk',
                         'Battle',
                         'neutral',
                         'ToSky',
                         'ToToonBuilding',
                         'ToSuitBuilding',
                         'ToCogHQ',
                         'WalkFromStreet']),
         State.State('WalkFromStreet',
                     self.enterWalkFromStreet,
                     self.exitWalkFromStreet, [
                         'ToToonBuilding',
                         'ToSuitBuilding',
                         'ToCogHQ',
                         'Battle',
                         'neutral',
                         'ToSky']),
         State.State('Walk',
                     self.enterWalk,
                     self.exitWalk, [
                         'WaitForBattle',
                         'Battle',
                         'neutral',
                         'WalkFromStreet',
                         'ToSky',
                         'FromCogHQ',
                         'ToCogHQ',
                         'Walk',
                         'PieSplat']),
         State.State('Battle',
                     self.enterBattle,
                     self.exitBattle, [
                         'Walk',
                         'ToToonBuilding',
                         'ToCogHQ',
                         'ToSuitBuilding',
                         'ToSky']),
         State.State('neutral',
                     self.enterNeutral,
                     self.exitNeutral, []),
         State.State('PieSplat',
                     self.enterPieSplat,
                     self.exitPieSplat, []),
         State.State('WaitForBattle',
                     self.enterWaitForBattle,
                     self.exitWaitForBattle, [
                         'Battle',
                         'neutral',
                         'Walk',
                         'WalkToStreet',
                         'WalkFromStreet',
                         'ToToonBuilding',
                         'ToCogHQ',
                         'ToSuitBuilding',
                         'ToSky']),
         State.State('ToToonBuilding',
                     self.enterToToonBuilding,
                     self.exitToToonBuilding, [
                         'neutral',
                         'Battle']),
         State.State('ToSuitBuilding',
                     self.enterToSuitBuilding,
                     self.exitToSuitBuilding, [
                         'neutral',
                         'Battle']),
         State.State('ToCogHQ',
                     self.enterToCogHQ,
                     self.exitToCogHQ, [
                         'neutral',
                         'Battle']),
         State.State('FromCogHQ',
                     self.enterFromCogHQ,
                     self.exitFromCogHQ, [
                         'neutral',
                         'Battle',
                         'Walk']),
         State.State('ToSky',
                     self.enterToSky,
                     self.exitToSky, [
                         'Battle']),
         State.State('FlyAway',
                     self.enterFlyAway,
                     self.exitFlyAway,
                     []),
         State.State('DanceThenFlyAway',
                     self.enterDanceThenFlyAway,
                     self.exitDanceThenFlyAway,
                     [])],
         'Off', 'Off')
        self.fsm.enterInitialState()
        self.__currentDialogue = None
        return

    def generate(self):
        DistributedSuitBase.DistributedSuitBase.generate(self)

    def disable(self):
        self.notify.debug(f'DistributedSuit {self.getDoId()}: disabling')
        self.resumePath(0)
        self.stopPathNow()
        self.setState('Off')
        DistributedSuitBase.DistributedSuitBase.disable(self)

    def delete(self):
        try:
            self.DistributedSuit_deleted
        except:
            self.DistributedSuit_deleted = 1
            self.notify.debug(f'DistributedSuit {self.getDoId()}: deleting')
            del self.fsm
            DistributedSuitBase.DistributedSuitBase.delete(self)

    def setPathEndpoints(self, start, end, minPathLen, maxPathLen):
        if self.pathEndpointStart == start and self.pathEndpointEnd == end and self.minPathLen == minPathLen and self.maxPathLen == maxPathLen and self.path != None:
            return
        self.pathEndpointStart = start
        self.pathEndpointEnd = end
        self.minPathLen = minPathLen
        self.maxPathLen = maxPathLen
        self.path = None
        self.pathLength = 0
        self.currentLeg = -1
        self.legList = None
        if self.maxPathLen == 0:
            return
        if not self.verifySuitPlanner():
            return
        self.startPoint = self.sp.pointIndexes[self.pathEndpointStart]
        self.endPoint = self.sp.pointIndexes[self.pathEndpointEnd]
        path = self.sp.genPath(self.startPoint, self.endPoint, self.minPathLen, self.maxPathLen)
        self.setPath(path)
        self.makeLegList()
        return

    def verifySuitPlanner(self):
        if self.sp == None and self.spDoId != 0:
            self.notify.warning(f'Suit {self.doId} does not have a suit planner! Expected SP doId {self.spDoId}.')
            self.sp = self.cr.doId2do.get(self.spDoId, None)
        if self.sp == None:
            return 0
        return 1

    def setPathPosition(self, index, timestamp):
        if not self.verifySuitPlanner():
            return
        if self.path == None:
            self.setPathEndpoints(self.pathEndpointStart, self.pathEndpointEnd, self.minPathLen, self.maxPathLen)
        self.pathPositionIndex = index
        self.pathPositionTimestamp = globalClockDelta.networkToLocalTime(timestamp)
        if self.legList != None:
            self.pathStartTime = self.pathPositionTimestamp - self.legList.getStartTime(self.pathPositionIndex)
        return

    def setPathState(self, state):
        self.pathState = state
        self.resumePath(state)

    def debugSuitPosition(self, elapsed, currentLeg, x, y, timestamp):
        now = globalClock.getFrameTime()
        chug = globalClock.getRealTime() - now
        messageAge = now - globalClockDelta.networkToLocalTime(timestamp, now)
        if messageAge < -(chug + 0.5) or messageAge > chug + 1.0:
            print('Apparently out of sync with AI by %0.2f seconds.  Suggest resync!' % messageAge)
            return
        localElapsed = now - self.pathStartTime
        timeDiff = localElapsed - (elapsed + messageAge)
        if abs(timeDiff) > 0.2:
            print("%s (%d) appears to be %0.2f seconds out of sync along its path.  Suggest '~cogs sync'." % (self.getName(), self.getDoId(), timeDiff))
            return
        if self.legList == None:
            print("%s (%d) doesn't have a legList yet." % (self.getName(), self.getDoId()))
            return
        netPos = Point3(x, y, 0.0)
        leg = self.legList.getLeg(currentLeg)
        calcPos = leg.getPosAtTime(elapsed - leg.getStartTime())
        calcPos.setZ(0.0)
        calcDelta = Vec3(netPos - calcPos)
        diff = calcDelta.length()
        if diff > 4.0:
            print('%s (%d) is %0.2f feet from the AI computed path!' % (self.getName(), self.getDoId(), diff))
            print('Probably your DNA files are out of sync.')
            return
        localPos = Point3(self.getX(), self.getY(), 0.0)
        localDelta = Vec3(netPos - localPos)
        diff = localDelta.length()
        if diff > 10.0:
            print('%s (%d) in state %s is %0.2f feet from its correct position!' % (self.getName(),
             self.getDoId(),
             self.fsm.getCurrentState().getName(),
             diff))
            print('Should be at (%0.2f, %0.2f), but is at (%0.2f, %0.2f).' % (x,
             y,
             localPos[0],
             localPos[1]))
            return
        print('%s (%d) is in the correct position.' % (self.getName(), self.getDoId()))
        return

    def denyBattle(self):
        DistributedSuitBase.DistributedSuitBase.denyBattle(self)
        self.disableBattleDetect()

    def resumePath(self, state):
        if self.localPathState != state:
            self.localPathState = state
            if state == 0:
                self.stopPathNow()
            elif state == 1:
                self.moveToNextLeg(None)
            elif state == 2:
                self.stopPathNow()
                if self.sp != None:
                    self.setState('Off')
                    self.setState('FlyAway')
            elif state == 3:
                pass
            elif state == 4:
                self.stopPathNow()
                if self.sp != None:
                    self.setState('Off')
                    self.setState('DanceThenFlyAway')
            elif state == 5:
                self.stopPathNow()
                self.setState('PieSplat')
            else:
                self.notify.error(f'No such state as: {state}')
        return

    def moveToNextLeg(self, task):
        if self.legList == None:
            self.notify.warning(f'Suit {self.getDoId()} does not have a path!')
            return Task.done
        now = globalClock.getFrameTime()
        elapsed = now - self.pathStartTime
        nextLeg = self.legList.getLegIndexAtTime(elapsed, self.currentLeg)
        numLegs = self.legList.getNumLegs()
        if self.currentLeg != nextLeg:
            self.currentLeg = nextLeg
            self.doPathLeg(self.legList[nextLeg], elapsed - self.legList.getStartTime(nextLeg))
        nextLeg += 1
        if nextLeg < numLegs:
            nextTime = self.legList.getStartTime(nextLeg)
            delay = nextTime - elapsed
            name = self.taskName('move')
            taskMgr.remove(name)
            taskMgr.doMethodLater(delay, self.moveToNextLeg, name)
        return Task.done

    def doPathLeg(self, leg, time):
        self.fsm.request(SuitLeg.getTypeName(leg.getType()), [leg, time])
        return 0

    def stopPathNow(self):
        name = self.taskName('move')
        taskMgr.remove(name)
        self.currentLeg = -1

    def calculateHeading(self, a, b):
        xdelta = b[0] - a[0]
        ydelta = b[1] - a[1]
        if ydelta == 0:
            if xdelta > 0:
                return -90
            else:
                return 90
        elif xdelta == 0:
            if ydelta > 0:
                return 0
            else:
                return 180
        else:
            angle = math.atan2(ydelta, xdelta)
            return rad2Deg(angle) - 90

    def beginBuildingMove(self, moveIn, doneEvent, suit = 0):
        doorPt = Point3(0)
        buildingPt = Point3(0)
        streetPt = Point3(0)
        if self.virtualPos:
            doorPt.assign(self.virtualPos)
        else:
            doorPt.assign(self.getPos())
        if moveIn:
            streetPt = self.prevPointPos()
        else:
            streetPt = self.currPointPos()
        dx = doorPt[0] - streetPt[0]
        dy = doorPt[1] - streetPt[1]
        buildingPt = Point3(doorPt[0] + dx, doorPt[1] + dy, doorPt[2])
        if moveIn:
            if suit:
                moveTime = SuitTimings.toSuitBuilding
            else:
                moveTime = SuitTimings.toToonBuilding
            return self.beginMove(doneEvent, buildingPt, time=moveTime)
        else:
            return self.beginMove(doneEvent, doorPt, buildingPt, time=SuitTimings.fromSuitBuilding)
        return None

    def setSPDoId(self, doId):
        self.spDoId = doId
        self.sp = self.cr.doId2do.get(doId, None)
        if self.sp == None and self.spDoId != 0:
            self.notify.warning(f'Suit {self.doId} created before its suit planner, {self.spDoId}')
        return

    def d_requestBattle(self, pos, hpr):
        self.cr.playGame.getPlace().setState('WaitForBattle')
        self.sendUpdate('requestBattle', [pos[0],
         pos[1],
         pos[2],
         hpr[0],
         hpr[1],
         hpr[2]])

    def __handleToonCollision(self, collEntry):
        if ClientSettings.CogInteraction.get():
            self.__createInteractHint()
        else:
            self.__enterBattle()

    def __enterBattle(self):
        if not base.localAvatar.wantBattles:
            return
        toonId = base.localAvatar.getDoId()
        self.notify.debug(f'Distributed suit: requesting a Battle with toon {toonId}')
        self.d_requestBattle(self.getPos(), self.getHpr())
        self.setState('WaitForBattle')

    def setAnimState(self, state):
        self.setState(state)

    def enterFromSky(self, leg, time):
        self.enableBattleDetect('fromSky', self.__handleToonCollision)
        self.loop('neutral', 0)
        if not self.verifySuitPlanner():
            return
        a = leg.getPosA()
        b = leg.getPosB()
        h = self.calculateHeading(a, b)
        self.setPosHprScale(a[0], a[1], a[2], h, 0.0, 0.0, 1.0, 1.0, 1.0)
        self.mtrack = self.beginSupaFlyMove(a, 1, self.uniqueName('fromSky'))
        self.mtrack.start(time)

    def exitFromSky(self):
        self.disableBattleDetect()
        self.mtrack.finish()
        del self.mtrack
        self.detachPropeller()

    def enterWalkToStreet(self, leg, time):
        self.enableBattleDetect('walkToStreet', self.__handleToonCollision)
        self.ignorePie()
        self.loop('walk', 0)
        a = leg.getPosA()
        b = leg.getPosB()
        delta = Vec3(b - a)
        length = delta.length()
        delta *= (length - STAND_OUTSIDE_DOOR) / length
        a1 = Point3(b - delta)
        self.enableRaycast(1)
        h = self.calculateHeading(a, b)
        self.quatScaleInterval(.3, (h, 0.0, 0.0), (1.0, 1.0, 1.0), blendType='easeInOut').start()
        self.mtrack = Sequence(LerpPosInterval(self, leg.getLegTime(), b, startPos=a1), name=self.taskName('walkToStreet'))
        self.mtrack.start(time)

    def exitWalkToStreet(self):
        self.disableBattleDetect()
        self.enableRaycast(0)
        self.mtrack.finish()
        del self.mtrack

    def enterWalkFromStreet(self, leg, time):
        self.enableBattleDetect('walkFromStreet', self.__handleToonCollision)
        self.ignorePie()
        self.loop('walk', 0)
        a = leg.getPosA()
        b = leg.getPosB()
        delta = Vec3(b - a)
        length = delta.length()
        delta *= (length - STAND_OUTSIDE_DOOR) / length
        b1 = Point3(a + delta)
        self.enableRaycast(1)
        h = self.calculateHeading(a, b)
        self.quatScaleInterval(.3, (h, 0.0, 0.0), (1.0, 1.0, 1.0), blendType='easeInOut').start()
        self.mtrack = Sequence(LerpPosInterval(self, leg.getLegTime(), b1, startPos=a), name=self.taskName('walkFromStreet'))
        self.mtrack.start(time)

    def exitWalkFromStreet(self):
        self.disableBattleDetect()
        self.enableRaycast(0)
        self.mtrack.finish()
        del self.mtrack

    def enterWalk(self, leg, time):
        self.enableBattleDetect('bellicose', self.__handleToonCollision)
        self.loop('walk', 0)
        a = leg.getPosA()
        b = leg.getPosB()
        h = self.calculateHeading(a, b)
        pos = leg.getPosAtTime(time)
        self.posQuatScaleInterval(.3, Point3(pos), (h, 0.0, 0.0), (1.0, 1.0, 1.0), blendType = 'easeInOut').start()
        self.mtrack = Sequence(LerpPosInterval(self, leg.getLegTime(), b, startPos=a), name=self.taskName('bellicose'))
        self.mtrack.start(time)

    def exitWalk(self):
        self.disableBattleDetect()
        self.mtrack.pause()
        del self.mtrack

    def enterToSky(self, leg, time):
        self.enableBattleDetect('toSky', self.__handleToonCollision)
        self.ignorePie()
        if not self.verifySuitPlanner():
            return
        a = leg.getPosA()
        b = leg.getPosB()
        h = self.calculateHeading(a, b)
        self.setPosHprScale(b[0], b[1], b[2], h, 0.0, 0.0, 1.0, 1.0, 1.0)
        self.mtrack = self.beginSupaFlyMove(b, 0, self.uniqueName('toSky'))
        self.mtrack.start(time)

    def exitToSky(self):
        self.disableBattleDetect()
        self.mtrack.finish()
        del self.mtrack
        self.detachPropeller()

    def enterFromSuitBuilding(self, leg, time):
        self.enableBattleDetect('fromSuitBuilding', self.__handleToonCollision)
        self.loop('walk', 0)
        if not self.verifySuitPlanner():
            return
        a = leg.getPosA()
        b = leg.getPosB()
        delta = Vec3(b - a)
        length = delta.length()
        delta2 = delta * (self.sp.suitWalkSpeed * leg.getLegTime()) / length
        delta *= (length - STAND_OUTSIDE_DOOR) / length
        b1 = Point3(b - delta)
        a1 = Point3(b1 - delta2)
        self.enableRaycast(1)
        h = self.calculateHeading(a, b)
        self.setHprScale(h, 0.0, 0.0, 1.0, 1.0, 1.0)
        self.mtrack = Sequence(LerpPosInterval(self, leg.getLegTime(), b1, startPos=a1), name=self.taskName('fromSuitBuilding'))
        self.mtrack.start(time)

    def exitFromSuitBuilding(self):
        self.disableBattleDetect()
        self.mtrack.finish()
        del self.mtrack

    def enterToToonBuilding(self, leg, time):
        self.loop('neutral', 0)

    def exitToToonBuilding(self):
        pass

    def enterToSuitBuilding(self, leg, time):
        self.loop('walk', 0)
        if not self.verifySuitPlanner():
            return
        a = leg.getPosA()
        b = leg.getPosB()
        delta = Vec3(b - a)
        length = delta.length()
        delta2 = delta * (self.sp.suitWalkSpeed * leg.getLegTime()) / length
        delta *= (length - STAND_OUTSIDE_DOOR) / length
        a1 = Point3(a + delta)
        b1 = Point3(a1 + delta2)
        self.enableRaycast(1)
        h = self.calculateHeading(a, b)
        self.setHprScale(h, 0.0, 0.0, 1.0, 1.0, 1.0)
        self.mtrack = Sequence(LerpPosInterval(self, leg.getLegTime(), b1, startPos=a1), name=self.taskName('toSuitBuilding'))
        self.mtrack.start(time)

    def exitToSuitBuilding(self):
        self.mtrack.finish()
        del self.mtrack

    def enterToCogHQ(self, leg, time):
        self.loop('neutral', 0)

    def exitToCogHQ(self):
        pass

    def enterFromCogHQ(self, leg, time):
        self.loop('neutral', 0)
        self.detachNode()

    def exitFromCogHQ(self):
        self.reparentTo(render)

    def enterBattle(self):
        DistributedSuitBase.DistributedSuitBase.enterBattle(self)
        self.resumePath(0)

    def enterNeutral(self):
        self.notify.debug('DistributedSuit: Neutral (entering a Door)')
        self.resumePath(0)
        self.loop('neutral', 0)

    def exitNeutral(self):
        pass

    def enterPieSplat(self):
        self.play('pie-small-react')
        self.mtrack = MovieUtil.createSuitStunInterval(self, 0.3, 1.3)
        self.mtrack.start()

    def exitPieSplat(self):
        self.mtrack.finish()
        del self.mtrack

    def enterWaitForBattle(self):
        DistributedSuitBase.DistributedSuitBase.enterWaitForBattle(self)
        self.resumePath(0)

    def enterFlyAway(self):
        self.enableBattleDetect('flyAway', self.__handleToonCollision)
        self.ignorePie()
        if not self.verifySuitPlanner():
            return
        b = Point3(self.getPos())
        self.mtrack = self.beginSupaFlyMove(b, 0, self.uniqueName('flyAway'))
        self.mtrack.start()

    def exitFlyAway(self):
        self.disableBattleDetect()
        self.mtrack.finish()
        del self.mtrack
        self.detachPropeller()

    def enterDanceThenFlyAway(self):
        self.enableBattleDetect('danceThenFlyAway', self.__handleToonCollision)
        self.ignorePie()
        if not self.verifySuitPlanner():
            return
        danceTrack = self.actorInterval('victory')
        b = Point3(self.getPos())
        flyMtrack = self.beginSupaFlyMove(b, 0, self.uniqueName('flyAway'))
        self.mtrack = Sequence(danceTrack, flyMtrack, name=self.taskName('danceThenFlyAway'))
        self.mtrack.start()

    def exitDanceThenFlyAway(self):
        self.disableBattleDetect()
        self.mtrack.finish()
        del self.mtrack
        self.detachPropeller()

    def playCurrentDialogue(self, dialogue, chatFlags, interrupt = 1):
        DistributedSuitBase.DistributedSuitBase.playCurrentDialogue(self, dialogue, chatFlags, interrupt)

    def playDialogueForString(self, chatString, delay = 0.0, exclaim=False):
        DistributedSuitBase.DistributedSuitBase.playDialogueForString(self, chatString, delay, exclaim)

    def playDialogue(self, type, length, chatString = '', delay = 0.0):
        DistributedSuitBase.DistributedSuitBase.playDialogue(self, type, length, chatString, delay)

    def handleCollisionSphereExit(self, collisionEntry = None):
        self.ignore(f'exit{self.battleDetectName}')
        self.__destroyInteractHint()

    def __createInteractHint(self):
        if not hasattr(self, "interactHint"):
            self.accept(HotkeySettings.Interact.getPressed(),
                        self.__enterBattle)

            self.accept(f'exit{self.battleDetectName}', self.handleCollisionSphereExit)
            self.accept('toonExitWalk', self.handleCollisionSphereExit)
            text = ControlManager.ControlManager.parseHotkeyString(TTLocalizer.BattleInteract % self.getName(),
                                                                   useGlyphs=True)
            if self.nametag:
                fg = NametagGlobals.getNameFg(self.nametag.getColorCode(), 0)
                font = self.nametag.getNameFont()
            else:
                fg = (1.0, 1.0, 1.0, 1.0)
                font = ToontownGlobals.getFancyFont()
            self.interactHint = OnscreenText(text, style = 3, scale = .065, parent = base.a2dBottomCenter,
                                             font = font, shadow = (1.0, 1.0, 1.0, 1.0), fg = fg, pos = (0.0, 0.0))

            taskMgr.add(self.__alignInteractHint, self.alignInteractHintTaskName)

    def __destroyInteractHint(self, colEntry = None):
        self.ignore(HotkeySettings.Interact.getPressed())
        self.ignore('toonExitWalk')
        # Remove interact hint
        if hasattr(self, "interactHint"):
            taskMgr.remove(self.alignInteractHintTaskName)
            self.interactHint.removeNode()
            del self.interactHint

    def __alignInteractHint(self, task):
        """
        Aligns the interact hint on the screen
        The hint should be positioned on the npc, then the position is projected to the aspect2d
        """
        if self.isDisabled():
            self.notify.debug('__alignInteractHint: Suit gone')
            self.__destroyInteractHint()
            return task.done

        if hasattr(self, 'interactHint'):
            center = base.cam.getRelativePoint(self.nametagNodePath, Point3(0, 0, 0.3))

            if base.camNode.isInView(center):
                center2d = Point2()
                base.camLens.project(center, center2d)

                center2d.x = bound(center2d.x, -0.7, 0.7)
                center2d.y = bound(center2d.y, -0.9, 0.95)
                self.interactHint['text'] = ControlManager.ControlManager.parseHotkeyString(
                    TTLocalizer.BattleInteractNoName, useGlyphs=True
                )
            else:
                # If the point isnt in the view, we set it to the 'default' position
                center2d = Point2(0.0, -0.45)
                self.interactHint['text'] = ControlManager.ControlManager.parseHotkeyString(
                    TTLocalizer.BattleInteract % self.getName(), useGlyphs=True
                )

            self.interactHint.set_pos(render2d, Point3(center2d.x, 0, center2d.y))

        return task.cont

    @property
    def alignInteractHintTaskName(self):
        return f'alignInteractHint-{self.getDoId()}'
