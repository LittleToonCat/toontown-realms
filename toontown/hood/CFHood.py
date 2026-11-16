from panda3d.core import *

from toontown.hood import SkyUtil
from toontown.safezone import CFSafeZoneLoader
from toontown.toonbase import ToontownGlobals
from toontown.town import CFTownLoader

from . import ToonHood


class CFHood(ToonHood.ToonHood):

    def __init__(self, parentFSM, doneEvent, dnaStore, hoodId):
        ToonHood.ToonHood.__init__(self, parentFSM, doneEvent, dnaStore, hoodId)

        # Zone ID
        self.id = ToontownGlobals.ToontownSkies

        # Loader classes
        self.townLoaderClass = CFTownLoader.CFTownLoader
        self.safeZoneLoaderClass = CFSafeZoneLoader.CFSafeZoneLoader

        # DNA paths
        self.storageDNAFile = 'phase_14.5/dna/ttrm_d_strg_crf.dna'

        # Skybox path
        self.skyFile = 'phase_3.5/models/props/TT_sky'

        # Title color
        self.titleColor = (1.0, 0.5, 0.4, 1.0)

    def load(self):
        ToonHood.ToonHood.load(self)
        self.parentFSM.getStateNamed('CFHood').addChild(self.fsm)

        # The Fields skybox is larger than usual
        self.sky.setScale(25.0)

    def unload(self):
        self.parentFSM.getStateNamed('CFHood').removeChild(self.fsm)
        ToonHood.ToonHood.unload(self)

    def enter(self, *args):
        ToonHood.ToonHood.enter(self, *args)

    def exit(self):
        ToonHood.ToonHood.exit(self)

    def skyTrack(self, task):
        return SkyUtil.cloudSkyTrack(task)
