from typing import Optional

from direct.gui.DirectGui import *
from panda3d.core import *

from otp.otpgui import OTPGUIUtils
from toontown.datapack.DataPackManager import DataPackManager
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer

import random
import time

from toontown.toonbase.ControlManager import ControlManager


class ToontownOfflineLoadingScreen:

    def __init__(self):
        self.__expectedCount = 0
        self.__count = 0

        self.backgroundImages = {}
        self.backgroundImage = None

        filePath = 'phase_3/maps/loading/loading_'
        for type in ToontownGlobals.LoadingScreenInfo:
            backgrounds = []
            for num in range(1, type[1] + 1):
                img = filePath + type[0] + '_' + str(num) + '.png'
                backgrounds.append(img)
            self.backgroundImages[type[0]] = backgrounds

        self.gui = aspect2d.attachNewNode('loading_gui')
        holidayIndex = self.getActiveHoliday()
        textColor = ToontownGlobals.HolidayColors[holidayIndex]
        shadow = (0, 0, 0, 1)
        self.title = DirectLabel(guiId='ToontownLoadingScreenTitle', parent=self.gui, relief=None,
                                 text_font = ToontownGlobals.getBuildingNametagFont(),
                                 pos=(0, 0, -0.77), text='', textMayChange=1, text_scale=0.08,
                                 text_fg=textColor, text_align=TextNode.ACenter, text_shadow=shadow)
        self.tip = DirectLabel(guiId='ToontownLoadingScreenTip', parent=self.gui, relief=None, text='',
                               text_scale=0.05, textMayChange=1, pos=(0.0, 0.0, -0.95),
                               text_fg=textColor, text_style=3, text_align=TextNode.ACenter)
        self.logo = None
        self.serverVersion = config.GetString('server-version', 'no_version_set')

        loadingGui = loader.loadModel('phase_3/models/gui/loading-background')

        self.shadow = loadingGui.find('**/bar_shadow')
        self.shadow.wrtReparentTo(aspect2d)

        self.backgroundOverlay = OnscreenImage(parent = hidden, image = 'phase_3/maps/ttrm_t_gui_loading_overlay.png',
                                               scale = (2, 1, 1))
        self.backgroundOverlay.setTransparency(TransparencyAttrib.MAlpha)


        self.pictureImage = loader.loadModel('phase_3.5/models/gui/photo_frame')
        self.pictureImage.setScale(0.39, 1, 0.3)
        self.pictureImage.setPos(0, 0, 0)
        self.pictureImage.reparentTo(hidden)

        self.logo = OnscreenImage(
                parent = self.gui,
                image = 'phase_3/maps/ttrm_t_gameLogo.png',
                scale = (1.4, 1, .7)
        )
        self.logo.setTransparency(TransparencyAttrib.MAlpha)
        loadingGui.removeNode()

        self.version = DirectLabel(text=self.serverVersion, parent=base.a2dpBottomRight,
                                   relief=None, pos=(-0.1, 0, 0.1), scale=0.05,
                                   text_fg=ToontownGlobals.HolidayColors[holidayIndex],
                                   text_align=TextNode.ARight, text_shadow=(0, 0, 0, 1))
        self.version.setBin('gui-popup', 0)

    def destroy(self):
        self.title.destroy()
        self.tip.destroy()
        self.pictureImage.removeNode()
        self.gui.removeNode()
        self.version.destroy()

    def getTip(self, tipCategory):
        if isinstance(tipCategory, int):
            tips = TTLocalizer.TipDict.get(tipCategory)
        elif isinstance(tipCategory, list):
            tips = ()
            for category in tipCategory:
                tip = TTLocalizer.TipDict.get(category)
                tips += tip
        else:
            return TTLocalizer.TipTitle
        tip = random.choice(tips)
        if '$$' in tip:
            tip = ControlManager.parseHotkeyString(tip, useGlyphs = True)
        return TTLocalizer.TipTitle + tip

    def begin(self, waitRange, label, gui, tipCategory, zoneId: Optional[int]):
        if tipCategory:
            self.tip['text'] = self.getTip(tipCategory)
        else:
            self.tip['text'] = ''

        self.title['text'] = label

        self.__count = 0
        self.__expectedCount = waitRange

        if gui:
            allowedImages = []
            holidayIndex = self.getActiveHoliday()
            episode = base.cr.episodeManager.getEpisode() if base.cr.episodeManager else 'no'
            for type in self.backgroundImages.keys():
                images = self.backgroundImages.get(type)
                if type in ('toons', 'cogs', episode):
                    allowedImages.extend(images)
                elif type == 'halloween' and holidayIndex == ToontownGlobals.HolidayHalloween:
                    allowedImages.extend(images)
                elif type == 'winter' and holidayIndex == ToontownGlobals.HolidayWinter:
                    allowedImages.extend(images)
                elif type == 'fools' and holidayIndex == ToontownGlobals.HolidayAprilFools:
                    allowedImages.extend(images)
            if not allowedImages:
                type = random.choice(('toons', 'cogs'))
                images = self.backgroundImages.get(type)
                allowedImages.extend(images)
            random.seed(time.time())
            imgPath = random.choice(allowedImages)
            textColor = ToontownGlobals.HolidayColors[holidayIndex]
            if zoneId is None:
                self.backgroundOverlay['image'] = DataPackManager.getTexture(f'phase_3/maps/ttoff_t_gui_loadingBg_img{random.randint(1, 5)}.png')
            else:
                self.backgroundOverlay['image'] = DataPackManager.getTexture(f'phase_3/maps/loading/zone/ttrm_t_gui_loadingZone_{zoneId}.png')
            self.backgroundOverlay.reparentTo(self.gui)
            self.backgroundOverlay.setShader(Shader.load(Shader.SLGLSL,
                                                         vertex = 'phase_3/shaders/ttoff_sha_ui_generic.vert',
                                                         fragment = 'phase_3/shaders/ttrm_sha_ui_loadingScreen_background.frag'
                                                         ))
            self.backgroundOverlay.setShaderInput('progress', 0.0)
            self.pictureImage.reparentTo(self.gui)
            self.backgroundImage = OnscreenImage(
                image=imgPath, pos=(0, 0, -0.145),
                scale=OTPGUIUtils.getImageScale(1280, 720, .4))
            self.backgroundImage.flattenMedium()
            self.backgroundImage.reparentTo(self.gui)
            self.shadow.reparentTo(base.hidden)
            self.tip['text_fg'] = textColor
            self.tip.reparentTo(self.gui)


            self.logo['scale'] = (0.9, 1, .45)
            self.logo.setPos(0, 0, .65)
            self.logo.reparentTo(self.gui, DGG.NO_FADE_SORT_INDEX)
            self.version.reparentTo(hidden)

            self.title['text_fg'] = textColor
            self.title.reparentTo(self.gui)
            self.gui.reparentTo(aspect2dp, DGG.NO_FADE_SORT_INDEX)
        else:
            self.backgroundImage = OnscreenImage(
                    image=f'phase_3/maps/ttoff_t_gui_loadingBg_img{random.randint(1, 5)}.png',
                    pos=(0, 0, 0), scale=(2., 1, 1))
            self.backgroundImage.reparentTo(aspect2dp, DGG.NO_FADE_SORT_INDEX)
            self.logo.reparentTo(aspect2dp, DGG.NO_FADE_SORT_INDEX)
            self.logo['scale'] = (1.4, 1, .7)
            self.logo.setPos(0, 0, .15)
            self.tip.reparentTo(aspect2dp, DGG.NO_FADE_SORT_INDEX)
            self.shadow.reparentTo(aspect2dp, DGG.NO_FADE_SORT_INDEX)
            self.shadow.setScale(1.32, 1.0, 1.0)
            self.version.reparentTo(base.a2dpBottomRight, DGG.NO_FADE_SORT_INDEX)
            self.title.reparentTo(aspect2dp, DGG.NO_FADE_SORT_INDEX)
            self.gui.reparentTo(hidden)

    def end(self, name):
        self.backgroundOverlay.setShaderInput('progress', 1.0)
        base.graphicsEngine.renderFrame()
        if self.backgroundImage:
            self.backgroundImage.reparentTo(self.gui)
        self.logo.reparentTo(self.gui)
        self.tip.reparentTo(self.gui)
        self.shadow.reparentTo(self.gui)
        self.title.reparentTo(self.gui)
        self.version.reparentTo(self.gui)
        self.backgroundOverlay.reparentTo(self.gui)
        self.gui.reparentTo(hidden)

        # Cleanup loading screen image
        if self.backgroundImage:
            self.backgroundImage.destroy()
            self.backgroundImage = None

        return (self.__expectedCount, self.__count)

    def abort(self):
        self.gui.reparentTo(hidden)

        # Cleanup loading screen image
        if self.backgroundImage:
            self.backgroundImage.destroy()
            self.backgroundImage = None

    def tick(self, updateBar = True):
        self.__count = self.__count + 1
        if updateBar:
            self.backgroundOverlay.setShaderInput('progress', self.__count / self.__expectedCount)
            base.graphicsEngine.renderFrame()

    def getActiveHoliday(self):
        currentTime = time.localtime()
        if currentTime.tm_mon == ToontownGlobals.HalloweenStart[0] and currentTime.tm_mday >= ToontownGlobals.HalloweenStart[1]:
            holidayIndex = ToontownGlobals.HolidayHalloween
        elif (currentTime.tm_mon == ToontownGlobals.WinterStart[0] and currentTime.tm_mday >= ToontownGlobals.WinterStart[1]) or (currentTime.tm_mon == ToontownGlobals.WinterEnd[0] and currentTime.tm_mday <= ToontownGlobals.WinterEnd[1]):
            holidayIndex = ToontownGlobals.HolidayWinter
        elif currentTime.tm_mon == ToontownGlobals.AprilFoolsStart[0] and currentTime.tm_mday == ToontownGlobals.AprilFoolsStart[1]:
            holidayIndex = ToontownGlobals.HolidayAprilFools
        else:
            holidayIndex = ToontownGlobals.HolidayNormal

        return holidayIndex
