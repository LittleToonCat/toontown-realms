# EPISODE 3 : STORM SELLBOT
import random

from direct.interval.IntervalGlobal import *

from panda3d.toontown import *

from panda3d.core import *

from otp.otpbase.PythonUtil import weightedChoice
from toontown.avatar import ToontownAvatarUtils
from toontown.episodes import DistributedEpisodeZone
from toontown.episodes import EpisodeConfig
from toontown.toon.ToonDNA import ToonDNA
from toontown.toonbase import TTLocalizer, ToontownGlobals


class EP03DistributedOakStreet(DistributedEpisodeZone.DistributedEpisodeZone):

    def __init__(self, cr):
        DistributedEpisodeZone.DistributedEpisodeZone.__init__(self, cr)
        self.episodeZoneId = EpisodeConfig.EP03_OAK_STREET

    def disable(self):
        DistributedEpisodeZone.DistributedEpisodeZone.disable(self)
        for cog in self.cogs:
            cog.delete()

    def generateGeom(self):
        base.loader.beginBulkLoad('episode', TTLocalizer.HeadingToHood % {
            'to': TTLocalizer.GlobalStreetNames[5300][0],
            'hood': TTLocalizer.GlobalStreetNames[5300][2]
        }, 6, 1, TTLocalizer.TIP_OFFLINE_MODE)
        # == Load Street ==
        loader.loadDNAFile(base.cr.playGame.hood.dnaStore, 'phase_8/dna/ttrm_d_strg_dga.dna')
        base.loader.tick()
        loader.loadDNAFile(base.cr.playGame.hood.dnaStore, 'phase_8/dna/ttrm_d_strg_dga_town.dna')
        base.loader.tick()
        loader.loadDNAFile(base.cr.playGame.hood.dnaStore, 'phase_14/dna/ttrm_d_strg_dga_ep03.dna')
        base.loader.tick()
        # We use a slightly modified dna file to allow us to make tiny changes to allow for some better camera angles
        node = loader.loadDNAFile(base.cr.playGame.hood.dnaStore,
                                  'phase_14/dna/ttrm_d_ara_dga_5300_ep03.dna')
        base.loader.tick()
        if node.getNumParents() == 1:
            self.geom = NodePath(node.getParent(0))
            self.geom.reparentTo(render)
        else:
            self.geom = render.attachNewNode(node)

        # Hide the black parts in the doors
        doorHoles = self.geom.findAllMatches('**/doorFrameHole*')
        for hole in doorHoles:
            hole.removeNode()

        # == Details ==
        # TODO Activate Interactive Props

        # Sky
        self.sky = loader.loadModel('phase_3.5/models/props/TT_sky')
        self.sky.reparentTo(self.geom)
        base.loader.tick()

        self.cogs = []
        for i in range(8):
            cog = ToontownAvatarUtils.createCog(
                    random.choice(ToontownGlobals.GreenEffectMassFlyCogs[0]), anim = 'walk', do = self
            )
            cog.addActive()
            base.loader.tick()
            self.cogs.append(cog)

        self.geom.flattenMedium()
        gsg = base.win.getGsg()
        if gsg:
            self.geom.prepareScene(gsg)

        base.loader.endBulkLoad('episode')

    def generateMovie(self):
        """
        DOODLE RUN OUT OF TUNNEL
        CAMERA (-24.5, -19.8, 0.4), (127.0, 5.0, 0.0)
        TOON (-98, -41, -0.47), (270, 0, 0) to (-73, -41, -0.47), (270, 0, 0)
        ===
        DOODLE RUN BY #1
        CAMERA (-37.85, -52.53, 0.43)
        TOON (-32.01, -41.66, -0.47) (268, 0, 0) TO (-9.5, -41.66, -0.47) (268, 0, 0)
        ===
        DOODLE RUN INTO TREE INTERSECTION
        CAMERA (-96.19, 121.62, 5.46) (-54.49, 1.43, 0)
        TOON (-8.43, 135.05, -0.47) (61.24, 0, 0) TO (-30.33, 147.06, -0.47) (61.24, 0, 0)
        ===
        DOODLE RUN OUT OF TREE INTERSECTION
        TOON (-30.33, 147.06, -0.47) (104.20, 0, 0) TO (-67.04, 137.77, -0.47) (104.20, 0, 0)
        ===
        DOODLE RUN PAST HQ
        CAMERA REVEALS 'TO SELLBOT HQ' SIGN (THIS SIGN IS A NEW PROP WITH SOURCE PANDORA TEXTURES FOR CLARITY)
        TOON startPos = (-105.48, 106.61, -0.47), startHpr = (150.98, 0, 0) pos = (-144.95, 95.31, -0.47)
        CAMERA startPos = (-197.19, 94.64, 8.81) startHpr = (-86.1, -2.4, 0) pos = (-197.44, 95.52, 4.32)
        ===
        DOODLE APPROACHES SBHQ TUNNEL
        CAMERA (-294.08, 239.40, 0.81) (24.68, 13.08, 0)
        TOON (-311.19, 238.15, -0.47) (0, 0, 0) TO (-311.19, 305.30, -0.47)
        ===
        DOODLE ENTER TUNNEL
        CAMERA (-310, 210, 25) (0, -9, 0) TO (-310, 235, 20) (0, -9, 0)
        TOON (-310.5, 309.0, -0.47) (0, 0, 0) TO (-310.5, 278, -0.47)
        """
        episodeStatus = 0  # base.cr.episodeManager.getEpisodeStatus(self.episodeZoneId)
        if not episodeStatus:
            self.movie = Sequence(
                    Func(self.lockToon),
                    Func(base.camera.reparentTo, render),
                    Func(self.toon.pet.loop, 'run'),

                    # DOODLE RUNS OUT OF TUNNEL
                    Parallel(
                            Func(base.camera.setPosHpr, (-24.5, -19.8, 0.4), (127.0, 5.0, 0.0)),
                            LerpPosHprInterval(self.toon, 2,
                                               startPos = (-98, -41, -0.47), startHpr = (270, 0, 0),
                                               pos = (-73, -41, -0.47), hpr = (270, 0, 0),
                                               ),
                            LerpPosHprInterval(self.cogs[0], 2,
                                               startPos = (-70, -45, -0.5), startHpr = (270, 0, 0),
                                               pos = (-60, -45, -0.5), hpr = (270, 0, 0))
                    ),

                    # DOODLE RUN BY 1
                    Parallel(
                            Func(base.camera.setPosHpr, (-30.31, -27.29, 0.43), (-145, 3, 0.0)),
                            LerpPosHprInterval(self.toon, 1.32,
                                               startPos = (-32.01, -41.66, -0.47), startHpr = (268, 0, 0),
                                               pos = (-9.5, -41.66, -0.47), hpr = (268, 0, 0),
                                               ),
                            LerpPosHprInterval(self.cogs[1], 1.32,
                                               startPos = (-30, -45, -0.5), startHpr = (270, 0, 0),
                                               pos = (-25, -45, -0.5), hpr = (270, 0, 0))
                    ),

                    Func(base.camera.setPosHpr, (-96.19, 121.62, 5.46), (-54.49, -1.43, 0)),

                    Parallel(
                            LerpPosHprInterval(base.camera, 3,
                                               startPos = (-96.19, 121.62, 5.46), startHpr = (-54.49, -1.43, 0),
                                               pos = (-87.42, 124.86, 3.88), hpr = (-60, -1.43, 0)),
                            Sequence(
                                    # DOODLE RUN INTO TREE INTERSECTION
                                    LerpPosHprInterval(self.toon, 1.5,
                                                       startPos = (-8.43, 135.05, -0.47), startHpr = (61.24, 0, 0),
                                                       pos = (-30.33, 147.06, -0.47), hpr = (61.24, 0, 0),
                                                       ),
                                    # DOODLE RUN OUT OF TREE INTERSECTION
                                    LerpPosHprInterval(self.toon, 1.5,
                                                       startPos = (-30.33, 147.06, -0.47), startHpr = (104.20, 0, 0),
                                                       pos = (-67.04, 137.77, -0.47), hpr = (104.20, 0, 0),
                                                       )
                            ),
                            LerpPosHprInterval(self.cogs[2], 3,
                                               startPos = (-17.42, 169.03, -0.5), startHpr = (45, 0, 0),
                                               pos = (-31.35, 183.01, -0.5), hpr = (45, 0, 0))

                    ),
                    # DOODLE RUN BY HQ
                    Parallel(
                            LerpPosHprInterval(base.camera, 1.6, blendType = 'easeOut',
                                               startPos = (-197.19, 94.64, 5.21), startHpr = (-86.1, -2.4, 0),
                                               pos = (-197.44, 95.52, 3.8), hpr = (-86.1, -2.4, 0)),
                            LerpPosHprInterval(self.toon, 2.3,
                                               startPos = (-105.48, 106.61, -0.47), startHpr = (105.98, 0, 0),
                                               pos = (-144.95, 95.31, -0.47), hpr = (105.98, 0, 0),
                                               ),
                    ),

                    # DOODLE APPROACH TUNNEL
                    Func(base.camera.setPosHpr, (-294.08, 239.40, 0.81), (24.68, 13.08, 0)),
                    LerpPosHprInterval(self.toon, 3.4,
                                       startPos = (-311.19, 238.15, -0.47), startHpr = (0, 0, 0),
                                       pos = (-311.19, 305.30, -0.47), hpr = (0, 0, 0),
                                       ),
                    # DOODLE ENTER TUNNEL
                    Parallel(
                            LerpPosHprInterval(base.camera, 1.6,
                                               startPos = (-310, 210, 25), startHpr = (0, -9, 0),
                                               pos = (-310, 235, 20), hpr = (0, -9, 0)),
                            LerpPosHprInterval(self.toon, 1.6,
                                               startPos = (-310, 305.0, -0.47), startHpr = (0, 0, 0),
                                               pos = (-310, 335, -0.47), hpr = (0, 0, 0),
                                               ),
                            Func(base.transitions.irisOut, 1.6)
                    ),
                    Func(self.releaseToon),
                    Func(self.toon.enableAvatarControls),
                    Func(self.teleportToZone, self.zoneConnections[0]),

                    name = 'ep302_movie_main'
            )
        else:
            self.movie = Sequence()
