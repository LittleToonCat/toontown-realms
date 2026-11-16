from panda3d.core import *
from . import ToonHood
from toontown.safezone import GSSafeZoneLoader
from toontown.toonbase.ToontownGlobals import *
from toontown.racing import DistributedVehicle
from . import SkyUtil

class GSHood(ToonHood.ToonHood):

    def __init__(self, parentFSM, doneEvent, dnaStore, hoodId):
        ToonHood.ToonHood.__init__(self, parentFSM, doneEvent, dnaStore, hoodId)
        self.id = GoofySpeedway
        self.safeZoneLoaderClass = GSSafeZoneLoader.GSSafeZoneLoader
        self.storageDNAFile = 'phase_6/dna/ttrm_d_strg_gsw.dna'
        self.holidayStorageDNADict = {HALLOWEEN_PROPS: ['phase_6/dna/ttrm_d_strg_gsw_halloween.dna'],
         SPOOKY_PROPS: ['phase_6/dna/ttrm_d_strg_gsw_halloween.dna'],
         CRASHED_LEADERBOARD: ['phase_6/dna/ttrm_d_strg_gsw_leaderboard.dna']}
        self.skyFile = 'phase_3.5/models/props/TT_sky'
        self.spookySkyFile = 'phase_14.5/models/props/halloween-skybox'
        self.titleColor = (1.0, 0.5, 0.4, 1.0)

    def load(self):
        ToonHood.ToonHood.load(self)
        self.parentFSM.getStateNamed('GSHood').addChild(self.fsm)

    def unload(self):
        self.parentFSM.getStateNamed('GSHood').removeChild(self.fsm)
        ToonHood.ToonHood.unload(self)

    def enter(self, *args):
        ToonHood.ToonHood.enter(self, *args)
        base.localAvatar.chatMgr.chatInputSpeedChat.addKartRacingMenu()
        base.camLens.setNearFar(SpeedwayCameraNear, SpeedwayCameraFar)

    def exit(self):
        base.camLens.setNearFar(DefaultCameraNear, DefaultCameraFar)
        base.localAvatar.chatMgr.chatInputSpeedChat.removeKartRacingMenu()
        ToonHood.ToonHood.exit(self)

    def skyTrack(self, task):
        return SkyUtil.cloudSkyTrack(task)

    def startSky(self):
        if not self.sky.getTag('sky') == 'Regular':
            self.endHolidaySky()
        SkyUtil.startCloudSky(self)
        messenger.send('resumeFireworks')

    def startSpookySky(self):
        if hasattr(self, 'sky') and self.sky:
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
