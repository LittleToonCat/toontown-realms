import math
from typing import Optional

from direct.showbase.InputStateGlobal import inputState
from direct.showbase.PythonUtil import lerp
from panda3d.core import Vec3, CollisionTraverser, CollisionSegment, CollisionNode, BitMask32, CollisionHandlerQueue, \
    CollisionSphere, CollisionHandlerPusher, Point3, deg2Rad, CollisionEntry, NodePath, Vec3F

from otp.camera.CameraBase import CameraBase
from otp.camera.CameraGlobals import *
from otp.otpbase import OTPGlobals
from otp.otpbase.PythonUtil import bound
from toontown.toonbase import ClientSettings
from toontown.sandbox.DistributedPropGenerator import DistributedPropGenerator


class CameraOrbital(CameraBase):
    CameraOffset = Vec3(0, -9, 0)

    def __init__(self, avatar):
        self.__initializedCollisions = False
        super().__init__(avatar)
        # Optimization: Don't keep calculating collisions if the camera hasnt moved at all
        self.__lastPosWrtRender: Optional[Vec3F] = None
        self.__lastHprWrtRender: Optional[Vec3F] = None
        self.__cameraAttachPoint: NodePath = avatar.attachNewNode('__orbitAttachPoint')

    def enterActive(self):
        super().enterActive()
        if not self.__initializedCollisions:
            self.__initializeCollisions()
            self.avatar.cTrav.addCollider(self.__ccSphereNodePath, self.__camPusher)

        self.__recalcCameraSphere()
        self.attachCamera()
        self.__acceptHotkeys()
        self.addTask(self.__doCollisionCheck, 'collisionCheck')

    def enterInactive(self):
        self.removeTask('collisionCheck')
        self.__ignoreHotkeys()

        if self.__initializedCollisions:
            self.avatar.cTrav.removeCollider(self.__ccSphereNodePath)
            self.__deleteCollisions()
        super().enterInactive()

    def attachCamera(self):
        self.__cameraAttachPoint.setPos(0, 0, self.avatar.getHeight())
        base.camera.reparentTo(self.__cameraAttachPoint)

        base.camera.setPosHpr(CameraOrbital.CameraOffset.x, self.__getScaledDistance(CameraOrbital.CameraOffset.y), 0,
                              0, 0, 0)

        base.localAvatar.setCameraFov(ClientSettings.CameraFOV.get())

    def _mouseUpdateTask(self, task):
        """ this task happens every frame the user is holding the mouse down """
        if hasattr(base, 'oobeMode') and base.oobeMode:
            return task.cont

        isMoving = self.isAvatarMoving() or base.localAvatar.isPresentingPie or DistributedPropGenerator.editorOpen
        if self._mouseDelta[0] or self._mouseDelta[1]:
            dx, dy = self._mouseDelta

            sensitivity = ClientSettings.CameraSensitivity.get() / 4
            self.__cameraAttachPoint.setH(self.__cameraAttachPoint, -dx * sensitivity)
            pitch = bound(self.__cameraAttachPoint.getP() + -dy * sensitivity, ORBIT_MIN_PITCH, ORBIT_MAX_PITCH)
            self.__cameraAttachPoint.setP(pitch)
            self.__cameraAttachPoint.setR(render, 0)

        # If we are moving, set the toons' rotation to the cameras rotation
        if isMoving:
            camPointH = self.__cameraAttachPoint.getH(render)
            if abs(camPointH - self.avatar.getH(render)) > 0.01:
                self.avatar.setH(render, camPointH)
                # then set the camera's relative rotation back to 0
                self.__cameraAttachPoint.setH(0)
        return task.cont

    def __handleObstruction(self, node: CollisionEntry):
        """ handle an object in the way """
        collisionPoint = node.getSurfacePoint(self.__cameraAttachPoint)

        base.camera.setPos(collisionPoint + node.getSurfaceNormal(self.__ccLineNodePath))

        # maybe???? makes the camera alwys looka t the toon but it can look weird
        # base.camera.lookAt(self.__cameraAttachPoint)
        # base.camera.setR(render, 0)

    def startMouseControl(self):
        super().startMouseControl()
        self.avatar.controlManager.setStrafing(True)

    def stopMouseControl(self):
        super().stopMouseControl()
        self.avatar.controlManager.setStrafing(False)

    def __acceptHotkeys(self):
        self.accept('wheel_up', self.__handleWheelUp)
        self.accept('page_up', self.__handleWheelUp)
        self.accept('wheel_down', self.__handleWheelDown)
        self.accept('page_down', self.__handleWheelDown)

    def __ignoreHotkeys(self):
        self.ignore('wheel_up')
        self.ignore('wheel_down')
        self.ignore('page_up')
        self.ignore('page_down')

    def __handleWheelUp(self):
        self.__setZoom(1)

    def __handleWheelDown(self):
        self.__setZoom(-1)

    def __setZoom(self, offset: int):
        """ Adjust the zoom level """
        y = CameraOrbital.CameraOffset.y
        y = bound(y + offset, ORBIT_MIN_ZOOM, ORBIT_MAX_ZOOM)
        CameraOrbital.CameraOffset.setY(y)
        z = lerp(self.avatar.getHeight(), self.avatar.getHeight(), (-14 - y) / -12)
        self.__cameraAttachPoint.setZ(z)

    def __doCollisionCheck(self, task):
        """ Check if the camera is obstructed and handle it """
        if hasattr(base, 'oobeMode') and base.oobeMode:
            return task.cont
        if self.__lastPosWrtRender == base.camera.getPos(render) and self.__lastHprWrtRender == base.camera.getHpr(
                render):
            return task.cont
        base.camera.setPos(CameraOrbital.CameraOffset.x, self.__getScaledDistance(CameraOrbital.CameraOffset.y), 0)
        base.camera.setHpr(Vec3(0))
        self.__ccLine.setPointA(Vec3(0, 0, self.avatar.getHeight()))
        self.__ccLine.setPointB(base.camera.getPos(self.avatar))

        self.__lastPosWrtRender, self.__lastPosWrtRender = base.camera.getPos(render), base.camera.getHpr(render)

        self.__ccTrav.traverse(render)

        if self.__camCollisionQueue.getNumEntries() > 0:
            self.__camCollisionQueue.sortEntries()
            self.__handleObstruction(self.__camCollisionQueue.getEntry(0))

        return task.cont

    @staticmethod
    def isAvatarMoving() -> bool:
        if inputState.isSet('forward') or inputState.isSet('reverse') or inputState.isSet(
                'turnRight') or inputState.isSet('turnLeft') or inputState.isSet('slideLeft') or inputState.isSet(
                'slideRight'):
            return True
        else:
            return False

    def __initializeCollisions(self):
        self.__initializedCollisions = True

        # setup camera collision traverser
        # we need this because normal collisions get handled just before
        # rendering. using the normal collision mechanisms would introduce
        # one frame of lag in the smart camera, allowing the camera to pop
        # through walls momentarily.
        self.__ccTrav = CollisionTraverser('CameraOrbital.ccTrav')

        # Set up the camera obstruction test line segment
        # This is a line segment from the visibility point to the ideal
        # camera location
        self.__ccLine = CollisionSegment(0.0, 0.0, 0.0, 0, -20, 0.0)
        self.__ccLineNode = CollisionNode('CameraOrbital.ccLineNode')
        self.__ccLineNode.addSolid(self.__ccLine)
        self.__ccLineNodePath = self.avatar.attachNewNode(self.__ccLineNode)
        # self.__ccLineNodePath.show()
        self.__ccLineNode.setFromCollideMask(OTPGlobals.CameraBitmask |
                                             OTPGlobals.CameraTransparentBitmask |
                                             OTPGlobals.FloorBitmask)
        self.__ccLineNode.setIntoCollideMask(BitMask32.allOff())

        self.__camCollisionQueue = CollisionHandlerQueue()

        self.__ccTrav.addCollider(self.__ccLineNodePath, self.__camCollisionQueue)

        # sphere to keep it away from walls
        # sphere radius n shit will be calculated later based on fov n stuff
        self.__ccSphere = CollisionSphere(0, 0, 0, 1)
        self.__ccSphereNode = CollisionNode('CameraOrbital.ccSphereNode')
        self.__ccSphereNode.addSolid(self.__ccSphere)
        self.__ccSphereNodePath = base.camera.attachNewNode(self.__ccSphereNode)
        # self.__ccSphereNodePath.show()
        self.__ccSphereNode.setFromCollideMask(OTPGlobals.CameraBitmask |
                                               OTPGlobals.CameraTransparentBitmask |
                                               OTPGlobals.FloorBitmask)
        self.__ccSphereNode.setIntoCollideMask(BitMask32.allOff())

        self.__camPusher = CollisionHandlerPusher()
        self.__camPusher.addCollider(self.__ccSphereNodePath, base.camera)
        self.__camPusher.addCollider(self.__ccLineNodePath, base.camera)

        self.__camPusher.setCenter(self.avatar)

        self.__ccPusherTrav = CollisionTraverser("CameraOrbital.ccPusherTrav")
        ##self.__ccPusherTrav.showCollisions(render)

    def __deleteCollisions(self):
        self.__initializedCollisions = False
        del self.__ccTrav
        del self.__ccLine

        del self.__ccLineNode
        self.__ccLineNodePath.removeNode()
        del self.__ccLineNodePath
        del self.__camCollisionQueue

        del self.__ccSphere
        del self.__ccSphereNode
        self.__ccSphereNodePath.removeNode()
        del self.__ccSphereNodePath

        del self.__camPusher
        del self.__ccPusherTrav

    def __recalcCameraSphere(self):
        """ this will adjust the smart camera for new FOV/near plane settings"""
        # get the near-plane params
        nearPlaneDist = base.camLens.getNear()
        hFov = base.camLens.getHfov()
        vFov = base.camLens.getVfov()

        hOff = nearPlaneDist * math.tan(deg2Rad(hFov / 2.))
        vOff = nearPlaneDist * math.tan(deg2Rad(vFov / 2.))

        # average the points together to get the sphere center
        camPnts = [Point3(hOff, nearPlaneDist, vOff),
                   Point3(-hOff, nearPlaneDist, vOff),
                   Point3(hOff, nearPlaneDist, -vOff),
                   Point3(-hOff, nearPlaneDist, -vOff),
                   Point3(0.0, 0.0, 0.0)]

        avgPnt = Point3(0.0, 0.0, 0.0)
        for camPnt in camPnts:
            avgPnt = avgPnt + camPnt
        avgPnt = avgPnt / len(camPnts)

        # calculate a minimum bounding sphere
        sphereRadius = 0.0
        for camPnt in camPnts:
            dist = Vec3(camPnt - avgPnt).length()
            if dist > sphereRadius:
                sphereRadius = dist

        # set the new sphere params
        avgPnt = Point3(avgPnt)
        self.__ccSphereNodePath.setPos(avgPnt)
        self.__ccSphere.setRadius(sphereRadius)

    def __getScaledDistance(self, distance: float) -> float:
        camHeight = self.avatar.getClampedAvatarHeight()
        heightScaleFactor = camHeight * 1./3.
        return distance * heightScaleFactor
