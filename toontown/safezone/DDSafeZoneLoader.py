from panda3d.core import *
from typing import Optional

from otp.otpbase import OTPRender
from . import SafeZoneLoader
from . import DDPlayground
from toontown.toonbase import ToontownGlobals, ClientSettings
from .Reflection import Reflection
from ..toonbase.ToontownSettings import REFLECTION_RESOLUTIONS


class DDSafeZoneLoader(SafeZoneLoader.SafeZoneLoader):

    def __init__(self, hood, parentFSM, doneEvent):
        SafeZoneLoader.SafeZoneLoader.__init__(self, hood, parentFSM, doneEvent)
        self.playgroundClass = DDPlayground.DDPlayground
        self.musicFile = 'phase_6/audio/bgm/DD_nbrhood.ogg'
        self.activityMusicFile = 'phase_6/audio/bgm/DD_SZ_activity.ogg'
        if base.cr.newsManager.isHolidayRunning(ToontownGlobals.HALLOWEEN_PROPS):
            self.dnaFile = 'phase_6/dna/ttrm_d_ara_dod_sz_halloween.dna'
            self.musicFile = 'phase_6/audio/bgm/ttoff_s_ara_dod_nbrhood_halloween.ogg'
        else:
            self.dnaFile = 'phase_6/dna/ttrm_d_ara_dod_sz.dna'
        self.safeZoneStorageDNAFile = 'phase_6/dna/ttrm_d_strg_dod_sz.dna'
        self.reflection: Optional[Reflection] = None

    def load(self):
        SafeZoneLoader.SafeZoneLoader.load(self)
        self.seagullSound = base.loader.loadSfx('phase_6/audio/sfx/SZ_DD_Seagull.ogg', manager = 'environment')
        self.underwaterSound = base.loader.loadSfx('phase_4/audio/sfx/AV_ambient_water.ogg', manager = 'environment')
        self.swimSound = base.loader.loadSfx('phase_4/audio/sfx/AV_swim_single_stroke.ogg', manager = 'environment')
        self.submergeSound = base.loader.loadSfx('phase_5.5/audio/sfx/AV_jump_in_water.ogg', manager = 'environment')

        water = self.geom.find('**/water')
        water.setTransparency(1)
        water.setColor(1, 1, 1, 0.8)

        reflRes: int = REFLECTION_RESOLUTIONS[ClientSettings.ReflectionQuality.get()]
        if reflRes:
            self.reflection = Reflection('reflection', reflRes, reflRes, base.render, Plane(Vec3(0, 0, 1), Vec3(0, 0, 1.65)))
            #self.reflection.createCard('fixed', 20)
            self.reflection.enable(True)
            self.__setupReflection()

        if __debug__:
            self.accept('r', self.__setupReflection)

        self.boat = self.geom.find('**/donalds_boat')
        if self.boat.isEmpty():
            self.notify.error('Boat not found')
        else:
            wheel = self.boat.find('**/wheel')
            if wheel.isEmpty():
                self.notify.warning('Wheel not found')
            else:
                wheel.hide()
            self.boat.stash()
        self.dockSound = base.loader.loadSfx('phase_6/audio/sfx/SZ_DD_dockcreak.ogg', manager = 'environment')
        self.foghornSound = base.loader.loadSfx('phase_5/audio/sfx/SZ_DD_foghorn.ogg', manager = 'environment')
        self.bellSound = base.loader.loadSfx('phase_6/audio/sfx/SZ_DD_shipbell.ogg', manager = 'environment')
        self.waterSound = base.loader.loadSfx('phase_6/audio/sfx/SZ_DD_waterlap.ogg', manager = 'environment')

    def __setupReflection(self):
        water: NodePath = self.geom.find('**/water')
        water.setShader(Shader.load(Shader.SLGLSL,
                                    fragment = 'phase_3/shaders/ttrm_sha_ara_gen_water.frag',
                                    vertex = 'phase_3/shaders/ttrm_sha_ara_gen_water.vert'
                                    ))
        water.setShaderInput('refl_texture', self.reflection.reflectionTexture)
        OTPRender.renderReflection(True, self.geom, 'geom_refl', None)
        OTPRender.renderReflection(False, water, 'geom_refl', None)

    def unload(self):
        SafeZoneLoader.SafeZoneLoader.unload(self)
        if __debug__:
            self.ignore('r')
        if self.reflection:
            self.reflection.enable(False)
            self.reflection.delete()
            self.reflection = None
        del self.seagullSound
        del self.underwaterSound
        del self.swimSound
        del self.dockSound
        del self.foghornSound
        del self.bellSound
        del self.waterSound
        del self.submergeSound
        del self.boat

    def enter(self, requestStatus):
        SafeZoneLoader.SafeZoneLoader.enter(self, requestStatus)

    def exit(self):
        SafeZoneLoader.SafeZoneLoader.exit(self)
