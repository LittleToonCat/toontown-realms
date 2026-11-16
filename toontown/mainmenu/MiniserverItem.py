from direct.gui import DirectGuiGlobals
from direct.gui.DirectButton import DirectButton
from direct.gui.DirectFrame import DirectFrame
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode, NodePath, TransparencyAttrib

from otp.otpgui import OTPDialog
from toontown.mainmenu.MainMenuGlobals import *
from toontown.server.MiniserverIcon import MiniserverIconButton
from toontown.toonbase import ToontownGlobals


class MiniserverItem(DirectFrame):
    settingsDecorationModel = loader.loadModel('phase_3/models/gui/ttoff_m_gui_opts_colorpicker')  # type: NodePath

    def __init__(self, data, **kwargs):
        gui = loader.loadModel('phase_3/models/gui/ttrm_m_gui_launch_mainGui')  # type: NodePath
        optiondefs = (
            ('relief', None, None),
            ('geom', gui.find('**/ServerListItem'), None),
            ('geom_scale', MultiplayerServerListGeomScale, None)
        )
        self.defineoptions(kwargs, optiondefs)
        DirectFrame.__init__(self, parent = aspect2d)
        self.initialiseoptions(MiniserverItem)
        self.data = data

        self.verified = self.data['Verified']
        namePos = MultiplayerServerListItemNamePosVerified if self.verified != "none" else MultiplayerServerListItemNamePos
        self.nameLabel = OnscreenText(
                parent = self,
                align = TextNode.ALeft,
                pos = namePos,
                scale = MultiplayerServerListItemNameScale,
                text = self.data['Name']
        )

        if self.verified != "none":
            self.verifyIcon = DirectButton(
                    parent = self,
                    relief = None,
                    image = gui.find('**/OfficialRealmIcon') if self.verified == "official" else gui.find('**/VerifiedIcon'),
                    pos = MultiplayerServerListItemVerifiedCheckPos,
                    scale = MultiplayerServerListItemVerifiedCheckScale
            )
            self.verifyHover = OnscreenImage(
                    parent = self.verifyIcon,
                    image = gui.find('**/OfficialRealmHover') if self.verified == "official" else gui.find('**/VerifiedHover'),
                    pos = MultiplayerServerListVerifyHoverPos,
                    scale = MultiplayerServerListVerifyHoverScale
            )
            self.verifyHover.hide()
            self.verifyHover.setBin('unsorted', 0)

            self.verifyIcon.bind(DirectGuiGlobals.ENTER, self.__verifyHoverOn)
            self.verifyIcon.bind(DirectGuiGlobals.EXIT, self.__verifyHoverOff)

        self.popLabel = OnscreenText(
                parent = self,
                align = TextNode.ALeft,
                pos = MultiplayerServerListItemPopPos,
                scale = MultiplayerServerListItemPopScale,
                text = f"{self.data['PopulationOnline']}/{self.data['PopulationMax']} players"
        )
        buttonTextures = (gui.find('**/Connect_Normal'),
                          gui.find('**/Connect_Press'),
                          gui.find('**/Connect_Hover'),
                          gui.find('**/Connect_Press'))  # type: tuple[NodePath, NodePath, NodePath, NodePath]
        self.connectButton = DirectButton(
                parent = self,
                relief = None,
                pressEffect = False,
                image = buttonTextures,
                scale = MultiplayerServerListConnectButtonScale,
                pos = MultiplayerServerListConnectButtonPos,
                command = lambda: base.connectToMiniserver(self.data['Address']))
        gui.removeNode()

        self.icon = MiniserverIconButton(
                url = self.data['Icon'],
                parent = self,
                pos = MultiplayerServerListIconPos,
                scale = MultiplayerServerListIconScale,
                command = self.__openPopup
        )
        self.icon.setTransparency(TransparencyAttrib.MAlpha)

    def destroy(self):
        DirectFrame.destroy(self)

    def __verifyHoverOn(self, e):
        self.verifyHover.show()

    def __verifyHoverOff(self, e):
        self.verifyHover.hide()

    def __openPopup(self):
        info = f"Server Address: {self.data['Address']}\n\n" \
               f"Description: {self.data['Description']}\n\n" \
               f"Time Zone: {self.data['Timezone']}\n"\
               f"Experience Multiplier: {self.data['ExperienceMultiplier']}\n"\
               f"Legit Mode: {'Yes' if self.data['LegitMode']else 'No'}\n"\
               f"Nerfed Mode: {'Yes' if self.data['NerfsMode'] else 'No'}\n"\
               f"Start as Maxed Toon: {'Yes' if self.data['DefaultMaxToon'] else 'No'}\n"
        dialClass = ToontownGlobals.getGlobalDialogClass()  # type: OTPDialog
        self.dialog = dialClass(
                message = info,
                doneEvent = f"server_info_{self.data['Address']}",
                text_wordwrap = 18,
                style = OTPDialog.Acknowledge
        )
        base.transitions.fadeScreen(0.5)
        self.acceptOnce(f"server_info_{self.data['Address']}", self.__exitPopup)

    def __exitPopup(self):
        self.dialog.cleanup()
        base.transitions.noFade()
