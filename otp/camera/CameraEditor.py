import math
from typing import Optional

from direct.showbase.InputStateGlobal import inputState
from direct.showbase.PythonUtil import lerp
from panda3d.core import Vec3, CollisionTraverser, CollisionSegment, CollisionNode, BitMask32, CollisionHandlerQueue, \
    CollisionSphere, CollisionHandlerPusher, Point3, deg2Rad, CollisionEntry, NodePath, LVector3, Vec3F

from otp.camera.CameraBase import CameraBase
from otp.camera.CameraGlobals import *
from otp.otpbase.PythonUtil import bound
from toontown.toonbase import ClientSettings


class CameraEditor(CameraBase):
    CameraOffset: Vec3F = Vec3(0, -40, -45)

    def __init__(self, avatar):
        self.__initializedCollisions = False
        super().__init__(avatar)
        self.__lastPosWrtRender: Optional[Vec3F] = None
        self.__lastHprWrtRender: Optional[Vec3F] = None
        self.__cameraAttachPoint: NodePath = avatar.attachNewNode('__editorOrbitAttachPoint')

    def enterActive(self):
        super().enterActive()
        self.attachCamera()
        self.__acceptHotkeys()
        self.addTask(self.__doCamUpdate, 'camUpdate')
        self.avatar.controlManager.setStrafing(True)

    def enterInactive(self):
        self.removeTask('camUpdate')
        self.__ignoreHotkeys()
        super().enterInactive()
        self.avatar.controlManager.setStrafing(False)

    def attachCamera(self):
        self.__cameraAttachPoint.setPos(0, 0, self.avatar.getHeight())
        self.__cameraAttachPoint.setP(CameraEditor.CameraOffset.z)
        base.camera.reparentTo(self.__cameraAttachPoint)
        base.localAvatar.setCameraFov(60)

        base.camera.setPosHpr(CameraEditor.CameraOffset.y, self.__getScaledDistance(CameraEditor.CameraOffset.y), 0,
                              0, 0, 0)

    def _mouseUpdateTask(self, task):
        """ this task happens every frame the user is holding the mouse down """
        if hasattr(base, 'oobeMode') and base.oobeMode:
            return task.cont

        if self._mouseDelta[0] or self._mouseDelta[1]:
            dx, dy = self._mouseDelta

            sensitivity = ClientSettings.CameraSensitivity.get() / 4
            self.__cameraAttachPoint.setH(self.__cameraAttachPoint, -dx * sensitivity)
            pitch = bound(self.__cameraAttachPoint.getP() + -dy * sensitivity, EDITOR_MIN_PITCH, EDITOR_MAX_PITCH)
            self.__cameraAttachPoint.setP(pitch)
            self.__cameraAttachPoint.setR(render, 0)

        # set the toons' rotation to the cameras rotation
        camPointH = self.__cameraAttachPoint.getH(render)
        if abs(camPointH - self.avatar.getH(render)) > 0.01:
            self.avatar.setH(render, camPointH)
            # then set the camera's relative rotation back to 0
            self.__cameraAttachPoint.setH(0)
        return task.cont

    def startMouseControl(self):
        super().startMouseControl()

    def stopMouseControl(self):
        super().stopMouseControl()

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

    def adjustZoom(self, offset: int):
        self.__setZoom(offset)

    def __setZoom(self, offset: int):
        """ Adjust the zoom level """
        y = CameraEditor.CameraOffset.y
        y = bound(y + offset, EDITOR_MIN_ZOOM, EDITOR_MAX_ZOOM)
        CameraEditor.CameraOffset.setY(y)
        z = lerp(self.avatar.getHeight(), self.avatar.getHeight(), (-14 - y) / -12)
        self.__cameraAttachPoint.setZ(z)

    def __doCamUpdate(self, task):
        """ update camera """
        if hasattr(base, 'oobeMode') and base.oobeMode:
           return task.cont
        if self.__lastPosWrtRender == base.camera.getPos(render) and self.__lastHprWrtRender == base.camera.getHpr(
                render):
            return task.cont
        base.camera.setPos(CameraEditor.CameraOffset.x, self.__getScaledDistance(CameraEditor.CameraOffset.y), 0)
        base.camera.setHpr(Vec3(0))

        self.__lastPosWrtRender, self.__lastPosWrtRender = base.camera.getPos(render), base.camera.getHpr(render)

        return task.cont

    @staticmethod
    def isAvatarMoving() -> bool:
        if inputState.isSet('forward') or inputState.isSet('reverse') or inputState.isSet(
                'turnRight') or inputState.isSet('turnLeft') or inputState.isSet('slideLeft') or inputState.isSet(
                'slideRight'):
            return True
        else:
            return False

    def __getScaledDistance(self, distance: float) -> float:
        camHeight = self.avatar.getClampedAvatarHeight()
        heightScaleFactor = camHeight * 0.3333333333
        return distance * heightScaleFactor
