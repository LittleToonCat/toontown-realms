from panda3d.core import Plane, Vec3, Shader, NodePath

from otp.otpbase import OTPRender
from toontown.toonbase import ToontownGlobals, ClientSettings
from toontown.effects.Fireflies import Fireflies
from typing import Optional

from . import Street
from ..hood import ZoneUtil
from ..safezone.Reflection import Reflection
from ..toonbase.ToontownSettings import REFLECTION_RESOLUTIONS


class DLStreet(Street.Street):

    def __init__(self, loader, parentFSM, doneEvent):
        Street.Street.__init__(self, loader, parentFSM, doneEvent)
        self.fireflies: Optional[Fireflies] = None
        self.reflection: Optional[Reflection] = None

    def enter(self, *args):
        Street.Street.enter(self, *args)

        self.fireflies = Fireflies()
        self.fireflies.reparentTo(base.localAvatar)
        self.fireflies.startLoop()

        branchZone = ZoneUtil.getBranchZone(self.zoneId)
        # Toons must be able to see the buildings in Dreamy Drive Outcove
        if branchZone in (ToontownGlobals.DreamyDriveOutcove, ToontownGlobals.DreamyDrive):
            base.camLens.setNearFar(ToontownGlobals.DreamyDriveOutcoveCameraNear,
                                    ToontownGlobals.DreamyDriveOutcoveCameraFar)
            self.loader.hood.sky.setScale(3.5)
        if branchZone == ToontownGlobals.DreamyDriveOutcove:
            messenger.send('enterSafeZone')
            reflRes: int = REFLECTION_RESOLUTIONS[ClientSettings.ReflectionQuality.get()]
            if reflRes:
                self.reflection = Reflection('reflection', reflRes, reflRes, base.render, Plane(Vec3(0, 0, 1), Vec3(0, 0, -.2)))
                #self.reflection.createCard('fixed', 20)
                self.reflection.enable(True)
                self.__setupReflection()

    def exit(self, *args):
        if self.fireflies is not None:
            self.fireflies.destroy()
        if self.reflection:
            self.reflection.enable(False)
            self.reflection.delete()
            self.reflection = None
        branchZone = ZoneUtil.getBranchZone(self.zoneId)
        if branchZone in (ToontownGlobals.DreamyDriveOutcove, ToontownGlobals.DreamyDrive):
            base.camLens.setNearFar(ToontownGlobals.DefaultCameraNear, ToontownGlobals.DefaultCameraFar)
            self.loader.hood.sky.setScale(1.0)
        if branchZone == ToontownGlobals.DreamyDriveOutcove:
            messenger.send('exitSafeZone')
        Street.Street.exit(self, *args)

    def __setupReflection(self):
        water: NodePath = self.loader.geom.find('**/Water')
        water.setShader(Shader.load(Shader.SLGLSL,
                                    fragment = 'phase_8/shaders/ttrm_sha_ara_ddlo_water.frag',
                                    vertex = 'phase_3/shaders/ttrm_sha_ara_gen_water.vert'
                                    ))
        water.setShaderInput('refl_texture', self.reflection.reflectionTexture)
        OTPRender.renderReflection(True, self.loader.geom, 'geom_refl', None)
        OTPRender.renderReflection(False, water, 'geom_refl', None)