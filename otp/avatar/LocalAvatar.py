from panda3d.core import *
from panda3d.toontown import Nametag, WhisperPopup
from direct.gui.DirectGui import *
from direct.showbase.PythonUtil import *
from direct.interval.IntervalGlobal import *
from direct.showbase.InputStateGlobal import inputState

from otp.avatar import OTPControlManager
from . import DistributedAvatar
from direct.task import Task
from otp.otpbase import OTPGlobals
import random
from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedSmoothNode
from otp.otpbase import OTPLocalizer
from .GravityWalker import GravityWalker
from direct.controls.ObserverWalker import ObserverWalker
from otp.avatar.SwimWalker import SwimWalker
from direct.controls.TwoDWalker import TwoDWalker

from toontown.hood import ZoneUtil
from ..camera.CameraFSM import CameraFSM
from ..camera.CameraGlobals import CameraMode
from ..otpbase.PythonUtil import deprecated
from toontown.toonbase import ClientSettings, HotkeySettings


class LocalAvatar(DistributedAvatar.DistributedAvatar, DistributedSmoothNode.DistributedSmoothNode):
    notify = DirectNotifyGlobal.directNotify.newCategory('LocalAvatar')
    wantDevCameraPositions = base.config.GetBool('want-dev-camera-positions', 0)
    wantMouse = base.config.GetBool('want-mouse', 0)
    sleepTimeout = base.config.GetInt('sleep-timeout', 120)
    swimTimeout = base.config.GetInt('afk-timeout', 600)
    acceptingNewFriends = base.config.GetBool('accepting-new-friends', 1)
    acceptingNonFriendWhispers = base.config.GetBool('accepting-non-friend-whispers', 0)
    GeomFadeLerpDur = 1.0

    def __init__(self, cr, chatMgr, talkAssistant = None):
        try:
            self.LocalAvatar_initialized
            return
        except:
            pass

        self.LocalAvatar_initialized = 1
        DistributedAvatar.DistributedAvatar.__init__(self, cr)
        DistributedSmoothNode.DistributedSmoothNode.__init__(self, cr)
        self.cTrav = CollisionTraverser('base.cTrav')
        base.pushCTrav(self.cTrav)
        self.cTrav.setRespectPrevTransform(1)
        self.avatarControlsEnabled = 0
        self.controlManager = OTPControlManager.OTPControlManager(True)
        self.initializeCollisions()
        self.cameraFSM = CameraFSM(avatar = self)
        self.cameraPositions = []
        self.animMultiplier = 1.0
        self.runTimeout = 2.5
        self.customMessages = []
        self.chatMgr = chatMgr
        base.talkAssistant = talkAssistant
        self.commonChatFlags = 0
        self.garbleChat = 1
        self.teleportAllowed = 1
        self.lockedDown = 0
        self.isPageUp = 0
        self.isPageDown = 0
        self.soundRun = None
        self.soundWalk = None
        self.sleepFlag = 0
        self.movingFlag = 0
        self.swimmingFlag = 0
        self.neverSleep = False
        self.lastNeedH = None
        self.accept('clickedWhisper', self.clickedWhisper)
        self.accept('playerOnline', self.__playerOnline)
        self.accept('playerOffline', self.__playerOffline)
        self.sleepCallback = None
        self.preventSleepWatch = False
        self.accept('wakeup', self.wakeUp)
        self.jumpLandAnimFixTask = None
        self.fov = OTPGlobals.DefaultCameraFov
        self.accept('avatarMoving', self.clearPageUpDown)
        self.nametag2dNormalContents = Nametag.CSpeech
        self.showNametag2d()
        self.setPickable(0)
        self.cameraLerp = None
        self.firstPerson = False
        self.cameraMode = 0
        self.shoulderTPNode = None

    def useSwimControls(self):
        self.controlManager.use('swim', self)

    def useGhostControls(self):
        self.controlManager.use('ghost', self)

    def useWalkControls(self):
        self.controlManager.use('walk', self)

    def useTwoDControls(self):
        self.controlManager.use('twoD', self)

    def isLockedDown(self):
        return self.lockedDown

    def lock(self):
        if self.lockedDown == 1:
            self.notify.debug('lock() - already locked!')
        self.lockedDown = 1

    def unlock(self):
        if self.lockedDown == 0:
            self.notify.debug('unlock() - already unlocked!')
        self.lockedDown = 0

    def isInWater(self):
        return self.getZ(render) <= 0.0

    def isTeleportAllowed(self):
        return self.teleportAllowed

    def setTeleportAllowed(self, flag):
        self.teleportAllowed = flag
        self.refreshOnscreenButtons()

    def sendSocialMenuEvent(self):
        self.wakeUp()
        self.notifications.exit()
        self.cameraMenu.exit()
        self.magicMenu.exit()
        messenger.send('openSocialMenu')

    def sendHideSocialMenuEvent(self):
        self.wakeUp()
        messenger.send('hideSocialMenu')

    def delete(self):
        try:
            self.LocalAvatar_deleted
        except AttributeError:
            self.LocalAvatar_deleted = 1

            self.ignoreAll()
            self.stopJumpLandTask()
            taskMgr.remove('shadowReach')
            base.popCTrav()
            if self.cameraLerp:
                self.cameraLerp.finish()
                self.cameraLerp = None
            self.disableAvatarControls()
            self.stopTrackAnimToSpeed()
            self.deactivateCamera()
            self.deleteCollisions()
            self.controlManager.delete()
            self.physControls = None
            del self.controlManager
            self.positionExaminer.delete()
            del self.positionExaminer
            taskMgr.remove(self.uniqueName('walkReturnTask'))
            self.chatMgr.delete()
            del self.chatMgr
            del self.soundRun
            del self.soundWalk
            if hasattr(self, 'soundWhisper'):
                del self.soundWhisper
            DistributedAvatar.DistributedAvatar.delete(self)
        return

    def shadowReach(self, state):
        if base.localAvatar.shadowPlacer:
            base.localAvatar.shadowPlacer.lifter.setReach(base.localAvatar.getAirborneHeight() + 4.0)
        return Task.cont

    def wantLegacyLifter(self):
        return False

    def setupControls(self, avatarRadius = 1.4, floorOffset = OTPGlobals.FloorOffset, reach = 4.0, wallBitmask = OTPGlobals.WallBitmask, floorBitmask = OTPGlobals.FloorBitmask, ghostBitmask = OTPGlobals.GhostBitmask):
        walkControls = GravityWalker(legacyLifter=self.wantLegacyLifter())
        walkControls.setWallBitMask(wallBitmask)
        walkControls.setFloorBitMask(floorBitmask)
        walkControls.initializeCollisions(self.cTrav, self, avatarRadius, floorOffset, reach)
        walkControls.setAirborneHeightFunc(self.getAirborneHeight)
        self.controlManager.add(walkControls, 'walk')
        self.physControls = walkControls
        twoDControls = TwoDWalker()
        twoDControls.setWallBitMask(wallBitmask)
        twoDControls.setFloorBitMask(floorBitmask)
        twoDControls.initializeCollisions(self.cTrav, self, avatarRadius, floorOffset, reach)
        twoDControls.setAirborneHeightFunc(self.getAirborneHeight)
        self.controlManager.add(twoDControls, 'twoD')
        swimControls = SwimWalker()
        swimControls.setWallBitMask(wallBitmask)
        swimControls.setFloorBitMask(floorBitmask)
        swimControls.initializeCollisions(self.cTrav, self, avatarRadius, floorOffset, reach)
        swimControls.setAirborneHeightFunc(self.getAirborneHeight)
        self.controlManager.add(swimControls, 'swim')
        ghostControls = GravityWalker(legacyLifter=self.wantLegacyLifter())
        ghostControls.setWallBitMask(ghostBitmask)
        ghostControls.setFloorBitMask(floorBitmask)
        ghostControls.initializeCollisions(self.cTrav, self, avatarRadius, floorOffset, reach)
        ghostControls.setAirborneHeightFunc(self.getAirborneHeight)
        self.controlManager.add(ghostControls, 'ghost')
        observerControls = ObserverWalker()
        observerControls.setWallBitMask(ghostBitmask)
        observerControls.setFloorBitMask(floorBitmask)
        observerControls.initializeCollisions(self.cTrav, self, avatarRadius, floorOffset, reach)
        observerControls.setAirborneHeightFunc(self.getAirborneHeight)
        self.controlManager.add(observerControls, 'observer')
        self.controlManager.use('walk', self)
        self.controlManager.disable()

    def initializeCollisions(self):
        self.setupControls()

        self.cRayMoveNodePath = hidden.attachNewNode('cRayMoveNode')
        self.avatarFloorCollisionBroadcaster = CollisionHandlerFloor()
        self.avatarFloorCollisionBroadcaster.setInPattern('on-floor')
        self.avatarFloorCollisionBroadcaster.setOutPattern('off-floor')
        self.avatarFloorCollisionBroadcaster.addCollider(
            self.physControls.cRayNodePath, self.cRayMoveNodePath)
        self.cTrav.addCollider(self.physControls.cRayNodePath,
                               self.avatarFloorCollisionBroadcaster)

    def deleteCollisions(self):
        self.cTrav.removeCollider(self.physControls.cRayNodePath)
        del self.avatarFloorCollisionBroadcaster
        self.cRayMoveNodePath.removeNode()
        del self.cRayMoveNodePath
        self.controlManager.deleteCollisions()
        self.ignore('entero157')
        del self.cTrav

    def collisionsOff(self):
        self.controlManager.collisionsOff()

    def collisionsOn(self):
        self.controlManager.collisionsOn()

    def putCameraFloorRayOnAvatar(self):
        self.camFloorRayNode.setPos(self, 0, 0, 5)

    def putCameraFloorRayOnCamera(self):
        self.camFloorRayNode.setPos(self.ccSphereNodePath, 0, 0, 0)

    def attachCamera(self):
        self.cameraFSM.attachCamera()
        base.enableMouse()
        base.setMouseOnNode(self.node())
        self.ignoreMouse = not self.wantMouse
        if ZoneUtil.isBetaPlaygroundZone(self.zoneId):
            self.setWalkSpeedOld()
        else:
            self.setWalkSpeedNormal()

    def detachCamera(self):
        base.disableMouse()

    def stopJumpLandTask(self):
        if self.jumpLandAnimFixTask:
            self.jumpLandAnimFixTask.remove()
            self.jumpLandAnimFixTask = None
        return

    def jumpStart(self):
        if not self.sleepFlag and self.hp > 0:
            self.b_setAnimState('jumpAirborne', 1.0)
            self.stopJumpLandTask()

    def returnToWalk(self, task):
        if self.sleepFlag:
            state = 'Sleep'
        elif self.hp > 0:
            state = 'Happy'
        else:
            state = 'Sad'
        self.b_setAnimState(state, 1.0)
        return Task.done

    def jumpLandAnimFix(self, jumpTime):
        if self.playingAnim != 'run' and self.playingAnim != 'walk':
            return taskMgr.doMethodLater(jumpTime, self.returnToWalk, self.uniqueName('walkReturnTask'))

    def jumpHardLand(self):
        if self.allowHardLand():
            self.b_setAnimState('jumpLand', 1.0)
            self.stopJumpLandTask()
            self.jumpLandAnimFixTask = self.jumpLandAnimFix(1.0)
        if self.d_broadcastPosHpr:
            self.d_broadcastPosHpr()

    def jumpLand(self):
        self.jumpLandAnimFixTask = self.jumpLandAnimFix(0.01)
        if self.d_broadcastPosHpr:
            self.d_broadcastPosHpr()

    def setupAnimationEvents(self):
        self.accept('jumpStart', self.jumpStart, [])
        self.accept('jumpHardLand', self.jumpHardLand, [])
        self.accept('jumpLand', self.jumpLand, [])

    def ignoreAnimationEvents(self):
        self.ignore('jumpStart')
        self.ignore('jumpHardLand')
        self.ignore('jumpLand')

    def allowHardLand(self):
        return not self.sleepFlag and self.hp > 0

    def enableSmartCameraViews(self):
        self.cameraFSM.initHotkeys()

    def disableSmartCameraViews(self):
        self.cameraFSM.ignoreHotkeys()
        return

    def enableAvatarControls(self):
        if self.avatarControlsEnabled:
            return
        self.avatarControlsEnabled = 1
        self.setupAnimationEvents()
        self.controlManager.enable()

    def disableAvatarControls(self):
        if not self.avatarControlsEnabled:
            return
        self.avatarControlsEnabled = 0
        self.ignoreAnimationEvents()
        self.controlManager.disable()
        self.clearPageUpDown()

    def setWalkSpeedNormal(self):
        self.controlManager.setSpeeds(OTPGlobals.ToonForwardSpeed, OTPGlobals.ToonJumpForce, OTPGlobals.ToonReverseSpeed, OTPGlobals.ToonRotateSpeed)

    def setWalkSpeedSlow(self):
        self.controlManager.setSpeeds(OTPGlobals.ToonForwardSlowSpeed, OTPGlobals.ToonJumpSlowForce, OTPGlobals.ToonReverseSlowSpeed, OTPGlobals.ToonRotateSlowSpeed)

    def setWalkSpeedOld(self):
        # Pre-2012 walk speed
        self.controlManager.setSpeeds(OTPGlobals.ToonForwardSpeedOld, OTPGlobals.ToonJumpForce, OTPGlobals.ToonReverseSpeedOld, OTPGlobals.ToonRotateSpeedOld)

    def disableJump(self):
        if not self.controlManager.forceAvJumpToken:
            self.controlManager.disableAvatarJump()

    def enableJump(self):
        if self.controlManager.forceAvJumpToken:
            self.controlManager.enableAvatarJump()

    def pageUp(self):
        if not self.avatarControlsEnabled:
            return
        self.wakeUp()
        if not self.isPageUp:
            self.isPageDown = 0
            self.isPageUp = 1
            self.lerpCameraFov(70 / (4./3.), 0.6, blendType = 'easeInOut')
            self.setCameraPositionByIndex(self.cameraIndex)
        else:
            self.clearPageUpDown()

    def pageDown(self):
        if not self.avatarControlsEnabled:
            return
        self.wakeUp()
        if not self.isPageDown:
            self.isPageUp = 0
            self.isPageDown = 1
            self.lerpCameraFov(70 / (4./3.), 0.6, blendType = 'easeInOut')
            self.setCameraPositionByIndex(self.cameraIndex)
        else:
            self.clearPageUpDown()

    def clearPageUpDown(self):
        if self.isPageDown or self.isPageUp:
            self.lerpCameraFov(self.fov / (4./3.), 0.6, blendType = 'easeInOut')
            self.isPageDown = 0
            self.isPageUp = 0
            self.setCameraPositionByIndex(self.cameraIndex)

    def nextCameraPos(self, forward):
        if not self.avatarControlsEnabled:
            return
        if self.firstPerson:
            self.enterFirstPerson(not self.cameraMode)
            return
        self.wakeUp()
        self.__cameraHasBeenMoved = 1
        if forward:
            self.cameraIndex += 1
            if self.cameraIndex > len(self.cameraPositions) - 1:
                self.cameraIndex = 0
        else:
            self.cameraIndex -= 1
            if self.cameraIndex < 0:
                self.cameraIndex = len(self.cameraPositions) - 1
        self.setCameraPositionByIndex(self.cameraIndex)

    def enterFirstPerson(self, mode = -1):
        if not self.avatarControlsEnabled and mode == -1:
            return
        self.wakeUp()
        self.__cameraHasBeenMoved = 1

        if self.firstPerson and mode == -1:
            self.exitFirstPerson()
            return
        self.cameraIndex = 1
        self.setCameraPositionByIndex(self.cameraIndex)
        if mode == -1:
            mode = self.cameraMode
        self.cameraMode = mode

        if self.cameraMode:
            camera.reparentTo(self.shoulderTPNode)
        else:
            camera.reparentTo(self)

        if not self.firstPerson:
            self.controlManager.setStrafing(True)

        self.firstPerson = True
        # Set the camera to the first person position
        camera.setPos(self.getIdealCameraPos())
        camera.setH(0)

        if not self.cameraMode:
            camera.setP(self.shoulderTPNode.getP())
        else:
            self.shoulderTPNode.setP(camera.getP())

        headParts = self.getHeadParts()
        if headParts:
            for head in headParts:
                if not self.cameraMode:
                    head.hide()
                else:
                    head.show()
        self.lerpCameraFov(60, 0.4, blendType = 'easeOut')
        # Lower the near distance to prevent clipping
        base.camLens.setNear(0.05)
        # Hide the mouse
        props = WindowProperties()
        props.setMouseMode(WindowProperties.MRelative)
        props.setCursorHidden(True)
        base.win.requestProperties(props)
        # Set mouse to center before starting the task to prevent a camera jump
        base.win.movePointer(0, base.win.getXSize() // 2, base.win.getYSize() // 2)
        taskName = self.taskName('updateFPCamera')
        taskMgr.remove(taskName)
        taskMgr.add(self.updateFPCamera, taskName, priority=47)

    def exitFirstPerson(self):
        if self.avatarControlsEnabled:
            self.firstPerson = 0
        if not self.isEmpty() and self.avatarControlsEnabled:
            camera.wrtReparentTo(self)
        taskName = self.taskName('updateFPCamera')
        taskMgr.remove(taskName)
        # Show the mouse
        props = WindowProperties()
        props.setMouseMode(WindowProperties.MAbsolute)
        props.setCursorHidden(False)

        self.controlManager.setStrafing(False)

        self.resetStrafeRotation()

        base.win.requestProperties(props)
        self.cameraIndex = 0
        self.setCameraPositionByIndex(self.cameraIndex)
        self.lerpCameraFov(OTPGlobals.DefaultCameraFov / (4. / 3.), 0.4, blendType = 'easeOut')
        headParts = self.getHeadParts()
        if headParts:
            for head in headParts:
                head.show()
        base.camLens.setNear(OTPGlobals.DefaultCameraNear)

    def updateFPCamera(self, task):
        if not self.firstPerson:
            return Task.done
        if not base.mouseWatcherNode.hasMouse():
            # The mouse doesn't exist (likely off screen)
            self.fpMouseDelta = (0, 0)
            return task.cont
        pointer = base.win.getPointer(0)
        if pointer.getX() > base.win.getXSize() or pointer.getY() > base.win.getYSize():
            # The pointer is off the screen, do nothing
            self.fpMouseDelta = (0, 0)
            return task.cont

        # Calculate how far the mouse has moved from the center this frame
        self.fpMouseDelta = (pointer.getX() - base.win.getXSize() // 2,
                             pointer.getY() - base.win.getYSize() // 2)

        # Return it to the center
        base.win.movePointer(0, base.win.getXSize() // 2, base.win.getYSize() // 2)

        deltaX, deltaY = self.fpMouseDelta
        if self.cameraMode == 0:
            camera.setPos(self.getIdealCameraPos())
        else:
            camHeight = self.getHeight()
            heightScaleFactor = max(camHeight * 0.3333333333, 1.2)
            self.shoulderTPNode.setZ(camHeight)
            camera.setPos(Vec3(heightScaleFactor, -4 * heightScaleFactor, 0))
            camera.setHpr(Vec3(0))
        # If the cursor is not in the center...
        if deltaX or deltaY:

            # then rotate!
            lastH = self.getH()
            newH = lastH + -deltaX * ClientSettings.CameraSensitivity.get() / 4
            self.setH(newH)

            lastP = camera.getP(self)
            newP = bound(lastP + -deltaY * ClientSettings.CameraSensitivity.get() / 4, -80, 80)
            if not self.cameraMode:
                camera.setP(newP)
            self.shoulderTPNode.setP(newP)

        return Task.cont

    def initCameraPositions(self):
        camHeight = self.getClampedAvatarHeight()
        heightScaleFactor = camHeight * 0.3333333333
        defLookAt = Point3(0.0, 1.5, camHeight)
        self.cameraPositions = [
           (
               Point3(0.0, -9.0 * heightScaleFactor, camHeight),
               defLookAt,
               Point3(0.0, camHeight, camHeight * 4.0),
               Point3(0.0, camHeight, camHeight * -1.0),
               0
           ),
           (
               Point3(0.0, 0.5, camHeight),
               defLookAt,
               Point3(0.0, camHeight, camHeight * 1.33),
               Point3(0.0, camHeight, camHeight * 0.66),
               1
           ),
           (
               Point3(5.7 * heightScaleFactor, 7.65 * heightScaleFactor, camHeight + 2.0),
               Point3(0.0, 1.0, camHeight),
               Point3(0.0, 1.0, camHeight * 4.0),
               Point3(0.0, 1.0, camHeight * -1.0),
               0
           ),
           (
               Point3(0.0, 12.0 * heightScaleFactor, camHeight),
               Point3(0.0, 1.0, camHeight),
               Point3(0.0, 1.5, camHeight * 4.0),
               Point3(0.0, 1.5, camHeight * -1.0),
               1),
           # cam for prop placing
           (
               Point3(0.0, -15, camHeight * 8),
               Point3(0.0, 0.0, 10),
               Point3(0.0, camHeight * 2, 0.0),
               Point3(0.0, -camHeight * 2, 0.0),
               1
           ),
           (
               Point3(0.0, -24.0 * heightScaleFactor, camHeight + 4.0),
               defLookAt,
               Point3(0.0, 1.5, camHeight * 4.0),
               Point3(0.0, 1.5, camHeight * -1.0),
               0),
           (
               Point3(0.0, -12.0 * heightScaleFactor, camHeight + 4.0),
               defLookAt,
               Point3(0.0, 1.5, camHeight * 4.0),
               Point3(0.0, 1.5, camHeight * -1.0),
               0
           )]# + self.auxCameraPositions
        if self.wantDevCameraPositions:
            self.cameraPositions += [(Point3(0.0, 0.0, camHeight * 3),
              Point3(0.0, 0.0, 0.0),
              Point3(0.0, camHeight * 2, 0.0),
              Point3(0.0, -camHeight * 2, 0.0),
              1),
             (Point3(camHeight * 3, 0.0, camHeight),
              Point3(0.0, 0.0, camHeight),
              Point3(0.0, camHeight, camHeight * 1.1),
              Point3(0.0, camHeight, camHeight * 0.9),
              1),
             (Point3(camHeight * 3, 0.0, 0.0),
              Point3(0.0, 0.0, camHeight),
              Point3(0.0, camHeight, camHeight * 1.1),
              Point3(0.0, camHeight, camHeight * 0.9),
              1),
             (Point3(-camHeight * 3, 0.0, camHeight),
              Point3(0.0, 0.0, camHeight),
              Point3(0.0, camHeight, camHeight * 1.1),
              Point3(0.0, camHeight, camHeight * 0.9),
              1),
             (Point3(0.0, -60, 60),
              defLookAt + Point3(0, 15, 0),
              defLookAt + Point3(0, 15, 0),
              defLookAt + Point3(0, 15, 0),
              1),
             (Point3(0.0, -20, 20),
              defLookAt + Point3(0, 5, 0),
              defLookAt + Point3(0, 5, 0),
              defLookAt + Point3(0, 5, 0),
              1)]

    def addCameraPosition(self, camPos = None):
        if camPos == None:
            lookAtNP = self.attachNewNode('lookAt')
            lookAtNP.setPos(base.cam, 0, 1, 0)
            lookAtPos = lookAtNP.getPos()
            camHeight = self.getClampedAvatarHeight()
            camPos = (base.cam.getPos(self),
             lookAtPos,
             Point3(0.0, 1.5, camHeight * 4.0),
             Point3(0.0, 1.5, camHeight * -1.0),
             1)
            lookAtNP.removeNode()
        self.auxCameraPositions.append(camPos)
        self.cameraPositions.append(camPos)
        return

    def resetCameraPosition(self):
        self.cameraIndex = 0
        if self.avatarControlsEnabled:
            self.cameraFSM.request('Off')
            self.cameraFSM.requestLastCamera()

    def removeCameraPosition(self):
        if len(self.cameraPositions) > 1:
            camPos = self.cameraPositions[self.cameraIndex]
            if camPos in self.auxCameraPositions:
                self.auxCameraPositions.remove(camPos)
            if camPos in self.cameraPositions:
                self.cameraPositions.remove(camPos)
            self.nextCameraPos(1)

    def printCameraPositions(self):
        print('[')
        for i in range(len(self.cameraPositions)):
            self.printCameraPosition(i)
            print(',')

        print(']')

    def printCameraPosition(self, index):
        cp = self.cameraPositions[index]
        print('(Point3(%0.2f, %0.2f, %0.2f),' % (cp[0][0], cp[0][1], cp[0][2]))
        print('Point3(%0.2f, %0.2f, %0.2f),' % (cp[1][0], cp[1][1], cp[1][2]))
        print('Point3(%0.2f, %0.2f, %0.2f),' % (cp[2][0], cp[2][1], cp[2][2]))
        print('Point3(%0.2f, %0.2f, %0.2f),' % (cp[3][0], cp[3][1], cp[3][2]))
        print('%d,' % cp[4])
        print(')', end=' ')

    def posCamera(self, lerp, time):
        if self.cameraFSM.activeCamera == CameraMode.CLASSIC:
            # todo: this should just be a cameraFSM.activeCamera.posCamera
            self.cameraFSM.classicCamera.posCamera(lerp, time)
            return

    def getClampedAvatarHeight(self):  # type: () -> float
        if self.getToonScale() != 1.0:
            return self.getHeight()
        return max(self.getHeight(), 3.0)

    def getVisibilityPoint(self):
        return Point3(0.0, 0.0, self.getHeight())

    def setLookAtPoint(self, la):
        self.__curLookAt = Point3(la)

    def getLookAtPoint(self):
        return Point3(self.__curLookAt)

    def setIdealCameraPos(self, pos):
        self.__idealCameraPos = Point3(pos)
        self.updateSmartCameraCollisionLineSegment()

    def getIdealCameraPos(self):
        return Point3(self.__idealCameraPos)

    def setCameraPositionByIndex(self, index):
        self.notify.debug('switching to camera position %s' % index)
        self.setCameraSettings(self.cameraPositions[index])

    def setCameraPosForPetInteraction(self):
        return
        height = self.getClampedAvatarHeight()
        point = Point3(height * (7 / 3.0), height * (-7 / 3.0), height)
        self.prevIdealPos = self.getIdealCameraPos()
        self.setIdealCameraPos(point)
        self.posCamera(1, 0.7)

    def unsetCameraPosForPetInteraction(self):
        return
        if hasattr(self, 'prevIdealPos'):
            self.setIdealCameraPos(self.prevIdealPos)
            del self.prevIdealPos
        self.posCamera(1, 0.7)

    def setCameraSettings(self, camSettings):
        self.setIdealCameraPos(camSettings[0])
        if self.isPageUp and self.isPageDown or not self.isPageUp and not self.isPageDown:
            self.__cameraHasBeenMoved = 1
            self.setLookAtPoint(camSettings[1])
        elif self.isPageUp:
            self.__cameraHasBeenMoved = 1
            self.setLookAtPoint(camSettings[2])
        elif self.isPageDown:
            self.__cameraHasBeenMoved = 1
            self.setLookAtPoint(camSettings[3])
        else:
            self.notify.error('This case should be impossible.')
        self.__disableSmartCam = camSettings[4]
        if self.__disableSmartCam:
            self.putCameraFloorRayOnAvatar()
            self.cameraZOffset = 0.0

    def getCompromiseCameraPos(self):
        if self.__idealCameraObstructed == 0:
            compromisePos = self.getIdealCameraPos()
        else:
            visPnt = self.getVisibilityPoint()
            idealPos = self.getIdealCameraPos()
            distance = Vec3(idealPos - visPnt).length()
            ratio = self.closestObstructionDistance / distance
            compromisePos = idealPos * ratio + visPnt * (1 - ratio)
            liftMult = 1.0 - ratio * ratio
            compromisePos = Point3(compromisePos[0], compromisePos[1], compromisePos[2] + self.getHeight() * 0.4 * liftMult)
        compromisePos.setZ(compromisePos[2] + self.cameraZOffset)
        return compromisePos

    def updateSmartCameraCollisionLineSegment(self):
        pointB = self.getIdealCameraPos()
        pointA = self.getVisibilityPoint()
        vectorAB = Vec3(pointB - pointA)
        lengthAB = vectorAB.length()
        if lengthAB > 0.001:
            self.ccLine.setPointA(pointA)
            self.ccLine.setPointB(pointB)

    @deprecated('Use camerafsm!')
    def initializeSmartCamera(self):
        return
        self.__idealCameraObstructed = 0
        self.closestObstructionDistance = 0.0
        self.cameraIndex = 0
        self.auxCameraPositions = []
        self.cameraZOffset = 0.0
        self.__onLevelGround = 0
        self.__camCollCanMove = 0
        self.__geom = render
        self.__disableSmartCam = 0
        self.initializeSmartCameraCollisions()
        self._smartCamEnabled = False

    def setOnLevelGround(self, flag):
        self.__onLevelGround = flag

    def setCameraCollisionsCanMove(self, flag):
        self.__camCollCanMove = flag

    def setGeom(self, geom):
        self.__geom = geom

    def activateCamera(self, push = 1):
        # Set our camera to the last one we used.
        self.cameraFSM.requestLastCamera()

    def deactivateCamera(self):
        self.cameraFSM.request('Off')

    def updateSmartCamera(self, task):
        if self.firstPerson:
            return Task.cont
        if not self.__camCollCanMove and not self.__cameraHasBeenMoved:
            if self.__lastPosWrtRender == camera.getPos(render):
                if self.__lastHprWrtRender == camera.getHpr(render):
                    return Task.cont
        self.__cameraHasBeenMoved = 0
        self.__lastPosWrtRender = camera.getPos(render)
        self.__lastHprWrtRender = camera.getHpr(render)
        self.__idealCameraObstructed = 0
        if not self.__disableSmartCam:
            self.ccTrav.traverse(self.__geom)
            if self.camCollisionQueue.getNumEntries() > 0:
                self.camCollisionQueue.sortEntries()
                self.handleCameraObstruction(self.camCollisionQueue.getEntry(0))
            if not self.__onLevelGround:
                self.handleCameraFloorInteraction()
        if not self.__idealCameraObstructed:
            self.nudgeCamera()
        if not self.__disableSmartCam:
            self.ccPusherTrav.traverse(self.__geom)
            self.putCameraFloorRayOnCamera()
        self.ccTravOnFloor.traverse(self.__geom)

        # Fade objects that get too close to the camera
        # Ported from Pirates
        nonObstrGeoms = dict(self._hiddenGeoms)
        self.ccFadeTrav.traverse(self.__geom)
        if self.camFadeCollisionQueue.getNumEntries() > 0:
            self.camFadeCollisionQueue.sortEntries()
            for collEntry in self.camFadeCollisionQueue.getEntries():
                intoNP = collEntry.getIntoNodePath()
                cMask = intoNP.node().getIntoCollideMask()
                # Collide masks with the bit for CameraBitmask turned on
                # can show up here too so we gotta double check
                if not (cMask & OTPGlobals.CameraTransparentBitmask).isZero():
                    if intoNP in nonObstrGeoms:
                        del nonObstrGeoms[intoNP]
                    self._fadeGeom(intoNP)
                    break
        for np in nonObstrGeoms.keys():
            self._unfadeGeom(np)
        return Task.cont

    def _fadeGeom(self, np):
        if np in self._fadeInIvals:
            self._fadeInIvals[np].finish()
            del self._fadeInIvals[np]
        if np not in self._hiddenGeoms:
            hadTransparency = np.getTransparency()
            fadeIval = Sequence(Func(np.setTransparency, 1),
                                LerpColorScaleInterval(np, self.GeomFadeLerpDur, VBase4(1, 1, 1, 0),
                                                       blendType='easeInOut'), name='CamFadeGeomOut')
            self._hiddenGeoms[np] = hadTransparency
            self._fadeOutIvals[np] = fadeIval
            fadeIval.start()

    def _unfadeGeom(self, np):
        if np in self._hiddenGeoms:
            if np in self._fadeOutIvals:
                self._fadeOutIvals[np].pause()
                del self._fadeOutIvals[np]
            fadeIval = Sequence(
                LerpColorScaleInterval(np, self.GeomFadeLerpDur, VBase4(1, 1, 1, 1), blendType='easeInOut'),
                Func(np.setTransparency, self._hiddenGeoms[np]), name='CamFadeGeomIn')
            del self._hiddenGeoms[np]
            self._fadeInIvals[np] = fadeIval
            fadeIval.start()

    def positionCameraWithPusher(self, pos, lookAt):
        if self.firstPerson:
            return Task.cont
        camera.setPos(pos)
        self.ccPusherTrav.traverse(self.__geom)
        camera.lookAt(lookAt)

    def nudgeCamera(self):
        CLOSE_ENOUGH = 0.01
        curCamPos = self.__instantaneousCamPos
        curCamHpr = camera.getHpr()
        targetCamPos = self.getCompromiseCameraPos()
        targetCamLookAt = self.getLookAtPoint()
        posDone = 0
        if Vec3(curCamPos - targetCamPos).length() <= CLOSE_ENOUGH:
            camera.setPos(targetCamPos)
            posDone = 1
        camera.setPos(targetCamPos)
        camera.lookAt(targetCamLookAt)
        targetCamHpr = camera.getHpr()
        hprDone = 0
        if Vec3(curCamHpr - targetCamHpr).length() <= CLOSE_ENOUGH:
            hprDone = 1
        if posDone and hprDone:
            return
        lerpRatio = 0.15
        lerpRatio = 1 - pow(1 - lerpRatio, globalClock.getDt() * 30.0)
        self.__instantaneousCamPos = targetCamPos * lerpRatio + curCamPos * (1 - lerpRatio)
        if self.__disableSmartCam or not self.__idealCameraObstructed:
            newHpr = targetCamHpr * lerpRatio + curCamHpr * (1 - lerpRatio)
        else:
            newHpr = targetCamHpr
        camera.setPos(self.__instantaneousCamPos)
        camera.setHpr(newHpr)

    def popCameraToDest(self):
        newCamPos = self.getCompromiseCameraPos()
        newCamLookAt = self.getLookAtPoint()
        self.positionCameraWithPusher(newCamPos, newCamLookAt)
        self.__instantaneousCamPos = camera.getPos()

    def handleCameraObstruction(self, camObstrCollisionEntry):
        collisionPoint = camObstrCollisionEntry.getSurfacePoint(self.ccLineNodePath)
        collisionVec = Vec3(collisionPoint - self.ccLine.getPointA())
        distance = collisionVec.length()
        self.__idealCameraObstructed = 1
        self.closestObstructionDistance = distance
        self.popCameraToDest()

    def handleCameraFloorInteraction(self):
        self.putCameraFloorRayOnCamera()
        self.ccTravFloor.traverse(self.__geom)
        if self.__onLevelGround:
            return
        if self.camFloorCollisionQueue.getNumEntries() == 0:
            return
        self.camFloorCollisionQueue.sortEntries()
        camObstrCollisionEntry = self.camFloorCollisionQueue.getEntry(0)
        camHeightFromFloor = camObstrCollisionEntry.getSurfacePoint(self.ccRayNodePath)[2]
        self.cameraZOffset = camera.getPos()[2] + camHeightFromFloor
        if self.cameraZOffset < 0:
            self.cameraZOffset = 0
        if self.__floorDetected == 0:
            self.__floorDetected = 1
            self.popCameraToDest()

    def lerpCameraFov(self, fov, time, blendType = 'noBlend'):
        if self.cameraFSM.activeCamera:
            self.cameraFSM.activeCamera.lerpCameraFov(fov, time, blendType)

    def setCameraFov(self, fov):
        if hasattr(self, 'camLerpInterval'):
            self.camLerpInterval.finish()
        self.fov = fov
        if not (self.isPageDown or self.isPageUp):
            base.camLens.setMinFov(self.fov)

    def gotoNode(self, node, eyeHeight = 3):
        possiblePoints = (Point3(3, 6, 0),
         Point3(-3, 6, 0),
         Point3(6, 6, 0),
         Point3(-6, 6, 0),
         Point3(3, 9, 0),
         Point3(-3, 9, 0),
         Point3(6, 9, 0),
         Point3(-6, 9, 0),
         Point3(9, 9, 0),
         Point3(-9, 9, 0),
         Point3(6, 0, 0),
         Point3(-6, 0, 0),
         Point3(6, 3, 0),
         Point3(-6, 3, 0),
         Point3(9, 9, 0),
         Point3(-9, 9, 0),
         Point3(0, 12, 0),
         Point3(3, 12, 0),
         Point3(-3, 12, 0),
         Point3(6, 12, 0),
         Point3(-6, 12, 0),
         Point3(9, 12, 0),
         Point3(-9, 12, 0),
         Point3(0, -6, 0),
         Point3(-3, -6, 0),
         Point3(0, -9, 0),
         Point3(-6, -9, 0))
        for point in possiblePoints:
            pos = self.positionExaminer.consider(node, point, eyeHeight)
            if pos:
                self.setPos(node, pos)
                self.lookAt(node)
                self.setHpr(self.getH() + random.choice((-10, 10)), 0, 0)
                return

        self.setPos(node, 0, 0, 0)

    def setCustomMessages(self, customMessages):
        self.customMessages = customMessages
        messenger.send('customMessagesChanged')

    def displayWhisper(self, fromId, chatString, whisperType):
        sender = None
        if not hasattr(self, 'soundWhisper') or not self.soundWhisper:
            return
        sfx = self.soundWhisper
        if whisperType == WhisperPopup.WTNormal or whisperType == WhisperPopup.WTQuickTalker:
            if sender == None:
                return
            base.talkAssistant.logWhisperFrom(sender, chatString)
            chatString = sender.getName() + ': ' + chatString
        whisper = WhisperPopup(chatString, OTPGlobals.getInterfaceFont(), whisperType)
        if sender != None:
            whisper.setClickable(sender.getName(), fromId)
        whisper.manage(base.marginManager)
        base.playSfx(sfx)
        return

    def displayWhisperPlayer(self, fromId, chatString, whisperType):
        sender = None
        playerInfo = None
        sfx = self.soundWhisper
        playerInfo = base.cr.playerFriendsManager.playerId2Info.get(fromId, None)
        if playerInfo == None:
            return
        senderName = playerInfo.playerName
        if whisperType == WhisperPopup.WTNormal or whisperType == WhisperPopup.WTQuickTalker:
            chatString = senderName + ': ' + chatString
        whisper = WhisperPopup(chatString, OTPGlobals.getInterfaceFont(), whisperType)
        if sender != None:
            whisper.setClickable(senderName, fromId)
        whisper.manage(base.marginManager)
        base.playSfx(sfx)
        return

    def setAnimMultiplier(self, value):
        self.animMultiplier = value

    def getAnimMultiplier(self):
        return self.animMultiplier

    def enableRun(self):
        self.accept('arrow_up', self.startRunWatch)
        self.accept('arrow_up-up', self.stopRunWatch)
        self.accept('control-arrow_up', self.startRunWatch)
        self.accept('control-arrow_up-up', self.stopRunWatch)
        self.accept('alt-arrow_up', self.startRunWatch)
        self.accept('alt-arrow_up-up', self.stopRunWatch)
        self.accept('shift-arrow_up', self.startRunWatch)
        self.accept('shift-arrow_up-up', self.stopRunWatch)

    def disableRun(self):
        self.ignore('arrow_up')
        self.ignore('arrow_up-up')
        self.ignore('control-arrow_up')
        self.ignore('control-arrow_up-up')
        self.ignore('alt-arrow_up')
        self.ignore('alt-arrow_up-up')
        self.ignore('shift-arrow_up')
        self.ignore('shift-arrow_up-up')

    def startRunWatch(self):

        def setRun(ignored):
            messenger.send('running-on')

        taskMgr.doMethodLater(self.runTimeout, setRun, self.uniqueName('runWatch'))
        return Task.cont

    def stopRunWatch(self):
        taskMgr.remove(self.uniqueName('runWatch'))
        messenger.send('running-off')
        return Task.cont

    def runSound(self):
        self.soundWalk.stop()
        base.playSfx(self.soundRun, looping=1)

    def walkSound(self):
        self.soundRun.stop()
        base.playSfx(self.soundWalk, looping=1)

    def stopSound(self):
        self.soundRun.stop()
        self.soundWalk.stop()

    def disableSleeping(self):
        self.neverSleep = True
        self.reconsiderSleep()

    def enableSleeping(self):
        self.neverSleep = False
        self.reconsiderSleep()

    def reconsiderSleep(self):
        self.notify.debug('Reconsidering sleep watch for local avatar.')
        if self.neverSleep or self.ghostMode == 2:
            # prevent sleep if sleep disabled or ghosting
            self.setPreventSleepWatch(True)
        else:
            self.setPreventSleepWatch(False)

        # Wake up the toon
        self.lastMoved = globalClock.getFrameTime()
        if self.sleepFlag:
            self.sleepFlag = 0

    def wakeUp(self):
        if self.neverSleep or self.ghostMode == 2:
            return
        if self.sleepCallback != None:
            taskMgr.remove(self.uniqueName('sleepwatch'))
            self.startSleepWatch(self.sleepCallback)
        self.lastMoved = globalClock.getFrameTime()
        if self.sleepFlag:
            self.sleepFlag = 0
        return

    def gotoSleep(self):
        if self.neverSleep or self.ghostMode == 2:
            return
        if not self.sleepFlag:
            self.b_setAnimState('Sleep', self.animMultiplier)
            self.sleepFlag = 1

    def forceGotoSleep(self):
        if self.hp > 0:
            self.sleepFlag = 0
            self.gotoSleep()

    def setPreventSleepWatch(self, preventSleepWatch):
        self.preventSleepWatch = preventSleepWatch

        if self.preventSleepWatch:
            taskMgr.remove(self.uniqueName('sleepwatch'))
        elif self.sleepCallback:
            self.startSleepWatch(self.sleepCallback)

    def startSleepWatch(self, callback):
        if self.preventSleepWatch:
            return

        self.sleepCallback = callback
        taskMgr.doMethodLater(self.sleepTimeout, callback, self.uniqueName('sleepwatch'))

    def stopSleepWatch(self):
        taskMgr.remove(self.uniqueName('sleepwatch'))
        self.sleepCallback = None
        return

    def startSleepSwimTest(self):
        taskName = self.taskName('sleepSwimTest')
        taskMgr.remove(taskName)
        task = Task.Task(self.sleepSwimTest)
        self.lastMoved = globalClock.getFrameTime()
        self.lastState = None
        self.lastAction = None
        self.sleepSwimTest(task)
        taskMgr.add(self.sleepSwimTest, taskName, 35)
        return

    def stopSleepSwimTest(self):
        taskName = self.taskName('sleepSwimTest')
        taskMgr.remove(taskName)
        self.stopSound()

    def sleepSwimTest(self, task):
        now = globalClock.getFrameTime()
        speed, rotSpeed, slideSpeed = self.controlManager.getSpeeds()
        if speed != 0.0 or rotSpeed != 0.0 or inputState.isSet('jump'):
            if not self.swimmingFlag:
                self.swimmingFlag = 1
        elif self.swimmingFlag:
            self.swimmingFlag = 0
        if self.swimmingFlag or self.hp <= 0:
            self.wakeUp()
        elif not self.sleepFlag:
            now = globalClock.getFrameTime()
            if now - self.lastMoved > self.swimTimeout:
                self.swimTimeoutAction()
                return Task.done
        return Task.cont

    def swimTimeoutAction(self):
        pass

    def trackAnimToSpeed(self, task):
        speed, rotSpeed, slideSpeed = self.controlManager.getSpeeds()
        if speed != 0.0 or rotSpeed != 0.0 or slideSpeed != 0 or inputState.isSet('jump'):
            if not self.movingFlag:
                self.movingFlag = 1
                self.stopLookAround()
        elif self.movingFlag:
            self.movingFlag = 0
            self.startLookAround()
        if self.movingFlag or self.hp <= 0:
            self.wakeUp()
        elif not self.sleepFlag:
            now = globalClock.getFrameTime()
            if now - self.lastMoved > self.sleepTimeout:
                self.gotoSleep()
        if self.sleepFlag:
            state = 'Sleep'
        elif self.hp > 0:
            state = 'Happy'
        else:
            state = 'Sad'
        if state != self.lastState:
            self.lastState = state
            if state != 'Sleep':
                # do NOT repeat a Sleep anim state call.
                # if not, this causes EVERYONE to see two sleep chats for *one* sleep call!
                self.b_setAnimState(state, self.animMultiplier)
            if state == 'Sad':
                self.setWalkSpeedSlow()
            elif ZoneUtil.isBetaPlaygroundZone(self.zoneId) and ClientSettings.BetaPlaygroundMovement.get():
                self.setWalkSpeedOld()
            else:
                self.setWalkSpeedNormal()
        if self.cheesyEffect == OTPGlobals.CEFlatProfile or self.cheesyEffect == OTPGlobals.CEFlatPortrait:
            needH = None
            if rotSpeed > 0.0:
                needH = -10
            elif rotSpeed < 0.0:
                needH = 10
            elif speed != 0.0:
                needH = 0
            if needH != None and self.lastNeedH != needH:
                node = self.getGeomNode().getChild(0)
                lerp = Sequence(LerpHprInterval(node, 0.5, Vec3(needH, 0, 0), blendType='easeInOut'), name='cheesy-lerp-hpr', autoPause=1)
                lerp.start()
                self.lastNeedH = needH
        else:
            self.lastNeedH = None
        action = self.setSpeed(speed, rotSpeed, slideSpeed)
        if action != self.lastAction:
            self.lastAction = action
            if self.emoteTrack:
                self.emoteTrack.finish()
                self.emoteTrack = None
            if action == OTPGlobals.WALK_INDEX or action == OTPGlobals.REVERSE_INDEX:
                self.walkSound()
            elif action in (OTPGlobals.RUN_INDEX, OTPGlobals.STRAFE_LEFT_INDEX, OTPGlobals.STRAFE_RIGHT_INDEX):
                self.runSound()
            else:
                self.stopSound()
        return Task.cont

    def hasTrackAnimToSpeed(self):
        taskName = self.taskName('trackAnimToSpeed')
        return taskMgr.hasTaskNamed(taskName)

    def startTrackAnimToSpeed(self):
        taskName = self.taskName('trackAnimToSpeed')
        taskMgr.remove(taskName)
        task = Task.Task(self.trackAnimToSpeed)
        self.lastMoved = globalClock.getFrameTime()
        self.lastState = None
        self.lastAction = None
        self.trackAnimToSpeed(task)
        taskMgr.add(self.trackAnimToSpeed, taskName, 35)
        return

    def stopTrackAnimToSpeed(self):
        taskName = self.taskName('trackAnimToSpeed')
        taskMgr.remove(taskName)
        self.stopSound()

    def startChat(self):
        self.chatMgr.start()
        self.accept(OTPGlobals.WhisperIncomingEvent, self.handlePlayerFriendWhisper)
        self.accept(HotkeySettings.DebugCamera.getPressed(), self.printCamPos)

    def stopChat(self):
        self.chatMgr.stop()
        self.ignore(OTPGlobals.WhisperIncomingEvent)
        self.ignore(HotkeySettings.DebugCamera.getPressed())

    def printCamPos(self):
        node = base.camera.getParent()
        pos = base.cam.getPos(node)
        hpr = base.cam.getHpr(node)
        print('cam pos = ', repr(pos), ', cam hpr = ', repr(hpr))

    def d_broadcastPositionNow(self):
        self.d_clearSmoothing()
        self.d_broadcastPosHpr()

    def travCollisionsLOS(self, n = None):
        if n == None:
            n = self.__geom
        self.ccTrav.traverse(n)

    def travCollisionsFloor(self, n = None):
        if n == None:
            n = self.__geom
        self.ccTravFloor.traverse(n)

    def travCollisionsPusher(self, n = None):
        if n == None:
            n = self.__geom
        self.ccPusherTrav.traverse(n)

    def __playerOnline(self, playerId):
        playerInfo = base.cr.playerFriendsManager.playerId2Info[playerId]
        if playerInfo:
            self.setSystemMessage(playerId, OTPLocalizer.WhisperPlayerOnline % (playerInfo.playerName, playerInfo.location))

    def __playerOffline(self, playerId):
        playerInfo = base.cr.playerFriendsManager.playerId2Info[playerId]
        if playerInfo:
            self.setSystemMessage(playerId, OTPLocalizer.WhisperPlayerOffline % playerInfo.playerName)

    def clickedWhisper(self, doId, isPlayer = None):
        if not isPlayer:
            friend = base.cr.identifyFriend(doId)
            if friend != None:
                messenger.send('clickedNametag', [friend])
                self.chatMgr.whisperTo(friend.getName(), doId, None, True)
        else:
            friend = base.cr.playerFriendsManager.getFriendInfo(doId)
            if friend:
                messenger.send('clickedNametagPlayer', [None, doId])
                self.chatMgr.whisperTo(friend.getName(), None, doId, None, True)
        return

    def d_setParent(self, parentToken):
        DistributedSmoothNode.DistributedSmoothNode.d_setParent(self, parentToken)

    def handlePlayerFriendWhisper(self, playerId, charMessage):
        print('handlePlayerFriendWhisper')
        self.displayWhisperPlayer(playerId, charMessage, WhisperPopup.WTNormal)

    def canChat(self):
        return 0

    def toggleLogo(self):
        logo = aspect2dp.find('**/sampleLogo')
        if logo is not None and not logo.isEmpty():
            logo.removeNode()
        else:
            loadingGui = loader.loadModel('phase_3/models/gui/loading-background')
            logo = loadingGui.find('**/logo').copyTo(aspect2dp.attachNewNode('sampleLogo'))
            logo.setPos(0, 0, 0.55)
            logo.setScale(0.7 * 1.25, 0.7 * 1.25, 0.45 * 1.25)
            loadingGui.removeNode()

    def getActiveCamera(self):
        if self.cameraFSM.state == 'Off':
            return None
        return self.cameraFSM.activeCamera


    def getActiveCameraMode(self):
        if self.cameraFSM.state == 'Off':
            return None
        return self.cameraFSM.activeCameraMode