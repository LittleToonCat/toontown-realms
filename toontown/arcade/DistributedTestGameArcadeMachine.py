"""
DistributedTestGameArcadeMachine Client Side • Created by Drew @ 10/6/2022
Authorized for use ONLY in Toontown Realms
"""
from typing import Tuple

from direct.fsm.FSM import FSM
from panda3d.core import Point3, TextNode, NodePath, Vec4

from toontown.arcade.DistributedArcadeMachine import DistributedArcadeMachine
from toontown.avatar import ToontownAvatarUtils
from toontown.toon.Toon import Toon
from toontown.toonbase import ToontownGlobals, HotkeySettings


class DistributedTestGameArcadeMachine(DistributedArcadeMachine, FSM):

    def __init__(self, cr):
        DistributedArcadeMachine.__init__(self, cr)
        FSM.__init__(self, 'TestArcade')

        self.machineNode: NodePath
        self.testToon: Toon

        self.titleText: TextNode
        self.titleTextNp: NodePath

        self.mainMenuSelectedButton = 0  # 0: PLAY, 1: QUIT

        self.playText: TextNode
        self.playTextNp: NodePath

        self.quitText: TextNode
        self.quitTextNp: NodePath

    def announceGenerate(self):
        self.machineNode: NodePath = loader.loadModel('phase_14.5/models/props/ttrm_m_ara_int_tsk_arcade_testGameMachine')
        DistributedArcadeMachine.announceGenerate(self)
        self.testToon = ToontownAvatarUtils.createToon(4105)
        self.testToon.reparentTo(self.gameRender)
        self.testToon.setPos(0, 3, 0)
        self.testToon.setH(180)
        self.testToon.loop('victory')
        self.testToon.hide()
        self.gameRenderCam.setPos(0, -4, 2.4)
        self.machineNode.setPos(11.45, -9.83, 0.03)
        self.request('NoPlay')

    def enterNoPlay(self):
        self.titleText = TextNode('TEST_PLAY_TITLE')
        self.titleText.setTextColor(1, 1, 1, 1.0)
        self.titleText.setAlign(TextNode.ACenter)
        self.titleText.setText('Test\nGame')
        self.titleText.setTextScale(0.3)
        self.titleTextNp: NodePath = self.gameRender.attachNewNode(self.titleText)
        self.titleTextNp.setPos(0, 0.2, 2.5)

    def exitNoPlay(self):
        self.titleText = None
        self.titleTextNp.removeNode()

    def startPlaying(self):
        DistributedArcadeMachine.startPlaying(self)
        self.request('MainMenu')

    def stopPlaying(self):
        DistributedArcadeMachine.stopPlaying(self)
        self.request('NoPlay')

    def enterMainMenu(self):
        self.playText = TextNode('TEST_PLAY_TITLE')
        self.playText.setTextColor(1, 1, 1, 1.0)
        self.playText.setAlign(TextNode.ACenter)
        self.playText.setText('PLAY')
        self.playText.setTextScale(0.3)
        self.playTextNp: NodePath = self.gameRender.attachNewNode(self.playText)
        self.playTextNp.setPos(0, 0.2, 2)

        self.quitText = TextNode('TEST_PLAY_TITLE')
        self.quitText.setTextColor(1, 1, 1, 1.0)
        self.quitText.setAlign(TextNode.ACenter)
        self.quitText.setText('QUIT')
        self.quitText.setTextScale(0.3)
        self.quitTextNp: NodePath = self.gameRender.attachNewNode(self.quitText)
        self.quitTextNp.setPos(0, 0.2, 1.5)
        self.mainMenuSelectedButton = 0

        self.mainMenuHighlightSelected()

        self.accept(HotkeySettings.MoveForward.getPressed(), self.mainMenuChangeOption)
        self.accept(HotkeySettings.MoveBackward.getPressed(), self.mainMenuChangeOption)
        self.accept(HotkeySettings.Action.getPressed(), self.mainMenuDoAction)

        self.displayHotkeys([
            (
                [
                    (ToontownGlobals.HotkeyMovement, ToontownGlobals.HotkeyUp),
                    (ToontownGlobals.HotkeyMovement, ToontownGlobals.HotkeyDown)
                ], "$Navigate Menu"
            ),
            (
                (ToontownGlobals.HotkeyMovement, ToontownGlobals.HotkeyAction),
                "$Select"
            )
        ])

    def exitMainMenu(self):
        self.playText = None
        self.playTextNp.removeNode()

        self.quitText = None
        self.quitTextNp.removeNode()

        self.ignore(HotkeySettings.MoveForward.getPressed())
        self.ignore(HotkeySettings.MoveBackward.getPressed())
        self.ignore(HotkeySettings.Action.getPressed())

    def mainMenuChangeOption(self):
        self.mainMenuSelectedButton = not self.mainMenuSelectedButton
        self.mainMenuHighlightSelected()

    def mainMenuHighlightSelected(self):
        texts = (self.playTextNp, self.quitTextNp)
        texts[self.mainMenuSelectedButton].setColorScale(Vec4(0.0, 1.0, 1.0, 1.0))
        texts[not self.mainMenuSelectedButton].setColorScale(Vec4(1.0, 1.0, 1.0, 0.8))

    def mainMenuDoAction(self):
        # QUIT BUTTON
        if self.mainMenuSelectedButton == 1:
            self.sendUpdate('requestLeave')
