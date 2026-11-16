# Distributed Door == Client Side
# Created by drewc Oct 14 2023
from direct.gui import DirectGuiGlobals
from direct.gui.DirectFrame import DirectFrame
from direct.interval.FunctionInterval import Func, Wait
from direct.interval.LerpInterval import LerpPosInterval, LerpPosHprInterval, LerpHprInterval
from direct.interval.MetaInterval import Sequence, Parallel
from direct.task.Task import Task
from typing import Optional, Dict, Union

from direct.fsm.ClassicFSM import ClassicFSM
from panda3d.core import CollisionSphere, CollisionNode, NodePath, Point3, Point2, TextNode, Vec3

from direct.gui.OnscreenText import OnscreenText
from direct.showbase.PythonUtil import bound
from panda3d.toontown import WhisperPopup

from toontown.hood import ZoneUtil
from toontown.sandbox import PropGlobals
from toontown.sandbox.Prop import Prop
from toontown.sandbox.PropDistributed import PropDistributed
from toontown.sandbox.PropGlobals import PropPool
from toontown.sandbox.PropUI import NumberEntry
from toontown.sandboxdistprops.DistributedProp import DistributedProp
from toontown.toon.DistributedToon import DistributedToon
from toontown.toonbase import TTLocalizer, ToontownGlobals, HotkeySettings, ControlManager
from toontown.toonbase.ToonBaseGlobal import base
from toontown.toontowngui.AnimatedButton import AnimatedButton


class DistributedPropDoor(DistributedProp):
    CopiedID: Optional[int] = None

    def __init__(self, cr):
        DistributedProp.__init__(self, cr)
        self.rightDoorFSM = ClassicFSM(f'DistPropDoor_RIGHT')
        self.targetDoId: int = 0
        self.targetZone: int = 0
        self.targetDoorId: int = 0

        self.doorId: int = 0

        self.collSphere: Optional[CollisionSphere] = None
        self.collNode: Optional[CollisionNode] = None
        self.collNodePath: Optional[NodePath] = None

        self.interactHint: Optional[OnscreenText] = None

        self.doorIdLabel: Optional[OnscreenText] = None
        self.targetDoorIdLabel: Optional[OnscreenText] = None

        self.experimentalWarning: Optional[OnscreenText] = None

        self.copyIdButton: Optional[AnimatedButton] = None
        self.pasteIdButton: Optional[AnimatedButton] = None

        self.targetDoorEntry: Optional[NumberEntry] = None
        self.setTargetDoorButton: Optional[AnimatedButton] = None

        self.editPage: Optional[DirectFrame] = None
        self.editTitle: Optional[OnscreenText] = None

    def announceGenerate(self):
        DistributedProp.announceGenerate(self)
        self.reparentTo(base.render)
        self.model = PropPool.getProp(self.getPropName())
        self.model.reparentTo(self)

        lhole = self.find('**/*door_*_hole_right')
        lhole.setDepthOffset(1)

        rhole = self.find('**/*door_*_hole_left')
        rhole.setDepthOffset(1)

        self.collSphere = CollisionSphere(0, 0, 0, 5)
        self.collSphere.setTangible(0)

        self.collNode = CollisionNode(self.getTriggerName())
        self.collNode.addSolid(self.collSphere)
        self.collNodePath: NodePath = self.attachNewNode(self.collNode)
        # self.collNodePath.show()

        self.collNode.setCollideMask(ToontownGlobals.WallBitmask)

        self.accept(self.getEnterTriggerEvent(), self.enterTrigger)

        # self.accept('')

    def createGui(self):
        DistributedProp.createGui(self)

        self.doorIdLabel = OnscreenText(
            parent = self.infoPage,
            text = f"{TTLocalizer.PropEditorDoor_ThisID} {self.doorId}",
            scale = PropGlobals.UIInfoScale,
            pos = PropGlobals.UIInfoUUIDLabelPos,
            align = TextNode.ALeft
        )

        self.targetDoorIdLabel = OnscreenText(
            parent = self.infoPage,
            text = f"{TTLocalizer.PropEditorDoor_TargetID} {self.targetDoorId}",
            scale = PropGlobals.UIInfoScale,
            pos = PropGlobals.UIInfoUUIDInfoPos,
            align = TextNode.ARight
        )

        self.targetDoorEntry = NumberEntry(
            parent = self.infoPage,
            pos = PropGlobals.UIPosZPos,
            scale = 0.8,
            incrementScale = 1,
            startValue = self.targetDoorId,
            numberType = int,
            minMax = (0, 999999),
        )

        self.copyIdButton = AnimatedButton(
            parent = self.infoPage,
            text = TTLocalizer.PropEditorDoor_CopyID,
            text_pos = (0, -0.025),
            text_scale = 0.09,
            image_scale = (.42, 1, .11),
            image = (PropGlobals.PropUi.find('**/button_normal'),
                     PropGlobals.PropUi.find('**/button_click'),
                     PropGlobals.PropUi.find('**/button_hover'),
                     PropGlobals.PropUi.find('**/button_normal')),
            pos = (-0.1, 0, 0.02),
            scale = 0.4,
            command = self.__copyId
        )

        self.pasteIdButton = AnimatedButton(
            parent = self.infoPage,
            text = TTLocalizer.PropEditorDoor_PasteID,
            text_pos = (0, -0.025),
            text_scale = 0.09,
            image_scale = (.42, 1, .11),
            image3_color = (1.0, 1.0, 1.0, 0.5),
            image = (PropGlobals.PropUi.find('**/button_normal'),
                     PropGlobals.PropUi.find('**/button_click'),
                     PropGlobals.PropUi.find('**/button_hover'),
                     PropGlobals.PropUi.find('**/button_normal')),
            pos = (0.1, 0, 0.02),
            scale = 0.4,
            command = self.__pasteId
        )

        if DistributedPropDoor.CopiedID is None:
            self.pasteIdButton['state'] = DirectGuiGlobals.DISABLED

        self.setTargetDoorButton = AnimatedButton(
            parent = self.infoPage,
            text = TTLocalizer.PropEditorSet,
            text_pos = (0, -0.025),
            text_scale = 0.08,
            image_scale = (.42, 1, .11),
            image = (PropGlobals.PropUi.find('**/button_normal'),
                     PropGlobals.PropUi.find('**/button_click'),
                     PropGlobals.PropUi.find('**/button_hover'),
                     PropGlobals.PropUi.find('**/button_normal')),
            pos = (0, 0, -0.23),
            scale = .8,
            command = self.requestChangeTarget
        )

        self.experimentalWarning = OnscreenText(
            parent = self.infoPage,
            text = TTLocalizer.PropDoor_WarningExperimental,
            pos = (0, .15),
            scale = 0.02,
            align = TextNode.ACenter,
            wordwrap = 20
        )

        # self.editPage = DirectFrame(parent = self.uiFrame, relief = None)
        # self.editTitle = self.makeTitle(parent = self.infoPage, text = TTLocalizer.PropEditorInfoTitle)

    def __copyId(self):
        self.pasteIdButton['state'] = DirectGuiGlobals.NORMAL
        DistributedPropDoor.CopiedID = self.doorId

    def __pasteId(self):
        self.targetDoorEntry.set(str(DistributedPropDoor.CopiedID))

    def requestChangeTarget(self):
        self.sendUpdate('requestDataChange', ['target_door', 0, (self.targetDoorEntry.get(),)])

    def setDoorId(self, doorId: int):
        self.doorId = doorId

    def setTargetDoorDoIdAndZone(self, doId: int, zone: int, doorId: int):
        self.targetDoId = doId
        self.targetZone = zone
        self.targetDoorId = doorId
        if self.targetDoorIdLabel:
            self.targetDoorIdLabel['text'] = f"{TTLocalizer.PropEditorDoor_TargetID} {self.targetDoorId}"

    def getRequestStatus(self) -> Dict[str, Union[int, str]]:
        return {
            'loader': ZoneUtil.getBranchLoaderName(self.targetZone),
            'where': ZoneUtil.getToonWhereName(self.targetZone),
            'how': 'doorIn',
            'hoodId': ZoneUtil.getHoodId(self.targetZone),
            'zoneId': self.targetZone,
            'avId': -1,
            'allowRedirect': 1,
            'doorDoId': self.targetDoId
        }

    def delete(self):
        DistributedProp.delete(self)

        del self.collSphere
        self.collNode.removeAllChildren()
        del self.collNode
        self.collNodePath.removeNode()
        del self.collNodePath

        self.destroyInteractHint()
        self.ignoreAll()

    def enterDoor(self):
        if self.targetZone == 0 or self.targetDoId == 0:
            base.localAvatar.setSystemMessage(0, TTLocalizer.PropDoor_ErrorNotLinked, WhisperPopup.WTSystem)
            return
        if Prop.selectedProp == self:
            self.deselect()
        self.destroyInteractHint()
        self.sendUpdate('requestEnter')

    def enterTrigger(self, e = None):
        self.ignore(self.getEnterTriggerEvent())
        self.accept(self.getExitTriggerEvent(), self.exitTrigger)

        self.createInteractHint()

    def exitTrigger(self, e = None):
        self.accept(self.getEnterTriggerEvent(), self.enterTrigger)

        self.destroyInteractHint()

    def readyToExit(self):
        self.sendUpdate('requestExit')

    def avatarEnter(self, avId: int):
        if avId == base.localAvatar.getDoId():
            place = self.cr.playGame.getPlace()
            if place:
                place.setState('stopped')

            def done():
                if self.targetZone == self.zoneId:
                    newDoor: DistributedPropDoor = base.cr.doId2do.get(self.targetDoId)
                    if newDoor:
                        newDoor.readyToExit()
                        return
                base.messenger.send('doorDoneEvent', [self.getRequestStatus()])

            seq = Sequence(
                Func(base.localAvatar.b_setAnimState, 'walk', -1),
                Parallel(
                    LerpPosHprInterval(base.localAvatar,
                                       .7,
                                       Vec3(1.5, -5, ToontownGlobals.FloorOffset),
                                       hpr = (0, 0, 0),
                                       other = self,
                                       blendType = 'easeInOut'),
                    LerpPosHprInterval(base.camera,
                                       .7,
                                       Vec3(0, -8, base.localAvatar.getHeight()),
                                       Vec3(0, 0, 0),
                                       other = base.localAvatar,
                                       blendType = 'easeInOut'
                                       )
                ),
                Func(base.localAvatar.b_setAnimState, 'neutral', 1),
                Wait(0.1),
                Func(base.localAvatar.b_setAnimState, 'walk', 1),
                Parallel(
                    Func(base.transitions.irisOut, 0.8),
                    LerpPosInterval(base.localAvatar,
                                    0.8,
                                    Vec3(1.5, 1, ToontownGlobals.FloorOffset),
                                    other = self),
                ),
                Func(done),
                name = f'door{self.getDoId()}avEnter{avId}'
            )
            seq.start()
        else:
            # its someone else
            toon: DistributedToon = self.cr.doId2do.get(avId)
            seq = Sequence(
                LerpPosHprInterval(toon,
                                   .7,
                                   Vec3(1.5, -5, ToontownGlobals.FloorOffset),
                                   hpr = (0, 0, 0),
                                   other = self,
                                   blendType = 'easeInOut'),
                Wait(0.1),
                LerpPosInterval(toon,
                                0.8,
                                Vec3(1.5, 1, ToontownGlobals.FloorOffset),
                                other = self),
                name = f'door{self.getDoId()}avEnter{avId}'
            )
            seq.start()

    def avatarExit(self, avId: int):
        if avId == base.localAvatar.getDoId():
            base.localAvatar.d_setParent(ToontownGlobals.SPRender)

            def done():
                place = self.cr.playGame.getPlace()
                if place:
                    place.setState('walk')

            seq = Sequence(
                Func(base.localAvatar.setPos, self, -1.5, 1, ToontownGlobals.FloorOffset),
                Func(base.camera.reparentTo, base.localAvatar),
                Func(base.camera.setPos, 0, 8, base.localAvatar.getHeight()),
                Func(base.camera.setHpr, 180, 0, 0),
                Func(base.localAvatar.setH, self, 180),
                Func(base.transitions.irisIn, 0.8),
                Func(base.localAvatar.b_setAnimState, 'walk'),
                LerpPosInterval(base.localAvatar,
                                1.2,
                                Vec3(-1.5, -5, ToontownGlobals.FloorOffset),
                                other = self,
                                blendType = 'easeOut'),
                Func(base.localAvatar.b_setAnimState, 'neutral'),
                Func(done),
                name = f'door{self.getDoId()}avExit{avId}'
            )

            seq.start()
        else:
            # its someone else
            toon: DistributedToon = self.cr.doId2do.get(avId)
            seq = Sequence(
                Func(toon.stopSmooth),
                Wait(0.01), # for some reason setH sometimes fails without this delay?
                Func(toon.setPos, self, -1.5, 1, ToontownGlobals.FloorOffset),
                Func(toon.setH, self, 180),
                LerpPosInterval(toon,
                                1.19,
                                Vec3(-1.5, -5, ToontownGlobals.FloorOffset),
                                other = self),
                Func(toon.startSmooth),
                name = f'door{self.getDoId()}avExit{avId}'
            )
            seq.start()

    def getAlignInteractHintTaskName(self) -> str:
        return f'alignInteractHint-{self.getDoId()}'

    def getTriggerName(self) -> str:
        return f'propdoor_{self.getDoId()}'

    def getEnterTriggerEvent(self) -> str:
        return 'enter' + self.getTriggerName()

    def getExitTriggerEvent(self) -> str:
        return 'exit' + self.getTriggerName()

    def __alignInteractHint(self, task: Task) -> int:
        """
        Aligns the interact hint on the screen
        The hint should be positioned on the door, then the position is projected to the aspect2d
        """
        if hasattr(self, 'interactHint') and not self.isEmpty():
            center = base.cam.getRelativePoint(self, Point3(0, 0, 3))

            if base.camNode.isInView(center):
                center2d = Point2()
                base.camLens.project(center, center2d)

                center2d.x = bound(center2d.x, -0.7, 0.7)
                center2d.y = bound(center2d.y, -0.9, 0.95)
            else:
                # If the point isnt in the view, we set it to the 'default' position
                center2d = Point2(0.0, -0.45)
            # We are using snake case bc camel case is actually a different function here (panda3d moment)
            self.interactHint.set_pos(base.render2d, Point3(center2d.x, 0, center2d.y))

        return task.cont

    def createInteractHint(self):
        if self.interactHint is None:
            self.accept(HotkeySettings.Interact.getPressed(),
                        self.enterDoor)
            self.accept('toonExitWalk', self.exitTrigger)

            text: str = ControlManager.ControlManager.parseHotkeyString(TTLocalizer.DoorInteractUnnamed % TTLocalizer.DoorInteractEnter,
                                                                   useGlyphs=True)

            fg = (1.0, 1.0, 1.0, 1.0)
            font = ToontownGlobals.getFancyFont()
            self.interactHint = OnscreenText(text, style = 3, scale = .065, parent = base.a2dBottomCenter,
                                             font = font, fg = fg, pos = (0.0, 0.0))

            self.addTask(self.__alignInteractHint, self.getAlignInteractHintTaskName())

    def destroyInteractHint(self):
        self.ignore(HotkeySettings.Interact.getPressed())
        self.ignore('toonExitWalk')
        # Remove interact hint
        if self.interactHint:
            self.removeTask(self.getAlignInteractHintTaskName())
            self.interactHint.removeNode()
            self.interactHint = None

    def setDoorState(self, door: int, state: bool):
        if door == 0:
            doorNP = self.find('**/*door_**_left')

            if state:
                LerpHprInterval(doorNP, 0.6, Vec3(-100, 0, 0), (0, 0, 0), blendType = 'easeInOut').start()
            else:
                LerpHprInterval(doorNP, 0.6, Vec3(0, 0, 0), (-100, 0, 0), blendType = 'easeInOut').start()
        else:
            doorNP = self.find('**/*door_**_right')
            if state:
                LerpHprInterval(doorNP, 0.6, Vec3(100, 0, 0), (0, 0, 0), blendType = 'easeInOut').start()
            else:
                LerpHprInterval(doorNP, 0.6, Vec3(0, 0, 0), (100, 0, 0), blendType = 'easeInOut').start()