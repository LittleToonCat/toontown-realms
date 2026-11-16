from panda3d.core import *
from direct.interval.IntervalGlobal import *
from . import ToonHood
from toontown.town import TTTownLoader
from toontown.safezone import TTSafeZoneLoader
from toontown.toonbase.ToontownGlobals import *
from . import SkyUtil
from direct.directnotify import DirectNotifyGlobal

class TTHood(ToonHood.ToonHood):
    notify = DirectNotifyGlobal.directNotify.newCategory('TTHood')

    def __init__(self, parentFSM, doneEvent, dnaStore, hoodId):
        ToonHood.ToonHood.__init__(self, parentFSM, doneEvent, dnaStore, hoodId)
        self.id = ToontownCentral
        self.townLoaderClass = TTTownLoader.TTTownLoader
        self.safeZoneLoaderClass = TTSafeZoneLoader.TTSafeZoneLoader
        self.storageDNAFile = 'phase_4/dna/ttrm_d_strg_ttc.dna'
        self.holidayStorageDNADict = {WINTER_DECORATIONS: ['phase_4/dna/ttrm_d_strg_ttc_winter.dna', 'phase_4/dna/ttrm_d_strg_ttc_sz_winter.dna'],
         WACKY_WINTER_DECORATIONS: ['phase_4/dna/ttrm_d_strg_ttc_winter.dna', 'phase_4/dna/ttrm_d_strg_ttc_sz_winter.dna'],
         HALLOWEEN_PROPS: ['phase_4/dna/ttrm_d_strg_ttc_halloween.dna', 'phase_4/dna/ttrm_d_strg_ttc_sz_halloween.dna'],
         SPOOKY_PROPS: ['phase_4/dna/ttrm_d_strg_ttc_halloween.dna', 'phase_4/dna/ttrm_d_strg_ttc_sz_halloween.dna']}
        self.skyFile = 'phase_3.5/models/props/TT_sky'
        self.spookySkyFile = 'phase_14.5/models/props/halloween-skybox'
        self.winterSkyFile = 'phase_3.5/models/props/BR_sky'
        self.titleColor = (1.0, 0.5, 0.4, 1.0)

    def load(self):
        ToonHood.ToonHood.load(self)
        self.parentFSM.getStateNamed('TTHood').addChild(self.fsm)

    def unload(self):
        self.parentFSM.getStateNamed('TTHood').removeChild(self.fsm)
        ToonHood.ToonHood.unload(self)

    def enter(self, *args):
        ToonHood.ToonHood.enter(self, *args)

    def exit(self):
        ToonHood.ToonHood.exit(self)

    def skyTrack(self, task):
        return SkyUtil.cloudSkyTrack(task)

    def startSky(self):
        self.sky.setTransparency(TransparencyAttrib.MDual, 1)
        self.notify.debug('The sky is: %s' % self.sky)
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
