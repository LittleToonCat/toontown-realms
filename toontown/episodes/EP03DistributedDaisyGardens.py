import random

from direct.actor import Actor
from direct.gui.DirectLabel import DirectLabel
from direct.interval.IntervalGlobal import *
from direct.showbase import Audio3DManager

from panda3d.toontown import *

from panda3d.core import *

from otp.otpbase.PythonUtil import weightedChoice
from toontown.avatar import ToontownAvatarUtils
from toontown.episodes import DistributedEpisodeZone, EpisodeLocalizer
from toontown.episodes import EpisodeConfig
from toontown.episodes.EpisodeGlobals import *
from toontown.parties import PartyGlobals
from toontown.toontowngui.ServerTimeGui import ServerTimeGui
from toontown.toon.ToonDNA import ToonDNA
from toontown.toonbase import TTLocalizer, ToontownGlobals, ClientSettings

from toontown.makeatoon import NameGenerator


class EP03DistributedDaisyGardens(DistributedEpisodeZone.DistributedEpisodeZone):

    def __init__(self, cr):
        DistributedEpisodeZone.DistributedEpisodeZone.__init__(self, cr)
        self.episodeZoneId = EpisodeConfig.EP03_DAISY_GARDENS

    def disable(self):
        DistributedEpisodeZone.DistributedEpisodeZone.disable(self)
        if hasattr(self.partyGateTimeGui, 'ival'):
            self.partyGateTimeGui.ival.finish()
        for movie in self.npcMovies:
            movie.finish()
        for toon in self.toons:
            toon.delete()

        self.sounds['bgm'].stop()

        self.partyGateTimeGui.destroy()
        del self.partyGateTimeGui
        del self.partyGateClockFlat

    def generateGeom(self):
        base.loader.beginBulkLoad('episode', TTLocalizer.HeadingToHood % {
            'to': TTLocalizer.DaisyGardens[0],
            'hood': TTLocalizer.DaisyGardens[2]
        }, 12, 1, TTLocalizer.TIP_OFFLINE_MODE)
        loader.loadDNAFile(base.cr.playGame.hood.dnaStore, 'phase_8/dna/ttrm_d_strg_dga.dna')
        loader.loadDNAFile(base.cr.playGame.hood.dnaStore, 'phase_8/dna/ttrm_d_strg_dga_sz.dna')
        loader.loadDNAFile(base.cr.playGame.hood.dnaStore, 'phase_14/dna/ttrm_d_strg_dga_ep03.dna')

        node = loader.loadDNAFile(base.cr.playGame.hood.dnaStore, 'phase_14/dna/ttrm_d_ara_dga_sz_ep03.dna')
        if node.getNumParents() == 1:
            self.geom = NodePath(node.getParent(0))
            self.geom.reparentTo(render)
        else:
            self.geom = render.attachNewNode(node)
        base.loader.tick()

        self.geom.flattenMedium()

        # Hide the black parts in the doors
        doorHoles = self.geom.findAllMatches('**/doorFrameHole*')
        for hole in doorHoles:
            hole.removeNode()

        self.sky = loader.loadModel('phase_3.5/models/props/TT_sky')
        self.sky.reparentTo(self.geom)

        base.loader.tick()

        # I'd love to just do a find from the geom, but we cant because the dna loader flattens the node
        # out of existence, so we'll just load a new petshop
        oldPetshop = self.geom.find('**/*toon_landmark_DG_pet_shop_DNARoot')

        self.toon.setPosHpr(38.23, 8.05, 9.4, 51, 0, -25)
        self.toon.setActiveShadow(0)

        self.petShop = loader.loadModel('phase_8/models/modules/PetShopExterior_DG')  # type: NodePath
        self.petShop.reparentTo(self.geom)
        self.petShop.setPosHpr(oldPetshop, 0, 0)

        # Move the DNASign and DNADoor to the substitute model
        oldPetshop.find('**/*sign_decal').reparentTo(self.petShop)
        oldPetshop.find('**/*door_front').reparentTo(self.petShop)

        # Destroy the old petshop
        oldPetshop.removeNode()

        # Hide the doodle
        self.petShop.find("**/doodleSilhouette").hide()

        base.loader.tick()

        self.bigFlower = loader.loadModel('phase_8/models/props/DG_flower-mod.bam')
        self.bigFlower.setPos(1.39, 92.91, 2.0)
        self.bigFlower.setScale(2.5)
        self.bigFlower.reparentTo(self.geom)

        base.loader.tick()

        fish = Actor.Actor('phase_4/models/props/exteriorfish-zero',
                           {'swim': 'phase_4/models/props/exteriorfish-swim'})
        fish.reparentTo(self.petShop)
        fish.setBlend(frameBlend=ClientSettings.SmoothAnimations.get())
        fish.loop('swim')

        base.loader.tick()

        # Add the fisherman
        fishermanOrigin = self.geom.find('**/npc_fisherman_origin_0;+s')
        self.fisherman = ToontownAvatarUtils.createToon(5008, coll = False)
        self.fisherman.addActive()
        self.fisherman.reparentTo(fishermanOrigin)
        self.fisherman.clearMat()

        base.loader.tick()

        self.audio3d = Audio3DManager.Audio3DManager(base.sfxManagerList[0], camera)

        self.sounds = {
            'crash': self.audio3d.loadSfx('phase_14/audio/sfx/ttoff_s_ep03_crashMono.ogg'),
            'bgm': loader.loadMusic('phase_8/audio/bgm/DG_nbrhood.ogg')
        }  # type: dict[str, AudioSound]

        toOakStreetTunnel = self.geom.find('**/linktunnel_dg_5301_DNARoot')
        linkSphere = toOakStreetTunnel.find('**/tunnel_trigger')

        cnode = linkSphere.node()
        cnode.setName('to_oakstreet302')
        cnode.setCollideMask(ToontownGlobals.WallBitmask | ToontownGlobals.GhostBitmask)

        base.loader.tick()

        # == Party Gate Stuff ==
        partyGate = self.geom.find('**/partyGate_grp')
        self.partyGateClockFlat = partyGate.find('**/clock_flat')
        self.partyGateTimeGui = ServerTimeGui(partyGate)
        self.partyGateTimeGui.setPos(partyGate.find('**/clockText_locator').getPos() + Point3(0.0, -0.04, -0.2))
        self.partyGateTimeGui.setHpr(partyGate.find('**/clockText_locator').getHpr())
        self.partyGateTimeGui.setScale(12.0, 1.0, 26.0)
        self.partyGateTimeGui.amLabel.setPos(-0.035, 0, -0.032)
        self.partyGateTimeGui.amLabel.setScale(0.5)
        self.partyGateTimeGui.updateTime()
        color = PartyGlobals.PlayGroundToPartyClockColors['dga']
        self.partyGateTimeGui.hourLabel['text_fg'] = color
        self.partyGateTimeGui.colonLabel['text_fg'] = color
        self.partyGateTimeGui.minutesLabel['text_fg'] = color
        self.partyGateTimeGui.amLabel['text_fg'] = color
        gateFont = ToontownGlobals.getMinnieFont()
        gateSign = self.geom.find('**/partyGateSignGroup')
        leftSign = gateSign.find('**/signTextL_locatorBack')
        signScale = 0.35
        wordWrap = 8
        leftText = DirectLabel(parent = leftSign, pos = (0, 0.04, 0.0), relief = None,
                               text = TTLocalizer.PartyGateLeftSign, text_align = TextNode.ACenter,
                               text_font = gateFont, text_wordwrap = wordWrap, text_fg = Vec4(0.7, 0.3, 0.3, 1.0),
                               scale = signScale)
        rightSign = gateSign.find('**/signTextR_locatorFront')
        rightText = DirectLabel(parent = rightSign, pos = (0, 0.04, 0.0), relief = None,
                                text = TTLocalizer.PartyGateRightSign, text_align = TextNode.ACenter,
                                text_font = gateFont, text_wordwrap = wordWrap, text_fg = Vec4(0.7, 0.3, 0.3, 1.0),
                                scale = signScale)

        # self.paths = loader.loadModel('phase_14/paths/ep03-dg-npc-paths')
        # self.toonAPath = Mopath.Mopath()
        # self.toonAPath.loadNodePath(self.paths.find('**/301_path_0'))
        # self.toonAPath.fFaceForward = 1
        # self.toonAPath.timeScale = 40
        # self.toonBPath = Mopath.Mopath()
        # self.toonBPath.loadNodePath(self.paths.find('**/301_path_1'))
        # self.toonBPath.fFaceForward = 1
        # self.toonBPath.timeScale = 20

        base.loader.tick()
        namegen = NameGenerator.NameGenerator()
        self.toons = []
        """
        these are the indexes for the npcs
        LEFT RAMP = 0
        FISHING = 1
        HQ = 2
        DD TUNNEL CONVO 1 = 3
        DD TUNNEL CONVO 2 = 4
        GAG SHOP = 5
        MAZE1 = 6
        MAZE2 = 7
        TROLLEY = 8
        """
        for npc in EP03_01_NPCS:
            dna = ToonDNA(type = 't')
            randName = namegen.randomNameMoreinfo(boy = dna.gender == 'm', girl = dna.gender == 'f')[
                -1]
            # todo: why the hell isnt the nametag style applying?
            nametag = weightedChoice((
                (50, 100), (30, 0), (30, random.randint(1, 13)),
            ))
            toon = ToontownAvatarUtils.createUniqueToon(name = randName, dna = dna, nametagStyle = nametag,
                                                        colorType = NametagGroup.CCSpeedChat)
            toon.addActive()
            toon.setPosHpr(*npc[0])
            toon.loop(npc[1])
            toon.setPickable(1)
            base.loader.tick()
            self.toons.append(toon)

        # add the petshop npc
        self.petshopClerk = ToontownAvatarUtils.createToon(5011, coll = False)
        self.petshopClerk.addActive()
        self.petshopClerk.setH(180)
        self.petshopClerk.reparentTo(self.petShop.find('**/*door_front'))
        # temp beforfe we add animations
        self.petshopClerk.setTPose()
        base.loader.tick()

        # Add the other doodles
        self.doodle2 = ToontownAvatarUtils.createDoodle('$doodle2name', 0, 1, 0, 0, 0, 0, 0, 1, 1)
        base.loader.tick()

        self.accept('enterto_oakstreet302', self.enterTunnel)
        self.sounds['bgm'].setLoop(1)
        self.acceptOnce(self.sounds['bgm'].getFinishedEvent(), self.sounds['bgm'].play)

        gsg = base.win.getGsg()
        if gsg:
            self.geom.prepareScene(gsg)

        base.loader.tick()
        # self.toonAWalk = MopathInterval(self.toonAPath, self.toons[0])
        # self.toonBWalk = MopathInterval(self.toonBPath, self.toons[1])
        # self.toonAWalk.loop()
        # self.toonBWalk.loop()

        base.loader.endBulkLoad('episode')

    def generateMovie(self):
        self.toon.setDoodleIndex(1)

        self.generateStory()
        self.story.hide()

        self.movie = Sequence(
                Func(self.lockToon),
                Func(base.camera.setPosHpr, 1.39, 92.91, 190, 15, -90, 0),

                # PLAYGROUND OVERVIEW
                Parallel(
                        Sequence(
                                Wait(2),
                                Func(self.enterText, self.story),
                                # THIS GREAT MOMENT IN TT HISTORY
                                Func(self.speakText, self.story, EpisodeLocalizer.StormSellbotIntroCard[0]),
                        ),
                        LerpPosHprInterval(base.camera, 8.0, pos = (1.39, 92.91, 130),
                                           hpr = (-35, -90, 0.0)),
                        LerpHprInterval(self.bigFlower, 8.0, hpr = (130, 0, 0))
                ),
                Func(base.camera.setPosHpr, 65.6, 52.6, 6.4, -27, -1.8, 0),

                # AS TOONS ARE CELEBRATING VICTORY PARTIES...
                Func(self.speakText, self.story, EpisodeLocalizer.StormSellbotIntroCard[1]),

                # CAMERA SHOT OF PETSHOP
                LerpPosHprInterval(base.camera, 6.0, pos = (8.17, 32.89, 3.29),
                                   hpr = (-129.0, 7.0, 0.0), blendType = 'easeInOut'),

                Wait(1.8),
                Func(self.toon.pet.loop, 'jump'),
                Wait(0.2),
                # Sparky breaks out of the shop
                Func(self.petShop.find("**/doodleSilhouette").show),
                Func(self.sounds['crash'].play),
                Parallel(
                        # LAUNCH SPARKY OUT OF THE BUILDING
                        LerpPosInterval(self.toon, 0.5, pos = (17.73, 24.65, 9.4),
                                        startPos = (38.23, 8.05, 9.4)),
                        # SHAKE THE CAMERA A LITTLE
                        Sequence(
                                LerpPosInterval(base.camera, 0.1,
                                                pos = (8.17, 32.89, 3.45),
                                                blendType = 'easeInOut'),
                                LerpPosInterval(base.camera, 0.1,
                                                pos = (8.17, 32.89, 3.12),
                                                blendType = 'easeInOut'),
                                LerpPosInterval(base.camera, 0.1,
                                                pos = (8.17, 32.89, 3.29),
                                                blendType = 'easeInOut'),
                        )
                ),
                # We do a quick cut and show sparky landing
                Func(self.toon.setActiveShadow, 1),
                Func(base.camera.setPosHpr, Point3(26.18, 31.72, 1.0), Point3(106.52, 5.0, 0.00)),
                Func(self.toon.setPosHpr, 14.27, 27.45, 3.4, 51, 0, 0),
                LerpPosInterval(self.toon, 0.2, pos = (14.27, 27.45, 0.02)),
                # Let the land part of the jump animation complete...
                Wait(1),
                # Then we can use the neutral anim
                Func(self.toon.pet.loop, 'neutralHappy'),

                Wait(3.0),

                # Show the other doodle escaping

                # clerk walks out


                # EXIT
                Func(self.toon.show),
                Func(self.toon.setPosHpr, self.toon, 0, 0, 0, 0, 0, 0),
                Func(self.releaseToon),
                Func(self.toon.enableAvatarControls),
                Func(self.leaveText, self.story),

                name = 'ep301_movie_main'
        )

        for movie in self.npcMovies:
            movie.loop()
        # Func(self.teleportToZone, self.zoneConnections[0])))

    @property
    def npcMovies(self):
        t = self.toons

        # TOON 0
        toon0Seq = Sequence(
                Func(t[0].setPosHpr, Point3(65.5, 180, 10.02), Point3(160.0, 0.0, 0.0)),
                Func(t[0].loop, 'run'),
                LerpPosInterval(t[0], 2.0, Point3(57.50, 158.02, 10.02)),
                Func(t[0].loop, 'neutral'),
                Wait(0.3),
                Func(t[0].loop, 'walk'),
                LerpHprInterval(t[0], 0.3, Point3(238.35, 0, 0)),
                Func(t[0].loop, 'run'),
                LerpPosInterval(t[0], 0.1, Point3(59.20, 156.97, 10.02)),
                LerpPosInterval(t[0], 2.0, Point3(78.12, 145.31, 0.03)),
                LerpPosInterval(t[0], 1.0, Point3(85.60, 140.70, 0.03)),
                Wait(0.5),
                name = 'ep301_dg_toon0'
        )

        return (toon0Seq,)

    def enterTunnel(self, collEntry):
        # TODO: Animation of doodle walking in
        self.teleportToZone(self.zoneConnections[0])
