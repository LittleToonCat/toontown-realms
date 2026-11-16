from direct.gui.DirectLabel import DirectLabel
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.MessengerGlobal import messenger
from direct.showbase.ShowBaseGlobal import render2d
from direct.task.TaskManagerGlobal import taskMgr
from panda3d.core import *
from panda3d.toontown import *
from direct.interval.IntervalGlobal import *
from direct.distributed.ClockDelta import *

from otp.otpbase.PythonUtil import bound
from toontown.toonbase import ToontownGlobals, HotkeySettings
from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.fsm import ClassicFSM, State
from direct.distributed import DistributedObject
from toontown.hood import ZoneUtil
from toontown.suit import Suit
from toontown.distributed import DelayDelete
from . import FADoorCodes
from direct.task.Task import Task
from . import DoorTypes
from toontown.toontowngui import TTDialog
from toontown.toonbase import TTLocalizer, ClientSettings, ControlManager
from toontown.distributed.DelayDeletable import DelayDeletable
from ..toonbase.ToonBaseGlobal import *

BldgNameStarters = ('toon_landmark', 'toon_interior')
AdjustTriggerTime = 0.5


class DistributedDoor(DistributedObject.DistributedObject, DelayDeletable):
    notify = directNotify.newCategory('DistributedDoor')

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        self.openSfx = base.loader.loadSfx('phase_3.5/audio/sfx/Door_Open_1.ogg', manager = 'environment')
        self.closeSfx = base.loader.loadSfx('phase_3.5/audio/sfx/Door_Close_1.ogg', manager = 'environment')
        self.nametag = None
        self.fsm = ClassicFSM.ClassicFSM('DistributedDoor_right',
                                         [State.State('off', self.enterOff, self.exitOff, ['closing',
                                                                                           'closed',
                                                                                           'opening',
                                                                                           'open']),
                                          State.State('closing', self.enterClosing, self.exitClosing,
                                                      ['closed', 'opening']),
                                          State.State('closed', self.enterClosed, self.exitClosed, ['opening']),
                                          State.State('opening', self.enterOpening, self.exitOpening, ['open']),
                                          State.State('open', self.enterOpen, self.exitOpen, ['closing', 'open'])],
                                         'off', 'off')
        self.fsm.enterInitialState()
        self.exitDoorFSM = ClassicFSM.ClassicFSM('DistributedDoor_left', [
            State.State('off', self.exitDoorEnterOff, self.exitDoorExitOff, ['closing',
                                                                             'closed',
                                                                             'opening',
                                                                             'open']),
            State.State('closing', self.exitDoorEnterClosing, self.exitDoorExitClosing, ['closed', 'opening']),
            State.State('closed', self.exitDoorEnterClosed, self.exitDoorExitClosed, ['opening']),
            State.State('opening', self.exitDoorEnterOpening, self.exitDoorExitOpening, ['open']),
            State.State('open', self.exitDoorEnterOpen, self.exitDoorExitOpen, ['closing', 'open'])], 'off', 'off')
        self.exitDoorFSM.enterInitialState()
        self.specialDoorTypes = {DoorTypes.EXT_HQ: 0,
                                 DoorTypes.EXT_COGHQ: 0,
                                 DoorTypes.INT_COGHQ: 0,
                                 DoorTypes.EXT_KS: 0,
                                 DoorTypes.INT_KS: 0
                                 }
        self.doorX = 1.5

    def generate(self):
        DistributedObject.DistributedObject.generate(self)
        self.avatarTracks = []
        self.avatarExitTracks = []
        self.avatarIDList = []
        self.avatarExitIDList = []
        self.doorTrack = None
        self.doorExitTrack = None

    def disable(self):
        self.clearNametag()
        taskMgr.remove(self.checkIsDoorHitTaskName())
        taskMgr.remove(self.getAdjustDoorTriggerTaskName())
        self.ignore(self.getEnterTriggerEvent())
        self.ignore(self.getExitTriggerEvent())
        self.ignore('clearOutToonInterior')
        self.fsm.request('off')
        self.exitDoorFSM.request('off')
        if 'building' in self.__dict__:
            del self.building
        self.finishAllTracks()
        self.avatarIDList = []
        self.avatarExitIDList = []
        if hasattr(self, 'tempDoorNodePath'):
            self.tempDoorNodePath.removeNode()
            del self.tempDoorNodePath
        DistributedObject.DistributedObject.disable(self)

    def delete(self):
        del self.fsm
        del self.exitDoorFSM
        del self.openSfx
        del self.closeSfx
        DistributedObject.DistributedObject.delete(self)

    def wantsNametag(self):
        return not ZoneUtil.isInterior(self.zoneId)

    def setupNametag(self):
        if self.nametag is None:
            self.nametag = NametagGroup()
            self.nametag.setFont(ToontownGlobals.getBuildingNametagFont())
            if TTLocalizer.BuildingNametagShadow:
                self.nametag.setShadow(*TTLocalizer.BuildingNametagShadow)
            self.nametag.setContents(Nametag.CName)
            self.nametag.setColorCode(NametagGroup.CCToonBuilding)
            self.nametag.setActive(0)
            self.nametag.setAvatar(self.getDoorNodePath())
            self.nametag.setObjectCode(self.block)
            name = self.cr.playGame.dnaStore.getTitleFromBlockNumber(self.block)
            if name is None:
                name = self.block
            self.nametag.setName(name)
            self.nametag.manage(base.marginManager)

            if not self.wantsNametag():
                self.nametag.getNametag2d().setContents(0)
        return

    def clearNametag(self):
        if self.nametag is not None:
            self.nametag.unmanage(base.marginManager)
            self.nametag.setAvatar(NodePath())
            self.nametag = None
        return

    def getTriggerName(self):
        if self.doorType == DoorTypes.INT_HQ or self.doorType in self.specialDoorTypes:
            return 'door_trigger_' + str(self.block) + '_' + str(self.doorIndex)
        else:
            return 'door_trigger_' + str(self.block)

    def getTriggerName_wip(self):
        name = 'door_trigger_%d' % (self.doId,)
        return name

    def getEnterTriggerEvent(self):
        return 'enter' + self.getTriggerName()

    def getExitTriggerEvent(self):
        return 'exit' + self.getTriggerName()

    def hideDoorParts(self):
        if self.doorType in self.specialDoorTypes:
            self.hideIfHasFlat(self.findDoorNode('rightDoor'))
            self.hideIfHasFlat(self.findDoorNode('leftDoor'))
            self.findDoorNode('doorFrameHoleRight').hide()
            self.findDoorNode('doorFrameHoleLeft').hide()
        else:
            return

    def setTriggerName(self):
        if self.doorType in self.specialDoorTypes:
            building = self.getBuilding()
            doorTrigger = building.find('**/door_' + str(self.doorIndex) + '/**/door_trigger*')
            doorTrigger.node().setName(self.getTriggerName())
        else:
            return

    def setTriggerName_wip(self):
        building = self.getBuilding()
        doorTrigger = building.find('**/door_%d/**/door_trigger_%d' % (self.doorIndex, self.block))
        if doorTrigger.isEmpty():
            doorTrigger = building.find('**/door_trigger_%d' % (self.block,))
        if doorTrigger.isEmpty():
            doorTrigger = building.find('**/door_%d/**/door_trigger_*' % (self.doorIndex,))
        if doorTrigger.isEmpty():
            doorTrigger = building.find('**/door_trigger_*')
        doorTrigger.node().setName(self.getTriggerName())

    def setZoneIdAndBlock(self, zoneId, block):
        self.zoneId = zoneId
        self.block = block

    def setDoorType(self, doorType):
        self.notify.debug('Door type = ' + str(doorType) + ' on door #' + str(self.doId))
        self.doorType = doorType

    def setDoorIndex(self, doorIndex):
        self.doorIndex = doorIndex

    def setSwing(self, flags):
        self.leftSwing = flags & 1 != 0
        self.rightSwing = flags & 2 != 0

    def setOtherZoneIdAndDoId(self, zoneId, distributedObjectID):
        self.otherZoneId = zoneId
        self.otherDoId = distributedObjectID

    def setState(self, state, timestamp):
        self.fsm.request(state, [globalClockDelta.localElapsedTime(timestamp)])

    def setExitDoorState(self, state, timestamp):
        self.exitDoorFSM.request(state, [globalClockDelta.localElapsedTime(timestamp)])

    def announceGenerate(self):
        DistributedObject.DistributedObject.announceGenerate(self)
        self.doPostAnnounceGenerate()

    def doPostAnnounceGenerate(self):
        if self.doorType in (DoorTypes.INT_STANDARD, DoorTypes.INT_TUTORIAL):
            self.bHasFlat = True
        else:
            self.bHasFlat = not self.findDoorNode('door*flat', True).isEmpty()
        self.hideDoorParts()
        self.setTriggerName()
        self.accept(self.getEnterTriggerEvent(), self.enterTrigger)
        self.acceptOnce('clearOutToonInterior', self.enterTrigger)
        self.setupNametag()
        # Delay this a bit because the Tutorial interior door actually loads before the geometry does
        taskMgr.doMethodLater(AdjustTriggerTime, self.__adjustTrigger, self.getAdjustDoorTriggerTaskName())

    def __adjustTrigger(self, task):
        # Adjust position of some door triggers for the hotkey so players don't have to run up against
        # the door to be inside the trigger
        bldgGeom = self.getBuilding()
        if bldgGeom.isEmpty():
            # This is necessary or it won't try to find the building again
            del self.building
            # Try this again if building wasn't returned
            task.delayTime = AdjustTriggerTime
            return task.again
        bldgName = bldgGeom.getName()
        for bldgNameStarter in BldgNameStarters:
            if bldgNameStarter in bldgName:
                trigger = bldgGeom.find('**/' + self.getTriggerName())
                if bldgName.endswith('toon_landmark_TT_bank_DNARoot'):
                    trigger.setY(trigger, -.2)
                elif 'toon_interior' in bldgName:
                    trigger.setX(trigger, .09)
                elif 'toon_landmark_DG_C1' in bldgName:
                    trigger.setScale(1.2)
                else:
                    trigger.setScale(1.01)
        return task.done

    def getBuilding(self):
        if 'building' not in self.__dict__:
            if self.doorType in (DoorTypes.INT_STANDARD, DoorTypes.INT_TUTORIAL):
                door = render.find('**/leftDoor;+s')
                self.building = door.getParent()
            elif self.doorType == DoorTypes.INT_HQ:
                door = render.find('**/door_0')
                self.building = door.getParent()
            elif self.doorType == DoorTypes.INT_KS:
                self.building = render.find('**/KartShop_Interior*')
            elif self.doorType in (DoorTypes.EXT_STANDARD, DoorTypes.EXT_HQ, DoorTypes.EXT_KS):
                self.building = self.cr.playGame.hood.loader.geom.find(
                    '**/??' + str(self.block) + ':*_landmark_*_DNARoot;+s')
                if self.building.isEmpty():
                    self.building = self.cr.playGame.hood.loader.geom.find(
                        '**/??' + str(self.block) + ':animated_building_*_DNARoot;+s')
            elif self.doorType in (DoorTypes.EXT_COGHQ, DoorTypes.INT_COGHQ):
                self.building = self.cr.playGame.hood.loader.geom
            else:
                self.notify.error('No such door type as ' + str(self.doorType))
        return self.building

    def readyToExit(self):
        base.transitions.fadeScreen(1.0)
        self.sendUpdate('requestExit')

    def avatarEnterDoorTrack(self, avatar, duration):
        trackName = 'avatarEnterDoor-%d-%d' % (self.doId, avatar.doId)
        track = Parallel(name = trackName)
        otherNP = self.getDoorNodePath()
        if hasattr(avatar, 'stopSmooth'):
            avatar.stopSmooth()
        if avatar.doId == base.localAvatar.doId:
            track.append(LerpPosHprInterval(nodePath = base.camera, other = avatar, duration = duration,
                                            pos = Point3(0, -8, avatar.getHeight()), hpr = VBase3(0, 0, 0),
                                            blendType = 'easeInOut'))
        finalPos = avatar.getParent().getRelativePoint(otherNP, Point3(self.doorX, 2, ToontownGlobals.FloorOffset))
        moveHere = Sequence(self.getAnimStateInterval(avatar, 'walk'),
                            LerpPosInterval(nodePath = avatar, duration = duration, pos = finalPos,
                                            blendType = 'easeIn'))
        track.append(moveHere)
        if avatar.doId == base.localAvatar.doId:
            track.append(
                Sequence(Wait(duration * 0.5), Func(base.transitions.irisOut, duration * 0.5), Wait(duration * 0.5),
                         Func(avatar.b_setParent, ToontownGlobals.SPHidden)))
        track.delayDelete = DelayDelete.DelayDelete(avatar, 'avatarEnterDoorTrack')
        return track

    def avatarEnqueueTrack(self, avatar, duration):
        if hasattr(avatar, 'stopSmooth'):
            avatar.stopSmooth()
        back = -5.0 - 2.0 * len(self.avatarIDList)
        if back < -9.0:
            back = -9.0
        offset = Point3(self.doorX, back, ToontownGlobals.FloorOffset)
        otherNP = self.getDoorNodePath()
        walkLike = ActorInterval(avatar, 'walk', startTime = 1, duration = duration, endTime = 0.0001)
        standHere = Sequence(LerpPosHprInterval(nodePath = avatar, other = otherNP, duration = duration, pos = offset,
                                                hpr = VBase3(0, 0, 0), blendType = 'easeInOut'),
                             self.getAnimStateInterval(avatar, 'neutral'))
        trackName = 'avatarEnqueueDoor-%d-%d' % (self.doId, avatar.doId)
        track = Parallel(walkLike, standHere, name = trackName)
        track.delayDelete = DelayDelete.DelayDelete(avatar, 'avatarEnqueueTrack')
        return track

    def getAnimStateInterval(self, avatar, animName):
        isSuit = isinstance(avatar, Suit.Suit)
        if isSuit:
            return Func(avatar.loop, animName, 0)
        else:
            return Func(avatar.setAnimState, animName)

    def isDoorHit(self):
        vec = base.localAvatar.getRelativeVector(self.currentDoorNp, self.currentDoorVec)
        netScale = self.currentDoorNp.getNetTransform().getScale()
        yToTest = vec.getY() / netScale[1]
        if ClientSettings.DoorInteraction.get():
            return True
        return yToTest < -0.5

    def enterDoor(self):
        messenger.send('DistributedDoor_doorTrigger')
        self.sendUpdate('requestEnter')

        self.__destroyInteractHint()

    def checkIsDoorHitTaskName(self):
        return 'checkIsDoorHit' + self.getTriggerName()

    def getAdjustDoorTriggerTaskName(self):
        return self.uniqueName('adjustDoorTriggerTask')

    def checkIsDoorHitTask(self, task):
        if self.isDoorHit():
            self.ignore(self.checkIsDoorHitTaskName())
            self.ignore(self.getExitTriggerEvent())
            self.enterDoor()
            return Task.done
        return Task.cont

    def cancelCheckIsDoorHitTask(self, args):
        taskMgr.remove(self.checkIsDoorHitTaskName())
        del self.currentDoorNp
        del self.currentDoorVec
        self.ignore(self.getExitTriggerEvent())
        self.accept(self.getEnterTriggerEvent(), self.enterTrigger)

    def enterTrigger(self, args = None):
        self.ignore(self.getEnterTriggerEvent())
        self.accept(self.getExitTriggerEvent(), self.exitTrigger)
        if args is None:
            self.enterDoor()
        else:
            self.currentDoorNp = NodePath(args.getIntoNodePath())
            self.currentDoorVec = Vec3(args.getSurfaceNormal(self.currentDoorNp))
            if self.isDoorHit():
                if ClientSettings.DoorInteraction.get():
                    self.createInteractHint()
                else:
                    self.enterDoor()
            else:
                self.accept(self.getExitTriggerEvent(), self.cancelCheckIsDoorHitTask)
                taskMgr.add(self.checkIsDoorHitTask, self.checkIsDoorHitTaskName())
        return

    def exitTrigger(self, e = None):
        """ Toon exits the trigger, used when door-interaction is enabled """
        self.accept(self.getEnterTriggerEvent(), self.enterTrigger)

        self.__destroyInteractHint()

    def avatarEnter(self, avatarID):
        avatar = self.cr.doId2do.get(avatarID, None)
        if avatar:
            avatar.setAnimState('neutral')
            track = self.avatarEnqueueTrack(avatar, 0.5)
            track.start()
            self.avatarTracks.append(track)
            self.avatarIDList.append(avatarID)
        return

    def rejectEnter(self, reason):
        message = FADoorCodes.reasonDict[reason]
        if message:
            self.__faRejectEnter(reason, message)
        else:
            self.__basicRejectEnter()

    def __basicRejectEnter(self):
        self.accept(self.getEnterTriggerEvent(), self.enterTrigger)
        if self.cr.playGame.getPlace():
            self.cr.playGame.getPlace().setState('walk')

    def __faRejectEnter(self, reason, message):
        self.rejectDialog = TTDialog.TTGlobalDialog(message = message, doneEvent = 'doorRejectAck',
                                                    style = TTDialog.Acknowledge)
        self.rejectDialog.show()
        self.rejectDialog.delayDelete = DelayDelete.DelayDelete(self, '__faRejectEnter')
        event = 'clientCleanup'
        self.acceptOnce(event, self.__handleClientCleanup)
        base.cr.playGame.getPlace().setState('stopped')
        self.acceptOnce('doorRejectAck', self.__handleRejectAck, extraArgs = [reason])
        self.acceptOnce('stoppedAsleep', self.__handleFallAsleepDoor)

    def __handleClientCleanup(self):
        if hasattr(self, 'rejectDialog') and self.rejectDialog:
            self.rejectDialog.doneStatus = 'ok'
        self.__handleRejectAck()

    def __handleFallAsleepDoor(self):
        self.rejectDialog.doneStatus = 'ok'
        self.__handleRejectAck()

    def __handleRejectAck(self, reason = 0):
        if reason and reason in FADoorCodes.uniqueRejects:
            base.localAvatar.b_setAnimState('neutral', 1)
            self.rejectDialog.hide()
            self.handleUniqueReject(reason)
            return

        self.ignore('doorRejectAck')
        self.ignore('stoppedAsleep')
        self.ignore('clientCleanup')
        doneStatus = self.rejectDialog.doneStatus
        if doneStatus != 'ok':
            self.notify.error('Unrecognized doneStatus: ' + str(doneStatus))
        self.__basicRejectEnter()
        if hasattr(self, 'rejectDialog') and self.rejectDialog:
            self.rejectDialog.delayDelete.destroy()
            self.rejectDialog.cleanup()
            del self.rejectDialog

    def handleUniqueReject(self, reason):
        if reason == FADoorCodes.LIGHTHOUSE_CLOSED:
            ival = Parallel()
            labels = []
            rejects = (TTLocalizer.GyroDoorReject_1, TTLocalizer.GyroDoorReject_2, TTLocalizer.GyroDoorReject_3)
            for text in rejects:
                label = DirectLabel(text = text, relief = None, parent = base.aspect2d,
                                    pos = ToontownGlobals.GyroDoorRejectLabelInfo[rejects.index(text)],
                                    text_font = ToontownGlobals.getMinnieFont(), text_fg = (1.0, 1.0, 1.0, 1.0),
                                    text_shadow = (0, 0, 0, 1))
                label.hide()
                labels.append(label)
                seq = Sequence(Wait(ToontownGlobals.GyroDoorRejectDelays[0][rejects.index(text)]), Func(label.show),
                               Parallel(Sequence(LerpScaleInterval(label, 0.8, scale = (0.3, 0.3, 0.3),
                                                                   startScale = (0.01, 0.01, 0.1)),
                                                 LerpScaleInterval(label, 0.3, scale = (0.25, 0.25, 0.25))),
                                        LerpHprInterval(label, 1.1, (0, 0, 0), startHpr = (1440, 0, 0),
                                                        blendType = 'easeOut')),
                               Wait(ToontownGlobals.GyroDoorRejectDelays[1][rejects.index(text)]))
                ival.append(seq)
            ival = Sequence(Wait(0.25), ival, Wait(1.0))
            parallel = Parallel()
            for label in labels:
                seq = Sequence(LerpColorScaleInterval(label, 1.5, colorScale = (1.0, 1.0, 1.0, 0.0)), Wait(0.25),
                               Func(label.destroy))
                parallel.append(seq)
            ival.append(parallel)
            ival.append(Func(self.__handleRejectAck))
            ival.start()

    def getDoorNodePath(self):
        if self.doorType in (DoorTypes.INT_STANDARD, DoorTypes.INT_TUTORIAL):
            otherNP = render.find('**/door_origin')
        elif self.doorType == DoorTypes.EXT_STANDARD:
            if hasattr(self, 'tempDoorNodePath'):
                return self.tempDoorNodePath
            else:
                posHpr = self.cr.playGame.dnaStore.getDoorPosHprFromBlockNumber(self.block)
                otherNP = NodePath('doorOrigin')
                otherNP.setPos(posHpr.getPos())
                otherNP.setHpr(posHpr.getHpr())
                self.tempDoorNodePath = otherNP
        elif self.doorType in self.specialDoorTypes:
            building = self.getBuilding()
            otherNP = building.find('**/door_origin_' + str(self.doorIndex))
        elif self.doorType == DoorTypes.INT_HQ:
            otherNP = render.find('**/door_origin_' + str(self.doorIndex))
        else:
            self.notify.error('No such door type as ' + str(self.doorType))
        return otherNP

    def avatarExitTrack(self, avatar, duration):
        if hasattr(avatar, 'stopSmooth'):
            avatar.stopSmooth()
        otherNP = self.getDoorNodePath()
        trackName = 'avatarExitDoor-%d-%d' % (self.doId, avatar.doId)
        track = Sequence(name = trackName)
        track.append(self.getAnimStateInterval(avatar, 'walk'))
        track.append(PosHprInterval(avatar, Point3(-self.doorX, 0, ToontownGlobals.FloorOffset), VBase3(179, 0, 0),
                                    other = otherNP))
        track.append(Func(avatar.setParent, ToontownGlobals.SPRender))
        if avatar.doId == base.localAvatar.doId:
            track.append(
                PosHprInterval(base.camera, VBase3(-self.doorX, 5, avatar.getHeight()), VBase3(180, 0, 0),
                               other = otherNP))
        if avatar.doId == base.localAvatar.doId:
            finalPos = render.getRelativePoint(otherNP, Point3(-self.doorX, -6, ToontownGlobals.FloorOffset))
        else:
            finalPos = render.getRelativePoint(otherNP, Point3(-self.doorX, -3, ToontownGlobals.FloorOffset))
        track.append(LerpPosInterval(nodePath = avatar, duration = duration, pos = finalPos, blendType = 'easeInOut'))
        if avatar.doId == base.localAvatar.doId:
            track.append(Func(self.exitCompleted))
            track.append(Func(base.transitions.irisIn))
        if hasattr(avatar, 'startSmooth'):
            track.append(Func(avatar.startSmooth))
        track.delayDelete = DelayDelete.DelayDelete(avatar, 'DistributedDoor.avatarExitTrack')
        return track

    def exitCompleted(self):
        base.localAvatar.setAnimState('neutral')
        place = self.cr.playGame.getPlace()
        if place:
            place.setState('walk')
        base.localAvatar.d_setParent(ToontownGlobals.SPRender)

    def avatarExit(self, avatarID):
        if avatarID in self.avatarIDList:
            self.avatarIDList.remove(avatarID)
            if avatarID == base.localAvatar.doId:
                self.exitCompleted()
        else:
            self.avatarExitIDList.append(avatarID)

    def finishDoorTrack(self):
        if self.doorTrack:
            self.doorTrack.finish()
        self.doorTrack = None
        return

    def finishDoorExitTrack(self):
        if self.doorExitTrack:
            self.doorExitTrack.finish()
        self.doorExitTrack = None
        return

    def finishAllTracks(self):
        self.finishDoorTrack()
        self.finishDoorExitTrack()
        for t in self.avatarTracks:
            t.finish()
            DelayDelete.cleanupDelayDeletes(t)

        self.avatarTracks = []
        for t in self.avatarExitTracks:
            t.finish()
            DelayDelete.cleanupDelayDeletes(t)

        self.avatarExitTracks = []

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    def getRequestStatus(self):
        zoneId = self.otherZoneId
        request = {'loader': ZoneUtil.getBranchLoaderName(zoneId),
                   'where': ZoneUtil.getToonWhereName(zoneId),
                   'how': 'doorIn',
                   'hoodId': ZoneUtil.getHoodId(zoneId),
                   'zoneId': zoneId,
                   'avId': -1,
                   'allowRedirect': 0,
                   'doorDoId': self.otherDoId
                   }
        return request

    def enterClosing(self, ts):
        def handleClosed():
            if hasattr(self, 'done'):
                request = self.getRequestStatus()
                messenger.send('doorDoneEvent', [request])

        doorFrameHoleRight = self.findDoorNode('doorFrameHoleRight')
        if doorFrameHoleRight.isEmpty():
            self.notify.warning('enterClosing(): did not find doorFrameHoleRight')
            handleClosed()
            return
        rightDoor = self.findDoorNode('rightDoor')
        if rightDoor.isEmpty():
            self.notify.warning('enterClosing(): did not find rightDoor')
            handleClosed()
            return
        otherNP = self.getDoorNodePath()
        trackName = 'doorClose-%d' % self.doId
        if self.rightSwing:
            h = 100
        else:
            h = -100
        self.finishDoorTrack()
        self.doorTrack = Sequence(
            LerpHprInterval(nodePath = rightDoor, duration = 1.0, hpr = VBase3(0, 0, 0), startHpr = VBase3(h, 0, 0),
                            other = otherNP, blendType = 'easeInOut'), Func(doorFrameHoleRight.hide),
            Func(self.hideIfHasFlat, rightDoor), SoundInterval(self.closeSfx, node = rightDoor), name = trackName)
        self.doorTrack.start(ts)
        handleClosed()

    def exitClosing(self):
        pass

    def enterClosed(self, ts):
        pass

    def exitClosed(self):
        pass

    def enterOpening(self, ts):
        doorFrameHoleRight = self.findDoorNode('doorFrameHoleRight')
        if doorFrameHoleRight.isEmpty():
            self.notify.warning('enterOpening(): did not find doorFrameHoleRight')
            return
        rightDoor = self.findDoorNode('rightDoor')
        if rightDoor.isEmpty():
            self.notify.warning('enterOpening(): did not find rightDoor')
            return
        otherNP = self.getDoorNodePath()
        trackName = 'doorOpen-%d' % self.doId
        if self.rightSwing:
            h = 100
        else:
            h = -100
        self.finishDoorTrack()
        self.doorTrack = Parallel(SoundInterval(self.openSfx, node = rightDoor),
                                  Sequence(HprInterval(rightDoor, VBase3(0, 0, 0), other = otherNP), Wait(0.4),
                                           Func(rightDoor.show), Func(doorFrameHoleRight.show),
                                           LerpHprInterval(nodePath = rightDoor, duration = 0.6, hpr = VBase3(h, 0, 0),
                                                           startHpr = VBase3(0, 0, 0), other = otherNP,
                                                           blendType = 'easeInOut')), name = trackName)
        self.doorTrack.start(ts)

    def exitOpening(self):
        pass

    def enterOpen(self, ts):
        for avatarID in self.avatarIDList:
            avatar = self.cr.doId2do.get(avatarID)
            if avatar:
                track = self.avatarEnterDoorTrack(avatar, 1.0)
                track.start(ts)
                self.avatarTracks.append(track)
            if avatarID == base.localAvatar.doId:
                self.done = 1

        self.avatarIDList = []

    def exitOpen(self):
        for track in self.avatarTracks:
            track.finish()
            DelayDelete.cleanupDelayDeletes(track)

        self.avatarTracks = []

    def exitDoorEnterOff(self):
        pass

    def exitDoorExitOff(self):
        pass

    def exitDoorEnterClosing(self, ts):
        doorFrameHoleLeft = self.findDoorNode('doorFrameHoleLeft')
        if doorFrameHoleLeft.isEmpty():
            self.notify.warning('enterOpening(): did not find flatDoors')
            return
        if self.leftSwing:
            h = -100
        else:
            h = 100
        leftDoor = self.findDoorNode('leftDoor')
        if not leftDoor.isEmpty():
            otherNP = self.getDoorNodePath()
            trackName = 'doorExitTrack-%d' % self.doId
            self.finishDoorExitTrack()
            self.doorExitTrack = Sequence(
                LerpHprInterval(nodePath = leftDoor, duration = 1.0, hpr = VBase3(0, 0, 0),
                                startHpr = VBase3(h, 0, 0),
                                other = otherNP, blendType = 'easeInOut'), Func(doorFrameHoleLeft.hide),
                Func(self.hideIfHasFlat, leftDoor), SoundInterval(self.closeSfx, node = leftDoor), name = trackName)
            self.doorExitTrack.start(ts)

    def exitDoorExitClosing(self):
        pass

    def exitDoorEnterClosed(self, ts):
        pass

    def exitDoorExitClosed(self):
        pass

    def exitDoorEnterOpening(self, ts):
        doorFrameHoleLeft = self.findDoorNode('doorFrameHoleLeft')
        if doorFrameHoleLeft.isEmpty():
            self.notify.warning('enterOpening(): did not find flatDoors')
            return
        leftDoor = self.findDoorNode('leftDoor')
        if self.leftSwing:
            h = -100
        else:
            h = 100
        if not leftDoor.isEmpty():
            otherNP = self.getDoorNodePath()
            trackName = 'doorDoorExitTrack-%d' % self.doId
            self.finishDoorExitTrack()
            self.doorExitTrack = Parallel(SoundInterval(self.openSfx, node = leftDoor),
                                          Sequence(Func(leftDoor.show), Func(doorFrameHoleLeft.show),
                                                   LerpHprInterval(nodePath = leftDoor, duration = 0.6,
                                                                   hpr = VBase3(h, 0, 0), startHpr = VBase3(0, 0, 0),
                                                                   other = otherNP, blendType = 'easeInOut')),
                                          name = trackName)
            self.doorExitTrack.start(ts)
        else:
            self.notify.warning('exitDoorEnterOpening(): did not find leftDoor')

    def exitDoorExitOpening(self):
        pass

    def exitDoorEnterOpen(self, ts):
        for avatarID in self.avatarExitIDList:
            avatar = self.cr.doId2do.get(avatarID)
            if avatar:
                track = self.avatarExitTrack(avatar, 0.2)
                track.start()
                self.avatarExitTracks.append(track)

        self.avatarExitIDList = []

    def exitDoorExitOpen(self):
        for track in self.avatarExitTracks:
            track.finish()
            DelayDelete.cleanupDelayDeletes(track)

        self.avatarExitTracks = []

    def findDoorNode(self, string, allowEmpty = False):
        building = self.getBuilding()
        if not building:
            self.notify.warning('getBuilding() returned None, avoiding crash, remark 896029')
            if self.doorType == DoorTypes.INT_TUTORIAL:
                allowEmpty = True
            foundNode = None
        else:
            foundNode = building.find('**/door_' + str(self.doorIndex) + '/**/' + string + '*;+s+i')
            if foundNode.isEmpty():
                foundNode = building.find('**/' + string + '*;+s+i')
        if allowEmpty and (not foundNode or foundNode.isEmpty()):
            return NodePath()
        return foundNode

    def hideIfHasFlat(self, node):
        if self.bHasFlat:
            node.hide()

    def __alignInteractHint(self, task):
        """
        Aligns the interact hint on the screen
        The hint should be positioned on the door, then the position is projected to the aspect2d
        """
        if hasattr(self, 'interactHint') and not self.getDoorNodePath().isEmpty():
            center = base.cam.getRelativePoint(self.getDoorNodePath(), Point3(0, 0, 3))

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

    def createInteractHint(self):
        if not hasattr(self, "interactHint"):
            self.accept(HotkeySettings.Interact.getPressed(),
                        self.enterDoor)
            self.accept('toonExitWalk', self.exitTrigger)
            name = self.cr.playGame.dnaStore.getTitleFromBlockNumber(self.block)
            state = TTLocalizer.DoorInteractExit if ZoneUtil.isInterior(self.zoneId) \
                else TTLocalizer.DoorInteractEnter
            if name != '':
                text = ControlManager.ControlManager.parseHotkeyString(TTLocalizer.DoorInteractNamed % (state, name),
                                                                       useGlyphs=True)
            else:
                text = ControlManager.ControlManager.parseHotkeyString(TTLocalizer.DoorInteractUnnamed % state, useGlyphs=True)

            if self.nametag:
                fg = NametagGlobals.getNameFg(self.nametag.getColorCode(), 3)
                font = self.nametag.getNameFont()
            else:
                fg = (1.0, 1.0, 1.0, 1.0)
                font = ToontownGlobals.getFancyFont()
            self.interactHint = OnscreenText(text, style = 3, scale = .065, parent = base.a2dBottomCenter,
                                             font = font, fg = fg, pos = (0.0, 0.0))

            taskMgr.add(self.__alignInteractHint, self.alignInteractHintTaskName)

    def __destroyInteractHint(self):
        self.ignore(HotkeySettings.Interact.getPressed())
        self.ignore('toonExitWalk')
        # Remove interact hint
        if hasattr(self, "interactHint"):
            taskMgr.remove(self.alignInteractHintTaskName)
            self.interactHint.removeNode()
            del self.interactHint

    @property
    def alignInteractHintTaskName(self):
        return f'alignInteractHint-{self.getDoId()}'
