from direct.gui.OnscreenText import OnscreenText
from panda3d.core import Point3, CollisionSphere, CollisionNode, BitMask32, Vec3, TextNode, Vec4, Point2
from otp.otpbase import OTPGlobals
from direct.interval.IntervalGlobal import Sequence, Parallel, SoundInterval
from direct.interval.FunctionInterval import Wait
from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from direct.gui import DirectLabel

from otp.otpbase.PythonUtil import bound
from toontown.toontowngui import TTDialog
from toontown.toontowngui.ServerTimeGui import ServerTimeGui
from toontown.toonbase import TTLocalizer, HotkeySettings
from toontown.toonbase import ToontownGlobals, ClientSettings, ControlManager
from toontown.parties.PublicPartyGui import PublicPartyGui
from toontown.parties import PartyGlobals
from toontown.toon import HealthForceAcknowledge
from toontown.toon import NPCForceAcknowledge

class DistributedPartyGate(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPartyGate')

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        self.publicPartyChooseGuiDoneEvent = 'doneChoosingPublicParty'
        self.publicPartyGui = PublicPartyGui(self.publicPartyChooseGuiDoneEvent)
        self.publicPartyGui.stash()
        self.loadClockSounds()
        self.hourSoundInterval = Sequence()
        self.accept('stoppedAsleep', self.handleSleep)
        self.hfaDoneEvent = 'hfaDoneEvent'
        self.npcfaDoneEvent = 'npcfaDoneEvent'

    def loadClockSounds(self):
        self.clockSounds = []
        for i in range(1, 13):
            if i < 10:
                si = '0%d' % i
            else:
                si = '%d' % i
            # clock03 was moved to phase_3 so it could be loaded for system messages
            # this is a special case to make sure it's actually loaded
            if si != '03':
                self.clockSounds.append(base.loader.loadSfx('phase_4/audio/sfx/clock%s.ogg' % si, manager = 'environment'))
            else:
                self.clockSounds.append(base.loader.loadSfx('phase_3/audio/sfx/clock03.ogg', manager = 'environment'))

    def generate(self):
        DistributedObject.DistributedObject.generate(self)
        loader = self.cr.playGame.hood.loader
        partyGate = loader.geom.find('**/partyGate_grp')
        if partyGate.isEmpty():
            self.notify.warning('Could not find partyGate_grp in loader.geom')
            return
        self.clockFlat = partyGate.find('**/clock_flat')
        collSphere = CollisionSphere(0, 0, 0, 6.9)
        collSphere.setTangible(1)
        self.partyGateSphere = CollisionNode('PartyGateSphere')
        self.partyGateSphere.addSolid(collSphere)
        self.partyGateCollNodePath = partyGate.find('**/partyGate_stepsLocator').attachNewNode(self.partyGateSphere)
        self.__enableCollisions()
        self.toontownTimeGui = ServerTimeGui(partyGate, hourCallback=self.hourChange)
        self.toontownTimeGui.setPos(partyGate.find('**/clockText_locator').getPos() + Point3(0.0, -0.04, -0.2))
        self.toontownTimeGui.setHpr(partyGate.find('**/clockText_locator').getHpr())
        self.toontownTimeGui.setScale(12.0, 1.0, 26.0)
        self.toontownTimeGui.amLabel.setPos(-0.035, 0, -0.032)
        self.toontownTimeGui.amLabel.setScale(0.5)
        self.setupSignText()
        self.partyGateStepsLocationNP = loader.geom.find('**/partyGate_stepsLocator')

    def setupSignText(self):
        loader = self.cr.playGame.hood.loader
        partyGate = loader.geom.find('**/partyGateSignGroup')
        if partyGate.isEmpty():
            self.notify.warning('Could not find partyGate_grp in loader.geom')
            return
        gateFont = ToontownGlobals.getMinnieFont()
        leftSign = partyGate.find('**/signTextL_locatorBack')
        signScale = 0.35
        wordWrap = 8
        leftText = DirectLabel.DirectLabel(parent=leftSign, pos=(0, 0.04, 0.0), relief=None, text=TTLocalizer.PartyGateLeftSign, text_align=TextNode.ACenter, text_font=gateFont, text_wordwrap=wordWrap, text_fg=Vec4(0.7, 0.3, 0.3, 1.0), scale=signScale)
        rightSign = partyGate.find('**/signTextR_locatorFront')
        rightText = DirectLabel.DirectLabel(parent=rightSign, pos=(0, 0.04, 0.0), relief=None, text=TTLocalizer.PartyGateRightSign, text_align=TextNode.ACenter, text_font=gateFont, text_wordwrap=wordWrap, text_fg=Vec4(0.7, 0.3, 0.3, 1.0), scale=signScale)
        return

    def announceGenerate(self):
        DistributedObject.DistributedObject.announceGenerate(self)
        if self.zoneId in ToontownGlobals.dnaMap:
            playground = ToontownGlobals.dnaMap[self.zoneId]
        else:
            playground = ToontownGlobals.dnaMap[2000]
        self.toontownTimeGui.hourLabel['text_fg'] = PartyGlobals.PlayGroundToPartyClockColors[playground]
        self.toontownTimeGui.colonLabel['text_fg'] = PartyGlobals.PlayGroundToPartyClockColors[playground]
        self.toontownTimeGui.minutesLabel['text_fg'] = PartyGlobals.PlayGroundToPartyClockColors[playground]
        self.toontownTimeGui.amLabel['text_fg'] = PartyGlobals.PlayGroundToPartyClockColors[playground]

    def disable(self):
        DistributedObject.DistributedObject.disable(self)
        self.__disableCollisions()
        self.hourSoundInterval.finish()
        if self.publicPartyGui:
            self.publicPartyGui.stash()
            self.publicPartyGui.destroy()
            self.publicPartyGui = None

    def delete(self):
        DistributedObject.DistributedObject.delete(self)
        self.toontownTimeGui.destroy()
        del self.toontownTimeGui
        self.hourSoundInterval.finish()
        del self.hourSoundInterval
        del self.clockFlat
        if self.publicPartyGui:
            self.publicPartyGui.destroy()
            del self.publicPartyGui
        self.partyGateCollNodePath.removeNode()
        del self.partyGateCollNodePath
        self.ignoreAll()

    def showMessage(self, message):
        self.messageDoneEvent = self.uniqueName('messageDoneEvent')
        self.acceptOnce(self.messageDoneEvent, self.__handleMessageDone)
        self.messageGui = TTDialog.TTGlobalDialog(doneEvent=self.messageDoneEvent, message=message, style=TTDialog.Acknowledge)

    def __handleMessageDone(self):
        self.ignore(self.messageDoneEvent)
        self.freeAvatar()
        self.messageGui.cleanup()
        self.messageGui = None

    def __handleAskDone(self):
        DistributedPartyGate.notify.debug('__handleAskDone')
        self.ignore(self.publicPartyChooseGuiDoneEvent)
        doneStatus = self.publicPartyGui.doneStatus
        self.publicPartyGui.stash()
        if not doneStatus:
            self.freeAvatar()
            return
        self.__enterHFA()
        
    def __enterHFA(self):
        self.acceptOnce(self.hfaDoneEvent, self.__doHFACallback)
        self.hfa = HealthForceAcknowledge.HealthForceAcknowledge(self.hfaDoneEvent)
        self.hfa.enter(1)
        
    def __enterNPCFA(self):
        self.acceptOnce(self.npcfaDoneEvent, self.__doNPCFACallback)
        self.npcfa = NPCForceAcknowledge.NPCForceAcknowledge(self.npcfaDoneEvent)
        self.npcfa.enter()
        
    def __handleForceAcknowledgeComplete(self):
        doneStatus = self.publicPartyGui.doneStatus
        self.sendUpdate('partyChoiceRequest', [base.localAvatar.doId, doneStatus[0], doneStatus[1]])
        
    def __doHFACallback(self, doneStatus):
        self.hfa.exit()
        del self.hfa
        if doneStatus['mode'] == 'complete':
            self.__enterNPCFA()
        elif doneStatus['mode'] == 'incomplete':
            self.freeAvatar()
            return
        else:
            self.notify.error('Unknown done status for HealthForceAcknowledge: ' + repr(doneStatus))
            
    def __doNPCFACallback(self, doneStatus):
        self.npcfa.exit()
        del self.npcfa
        if doneStatus['mode'] == 'complete':
            self.__handleForceAcknowledgeComplete()
        elif doneStatus['mode'] == 'incomplete':
            self.freeAvatar()
            return
        else:
            self.notify.error('Unknown done status for NPCForceAcknowledge: ' + repr(doneStatus))

    def partyRequestDenied(self, reason):
        DistributedPartyGate.notify.debug('partyRequestDenied( reason=%s )' % PartyGlobals.PartyGateDenialReasons(reason).name)
        if reason == PartyGlobals.PartyGateDenialReasons.Unavailable:
            self.showMessage(TTLocalizer.PartyGatePartyUnavailable)
        elif reason == PartyGlobals.PartyGateDenialReasons.Full:
            self.showMessage(TTLocalizer.PartyGatePartyFull)

    def setParty(self, partyInfoTuple):
        DistributedPartyGate.notify.debug('setParty')
        self.freeAvatar()
        if partyInfoTuple[0] == 0:
            DistributedPartyGate.notify.debug('Public Party closed before toon could get to it.')
            return
        shardId, zoneId, numberOfGuests, hostName, activityIds, lane = partyInfoTuple
        if base.localAvatar.defaultShard == shardId:
            shardId = None
        base.cr.playGame.getPlace().requestLeave({'loader': 'safeZoneLoader',
         'where': 'party',
         'how': 'teleportIn',
         'hoodId': ToontownGlobals.PartyHood,
         'zoneId': zoneId,
         'shardId': shardId,
         'avId': -1})

    def freeAvatar(self):
        base.localAvatar.posCamera(0, 0)
        base.cr.playGame.getPlace().setState('walk')

    def hourChange(self, currentHour):
        currentHour = currentHour % 12
        if currentHour == 0:
            currentHour = 12
        self.hourSoundInterval = Parallel()
        seq1 = Sequence()
        for i in range(currentHour):
            seq1.append(SoundInterval(self.clockSounds[i]))
            seq1.append(Wait(0.2))

        timeForEachDeformation = seq1.getDuration() / currentHour
        seq2 = Sequence()
        for i in range(currentHour):
            seq2.append(self.clockFlat.scaleInterval(timeForEachDeformation / 2.0, Vec3(0.9, 1.0, 1.2), blendType='easeInOut'))
            seq2.append(self.clockFlat.scaleInterval(timeForEachDeformation / 2.0, Vec3(1.2, 1.0, 0.9), blendType='easeInOut'))

        seq2.append(self.clockFlat.scaleInterval(timeForEachDeformation / 2.0, Vec3(1.0, 1.0, 1.0), blendType='easeInOut'))
        self.hourSoundInterval.append(seq1)
        self.hourSoundInterval.append(seq2)
        self.hourSoundInterval.start()

    def handleEnterGateSphere(self, collEntry):
        if ClientSettings.ActivityInteraction.get():
            self.__createInteractHint()
        else:
            self.__interact()

    def handleExitGateSphere(self, collEntry = None):
        self.ignore('exitPartyGateSphere')
        self.__destroyInteractHint()

    def __interact(self):
        self.notify.debug('Entering steps Sphere....')
        base.cr.playGame.getPlace().fsm.request('stopped')
        self.sendUpdate('getPartyList', [base.localAvatar.doId])

    def listAllPublicParties(self, publicPartyInfo):
        self.notify.debug('listAllPublicParties : publicPartyInfo = %s' % publicPartyInfo)
        self.acceptOnce(self.publicPartyChooseGuiDoneEvent, self.__handleAskDone)
        self.publicPartyGui.refresh(publicPartyInfo)
        self.publicPartyGui.unstash()

    def __enableCollisions(self):
        self.accept('enterPartyGateSphere', self.handleEnterGateSphere)
        self.partyGateSphere.setCollideMask(OTPGlobals.WallBitmask)

    def __disableCollisions(self):
        self.ignore('enterPartyGateSphere')
        self.partyGateSphere.setCollideMask(BitMask32(0))

    def handleSleep(self):
        if hasattr(self, 'messageGui') and self.messageGui:
            self.__handleMessageDone()

    def __createInteractHint(self):
        if not hasattr(self, "interactHint"):
            self.accept(HotkeySettings.Interact.getPressed(),
                        self.__interact)
            self.accept('exitPartyGateSphere', self.handleExitGateSphere)
            self.accept('toonExitWalk', self.handleExitGateSphere)
            if self.zoneId in ToontownGlobals.dnaMap:
                playground = ToontownGlobals.dnaMap[self.zoneId]
            else:
                playground = ToontownGlobals.dnaMap[2000]
            text: str = ControlManager.ControlManager.parseHotkeyString(TTLocalizer.ActivityInteractParty, useGlyphs=True)
            self.interactHint = OnscreenText(text, style = 3, scale = .065, parent = base.a2dBottomCenter,
                                             font = ToontownGlobals.getMinnieFont(),
                                             fg = PartyGlobals.PlayGroundToPartyClockColors[playground],
                                             pos = (0.0, 0.0))

            taskMgr.add(self.__alignInteractHint, self.alignInteractHintTaskName)

    def __destroyInteractHint(self):
        self.ignore(HotkeySettings.Interact.getPressed())
        self.ignore('toonExitWalk')
        # Remove interact hint
        if hasattr(self, "interactHint"):
            taskMgr.remove(self.alignInteractHintTaskName)
            self.interactHint.removeNode()
            del self.interactHint

    def __alignInteractHint(self, task):
        """
        Aligns the interact hint on the screen
        The hint should be positioned on the npc, then the position is projected to the aspect2d
        """
        if hasattr(self, 'interactHint'):
            center = base.cam.getRelativePoint(self.partyGateStepsLocationNP, Point3(0, 0, 0.2))

            if base.camNode.isInView(center):
                center2d = Point2()
                base.camLens.project(center, center2d)

                center2d.x = bound(center2d.x, -0.7, 0.7)
                center2d.y = bound(center2d.y, -0.9, 0.95)
            else:
                # If the point isnt in the view, we set it to the 'default' position
                center2d = Point2(0.0, -0.45)

            self.interactHint.set_pos(render2d, Point3(center2d.x, 0, center2d.y))

        return task.cont

    @property
    def alignInteractHintTaskName(self):
        return f'alignInteractHint-{self.getDoId()}'

