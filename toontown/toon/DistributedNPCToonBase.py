from direct.gui.OnscreenText import OnscreenText
from panda3d.core import *
from panda3d.toontown import *
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM
from direct.fsm import State

from otp.otpbase.PythonUtil import bound
from toontown.toonbase import ToontownGlobals, TTLocalizer, ClientSettings, HotkeySettings, ControlManager
from . import DistributedToon
from direct.distributed import DistributedObject
from . import NPCToons
from direct.distributed import ClockDelta
from toontown.quest import QuestParser
from direct.interval.IntervalGlobal import *
import random

from .ToonDNA import ToonDNA

HALLOWEEN = False


class DistributedNPCToonBase(DistributedToon.DistributedToon):

    def __init__(self, cr):
        try:
            self.DistributedNPCToon_initialized
        except:
            self.DistributedNPCToon_initialized = 1
            DistributedToon.DistributedToon.__init__(self, cr)
            self.__initCollisions()
            self.setPickable(0)
            self.setPlayerType(NametagGroup.CCNonPlayer)
            self.setNametagStyle(100)

    def disable(self):
        self.ignore('enter' + self.cSphereNode.getName())
        DistributedToon.DistributedToon.disable(self)

    def delete(self):
        try:
            self.DistributedNPCToon_deleted
        except:
            self.DistributedNPCToon_deleted = 1
            self.__deleteCollisions()
            DistributedToon.DistributedToon.delete(self)

    def generate(self):
        DistributedToon.DistributedToon.generate(self)
        self.cSphereNode.setName(self.uniqueName('NPCToon'))
        self.detectAvatars()
        self.setParent(ToontownGlobals.SPRender)
        self.startLookAround()

    def generateToon(self):
        self.setLODs()
        self.generateToonLegs()
        self.generateToonHead()
        self.generateToonTorso()
        self.generateToonColor()
        self.parentToonParts()
        self.rescaleToon()
        self.resetHeight()
        self.rightHands = []
        self.leftHands = []
        self.headParts = []
        self.hipsParts = []
        self.torsoParts = []
        self.legsParts = []
        self.__bookActors = []
        self.__holeActors = []

    def announceGenerate(self):
        self.initToonState()
        DistributedToon.DistributedToon.announceGenerate(self)
        if HALLOWEEN:
            # halloween only
            random.seed(self.getDoId())
            costume = ToontownGlobals.NPCHalloweenCostumes[1] if type == self.getName() == 'Flippy' else \
                random.choice(ToontownGlobals.NPCHalloweenCostumes)
            if len(costume) == 7:  # we have a full costume
                dna = self.style
                dna.topTex = costume[0][0]
                dna.topTexColor = costume[0][1]
                dna.sleeveTex = costume[1][0]
                dna.sleeveTexColor = costume[1][1]
                dna.botTex = costume[2][0]
                dna.botTexColor = costume[2][1]
                self.setDNA(dna)
                self.setHat(*costume[3], 0)
                self.setGlasses(*costume[4], 0)
                self.setBackpack(*costume[5], 0)
                self.setShoes(*costume[6], 0)
            elif len(costume) == 4:
                self.setHat(*costume[0], 0)
                self.setGlasses(*costume[1], 0)
                self.setBackpack(*costume[2], 0)
                self.setShoes(*costume[3], 0)
            else:
                notify.error(f"Invalid costume defined: {costume}")

    def initToonState(self):
        self.setAnimState('neutral', 0.9, None, None)
        npcOrigin = render.find('**/npc_origin_' + repr((self.posIndex)))
        if not npcOrigin.isEmpty():
            self.reparentTo(npcOrigin)
            self.initPos()
        else:
            self.notify.warning('announceGenerate: Could not find npc_origin_' + str(self.posIndex))
        return

    def initPos(self):
        self.clearMat()

    def wantsSmoothing(self):
        return 0

    def detectAvatars(self):
        self.accept('enter' + self.cSphereNode.getName(), self.handleInteraction)

    def handleInteraction(self, collisionEntry):
        if ClientSettings.NPCInteraction.get():
            self.__createInteractHint(collisionEntry)
        else:
            self.handleCollisionSphereEnter(collisionEntry)

    def ignoreAvatars(self):
        self.ignore('enter' + self.cSphereNode.getName())

    def getCollSphereRadius(self):
        return 3.25

    def __initCollisions(self):
        self.cSphere = CollisionTube(0.0, 1.0, 0.0, 0.0, 1.0, 5.0, self.getCollSphereRadius())
        self.cSphere.setTangible(0)
        self.cSphereNode = CollisionNode('cSphereNode')
        self.cSphereNode.addSolid(self.cSphere)
        self.cSphereNodePath = self.attachNewNode(self.cSphereNode)
        self.cSphereNodePath.hide()
        self.cSphereNode.setCollideMask(ToontownGlobals.WallBitmask)

    def __deleteCollisions(self):
        del self.cSphere
        del self.cSphereNode
        self.cSphereNodePath.removeNode()
        del self.cSphereNodePath

    def handleCollisionSphereEnter(self, collEntry):
        pass

    def setupAvatars(self, av):
        self.ignoreAvatars()
        av.headsUp(self, 0, 0, 0)
        self.headsUp(av, 0, 0, 0)
        av.stopLookAround()
        av.lerpLookAt(Point3(-0.5, 4, 0), time=0.5)
        self.stopLookAround()
        self.lerpLookAt(Point3(av.getPos(self)), time=0.5)

    def b_setPageNumber(self, paragraph, pageNumber):
        self.setPageNumber(paragraph, pageNumber)
        self.d_setPageNumber(paragraph, pageNumber)

    def d_setPageNumber(self, paragraph, pageNumber):
        timestamp = ClockDelta.globalClockDelta.getFrameNetworkTime()
        self.sendUpdate('setPageNumber', [paragraph, pageNumber, timestamp])

    def freeAvatar(self):
        base.localAvatar.posCamera(0, 0)
        base.cr.playGame.getPlace().setState('walk')

    def setPositionIndex(self, posIndex):
        self.posIndex = posIndex

    def _startZombieCheck(self):
        pass

    def _stopZombieCheck(self):
        pass

    def isPlayerControlled(self):
        return False

    def setCogIndex(self, name, level, cogType = 1):
        if not name:
            self.takeOffTransformation()
            return
        from toontown.suit import SuitDNA
        self.putOnSuit(name, displayLevel = level, cogType=cogType)

    def __interact(self, collisionEntry):
        self.__destroyInteractHint()
        self.handleCollisionSphereEnter(collisionEntry)

    def handleCollisionSphereExit(self, collisionEntry = None):
        self.__destroyInteractHint()

    def __createInteractHint(self, collisionEntry):
        if not hasattr(self, "interactHint"):
            self.accept(HotkeySettings.Interact.getPressed(),
                        self.__interact, extraArgs = [collisionEntry])

            self.accept(f'exit{self.cSphereNode.getName()}', self.handleCollisionSphereExit)
            self.accept('toonExitWalk', self.handleCollisionSphereExit)
            text = ControlManager.ControlManager.parseHotkeyString(
                TTLocalizer.AvatarInteract % self.getName(), useGlyphs = True
            )

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

    def __alignInteractHint(self, task):
        """
        Aligns the interact hint on the screen
        The hint should be positioned on the npc, then the position is projected to the aspect2d
        """
        if hasattr(self, 'interactHint'):
            center = base.cam.getRelativePoint(self.nametagNodePath, Point3(0, 0, 0.3))

            if base.camNode.isInView(center):
                center2d = Point2()
                base.camLens.project(center, center2d)

                center2d.x = bound(center2d.x, -0.7, 0.7)
                center2d.y = bound(center2d.y, -0.9, 0.95)
                self.interactHint['text'] = ControlManager.ControlManager.parseHotkeyString(
                    TTLocalizer.AvatarInteractNoName, useGlyphs = True
                )
            else:
                # If the point isnt in the view, we set it to the 'default' position
                center2d = Point2(0.0, -0.45)
                self.interactHint['text'] = ControlManager.ControlManager.parseHotkeyString(
                    TTLocalizer.AvatarInteract % self.getName(), useGlyphs = True
                )

            self.interactHint.set_pos(render2d, Point3(center2d.x, 0, center2d.y))

        return task.cont

    @property
    def alignInteractHintTaskName(self):
        return f'alignInteractHint-{self.getDoId()}'

