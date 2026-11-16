from panda3d.core import CollisionSphere, CollisionNode
from direct.interval.IntervalGlobal import Sequence, LerpFunctionInterval, FunctionInterval
from . import SafeZoneLoader
from . import BRBPlayground
from toontown.battle import BattleParticles
from toontown.toonbase.ToontownGlobals import WallBitmask


class BRBSafeZoneLoader(SafeZoneLoader.SafeZoneLoader):
    SnowFadeLerpTime = 2.0

    def __init__(self, hood, parentFSM, doneEvent):
        SafeZoneLoader.SafeZoneLoader.__init__(self, hood, parentFSM, doneEvent)
        self.playgroundClass = BRBPlayground.BRBPlayground
        self.musicFile = 'phase_8/audio/bgm/TB_nbrhood.ogg'
        self.activityMusicFile = 'phase_8/audio/bgm/TB_SZ_activity.ogg'
        self.dnaFile = 'phase_14.5/dna/ttrm_d_ara_brb_sz.dna'
        self.safeZoneStorageDNAFile = 'phase_8/dna/ttrm_d_strg_tbr_sz.dna'

    def load(self):
        SafeZoneLoader.SafeZoneLoader.load(self)
        self.wind1Sound = base.loader.loadSfx('phase_8/audio/sfx/SZ_TB_wind_1.ogg', manager = 'environment')
        self.wind2Sound = base.loader.loadSfx('phase_8/audio/sfx/SZ_TB_wind_2.ogg', manager = 'environment')
        self.wind3Sound = base.loader.loadSfx('phase_8/audio/sfx/SZ_TB_wind_3.ogg', manager = 'environment')
        self.snow = BattleParticles.loadParticleFile('snowdisk.ptf')
        self.snow.setPos(0, 0, 5)
        self.snowRender = self.geom.attachNewNode('snowRender')
        self.snowRender.setDepthWrite(0)
        self.snowRender.setBin('fixed', 1)
        self.snowFade = None
        # Hacky sacky way to setup igloo entry collisions until the igloo model is edited
        cs = CollisionSphere(-110, 60, 0, 20.5)
        cs.setTangible(0)
        colNodePath = self.geom.find('**/igloo/igloo_collisions').attachNewNode(CollisionNode('iglooColl'))
        colNodePath.node().addSolid(cs)
        colNodePath.node().setCollideMask(WallBitmask)
        colNodePath.node().setName('igloo-interior')

    def unload(self):
        del self.wind1Sound
        del self.wind2Sound
        del self.wind3Sound
        del self.snow
        del self.snowRender
        SafeZoneLoader.SafeZoneLoader.unload(self)

    def enter(self, requestStatus):
        SafeZoneLoader.SafeZoneLoader.enter(self, requestStatus)
        self.snow.start(camera, self.snowRender)
        self.accept('enterigloo-interior', self.enterIgloo)
        self.accept('exitigloo-interior', self.exitIgloo)

    def exit(self):
        self.ignore('enterigloo-interior')
        self.ignore('exitigloo-interior')
        self.resetSnowLerp()
        self.snow.cleanup()
        SafeZoneLoader.SafeZoneLoader.exit(self)

    def enterIgloo(self, entry):
        self.fadeOutSnow()

    def exitIgloo(self, entry):
        self.fadeInSnow()

    def resetSnowLerp(self):
        if self.snowFade:
            self.snowFade.finish()
            self.snowFade = None

    def fadeInSnow(self):
        self.resetSnowLerp()
        currentScale = self.snowRender.getColorScale()[3]
        self.snowFade = Sequence(LerpFunctionInterval(self.snowRender.setAlphaScale, fromData=currentScale, toData=1.0,
                                                      duration=self.SnowFadeLerpTime),
                                 FunctionInterval(self.snowRender.clearColorScale))
        self.snowFade.start()

    def fadeOutSnow(self):
        self.resetSnowLerp()
        currentScale = self.snowRender.getColorScale()[3]
        self.snowFade = Sequence(LerpFunctionInterval(self.snowRender.setAlphaScale, fromData=currentScale, toData=0.0,
                                                      duration=self.SnowFadeLerpTime))
        self.snowFade.start()
