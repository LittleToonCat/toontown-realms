from panda3d.core import *
from . import ToonHood
from toontown.town import MMBTownLoader
from toontown.safezone import MMBSafeZoneLoader
from toontown.toonbase.ToontownGlobals import *

class MMBetaHood(ToonHood.ToonHood):

    def __init__(self, parentFSM, doneEvent, dnaStore, hoodId):
        ToonHood.ToonHood.__init__(self, parentFSM, doneEvent, dnaStore, hoodId)
        self.id = MinniesMelodylandBeta
        self.townLoaderClass = MMBTownLoader.MMBTownLoader
        self.safeZoneLoaderClass = MMBSafeZoneLoader.MMBSafeZoneLoader
        self.storageDNAFile = 'phase_6/dna/ttrm_d_strg_mml.dna'
        self.skyFile = 'phase_6/models/props/MM_sky'
        self.titleColor = (1.0, 0.5, 0.5, 1.0)

    def load(self):
        ToonHood.ToonHood.load(self)
        self.parentFSM.getStateNamed('MMBetaHood').addChild(self.fsm)
        if self.sky.getTag('sky') == 'Regular':
            self.sky.setDepthTest(0)
            self.sky.setDepthWrite(0)
            self.sky.setBin('background', 100)
            clouds = self.sky.find('**/clouds')
            clouds.setBin('background', 101)

    def unload(self):
        self.parentFSM.getStateNamed('MMBetaHood').removeChild(self.fsm)
        ToonHood.ToonHood.unload(self)

    def enter(self, *args):
        ToonHood.ToonHood.enter(self, *args)

    def exit(self):
        ToonHood.ToonHood.exit(self)
