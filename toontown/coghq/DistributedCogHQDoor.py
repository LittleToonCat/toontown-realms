from direct.gui.OnscreenText import OnscreenText
from panda3d.core import *
from direct.interval.IntervalGlobal import *
from direct.distributed.ClockDelta import *
from toontown.toonbase import ToontownGlobals, HotkeySettings, ControlManager
from toontown.building import DistributedDoor
from toontown.hood import ZoneUtil
from toontown.toonbase import TTLocalizer


class DistributedCogHQDoor(DistributedDoor.DistributedDoor):

    def __init__(self, cr):
        DistributedDoor.DistributedDoor.__init__(self, cr)
        self.openSfx = base.loader.loadSfx('phase_9/audio/sfx/CHQ_door_open.ogg')
        self.closeSfx = base.loader.loadSfx('phase_9/audio/sfx/CHQ_door_close.ogg')

    def wantsNametag(self):
        return 0

    def getRequestStatus(self):
        zoneId = self.otherZoneId
        request = {'loader': ZoneUtil.getBranchLoaderName(zoneId),
         'where': ZoneUtil.getToonWhereName(zoneId),
         'how': 'doorIn',
         'hoodId': ZoneUtil.getHoodId(zoneId),
         'zoneId': zoneId,
         'avId': -1,
         'allowRedirect': 0,
         'doorDoId': self.otherDoId}
        return request

    def enterClosing(self, ts):
        doorFrameHoleRight = self.findDoorNode('doorFrameHoleRight')
        if doorFrameHoleRight.isEmpty():
            self.notify.warning('enterClosing(): did not find doorFrameHoleRight')
            return
        rightDoor = self.findDoorNode('rightDoor')
        if rightDoor.isEmpty():
            self.notify.warning('enterClosing(): did not find rightDoor')
            return
        otherNP = self.getDoorNodePath()
        trackName = 'doorClose-%d' % self.doId
        if self.rightSwing:
            h = 100
        else:
            h = -100
        self.finishDoorTrack()
        self.doorTrack = Parallel(Sequence(LerpHprInterval(nodePath=rightDoor, duration=1.0, hpr=VBase3(0, 0, 0), startHpr=VBase3(h, 0, 0), other=otherNP, blendType='easeInOut'), Func(doorFrameHoleRight.hide), Func(self.hideIfHasFlat, rightDoor)), Sequence(Wait(0.5), SoundInterval(self.closeSfx, node=rightDoor)), name=trackName)
        self.doorTrack.start(ts)
        if hasattr(self, 'done'):
            request = self.getRequestStatus()
            messenger.send('doorDoneEvent', [request])

    def exitDoorEnterClosing(self, ts):
        doorFrameHoleLeft = self.findDoorNode('doorFrameHoleLeft')
        if doorFrameHoleLeft.isEmpty():
            self.notify.warning('enterOpening(): did not find flatDoors')
            return
        if ZoneUtil.isInterior(self.zoneId):
            doorFrameHoleLeft.setColor(1.0, 1.0, 1.0, 1.0)
        if self.leftSwing:
            h = -100
        else:
            h = 100
        leftDoor = self.findDoorNode('leftDoor')
        if not leftDoor.isEmpty():
            otherNP = self.getDoorNodePath()
            trackName = 'doorExitTrack-%d' % self.doId
            self.doorExitTrack = Parallel(Sequence(LerpHprInterval(nodePath=leftDoor, duration=1.0, hpr=VBase3(0, 0, 0), startHpr=VBase3(h, 0, 0), other=otherNP, blendType='easeInOut'), Func(doorFrameHoleLeft.hide), Func(self.hideIfHasFlat, leftDoor)), Sequence(Wait(0.5), SoundInterval(self.closeSfx, node=leftDoor)), name=trackName)
            self.doorExitTrack.start(ts)

    def setZoneIdAndBlock(self, zoneId, block):
        self.zoneId = zoneId
        self.block = block
        canonicalZoneId = ZoneUtil.getCanonicalZoneId(zoneId)
        if canonicalZoneId in (ToontownGlobals.BossbotHQ, ToontownGlobals.BossbotLobby):
            self.doorX = 1.0

    def enterTrigger(self, args = None):
        if localAvatar.hasActiveBoardingGroup():
            rejectText = TTLocalizer.BoardingCannotLeaveZone
            localAvatar.boardingParty.showMe(rejectText)
            return
        DistributedDoor.DistributedDoor.enterTrigger(self, args)

    def doPostAnnounceGenerate(self):
        DistributedDoor.DistributedDoor.doPostAnnounceGenerate(self)
        trigger = self.getBuilding().find('**/' + self.getTriggerName())
        # The cog hq's have some wacky triggers, so we have to adjust them so they
        # arent a pain when using door-interaction
        if self.zoneId == ToontownGlobals.LawbotHQ:
            trigger.setY(trigger, 3)
        elif self.zoneId == ToontownGlobals.CashbotHQ:
            trigger.setY(trigger, 4)
        elif self.zoneId == ToontownGlobals.CashbotLobby:
            trigger.setY(trigger, -1)
        elif self.zoneId == ToontownGlobals.SellbotHQ:
            trigger.setY(trigger, -1)

    def createInteractHint(self):
        if not hasattr(self, "interactHint"):
            self.accept(HotkeySettings.Interact.getPressed(),
                        self.enterDoor)
            self.accept('toonExitWalk', self.exitTrigger)
            name = '??'
            state = '??'

            if self.zoneId == ToontownGlobals.LawbotHQ:
                state = TTLocalizer.DoorInteractEnter
                if self.doorIndex == 0:  # DA OFFICE LOBBY
                    name = TTLocalizer.GlobalStreetNames[ToontownGlobals.LawbotOfficeExt][2]
                else:  # CJ LOBBY
                    name = TTLocalizer.GlobalStreetNames[ToontownGlobals.LawbotLobby][2]

            elif self.zoneId == ToontownGlobals.CashbotHQ:
                state = TTLocalizer.DoorInteractEnter
                name = TTLocalizer.GlobalStreetNames[ToontownGlobals.CashbotLobby][2]

            elif self.zoneId == ToontownGlobals.BossbotHQ:
                state = TTLocalizer.DoorInteractEnter
                name = TTLocalizer.GlobalStreetNames[ToontownGlobals.BossbotLobby][2]

            elif self.zoneId == ToontownGlobals.SellbotHQ:
                state = TTLocalizer.DoorInteractEnter
                name = TTLocalizer.GlobalStreetNames[ToontownGlobals.SellbotLobby][2]

            elif self.zoneId in (ToontownGlobals.LawbotOfficeExt,
                                 ToontownGlobals.LawbotLobby,
                                 ToontownGlobals.CashbotLobby,
                                 ToontownGlobals.SellbotLobby,
                                 ToontownGlobals.BossbotLobby):
                state = TTLocalizer.DoorInteractExit
                name = TTLocalizer.GlobalStreetNames[self.zoneId][2]

            text: str = ControlManager.ControlManager.parseHotkeyString(TTLocalizer.DoorInteractNamed % (state, name),
                                                                   useGlyphs=True)
            self.interactHint = OnscreenText(text, style = 3, scale = .065, parent = base.a2dBottomCenter,
                                             font = ToontownGlobals.getSuitFont(), fg = (0.5, 0.5, 0.5, 1.0),
                                             pos = (0.0, 0.0))

            taskMgr.add(self.__alignInteractHint, self.alignInteractHintTaskName)

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