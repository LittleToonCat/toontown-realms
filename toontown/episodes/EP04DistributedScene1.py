import random

from direct.actor import Actor
from direct.directutil import Mopath
from direct.gui.DirectLabel import DirectLabel
from direct.interval.IntervalGlobal import *
from direct.showbase import Audio3DManager

from panda3d.toontown import *

from panda3d.core import *

from toontown.episodes import EpisodeLocalizer
from otp.otpbase.PythonUtil import weightedChoice, fitDestAngle2Src
from toontown.avatar import ToontownAvatarUtils
from toontown.episodes import DistributedEpisodeZone, EpisodeLocalizer
from toontown.episodes import EpisodeConfig
from toontown.episodes.EpisodeGlobals import *
from toontown.hood import SkyUtil
from toontown.hood.PetShopFishAnimatedProp import PetShopFishAnimatedProp
from toontown.parties import PartyGlobals
from toontown.toontowngui.ServerTimeGui import ServerTimeGui
from toontown.toon.ToonDNA import ToonDNA
from toontown.toonbase import TTLocalizer, ToontownGlobals

from toontown.makeatoon import NameGenerator


class EP04DistributedScene1(DistributedEpisodeZone.DistributedEpisodeZone):

    def __init__(self, cr):
        DistributedEpisodeZone.DistributedEpisodeZone.__init__(self, cr)

        self.toons = []
        self.episodeZoneId = EpisodeConfig.EP04_INTRO

    def disable(self):
        DistributedEpisodeZone.DistributedEpisodeZone.disable(self)
        self.sky.removeNode()
        taskMgr.remove('skyTrack')
        for toon in self.toons:
            toon.delete()

    def generateGeom(self):
        base.loader.beginBulkLoad('episode', TTLocalizer.HeadingToHood % {
            'to': TTLocalizer.ToontownCentral[0],
            'hood': TTLocalizer.ToontownCentral[2]
        }, 14, 1, TTLocalizer.TIP_OFFLINE_MODE)
        loader.loadDNAFile(base.cr.playGame.hood.dnaStore, 'phase_4/dna/ttrm_d_strg_ttc.dna')
        loader.loadDNAFile(base.cr.playGame.hood.dnaStore, 'phase_4/dna/ttrm_d_strg_ttc_sz.dna')
        loader.loadDNAFile(base.cr.playGame.hood.dnaStore, 'phase_5/dna/ttrm_d_strg_ttc_town.dna')

        node = loader.loadDNAFile(base.cr.playGame.hood.dnaStore, 'phase_14/dna/ttrm_d_ara_ttc_sz_ep04.dna')
        if node.getNumParents() == 1:
            self.geom = NodePath(node.getParent(0))
            self.geom.reparentTo(render)
        else:
            self.geom = render.attachNewNode(node)
        base.loader.tick()

        self.geom.flattenMedium()
        base.loader.tick()

        # Hide the black parts in the doors
        doorHoles = self.geom.findAllMatches('**/doorFrameHole*')
        for hole in doorHoles:
            hole.removeNode()

        base.loader.tick()

        toOakStreetTunnel = self.geom.find('**/prop_sostunnel_DNARoot')
        linkSphere = toOakStreetTunnel.find('**/tunnel_trigger')

        cnode = linkSphere.node()
        cnode.setName('to_str402')
        cnode.setCollideMask(ToontownGlobals.WallBitmask | ToontownGlobals.GhostBitmask)
        self.accept('enterto_str402', self.enterTunnel)
        base.loader.tick()

        self.sky = loader.loadModel('phase_3.5/models/props/TT_sky')
        self.sky.reparentTo(self.geom)

        self.startCloudSky()

        base.loader.tick()
        self.toon.setPosHpr(Point3(-60.61, -10.10, 1.23), Point3(188.11, 0.00, 0.00))

        self.sounds = {
        }  # type: dict[str, AudioSound]

        base.loader.tick()

        gsg = base.win.getGsg()
        if gsg:
            self.geom.prepareScene(gsg)

        base.loader.tick()
        base.loader.endBulkLoad('episode')

    def startCloudSky(self):
        return SkyUtil.startCloudSky(self)

    def skyTrack(self, task):
        return SkyUtil.cloudSkyTrack(task)

    def generateMovie(self):
        self.generateStory()
        self.story.hide()

        self.movie = Sequence(
                Func(self.lockToon),

                # mput movie here

                # EXIT
                Func(self.toon.show),
                Func(self.toon.setPosHpr, self.toon, 0, 0, 0, 0, 0, 0),
                Func(self.releaseToon),
                Func(self.toon.enableAvatarControls),

                name = 'ep401_movie_main'
        )

        # Func(self.teleportToZone, self.zoneConnections[0])))

    def enterTunnel(self, collEntry):
        tunnelOrigin = self.geom.find('**/prop_sostunnel_DNARoot').find('**/tunnel_origin')
        x, y, z = tunnelOrigin.getPos(render)
        h = tunnelOrigin.getH(render)
        # create a temporary tunnel origin node
        tunnelOrigin = self.geom.attachNewNode('tunnelOrigin')
        tunnelOrigin.setPosHpr(x, y, z, h, 0, 0)

        self.toon.animFSM.request("run")

        tracks = Parallel()

        # Pull the camera back
        base.camera.wrtReparentTo(render)
        startPos = base.camera.getPos(tunnelOrigin)
        startHpr = base.camera.getHpr(tunnelOrigin)
        camLerpDur = 1.
        reducedCamH = fitDestAngle2Src(startHpr[0], 180)
        tracks.append(
                LerpPosHprInterval(base.camera, camLerpDur,
                                   pos = Point3(0, 20, 12),
                                   hpr = Point3(reducedCamH, -20, 0),
                                   startPos = startPos,
                                   startHpr = startHpr,
                                   other = tunnelOrigin, blendType = "easeInOut",
                                   name = "tunnelOutLerpCamPos"),
        )
        startX, startY = self.toon.getX(tunnelOrigin) * 0.95, self.toon.getY(tunnelOrigin)
        toonTrack = self.toon.getTunnelOutToonTrack(startX, startY, tunnelOrigin)
        tracks.append(toonTrack)
        seq = Sequence(
                Func(self.lockToon),
                tracks,
                Func(self.teleportToZone, self.zoneConnections[0])
        )

        seq.start()


        #self.teleportToZone(self.zoneConnections[0])
