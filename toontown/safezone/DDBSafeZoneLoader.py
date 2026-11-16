from panda3d.core import *
from . import SafeZoneLoader
from . import DDBPlayground
from direct.fsm import State
from toontown.char import CharDNA
from toontown.char import Char
from toontown.toonbase import ToontownGlobals

class DDBSafeZoneLoader(SafeZoneLoader.SafeZoneLoader):

    def __init__(self, hood, parentFSM, doneEvent):
        SafeZoneLoader.SafeZoneLoader.__init__(self, hood, parentFSM, doneEvent)
        self.playgroundClass = DDBPlayground.DDBPlayground
        self.musicFile = 'phase_6/audio/bgm/DD_nbrhood.ogg'
        self.activityMusicFile = 'phase_6/audio/bgm/DD_SZ_activity.ogg'
        self.dnaFile = 'phase_14.5/dna/ttrm_d_ara_ddb_sz.dna'
        self.safeZoneStorageDNAFile = 'phase_6/dna/ttrm_d_strg_dod_sz.dna'

    def load(self):
        SafeZoneLoader.SafeZoneLoader.load(self)
        self.seagullSound = base.loader.loadSfx('phase_6/audio/sfx/SZ_DD_Seagull.ogg', manager = 'environment')
        self.underwaterSound = base.loader.loadSfx('phase_4/audio/sfx/AV_ambient_water.ogg', manager = 'environment')
        self.swimSound = base.loader.loadSfx('phase_4/audio/sfx/AV_swim_single_stroke.ogg', manager = 'environment')
        self.submergeSound = base.loader.loadSfx('phase_5.5/audio/sfx/AV_jump_in_water.ogg', manager = 'environment')
        water = self.geom.find('**/water')
        water.setTransparency(1)
        water.setColor(1, 1, 1, 0.8)
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

    def unload(self):
        SafeZoneLoader.SafeZoneLoader.unload(self)
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
