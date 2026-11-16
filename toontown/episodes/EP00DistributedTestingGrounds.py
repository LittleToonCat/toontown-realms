from typing import Optional

from direct.interval.IntervalGlobal import *
from direct.showbase.BufferViewer import BufferViewer

from panda3d.toontown import *

from panda3d.core import *

from otp.otpbase import OTPRender
from toontown.episodes import DistributedEpisodeZone
from toontown.episodes import EpisodeConfig
from toontown.safezone.Reflection import Reflection
from toontown.toonbase import ClientSettings
from toontown.toonbase.ToontownSettings import REFLECTION_RESOLUTIONS


class EP00DistributedTestingGrounds(DistributedEpisodeZone.DistributedEpisodeZone):

    def __init__(self, cr):
        DistributedEpisodeZone.DistributedEpisodeZone.__init__(self, cr)
        self.episodeZoneId = EpisodeConfig.EP00_TESTING_GROUNDS
        self.reflection: Optional[Reflection] = None
        self.floorTest: Optional[NodePath] = None

    def disable(self):
        DistributedEpisodeZone.DistributedEpisodeZone.disable(self)

    def generateGeom(self):
        loader.loadDNAFile(base.cr.playGame.hood.dnaStore, 'phase_4/dna/ttrm_d_strg.dna')
        loader.loadDNAFile(base.cr.playGame.hood.dnaStore, 'phase_6/dna/ttrm_d_strg_mml.dna')
        loader.loadDNAFile(base.cr.playGame.hood.dnaStore, 'phase_6/dna/ttrm_d_strg_mml_sz.dna')
        loader.loadDNAFile(base.cr.playGame.hood.dnaStore, 'phase_6/dna/ttrm_d_strg_mml_town.dna')

        node = loader.loadDNAFile(base.cr.playGame.hood.dnaStore, 'phase_3/dna/ttoff_d_launch_backgroundMM.dna')
        if node.getNumParents() == 1:
            self.geom = NodePath(node.getParent(0))
            self.geom.reparentTo(render)
        else:
            self.geom = render.attachNewNode(node)
        #self.geom.flattenMedium()
        gsg = base.win.getGsg()
        if gsg:
            self.geom.prepareScene(gsg)
        self.sky = loader.loadModel('phase_3.5/models/props/TT_sky')
        self.sky.reparentTo(self.geom)

        base.bufferViewer.enable(True)

        reflRes: int = REFLECTION_RESOLUTIONS[ClientSettings.ReflectionQuality.get()]
        if reflRes:
            self.reflection = Reflection('reflection', reflRes, reflRes, base.render, Plane(Vec3(0, 0, 1), Vec3(0, 0, 0.0)))
            # self.reflection.createCard('fixed', 20)
            self.reflection.enable(True)
        self.floorTest: NodePath = base.loader.loadModel('phase_14.5/models/props/ttrm_m_debug_floorMaterialTest')
        self.floorTest.reparentTo(self.geom)
        self.floorTest.setPos(25, -30, 0)
        self.floorTest.setScale(2)
        self.reloadShader()
        self.accept('r', self.reloadShader)
        self.accept('end', self.toggleBuffer)
        self.toon.setChatAbsolute("r to reload shaders\n\nend to toggle buffer viewer", CFSpeech | CFTimeout)

    def reloadShader(self):
        floor1: NodePath = self.floorTest.find('**/floor001')
        floor1.setTexture(base.loader.loadTexture('phase_4/maps/water3.png'), 1)
        floor1.clearShader()
        floor1.setShader(Shader.load(Shader.SLGLSL,
                                     fragment = 'phase_3/shaders/ttrm_sha_ara_gen_water.frag',
                                     vertex = 'phase_3/shaders/ttrm_sha_ara_gen_water.vert'
                                     ))
        floor1.setShaderInput('refl_texture', self.reflection.reflectionTexture)

        floor2: NodePath = self.floorTest.find('**/floor002')
        floor2.setTexture(base.loader.loadTexture('phase_11/maps/LB_Marble4.png'), 1)
        floor2.clearShader()
        floor2.setShader(Shader.load(Shader.SLGLSL,
                                     fragment = 'phase_11/shaders/ttrm_sha_ara_lbhq_floor.frag',
                                     vertex = 'phase_11/shaders/ttrm_sha_ara_lbhq_floor.vert'
                                     ))
        floor2.setShaderInput('refl_texture', self.reflection.reflectionTexture)
        OTPRender.renderReflection(True, floor1, 'water', None)

        for geom in self.geom.findAllMatches("**/**street_**_street*"):
            geom.setShader(Shader.load(Shader.SLGLSL,
                                     fragment = 'phase_3/shaders/ttrm_sha_ara_gen_streetmodule.frag',
                                     vertex = 'phase_3/shaders/ttrm_sha_ara_gen_streetmodule.vert'
                                     ))

    def toggleBuffer(self):
        bfvr: BufferViewer = base.bufferViewer
        bfvr.toggleEnable()

    def generateMovie(self):
        self.movie = Sequence()
