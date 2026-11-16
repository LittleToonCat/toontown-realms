"""
Classic Camera Mode
"""
import math
from typing import Tuple, Optional

from direct.interval.LerpInterval import LerpPosHprInterval
from direct.task import Task
from panda3d.core import CollisionTraverser, CollisionSegment, CollisionHandlerQueue, BitMask32, \
    CollisionSphere, CollisionNode, CollisionHandlerPusher, CollisionRay, CollisionHandlerFloor, Point3, Vec3, \
    deg2Rad, CollisionEntry, Vec3F, NodePath

from otp.camera.CameraBase import CameraBase
from otp.otpbase import OTPGlobals
from toontown.toonbase import ClientSettings


class CameraClassic(CameraBase):

    def __init__(self, avatar):
        self.initializedCollisions = False
        self._smartCamEnabled = False
        super().__init__(avatar)
        self.__idealCameraObstructed = 0
        self.closestObstructionDistance = 0.0
        # create self.cameraIndex
        self.cameraIndex = 0
        self.auxCameraPositions = []
        self.cameraZOffset = 0.0

        self.__lastPosWrtRender: Optional[Vec3F] = None
        self.__lastHprWrtRender: Optional[Vec3F] = None

        self.__onLevelGround = 0
        self.__camCollCanMove = 0
        self.__geom: NodePath = render

    def enterActive(self):
        self.attachCamera()

        self.__disableSmartCam = 0

        self.__onLevelGround = 0
        self.__camCollCanMove = 0
        self.__geom = render
        if not self.initializedCollisions:
            self.initializeSmartCameraCollisions()

        self.startUpdateSmartCamera()

    def startUpdateSmartCamera(self, push: bool = 1):
        """
        Spawn a task to update the smart camera every frame
        """
        if self._smartCamEnabled:
            self.notify.warning(
                    'redundant call to startUpdateSmartCamera')
            return

        # We use getKey() as a temporary workaround for problem with
        # inherited ==.
        assert camera.getParent().getKey() == self.avatar.getKey(), \
            "camera must be parented to localToon before calling " \
            "startUpdateSmartCamera"

        self._smartCamEnabled = True

        # this flag is needed in cases where the camera is created before
        # it's put into the world. When the world suddenly shows up, we
        # jump to where the floor is and set this flag.
        self.__floorDetected = 0

        # In the smart camera update task,
        # we check to see if the camera has moved (wrt render) since
        # the last frame. If it hasn't, then the camera can't possibly
        # have become obstructed, since there is nothing that moves AND
        # obstructs the camera. We can use this knowledge to save some
        # CPU time.
        # When we move the camera explicitly to a new location (i.e. when
        # the user presses TAB), we need to override this check, by setting
        # this flag to a non-zero value.
        self.__cameraHasBeenMoved = 0

        # adjust for any changes to the camera FOV, etc.
        self.recalcCameraSphere()

        # initialize a whole buncha stuff
        # this would all be in initializeSmartCamera() except that self.height
        # is NOT set by the time initializeSmartCamera() is called
        self.initCameraPositions()
        self.setCameraPositionByIndex(self.cameraIndex)
        # slam the camera to its destination
        self.posCamera(0, 0.)
        # self.__instantaneousCamPos holds the current "instantaneous"
        # camera position. this variable is used to keep the camera moving
        # in a straight line towards its target position regardless of how
        # the camera is pushed off-track by its pusher.
        self.__instantaneousCamPos = camera.getPos()

        if push:

            # Activate the camera Pusher
            self.avatar.cTrav.addCollider(self.ccSphereNodePath, self.camPusher)
            # activate the on-floor ray
            self.ccTravOnFloor.addCollider(self.ccRay2NodePath,
                                           self.camFloorCollisionBroadcaster)
            self.__disableSmartCam = 0
        else:
            self.__disableSmartCam = 1

        self.__lastPosWrtRender = camera.getPos(render)
        self.__lastHprWrtRender = camera.getHpr(render)

        # remove any old
        self.removeTask("updateSmartCamera")
        # spawn the new task
        # Set the priority somewhere between the collision task and
        # the rendering:
        self.addTask(self.updateSmartCamera, "updateSmartCamera", priority = 47)

    def enterInactive(self):
        # self.disableSmartCameraViews()
        if not self.initializedCollisions:
            return
        # Deactivate the cam pusher
        self.avatar.cTrav.removeCollider(self.ccSphereNodePath)
        # Deactivate the on-floor ray
        self.ccTravOnFloor.removeCollider(self.ccRay2NodePath)

        # make sure the floor-detection rays are right on top of the
        # toon (but watch out when we're shutting down and the toon has
        # already been deleted).
        if not base.localAvatar.isEmpty():
            self.putCameraFloorRayOnAvatar()

        self.removeTask("updateSmartCamera")
        self._smartCamEnabled = False
        self.deleteSmartCameraCollisions()

    def initializeSmartCameraCollisions(self):
        self.initializedCollisions = True
        # SMART-CAMERA STUFF

        # set up the smart camera's collision traverser
        # we need this because normal collisions get handled just before
        # rendering. using the normal collision mechanisms would introduce
        # one frame of lag in the smart camera, allowing the camera to pop
        # through walls momentarily.
        self.ccTrav = CollisionTraverser("ClassicCamera.ccTrav")

        # Set up the camera obstruction test line segment
        # This is a line segment from the visibility point to the ideal
        # camera location
        self.ccLine = CollisionSegment(0.0, 0.0, 0.0, 1.0, 0.0, 0.0)
        self.ccLineNode = CollisionNode('ccLineNode')
        self.ccLineNode.addSolid(self.ccLine)
        self.ccLineNodePath = self.avatar.attachNewNode(self.ccLineNode)
        self.ccLineBitMask = OTPGlobals.CameraBitmask
        self.ccLineNode.setFromCollideMask(self.ccLineBitMask)
        self.ccLineNode.setIntoCollideMask(BitMask32.allOff())

        # set up camera collision mechanism
        self.camCollisionQueue = CollisionHandlerQueue()

        # set up camera obstruction collision reciever
        self.ccTrav.addCollider(self.ccLineNodePath, self.camCollisionQueue)

        ## set up a sphere around camera to keep it away from the walls

        # make the sphere
        # the sphere attribs will be calculated later
        self.ccSphere = CollisionSphere(0, 0, 0, 1)
        self.ccSphereNode = CollisionNode('ccSphereNode')
        self.ccSphereNode.addSolid(self.ccSphere)
        self.ccSphereNodePath = base.camera.attachNewNode(self.ccSphereNode)
        self.ccSphereNode.setFromCollideMask(OTPGlobals.CameraBitmask)
        self.ccSphereNode.setIntoCollideMask(BitMask32.allOff())

        # attach a pusher to the sphere
        self.camPusher = CollisionHandlerPusher()
        # Do this when the camera gets activated
        # self.cTrav.addCollider(self.ccSphereNodePath, self.camPusher)
        self.camPusher.addCollider(self.ccSphereNodePath, base.camera)

        # Set a special mode on the pusher so that it doesn't get
        # fooled by walls facing away from the toon.
        self.camPusher.setCenter(self.avatar)

        ####
        # create another traverser with a camera pusher
        # sphere so that we can push the camera at will
        self.ccPusherTrav = CollisionTraverser("LocalAvatar.ccPusherTrav")

        # make the sphere
        self.ccSphere2 = self.ccSphere
        self.ccSphereNode2 = CollisionNode('ccSphereNode2')
        self.ccSphereNode2.addSolid(self.ccSphere2)
        self.ccSphereNodePath2 = base.camera.attachNewNode(self.ccSphereNode2)
        self.ccSphereNode2.setFromCollideMask(OTPGlobals.CameraBitmask)
        self.ccSphereNode2.setIntoCollideMask(BitMask32.allOff())

        # attach a pusher to the sphere
        self.camPusher2 = CollisionHandlerPusher()
        self.ccPusherTrav.addCollider(self.ccSphereNodePath2, self.camPusher2)
        self.camPusher2.addCollider(self.ccSphereNodePath2, base.camera)

        # Set a special mode on the pusher so that it doesn't get
        # fooled by walls facing away from the toon.
        self.camPusher2.setCenter(self.avatar)

        # create a separate node for the camera's floor-detection ray
        # If we just parented the ray to the camera, it would rotate
        # with the camera and no longer be facing straight down.
        self.camFloorRayNode = self.avatar.attachNewNode("camFloorRayNode")

        # set up camera collision mechanisms

        # Set up the "cameraman" collison ray
        # This is a ray cast from the camera down to detect floor polygons
        self.ccRay = CollisionRay(0.0, 0.0, 0.0, 0.0, 0.0, -1.0)
        self.ccRayNode = CollisionNode('ccRayNode')
        self.ccRayNode.addSolid(self.ccRay)
        self.ccRayNodePath = self.camFloorRayNode.attachNewNode(self.ccRayNode)
        self.ccRayBitMask = OTPGlobals.FloorBitmask
        self.ccRayNode.setFromCollideMask(self.ccRayBitMask)
        self.ccRayNode.setIntoCollideMask(BitMask32.allOff())

        self.ccTravFloor = CollisionTraverser("LocalAvatar.ccTravFloor")

        self.camFloorCollisionQueue = CollisionHandlerQueue()
        self.ccTravFloor.addCollider(self.ccRayNodePath,
                                     self.camFloorCollisionQueue)

        self.ccTravOnFloor = CollisionTraverser("LocalAvatar.ccTravOnFloor")

        # set up another ray to generate on-floor/off-floor events
        self.ccRay2 = CollisionRay(0.0, 0.0, 0.0, 0.0, 0.0, -1.0)
        self.ccRay2Node = CollisionNode('ccRay2Node')
        self.ccRay2Node.addSolid(self.ccRay2)
        self.ccRay2NodePath = self.camFloorRayNode.attachNewNode(
                self.ccRay2Node)
        self.ccRay2BitMask = OTPGlobals.FloorBitmask
        self.ccRay2Node.setFromCollideMask(self.ccRay2BitMask)
        self.ccRay2Node.setIntoCollideMask(BitMask32.allOff())

        # dummy node for CollisionHandlerFloor to move
        self.ccRay2MoveNodePath = hidden.attachNewNode('ccRay2MoveNode')

        # import pdb; pdb.set_trace()
        self.camFloorCollisionBroadcaster = CollisionHandlerFloor()
        self.camFloorCollisionBroadcaster.setInPattern("on-floor")
        self.camFloorCollisionBroadcaster.setOutPattern("off-floor")
        # detect the floor with ccRay2, and move a dummy node
        self.camFloorCollisionBroadcaster.addCollider(
                self.ccRay2NodePath, self.ccRay2MoveNodePath)

    def deleteSmartCameraCollisions(self):
        self.initializedCollisions = False
        del self.ccTrav
        del self.ccLine

        del self.ccLineNode
        self.ccLineNodePath.removeNode()
        del self.ccLineNodePath
        del self.camCollisionQueue

        del self.ccRay
        del self.ccRayNode
        self.ccRayNodePath.removeNode()
        del self.ccRayNodePath

        del self.ccRay2
        del self.ccRay2Node
        self.ccRay2NodePath.removeNode()
        del self.ccRay2NodePath
        self.ccRay2MoveNodePath.removeNode()
        del self.ccRay2MoveNodePath

        del self.ccTravOnFloor
        del self.ccTravFloor
        del self.camFloorCollisionQueue
        del self.camFloorCollisionBroadcaster

        del self.ccSphere
        del self.ccSphereNode
        self.ccSphereNodePath.removeNode()
        del self.ccSphereNodePath

        del self.camPusher
        del self.ccPusherTrav

        del self.ccSphere2
        del self.ccSphereNode2
        self.ccSphereNodePath2.removeNode()
        del self.ccSphereNodePath2

        del self.camPusher2

    def updateSmartCamera(self, task):
        if (not self.__camCollCanMove) and (not self.__cameraHasBeenMoved):
            if self.__lastPosWrtRender == camera.getPos(render):
                if self.__lastHprWrtRender == camera.getHpr(render):
                    return Task.cont

        self.__cameraHasBeenMoved = 0
        self.__lastPosWrtRender = camera.getPos(render)
        self.__lastHprWrtRender = camera.getHpr(render)

        self.__idealCameraObstructed = 0

        # if the smart cam is not disabled, check for view obstructions
        if not self.__disableSmartCam:
            # traverse the smart camera line segment collision tree
            self.ccTrav.traverse(self.__geom)
            # check if we have any collisions
            if self.camCollisionQueue.getNumEntries() > 0:
                # just take the closest one
                self.camCollisionQueue.sortEntries()
                self.handleCameraObstruction(
                        self.camCollisionQueue.getEntry(0))

            # account for the floor
            # optimization 2
            if not self.__onLevelGround:
                self.handleCameraFloorInteraction()

        if not self.__idealCameraObstructed:
            # move the camera a bit
            self.nudgeCamera()

        if not self.__disableSmartCam:
            # tell the pusher to do its thing; keep the camera out of the walls
            self.ccPusherTrav.traverse(self.__geom)
            # make sure the on-floor ray is in the same spot as the camera
            self.putCameraFloorRayOnCamera()

        # now that the camera is in its final pos, do the on-floor traversal
        # (this generates the on-floor event)
        self.ccTravOnFloor.traverse(self.__geom)

        return Task.cont

    def positionCameraWithPusher(self, pos: Vec3F, lookAt: Vec3F):
        """positionCameraWithPusher(self, Point3, Point3)
        Positions the camera at pos, invokes the camera collision
        pusher, and orients the camera towards lookAt
        """
        # load in the target position
        camera.setPos(pos)
        # tell the pusher to do its thing
        self.ccPusherTrav.traverse(self.__geom)
        # look at the target lookAt point
        camera.lookAt(lookAt)

    def nudgeCamera(self):
        """
        Move the camera a little bit closer to its desired
        position as indicated by getCompromiseCameraPos().
        """
        # when the pos or hpr gets within this distance of the target,
        # set it and be done with it
        CLOSE_ENOUGH = 0.01

        # save current camera position
        curCamPos = self.__instantaneousCamPos
        curCamHpr = camera.getHpr()

        # get target camera params
        targetCamPos = self.getCompromiseCameraPos()
        targetCamLookAt = self.getLookAtPoint()

        posDone = 0
        if Vec3(curCamPos - targetCamPos).length() <= CLOSE_ENOUGH:
            camera.setPos(targetCamPos)
            posDone = 1

        ## do this here to get correct HPR
        # targetCamPos.setZ(targetCamPos[2] + self.cameraZOffset)

        ####################
        # we've got a target camera position and look-at point
        # we need to figure out our desired HPR from this info

        ## this is more correct, but slower; it takes the pusher's
        ## effect on the camera HPR into account
        self.positionCameraWithPusher(targetCamPos, targetCamLookAt)

        # this is less correct but quicker; it ignores the influence
        # of the pusher on the camera HPR
        #camera.setPos(targetCamPos)
        #camera.lookAt(targetCamLookAt)
        ####################

        targetCamHpr = camera.getHpr()

        hprDone = 0
        if Vec3(curCamHpr - targetCamHpr).length() <= CLOSE_ENOUGH:
            # hpr was just set above
            hprDone = 1

        # can we bail early?
        if posDone and hprDone:
            return

        # move camera every frame according to this normalized percentage
        # of the distance between its current position and its
        # destination position
        # note: here, 'frame' == 1/30 of a second
        lerpRatio = 0.15

        # account for dt
        lerpRatio = 1 - pow((1 - lerpRatio), globalClock.getDt() * 30.0)

        # calc new instantaneous position
        # (this will be modified if necessary by collision pusher)
        self.__instantaneousCamPos = ((targetCamPos * lerpRatio) +
                                      (curCamPos * (1 - lerpRatio)))

        if self.__disableSmartCam or (not self.__idealCameraObstructed):
            # calc new hpr
            newHpr = (targetCamHpr * lerpRatio) + (curCamHpr * (1 - lerpRatio))
        else:
            # why lerp the hpr at all in smart-cam mode?
            # It was causing a sickening camera-turn
            newHpr = targetCamHpr

        # set new camera params
        camera.setPos(self.__instantaneousCamPos)
        camera.setHpr(newHpr)

    def popCameraToDest(self):
        # get new camera params
        newCamPos = self.getCompromiseCameraPos()
        newCamLookAt = self.getLookAtPoint()

        # set the new camera position with the pusher, so
        # that the HPR gets set correctly and we don't make
        # the player sick
        self.positionCameraWithPusher(newCamPos, newCamLookAt)

        # camera has been 'HOG' moved (Hand Of God)
        # so set the instantaneous position to the new
        # position, taking the pusher into account
        self.__instantaneousCamPos = camera.getPos()

    # camera obstruction detection handler
    def handleCameraObstruction(self, camObstrCollisionEntry: CollisionEntry):
        # calculate distance of obstruction
        collisionPoint = camObstrCollisionEntry.getSurfacePoint(
                self.ccLineNodePath)
        collisionVec = Vec3(collisionPoint - self.ccLine.getPointA())
        distance = collisionVec.length()

        self.__idealCameraObstructed = 1
        self.closestObstructionDistance = distance

        self.popCameraToDest()

    # camera's floor-ray collision handler
    def handleCameraFloorInteraction(self):
        # figure out a Z offset for the camera

        # first, update the position of the ray's parent node
        # if smart cam is disabled, we should not be moving the ray to
        # where the camera is
        assert not self.__disableSmartCam
        self.putCameraFloorRayOnCamera()

        # traverse the smart camera floor ray collision tree
        self.ccTravFloor.traverse(self.__geom)

        # we might be in here just for the sake of the collision traversal.
        # if so, bail out now.
        if self.__onLevelGround:
            return

        # check if we have any collisions
        if self.camFloorCollisionQueue.getNumEntries() == 0:
            return

        # get the closest one
        self.camFloorCollisionQueue.sortEntries()
        camObstrCollisionEntry = self.camFloorCollisionQueue.getEntry(0)

        # the intersection point's Z is the floor's offset from the camera;
        # we would normally negate it to get the camera's offset from the floor
        # This is a negative number
        camHeightFromFloor = camObstrCollisionEntry.getSurfacePoint(
                self.ccRayNodePath)[2]

        # the "target height" is the camera's ideal height,
        # translated to the floor that's currently under it
        self.cameraZOffset = camera.getPos()[2] + camHeightFromFloor

        # Don't move down at all because when you are standing on a crate
        # you do not want the camera to be below your feet looking up at you

        if self.cameraZOffset < -10:
            self.cameraZOffset = 0
        elif self.cameraZOffset < -1:
            self.cameraZOffset = -1

        # if this is the first time we've hit floor, pop right to the
        # destination height
        if self.__floorDetected == 0:
            self.__floorDetected = 1
            self.popCameraToDest()

    def putCameraFloorRayOnAvatar(self):
        self.camFloorRayNode.setPos(self.avatar, 0, 0, 5)

    def putCameraFloorRayOnCamera(self):
        self.camFloorRayNode.setPos(self.ccSphereNodePath, 0, 0, 0)

    def posCamera(self, lerp: bool, time: float):
        if not lerp:
            self.positionCameraWithPusher(self.getCompromiseCameraPos(), self.getLookAtPoint())
        else:
            camPos = self.getCompromiseCameraPos()
            savePos = camera.getPos()
            saveHpr = camera.getHpr()
            self.positionCameraWithPusher(camPos, self.getLookAtPoint())
            x = camPos[0]
            y = camPos[1]
            z = camPos[2]
            destHpr = camera.getHpr()
            h = destHpr[0]
            p = destHpr[1]
            r = destHpr[2]
            camera.setPos(savePos)
            camera.setHpr(saveHpr)
            if self.cameraLerp:
                self.cameraLerp.finish()
                self.cameraLerp = None
            self.cameraLerp = LerpPosHprInterval(camera, time, Point3(x, y, z), Point3(h, p, r), other = self,
                                                 name = 'posCamera')
            self.cameraLerp.start()

    def getVisibilityPoint(self) -> Vec3F:
        return Point3(0.0, 0.0, self.avatar.getHeight())

    def setLookAtPoint(self, la: Vec3F):
        self.__curLookAt = Point3(la)

    def getLookAtPoint(self) -> Vec3F:
        return Point3(self.__curLookAt)

    def setIdealCameraPos(self, pos: Vec3F):
        self.__idealCameraPos = Point3(pos)
        self.updateSmartCameraCollisionLineSegment()

    def getIdealCameraPos(self) -> Vec3F:
        return Point3(self.__idealCameraPos)

    def setCameraPositionByIndex(self, index: int):
        self.notify.debug('switching to camera position %s' % index)
        self.setCameraSettings(self.cameraPositions[index])

    def setCameraPosForPetInteraction(self):
        height = self.avatar.getClampedAvatarHeight()
        point = Point3(height * (7 / 3.0), height * (-7 / 3.0), height)
        self.prevIdealPos = self.getIdealCameraPos()
        self.setIdealCameraPos(point)
        self.posCamera(1, 0.7)

    def unsetCameraPosForPetInteraction(self):
        if hasattr(self, 'prevIdealPos'):
            self.setIdealCameraPos(self.prevIdealPos)
            del self.prevIdealPos
        self.posCamera(1, 0.7)

    def setCameraSettings(self, camSettings: Tuple[Vec3F, Vec3F, Vec3F, Vec3F, bool]):
        self.setIdealCameraPos(camSettings[0])
        self.setLookAtPoint(camSettings[1])
        if self._isPageUp and self._isPageDown or not self._isPageUp and not self._isPageDown:
            self.__cameraHasBeenMoved = 1
            self.setLookAtPoint(camSettings[1])
        elif self._isPageUp:
            self.__cameraHasBeenMoved = 1
            self.setLookAtPoint(camSettings[2])
        elif self._isPageDown:
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
            compromisePos = Point3(compromisePos[0], compromisePos[1],
                                   compromisePos[2] + self.avatar.getHeight() * 0.4 * liftMult)
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

    def recalcCameraSphere(self):
        nearPlaneDist = base.camLens.getNear()
        hFov = base.camLens.getHfov()
        vFov = base.camLens.getVfov()
        hOff = nearPlaneDist * math.tan(deg2Rad(hFov / 2.0))
        vOff = nearPlaneDist * math.tan(deg2Rad(vFov / 2.0))
        camPnts = [Point3(hOff, nearPlaneDist, vOff),
                   Point3(-hOff, nearPlaneDist, vOff),
                   Point3(hOff, nearPlaneDist, -vOff),
                   Point3(-hOff, nearPlaneDist, -vOff),
                   Point3(0.0, 0.0, 0.0)]
        avgPnt = Point3(0.0, 0.0, 0.0)
        for camPnt in camPnts:
            avgPnt = avgPnt + camPnt

        avgPnt = avgPnt / len(camPnts)
        sphereRadius = 0.0
        for camPnt in camPnts:
            dist = Vec3(camPnt - avgPnt).length()
            if dist > sphereRadius:
                sphereRadius = dist

        avgPnt = Point3(avgPnt)
        self.ccSphereNodePath.setPos(avgPnt)
        self.ccSphereNodePath2.setPos(avgPnt)
        self.ccSphere.setRadius(sphereRadius)

    def initCameraPositions(self):
        camHeight = self.avatar.getClampedAvatarHeight()
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
            )]  # + self.auxCameraPositions

    def addCameraPosition(self, camPos: Optional[Tuple[Vec3F, Vec3F, Vec3F, Vec3F, bool]] = None):
        if camPos is None:
            lookAtNP = self.avatar.attachNewNode('lookAt')
            lookAtNP.setPos(base.cam, 0, 1, 0)
            lookAtPos = lookAtNP.getPos()
            camHeight = self.avatar.getClampedAvatarHeight()
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
        self.setCameraPositionByIndex(self.cameraIndex)

    def removeCameraPosition(self):
        if len(self.cameraPositions) > 1:
            camPos = self.cameraPositions[self.cameraIndex]
            if camPos in self.auxCameraPositions:
                self.auxCameraPositions.remove(camPos)
            if camPos in self.cameraPositions:
                self.cameraPositions.remove(camPos)
            self.changePreset(1)

    def pageUp(self):
        if not self.avatar.avatarControlsEnabled:
            return
        self.avatar.wakeUp()
        if not self._isPageUp:
            self._isPageDown = 0
            self._isPageUp = 1
            self.lerpCameraFov(ClientSettings.CameraFOV.get() * 1.34,
                               0.6, blendType = 'easeInOut')
            self.setCameraPositionByIndex(self.cameraIndex)
        else:
            self.clearPageUpDown()

    def pageDown(self):
        if not self.avatar.avatarControlsEnabled:
            return
        self.avatar.wakeUp()
        if not self._isPageDown:
            self._isPageUp = 0
            self._isPageDown = 1
            self.lerpCameraFov(ClientSettings.CameraFOV.get() * 1.34,
                               0.6, blendType = 'easeInOut')
            self.setCameraPositionByIndex(self.cameraIndex)
        else:
            self.clearPageUpDown()

    def clearPageUpDown(self):
        if self._isPageDown or self._isPageUp:
            self.lerpCameraFov(ClientSettings.CameraFOV.get(),
                               0.6, blendType = 'easeInOut')
            self._isPageDown = 0
            self._isPageUp = 0
            self.setCameraPositionByIndex(self.cameraIndex)

    def changePreset(self, direction: int):
        if not self.avatar.avatarControlsEnabled:
            return
        self.avatar.wakeUp()
        self.__cameraHasBeenMoved = 1
        if direction == 1:
            self.cameraIndex += 1
            if self.cameraIndex > len(self.cameraPositions) - 1:
                self.cameraIndex = 0
        else:
            self.cameraIndex -= 1
            if self.cameraIndex < 0:
                self.cameraIndex = len(self.cameraPositions) - 1
        self.setCameraPositionByIndex(self.cameraIndex)
