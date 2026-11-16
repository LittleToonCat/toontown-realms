from panda3d.core import *
from direct.gui.DirectGui import *
from direct.showbase import DirectObject
from otp.avatar import Avatar
from direct.distributed import DistributedObject
from . import SuitDNA
from toontown.toonbase import TTLocalizer
from otp.avatar import AvatarPanel
from toontown.social import SocialMenu
from . import Suit
from ..toonbase.ToontownTypes import CogAppearanceIndex


class SuitAvatarPanel(AvatarPanel.AvatarPanel):
    currentAvatarPanel = None

    def __init__(self, avatar: Suit):
        AvatarPanel.AvatarPanel.__init__(self, avatar, socialMenu = SocialMenu)
        self.avName = avatar.getName()
        gui = loader.loadModel('phase_3.5/models/gui/suit_detail_panel')
        self.frame = DirectFrame(geom=gui.find('**/avatar_panel'), geom_scale=(0.21, 0.21, 0.225), geom_pos=(0, 0, 0), relief=None, pos=(-0.245, 0, -0.4875), parent=base.a2dTopRight)
        disabledImageColor = Vec4(1, 1, 1, 0.4)
        text0Color = Vec4(1, 1, 1, 1)
        text1Color = Vec4(0.5, 1, 0.5, 1)
        text2Color = Vec4(1, 1, 0.5, 1)
        text3Color = Vec4(1, 1, 1, 0.2)

        self.head = self.frame.attachNewNode('body')
        self.model = Suit.Suit()
        dna = SuitDNA.SuitDNA()
        dna.newSuit(avatar.dna.name)
        self.model.setDNA(dna)
        self.model.update()
        self.model.reparentTo(self.head)
        self.model.setH(-20)
        self.model.getGeomNode().setScale(0.12)
        self.model.setZ((-.88, -0.8, -0.6)[avatar.appearance[CogAppearanceIndex.BODY_TYPE]])
        self.model.setDepthTest(1)
        self.model.setDepthWrite(1)
        size = .1895
        self.head.setPosHprScale(0, 0, .15, 180, 0, 0, 1, 1, 1)
        self.model.setScissor(self.head, Vec3(-size), Vec3(size))
        self.model.pose('neutral', 30)

        self.nameLabel = DirectLabel(parent=self.frame, pos=(0, 0, 0.36), relief=None, text=self.avName, text_font=avatar.getFont(), text_align=TextNode.ACenter, text_fg=Vec4(0, 0, 0, 1), text_pos=(0, 0), text_scale=0.047, text_wordwrap=7.5, text_shadow=(1, 1, 1, 1))
        level = avatar.getActualLevel()
        dept = SuitDNA.getSuitDeptFullname(avatar.dna.name)
        self.levelLabel = DirectLabel(parent=self.frame, pos=(0, 0, -0.1), relief=None, text=TTLocalizer.AvatarPanelCogLevel % level, text_font=avatar.getFont(), text_align=TextNode.ACenter, text_fg=Vec4(0, 0, 0, 1), text_pos=(0, 0), text_scale=0.05, text_wordwrap=8.0)
        if not base.cr.legitMode:
            self.shorthandLabel = DirectLabel(parent=self.frame, pos=(0, 0, -0.14), relief=None, text=TTLocalizer.AvatarPanelCogShorthand % avatar.dna.name, text_font=avatar.getFont(), text_fg=Vec4(0, 0, 0, 1), text_pos=(0, 0), text_scale=0.037, text_wordwrap=15, text_shadow=(1, 1, 1, 1))
        if avatar.corpMedallion:
            corpIcon = avatar.corpMedallion.copyTo(hidden)
            corpIcon.show()
        else:
            corpIcon = avatar.getCorporateMedallionIcon()
        corpIcon.setPosHprScale(0, 0, 0, 0, 0, 0, 0, 0, 0)

        if not base.cr.legitMode:
            corpIconPos = (0, 0, -0.245)
            deptLabelPos = (0, 0, -0.35)
            closeButtonPos = (0, 0, -0.4125)
        else:
            corpIconPos = (0, 0, -0.215)
            deptLabelPos = (0, 0, -0.325)
            closeButtonPos = (0, 0, -0.4025)

        self.corpIcon = DirectLabel(parent=self.frame, geom=corpIcon, geom_scale=0.13, pos=corpIconPos, relief=None)
        corpIcon.removeNode()
        self.deptLabel = DirectLabel(parent=self.frame, pos=deptLabelPos, relief=None, text=dept, text_font=avatar.getFont(), text_align=TextNode.ACenter, text_fg=Vec4(0, 0, 0, 1), text_pos=(0, 0), text_scale=0.05, text_wordwrap=8.0)
        self.closeButton = DirectButton(parent=self.frame, relief=None, pos=closeButtonPos, text=TTLocalizer.AvatarPanelCogDetailClose, text_font=avatar.getFont(), text0_fg=Vec4(0, 0, 0, 1), text1_fg=Vec4(0.5, 0, 0, 1), text2_fg=Vec4(1, 0, 0, 1), text_pos=(0, 0), text_scale=0.05, command=self.__handleClose)
        gui.removeNode()
        menuX = -0.05
        menuScale = 0.064
        self.frame.show()
        messenger.send('avPanelDone')

    def cleanup(self):
        if self.frame == None:
            return
        self.frame.destroy()
        del self.frame
        self.frame = None
        self.head.removeNode()
        del self.head
        self.model = None
        AvatarPanel.AvatarPanel.cleanup(self)

    def __handleClose(self):
        self.cleanup()
        AvatarPanel.currentAvatarPanel = None
