from panda3d.core import NodePath

from otp.camera.CameraBase import CameraBase
from otp.camera.CameraGlobals import *
from otp.otpbase.PythonUtil import bound
from toontown.toonbase import ClientSettings


class CameraShoulder(CameraBase):

    def __init__(self, avatar):
        super().__init__(avatar)
        self.__cameraAttachPoint: NodePath = avatar.attachNewNode('__shoulderAttachPoint')

    def enterActive(self):
        super().enterActive()
        self.attachCamera()
        self.addTask(self.__doCamUpdate, 'camUpdate')

    def enterInactive(self):
        self.removeTask('camUpdate')
        super().enterInactive()

    def attachCamera(self):
        base.camera.reparentTo(self.__cameraAttachPoint)
        self.__cameraAttachPoint.setZ(self.avatar.getHeight())
        base.camera.setPosHpr(self.__getScaledDistance(1), self.__getScaledDistance(-4), 0, 0, 0, 0)

        base.localAvatar.setCameraFov(ClientSettings.CameraFOV.get()*1.5)

    def _mouseUpdateTask(self, task):
        """ this task happens every frame the user is holding the mouse down """
        if hasattr(base, 'oobeMode') and base.oobeMode:
            return task.cont

        if self._mouseDelta[0] or self._mouseDelta[1]:
            dx, dy = self._mouseDelta

            sensitivity = ClientSettings.CameraSensitivity.get() / 4
            self.avatar.setH(self.avatar, -dx * sensitivity)
            base.camera.setH(0)
            self.__cameraAttachPoint.setP(bound(self.__cameraAttachPoint.getP() + -dy * sensitivity,
                                                ORBIT_MIN_PITCH, ORBIT_MAX_PITCH))
            base.camera.setR(render, 0)

        return task.cont

    def startMouseControl(self):
        super().startMouseControl()
        self.avatar.controlManager.setStrafing(True)

    def stopMouseControl(self):
        super().stopMouseControl()
        self.avatar.controlManager.setStrafing(False)

    def __doCamUpdate(self, task):
        """ update camera """
        if hasattr(base, 'oobeMode') and base.oobeMode:
           return task.cont
        base.camera.setPos(self.__getScaledDistance(1), self.__getScaledDistance(-4), 0)
        return task.cont

    def __getScaledDistance(self, distance: float) -> float:
        camHeight = self.avatar.getClampedAvatarHeight()
        heightScaleFactor = camHeight * 0.3333333333
        return distance * heightScaleFactor
