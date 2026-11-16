from direct.interval.IntervalGlobal import *

from panda3d.toontown import *

from panda3d.core import *

from . import EpisodeLocalizer
from toontown.episodes import DistributedEpisodeZone
from toontown.episodes import EpisodeConfig
from toontown.toonbase import ToontownGlobals


class EP01DistributedOakStreet(DistributedEpisodeZone.DistributedEpisodeZone):

    def __init__(self, cr):
        DistributedEpisodeZone.DistributedEpisodeZone.__init__(self, cr)
        self.episodeZoneId = EpisodeConfig.EP01_OAK_STREET

    def disable(self):
        DistributedEpisodeZone.DistributedEpisodeZone.disable(self)

        self.sunchaser.removeNode()
        del self.sunchaser

        if self.nametag:
            self.nametag.unmanage(base.marginManager)
            self.nametagNP.removeNode()
        del self.nametag
        del self.nametagNP

    def generateGeom(self):
        loader.loadDNAFile(base.cr.playGame.hood.dnaStore, 'phase_8/dna/ttrm_d_strg_dga.dna')
        # storage_town.dna commented out until further notice
        # loader.loadDNAFile(base.cr.playGame.hood.dnaStore, 'phase_5/dna/storage_town.dna')  # this is *EXTREMELY* important for gyro's lab doors to work properly! DO NOT REMOVE!!!
        loader.loadDNAFile(base.cr.playGame.hood.dnaStore, 'phase_8/dna/ttrm_d_strg_dga_town.dna')
        # TODO: figure out if the below logic is really needed, or if the old logic works fine
        node = loader.loadDNAFile(base.cr.playGame.hood.dnaStore, 'phase_14.5/dna/ttrm_d_ara_dgb_22100.dna')
        if node.getNumParents() == 1:
            self.geom = NodePath(node.getParent(0))
            self.geom.reparentTo(render)
        else:
            self.geom = render.attachNewNode(node)
        self.geom.flattenMedium()
        gsg = base.win.getGsg()
        if gsg:
            self.geom.prepareScene(gsg)

        self.geom.setColorScale(0.65, 0.65, 0.65, 1.0)

        nightSky = loader.loadModel('phase_8/models/props/DL_sky')
        nightSky.setZ(-450)
        nightSky.setScale(5.0)
        nightSky.reparentTo(self.geom)

        barrierNode = CollisionNode('barrierNode')
        barrierNode.addSolid(CollisionBox(Point3(-222.77, 215.28, 0), 0.5, 30, 10))
        self.geom.attachNewNode(barrierNode)

        self.sunchaser = loader.loadModel('phase_14/models/props/sunchaser')
        self.sunchaser.setTransparency(1)
        self.sunchaser.setPosHpr(-311.87, 211.72, 50.0, 180.0, 0.0, 0.0)
        self.sunchaser.setScale(5.0)
        self.sunchaser.reparentTo(render)

        dropShadow = loader.loadModel('phase_3/models/props/drop_shadow')
        dropShadow.setColor(0, 0, 0, 0.5)
        dropShadow.setPos(0, 0, -0.55)
        dropShadow.setScale(1.25)
        dropShadow.flattenLight()
        dropShadow.reparentTo(self.sunchaser)

        self.nametag = NametagGroup()
        self.nametag.setAvatar(self.sunchaser)
        self.nametag.setFont(ToontownGlobals.getToonFont())
        self.nametag.setName(EpisodeLocalizer.PrologueLaunchpadMcQuack)
        self.nametag.setActive(0)
        self.nametag.manage(base.marginManager)
        self.nametag.getNametag3d().setBillboardOffset(4)
        nametagNode = self.nametag.getNametag3d().upcastToPandaNode()
        self.nametagNP = self.sunchaser.attachNewNode(nametagNode)
        self.nametagNP.setName('sunchaser')
        self.nametagNP.setScale(0.3)
        self.nametagNP.setPos(0, 0, 1)
        self.nametagNP.hide()

    def generateMovie(self):
        episodeStatus = base.cr.episodeManager.getEpisodeStatus(self.episodeZoneId)
        if not episodeStatus:
            runSfx = base.loader.loadSfx('phase_6/audio/sfx/KART_Engine_loop_1.ogg')
            landingSfx = base.loader.loadSfx('phase_6/audio/sfx/KART_Skidding_On_Asphalt.ogg')

            propellerTrack = Parallel(LerpHprInterval(self.sunchaser.find('**/prop_right'), 0.5, (0, 0, 360),
                                                      startHpr=(0, 0, 0)),
                                      LerpHprInterval(self.sunchaser.find('**/prop_left'), 0.5, (0, 0, -360),
                                                      startHpr=(0, 0, 0)))
            propellerIdleTrack = Parallel(LerpHprInterval(self.sunchaser.find('**/prop_right'), 2.0, (0, 0, 360),
                                                          startHpr=(0, 0, 0)),
                                          LerpHprInterval(self.sunchaser.find('**/prop_left'), 2.0, (0, 0, -360),
                                                          startHpr=(0, 0, 0)))

            dialogue = EpisodeLocalizer.PrologueOakStreetDialogue

            self.movie = Sequence(Func(self.toon.hide), Func(self.lockToon), Func(base.camera.reparentTo, self.sunchaser),
                                  Func(base.camera.setPosHpr, 0, -10, 0, 0, 0, 0), Func(propellerTrack.loop),
                                  Func(base.playSfx, runSfx, looping=1, volume=0.5, node=self.sunchaser),
                                  LerpPosInterval(self.sunchaser, 7.5, (-311.87, 377.01, 2.8999)),
                                  Func(LerpFunctionInterval(runSfx.setVolume, fromData=0.5, toData=0.3, duration=2.0).start),
                                  Func(base.playSfx, landingSfx), Func(propellerTrack.finish), Func(propellerIdleTrack.loop),
                                  LerpPosInterval(self.sunchaser, 2.5, (-311.87, 400.0, 2.8999), blendType='easeOut'),
                                  Wait(0.5), Func(self.nametagNP.show), Func(self.nametag.setChat, dialogue[0], CFSpeech),
                                  LerpPosHprInterval(base.camera, 0.5, (0, -4, 0), (0, 7.5, 0)),
                                  Wait(4.5), Func(self.toon.show), Func(self.releaseToon), Func(self.nametag.clearChat),
                                  Func(self.toon.setPosHpr, -331.33, 426.4, -0.28, 212.32, 0, 0), Wait(1.0),
                                  Func(self.toon.displayTalk, dialogue[1]), Wait(4.0), Func(self.toon.clearChat),
                                  Func(self.nametag.setChat, dialogue[2], CFSpeech), Wait(5.0),
                                  Func(self.nametag.clearChat), Func(self.nametag.setChat, dialogue[3], CFSpeech),
                                  Wait(1.0), Parallel(LerpPosInterval(self.sunchaser, 7.5, (-311.87, 550.01, 80)),
                                                      LerpFunctionInterval(runSfx.setVolume, fromData=0.3, toData=0,
                                                                           duration=3.0),
                                                      Sequence(Wait(3.0), Func(self.nametagNP.hide),
                                                               Func(self.toon.enableAvatarControls),
                                                               LerpColorScaleInterval(self.sunchaser, 4.5, (1, 1, 1, 0)))),
                                  Func(runSfx.stop), Func(propellerIdleTrack.finish))
