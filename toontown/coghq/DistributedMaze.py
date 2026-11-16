from otp.level.BasicEntities import DistributedNodePathEntity
from panda3d.core import *
from direct.interval.IntervalGlobal import *
from toontown.toonbase.ToontownGlobals import *
import random
from direct.directnotify import DirectNotifyGlobal
from direct.distributed.ClockDelta import globalClockDelta
from . import DistributedBarrelBase
from otp.camera.CameraGlobals import CameraMode
from otp.level.BasicEntities import DistributedNodePathEntity
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from direct.task import Task
from direct.gui.DirectGui import DGG, DirectFrame, DirectLabel

class DistributedMaze(DistributedNodePathEntity):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedMaze')
    ScheduleTaskName = 'mazeScheduler'
    RemoveBlocksDict = {2: ('HedgeBlock_0_1',),
     4: (('HedgeBlock_0_1', 'HedgeBlock_1_3', 'HedgeBlock_2_3'), ('HedgeBlock_0_2', 'HedgeBlock_2_3', 'HedgeBlock_1_3'), ('HedgeBlock_0_1', 'HedgeBlock_0_2', 'HedgeBlock_1_3', 'HedgeBlock_2_3'))}

    def __init__(self, cr):
        DistributedNodePathEntity.__init__(self, cr)
        self.numSections = 0
        self.finished = 0
        self.timedOut = 0

    def announceGenerate(self):
        DistributedNodePathEntity.announceGenerate(self)
        self.addHints(self.roomHold)

    def disable(self):
        DistributedNodePathEntity.disable(self)
        self.ignoreAll()

    def setRoomDoId(self, roomDoId):
        self.roomDoId = roomDoId
        room = self.cr.doId2do.get(roomDoId)
        if room:
            self.gotRoom([room])
        else:
            self.roomRequest = self.cr.relatedObjectMgr.requestObjects([roomDoId], allCallback=self.gotRoom, timeout=5)

    def gotRoom(self, rooms):
        self.roomRequest = None
        room = rooms[0]
        self.roomHold = room
        rotations = [0,
         0,
         90,
         90,
         180,
         180,
         270,
         270]
        self.getRng().shuffle(rotations)
        self.numSections = 0
        for i in range(0, 4):
            maze = room.getGeom().find('**/Maze_Inside_%d' % i)
            if not maze.isEmpty():
                self.numSections += 1
                if rotations:
                    maze.setH(rotations.pop())

        self.removeHedgeBlocks(room)

    def addHints(self, room):
        self.focusPoint = self.attachNewNode('GolfGreenGameFrame')
        hintList = room.getGeom().findAllMatches('**/dead*')
        for hint in hintList:
            self.actSphere = CollisionSphere(0, 0, 0, 7.0)
            self.actSphereNode = CollisionNode('mazegame_hint-%s-%s' % (self.level.getLevelId(), self.entId))
            self.actSphereNode.addSolid(self.actSphere)
            self.actSphereNodePath = hint.attachNewNode(self.actSphereNode)
            self.actSphereNode.setCollideMask(WallBitmask)
            self.actSphere.setTangible(0)
            self.enterEvent = 'enter' + self.actSphereNode.getName()
            self.accept(self.enterEvent, self.__handleToonEnterHint)
            self.exitEvent = 'exit' + self.actSphereNode.getName()
            self.accept(self.exitEvent, self.__handleToonExitHint)

    def __handleToonEnterHint(self, collEntry):
        camHeight = base.localAvatar.getClampedAvatarHeight()
        heightScaleFactor = camHeight * 0.3333333333
        defLookAt = Point3(0.0, 1.5, camHeight)
        cameraPoint = Point3(0.0, -22.0 * heightScaleFactor, camHeight + 54.0)
        base.localAvatar.deactivateCamera()
        base.localAvatar.activateCamera(push=0)
        if base.localAvatar.getActiveCameraMode() == CameraMode.CLASSIC:
            base.localAvatar.cameraFSM.classicCamera.setIdealCameraPos(cameraPoint)

    def __handleToonExitHint(self, collEntry):
        base.localAvatar.deactivateCamera()
        base.localAvatar.activateCamera()
        if base.localAvatar.getActiveCameraMode() == CameraMode.CLASSIC:
            base.localAvatar.cameraFSM.classicCamera.setCameraPositionByIndex(base.localAvatar.cameraIndex)
        self.cameraHold = None

    def getRng(self):
        return random.Random(self.entId * self.doId)

    def removeHedgeBlocks(self, room):
        if self.numSections in self.RemoveBlocksDict:
            blocksToRemove = self.getRng().choice(self.RemoveBlocksDict[self.numSections])
            for blockName in blocksToRemove:
                block = room.getGeom().find('**/%s' % blockName)
                if not block.isEmpty():
                    block.removeNode()
