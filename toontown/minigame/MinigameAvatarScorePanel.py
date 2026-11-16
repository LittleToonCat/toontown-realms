from panda3d.core import *

from otp.otpgui import OTPGUIUtils
from toontown.instancedgames.InstancedGamesGUI import ToonPortrait
from toontown.toonbase import ClientSettings
from toontown.toonbase.ToontownGlobals import *
from direct.gui.DirectGui import *
from toontown.toon import LaffMeter

class MinigameAvatarScorePanel(DirectFrame):

    def __init__(self, avId, avName):
        self.avId = avId
        if self.avId in base.cr.doId2do:
            self.avatar = base.cr.doId2do[self.avId]
        else:
            self.avatar = None
        DirectFrame.__init__(self, relief=None, image_color=GlobalDialogColor, image_scale=(0.4, 1.0, 0.24), image_pos=(0.0, 0.1, 0.0))
        self['image'] = DGG.getDefaultDialogGeom()
        self.scoreText = DirectLabel(self, relief=None, text='0', text_scale=TTLocalizer.MASPscoreText, pos=(0.1, 0.0, -0.09))
        if self.avatar:
            if ClientSettings.ClassicTrolleyGamePortraits.get():
                self.laffMeter = LaffMeter.LaffMeter(self.avatar.style, self.avatar.hp, self.avatar.maxHp, self.avatar.laffMeterTextColor)
                self.laffMeter.reparentTo(self)
                self.laffMeter.setPos(-0.085, 0, -0.035)
                self.laffMeter.setScale(0.05)
                self.laffMeter.start()
            else:
                self.laffMeter = ToonPortrait(self.avatar, 3)
                self.laffMeter['image_color'] = Vec4(1.0, 1.0, 1.0, 0.0)
                self.laffMeter.reparentTo(self)
                self.laffMeter.setPos(-0.085, 0, -0.025)
                self.laffMeter.setScale(0.2)
        else:
            self.laffMeter = None
        self.nameText = DirectLabel(self, relief=None, text=avName, text_scale=TTLocalizer.MASPnameText, text_pos=(0.0, 0.06), text_wordwrap=7.5, text_shadow=(1, 1, 1, 1))
        self.show()

    def cleanup(self):
        if self.laffMeter:
            self.laffMeter.destroy()
            del self.laffMeter
        del self.scoreText
        del self.nameText
        self.destroy()

    def setScore(self, score):
        self.scoreText['text'] = str(score)
        OTPGUIUtils.Animations.pulse(self.scoreText, halfDuration = 0.15, intensity = 1.1, loopDelay = 0).start()
        if ClientSettings.ClassicTrolleyGamePortraits.get():
            OTPGUIUtils.Animations.pulse(self.laffMeter, halfDuration = 0.2, intensity = 1.1, loopDelay = 0).start()
        else:
            OTPGUIUtils.Animations.pulse(self.laffMeter.toon, halfDuration = 0.2, intensity = 1.05, loopDelay = 0).start()

    def getScore(self):
        return int(self.scoreText['text'])

    def makeTransparent(self, alpha):
        self.setTransparency(1)
        self['image_color'] = (1, 1, 0.75, alpha)
