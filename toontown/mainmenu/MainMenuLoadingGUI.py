"""
Essentially a reimplementation of the ToontownLoadingBlocker, but without the unneeded functionality
"""

from direct.directnotify import DirectNotifyGlobal
from direct.gui.DirectGui import *
from panda3d.core import TextNode

from toontown.toonbase import ToontownGlobals, ControlManager
from toontown.toonbase import TTLocalizer
from toontown.toontowngui import TTDialog
from direct.interval.LerpInterval import LerpFunctionInterval
from direct.interval.IntervalGlobal import Sequence, Func
import random


class MainMenuLoadingGUI(TTDialog.TTDialog):
    notify = DirectNotifyGlobal.directNotify.newCategory("MainMenuLoadingGUI")

    def __init__(self, text = TTLocalizer.MainMenuConnecting, indeterminate = True, mini = False):
        """
        Initialize the loading GUI

        :param text: The line of text to display at the top of the dialog
        :param indeterminate: If true, the bar will do a constant animation instead of display a value
        """
        TTDialog.TTDialog.__init__(self)
        self.indeterminate = indeterminate
        self.percentage = 0.0

        gui = loader.loadModel("phase_3/models/gui/tt_m_gui_pat_mainGui")
        img = gui.find("**/tt_t_gui_pat_loadingPopup")
        self['image'] = img
        self['image_scale'] = (1, 0, 1)
        self['image_pos'] = (0, 0, -0.4)

        self.loadBarIval = None

        gui.removeNode()
        base.transitions.fadeScreen()
        self.title = DirectLabel(
                parent = self,
                relief = None,
                pos = (0, 0, 0.38),
                text = text,
                text_font = ToontownGlobals.getSignFont(),
                text_fg = (1, 0.9, 0.1, 1),
                text_align = TextNode.ACenter,
                text_scale = 0.1,
                text_wordwrap = 18,
                textMayChange = 1,
                sortOrder = 50,
        )
        self.loadingText = DirectLabel(
                parent = self,
                relief = None,
                pos = (0, 0, -0.2357),
                text = "Loading...",
                text_fg = (1, 1, 1, 1),
                text_shadow = (0, 0, 0, 0.6),
                text_scale = 0.055,
                textMayChange = 1,
                text_align = TextNode.ACenter,
                sortOrder = 50,
        )
        self.loadingText['text'] = random.choice(TTLocalizer.BlockerLoadingTexts)

        taskMgr.doMethodLater(3, self.__changeLoadingText, 'changeLoadingText')

        def getTip(tipCategory):
            tip = random.choice(TTLocalizer.TipDict.get(tipCategory))
            if '$$' in tip:
                tip = ControlManager.ControlManager.parseHotkeyString(tip, useGlyphs = True)
            return TTLocalizer.TipTitle + "\n" + tip

        self.toonTipText = DirectLabel(
                parent = self,
                relief = None,
                pos = (0, 0, -0.4688),
                text = getTip(TTLocalizer.TIP_GENERAL),
                text_fg = (1, 1, 1, 1),
                text_shadow = (0, 0, 0, 0.6),
                text_scale = 0.05,
                textMayChange = 1,
                text_align = TextNode.ACenter,
                text_wordwrap = 32,
                sortOrder = 50,
        )

        self.bar = DirectWaitBar(
                parent = self,
                pos = (0, 0, -0.3138),
                text = '',
                text_scale = (0.08, 0.128),
                text_fg = (1, 1, 1, 1),
                text_align = TextNode.ACenter,
                text_pos = (0, -0.035),
                relief = DGG.FLAT,
                frameSize = (-0.6, 0.6, -0.1, 0.1),
                borderWidth = (0.02, 0.02),
                scale = (0.8, 0.8, 0.5),
                range = 100,
                sortOrder = 5000,
                frameColor = (0.5, 0.5, 0.5, 0.5),
                barColor = (0.2, 0.7, 0.2, 0.5)
        )
        self.bar.setBin('gui-popup', 1)

        self.setMini(mini)

        if self.indeterminate:
            self.__startBarAnimation()

    def setMini(self, mini):
        self.mini = mini
        if self.mini:
            self.bar.setScale(0.35, 0.25, 0.25)
            self.bar.reparentTo(base.a2dpBottomLeft)
            self.bar.setBin('fixed', 10)
            self.bar.setPos(0.23, 0, 0.04)
            self.title.reparentTo(base.a2dpBottomLeft)
            self.title.setBin('fixed', 12)
            self.title.setPos(0.23, 0, 0.03)
            self.title.setScale(0.3)
            self.title['text_wordwrap'] = 50
            self.title['text_font'] = ToontownGlobals.getInterfaceFont()
            self.title['text_shadow'] = (0.0, 0.0, 0.0, 0.8)
            self.hide()
        else:
            self.bar.reparentTo(self)
            self.bar.setBin('gui-popup', 1)
            self.bar.setPos(0, 0, -0.3138)
            self.bar.setScale(0.8, 0.8, 0.5)
            self.title.reparentTo(self)
            self.title.setPos(0, 0, 0.38)
            self.title.setScale(1)
            self.title.clearBin()
            self.title['text_wordwrap'] = 18
            self.title['text_font'] = ToontownGlobals.getSignFont()
            self.title['text_shadow'] = (0.0, 0.0, 0.0, 0.0)
            self.show()

    def __startBarAnimation(self):
        def setBarVal(val):
            self.bar['value'] = val

        def setBarTextR(r):
            self.bar['text_roll'] = 180*r
            self.bar['text_pos'] = ((0, -0.035), (0, 0.035))[r]

        self.loadBarIval = Sequence(
                LerpFunctionInterval(setBarVal, 0.8, fromData = 0, toData = 100,  blendType = 'easeIn'),
                Func(self.bar.setR, 180),
                Func(setBarTextR, 1),
                LerpFunctionInterval(setBarVal, 0.8, fromData = 100, toData = 0, blendType = 'easeOut'),
                LerpFunctionInterval(setBarVal, 0.8, fromData = 0, toData = 100, blendType = 'easeIn'),
                Func(self.bar.setR, 0),
                Func(setBarTextR, 0),
                LerpFunctionInterval(setBarVal, 0.8, fromData = 100, toData = 0, blendType = 'easeOut'),
        )
        self.loadBarIval.loop()

        #taskMgr.doMethodLater(2, self.__changeLoadingTip, 'changeLoadingTip')

    def __changeLoadingText(self, task):
        self.loadingText['text'] = random.choice(TTLocalizer.BlockerLoadingTexts)
        return task.again

    def setPercentage(self, percentage = 100.0):
        self.percentage = percentage
        if not self.indeterminate:
            self.bar['value'] = self.percentage
            self.bar['text'] = f'{self.percentage:.0f}%'

    def setIndeterminate(self, indeterminate = False):
        if self.loadBarIval:
            self.loadBarIval.finish()

        self.indeterminate = indeterminate
        if self.indeterminate:
            self.__startBarAnimation()

    def destroy(self):
        taskMgr.remove('changeLoadingText')
        taskMgr.remove('changeLoadingTip')

        base.transitions.noFade()
        self.title.destroy()
        self.title = None

        self.loadingText.destroy()
        self.loadingText = None

        self.toonTipText.destroy()
        self.toonTipText = None

        if self.loadBarIval:
            self.loadBarIval.finish()

        self.bar.destroy()
        self.bar = None

        TTDialog.TTDialog.destroy(self)
