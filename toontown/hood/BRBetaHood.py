from panda3d.core import *
from . import ToonHood
from toontown.town import BRBTownLoader
from toontown.safezone import BRBSafeZoneLoader
from toontown.toonbase.ToontownGlobals import *

class BRBetaHood(ToonHood.ToonHood):

    def __init__(self, parentFSM, doneEvent, dnaStore, hoodId):
        ToonHood.ToonHood.__init__(self, parentFSM, doneEvent, dnaStore, hoodId)
        self.id = TheBrrrghBeta
        self.townLoaderClass = BRBTownLoader.BRBTownLoader
        self.safeZoneLoaderClass = BRBSafeZoneLoader.BRBSafeZoneLoader
        self.storageDNAFile = 'phase_8/dna/ttrm_d_strg_tbr.dna'
        self.skyFile = 'phase_3.5/models/props/BR_sky'
        self.titleColor = (0.3, 0.6, 1.0, 1.0)

    def load(self):
        ToonHood.ToonHood.load(self)
        self.parentFSM.getStateNamed('BRBetaHood').addChild(self.fsm)

    def unload(self):
        self.parentFSM.getStateNamed('BRBetaHood').removeChild(self.fsm)
        ToonHood.ToonHood.unload(self)

    def enter(self, *args):
        ToonHood.ToonHood.enter(self, *args)

    def exit(self):
        ToonHood.ToonHood.exit(self)
