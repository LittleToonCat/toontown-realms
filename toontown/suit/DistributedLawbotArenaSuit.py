from direct.interval.IntervalGlobal import *
from direct.fsm import ClassicFSM, State
from direct.gui.DirectGui import *
from direct.directnotify import DirectNotifyGlobal
from direct.task import Task

from panda3d.core import *

from toontown.battle import MovieUtil
from toontown.effects import DustCloud
from toontown.suit import SuitDNA
from toontown.toonbase import ToontownGlobals, TTLocalizer

from . import DistributedSuitBase


class DistributedLawbotArenaSuit(DistributedSuitBase.DistributedSuitBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedLawbotArenaSuit')
    timeToShow = 1.0
    timeToRelease = 3.15
    throwPlayrate = 1.0
    throwPaperEndTime = 4.33

    def __init__(self, cr):
        try:
            self.DistributedSuit_initialized
        except:
            self.DistributedSuit_initialized = 1
            DistributedSuitBase.DistributedSuitBase.__init__(self, cr)

            self.boss = None
            self.team = ToontownGlobals.BossArenaNoTeam
            self.mode = ToontownGlobals.LawbotArenaProsecutingBoth
            self.bonus = False

            self.icons = []

            self.activeIntervals = {}
            self.flyingEvidenceTrack = None

            # Lawyer FSM
            self.fsm = ClassicFSM.ClassicFSM('DistributedLawbotArenaSuit',
                                             [State.State('Off', self.enterOff, self.exitOff, ['Battle', 'neutral', 'hidden']),
                                              State.State('Battle', self.enterBattle, self.exitBattle, []),
                                              State.State('hidden', self.enterHidden, self.exitHidden, ['flyIn']),
                                              State.State('flyIn', self.enterFlyIn, self.exitFlyIn, ['hidden', 'neutral']),
                                              State.State('neutral', self.enterNeutral, self.exitNeutral, ['PreThrowProsecute', 'PreThrowAttack', 'Stunned']),
                                              State.State('PreThrowProsecute', self.enterPreThrowProsecute, self.exitPreThrowProsecute, ['PostThrowProsecute', 'neutral', 'Stunned']),
                                              State.State('PostThrowProsecute', self.enterPostThrowProsecute, self.exitPostThrowProsecute, ['PreThrowAttack', 'PreThrowProsecute', 'neutral', 'Stunned']),
                                              State.State('PreThrowAttack', self.enterPreThrowAttack, self.exitPreThrowAttack, ['PostThrowAttack', 'neutral', 'Stunned']),
                                              State.State('PostThrowAttack', self.enterPostThrowAttack, self.exitPostThrowAttack, ['PreThrowAttack', 'PreThrowProsecute', 'neutral', 'Stunned']),
                                              State.State('Stunned', self.enterStunned, self.exitStunned, ['neutral']),
                                              State.State('WaitForBattle', self.enterWaitForBattle, self.exitWaitForBattle, ['Battle'])],
                                             'Off', 'Off')
            self.fsm.enterInitialState()

        return

    def generate(self):
        self.notify.debug('DLBS.generate:')
        DistributedSuitBase.DistributedSuitBase.generate(self)

    def announceGenerate(self):
        DistributedSuitBase.DistributedSuitBase.announceGenerate(self)
        self.notify.debug('DLBS.announceGenerate')

        colNode = self.find('**/distAvatarCollNode*')
        colNode.setTag('pieCode', str(ToontownGlobals.PieCodeLawyer))

        self.attackEvidenceA, self.attackEvidenceCollisionA = self.getEvidence(True)
        self.attackEvidenceB, self.attackEvidenceCollisionB = self.getEvidence(True)
        self.attackEvidence = self.attackEvidenceA
        self.attackEvidenceCollision = self.attackEvidenceCollisionA
        self.prosecuteEvidence, collision = self.getEvidence(False)

        self.hideName()

        # Generate three icons over the lawyers head to show it's mode
        labels = (TTLocalizer.LawbotArenaAttackingBoth, TTLocalizer.LawbotArenaAttackingToon,
                  TTLocalizer.LawbotArenaAttackingBoss)
        for state in range(len(labels)):
            texture = loader.loadTexture('phase_11/maps/LB_Arena_Button_{}.png'.format(state + 1))
            texture = OnscreenImage(texture)
            texture.setTransparency(1)
            name = self.uniqueName('mode_'.format(state))
            icon = NodePath(name)
            icon.setBillboardAxis()
            icon.reparentTo(self.nametag.getNameIcon())
            icon.setZ(3.5)
            icon.setScale(2.25)
            icon.hide()
            self.icons.append(icon)
            texture.reparentTo(icon)

        # Enable toon collisions
        self.enableBattleDetect('walk', self.__handleToonCollision)

        # Set starting hp to 0
        self.currHP = 0

    def disable(self):
        self.notify.debug('DistributedSuit %d: disabling' % self.getDoId())
        self.setState('Off')

        DistributedSuitBase.DistributedSuitBase.disable(self)

        self.cleanupIntervals()
        self.boss = None

    def delete(self):
        try:
            self.DistributedSuit_deleted
        except:
            self.DistributedSuit_deleted = 1
            self.notify.debug('DistributedSuit %d: deleting' % self.getDoId())
            del self.fsm
            DistributedSuitBase.DistributedSuitBase.delete(self)

    def setTeam(self, team):
        self.team = team

    def getTeam(self):
        return self.team

    def setMode(self, mode):
        previousMode = self.getMode()
        self.mode = mode

        # Change the icon depending on the mode
        if self.icons:
            if self.boss.getTeam() == self.getTeam():
                oldIcon = self.icons[previousMode]
                oldIcon.hide()

                icon = self.icons[mode]
                icon.show()

    def getMode(self):
        return self.mode

    def setHP(self, hp):
        self.currHP = hp
        if hasattr(self, 'boss') and self.boss:
            # Make sure to only do this if the Toon is currently keyed into this particular lawyer's panel
            panel = base.cr.playGame.getPlace().avatarPanel
            if self == self.boss.activeLawyer and panel:
                panel.changeLawyerLevel(self)
            self.flashGreen()

    def setLevel(self, level):
        self.level = level

        # Change the lawyer's nametag
        nameWLevel = TTLocalizer.SuitBaseNameWithLevel % {'name': self._name, 'dept': self.getStyleDept(),
                                                          'level': level}
        self.setDisplayName(nameWLevel)

        # Make a "poof" effect when the level changes
        dustCloud = DustCloud.DustCloud(fBillboard=0, wantSound=1)
        dustCloud.setBillboardAxis(2.0)
        dustCloud.setZ(3)
        dustCloud.setScale(0.6)
        dustCloud.createTrack()

        ivalName = 'dustCloadIval'
        ival = Sequence(Func(dustCloud.reparentTo, self), dustCloud.track, Func(dustCloud.destroy), name=ivalName)
        ival.start()
        self.activeIntervals[ivalName] = ival

        # Satisfying sfx for leveling up the lawyer
        sfx = loader.loadSfx('phase_11/audio/sfx/LB_toon_jury.ogg')
        base.playSfx(sfx, node=self)

    def enableBattleDetect(self, name, handler):
        if self.collTube:
            self.battleDetectName = self.taskName(name)
            self.collNode = CollisionNode(self.battleDetectName)
            self.collNode.addSolid(self.collTube)
            self.collNodePath = self.attachNewNode(self.collNode)
            self.collNode.setCollideMask(ToontownGlobals.WallBitmask)
            self.accept('enter' + self.battleDetectName, handler, extraArgs=[True])
            self.accept('exit' + self.battleDetectName, handler, extraArgs=[False])
        return Task.done

    def disableBattleDetect(self):
        if self.battleDetectName:
            self.ignore('enter' + self.battleDetectName)
            self.ignore('exit' + self.battleDetectName)
            self.battleDetectName = None

        if self.collNodePath:
            self.collNodePath.removeNode()
            self.collNodePath = None

    def __handleToonCollision(self, state, collEntry=None):
        # We can't open up the lawyer panel if these aren't our lawyers
        if self.boss.getTeam() != self.getTeam():
            return

        if state:
            self.boss.handleClickedNametag(self)

        else:
            place = base.cr.playGame.getPlace()
            if hasattr(place, 'avatarPanel') and place.avatarPanel:
                if hasattr(place.avatarPanel, '_LawbotArenaLawyerInterface__handleClose'):
                    place.avatarPanel._LawbotArenaLawyerInterface__handleClose()
                # SuitAvatarPanel pops up for a split second so this is necessary
                elif hasattr(place.avatarPanel, '_SuitAvatarPanel__handleClose'):
                    place.avatarPanel._SuitAvatarPanel__handleClose()
                # Don't do anything if the current avatarPanel is some other type
                # like a ToonAvatarPanel or PetAvatarPanel

    def enterHidden(self):
        self.notify.debug('enterHidden')
        self.hide()

    def exitHidden(self):
        self.notify.debug('exitHidden')
        self.show()

    def enterFlyIn(self):
        self.notify.debug('enterFlyIn')
        for icon in self.icons:
            icon.hide()

        flyIn = self.beginSupaFlyMove(self.getPos(), 1, 'flyIn', False)
        self.flyIn = Sequence(Wait(4.0), flyIn, Func(self.loop, 'neutral', 0))
        self.flyIn.start()

    def exitFlyIn(self):
        self.notify.debug('exitFlyIn')
        if self.boss.getTeam() == self.getTeam():
            icon = self.icons[self.getMode()]
            icon.show()

        if hasattr(self, 'flyIn') and self.flyIn:
            self.flyIn.finish()
            del self.flyIn

    def enterNeutral(self):
        self.notify.debug('enterNeutral')
        self.loop('neutral', 0)

    def exitNeutral(self):
        self.notify.debug('exitNeutral')

    def doAttack(self, x1, y1, z1, x2, y2, z2):
        if self.dna.name == 'bf':
            self.throwPlayrate = 0.775

        self.curTargetPt = Point3(x2, y2, z2)
        self.fsm.request('PreThrowAttack')

    def doProsecute(self):
        self.notify.debug('doProsecute')

        if self.dna.name == 'bf':
            self.throwPlayrate = 0.775

        bounds = self.boss.prosecutionColNodePath.getBounds()
        panCenter = bounds.getCenter()
        localPos = panCenter

        team = self.getTeam()
        if team == ToontownGlobals.BossArenaTeamB:
            prosecutionPanPos = render.getRelativePoint(self.boss.prosecutionColNodePath, localPos)
        elif team == ToontownGlobals.BossArenaTeamA:
            prosecutionPanPos = render.getRelativePoint(self.boss.defenseColNodePath, localPos)
        else:
            return

        self.curTargetPt = prosecutionPanPos
        self.fsm.request('PreThrowProsecute')

    def makePreThrowAttackTrack(self, evidence, inFlightDuration, hitPos):
        # Clear attack tag on previous evidence collision
        if hasattr(self, 'attackEvidenceCollision') and self.attackEvidenceCollision:
            self.attackEvidenceCollision.clearTag('attackCode')

        suitTrack = Sequence()
        suitTrack.append(ActorInterval(self, 'throw-paper', endTime=self.timeToRelease, playRate=self.throwPlayrate))
        origHpr = self.getHpr()
        self.headsUp(hitPos)
        newHpr = self.getHpr()
        self.setHpr(origHpr)
        rotateTrack = Sequence(self.hprInterval(self.timeToShow, newHpr, fluid=1))
        propTrack = Sequence(Func(evidence.hide), Func(evidence.setPos, 0, 0.5, -0.3), Func(evidence.setScale, 1),
                             Func(evidence.setHpr, 0, 0, 0), Func(evidence.reparentTo, self.getRightHand()), Wait(self.timeToShow),
                             Func(evidence.show), Wait(self.timeToRelease - self.timeToShow))
        throwingTrack = Parallel(suitTrack, propTrack, rotateTrack)
        return throwingTrack

    def makePostThrowAttackTrack(self, evidence, inFlightDuration, hitPos):
        suitTrack = Sequence()
        suitTrack.append(ActorInterval(self, 'throw-paper', startTime=self.timeToRelease, playRate=self.throwPlayrate))
        propTrack = Sequence()
        if hasattr(self, 'attackEvidenceCollision') and self.attackEvidenceCollision:
            attackCode = ToontownGlobals.BossCogLawyerAttack

            propTrack.append(Func(self.attackEvidenceCollision.setTag, 'attackCode', str(attackCode)))
        propTrack.append(Sequence(Func(evidence.wrtReparentTo, render), Func(evidence.setScale, 1), Func(evidence.show),
                                  Func(evidence.setZ, 1.3), evidence.posInterval(inFlightDuration, hitPos, fluid=1), Func(evidence.hide)))
        return (suitTrack, propTrack)

    def makePreThrowProsecuteTrack(self, evidence, inFlightDuration, hitPos):
        return self.makePreThrowAttackTrack(evidence, inFlightDuration, hitPos)

    def makePostThrowProsecuteTrack(self, evidence, inFlightDuration, hitPos):
        suitTrack = Sequence()
        suitTrack.append(ActorInterval(self, 'throw-paper', startTime=self.timeToRelease, playRate=self.throwPlayrate))
        propTrack = Sequence(Func(evidence.wrtReparentTo, render), Func(evidence.setScale, 1), Func(evidence.show),
                             evidence.posInterval(inFlightDuration, hitPos, fluid=1), Func(evidence.hide))
        return (suitTrack, propTrack)

    def getEvidence(self, usedForAttack = False):
        # Evidence model
        model = loader.loadModel('phase_5/models/props/lawbook')
        collision = None

        # Only add collisions to the book if you aren't on this lawyer's team
        if usedForAttack:
            bounds = model.getBounds()
            center = bounds.getCenter()
            radius = bounds.getRadius()
            sphere = CollisionSphere(center.getX(), center.getY(), center.getZ(), radius)
            colNode = CollisionNode('BossZap')
            colNode.addSolid(sphere)
            collision = model.attachNewNode(colNode)
            model.setTransparency(1)
            model.setAlphaScale(0.5)

        return (model, collision)

    def cleanupIntervals(self):
        for interval in list(self.activeIntervals.values()):
            interval.finish()

        self.activeIntervals = {}

    def clearInterval(self, name, finish = 1):
        if name in self.activeIntervals:
            ival = self.activeIntervals[name]
            if finish:
                ival.finish()
            else:
                ival.pause()
            if name in self.activeIntervals:
                del self.activeIntervals[name]
        else:
            self.notify.debug('interval: %s already cleared' % name)

    def setBossCogId(self, bossCogId):
        self.bossCogId = bossCogId
        self.boss = base.cr.doId2do[bossCogId]

        # Now that we have the boss variable, we can find out our localAvatar's team
        if self.boss.getTeam() == self.getTeam():
            icon = self.icons[ToontownGlobals.LawbotArenaProsecutingBoth]
            icon.show()
        else:
            self.setPickable(False)

    def doStun(self):
        self.notify.debug('doStun')
        self.fsm.request('Stunned')

    def flashGreen(self):
        intervalName = self.uniqueName('FlashGreen')
        self.clearInterval(intervalName)
        self.setColorScale(1, 1, 1, 1)
        seq = Sequence(self.colorScaleInterval(0.1, colorScale=VBase4(0, 1, 0, 1)),
                       self.colorScaleInterval(0.3, colorScale=VBase4(1, 1, 1, 1)),
                       name=intervalName)
        seq.start()
        self.activeIntervals[intervalName] = seq

    def enterPreThrowProsecute(self):
        duration = ToontownGlobals.LawbotBossLawyerToPanTime
        throwName = self.uniqueName('preThrowProsecute')
        preThrowTrack = self.makePreThrowProsecuteTrack(self.prosecuteEvidence, duration, self.curTargetPt)
        fullSequence = Sequence(preThrowTrack, Func(self.requestStateIfNotInFlux, 'PostThrowProsecute'), name=throwName)
        self.activeIntervals[throwName] = fullSequence
        fullSequence.start()

    def exitPreThrowProsecute(self):
        throwName = self.uniqueName('preThrowProsecute')
        if throwName in self.activeIntervals:
            self.activeIntervals[throwName].pause()
            del self.activeIntervals[throwName]

    def enterPostThrowProsecute(self):
        duration = ToontownGlobals.LawbotBossLawyerToPanTime
        throwName = self.uniqueName('postThrowProsecute')
        postThrowTrack, self.flyingEvidenceTrack = self.makePostThrowProsecuteTrack(self.prosecuteEvidence, duration, self.curTargetPt)
        fullSequence = Sequence(postThrowTrack, Func(self.requestStateIfNotInFlux, 'neutral'), name=throwName)
        self.activeIntervals[throwName] = fullSequence
        fullSequence.start()
        flyName = self.uniqueName('flyingEvidence')
        self.activeIntervals[flyName] = self.flyingEvidenceTrack
        self.flyingEvidenceTrack.append(Func(self.finishedWithFlying, 'prosecute'))
        self.flyingEvidenceTrack.start()

    def exitPostThrowProsecute(self):
        throwName = self.uniqueName('postThrowProsecute')
        if throwName in self.activeIntervals:
            self.activeIntervals[throwName].finish()
            del self.activeIntervals[throwName]

    def requestStateIfNotInFlux(self, state):
        if not self.fsm._ClassicFSM__internalStateInFlux:
            self.fsm.request(state)

    def enterPreThrowAttack(self):
        if self.boss and self.boss.getTeam() == self.getTeam():
            self.attackEvidence = self.prosecuteEvidence
        elif self.attackEvidence == self.attackEvidenceA:
            self.attackEvidence = self.attackEvidenceB
            self.attackEvidenceCollision = self.attackEvidenceCollisionB
        else:
            self.attackEvidence = self.attackEvidenceA
            self.attackEvidenceCollision = self.attackEvidenceCollisionA

        colNode = self.attackEvidence.find('**/+CollisionNode')
        attackCode = ToontownGlobals.BossCogLawyerAttack
        if colNode:
            colNode.setTag('attackCode', str(attackCode))

        duration = 3.0
        throwName = self.uniqueName('preThrowAttack')
        preThrowTrack = self.makePreThrowAttackTrack(self.attackEvidence, duration, self.curTargetPt)
        fullSequence = Sequence(preThrowTrack, Func(self.requestStateIfNotInFlux, 'PostThrowAttack'), name=throwName)
        self.activeIntervals[throwName] = fullSequence
        fullSequence.start()

    def exitPreThrowAttack(self):
        throwName = self.uniqueName('preThrowAttack')
        if throwName in self.activeIntervals:
            self.activeIntervals[throwName].pause()
            del self.activeIntervals[throwName]

    def enterPostThrowAttack(self):
        duration = 3.0
        throwName = self.uniqueName('postThrowAttack')
        postThrowTrack, self.flyingEvidenceTrack = self.makePostThrowAttackTrack(self.attackEvidence, duration, self.curTargetPt)
        fullSequence = Sequence(postThrowTrack, Func(self.requestStateIfNotInFlux, 'neutral'), name=throwName)
        self.notify.debug('duration of postThrowAttack = %f' % fullSequence.getDuration())
        self.activeIntervals[throwName] = fullSequence
        fullSequence.start()
        flyName = self.uniqueName('flyingEvidence')
        self.activeIntervals[flyName] = self.flyingEvidenceTrack
        self.flyingEvidenceTrack.append(Func(self.finishedWithFlying, 'attack'))
        self.flyingEvidenceTrack.start()

    def finishedWithFlying(self, str):
        self.notify.debug('finished flyingEvidenceTrack %s' % str)

    def exitPostThrowAttack(self):
        throwName = self.uniqueName('postThrowAttack')
        if throwName in self.activeIntervals:
            self.activeIntervals[throwName].finish()
            del self.activeIntervals[throwName]

    def enterStunned(self):
        # Default stun duration
        duration = ToontownGlobals.LawbotArenaLawyerStunTime

        # Interval for being stunned
        stunSequence = Sequence(
            Parallel(
                MovieUtil.createSuitStunInterval(self, 0, duration),
                Func(self.loop, 'lured')
            ),
            Func(self.fsm.request, 'neutral')
        )
        seqName = stunSequence.getName()
        self.activeIntervals[seqName] = stunSequence
        stunSequence.start()

        # Darken the icon interface to show they aren't doing anything
        for icon in self.icons:
            icon.setColorScale(0.5, 0.5, 0.5, 1.0)

    def exitStunned(self):
        self.prosecuteEvidence.hide()
        self.attackEvidence.hide()

        # Set the current icon back to normal
        for icon in self.icons:
            icon.setColorScale(1.0, 1.0, 1.0, 1.0)
