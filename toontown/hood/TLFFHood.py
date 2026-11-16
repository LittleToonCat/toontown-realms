from panda3d.core import Fog, TransparencyAttrib, CompassEffect, Vec4

from otp.otpbase.OTPGlobals import DefaultCameraNear, DefaultCameraFar
from . import ToonHood
from toontown.town import TLFFTownLoader
from . import SkyUtil
from . import ToonHood
from ..safezone import TLFFSafeZoneLoader
from ..toonbase.ToontownGlobals import ToonLandFunnyFarm, SpeedwayCameraNear, SpeedwayCameraFar


class TLFFHood(ToonHood.ToonHood):

    def __init__(self, parentFSM, doneEvent, dnaStore, hoodId):
        super().__init__(parentFSM, doneEvent, dnaStore, hoodId)
        self.id = ToonLandFunnyFarm
        self.townLoaderClass = TLFFTownLoader.TLFFTownLoader
        self.safeZoneLoaderClass = TLFFSafeZoneLoader.TLFFSafeZoneLoader
        self.storageDNAFile = 'phase_14.5/dna/ttrm_d_strg_tnl.dna'
        self.skyFile = 'phase_3.5/models/props/TT_sky'
        self.spookySkyFile = 'phase_14.5/models/props/halloween-skybox'
        self.titleColor = (0.55, 1.0, 0.55, 1.0)

    def load(self):
        super().load()
        self.parentFSM.getStateNamed('TLFFHood').addChild(self.fsm)
        self.fog = Fog('OZFog')

    def unload(self):
        self.parentFSM.getStateNamed('TLFFHood').removeChild(self.fsm)
        super().unload()

    def enter(self, *args):
        super().enter(*args)
        base.camLens.setNearFar(SpeedwayCameraNear, SpeedwayCameraFar)

    def exit(self):
        super().exit()
        base.camLens.setNearFar(DefaultCameraNear, DefaultCameraFar)

    def skyTrack(self, task):
        return SkyUtil.cloudSkyTrack(task)

    def startSky(self):
        if not self.sky.getTag('sky') == 'Regular':
            self.endHolidaySky()
        SkyUtil.startCloudSky(self)
        messenger.send('resumeFireworks')

    def startSpookySky(self):
        if self.sky:
            self.stopSky()
        self.sky = loader.loadModel(self.spookySkyFile)
        self.sky.setTag('sky', 'Halloween')
        self.sky.setScale(1.0)
        self.sky.setDepthTest(0)
        self.sky.setDepthWrite(0)
        self.sky.setColor(0.5, 0.5, 0.5, 1)
        self.sky.setBin('background', 100)
        self.sky.setFogOff()
        self.sky.reparentTo(camera)
        self.sky.setTransparency(TransparencyAttrib.MDual, 1)
        fadeIn = self.sky.colorScaleInterval(1.5, Vec4(1, 1, 1, 1), startColorScale=Vec4(1, 1, 1, 0.25), blendType='easeInOut')
        fadeIn.start()
        self.sky.setZ(0.0)
        self.sky.setHpr(0.0, 0.0, 0.0)
        ce = CompassEffect.make(NodePath(), CompassEffect.PRot | CompassEffect.PZ)
        self.sky.node().setEffect(ce)
        messenger.send('resumeFireworks')
