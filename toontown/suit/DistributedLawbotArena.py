from direct.interval.IntervalGlobal import *
from otp.otpbase.PythonUtil import StackTrace
from direct.gui.DirectGui import *
from panda3d.core import *
from panda3d.toontown import NametagGroup, CFSpeech, CFTimeout, NametagGlobals
from direct.fsm import FSM
from direct.directnotify import DirectNotifyGlobal
from otp.otpbase.PythonUtil import cmp_to_key
from toontown.toonbase import ToontownGlobals, ToontownTimer, ControlManager
from . import DistributedBossCog, DistributedLawbotArenaSuit, LawbotArenaLawyerInterface
from toontown.toonbase import TTLocalizer
from . import SuitDNA
from toontown.toon import NPCToons
from direct.directutil import Mopath
from toontown.distributed import DelayDelete
from toontown.building import ElevatorConstants
OneBossCog = None


class DistributedLawbotArena(DistributedBossCog.DistributedBossCog, FSM.FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedLawbotArena')

    def __init__(self, cr):
        DistributedBossCog.DistributedBossCog.__init__(self, cr)
        FSM.FSM.__init__(self, 'DistributedLawbotArena')

        # Geometry & Constants
        self.elevatorType = ElevatorConstants.ELEVATOR_CJ
        self.mainDoor = None
        self.reflectedMainDoor = None

        # NPC Toons
        self.witnessToonA = None
        self.witnessToonAId = None
        self.witnessToonAName = ''
        self.witnessToonB = None
        self.witnessToonBId = None
        self.witnessToonAName = ''
        self.witnessToonsOnstage = False

        # Battle One
        self.lawyers = []
        self.lawyerRequest = None
        self.gavels = {}
        self.attackCode = None
        self.attackAvId = 0
        self.everThrownPie = 0
        self.everHitCog = 0
        self.foundRightPan = 0
        self.otherTeamStunned = 0
        self.foundLawyer = 0
        self.onscreenMessage = None
        self.battleOneMusicTime = 0
        self.bossDamage = 0
        self.bossMaxDamage = ToontownGlobals.LawbotArenaMaxDamage
        self.defensePanFlashInterval = None
        self.prosecutionPanFlashInterval = None
        self.panDamage = 3
        self.bonusState = ToontownGlobals.BossArenaNoTeam
        self.bonusTimer = None
        self.teamIcons = []
        self.baseColStashed = False
        self.pieTimestamp = None
        self.suddenDealthMultiplier = 1.0

        # Battle One SFX
        self.evidenceHitSfx = None
        self.toonUpSfx = None
        self.warningSfx = None
        self.suddenDeathSfx = None
        self.piesRestockSfx = None

        # Battle One Lawyer Interface
        self.activeLawyer = None

    def announceGenerate(self):
        # Instantiate the Boss Cog
        DistributedBossCog.DistributedBossCog.announceGenerate(self)

        # Set the Boss's name
        self.setName(TTLocalizer.LawbotBossName)
        nameInfo = TTLocalizer.BossCogNameWithDept % {'name': self._name, 'dept': SuitDNA.getDeptFullname(self.style.dept)}
        self.setDisplayName(nameInfo)

        # Load environment
        self.loadEnvironment()
        self.loadMopaths()
        self.makeWitnessToons()

        # Anything can be hit by a pie that isn't the Boss Cog
        render.setTag('pieCode', str(ToontownGlobals.PieCodeNotBossCog))

        # Load SFX
        self.evidenceHitSfx = loader.loadSfx('phase_11/audio/sfx/LB_evidence_hit.ogg')
        self.toonUpSfx = loader.loadSfx('phase_11/audio/sfx/LB_toonup.ogg')
        self.warningSfx = loader.loadSfx('phase_9/audio/sfx/CHQ_GOON_tractor_beam_alarmed.ogg')
        self.suddenDeathSfx = loader.loadSfx('phase_11/audio/sfx/LB_sparks_1.ogg')
        self.piesRestockSfx = loader.loadSfx('phase_5/audio/sfx/LB_receive_evidence.ogg')

        # Setup the Lawyer Interface behavior
        # Custom nametag click behavior for this scenario
        self.accept('clickedNametag', self.handleClickedNametag)

        # Load team icons
        for team in range(2):
            texture = loader.loadTexture('phase_11/maps/LB_Arena_Button_{}.png'.format(team + 2))
            texture = OnscreenImage(texture)
            texture.setTransparency(1)
            icon = DirectFrame(parent=base.a2dBottomRight, relief=None, image=texture, pos=(-0.173, 0, 0.4), scale=0.1)
            icon.hide()
            self.teamIcons.append(icon)
            texture.destroy()

        # Add Lawbot Arena speedchat menu
        localAvatar.chatMgr.chatInputSpeedChat.addLawbotArenaMenu()

        # Set OneBossCog flag
        global OneBossCog
        if OneBossCog:
            self.notify.warning('Multiple BossCogs visible!')
        OneBossCog = self

    def disable(self):
        DistributedBossCog.DistributedBossCog.disable(self)
        self.request('Off')

        self.unloadEnvironment()
        self.cleanupWitnessToons()
        self.__unloadMopaths()

        self.__clearOnscreenMessage()
        taskMgr.remove(self.uniqueName('PieAdvice'))
        render.clearTag('pieCode')

        self.cr.relatedObjectMgr.abortRequest(self.lawyerRequest)
        self.lawyerRequest = None

        # Cleanup UI
        self.cleanupToonIcons()

        self.promotionMusic.stop()
        self.stingMusic.stop()
        self.battleOneMusic.stop()

        if self.bonusTimer:
            self.bonusTimer.destroy()
            del self.bonusTimer

        if self.teamIcons:
            for icon in self.teamIcons:
                icon.destroy()
                del icon
        del self.teamIcons

        localAvatar.chatMgr.chatInputSpeedChat.removeLawbotArenaMenu()

        global OneBossCog
        if OneBossCog == self:
            OneBossCog = None

    def delete(self):
        DistributedBossCog.DistributedBossCog.delete(self)

    def d_hitBoss(self, bossDamage):
        self.sendUpdate('hitBoss', [bossDamage])

    def d_healBoss(self, bossHeal):
        self.sendUpdate('healBoss', [bossHeal])

    def d_hitToon(self, toonId):
        self.sendUpdate('hitToon', [toonId])

    def gotToon(self, toon):
        stateName = self.state
        if stateName == 'Elevator':
            self.placeToonInElevator(toon)

    def setLawyerIds(self, lawyerIds):
        self.lawyers = []
        self.cr.relatedObjectMgr.abortRequest(self.lawyerRequest)
        self.lawyerRequest = self.cr.relatedObjectMgr.requestObjects(lawyerIds, allCallback=self.__gotLawyers)

    def __gotLawyers(self, lawyers):
        self.lawyerRequest = None
        self.lawyers = lawyers
        for i in range(len(self.lawyers)):
            suit = self.lawyers[i]
            suit.fsm.request('hidden')
            suit.setBossCogId(self.doId)

    def setBossDamage(self, bossDamage):
        self.bossDamage = bossDamage
        taskName = 'RecoverBossDamage'
        taskMgr.remove(taskName)
        self.makeScaleReflectDamage()

    def getBossDamage(self):
        return self.bossDamage

    def getTeam(self, doId=None):
        if doId is None:
            doId = base.localAvatar.getDoId()
        if doId in self.toonsA:
            return ToontownGlobals.BossArenaTeamA
        elif doId in self.toonsB:
            return ToontownGlobals.BossArenaTeamB
        else:
            return ToontownGlobals.BossArenaNoTeam

    def __showOnscreenMessage(self, text):
        if self.onscreenMessage:
            self.onscreenMessage.destroy()
            self.onscreenMessage = None
        self.onscreenMessage = DirectLabel(text=text, text_fg=VBase4(1, 1, 1, 1), text_align=TextNode.ACenter, relief=None, pos=(0, 0, -0.725), scale=0.1)

    def __clearOnscreenMessage(self, task=None):
        if self.onscreenMessage:
            self.onscreenMessage.destroy()
            self.onscreenMessage = None
        if task:
            return task.done

    def __showWaitingMessage(self, task):
        self.__showOnscreenMessage(TTLocalizer.BuildingWaitingForVictors)
        return task.done

    def loadEnvironment(self):
        DistributedBossCog.DistributedBossCog.loadEnvironment(self)

        self.geom = loader.loadModel('phase_11/models/lawbotHQ/LawbotCourtroom4')
        self.geom.setPos(0, 0, -71.601)
        self.geom.setScale(1)
        self.geom.find('**/EasterEgg1').removeNode()
        self.geom.find('**/EasterEgg2').removeNode()

        self.elevatorEntrance = self.geom.find('**/elevator_origin')
        self.elevatorEntrance.getChildren().detach()
        self.elevatorEntrance.setScale(1)
        elevatorModel = loader.loadModel('phase_11/models/lawbotHQ/LB_Elevator')
        elevatorModel.reparentTo(self.elevatorEntrance)
        self.setupElevator(elevatorModel)

        self.promotionMusic = base.loader.loadMusic('phase_7/audio/bgm/encntr_suit_winning_indoor.ogg')
        self.battleOneMusic = base.loader.loadMusic('phase_11/audio/bgm/LB_arena.ogg')

        floor = self.geom.find('**/MidVaultFloor1')
        if floor.isEmpty():
            floor = self.geom.find('**/CR3_Floor')
        self.evFloor = self.replaceCollisionPolysWithPlanes(floor)
        self.evFloor.reparentTo(self.geom)
        self.evFloor.setName('floor')
        plane = CollisionPlane(Plane(Vec3(0, 0, 1), Point3(0, 0, -50)))
        planeNode = CollisionNode('dropPlane')
        planeNode.addSolid(plane)
        planeNode.setCollideMask(ToontownGlobals.PieBitmask)
        self.geom.attachNewNode(planeNode)
        self.door3 = self.geom.find('**/SlidingDoor1/')
        if self.door3.isEmpty():
            self.door3 = self.geom.find('**/interior/CR3_Door')
        self.mainDoor = self.geom.find('**/Door_1')
        if not self.mainDoor.isEmpty():
            itemsToHide = ['interior/Door_1']
            for str in itemsToHide:
                stuffToHide = self.geom.find('**/%s' % str)
                if not stuffToHide.isEmpty():
                    self.notify.debug('found %s' % stuffToHide)
                    stuffToHide.wrtReparentTo(self.mainDoor)
                else:
                    self.notify.debug('not found %s' % stuffToHide)

        self.reflectedMainDoor = self.geom.find('**/interiorrefl/CR3_Door')
        if not self.reflectedMainDoor.isEmpty():
            itemsToHide = ['Reflections/Door_1']
            for str in itemsToHide:
                stuffToHide = self.geom.find('**/%s' % str)
                if not stuffToHide.isEmpty():
                    self.notify.debug('found %s' % stuffToHide)
                    stuffToHide.wrtReparentTo(self.reflectedMainDoor)
                else:
                    self.notify.debug('not found %s' % stuffToHide)

        self.geom.reparentTo(render)
        self.loadWitnessStand()
        self.loadScale()
        self.scaleNodePath.stash()
        self.loadJuryBox()
        self.loadPodium()
        ug = self.geom.find('**/Reflections')
        ug.setBin('ground', -10)

    def placeToonInElevator(self, toon):
        self.putToonInCogSuit(toon)
        toonIndex = self.involvedToons.index(toon.doId)
        toon.reparentTo(self.elevatorModel)
        toon.setPos(*ElevatorConstants.ArenaElevatorPoints[toonIndex])
        toon.setHpr(180, 0, 0)
        toon.suit.loop('neutral')

    def loadJuryBox(self):
        self.juryBox = self.geom.find('**/JuryBox')
        self.reflectedJuryBox = self.geom.find('**/JuryBox_Geo_Reflect')
        self.reflectedJuryBox.setZ(self.reflectedJuryBox.getZ() + ToontownGlobals.LawbotBossJuryBoxRelativeEndPos[2])

    def loadPodium(self):
        self.podium = self.geom.find('**/Podium')
        newZ = self.podium.getZ() - ToontownGlobals.LawbotBossBattleTwoPosHpr[2]
        self.podium.setZ(newZ)

        self.reflectedPodium = self.geom.find('**/Podium_Geo1_Refl')
        reflectedZ = self.reflectedPodium.getZ()
        self.reflectedPodium.setZ(reflectedZ)

    def loadWitnessStand(self):
        # Setup pie-obtaining collisions for Team A's witness stand
        self.realWitnessStand = self.geom.find('**/WitnessStand')
        colNode = self.realWitnessStand.find('**/witnessStandCollisions/Witnessstand_Collision')
        colNode.setName('WitnessStand')

        # Setup pie-obtaining collisions for Team A's witness stand
        self.realWitnessStandB = self.geom.find('**/WitnessStandB')
        colNode = self.realWitnessStandB.find('**/witnessStandCollisionsB/Witnessstand_CollisionB')
        colNode.setName('WitnessStandB')

    def loadScale(self):
        self.scaleNodePath = loader.loadModel('phase_11/models/lawbotHQ/scale')
        self.beamNodePath = self.scaleNodePath.find('**/scaleBeam')
        self.defensePanNodePath = self.scaleNodePath.find('**/defensePan')
        self.prosecutionPanNodePath = self.scaleNodePath.find('**/prosecutionPan')
        self.defenseColNodePath = self.scaleNodePath.find('**/DefenseCol')
        self.defenseColNodePath.setTag('pieCode', str(ToontownGlobals.PieCodeDefensePan))
        self.prosecutionColNodePath = self.scaleNodePath.find('**/ProsecutionCol')
        self.prosecutionColNodePath.setTag('pieCode', str(ToontownGlobals.PieCodeProsecutionPan))
        self.standNodePath = self.scaleNodePath.find('**/scaleStand')
        self.scaleNodePath.setPosHpr(*ToontownGlobals.LawbotBossInjusticePosHpr)
        self.defenseLocator = self.scaleNodePath.find('**/DefenseLocator')
        defenseLocBounds = self.defenseLocator.getBounds()
        defenseLocPos = defenseLocBounds.getCenter()
        self.notify.debug('defenseLocatorPos = %s' % defenseLocPos)
        self.defensePanNodePath.setPos(defenseLocPos)
        self.defensePanNodePath.reparentTo(self.beamNodePath)
        self.notify.debug('defensePanNodePath.getPos()=%s' % self.defensePanNodePath.getPos())
        self.prosecutionLocator = self.scaleNodePath.find('**/ProsecutionLocator')
        prosecutionLocBounds = self.prosecutionLocator.getBounds()
        prosecutionLocPos = prosecutionLocBounds.getCenter()
        self.notify.debug('prosecutionLocatorPos = %s' % prosecutionLocPos)
        self.prosecutionPanNodePath.setPos(prosecutionLocPos)
        self.prosecutionPanNodePath.reparentTo(self.beamNodePath)
        self.beamLocator = self.scaleNodePath.find('**/StandLocator1')
        beamLocatorBounds = self.beamLocator.getBounds()
        beamLocatorPos = beamLocatorBounds.getCenter()
        negBeamLocatorPos = -beamLocatorPos
        self.notify.debug('beamLocatorPos = %s' % beamLocatorPos)
        self.notify.debug('negBeamLocatorPos = %s' % negBeamLocatorPos)
        self.beamNodePath.setPos(beamLocatorPos)
        self.scaleNodePath.setScale(*ToontownGlobals.LawbotBossInjusticeScale)
        self.scaleNodePath.wrtReparentTo(self.geom)
        self.baseHighCol = self.scaleNodePath.find('**/BaseHighCol')
        oldBitMask = self.baseHighCol.getCollideMask()
        newBitMask = oldBitMask & ~ToontownGlobals.PieBitmask
        newBitMask = newBitMask & ~ToontownGlobals.CameraBitmask
        self.baseHighCol.setCollideMask(newBitMask)
        self.defenseHighCol = self.scaleNodePath.find('**/DefenseHighCol')
        self.defenseHighCol.stash()
        self.defenseHighCol.setCollideMask(newBitMask)
        self.baseTopCol = self.scaleNodePath.find('**/Scale_base_top_collision')
        self.baseSideCol = self.scaleNodePath.find('**/Scale_base_side_col')
        self.defenseLocator.hide()
        self.prosecutionLocator.hide()
        self.beamLocator.hide()

    def setScaleTilt(self, tilt):
        self.beamNodePath.setP(tilt)
        self.defensePanNodePath.setP(-tilt)
        self.prosecutionPanNodePath.setP(-tilt)

    def stashBaseCol(self):
        if not self.baseColStashed:
            self.notify.debug('stashBaseCol')
            self.baseTopCol.stash()
            self.baseSideCol.stash()
            self.baseColStashed = True

    def unstashBaseCol(self):
        if self.baseColStashed:
            self.notify.debug('unstashBaseCol')
            self.baseTopCol.unstash()
            self.baseSideCol.unstash()
            self.baseColStashed = False

    def makeScaleReflectDamage(self):
        diffDamage = self.bossDamage - ToontownGlobals.LawbotArenaInitialDamage
        diffDamage *= 1.0
        if diffDamage >= 0:
            percentDamaged = diffDamage / (ToontownGlobals.LawbotArenaMaxDamage - ToontownGlobals.LawbotArenaInitialDamage)
            tilt = percentDamaged * ToontownGlobals.LawbotBossWinningTilt
        else:
            percentDamaged = diffDamage / (ToontownGlobals.LawbotArenaInitialDamage - 0)
            tilt = percentDamaged * ToontownGlobals.LawbotBossWinningTilt
        self.setScaleTilt(tilt)
        if self.bossDamage < ToontownGlobals.LawbotArenaMaxDamage * 0.85:
            self.unstashBaseCol()
        else:
            self.stashBaseCol()

    def unloadEnvironment(self):
        DistributedBossCog.DistributedBossCog.unloadEnvironment(self)
        self.geom.removeNode()
        del self.geom

    def loadMopaths(self):
        self.toonsEnterA = Mopath.Mopath()
        self.toonsEnterA.loadFile('phase_9/paths/bossBattle-toonsEnterA')
        self.toonsEnterA.fFaceForward = 1
        self.toonsEnterA.timeScale = 35
        self.toonsEnterB = Mopath.Mopath()
        self.toonsEnterB.loadFile('phase_9/paths/bossBattle-toonsEnterB')
        self.toonsEnterB.fFaceForward = 1
        self.toonsEnterB.timeScale = 35

    def __unloadMopaths(self):
        self.toonsEnterA.reset()
        self.toonsEnterB.reset()

    def handleClickedNametag(self, avatar):
        self.notify.debug('handleClickedNametag')
        if self.state != 'BattleOne':
            return
        if self.cr:
            place = self.cr.playGame.getPlace()
            if place and hasattr(place, 'fsm'):
                if isinstance(avatar, DistributedLawbotArenaSuit.DistributedLawbotArenaSuit):
                    def doStuff():
                        if hasattr(place, 'avatarPanel') and place.avatarPanel:
                            place.avatarPanel.cleanup()
                        place.avatarPanel = LawbotArenaLawyerInterface.LawbotArenaLawyerInterface(avatar, self)
                    # Hacky way to make this wait til after the main __handleClickedNametag
                    # function executes
                    Sequence(Wait(0.05), Func(doStuff)).start()

    def releaseToons(self, finalBattle = 0):
        DistributedBossCog.DistributedBossCog.releaseToons(self, finalBattle)

        # Take off transformations in-case they haven't been already
        for toonId in self.involvedToons:
            toon = self.cr.doId2do.get(toonId)
            if toon:
                toon.takeOffTransformation(ToontownGlobals.TransformationCog, effect=False)

    def enterOff(self):
        DistributedBossCog.DistributedBossCog.enterOff(self)

        if self.witnessToonA:
            self.witnessToonA.clearChat()

        if self.witnessToonB:
            self.witnessToonB.clearChat()

    def enterWaitForToons(self):
        DistributedBossCog.DistributedBossCog.enterWaitForToons(self)

        self.geom.hide()
        self.witnessToonA.removeActive()
        self.witnessToonB.removeActive()

    def exitWaitForToons(self):
        DistributedBossCog.DistributedBossCog.exitWaitForToons(self)

        self.geom.show()
        self.witnessToonA.addActive()
        self.witnessToonB.addActive()

    def enterElevator(self):
        DistributedBossCog.DistributedBossCog.enterElevator(self)

        self.witnessToonA.removeActive()
        self.witnessToonB.removeActive()

        self.reparentTo(render)
        self.setPosHpr(*ToontownGlobals.LawbotBossStartPosHpr)

        self.podium.setZ(0)

        # Set up the Boss Cog animations
        self.happy = 1
        self.raised = 1
        self.forward = 1
        self.doAnimate()

        if not self.mainDoor.isEmpty():
            self.mainDoor.stash()
        if not self.reflectedMainDoor.isEmpty():
            self.reflectedMainDoor.stash()

        # Position the camera correctly for the elevator
        base.camera.reparentTo(self.elevatorModel)
        base.camera.setPosHpr(0, 30, 8, 180, 0, 0)

    def exitElevator(self):
        DistributedBossCog.DistributedBossCog.exitElevator(self)

        self.witnessToonA.removeActive()
        self.witnessToonB.removeActive()

    def enterIntroduction(self):
        self.reparentTo(render)
        self.setPosHpr(*ToontownGlobals.LawbotBossBattleOnePosHpr)
        self.stopAnimate()

        self.showWitnessToons()

        DistributedBossCog.DistributedBossCog.enterIntroduction(self)

        base.playMusic(self.promotionMusic, looping=1, volume=0.9)

        if not self.mainDoor.isEmpty():
            self.mainDoor.stash()
        if not self.reflectedMainDoor.isEmpty():
            self.reflectedMainDoor.stash()

    def exitIntroduction(self):
        DistributedBossCog.DistributedBossCog.exitIntroduction(self)

        self.promotionMusic.stop()

        self.releaseToons(finalBattle=1)

        if not self.mainDoor.isEmpty():
            pass
        if not self.reflectedMainDoor.isEmpty():
            self.reflectedMainDoor.unstash()
        if not self.elevatorEntrance.isEmpty():
            pass

    def enterBattleOne(self):
        # We're not calling the superclass's enterBattleOne
        # because toonsToBattlePosition isn't necessary here
        # (in fact, it actually breaks since there can be more
        # than 8 toons)
        self.cleanupIntervals()
        self.releaseToons()

        # Show the scale
        self.scaleNodePath.unstash()

        # Position the Toon
        index = self.involvedToons.index(base.localAvatar.getDoId())
        if index > 7:
            offset = -10
        else:
            offset = 10
        pos = ToontownGlobals.LawbotArenaLawyerPosHprs[index]
        localAvatar.setPos(pos[0] + offset, pos[1], pos[2])

        # Set the camera back to normal
        base.localAvatar.attachCamera()
        base.localAvatar.activateCamera()       

        # Clear any remaining chat from the CJ
        self.clearChat()

        # Clear any remaining chat from the witness Toons
        self.witnessToonA.clearChat()
        self.witnessToonB.clearChat()

        self.reparentTo(render)

        self.happy = 1
        self.raised = 1
        self.forward = 1
        self.doAnimate()

        for i in range(len(self.lawyers)):
            suit = self.lawyers[i]
            suit.fsm.request('neutral')

        team = self.getTeam()

        # Load team icons for nametags
        for toonId in self.involvedToons:
            toon = self.cr.doId2do.get(toonId)
            if toon and self.getTeam(toonId) == team:
                toon.setCustomIcon(texturePath=('phase_11/maps/LB_Arena_Button_{}.png'.format(team + 2)), z=5, scale=1.5)

        # Team A can only obtain evidence from their witness stand, same for Team B
        if team == ToontownGlobals.BossArenaTeamA:
            self.accept('enterWitnessStand', self.__touchedWitnessStand)
            self.accept('enterWitnessStandB', self.__wrongWitnessStand)
        elif team == ToontownGlobals.BossArenaTeamB:
            self.accept('enterWitnessStand', self.__wrongWitnessStand)
            self.accept('enterWitnessStandB', self.__touchedWitnessStand)

        self.accept('pieSplat', self.__pieSplat)
        self.accept('localPieSplat', self.__localPieSplat)
        self.accept('outOfPies', self.__outOfPies)
        self.accept('begin-pie', self.__foundPieButton)
        self.accept('enterDefenseCol', self.__enterDefenseCol)
        self.accept('enterProsecutionCol', self.__enterProsecutionCol)
        taskMgr.doMethodLater(30, self.__howToGetPies, self.uniqueName('PieAdvice'))
        self.stickBossToFloor()
        self.setPosHpr(*ToontownGlobals.LawbotBossBattleThreePosHpr)
        self.bossMaxDamage = ToontownGlobals.LawbotArenaMaxDamage
        base.playMusic(self.battleOneMusic, looping=1, volume=1.1)
        self.showWitnessToons()
        NametagGlobals.setMasterArrowsOn(0)
        NametagGlobals.setMasterNametagsActive(1)

    def cleanupToonIcons(self):
        team = self.getTeam()

        for toonId in self.involvedToons:
            toon = self.cr.doId2do.get(toonId)
            if toon and self.getTeam(toonId) == team:
                toon.removeCustomIcon()

    def exitBattleOne(self):
        DistributedBossCog.DistributedBossCog.exitBattleOne(self)
        self.cleanupToonIcons()
        NametagGlobals.setMasterArrowsOn(1)
        bossDoneEventName = self.uniqueName('DestroyedBoss')
        self.ignore(bossDoneEventName)
        taskMgr.remove(self.uniqueName('StandUp'))
        self.ignore('enterWitnessStand')
        self.ignore('enterWitnessStandB')
        self.ignore('pieSplat')
        self.ignore('localPieSplat')
        self.ignore('outOfPies')
        self.ignore('begin-pie')
        self.ignore('enterDefenseCol')
        self.ignore('enterProsecutionCol')
        self.ignore('clickedNametag')
        self.__clearOnscreenMessage()
        taskMgr.remove(self.uniqueName('PieAdvice'))
        taskMgr.remove(self.uniqueName('UpgradeAdvice'))
        self.unstickBoss()
        taskName = 'RecoverBossDamage'
        taskMgr.remove(taskName)
        self.battleOneMusicTime = self.battleOneMusic.getTime()
        self.battleOneMusic.stop()
        return

    def enterVictory(self):
        self.cleanupIntervals()
        self.reparentTo(render)
        self.setPosHpr(*ToontownGlobals.LawbotBossBattleThreePosHpr)
        self.loop('neutral')
        self.clearChat()

        self.witnessToonA.clearChat()
        self.witnessToonB.clearChat()

        self.controlToons()
        self.setToonsToNeutral(self.involvedToons)
        self.happy = 1
        self.raised = 1
        self.forward = 1
        intervalName = 'VictoryMovie'
        seq = Sequence(self.makeWinnerMovie(ToontownGlobals.BossArenaTeamA), Func(self.__continueVictory), name=intervalName)
        seq.start()
        self.storeInterval(seq, intervalName)
        base.playMusic(self.battleOneMusic, looping=1, volume=0.9, time=self.battleOneMusicTime)

    def __continueVictory(self):
        self.doneBarrier('Victory')

    def exitVictory(self):
        self.stopAnimate()
        self.unstash()
        self.battleOneMusicTime = self.battleOneMusic.getTime()
        self.battleOneMusic.stop()

    def enterDefeat(self):
        self.cleanupIntervals()
        self.reparentTo(render)
        self.setPosHpr(*ToontownGlobals.LawbotBossBattleThreePosHpr)
        self.loop('neutral')
        self.clearChat()

        self.witnessToonA.clearChat()
        self.witnessToonB.clearChat()

        self.controlToons()
        self.setToonsToNeutral(self.involvedToons)
        self.happy = 1
        self.raised = 1
        self.forward = 1
        intervalName = 'DefeatMovie'
        seq = Sequence(self.makeWinnerMovie(ToontownGlobals.BossArenaTeamB), Func(self.__continueDefeat), name=intervalName)
        seq.start()
        self.storeInterval(seq, intervalName)
        base.playMusic(self.battleOneMusic, looping=1, volume=0.9, time=self.battleOneMusicTime)

    def __continueDefeat(self):
        self.doneBarrier('Defeat')

    def exitDefeat(self):
        self.stopAnimate()
        self.unstash()
        self.battleOneMusicTime = self.battleOneMusic.getTime()
        self.battleOneMusic.stop()

    def __outOfPies(self):
        self.__showOnscreenMessage(TTLocalizer.LawbotBossNeedMoreEvidence)
        taskMgr.doMethodLater(20, self.__howToGetPies, self.uniqueName('PieAdvice'))

    def __howToGetPies(self, task):
        self.__showOnscreenMessage(TTLocalizer.LawbotBossHowToGetEvidence)
        return task.done

    def __howToThrowPies(self, task):
        dialog = ControlManager.ControlManager.parseHotkeyString(TTLocalizer.LawbotBossHowToThrowPies, useGlyphs=True)
        self.__showOnscreenMessage(dialog)
        return task.done

    def __howToUpgrade(self, task):
        self.__showOnscreenMessage(TTLocalizer.LawbotArenaTipUpgrade)
        return task.done

    def __foundPieButton(self):
        self.everThrownPie = 1
        self.__clearOnscreenMessage()
        taskMgr.remove(self.uniqueName('PieAdvice'))

    def __foundUpgrade(self):
        self.everHitCog = 1
        self.__clearOnscreenMessage()
        taskMgr.remove(self.uniqueName('UpgradeAdvice'))

    def __foundRightPan(self):
        self.foundRightPan = 1
        self.__clearOnscreenMessage()

    def __wrongPan(self):
        if not self.foundRightPan:
            self.__showOnscreenMessage(TTLocalizer.LawbotArenaTipWrongPan)

    def __stunTip(self):
        self.otherTeamStunned = 1
        self.__showOnscreenMessage(TTLocalizer.LawbotArenaTipStun)

    def lawyerTip(self):
        self.foundLawyer = 1
        self.__showOnscreenMessage(TTLocalizer.LawbotArenaTipLawyer)

    def __wrongWitnessStand(self, entry):
        self.__showOnscreenMessage(TTLocalizer.LawbotArenaTipWrongStand)

    def __touchedWitnessStand(self, entry):
        self.sendUpdate('touchWitnessStand', [])
        self.__clearOnscreenMessage()
        team = self.getTeam()
        if team == ToontownGlobals.BossArenaTeamA:
            self.ignore('enterWitnessStandB')
        elif team == ToontownGlobals.BossArenaTeamB:
            self.ignore('enterWitnessStand')
        taskMgr.remove(self.uniqueName('PieAdvice'))
        base.playSfx(self.piesRestockSfx)
        if not self.everThrownPie:
            taskMgr.doMethodLater(30, self.__howToThrowPies, self.uniqueName('PieAdvice'))
        if not self.everHitCog:
            taskMgr.doMethodLater(45, self.__howToUpgrade, self.uniqueName('UpgradeAdvice'))

    def __pieSplat(self, toon, pieCode):
        if pieCode == ToontownGlobals.PieCodeDefensePan:
            if base.localAvatar.getDoId() not in self.toonsA:
                if toon == localAvatar:
                    self.__wrongPan()
                return
            self.flashRed()
            self.flashPanBlue()
            base.playSfx(self.evidenceHitSfx, node=self.defensePanNodePath, volume=0.25)
            if toon == localAvatar:
                self.__foundRightPan()
                self.d_hitBoss(self.panDamage)
        elif pieCode == ToontownGlobals.PieCodeProsecutionPan:
            if base.localAvatar.getDoId() not in self.toonsB:
                if toon == localAvatar:
                    self.__wrongPan()
                return
            self.flashGreen()
            self.flashPanOrange()
            base.playSfx(self.evidenceHitSfx, node=self.prosecutionPanNodePath, volume=0.25)
            if toon == localAvatar:
                self.__foundRightPan()
                self.d_healBoss(self.panDamage)
        elif pieCode == ToontownGlobals.PieCodeLawyer:
            pass

    def __localPieSplat(self, pieCode, entry, timestamp32):
        # Set a timestamp for this current pie so that it cannot be used multiple times for glitches
        if self.pieTimestamp == timestamp32:
            return

        self.pieTimestamp = timestamp32

        if pieCode == ToontownGlobals.PieCodeLawyer:
            self.__lawyerGotHit(entry)
        if pieCode != ToontownGlobals.PieCodeToon:
            return
        avatarDoId = entry.getIntoNodePath().getNetTag('avatarDoId')
        if avatarDoId == '':
            self.notify.warning('Toon %s has no avatarDoId tag.' % repr(entry.getIntoNodePath()))
            return
        doId = int(avatarDoId)
        if doId != localAvatar.doId:
            self.d_hitToon(doId)

    def __lawyerGotHit(self, entry):
        lawyerCol = entry.getIntoNodePath()
        names = lawyerCol.getName().split('-')
        lawyerDoId = int(names[1])
        for lawyer in self.lawyers:
            if lawyerDoId == lawyer.doId:
                lawyer.sendUpdate('hitByToon', [])
                if lawyer.getTeam() == self.getTeam():
                    self.__foundUpgrade()

    def replaceCollisionPolysWithPlanes(self, model):
        newCollisionNode = CollisionNode('collisions')
        newCollideMask = BitMask32(0)
        planes = []
        collList = model.findAllMatches('**/+CollisionNode')
        if not collList:
            collList = [model]
        for cnp in collList:
            cn = cnp.node()
            if not isinstance(cn, CollisionNode):
                self.notify.warning('Not a collision node: %s' % repr(cnp))
                break
            newCollideMask = newCollideMask | cn.getIntoCollideMask()
            for i in range(cn.getNumSolids()):
                solid = cn.getSolid(i)
                if isinstance(solid, CollisionPolygon):
                    plane = Plane(solid.getPlane())
                    planes.append(plane)
                else:
                    self.notify.warning('Unexpected collision solid: %s' % repr(solid))
                    newCollisionNode.addSolid(plane)

        newCollisionNode.setIntoCollideMask(newCollideMask)
        threshold = 0.1
        planes.sort(key=cmp_to_key(lambda p1, p2: p1.compareTo(p2, threshold)))
        lastPlane = None
        for plane in planes:
            if lastPlane == None or plane.compareTo(lastPlane, threshold) != 0:
                cp = CollisionPlane(plane)
                newCollisionNode.addSolid(cp)
                lastPlane = plane

        return NodePath(newCollisionNode)

    def makeIntroductionMovie(self, delayDeletes):
        for toonId in self.involvedToons:
            toon = self.cr.doId2do.get(toonId)
            if toon:
                delayDeletes.append(DelayDelete.DelayDelete(toon, 'LawbotArena.makeIntroductionMovie'))

        upperDoor = self.geom.find('**/interior').find('**/CR3_Door')
        lowerDoor = self.geom.find('**/CR3_Door')

        def flyInLawyers():
            for i in range(len(self.lawyers)):
                suit = self.lawyers[i]
                suit.fsm.request('flyIn')

        movementIval = Sequence(Func(self.loop, 'Ff_neutral'), self.posInterval(5, (-3.00, 89.00, 21), (-3.00, 140, 21)))
        animationIval = Sequence(Func(self.loop, 'Ff_neutral'), Wait(3.0),
                                 ActorInterval(self, 'Ff_speech'), ActorInterval(self, 'Ff_speech'),
                                 ActorInterval(self, 'Ff_lookLt', duration=2.9),
                                 ActorInterval(self, 'Ff_lookLt', startFrame=74, endFrame=55),
                                 ActorInterval(self, 'Ff_lookLt', startFrame=55, endFrame=74),
                                 ActorInterval(self, 'Ff_lookLt', startFrame=74, endFrame=55),
                                 ActorInterval(self, 'Ff_lookLt', startFrame=55, endFrame=74),
                                 ActorInterval(self, 'Ff_lookLt', startFrame=74, endFrame=55),
                                 ActorInterval(self, 'Ff_lookLt', startFrame=55, endFrame=74),
                                 ActorInterval(self, 'Ff_lookLt', startTime=2.9, endTime=0),
                                 ActorInterval(self, 'Ff_speech', duration=11.5, loop=1), Wait(4.75),
                                 ActorInterval(self, 'Ff_lookRt', endTime=2.9),
                                 ActorInterval(self, 'Ff_lookRt', startTime=2.9, endTime=0),
                                 Func(self.loop, 'Ff_neutral'))
        treadIval = Sequence(Func(self.treadWheels, self, 5), Wait(13.5), Func(self.treadWheels, self, 9))
        doorIval = Sequence(Parallel(upperDoor.posInterval(2.5, (0.00, 2.50, 30.00), (0.00, 0, 0)),
                                     lowerDoor.posInterval(3.5, (0.00, 0.00, -32.00), (0.00, 0.00, 0))),
                            Parallel(upperDoor.posInterval(3, (.5, 0, 0)), lowerDoor.posInterval(3, (0, 0, 0))))
        cameraIval = Sequence(Func(base.camera.wrtReparentTo, render),
                              LerpPosHprInterval(base.camera, 6.0, (-3.00, 25.00, 30.00), (0.00, 8.00, 0.00), blendType='easeInOut'), Wait(0.5),
                              LerpPosHprInterval(base.camera, 5.0, (83.81, 70.00, 14.00), (70.00, 12.5, 0.0), blendType='easeInOut'), Wait(0.5),
                              LerpPosHprInterval(base.camera, 1.0, (69.00, 77.00, 16.00), (46.50, -1.50, 0.0), blendType='easeInOut'), Wait(3.0),
                              LerpPosHprInterval(base.camera, 1.0, (30.00, 82.77, 27.00), (77.5, 30.00, 0.0), blendType='easeInOut'), Wait(2.0),
                              LerpPosHprInterval(base.camera, 1.0, (-2.58, 50.00, 28.52), (0.0, 21.00, 0.0), blendType='easeInOut'), Wait(4.25),
                              Func(base.camera.setPosHpr, -3, -50, 6, 180, 5, 0),
                              Wait(3.0), Func(base.camera.setPosHpr, -2.58, 49.00, 28.52, 0.0, 21.00, 0.0),
                              Wait(3.9), Func(base.camera.setPosHpr, -74.89, 64.59, 16.3, -30.0, 1.0, 0.0), Wait(5.5),
                              LerpPosHprInterval(base.camera, 1.25, (-89.89, 61.47, 15.35), (-57.75, 7.75, 0.0), blendType='easeInOut'), Wait(4.0),
                              LerpPosHprInterval(base.camera, 1.0, (-2.58, 49.00, 28.52), (0.0, 23.5, 0.0), blendType='easeInOut'), Wait(12.0),
                              Func(flyInLawyers), LerpPosHprInterval(base.camera, 10.0, (-2.58, -89.16, 18.15), (0.0, -1.5, 0.0), blendType='easeInOut'),
                              Wait(1.0))
        dialogueIval = Track((3, Sequence(Func(self.setChatAbsolute, TTLocalizer.LawbotArenaIntro0, CFSpeech | CFTimeout), Wait(4.5), Func(self.clearChat))),
                             (9, Sequence(Func(self.setChatAbsolute, TTLocalizer.LawbotArenaIntro1, CFSpeech | CFTimeout), Wait(3.0), Func(self.clearChat))),
                             (12, Sequence(Func(self.witnessToonA.setChatAbsolute, TTLocalizer.LawbotArenaIntro2, CFSpeech | CFTimeout), Wait(4.0), Func(self.witnessToonA.clearChat))),
                             (16.0, Func(self.setChatAbsolute, TTLocalizer.LawbotArenaIntro3, CFSpeech | CFTimeout)),
                             (20.0, Func(self.setChatAbsolute, TTLocalizer.LawbotArenaIntro4, CFSpeech | CFTimeout)),
                             (24.0, Sequence(Func(self.clearChat), self.loseCogSuits(self.toonsA + self.toonsB, render, (-2.798, -8, 7, 180, 0, 0)))),
                             (26.0, Sequence(self.toonNormalEyes(self.involvedToons))),
                             (27.5, Sequence(Func(self.setChatAbsolute, TTLocalizer.LawbotArenaIntro5, CFSpeech | CFTimeout), Wait(3.5), Func(self.clearChat))),
                             (31.0, Func(self.witnessToonB.setChatAbsolute, TTLocalizer.LawbotArenaIntro6, CFSpeech | CFTimeout)),
                             (36.0, Sequence(Func(self.witnessToonB.setChatAbsolute, TTLocalizer.LawbotArenaIntro7, CFSpeech | CFTimeout), Wait(6.0), Func(self.witnessToonB.clearChat))),
                             (42.0, Func(self.setChatAbsolute, TTLocalizer.LawbotArenaIntro8, CFSpeech | CFTimeout)),
                             (47.0, Func(self.setChatAbsolute, TTLocalizer.LawbotArenaIntro9, CFSpeech | CFTimeout)),
                             (54.5, Func(self.setChatAbsolute, TTLocalizer.LawbotArenaIntro10, CFSpeech | CFTimeout)),
                             (59.0, Func(self.setChatAbsolute, TTLocalizer.LawbotArenaIntro11.format(self.witnessToonBName, self.witnessToonAName), CFSpeech | CFTimeout)))

        track = Parallel(movementIval, animationIval, cameraIval, doorIval, dialogueIval, treadIval)
        return Sequence(Func(self.stickToonsToFloor), track, Func(self.unstickToons),
                        name=self.uniqueName('Introduction'))

    def treadWheels(self, boss, duration):
        leftTread = boss.find('**/left_tread')
        rightTread = boss.find('**/right_tread')
        Ltread = NodePath('Ltread')
        Rtread = NodePath('Rtread')
        leftTread.setTexProjector(TextureStage.getDefault(), NodePath(), Ltread)
        rightTread.setTexProjector(TextureStage.getDefault(), NodePath(), Rtread)

        leftWheel = Ltread.posInterval(20, VBase3(-60, 0, 0))
        rightWheel = Rtread.posInterval(20, VBase3(-60, 0, 0))
        Sequence(Wait(duration), Func(leftWheel.finish), Func(rightWheel.finish)).start()
        leftWheel.loop()
        rightWheel.loop()

    def touchedGavel(self, gavel, entry):
        self.notify.debug('touchedGavel')
        attackCodeStr = entry.getIntoNodePath().getNetTag('attackCode')
        if attackCodeStr == '':
            self.notify.warning('Node %s has no attackCode tag.' % repr(entry.getIntoNodePath()))
            return
        attackCode = int(attackCodeStr)
        into = entry.getIntoNodePath()
        self.zapLocalToon(attackCode, into)

    def touchedGavelHandle(self, gavel, entry):
        attackCodeStr = entry.getIntoNodePath().getNetTag('attackCode')
        if attackCodeStr == '':
            self.notify.warning('Node %s has no attackCode tag.' % repr(entry.getIntoNodePath()))
            return
        attackCode = int(attackCodeStr)
        into = entry.getIntoNodePath()
        self.zapLocalToon(attackCode, into)

    def __enterDefenseCol(self, entry):
        self.notify.debug('__enterDefenseCol')

    def __enterProsecutionCol(self, entry):
        self.notify.debug('__enterProsecutionCol')

    def makeWinnerMovie(self, state):
        # Sfx for declaring the winner
        fanfareSfx = loader.loadSfx('phase_5/audio/sfx/SZ_MM_fanfare.ogg')

        # The winner's name
        if state == ToontownGlobals.BossArenaTeamA:
            winner = TTLocalizer.LawbotArenaToonsTeamName.format(self.witnessToonAName)
        elif state == ToontownGlobals.BossArenaTeamB:
            winner = TTLocalizer.LawbotArenaToonsTeamName.format(self.witnessToonBName)
        else:
            winner = TTLocalizer.LawbotArenaToonsUnknownName

        # The winner's icon
        if state != ToontownGlobals.BossArenaNoTeam:
            texture = loader.loadTexture('phase_11/maps/LB_Arena_Button_{}.png'.format(state + 2))
            texture = OnscreenImage(texture, scale=(0.01, 0.01, 0.01))
            texture.setTransparency(1)
            texture.hide()

            # Icon scale ival
            iconIval = Sequence(Func(fanfareSfx.play), Func(texture.show),
                                LerpScaleInterval(texture, 0.75, (0.4, 0.4, 0.4)),
                                LerpScaleInterval(texture, 0.5, (0.3, 0.3, 0.3)),
                                LerpScaleInterval(texture, 0.5, (0.4, 0.4, 0.4)),
                                LerpScaleInterval(texture, 0.5, (0.3, 0.3, 0.3)),
                                LerpScaleInterval(texture, 0.5, (0.4, 0.4, 0.4)),
                                LerpScaleInterval(texture, 0.5, (0.3, 0.3, 0.3)),
                                LerpScaleInterval(texture, 0.5, (0.4, 0.4, 0.4)),
                                LerpScaleInterval(texture, 0.5, (0.01, 0.01, 0.01)),
                                Func(texture.removeNode))
        else:
            iconIval = Sequence()

        # Interval
        bossTrack = Track((0.5, Sequence(Func(self.clearChat), Func(camera.reparentTo, render),
                                         Func(camera.setPos, -3, 45, 25), Func(camera.setHpr, 0, 10, 0))),
                          (1.0, Func(self.setChatAbsolute, TTLocalizer.LawbotArenaWinnerSpeech1, CFSpeech)),
                          (5.5, Func(self.setChatAbsolute, TTLocalizer.LawbotArenaWinnerSpeech2, CFSpeech)),
                          (9.5, Sequence(Func(self.setChatAbsolute, winner, CFSpeech), iconIval)),
                          (14.5, Func(self.setChatAbsolute, TTLocalizer.LawbotArenaWinnerSpeech3, CFSpeech)),
                          (18.0, Func(self.setChatAbsolute, TTLocalizer.LawbotArenaWinnerSpeech4, CFSpeech)),
                          (21.0, Sequence(Func(base.camera.reparentTo, localAvatar),
                                          Func(base.camera.setPos, localAvatar.cameraPositions[0][0]),
                                          Func(base.camera.setHpr, 0, 0, 0))))
        return bossTrack

    def setWitnessToonIds(self, witnessToonAId, witnessToonBId):
        self.witnessToonAId = witnessToonAId
        self.witnessToonBId = witnessToonBId

    def makeWitnessToons(self):
        # Create Witness Toon A and make him sit.
        self.witnessToonA = NPCToons.createLocalNPC(self.witnessToonAId)
        self.witnessToonA.setPosHpr(*ToontownGlobals.LawbotArenaWitnessStandAPosHpr)
        self.witnessToonA.animFSM.request('Sit')
        self.witnessToonAName = self.witnessToonA.getName()

        # Create Witness Toon B and make him sit.
        self.witnessToonB = NPCToons.createLocalNPC(self.witnessToonBId)
        self.witnessToonB.setPosHpr(*ToontownGlobals.LawbotArenaWitnessStandBPosHpr)
        self.witnessToonB.animFSM.request('Sit')
        self.witnessToonBName = self.witnessToonB.getName()

    def cleanupWitnessToons(self):
        self.hideWitnessToons()

        if self.witnessToonA:
            self.witnessToonA.removeActive()
            self.witnessToonA.delete()
            self.witnessToonA = None
            
        if self.witnessToonB:
            self.witnessToonB.removeActive()
            self.witnessToonB.delete()
            self.witnessToonB = None

    def showWitnessToons(self):
        if not self.witnessToonsOnstage:
            # Witness Toon A
            self.witnessToonA.addActive()
            self.witnessToonA.reparentTo(self.geom)
            seatCenter = self.realWitnessStand.find('**/witnessStandSeatEdge')
            center = seatCenter.getPos()
            self.notify.debug('center = %s' % center)
            self.witnessToonA.setPos(center)
            self.witnessToonA.setH(180)
            self.witnessToonA.setZ(self.witnessToonA.getZ() - 1.5)
            self.witnessToonA.setY(self.witnessToonA.getY() - 1.15)

            # Witness Toon B
            self.witnessToonB.addActive()
            self.witnessToonB.reparentTo(self.geom)
            seatCenter = self.realWitnessStandB.find('**/witnessStandSeatEdgeB')
            center = seatCenter.getPos()
            self.notify.debug('center = %s' % center)
            self.witnessToonB.setPos(center)
            self.witnessToonB.setH(180)
            self.witnessToonB.setZ(self.witnessToonB.getZ() - 1.5)
            self.witnessToonB.setY(self.witnessToonB.getY() - 1.15)

            self.witnessToonsOnstage = 1

    def hideWitnessToons(self):
        if self.witnessToonsOnstage:
            # Witness Toon A
            self.witnessToonA.removeActive()
            self.witnessToonA.detachNode()

            # Witness Toon B
            self.witnessToonB.removeActive()
            self.witnessToonB.detachNode()

            self.witnessToonsOnstage = 0

    def cleanupDefensePanFlash(self):
        if self.defensePanFlashInterval:
            self.defensePanFlashInterval.finish()
            self.defensePanFlashInterval = None
        return

    def flashPanBlue(self):
        self.cleanupDefensePanFlash()
        intervalName = 'FlashPanBlue'
        self.defensePanNodePath.setColorScale(1, 1, 1, 1)
        seq = Sequence(self.defensePanNodePath.colorScaleInterval(0.1, colorScale=VBase4(0, 0, 1, 1)), 
                       self.defensePanNodePath.colorScaleInterval(0.3, colorScale=VBase4(1, 1, 1, 1)), 
                       name=intervalName)
        self.defensePanFlashInterval = seq
        seq.start()
        self.storeInterval(seq, intervalName)

    def cleanupProsecutionPanFlash(self):
        if self.prosecutionPanFlashInterval:
            self.prosecutionPanFlashInterval.finish()
            self.prosecutionPanFlashInterval = None
        return

    def flashPanOrange(self):
        self.cleanupProsecutionPanFlash()
        intervalName = 'FlashPanOrange'
        self.prosecutionPanNodePath.setColorScale(1, 1, 1, 1)
        seq = Sequence(self.prosecutionPanNodePath.colorScaleInterval(0.1, colorScale=VBase4(245/255, 209/255, 66/255, 1)),
                       self.prosecutionPanNodePath.colorScaleInterval(0.3, colorScale=VBase4(1, 1, 1, 1)),
                       name=intervalName)
        self.prosecutionPanFlashInterval = seq
        seq.start()
        self.storeInterval(seq, intervalName)

    def saySomething(self, chatString):
        intervalName = 'ChiefJusticeTaunt'
        seq = Sequence(name=intervalName)
        seq.append(Func(self.setChatAbsolute, chatString, CFSpeech))
        seq.append(Wait(4.0))
        seq.append(Func(self.clearChat))
        oldSeq = self.activeIntervals.get(intervalName)
        if oldSeq:
            oldSeq.finish()
        seq.start()
        self.storeInterval(seq, intervalName)

    def setTaunt(self, tauntIndex, extraInfo):
        gotError = False
        if not hasattr(self, 'state'):
            self.notify.warning('returning from setTaunt, no attr state')
            gotError = True
        elif not self.state == 'BattleOne':
            self.notify.warning('returning from setTaunt, not in battle one state, state=' + str(self.state))
            gotError = True
        if not hasattr(self, 'nametag'):
            self.notify.warning('returning from setTaunt, no attr nametag')
            gotError = True
        if gotError:
            st = StackTrace()
            print(st)
            return
        chatString = TTLocalizer.LawbotArenaTaunts[1]
        if tauntIndex == 0:
            if extraInfo < len(self.involvedToons):
                toonId = self.involvedToons[extraInfo]
                toon = base.cr.doId2do.get(toonId)
                if toon:
                    chatString = TTLocalizer.LawbotArenaTaunts[tauntIndex] % toon.getName()
        else:
            chatString = TTLocalizer.LawbotArenaTaunts[tauntIndex]
        self.saySomething(chatString)

    def toonGotHealed(self, toonId):
        # Play a heal SFX on the Toon if they still exist
        toon = base.cr.doId2do.get(toonId)
        if toon:
            base.playSfx(self.toonUpSfx, node=toon)

    def hideBonusTimer(self, teamIcon):
        # Hide the bonus state timer if there is one
        if self.bonusTimer:
            self.bonusTimer.hide()

        # Hide team icon
        if teamIcon:
            teamIcon.hide()

        # Disable the bonus on the lawyer interface
        place = base.cr.playGame.getPlace()
        if isinstance(place.avatarPanel, LawbotArenaLawyerInterface.LawbotArenaLawyerInterface):
            place.avatarPanel.updateLawyerDamage()

    def enteredBonusState(self, team):
        # Set the bonus state
        self.bonusState = team

        # How are we in a bonus state that belongs to no team?
        if self.bonusState == ToontownGlobals.BossArenaNoTeam:
            return

        # Determine the Witness Toon based on the team who has the bonus
        if self.bonusState == ToontownGlobals.BossArenaTeamA:
            witnessToon = self.witnessToonA
        elif self.bonusState == ToontownGlobals.BossArenaTeamB:
            witnessToon = self.witnessToonB
        else:
            return

        # Make the Witness Toon say a phrase announcing the bonus
        witnessToon.clearChat()
        text = TTLocalizer.WitnessToonBonus % (ToontownGlobals.LawbotBossBonusWeightMultiplier, ToontownGlobals.LawbotBossBonusDuration)
        witnessToon.setChatAbsolute(text, CFSpeech | CFTimeout)

        # Play a SFX to signify the bonus
        base.playSfx(self.toonUpSfx)

        # Generate a bonus timer if there is not one already
        if not self.bonusTimer:
            self.bonusTimer = ToontownTimer.ToontownTimer()
            self.bonusTimer.posAboveMapButton()

        # Show team icon
        teamIcon = self.teamIcons[team]
        teamIcon.show()

        # Show and begin the bonus timer
        self.bonusTimer.show()
        self.bonusTimer.countdown(ToontownGlobals.LawbotBossBonusDuration)

        taskMgr.doMethodLater(ToontownGlobals.LawbotBossBonusDuration, self.hideBonusTimer, self.uniqueName('hideBonusTimer'), extraArgs=[teamIcon])

        # Show tip about stunning the cogs
        if self.bonusState != self.getTeam() and not self.otherTeamStunned:
            self.__stunTip()

    def setAttackCode(self, attackCode, avId = 0):
        DistributedBossCog.DistributedBossCog.setAttackCode(self, attackCode, avId)
        if attackCode == ToontownGlobals.BossCogAreaAttack:
            self.saySomething(TTLocalizer.LawbotBossAreaAttackTaunt)
            base.playSfx(self.warningSfx)

    def increaseSuddenDeath(self, multiplier):
        self.suddenDealthMultiplier = multiplier

        if multiplier == ToontownGlobals.LawbotArenaSuddenDeathInitialMultiplier:
            self.__showOnscreenMessage(TTLocalizer.LawbotArenaTipSuddenDeath)
            base.playSfx(self.suddenDeathSfx)
        else:
            self.__clearOnscreenMessage()
