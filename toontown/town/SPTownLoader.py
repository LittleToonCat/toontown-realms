from panda3d.core import NodePath, BitMask32
from direct.interval.IntervalGlobal import Wait, Sequence
from . import TownLoader
from . import SPStreet
from toontown.coghq import SellbotHQFutureGlobals
from toontown.suit import Suit, SuitDNA, BossCog
from toontown.toonbase import ToontownGlobals
from toontown.distributed import HoodMgr


class SPTownLoader(TownLoader.TownLoader):

    def __init__(self, hood, parentFSM, doneEvent):
        TownLoader.TownLoader.__init__(self, hood, parentFSM, doneEvent)

        # Street class
        self.streetClass = SPStreet.SPStreet

        self.musicFile = {ToontownGlobals.TutorialTerrace: 'phase_3.5/audio/bgm/TC_SZ.ogg',
                          ToontownGlobals.ToontownSkies: 'phase_14.5/audio/bgm/SP_SZ_activity.ogg',
                          ToontownGlobals.CogtownCentral: 'phase_9/audio/bgm/encntr_suit_HQ_nbrhood.ogg',
                          ToontownGlobals.SellbotHQFuture: 'phase_9/audio/bgm/encntr_suit_HQ_nbrhood.ogg'}
        self.activityMusicFile = {ToontownGlobals.TutorialTerrace: 'phase_3.5/audio/bgm/TC_SZ_activity.ogg',
                                  ToontownGlobals.CogtownCentral: 'phase_9/audio/bgm/encntr_suit_HQ_nbrhood.ogg',
                                  ToontownGlobals.SellbotHQFuture: 'phase_9/audio/bgm/encntr_suit_HQ_nbrhood.ogg'}
        self.battleMusicFile = 'phase_4/audio/bgm/TC_battle.ogg'

        # Load the appropriate storage for this theme
        self.townStorageDNAFile = ('phase_5/dna/ttrm_d_strg_ttc_town.dna',
                                   'phase_14.5/dna/ttrm_d_strg_sph_town.dna')

        self.actors = []

    def load(self, zoneId):
        TownLoader.TownLoader.load(self, zoneId)
        Suit.loadSuits()

        if self.canonicalBranchZone != ToontownGlobals.SellbotHQFuture:
            dnaFile = 'phase_14.5/dna/ttrm_d_ara_sph_' + str(self.canonicalBranchZone) + '.dna'
            self.createHood(dnaFile)

            # Unique changes for the Cogtown Central zone
            if self.canonicalBranchZone == ToontownGlobals.CogtownCentral:
                tunnels = self.geom.findAllMatches('**/prop_safe_zone_tunnel')
                bldgs = self.geom.findAllMatches('**/suit_landmark_**')
                signs = self.geom.findAllMatches('**/prop_sign_**')

                for tunnel in tunnels:
                    tunnel.setColorScale(0.5, 0.5, 0.5, 1)

                for bldg in bldgs:
                    bldg.setColorScale(0.75, 0.75, 0.75, 1)

                for sign in signs:
                    sign.setColorScale(0.75, 0.75, 0.75, 1)
        else:
            # Setup Sellbot HQ Future
            cog = Suit.Suit()
            cogDNA = SuitDNA.SuitDNA()
            cogDNA.newSuit('ms')
            cog.setDNA(cogDNA)
            cog.loop('neutral')
            cog.setPos(32, -170, 100.288)
            cog.setH(175)
            cog.reparentTo(render)
            self.actors.append(cog)

            vp = BossCog.BossCog()
            vpDNA = SuitDNA.SuitDNA()
            vpDNA.newBossCog('s')
            vp.setDNA(vpDNA, 0)
            vp.setPos(69, -246, 80)
            vp.setHpr(180, 0, 280)
            vp.reparentTo(render)
            self.actors.append(vp)

            cfo = BossCog.BossCog()
            cfoDNA = SuitDNA.SuitDNA()
            cfoDNA.newBossCog('m')
            cfo.setDNA(cfoDNA, 0)
            cfo.setPos(48, 105.6, 94)
            cfo.loop('wave')
            cfo.setH(90)
            cfo.pelvis.setH(-90)
            cfo.setScale(0.2)
            cfo.reparentTo(render)
            self.actors.append(cfo)

            ceo = BossCog.BossCog()
            ceoDNA = SuitDNA.SuitDNA()
            ceoDNA.newBossCog('c')
            ceo.setDNA(ceoDNA, 0)
            ceo.setPos(119, 604, 167)
            ceo.loop('wave')
            ceo.setHpr(-6.077, 0, 0)
            ceo.pelvis.setH(-90)
            ceo.setScale(1.8)
            ceo.doorA.request('open')
            ceo.doorB.request('open')
            ceo.reparentTo(render)
            self.actors.append(ceo)

            geom = NodePath('SellbotHQFuture')

            flattenGroups = {}

            for modelData in SellbotHQFutureGlobals.Models:
                model = loader.loadModel(modelData[0])

                pos = modelData[1]
                if pos:
                    model.setPos(pos)

                hpr = modelData[2]
                if hpr:
                    model.setHpr(hpr)

                scale = modelData[3]
                if scale:
                    model.setScale(scale)

                color = modelData[4]
                if color:
                    if isinstance(color, int):
                        model.setColor(color)
                    elif isinstance(color, (tuple, list)):
                        model.setColor(*color)

                colorScale = modelData[5]
                if colorScale:
                    if isinstance(colorScale, int):
                        model.setColorScale(colorScale)
                    elif isinstance(colorScale, (tuple, list)):
                        model.setColorScale(*colorScale)

                texturePath = modelData[6]
                if texturePath:
                    model.setTexture(loader.loadTexture(texturePath), 1)

                flattenGroupIndex = modelData[7]
                if flattenGroupIndex:
                    flattenGroup = flattenGroups.get(flattenGroupIndex)
                    if not flattenGroup:
                        flattenGroup = NodePath('flattenGroup-%d' % flattenGroupIndex)
                        flattenGroups[flattenGroupIndex] = flattenGroup
                    model.reparentTo(flattenGroup)
                else:
                    model.reparentTo(geom)

            for flattenGroup in flattenGroups.values():
                flattenGroup.reparentTo(geom)
                flattenGroup.flattenStrong()

            del flattenGroups

            self.geom = geom

            elevator = self.geom.find('**/Elevator.egg')
            if not elevator.isEmpty():
                # Make the elevator a bit easier to use
                elevator.find('**/wall_back').setCollideMask(BitMask32.allOff())
                elevator.find('**/wall_front').setCollideMask(BitMask32.allOff())

                elevatorPosIvalUp = elevator.posInterval(13, (89, 260, 150))
                elevatorPosIvalDown = elevator.posInterval(13, (89, 260, 114))
                self.elevatorIval = Sequence(elevatorPosIvalUp, Wait(13), elevatorPosIvalDown, Wait(13), name='elevatorIval')
                self.elevatorIval.loop()

    def unload(self):
        Suit.unloadSuits()

        for actor in self.actors:
            actor.delete()

        if hasattr(self, 'elevatorIval') and self.elevatorIval.isPlaying():
            self.elevatorIval.finish()

        TownLoader.TownLoader.unload(self)
