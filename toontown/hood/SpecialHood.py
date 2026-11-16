from panda3d.core import *

from toontown.distributed import HoodMgr
from toontown.hood import SkyUtil
from toontown.safezone import SPSafeZoneLoader
from toontown.toonbase import ToontownGlobals
from toontown.town import SPTownLoader

from . import ToonHood


class SpecialHood(ToonHood.ToonHood):

    def __init__(self, parentFSM, doneEvent, dnaStore, hoodId):
        ToonHood.ToonHood.__init__(self, parentFSM, doneEvent, dnaStore, hoodId)

        # Zone ID
        self.id = ToontownGlobals.ToontownOutskirts

        # Loader classes
        self.townLoaderClass = SPTownLoader.SPTownLoader
        self.safeZoneLoaderClass = SPSafeZoneLoader.SPSafeZoneLoader

        # DNA paths
        self.storageDNAFile = 'phase_4/dna/ttrm_d_strg_ttc.dna'
        self.holidayStorageDNADict = {ToontownGlobals.WINTER_DECORATIONS: ['phase_4/dna/ttrm_d_strg_ttc_winter.dna',
                                                                           'phase_4/dna/ttrm_d_strg_ttc_sz_winter.dna'],
                                      ToontownGlobals.WACKY_WINTER_DECORATIONS: ['phase_4/dna/ttrm_d_strg_ttc_winter.dna',
                                                                                 'phase_4/dna/ttrm_d_strg_ttc_sz_winter.dna'],
                                      ToontownGlobals.HALLOWEEN_PROPS: ['phase_4/dna/ttrm_d_strg_ttc_halloween.dna'],
                                      ToontownGlobals.SPOOKY_PROPS: ['phase_4/dna/ttrm_d_strg_ttc_halloween.dna']}

        # Skybox path
        self.skyFile = ToontownGlobals.Playground2Skybox.get('tt')

        # Title color
        self.titleColor = {ToontownGlobals.ToontownOutskirts: ToontownGlobals.Playground2Title.get('tt'),
                           ToontownGlobals.TutorialTerrace: ToontownGlobals.Playground2Title.get('tt'),
                           ToontownGlobals.ToontownSkies: (1.0, 0.5, 0.4, 1.0),
                           ToontownGlobals.CogtownCentral: (0.5, 0.5, 0.5, 1.0),
                           ToontownGlobals.SellbotHQFuture: (0.5, 0.5, 0.5, 1.0)}

    def load(self):
        ToonHood.ToonHood.load(self)
        self.parentFSM.getStateNamed('SpecialHood').addChild(self.fsm)

        # The Toontown Outskirts skybox is larger than usual
        self.sky.setScale(3.0)

    def unload(self):
        self.parentFSM.getStateNamed('SpecialHood').removeChild(self.fsm)
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

    def startSpookySky(self):
        if hasattr(self, 'sky') and self.sky:
            self.stopSky()

        self.sky = loader.loadModel('phase_14.5/models/props/halloween-skybox')
        self.sky.setTag('sky', 'Halloween')
        self.sky.setScale(3.0)
        self.sky.setDepthTest(0)
        self.sky.setDepthWrite(0)
        self.sky.setColor(0.5, 0.5, 0.5, 1)
        self.sky.setBin('background', 100)

        self.sky.reparentTo(self.loader.geom)

        self.sky.setTransparency(TransparencyAttrib.MDual, 1)

        fadeIn = self.sky.colorScaleInterval(1.5, Vec4(1, 1, 1, 1), startColorScale=Vec4(1, 1, 1, 0.25), blendType='easeInOut')
        fadeIn.start()

        self.sky.setZ(0.0)
        self.sky.setHpr(0.0, 0.0, 0.0)

        ce = CompassEffect.make(NodePath(), CompassEffect.PRot | CompassEffect.PZ)
        self.sky.node().setEffect(ce)

        messenger.send('resumeFireworks')

    def startWinterSky(self):
        # We don't want to make a duplicate sky if one already exists
        if hasattr(self, 'sky') and self.sky:
            self.stopSky()

        # Load the sky up and apply some attributes to it
        self.sky = loader.loadModel('phase_3.5/models/props/BR_sky')
        self.sky.setTag('sky', 'Winter')
        self.sky.setScale(3.0)
        self.sky.setDepthTest(0)
        self.sky.setDepthWrite(0)
        self.sky.setColor(0.9, 0.9, 0.9, 1)
        self.sky.setBin('background', 100)

        # The sky in the Outskirts is a bit unique, because we want it to be properly affected by fog during the Winter
        # But if it's reparented to the camera, well, it just doesn't get the effects of the fog
        # So in this one instance, we reparent the sky to the geom
        self.sky.reparentTo(self.loader.geom)

        # Make the sky transparent
        self.sky.setTransparency(TransparencyAttrib.MDual, 1)

        # An interval that slowly fades the sky in
        fadeIn = self.sky.colorScaleInterval(1.5, Vec4(1, 1, 1, 1), startColorScale=Vec4(1, 1, 1, 0.25), blendType='easeInOut')
        fadeIn.start()

        # Center the sky
        self.sky.setZ(0.0)
        self.sky.setHpr(0.0, 0.0, 0.0)

        # Compass effect
        ce = CompassEffect.make(NodePath(), CompassEffect.PRot | CompassEffect.PZ)
        self.sky.node().setEffect(ce)

        # Resume the fireworks once the sky has been properly loaded
        messenger.send('resumeFireworks')

    def endHolidaySky(self):
        self.skyFile = ToontownGlobals.Playground2Skybox.get('tt')

        ToonHood.ToonHood.endHolidaySky(self)

    def setWhiteFog(self):
        if base.wantFog:
            self.fog = Fog('SPFog')
            self.fog.setColor(Vec4(0.8, 0.8, 0.8, 1))
            self.fog.setLinearRange(0.0, 1300.0)
            render.clearFog()
            render.setFog(self.fog)
            self.sky.clearFog()
            self.sky.setFog(self.fog)

    def setNoFog(self):
        if base.wantFog and hasattr(self, 'fog') and self.fog:
            render.clearFog()
            self.sky.clearFog()
            self.fog = None
