from panda3d.core import *
from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.interval.IntervalGlobal import *
from direct.actor import Actor
from toontown.toonbase import ToontownGlobals, ClientSettings
import random
from toontown.parties import PartyGlobals
from toontown.parties.PartyUtils import getCenterPosFromGridSize


class Decoration(NodePath):
    notify = directNotify.newCategory('Decoration')

    def __init__(self, decorId, x, y, h):
        name = PartyGlobals.DecorationIds(decorId).name
        NodePath.__init__(self, name)
        self.name = name
        centerX, centerY = getCenterPosFromGridSize(x, y, PartyGlobals.DecorationInformationDict[decorId]['gridsize'])
        self.setPos(centerX, centerY, 0.0)
        self.setH(h)
        
        def loadSky(skyFile, tag):
            base.cr.playGame.hood.sky = loader.loadModel(skyFile)
            base.cr.playGame.hood.sky.setTag('sky', tag)
            base.cr.playGame.hood.sky.setName('party_skybox')
            base.cr.playGame.hood.sky.setScale(2.0)
            base.cr.playGame.hood.sky.reparentTo(render)
        
        if self.name == 'CakeTower':
            self.partyCake = loader.loadModel('phase_13/models/parties/tt_m_ara_pty_cakeTower')
            tntSeqNode = self.partyCake.find('**/seqNode_tnt').node()
            tntSeqNode.setFrameRate(20)
            self.partyCake.reparentTo(self)
        elif self.name == 'BannerJellyBean':
            partyBannerModel = loader.loadModel('phase_13/models/parties/tt_m_ara_pty_bannerJellybean_model')
            banner = []
            banner1 = partyBannerModel.find('**/banner1')
            banner2 = partyBannerModel.find('**/banner2')
            temp = NodePath('Empty')
            banner1.reparentTo(temp)
            banner2.reparentTo(temp)
            banner.append(banner1)
            banner.append(banner2)
            self.partyBanner = Actor.Actor(partyBannerModel, {'float': 'phase_13/models/parties/tt_m_ara_pty_bannerJellybean'})
            self.partyBanner.setBlend(frameBlend=ClientSettings.SmoothAnimations.get())
            bannerSeqNodeParent = self.partyBanner.find('**/bannerJoint')
            bannerSeqNode = SequenceNode('banner')
            for bannerNode in banner:
                bannerSeqNode.addChild(bannerNode.node())

            temp.detachNode()
            del temp
            bannerSeqNodeParent.attachNewNode(bannerSeqNode)
            bannerSeqNode.setFrameRate(4)
            bannerSeqNode.loop(True)
            bannerSeqNode.setPlayRate(1)
            balloonLeft = self.partyBanner.find('**/balloonsLMesh')
            balloonRight = self.partyBanner.find('**/balloonsRMesh')
            balloonLeft.setBillboardAxis()
            balloonRight.setBillboardAxis()
            balloonLeftLocator = self.partyBanner.find('**/balloonJointL')
            balloonRightLocator = self.partyBanner.find('**/balloonJointR')
            balloonLeft.reparentTo(balloonLeftLocator)
            balloonRight.reparentTo(balloonRightLocator)
            self.partyBanner.loop('float')
            self.partyBanner.reparentTo(self)
        elif self.name == 'GagGlobe':
            self.partyGlobe = Actor.Actor('phase_13/models/parties/tt_m_ara_pty_gagGlobe_model', {'idle': 'phase_13/models/parties/tt_m_ara_pty_gagGlobe'})
            self.partyGlobe.setBlend(frameBlend=ClientSettings.SmoothAnimations.get())
            self.partyGlobe.setBillboardAxis()
            confettiLocator = self.partyGlobe.find('**/uvj_confetti')
            confettiMesh = self.partyGlobe.find('**/innerGlobeMesh')
            confettiMesh.setTexProjector(confettiMesh.findTextureStage('default'), confettiLocator, self.partyGlobe)
            collisionMesh = self.partyGlobe.find('**/collisionMesh')
            collisionMesh.hide()
            self.globeSphere = CollisionSphere(confettiMesh.getBounds().getCenter(), confettiMesh.getBounds().getRadius())
            self.globeSphere.setTangible(1)
            self.globeSphereNode = CollisionNode('gagGlobe' + str(self.getPos()))
            self.globeSphereNode.setIntoCollideMask(ToontownGlobals.WallBitmask)
            self.globeSphereNode.addSolid(self.globeSphere)
            self.globeSphereNodePath = self.partyGlobe.attachNewNode(self.globeSphereNode)
            self.partyGlobe.loop('idle')
            self.partyGlobe.reparentTo(self)
        elif self.name == 'FlyingHeart':
            flyingHeartModel = loader.loadModel('phase_13/models/parties/tt_m_ara_pty_heartWing_model')
            self.flyingHeart = Actor.Actor(flyingHeartModel, {'idle': 'phase_13/models/parties/tt_m_ara_pty_heartWing'})
            self.flyingHeart.setBlend(frameBlend=ClientSettings.SmoothAnimations.get())
            wingsSeqNodeParent = self.flyingHeart.find('**/heartWingJoint')
            collisionMesh = self.flyingHeart.find('**/collision_heartWing')
            collisionMesh.hide()
            self.globeSphere = CollisionSphere(collisionMesh.getBounds().getCenter(), collisionMesh.getBounds().getRadius())
            self.globeSphere.setTangible(1)
            self.globeSphereNode = CollisionNode('flyingHeart' + str(self.getPos()))
            self.globeSphereNode.setIntoCollideMask(ToontownGlobals.WallBitmask)
            self.globeSphereNode.addSolid(self.globeSphere)
            self.globeSphereNodePath = self.flyingHeart.attachNewNode(self.globeSphereNode)
            self.globeSphereNodePath.reparentTo(wingsSeqNodeParent)
            wings = []
            wingsSeqNode = SequenceNode('wingsSeqNode')
            temp = NodePath('Empty')
            wing1 = self.flyingHeart.find('**/wing1')
            wing2 = self.flyingHeart.find('**/wing2')
            wing3 = self.flyingHeart.find('**/wing3')
            wing4 = self.flyingHeart.find('**/wing4')
            wing1.reparentTo(temp)
            wing2.reparentTo(temp)
            wing3.reparentTo(temp)
            wing4.reparentTo(temp)
            wings.append(wing1)
            wings.append(wing2)
            wings.append(wing3)
            wings.append(wing4)
            wingsSeqNode.addChild(wing1.node())
            wingsSeqNode.addChild(wing2.node())
            wingsSeqNode.addChild(wing3.node())
            wingsSeqNode.addChild(wing4.node())
            wingsSeqNode.addChild(wing3.node())
            wingsSeqNode.addChild(wing2.node())
            temp.detachNode()
            del temp
            wingsSeqNodeParent.attachNewNode(wingsSeqNode)
            wingsSeqNode.setFrameRate(12)
            wingsSeqNode.loop(True)
            wingsSeqNode.setPlayRate(1)
            self.flyingHeart.loop('idle')
            self.flyingHeart.reparentTo(self)
        elif self.name == 'HeartBanner':
            self.heartBanner = Actor.Actor('phase_13/models/parties/tt_m_ara_pty_bannerValentine_model', {'idle': 'phase_13/models/parties/tt_m_ara_pty_bannerValentine'})
            self.heartBanner.setBlend(frameBlend=ClientSettings.SmoothAnimations.get())
            balloonLeft = self.heartBanner.find('**/balloonsL')
            balloonRight = self.heartBanner.find('**/balloonsR')
            balloonLeft.setBillboardAxis()
            balloonRight.setBillboardAxis()
            balloonLeftLocator = self.heartBanner.find('**/balloonJointL')
            balloonRightLocator = self.heartBanner.find('**/balloonJointR')
            balloonLeft.reparentTo(balloonLeftLocator)
            balloonRight.reparentTo(balloonRightLocator)
            self.heartBanner.loop('idle')
            self.heartBanner.reparentTo(self)
        elif self.name == 'Hydra' or self.name == 'StageWinter':
            if self.name == 'StageWinter':
                self.hydra = Actor.Actor('phase_13/models/parties/tt_r_ara_pty_winterProps', {'dance': 'phase_13/models/parties/tt_a_ara_pty_hydra_dance'})
            else:
                self.hydra = Actor.Actor('phase_13/models/parties/tt_a_ara_pty_hydra_default', {'dance': 'phase_13/models/parties/tt_a_ara_pty_hydra_dance'})
            self.hydra.setBlend(frameBlend=ClientSettings.SmoothAnimations.get())
            st = random.randint(0, 10)
            animIval = ActorInterval(self.hydra, 'dance')
            animIvalDur = animIval.getDuration()
            self.decSfx = loader.loadSfx('phase_13/audio/sfx/tt_s_ara_pty_propsShow_dance.ogg')
            soundIval = SoundInterval(self.decSfx, node=self.hydra, listenerNode=base.localAvatar, volume=PartyGlobals.DECORATION_VOLUME, cutOff=PartyGlobals.DECORATION_CUTOFF, duration=animIvalDur)
            self.animSeq = Parallel(animIval, soundIval)
            self.animSeq.loop(st)
            collisions = self.hydra.find('**/*collision*')
            collisions.setPos(0, 0, -5)
            self.hydra.flattenStrong()
            self.hydra.reparentTo(self)
            if self.name == 'StageWinter':
                stageBounds = self.hydra.find('**/stage').node().getBounds()
                self.hydra.node().setBounds(stageBounds)
                self.hydra.node().setFinal(1)
        elif self.name == 'TubeCogVictory':
            self.tubeCog = Actor.Actor('phase_5.5/models/estate/tt_a_ara_pty_tubeCogVictory_default', {'wave': 'phase_5.5/models/estate/tt_a_ara_pty_tubeCogVictory_wave'})
            self.tubeCog.setBlend(frameBlend=ClientSettings.SmoothAnimations.get())
            st = random.randint(0, 10)
            animIval = ActorInterval(self.tubeCog, 'wave')
            animIvalDur = animIval.getDuration()
            self.decSfx = loader.loadSfx('phase_13/audio/sfx/tt_s_ara_pty_tubeCogVictory_wave.ogg')
            soundIval = SoundInterval(self.decSfx, node=self.tubeCog, listenerNode=base.localAvatar, volume=PartyGlobals.DECORATION_VOLUME, cutOff=PartyGlobals.DECORATION_CUTOFF, duration=animIvalDur)
            self.animSeq = Parallel(animIval, soundIval)
            self.animSeq.loop()
            self.animSeq.setT(st)
            self.tubeCog.flattenStrong()
            self.tubeCog.reparentTo(self)
        elif self.name == 'BannerVictory':
            self.bannerVictory = Actor.Actor('phase_13/models/parties/tt_m_ara_pty_bannerVictory_model', {'idle': 'phase_13/models/parties/tt_m_ara_pty_bannerVictory'})
            self.bannerVictory.setBlend(frameBlend=ClientSettings.SmoothAnimations.get())
            balloonLeft = self.bannerVictory.find('**/balloonsLMesh')
            balloonRight = self.bannerVictory.find('**/balloonsRMesh')
            balloonLeft.setBillboardAxis()
            balloonRight.setBillboardAxis()
            balloonLeftLocator = self.bannerVictory.find('**/balloonJointL')
            balloonRightLocator = self.bannerVictory.find('**/balloonJointR')
            balloonLeft.reparentTo(balloonLeftLocator)
            balloonRight.reparentTo(balloonRightLocator)
            self.bannerVictory.loop('idle')
            self.bannerVictory.reparentTo(self)
        elif self.name == 'CannonVictory':
            self.cannonVictory = Actor.Actor('phase_13/models/parties/tt_m_ara_pty_cannonVictory_model', {'idle': 'phase_13/models/parties/tt_m_ara_pty_cannonVictory'})
            self.cannonVictory.setBlend(frameBlend=ClientSettings.SmoothAnimations.get())
            confettiLocator = self.cannonVictory.findAllMatches('**/uvj_confetties')[1]
            confettiMesh = self.cannonVictory.find('**/confettis')
            confettiMesh.setTexProjector(confettiMesh.findTextureStage('default'), self.cannonVictory, confettiLocator)
            self.cannonVictory.flattenStrong()
            self.cannonVictory.loop('idle')
            self.cannonVictory.reparentTo(self)
        elif self.name == 'CogStatueVictory':
            self.decorationModel = loader.loadModel('phase_13/models/parties/tt_m_ara_pty_cogDoodleVictory')
            self.decorationModel.reparentTo(self)
            self.decorationShadow = self.setupAnimSeq()
        elif self.name == 'cogIceCreamVictory':
            self.decorationModel = loader.loadModel('phase_13/models/parties/tt_m_ara_pty_cogIceCreamVictory')
            self.decorationModel.reparentTo(self)
            self.decorationShadow = self.setupAnimSeq()
        elif self.name == 'cogIceCreamWinter':
            self.decorationModel = loader.loadModel('phase_13/models/parties/tt_m_ara_pty_cogIceCreamWinter')
            self.decorationModel.reparentTo(self)
            self.decorationShadow = self.setupAnimSeq()
        elif self.name == 'CogStatueWinter':
            self.decorationModel = loader.loadModel('phase_13/models/parties/tt_m_ara_pty_cogDoodleWinter')
            self.decorationModel.reparentTo(self)
            self.decorationShadow = self.setupAnimSeq()
        elif self.name == 'snowman':
            self.decorationModel = loader.loadModel('phase_13/models/estate/tt_m_prp_ext_snowman')
            self.decorationModel.reparentTo(self)
            self.decorationModel.find('**/growthStage_1').hide()
            self.decorationModel.find('**/growthStage_2').hide()
        elif self.name == 'snowDoodle':
            self.decorationModel = loader.loadModel('phase_5.5/models/estate/tt_m_prp_ext_snowDoodle')
            self.decorationModel.reparentTo(self)
            self.decorationModel.find('**/growthStage_1').hide()
            self.decorationModel.find('**/growthStage_2').hide()
        elif self.name == 'skybox_ttc':
            skyFile = 'phase_3.5/models/props/TT_sky'
            loadSky(skyFile, 'ttc')
        elif self.name == 'skybox_mml':
            skyFile = 'phase_6/models/props/MM_sky'
            loadSky(skyFile, 'mml')
            base.cr.playGame.hood.loader.geom.setColorScale(1, 0.95, 0.85, 1.0)
        elif self.name == 'skybox_br':
            skyFile = 'phase_3.5/models/props/BR_sky'
            loadSky(skyFile, 'br')
        elif self.name == 'skybox_ddl':
            skyFile = 'phase_8/models/props/DL_sky'
            loadSky(skyFile, 'ddl')
            base.cr.playGame.hood.loader.geom.setColorScale(0.7, 0.7, 0.7, 1.0)
        elif self.name == 'skybox_hw':
            skyFile = 'phase_14.5/models/props/halloween-skybox'
            loadSky(skyFile, 'hw')
            base.cr.playGame.hood.loader.geom.setColorScale(0.55, 0.55, 0.65, 1.0)
        elif self.name == 'skybox_sbhq':
            skyFile = 'phase_9/models/cogHQ/cog_sky'
            loadSky(skyFile, 'sbhq')
            base.cr.playGame.hood.loader.geom.setColorScale(0.7, 0.7, 0.7, 1.0)
        elif self.name == 'skybox_sbhq2003':
            skyFile = 'phase_9/models/cogHQ/old_sky'
            loadSky(skyFile, 'sbhq2003')
            base.cr.playGame.hood.loader.geom.setColorScale(0.7, 0.7, 0.7, 1.0)
        elif self.name == 'skybox_bbhq':
            skyFile = 'phase_12/models/bossbotHQ/BossTestSkyBox'
            loadSky(skyFile, 'bbhq')
            base.cr.playGame.hood.loader.geom.setColorScale(0.7, 0.7, 0.7, 1.0)
        else:
            self.decorationModels = loader.loadModel('phase_4/models/parties/partyDecorations')
            self.decorationModels.copyTo(self)
            decors = self.findAllMatches('**/partyDecoration_*')
            for i in range(decors.getNumPaths()):
                decPiece = decors.getPath(i)
                n = decPiece.getName()
                if n.endswith('shadow') or n.endswith('base') or n.endswith('collision') or n.endswith(name):
                    pass
                else:
                    decPiece.reparentTo(hidden)

        self.reparentTo(base.cr.playGame.hood.loader.geom)

    def setupAnimSeq(self):
        self.startAnim = 1
        self.animSeq = None
        shadow = self.find('**/*shadow*;+i')
        shadow.wrtReparentTo(base.cr.playGame.hood.loader.geom)
        self.startAnimSeq()
        return shadow

    def startAnimSeq(self):
        if self.animSeq:
            self.animSeq.finish()
        if self.startAnim == 1:
            self.animSeq = Sequence(LerpHprInterval(self.decorationModel, 3.0, Vec3(random.randint(0, 5), random.randint(0, 5), random.randint(0, 5))), Wait(0.05), Func(self.startAnimSeq))
            self.animSeq.start()

    def cleanUpAnimSequences(self):
        self.startAnim = 0
        if hasattr(self, 'animSeq'):
            self.animSeq.pause()
            self.animSeq.finish()
            if self.animSeq:
                del self.animSeq

    def unload(self):
        self.notify.debug('Unloading')
        if self.name == 'GagGlobe':
            self.globeSphereNodePath.removeNode()
            del self.globeSphereNodePath
            del self.globeSphereNode
            del self.globeSphere
            self.partyGlobe.delete()
            del self.partyGlobe
        elif self.name == 'Hydra' or self.name == 'StageWinter':
            self.cleanUpAnimSequences()
            self.hydra.delete()
            del self.hydra
            if hasattr(self, 'decSfx'):
                del self.decSfx
        elif self.name == 'TubeCogVictory':
            self.cleanUpAnimSequences()
            self.tubeCog.delete()
            del self.tubeCog
            if hasattr(self, 'decSfx'):
                del self.decSfx
        elif self.name == 'BannerJellyBean':
            self.partyBanner.delete()
        elif self.name == 'CakeTower':
            self.partyCake.removeNode()
        elif self.name == 'FlyingHeart':
            self.globeSphereNodePath.removeNode()
            del self.globeSphereNodePath
            del self.globeSphereNode
            del self.globeSphere
            self.flyingHeart.delete()
        elif self.name == 'HeartBanner':
            self.heartBanner.delete()
        elif self.name == 'CannonVictory':
            self.cannonVictory.delete()
            del self.cannonVictory
        elif self.name == 'cogIceCreamVictory' or self.name == 'CogStatueVictory' or self.name == 'cogIceCreamWinter' or self.name == 'CogStatueWinter':
            self.cleanUpAnimSequences()
            self.decorationModel.removeNode()
            self.decorationShadow.removeNode()
            del self.decorationShadow
        elif self.name == 'snowman' or self.name == 'snowDoodle':
            self.decorationModel.removeNode()
        elif self.name == 'BannerVictory':
            self.bannerVictory.delete()
            del self.bannerVictory
        elif 'skybox' in self.name:
            pass
        else:
            self.decorationModels.removeNode()
