from typing import Optional

from direct.gui.DirectGui import *

from panda3d.core import *

from toontown.toonbase import ToontownGlobals, ClientSettings
from toontown.toonbase import TTLocalizer

import random
import time

from toontown.toonbase.ControlManager import ControlManager


class ToontownLoadingScreen:

    def __init__(self):

        self.__expectedCount = 0
        self.__count = 0

        self.gui = loader.loadModel('phase_3/models/gui/progress-background-retro')

        # TODO: Add a "Retro Mode" setting for the original, 2003 loading screen.
        #  Right now, we have a retro mode option to toggle the TTOff loading screen vs. Disney's
        #  However, when we decide to add the 2003 version, this toggle should become an integer instead of a bool like it is now
        #  0 would be TTOff, 1 would be 2013 TTO, and 2 would be 2003 TTO
        #  If we do make this change, don't forget to change it in ToontownStart as well
        self.retroMode = ClientSettings.ClassicLoadingScreen.get()

        if self.retroMode:
            image = loader.loadTexture("phase_3.5/maps/trolley.png")
            self.banner = DirectLabel(parent=self.gui, relief=None, sortOrder=0, image=image, scale=0.625)
            self.banner.setTransparency(TransparencyAttrib.MAlpha)
            self.logo = DirectLabel(parent=self.gui, relief=None, sortOrder=1, image=self.gui.find("**/logo"))
            self.gui.find("**/logo").hide()
        else:
            self.banner = loader.loadModel('phase_3/models/gui/toon_council').find('**/scroll')
            self.banner.reparentTo(self.gui)
            self.banner.setScale(0.4, 0.4, 0.4)

        self.tip = DirectLabel(guiId='ToontownLoadingScreenTip', parent=self.banner, relief=None, text='',
                               text_scale=TTLocalizer.TLStip, textMayChange=1, pos=(-1.2, 0.0, 0.1),
                               text_fg=(0.4, 0.3, 0.2, 1), text_wordwrap=13, text_align=TextNode.ALeft)
        if self.retroMode:
            self.tip.hide()

        self.title = DirectLabel(guiId='ToontownLoadingScreenTitle', parent=self.gui, relief=None, pos=(-1.06, 0, -0.77),
                                 text='', textMayChange=1, text_scale=0.08, text_fg=(0, 0, 0.5, 1), text_align=TextNode.ALeft)
        self.waitBar = DirectWaitBar(guiId='ToontownLoadingScreenWaitBar', parent=self.gui,
                                     frameSize=(-1.06, 1.06, -0.03, 0.03), pos=(0, 0, -0.85), text='')
        return

    def destroy(self):
        self.tip.destroy()
        self.title.destroy()
        self.waitBar.destroy()
        self.banner.removeNode()
        if hasattr(self, "logo"):
            self.logo.removeNode()
        self.gui.removeNode()

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
        if '%' in tip:
            tip = ControlManager.parseHotkeyString(tip, useGlyphs = True)
        return TTLocalizer.TipTitle + '\n' + tip

    def begin(self, range, label, gui, tipCategory, zoneId: Optional[int]):
        self.gui.find("**/bg").setScale(base.getAspectRatio(), 1, 1)
        self.waitBar['range'] = range
        self.title['text'] = label
        self.tip['text'] = self.getTip(tipCategory)
        self.__count = 0
        self.__expectedCount = range
        if gui:
            self.waitBar.reparentTo(self.gui)
            self.title.reparentTo(self.gui)
            self.gui.reparentTo(aspect2dp, DGG.NO_FADE_SORT_INDEX)
            self.gui.find('**/bg').setScale(aspect2dp, VBase3(base.getAspectRatio(), 1, 1))
        else:
            self.waitBar.reparentTo(aspect2dp, DGG.NO_FADE_SORT_INDEX)
            self.title.reparentTo(aspect2dp, DGG.NO_FADE_SORT_INDEX)
            self.gui.reparentTo(hidden)
        self.waitBar.update(self.__count)

    def end(self, name):
        self.waitBar.finish()
        self.waitBar.reparentTo(self.gui)
        self.title.reparentTo(self.gui)
        self.gui.reparentTo(hidden)
        return (self.__expectedCount, self.__count)

    def abort(self):
        self.gui.reparentTo(hidden)

    def tick(self, updateBar = True):
        self.__count = self.__count + 1
        if updateBar:
            self.waitBar.update(self.__count)

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
