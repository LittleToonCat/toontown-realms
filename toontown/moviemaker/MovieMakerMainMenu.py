from typing import Dict, Optional, List

from direct.fsm.FSM import FSM
from direct.gui import DirectGuiGlobals
from direct.gui.DirectButton import DirectButton
from direct.stdpy.file import listdir
import json
from otp.otpgui import OTPGUIUtils
from toontown.moviemaker.MovieMaker import MovieMaker
from toontown.toontowngui.ToontownScrolledFrame import ToontownScrolledFrame


class MovieMakerMainMenu(FSM):

    def __init__(self):
        FSM.__init__(self, 'MovieMakerMenu')
        self.__selectedEnvironment: Optional[Dict] = None

    def enterHome(self):
        self.newSceneButton = DirectButton(
                parent = aspect2d,
                pos = (0, 0, 0),
                text = '$new scene',
                scale = 0.1,
                command = self.__newScene
        )

    def exitHome(self):
        self.newSceneButton.destroy()

    def __newScene(self):
        self.request('NewScene')

    def enterNewScene(self):
        # load the scene options

        settingsScrollbarModel = loader.loadModel('phase_3.5/models/gui/ttoff_m_gui_sbk_generic', allowInstance = True)
        self.areaList = ToontownScrolledFrame(parent = aspect2d,
                                              relief = DirectGuiGlobals.SUNKEN,
                                              borderWidth = (0.01, 0.01),
                                              pos = (0, 0.0, 0),
                                              height = 0.6,
                                              width = .63,
                                              itemMargin = (.05, 0),
                                              itemPadding = .12,
                                              frameColor = (0.85, 0.95, 1, 1),
                                              autoHideScrollBars = True,
                                              manageScrollBars = False,
                                              verticalScroll_frameColor = (0, 0, 0, 0),
                                              verticalScroll_manageButtons = False,
                                              verticalScroll_thumb_geom = (
                                                  settingsScrollbarModel.find('**/scrollbar_normal'),
                                                  settingsScrollbarModel.find('**/scrollbar_press'),
                                                  settingsScrollbarModel.find('**/scrollbar_hover')),
                                              verticalScroll_thumb_geom_scale = OTPGUIUtils.getImageScale(151, 399, 0.15),
                                              verticalScroll_thumb_relief = None,
                                              verticalScroll_resizeThumb = False,
                                              verticalScroll_decButton_relief = None,
                                              verticalScroll_incButton_relief = None)

        areaFiles = []
        if __debug__:
            # This works differently on DEV
            for file in listdir("resources/phase_3/data/movie_environments/"):
                if file.endswith('.json'):
                    areaFiles.append(f'resources/phase_3/data/movie_environments/{file}')
        else:
            for file in listdir("/phase_3/data/movie_environments/"):
                if file.endswith('.json'):
                    areaFiles.append(f'/phase_3/data/movie_environments/{file}')

        btns: List[DirectButton] = []
        for file in areaFiles:
            with open(file, 'r') as sceneFile:
                jsonData = json.load(sceneFile)
                btn = DirectButton(
                        parent = aspect2d,
                        pos = (0, 0, 0),
                        text = jsonData['name'],
                        scale = 0.1,
                        command = self.__setSelectedEnvironment,
                        extraArgs = [jsonData])
                btns.append(btn)

        self.areaList.addItems(*btns)

        return

    def exitNewScene(self):
        self.areaList.destroy()

    def __setSelectedEnvironment(self, environment: Dict):
        self.__selectedEnvironment = environment
        self.request('SceneEditing')

    def __createScene(self):
        self.request('SceneEditing')

    def enterSceneEditing(self):
        self.activeScene = MovieMaker()
        self.activeScene.loadEnvironment(self.__selectedEnvironment)

    def exitSceneEditing(self):
        pass