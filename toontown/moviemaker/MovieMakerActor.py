from typing import Dict, Any, Tuple, List, Optional

from direct.gui import DirectGuiGlobals
from direct.gui.DirectButton import DirectButton
from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectSlider import DirectSlider
from direct.gui.OnscreenText import OnscreenText
from direct.interval.FunctionInterval import Func
from direct.interval.Interval import Interval
from direct.interval.LerpInterval import LerpPosInterval
from direct.interval.MetaInterval import Parallel
from panda3d.core import Vec3, TextNode

from otp.otpgui import OTPGUIUtils
from toontown.moviemaker.MovieMakerGUI import MovieMakerGUI
from toontown.suit.Suit import Suit, SuitsCEOBattle, AllSuitsTutorialBattle, AllSuitsBattle, AllSuitsMinigame, AllSuits, SuitBattleAnims
from toontown.toon.Toon import Toon, Phase3AnimList, Phase3_5AnimList, Phase4AnimList, Phase5AnimList, Phase6AnimList, Phase5_5AnimList, Phase9AnimList, Phase10AnimList, \
    Phase12AnimList


class MovieMakerActor:

    def __init__(self, scene):
        self.scene = scene
        self.intervalNodes: List[Tuple[float, MovieMakerBaseNode]] = []
        self.gui: Optional[DirectFrame] = None
        self.nodeHash = 'base actor this cant be used'
        self.guiTabs: List[DirectFrame] = []

    def loadIvalFromJson(self, json: List[Dict[str, Any]]):
        """
        json data should look like
        [
            {
            "time": 0.12,
            "type": "ivNode_setPos",
            "args": [...]
            }
        ]
        :param json:
        :return:
        """

        nameToClass = {
            'MovieMakerSetPos': MovieMakerSetPos,
            'MovieMakerLerpPos': MovieMakerLerpPos,
            'MovieMakerActorLoop': MovieMakerActorLoop
        }

        for i in json:
            _time, _type, _args = i['time'], i['type'], i['args']
            self.intervalNodes.append(
                    (_time, nameToClass.get(_type)(self, *_args))
            )

    def getHash(self) -> str:
        return self.nodeHash

    def toJson(self):
        dict = {
            "type": self.__class__.__name__,
            "initPosHprScale": [0, 0, 0, 0, 0, 0, 1, 1, 1],
            "interval": []
        }

        for _time, _ivNode in self.intervalNodes:
            dict['interval'].append((_time, _ivNode.toJson()))

        return dict

    def openEditor(self):
        guiModel = MovieMakerGUI.gui

        self.gui = DirectFrame(
                relief = None,
                parent = base.a2dTopRight,
                pos = (-0.35, 0, -0.6),
                image = guiModel.find('**/actor_editor_bg'),
                image_scale = OTPGUIUtils.getImageScale(646, 932),
                state = DirectGuiGlobals.NORMAL
        )

        LerpPosInterval(self.gui, 0.2, pos = (-0.35, 0, -0.6), startPos = (.35, 0, -0.6), blendType = 'easeOut').start()

        self.title = OnscreenText(
                text = self.__class__.__name__, # temp: actually localize it
                pos = (-0.32, .44),
                align = TextNode.ALeft,
                scale = 0.05,
                parent = self.gui
        )
        self.closeBtn = DirectButton(
                relief = None,
                parent = self.gui,
                pos = (.3, 0, .46),
                image = guiModel.find('**/tab_close'),
                scale = 0.05,
                command = self.__closeEditor
        )
        self.moveButton = DirectButton(
                relief = None,
                parent = self.gui,
                pos = (-.3, 0, -.46),
                image = guiModel.find('**/actor_move'),
                scale = 0.05,
                command = self.scene.grabActor,
                extraArgs = [self]
        )

        self.mainTab = DirectFrame(
                relief = None,
                parent = self.gui
        )
        self.guiTabs.append(self.mainTab)

        self.mainTabBtn = DirectButton(
                relief = None,
                parent = self.gui,
                pos = (-.25, 0, .5385),
                image = guiModel.find('**/actor_tab_main'),
                image_scale = OTPGUIUtils.getImageScale(105, 87),
                scale = 0.08,
                command = self.setTab,
                extraArgs = [self.mainTab]
        )

    def setTab(self, frame):
        for tab in self.guiTabs:
            tab.show() if tab == frame else tab.hide()

    def __closeEditor(self):
        self.scene.deselect()
        self.closeEditor()

    def closeEditor(self):
        self.gui.destroy()
        self.guiTabs = []


class MovieMakerToon(MovieMakerActor, Toon):

    def __init__(self, scene):
        MovieMakerActor.__init__(self, scene)
        Toon.__init__(self)
        self.lastAnim = 'neutral'
        self.lastPoseVal: float = -1
        self.reparentTo(render)
        self.setTag('actor', str(hash(self.getGeomNode())))
        self.nodeHash = str(hash(self.getGeomNode()))

    def toJson(self):
        dict = MovieMakerActor.toJson(self)
        dict['type'] = self.__class__.__name__
        dict['dna'] = self.getStyle().makeNetString()
        dict['name'] = self.getName()
        dict['initPosHprScale'] = (*self.getPos(), *self.getHpr(), *self.getScale())
        return dict

    def openEditor(self):
        MovieMakerActor.openEditor(self)
        self.title['text'] = self.getName()
        guiModel = MovieMakerGUI.gui
        self.neutralAnimButton = DirectButton(
            parent = self.mainTab,
            pos = (-.13, 0, .3),
            frameSize = (-2.5, 2.5, -1, 1),
            text = 'Neutral',
            text_pos = (0, -0.2),
            text_scale = 0.7,
            scale = 0.05,
            command = self.loop,
            extraArgs = ['neutral']
        )

        self.animButton = DirectButton(
            parent = self.mainTab,
            pos = (.13, 0, .3),
            frameSize = (-2.5, 2.5, -1, 1),
            text = 'Anims',
            text_pos = (0, -0.2),
            text_scale = 0.7,
            scale = 0.05,
            command = self.setTab
        )

        self.loopButton = DirectButton(
            parent = self.mainTab,
            pos = (-.13, 0, .19),
            frameSize = (-2.5, 2.5, -1, 1),
            text = 'Loop',
            text_pos = (0, -0.2),
            text_scale = 0.7,
            scale = 0.05,
            command = self.__loopCurrentAnim
        )

        self.poseButton = DirectButton(
            parent = self.mainTab,
            pos = (.13, 0, .19),
            frameSize = (-2.5, 2.5, -1, 1),
            text = 'Pose',
            text_pos = (0, -0.2),
            text_scale = 0.7,
            scale = 0.05,
            command = self.setTab,
        )

        self.headButton = DirectButton(
            parent = self.mainTab,
            pos = (-.13, 0, .08),
            frameSize = (-2.5, 2.5, -1, 1),
            text = 'Head\nRotation',
            text_pos = (0, 0.15),
            text_scale = 0.7,
            scale = 0.05,
            command = self.setTab
        )

        self.eyesAndMuzzleButton = DirectButton(
            parent = self.mainTab,
            pos = (.13, 0, 0.08),
            frameSize = (-2.5, 2.5, -1, 1),
            text = 'Eyes &\nMuzzle',
            text_pos = (0, 0.15),
            text_scale = 0.7,
            scale = 0.05,
            command = self.setTab
        )

        self.propsTab = DirectFrame(
                relief = None,
                parent = self.gui
        )

        self.propsTabBtn = DirectButton(
                relief = None,
                parent = self.gui,
                pos = (-.15, 0, .5385),
                image = guiModel.find('**/actor_tab_properties'),
                image_scale = OTPGUIUtils.getImageScale(105, 87),
                scale = 0.08,
                command = self.setTab,
                extraArgs = [self.propsTab]
        )
        self.propsTab.hide()
        self.guiTabs.append(self.propsTab)

        self.faceTab = DirectFrame(
            relief = None,
            parent = self.gui
        )
        self.faceTab.hide()
        self.eyesAndMuzzleButton['extraArgs'] = [self.faceTab]

        self.startBlinkBtn = DirectButton(
            parent = self.faceTab,
            pos = (-.13, 0, 0.3),
            frameSize = (-2.5, 2.5, -1, 1),
            text = 'Start\nBlink',
            text_pos = (0, 0.15),
            text_scale = 0.7,
            scale = 0.05,
            command = self.startBlink
        )

        self.stopBlinkBtn = DirectButton(
            parent = self.faceTab,
            pos = (.13, 0, .3),
            frameSize = (-2.5, 2.5, -1, 1),
            text = 'Stop\nBlink',
            text_pos = (0, 0.15),
            text_scale = 0.7,
            scale = 0.05,
            command = self.stopBlink
        )

        self.faceBackBtn = DirectButton(
            parent = self.faceTab,
            pos = (-.13, 0, -0.25),
            frameSize = (-2.5, 2.5, -1, 1),
            text = 'BACK\n<<',
            text_pos = (0, 0.15),
            text_scale = 0.7,
            scale = 0.05,
            command = self.setTab,
            extraArgs = [self.mainTab]
        )

        self.guiTabs.append(self.faceTab)

        self.poseTab = DirectFrame(
            relief = None,
            parent = self.gui
        )
        self.poseTab.hide()

        self.guiTabs.append(self.poseTab)

        self.poseButton['extraArgs'] = [self.poseTab]

        self.poseSlider = DirectSlider(
            parent = self.poseTab,
            pos = (0, 0, 0.3),
            frameSize = (-1, 1, -.1, .1),
            scrollSize = 1,
            pageSize = 1,
            scale = 0.2,
            value = self.lastPoseVal,
            command = self.__poseCurrent
        )

        self.poseBackButton = DirectButton(
            parent = self.poseTab,
            pos = (-.13, 0, -0.25),
            frameSize = (-2.5, 2.5, -1, 1),
            text = 'BACK\n<<',
            text_pos = (0, 0.15),
            text_scale = 0.7,
            scale = 0.05,
            command = self.setTab,
            extraArgs = [self.mainTab]
        )

        self.headTab = DirectFrame(
            relief = None,
            parent = self.gui
        )
        self.headButton['extraArgs'] = [self.headTab]
        self.headTab.hide()
        self.guiTabs.append(self.headTab)
        self.startLookAroundBtn = DirectButton(
            parent = self.headTab,
            pos = (-.13, 0, -0.03),
            frameSize = (-2.5, 2.5, -1, 1),
            text = 'Start\nLook Around',
            text_pos = (0, 0.15),
            text_scale = 0.7,
            scale = 0.05,
            command = self.startLookAround
        )

        self.stopLookAroundBtn = DirectButton(
            parent = self.headTab,
            pos = (.13, 0, -0.03),
            frameSize = (-2.5, 2.5, -1, 1),
            text = 'Stop\nLook Around',
            text_pos = (0, 0.15),
            text_scale = 0.7,
            scale = 0.05,
            command = self.__resetHeadRotation
        )

        self.headBackButton = DirectButton(
            parent = self.headTab,
            pos = (-.13, 0, -0.25),
            frameSize = (-2.5, 2.5, -1, 1),
            text = 'BACK\n<<',
            text_pos = (0, 0.15),
            text_scale = 0.7,
            scale = 0.05,
            command = self.setTab,
            extraArgs = [self.mainTab]
        )

        self.headHSlider = DirectSlider(
            parent = self.headTab,
            pos = (0, 0, .3),
            frameSize = (-1, 1, -.1, .1),
            scrollSize = 1,
            pageSize = 1,
            range = (-180, 180),
            value = self.getPart('head', self.getLODNames()[0]).getH(),
            scale = 0.2,
            command = self.__setHeadH
        )

        self.headPSlider = DirectSlider(
            parent = self.headTab,
            pos = (0, 0, .2),
            frameSize = (-1, 1, -.1, .1),
            scrollSize = 1,
            pageSize = 1,
            range = (-180, 180),
            value = self.getPart('head', self.getLODNames()[0]).getP(),
            scale = 0.2,
            command = self.__setHeadP
        )

        self.headRSlider = DirectSlider(
            parent = self.headTab,
            pos = (0, 0, .1),
            frameSize = (-1, 1, -.1, .1),
            scrollSize = 1,
            pageSize = 1,
            range = (-180, 180),
            value = self.getPart('head', self.getLODNames()[0]).getR(),
            scale = 0.2,
            command = self.__setHeadR
        )

        toonAnimList = []
        animLists: List[Tuple[Tuple[str, str], ...]] = [
            Phase3AnimList,
            Phase3_5AnimList,
            Phase4AnimList,
            Phase5AnimList,
            Phase6AnimList,
            Phase5_5AnimList,
            Phase9AnimList,
            Phase10AnimList,
            Phase12AnimList,
        ]

        for aList in animLists:
            item: Tuple[str, str]
            for item in aList:
                toonAnimList.append(item[0])
        toonAnimList.sort()

        animPageNum = 0
        y = 0.3

        for i, anim in enumerate(toonAnimList):
            if i % 10 == 0:
                y = 0.3
                animPageNum += 1
                newPage = DirectFrame(
                    relief = None,
                    parent = self.gui
                )
                newPage.hide()

                setattr(self, f'animPage{animPageNum}', newPage)
                if animPageNum != 1:
                    backBtn = DirectButton(
                                parent = newPage,
                                pos = (-.13, 0, -0.25),
                                frameSize = (-2.5, 2.5, -1, 1),
                                text = 'BACK\n<<',
                                text_pos = (0, 0.15),
                                text_scale = 0.7,
                                scale = 0.05,
                                command = self.setTab,
                                extraArgs = [getattr(self, f'animPage{animPageNum-1}')]
                            )
                else:
                    backBtn = DirectButton(
                                parent = newPage,
                                pos = (-.13, 0, -0.25),
                                frameSize = (-2.5, 2.5, -1, 1),
                                text = 'BACK\n<<',
                                text_pos = (0, 0.15),
                                text_scale = 0.7,
                                scale = 0.05,
                                command = self.setTab,
                                extraArgs = [self.mainTab]
                            )
                homeBtn = DirectButton(
                    parent = newPage,
                    pos = (-.13, 0, -0.36),
                    frameSize = (-2.5, 2.5, -1, 1),
                    text = 'Home',
                    text_pos = (0, -0.2),
                    text_scale = 0.7,
                    scale = 0.05,
                    command = self.setTab,
                    extraArgs = [self.mainTab]
                )

                poseTabBtn = DirectButton(
                    parent = newPage,
                    pos = (.13, 0, -0.36),
                    frameSize = (-2.5, 2.5, -1, 1),
                    text = 'Pose',
                    text_pos = (0, -0.2),
                    text_scale = 0.7,
                    scale = 0.05,
                    command = self.setTab,
                    extraArgs = [self.poseTab]
                )

                if hasattr(self, f'animPage{animPageNum-1}'):
                    lastPage = getattr(self, f'animPage{animPageNum-1}')
                    nextBtn = DirectButton(
                                parent = lastPage,
                                pos = (.13, 0, -0.25),
                                frameSize = (-2.5, 2.5, -1, 1),
                                text = 'NEXT\n>>',
                                text_pos = (0, 0.15),
                                text_scale = 0.7,
                                scale = 0.05,
                                command = self.setTab,
                                extraArgs = [getattr(self, f'animPage{animPageNum}')]
                            )

                self.guiTabs.append(getattr(self, f'animPage{animPageNum}'))
            animButton = DirectButton(
                parent = getattr(self, f'animPage{animPageNum}'),
                pos = (
                    -0.13 if i % 2 == 0 else 0.13,
                    0,
                    y
                ),
                frameSize = (-2.5, 2.5, -1, 1),
                text = anim,
                text_pos = (0, -0.2),
                text_scale = 0.7,
                scale = 0.05,
                command = self.loop,
                extraArgs = [anim]
            )

            if i % 2 == 1:
                y -= 0.11

            self.animButton['extraArgs'] = [getattr(self, 'animPage1')]

    def loop(self, animName: str, restart: bool = True,
             partName: Optional[str] = None,
             fromFrame: Optional[int] = None,
             toFrame: Optional[int] = None):
        self.lastAnim = animName
        Toon.loop(self, animName, restart, partName, fromFrame, toFrame)

    def __loopCurrentAnim(self):
        Toon.loop(self, self.lastAnim)

    def __poseCurrent(self):
        if self.poseTab.isHidden():
            return
        self.lastPoseVal = self.poseSlider.getValue()
        self.pose(self.lastAnim, self.getNumFrames(self.lastAnim) * self.poseSlider.getValue())

    def __setHeadH(self):
        self.getPart('head', self.getLODNames()[0]).setH(self.headHSlider.getValue())

    def __setHeadP(self):
        self.getPart('head', self.getLODNames()[0]).setP(self.headPSlider.getValue())

    def __setHeadR(self):
        self.getPart('head', self.getLODNames()[0]).setR(self.headRSlider.getValue())

    def __resetHeadRotation(self):
        self.headHSlider['value'] = 0.0
        self.headPSlider['value'] = 0.0
        self.headRSlider['value'] = 0.0
        self.stopLookAroundNow()

class MovieMakerCog(MovieMakerActor, Suit):

    def __init__(self, scene):
        MovieMakerActor.__init__(self, scene)
        Suit.__init__(self)
        self.lastAnim = 'neutral'
        self.lastPoseVal: float = -1
        self.reparentTo(render)
        self.setTag('actor', str(hash(self.getGeomNode())))
        self.nodeHash = str(hash(self.getGeomNode()))

    def toJson(self):
        dict = MovieMakerActor.toJson(self)
        dict['type'] = self.__class__.__name__
        dict['dna'] = self.getStyle().makeNetString()
        dict['name'] = self.getName()
        dict['initPosHprScale'] = (*self.getPos(), *self.getHpr(), *self.getScale())
        return dict

    def openEditor(self):
        MovieMakerActor.openEditor(self)
        self.title['text'] = self.getName()
        guiModel = MovieMakerGUI.gui
        self.neutralAnimButton = DirectButton(
            parent = self.mainTab,
            pos = (-.13, 0, .3),
            frameSize = (-2.5, 2.5, -1, 1),
            text = 'Neutral',
            text_pos = (0, -0.2),
            text_scale = 0.7,
            scale = 0.05,
            command = self.loop,
            extraArgs = ['neutral']
        )

        self.animButton = DirectButton(
            parent = self.mainTab,
            pos = (.13, 0, .3),
            frameSize = (-2.5, 2.5, -1, 1),
            text = 'Anims',
            text_pos = (0, -0.2),
            text_scale = 0.7,
            scale = 0.05,
            command = self.setTab
        )

        self.loopButton = DirectButton(
            parent = self.mainTab,
            pos = (-.13, 0, .19),
            frameSize = (-2.5, 2.5, -1, 1),
            text = 'Loop',
            text_pos = (0, -0.2),
            text_scale = 0.7,
            scale = 0.05,
            command = self.__loopCurrentAnim
        )

        self.poseButton = DirectButton(
            parent = self.mainTab,
            pos = (.13, 0, .19),
            frameSize = (-2.5, 2.5, -1, 1),
            text = 'Pose',
            text_pos = (0, -0.2),
            text_scale = 0.7,
            scale = 0.05,
            command = self.setTab,
        )

        self.propsTab = DirectFrame(
                relief = None,
                parent = self.gui
        )

        self.propsTabBtn = DirectButton(
                relief = None,
                parent = self.gui,
                pos = (-.15, 0, .5385),
                image = guiModel.find('**/actor_tab_properties'),
                image_scale = OTPGUIUtils.getImageScale(105, 87),
                scale = 0.08,
                command = self.setTab,
                extraArgs = [self.propsTab]
        )
        self.propsTab.hide()
        self.guiTabs.append(self.propsTab)

        self.poseTab = DirectFrame(
            relief = None,
            parent = self.gui
        )
        self.poseTab.hide()

        self.guiTabs.append(self.poseTab)

        self.poseButton['extraArgs'] = [self.poseTab]

        self.poseSlider = DirectSlider(
            parent = self.poseTab,
            pos = (0, 0, 0.3),
            frameSize = (-1, 1, -.1, .1),
            scrollSize = 1,
            pageSize = 1,
            scale = 0.2,
            value = self.lastPoseVal,
            command = self.__poseCurrent
        )

        self.poseBackButton = DirectButton(
            parent = self.poseTab,
            pos = (-.13, 0, -0.25),
            frameSize = (-2.5, 2.5, -1, 1),
            text = 'BACK\n<<',
            text_pos = (0, 0.15),
            text_scale = 0.7,
            scale = 0.05,
            command = self.setTab,
            extraArgs = [self.mainTab]
        )

        toonAnimList = []
        animLists: List[Tuple[Tuple[str, str], ...]] = [
            AllSuits,
            AllSuitsMinigame,
            AllSuitsTutorialBattle,
            AllSuitsBattle,
            SuitsCEOBattle,
            SuitBattleAnims['all'],
            SuitBattleAnims[self.getBodyType()]
        ]


        for aList in animLists:
            item: Tuple[str, str]
            for item in aList:
                toonAnimList.append(item[0])
        toonAnimList.sort()

        animPageNum = 0
        y = 0.3

        for i, anim in enumerate(toonAnimList):
            if i % 10 == 0:
                y = 0.3
                animPageNum += 1
                newPage = DirectFrame(
                    relief = None,
                    parent = self.gui
                )
                newPage.hide()

                setattr(self, f'animPage{animPageNum}', newPage)
                if animPageNum != 1:
                    backBtn = DirectButton(
                                parent = newPage,
                                pos = (-.13, 0, -0.25),
                                frameSize = (-2.5, 2.5, -1, 1),
                                text = 'BACK\n<<',
                                text_pos = (0, 0.15),
                                text_scale = 0.7,
                                scale = 0.05,
                                command = self.setTab,
                                extraArgs = [getattr(self, f'animPage{animPageNum-1}')]
                            )
                else:
                    backBtn = DirectButton(
                                parent = newPage,
                                pos = (-.13, 0, -0.25),
                                frameSize = (-2.5, 2.5, -1, 1),
                                text = 'BACK\n<<',
                                text_pos = (0, 0.15),
                                text_scale = 0.7,
                                scale = 0.05,
                                command = self.setTab,
                                extraArgs = [self.mainTab]
                            )
                homeBtn = DirectButton(
                    parent = newPage,
                    pos = (-.13, 0, -0.36),
                    frameSize = (-2.5, 2.5, -1, 1),
                    text = 'Home',
                    text_pos = (0, -0.2),
                    text_scale = 0.7,
                    scale = 0.05,
                    command = self.setTab,
                    extraArgs = [self.mainTab]
                )

                poseTabBtn = DirectButton(
                    parent = newPage,
                    pos = (.13, 0, -0.36),
                    frameSize = (-2.5, 2.5, -1, 1),
                    text = 'Pose',
                    text_pos = (0, -0.2),
                    text_scale = 0.7,
                    scale = 0.05,
                    command = self.setTab,
                    extraArgs = [self.poseTab]
                )

                if hasattr(self, f'animPage{animPageNum-1}'):
                    lastPage = getattr(self, f'animPage{animPageNum-1}')
                    nextBtn = DirectButton(
                                parent = lastPage,
                                pos = (.13, 0, -0.25),
                                frameSize = (-2.5, 2.5, -1, 1),
                                text = 'NEXT\n>>',
                                text_pos = (0, 0.15),
                                text_scale = 0.7,
                                scale = 0.05,
                                command = self.setTab,
                                extraArgs = [getattr(self, f'animPage{animPageNum}')]
                            )

                self.guiTabs.append(getattr(self, f'animPage{animPageNum}'))
            animButton = DirectButton(
                parent = getattr(self, f'animPage{animPageNum}'),
                pos = (
                    -0.13 if i % 2 == 0 else 0.13,
                    0,
                    y
                ),
                frameSize = (-2.5, 2.5, -1, 1),
                text = anim,
                text_pos = (0, -0.2),
                text_scale = 0.7,
                scale = 0.05,
                command = self.loop,
                extraArgs = [anim]
            )

            if i % 2 == 1:
                y -= 0.11

            self.animButton['extraArgs'] = [getattr(self, 'animPage1')]

    def loop(self, animName: str, restart: bool = True,
             partName: Optional[str] = None,
             fromFrame: Optional[int] = None,
             toFrame: Optional[int] = None):
        self.lastAnim = animName
        Suit.loop(self, animName, restart, partName, fromFrame, toFrame)

    def __loopCurrentAnim(self):
        Suit.loop(self, self.lastAnim)

    def __poseCurrent(self):
        if self.poseTab.isHidden():
            return
        self.lastPoseVal = self.poseSlider.getValue()
        self.pose(self.lastAnim, self.getNumFrames(self.lastAnim) * self.poseSlider.getValue())


class MovieMakerBaseNode:

    def __init__(self, actor: MovieMakerActor):
        self.actor = actor
        return

    def evaluate(self) -> Interval:
        raise Exception('Cannot call this on a base node. we shouldnt even have any')

    def toJson(self) -> Dict:
        raise Exception('Cannot call this on a base node. we shouldnt even have any')


class MovieMakerSetPos(MovieMakerBaseNode):

    def __init__(self, actor: MovieMakerActor, x: float, y: float, z: float):
        MovieMakerBaseNode.__init__(self, actor)
        self._toPos = Vec3(x, y, z)

    def evaluate(self) -> Interval:
        return Func(self.actor.setPos, self._toPos)

    def toJson(self) -> Dict:
        return {
            "type": self.__class__.__name__,
            "args": [*self._toPos]
        }


class MovieMakerLerpPos(MovieMakerBaseNode):

    def __init__(self, actor: MovieMakerActor, duration: float, x: float, y: float, z: float):
        MovieMakerBaseNode.__init__(self, actor)
        self._duration = duration
        self._toPos = Vec3(x, y, z)

    def evaluate(self) -> Interval:
        return LerpPosInterval(self.actor, self._duration, self._toPos)

    def toJson(self) -> Dict:
        return {
            "type": self.__class__.__name__,
            "args": [self._duration, *self._toPos]
        }


class MovieMakerActorLoop(MovieMakerBaseNode):

    def __init__(self, actor: MovieMakerActor, anim: str, speed: float):
        MovieMakerBaseNode.__init__(self, actor)
        self._anim = anim
        self._speed = speed

    def evaluate(self) -> Interval:
        return Parallel(
                Func(self.actor.setPlayRate, self._speed),
                Func(self.actor.loop, self._anim))

    def toJson(self) -> Dict:
        return {
            "type": self.__class__.__name__,
            "args": [self._anim, self._speed]
        }
