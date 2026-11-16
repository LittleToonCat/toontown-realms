from panda3d.core import *
from direct.task.Task import Task
from . import ToonHood
from toontown.battle import BattleParticles
from toontown.town import BRTownLoader
from toontown.safezone import BRSafeZoneLoader
from toontown.toonbase.ToontownGlobals import *
from toontown.toonbase import EnvironmentManager
from . import SkyUtil
import random


class BRHood(ToonHood.ToonHood):

    def __init__(self, parentFSM, doneEvent, dnaStore, hoodId):
        ToonHood.ToonHood.__init__(self, parentFSM, doneEvent, dnaStore, hoodId)
        self.id = TheBrrrgh
        self.townLoaderClass = BRTownLoader.BRTownLoader
        self.safeZoneLoaderClass = BRSafeZoneLoader.BRSafeZoneLoader
        self.storageDNAFile = 'phase_8/dna/ttrm_d_strg_tbr.dna'
        self.holidayStorageDNADict = {WINTER_DECORATIONS: ['phase_8/dna/ttrm_d_strg_tbr_winter.dna'],
         WACKY_WINTER_DECORATIONS: ['phase_8/dna/ttrm_d_strg_tbr_winter.dna'],
         HALLOWEEN_PROPS: ['phase_8/dna/ttrm_d_strg_tbr_halloween.dna'],
         SPOOKY_PROPS: ['phase_8/dna/ttrm_d_strg_tbr_halloween.dna']}
        self.skyFile = 'phase_3.5/models/props/BR_sky'
        self.spookySkyFile = 'phase_14.5/models/props/halloween-skybox'
        self.fogColor = Vec4(0.8, 0.8, 0.8, 1)
        self.titleColor = (0.3, 0.6, 1.0, 1.0)

    def load(self):
        ToonHood.ToonHood.load(self)
        self.wind1Sound = base.loader.loadSfx('phase_8/audio/sfx/SZ_TB_wind_1.ogg', manager = 'environment')
        self.wind2Sound = base.loader.loadSfx('phase_8/audio/sfx/SZ_TB_wind_2.ogg', manager = 'environment')
        self.wind3Sound = base.loader.loadSfx('phase_8/audio/sfx/SZ_TB_wind_3.ogg', manager = 'environment')
        if base.cr.experimentalFeatures:
            snow = BattleParticles.loadParticleFile('ttoff_p_efx_launch_tbrSnow')
            snow.setPos(0, 40, 10)
        else:
            snow = BattleParticles.loadParticleFile('snowdisk.ptf')
            snow.setPos(0, 0, 5)
        EnvironmentManager.setDefaultParticle(snow)
        EnvironmentManager.setActiveParticle(snow)
        snowRender = render.attachNewNode('snowRender')
        snowRender.setDepthWrite(0)
        snowRender.setBin('fixed', 1)
        EnvironmentManager.setDefaultParticleRender(snowRender)
        EnvironmentManager.setActiveParticleRender(snowRender)
        fog = Fog('TBRFog')
        fog.setColor(self.fogColor)
        fog.setLinearRange(0, 400)
        EnvironmentManager.setDefaultFog(fog)
        EnvironmentManager.setActiveFog(fog)
        self.parentFSM.getStateNamed('BRHood').addChild(self.fsm)

    def unload(self):
        EnvironmentManager.unloadEnvironment()
        del self.wind1Sound
        del self.wind2Sound
        del self.wind3Sound
        self.parentFSM.getStateNamed('BRHood').removeChild(self.fsm)
        ToonHood.ToonHood.unload(self)

    def skyTrackNoClouds(self, task):
        return SkyUtil.noCloudSkyTrack(task)

    def startAmbience(self):
        self.nextWindTime = 0
        taskMgr.add(self.__windTask, 'br-wind')
        EnvironmentManager.enableEnvironment()

    def stopAmbience(self):
        taskMgr.remove('br-wind')
        EnvironmentManager.disableEnvironment()

    def startSky(self):
        self.sky.setTransparency(TransparencyAttrib.MDual, 1)
        self.notify.debug('The sky is: %s' % self.sky)
        if not self.sky.getTag('sky') == 'Regular':
            self.endSpookySky()
        SkyUtil.startNoCloudSky(self)

    def __windTask(self, task):
        now = globalClock.getFrameTime()
        if now < self.nextWindTime:
            return Task.cont
        randNum = random.random()
        wind = int(randNum * 100) % 3 + 1
        if wind == 1:
            base.playSfx(self.wind1Sound)
        elif wind == 2:
            base.playSfx(self.wind2Sound)
        elif wind == 3:
            base.playSfx(self.wind3Sound)
        self.nextWindTime = now + randNum * 8.0
        return Task.cont