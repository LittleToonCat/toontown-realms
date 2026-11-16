from typing import List

from direct.fsm.FSM import FSM
from direct.gui import DirectGuiGlobals
from direct.gui.DirectButton import DirectButton
from direct.gui.DirectFrame import DirectFrame
from direct.gui.OnscreenImage import OnscreenImage
from panda3d.core import NodePath, VBase4, Vec3

from otp.otpgui import OTPGUIUtils
from toontown.datapack.DataPackManager import DataPackManager
from toontown.sandbox import PropGlobals
from toontown.toon.NPCToons import NPCToonDict
from toontown.toonbase.ToontownTypes import CogAppearanceIndex
from toontown.toontowngui.ToontownScrolledGridFrame import ToontownScrolledGridFrame

BROWSER_HIDDEN = (0.895, 0, -0.35)
BROWSER_OPEN = (0.895, 0, 0.35)


class MovieMakerGUI(FSM):
    gui: NodePath = loader.loadModel('phase_3/models/gui/ttrm_m_gui_mvmk')
    iconBg: NodePath = gui.find('**/icon_bg')
    iconGui: NodePath = loader.loadModel('phase_3.5/models/gui/ttrm_m_gui_mvmk_brwsrIcns')

    def __init__(self, movieMaker):
        FSM.__init__(self, 'MMGUI')
        self.movieMaker = movieMaker

        self.browser = ToontownScrolledGridFrame(
            parent = base.a2dBottomLeft,
            pos = BROWSER_OPEN,
            relief = None,
            image = self.gui.find('**/browser'),
            image_scale = OTPGUIUtils.getImageScale(1516, 593, 0.7),
            image_color = VBase4(1.0, 1.0, 1.0, 0.6),
            height = .33,
            width = .88,
            itemPadding = .16,
            itemMargin = (-.56, -.17),
            itemsPerRow = 10,
        )

        self.browserIcons: List[DirectButton] = []

        self.closeTab = DirectButton(
            relief = None,
            parent = self.browser,
            pos = (0.83, 0, 0.41),
            scale = 0.08,
            image = self.gui.find('**/tab_close'),
            command = lambda: self.request('NoTab')
        )

        self.toonTab = DirectButton(
            #relief = None,
            parent = self.browser,
            pos = (-0.79, 0, 0.39),
            scale = 0.04,
            text = 'NPC TOONS',
            text_scale = 0.8,
            text_pos = (0, -0.2),
            frameSize = (-2.5, 2.5, -1, 1),
            # image = self.gui.find('**/tab_close'),
            # image_scale = OTPGUIUtils.getImageScale(290, 114),
            command = lambda: self.request('Toons')
        )

        self.propsTab = DirectButton(
            #relief = None,
            parent = self.browser,
            pos = (-0.59, 0, 0.39),
            scale = 0.04,
            text = 'COGS',
            text_scale = 0.8,
            text_pos = (0, -0.2),
            frameSize = (-2.5, 2.5, -1, 1),
            #image = self.gui.find('**/tab_close'),
            #image_scale = OTPGUIUtils.getImageScale(290, 114),
            command = lambda: self.request('Cogs')
        )


        self.propsTab = DirectButton(
            #relief = None,
            parent = self.browser,
            pos = (-0.39, 0, 0.39),
            scale = 0.04,
            text = 'Props',
            text_scale = 0.8,
            text_pos = (0, -0.2),
            frameSize = (-2.5, 2.5, -1, 1),
            #image = self.gui.find('**/tab_close'),
            #image_scale = OTPGUIUtils.getImageScale(290, 114),
            command = lambda: self.request('Props')
        )

        self.settingsTabButton = DirectButton(
            #relief = None,
            parent = self.browser,
            pos = (-0.19, 0, 0.39),
            scale = 0.04,
            text = 'Settings',
            text_scale = 0.8,
            text_pos = (0, -0.2),
            frameSize = (-2.5, 2.5, -1, 1),
            # image = self.gui.find('**/tab_close'),
            # image_scale = OTPGUIUtils.getImageScale(290, 114),
            command = lambda: self.request('Settings')
        )

        self.request('NoTab')

    def enterToons(self):
        self.browser.setPos(BROWSER_OPEN)
        for icon in self.browserIcons:
            icon.destroy()
            del icon
        self.browserIcons = []
        _scale = 0.15
        for key, val in NPCToonDict.items():
            btn = DirectButton(
                parent = hidden,
                image = self.gui.find('**/icon_bg'),
                text = f'{key}\n{val[1]}',
                text_pos = (0, .3),
                text_wordwrap = 5,
                text_scale = 0.14,
                relief = None,
                scale = 0.15,
                command = self.movieMaker.placeToon,
                extraArgs = [key]
            )
            self.browserIcons.append(btn)

        self.browser.addItems(*self.browserIcons)
        self.closeTab.show()

    def exitToons(self):
        self.browser.clearItems()
        self.browserIcons = []

    def enterCogs(self):
        self.browser.setPos(BROWSER_OPEN)
        for icon in self.browserIcons:
            icon.destroy()
            del icon
        self.browserIcons = []
        _scale = 0.15
        if hasattr(base.cr, 'dataPackMgr'):
            for name, app in base.cr.dataPackMgr.getCogAppearances().items():
                btn = DirectButton(
                    parent = hidden,
                    image = self.gui.find('**/icon_bg'),
                    text = f'{name}\n\n{DataPackManager.getLocalizedText(app[CogAppearanceIndex.NAME])}',
                    text_pos = (0, .3),
                    text_wordwrap = 5,
                    text_scale = 0.14,
                    relief = None,
                    scale = 0.15,
                    command = self.movieMaker.placeCog,
                    extraArgs = [name]
                )
                self.browserIcons.append(btn)
        else:
            btn = DirectButton(
                parent = hidden,
                image = self.gui.find('**/icon_bg'),
                text = 'YOU MUST LOAD INTO A SERVER OR OFFLINE MODE',
                text_pos = (0, .3),
                text_wordwrap = 5,
                text_scale = 0.14,
                relief = None,
                scale = 0.15
            )
            self.browserIcons.append(btn)
            btn = DirectButton(
                parent = hidden,
                image = self.gui.find('**/icon_bg'),
                text = 'THEN EXIT TO MAIN MENU TO USE COGS IN MOVIE MAKER',
                text_pos = (0, .3),
                text_wordwrap = 5,
                text_scale = 0.14,
                relief = None,
                scale = 0.15
            )
            self.browserIcons.append(btn)

        self.browser.addItems(*self.browserIcons)
        self.closeTab.show()

    def exitCogs(self):
        self.browser.clearItems()
        self.browserIcons = []

    def enterProps(self):
        self.browser.setPos(BROWSER_OPEN)
        for i, dat in enumerate(PropGlobals.PropList):
            icon: NodePath = self.iconGui.find(f"**/bsr_ico_{dat.lower().replace(' ', '_')}")

            btn = DirectButton(
                parent = hidden,
                image = self.iconBg,
                # text = dat[0],
                # text_pos = (0, .3),
                # text_wordwrap = 5,
                # text_scale = 0.14,
                relief = None,
                scale = 0.15
                # command = dat[1],
                # extraArgs = [dat[2]]
            )
            if not icon.isEmpty():
                icon.setScale(.8)
                icon.instanceTo(btn)
            self.browserIcons.append(btn)
        self.browser.addItems(*self.browserIcons)
        self.closeTab.show()

    def exitProps(self):
        self.browser.clearItems()
        self.browserIcons = []

    def tempMoveSkybox(self):
        """until i properly parent it to the camera or something"""
        self.movieMaker.sky.setPos(base.camera.getPos(render))


    def enterSettings(self):
        self.browser.setPos(BROWSER_OPEN)
        for icon in self.browserIcons:
            icon.destroy()
            del icon
        self.browserIcons = []
        _scale = 0.15
        for i, dat in enumerate(
                [
                    ('Show World', self.movieMaker.geom.show, []),
                    ('Hide World', self.movieMaker.geom.hide, []),
                    ('Show Actors', self.movieMaker.actorLayer.show, []),
                    ('Hide Actors', self.movieMaker.actorLayer.hide, []),
                    ('Save Screenshot', self.movieMaker.screenshot, []),
                    ('FOV 30', base.camLens.setMinFov, [30]),
                    ('FOV 40', base.camLens.setMinFov, [40]),
                    ('FOV 60', base.camLens.setMinFov, [60]),
                    ('Background Grey', base.setBackgroundColor, [0.2, 0.2, 0.2, 0.0]),
                    ('DDL Color', base.render.setColorScale, [0.85, 0.85, 0.9, 1]),
                    ('REG Color', base.render.setColorScale, [1, 1, 1, 1]),
                    ('Move Skybox', self.tempMoveSkybox, []),
                    #('Hide Dev Branding', base.WIP_LABEL.hide, [])
                ]):
            btn = DirectButton(
                parent = base.hidden,
                image = self.gui.find('**/icon_bg'),
                text = dat[0],
                text_pos = (0, .3),
                text_wordwrap = 5,
                text_scale = 0.14,
                relief = None,
                scale = 0.15,
                command = dat[1],
                extraArgs = dat[2]
            )
            self.browserIcons.append(btn)

        self.browser.addItems(*self.browserIcons)
        self.closeTab.show()

    def exitSettings(self):
        self.browser.clearItems()
        self.browserIcons = []

    def enterNoTab(self):
        self.browser.setPos(BROWSER_HIDDEN)

        self.closeTab.hide()

    def exitNoTab(self):
        pass
