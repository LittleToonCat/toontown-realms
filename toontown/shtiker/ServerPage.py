from direct.directnotify import DirectNotifyGlobal
from direct.gui.DirectGui import *
from panda3d.core import *

from . import ShtikerPage
from otp.otpbase import PythonUtil
from toontown.toonbase import TTLocalizer
from toontown.server import MiniserverIcon

POP_COLORS_NTT = (Vec4(0.0, 1.0, 0.0, 1.0), Vec4(1.0, 1.0, 0.0, 1.0), Vec4(1.0, 0.0, 0.0, 1.0))
POP_COLORS = (Vec4(0.4, 0.4, 1.0, 1.0), Vec4(0.4, 1.0, 0.4, 1.0), Vec4(1.0, 0.4, 0.4, 1.0))


class ServerPage(ShtikerPage.ShtikerPage):
    notify = DirectNotifyGlobal.directNotify.newCategory('ServerPage')

    def updatePopulationCount(self):
        # Add 1 to include our localAvatar.
        currentPop = (len(base.cr.onlineAvatars) - len(base.cr.invisibleAvatars)) + 1
        maxPop = base.cr.discordManager.getDistrictLimit()
        self.populationLabel.setText(TTLocalizer.ServerPagePopulation.format(currentPop, maxPop))

    def load(self):
        ShtikerPage.ShtikerPage.load(self)

        cdrGui = loader.loadModel('phase_3.5/models/gui/tt_m_gui_sbk_codeRedemptionGui')
        connectButtonGui = loader.loadModel('phase_3/models/gui/quit_button')
        titleHeight = 0.61

        self.title = DirectLabel(parent = self, relief = None, text = TTLocalizer.ServerPageTitle, text_scale = 0.12,
                                 pos = (0, 0, titleHeight))
        title = TTLocalizer.ServerPageName % base.cr.serverName
        newTitle = title[:45]
        if len(newTitle) < len(title):
            newTitle = newTitle + TTLocalizer.ServerPageEllipse
        self.titleLabel = DirectLabel(parent = self, relief = None, text = newTitle, text_scale = 0.0625,
                                      text_wordwrap = 24,
                                      textMayChange = 1, text_align = TextNode.ALeft, pos = (-0.825, 0, 0.4))
        population = TTLocalizer.ServerPagePopulation.format(base.cr.discordManager.getDistrictAvatarCount(),
                                                             base.cr.discordManager.getDistrictLimit())
        self.populationLabel = DirectLabel(parent = self, relief = None, text = population, text_scale = 0.0625,
                                           text_wordwrap = 15, textMayChange = 1, text_align = TextNode.ALeft,
                                           pos = (-0.825, 0, 0.3))
        description = TTLocalizer.ServerPageDesc % base.cr.serverDescription
        newDescription = description[:80]
        if len(newDescription) < len(description):
            newDescription = newDescription + TTLocalizer.ServerPageEllipse
        self.descriptionLabel = DirectLabel(parent = self, relief = None,
                                            text = newDescription,
                                            text_scale = 0.0625, text_wordwrap = 12, textMayChange = 1,
                                            text_align = TextNode.ALeft, pos = (-0.825, 0, 0.2))
        self.serverIcon = MiniserverIcon.MiniserverIcon(
                parent = self,
                url = base.cr.serverIconPath,
                pos = (-0.75, 0, 0.6),
                scale = .1
        )

        cdrGui.removeNode()
        connectButtonGui.removeNode()

    def enter(self):
        ShtikerPage.ShtikerPage.enter(self)

        self.updatePopulationCount()
        self.accept('onlineAvatarsChanged', self.updatePopulationCount)

    def exit(self):
        self.ignore('onlineAvatarsChanged')

        ShtikerPage.ShtikerPage.exit(self)

    def unload(self):
        self.title.destroy()
        del self.title

        self.titleLabel.destroy()
        del self.titleLabel

        self.populationLabel.destroy()
        del self.populationLabel

        self.descriptionLabel.destroy()
        del self.descriptionLabel

        self.serverIcon.destroy()
        del self.serverIcon

        self.ignoreAll()

        ShtikerPage.ShtikerPage.unload(self)


