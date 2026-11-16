import json
from typing import List, Tuple, Callable, Dict, Type

from direct.gui.DirectFrame import DirectFrame
from panda3d.core import NodePath, TextNode, PandaNode

from otp.otpgui import OTPGUIUtils
from toontown.login.WelcomeGUI import WelcomeGUI
from toontown.toonbase import ToontownGlobals, ClientSettings
from toontown.toontowngui.AnimatedButton import AnimatedButton
from toontown.toontowngui.ToontownScrolledFrame import ToontownScrolledFrame


class Utils:
    @staticmethod
    def parseColor(color: str) -> Tuple[float, float, float, float]:
        try:
            _color = color.lstrip('#')

            if len(_color) == 6:
                # RGB, no alpha
                r, g, b = tuple(int(_color[i:i + 2], 16) / 255. for i in (0, 2, 4))
                return r, g, b, 1.0
            elif len(_color) == 8:
                # RGBA
                return tuple(int(_color[i:i + 2], 16) / 255. for i in (0, 2, 4, 6))
            else:
                raise Exception('Malformed hex rgb string. Must be one of (#RRGGBB, #RRGGBBAA)')
        except:
            return 0.0, 0.0, 0.0, 1.0

    @staticmethod
    def getFont(fontName: str):
        fontNameToFunc: Dict[str, Callable]


class XMLMOTDElement:
    def __init__(self, element: Dict):
        self.element = element

    def generate(self):
        print('element')


class XMLMOTDText(XMLMOTDElement):
    def __init__(self, element: Dict):
        XMLMOTDElement.__init__(self, element)

        self.color = Utils.parseColor(self.element.get('color', '#000000FF'))
        self.text = self.element.get('content', 'Error getting MOTD Content')
        self.align = 'center'  # self.element.get('align', 'left')

    def generate(self) -> TextNode:
        tn: TextNode = TextNode(str(hash(repr(self.element))))
        tn.setTextColor(self.color)
        tn.setFont(ToontownGlobals.getInterfaceFont())  # todo: this can be chosen

        tn.setAlign({'left': TextNode.ALeft, 'center': TextNode.ACenter, 'right': TextNode.ARight}.get(self.align))
        tn.setTextScale(0.055)
        tn.setWordwrap(1.5)
        tn.setText(self.text)
        return tn


class XMLMOTDSpacer(XMLMOTDElement):
    def __init__(self, element: Dict):
        XMLMOTDElement.__init__(self, element)

    def generate(self) -> TextNode:
        # little hack
        tn: TextNode = TextNode(str(hash(repr(self.element))))
        tn.setAlign(TextNode.ACenter)
        tn.setTextScale(0.055)
        tn.setText(" ")
        return tn


class XMLMOTDHeader(XMLMOTDElement):
    def __init__(self, element: Dict):
        XMLMOTDElement.__init__(self, element)

        self.color = Utils.parseColor(self.element.get('color', '#000000FF'))
        self.text = self.element.get('content', 'Error getting MOTD Content')
        self.align = 'center'  # self.element.get('align', 'center')

    def generate(self) -> TextNode:
        tn: TextNode = TextNode(str(hash(repr(self.element))))
        tn.setTextColor(self.color)
        tn.setFont(ToontownGlobals.getBuildingNametagFont())  # todo: this can be chosen
        tn.setAlign({'left': TextNode.ALeft, 'center': TextNode.ACenter, 'right': TextNode.ARight}.get(self.align))
        tn.setTextScale(0.085)
        tn.setWordwrap(1.5)
        tn.setText(self.text)
        return tn


class MOTDDialog(DirectFrame):

    def __init__(self, motdText: str):
        settingsButtonsModel: NodePath = loader.loadModel('phase_3/models/gui/ttoff_m_gui_opts_buttons')
        colorPickerModel: NodePath = loader.loadModel("phase_3/models/gui/ttoff_m_gui_opts_colorpicker", allowInstance = True)
        DirectFrame.__init__(self, pos = (0, 0, 0.05), relief = None, image = colorPickerModel.find("**/temp_bg"),
                             image_scale = (1.8, 1, 1.6), image_pos = (0, 0, -0.05),
                             image_color = ToontownGlobals.GlobalDialogColor, borderWidth = (0.01, 0.01))
        self.reparentTo(hidden)

        self.setBin('gui-popup', 0)

        settingsScrollbarModel = loader.loadModel('phase_3.5/models/gui/ttoff_m_gui_sbk_generic')
        self.initialiseoptions(MOTDDialog)
        self.scrollFrame = ToontownScrolledFrame(
            parent = self,
            height = 0.7682,
            pos = (0, 0, -0.05),
            width = .9,
            itemMargin = (.05, -.04),
            itemPadding = .02,
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
            verticalScroll_incButton_relief = None
        )

        self.closeButton = AnimatedButton(
            parent = self,
            relief = None,
            image = (settingsButtonsModel.find('**/close_button_normal'),
                     settingsButtonsModel.find('**/close_button_click'),
                     settingsButtonsModel.find('**/close_button_hover')),
            image_scale = .09,
            pos = (0.775, 0, 0.65),
            command = self.exit
        )

        rootNode: List[Dict] = json.loads(motdText)

        tagNameToClass: Dict[str, Type[XMLMOTDElement]] = {
            'Header': XMLMOTDHeader,
            'Text': XMLMOTDText,
            'Break': XMLMOTDSpacer
        }

        self.xmlnodes: List[XMLMOTDElement] = []

        for node in rootNode:
            classType = tagNameToClass.get(node.get('type', None), None)
            if classType:
                if isinstance(node.get('content', None), list):
                    # We can specify multiple contents in one element if we are reusing the same settings in a row
                    for line in node.get('content'):
                        _newNode = node.copy()
                        _newNode['content'] = line

                        self.xmlnodes.append(classType(element = _newNode))
                else:
                    self.xmlnodes.append(classType(element = node))

        textnodes: List[TextNode] = []
        for node in self.xmlnodes:
            textnodes.append(node.generate())

        for i, tn in enumerate(textnodes):
            if i > 0:
                hOff = textnodes[i - 1].getHeight()
            else:
                hOff = tn.getHeight() / 2

            _tn: PandaNode = tn.generate()
            self.scrollFrame.addItems((hidden.attachNewNode(_tn), {'zOffset': hOff}))

    def show(self):
        base.transitions.fadeScreen(0.5)
        OTPGUIUtils.Animations.popup(self, 1).start()
        self.reparentTo(aspect2dp)

    def exit(self):
        self.scrollFrame.clearItems()
        base.transitions.noTransitions()
        self.ignoreAll()
        self.destroy()

        if ClientSettings.LastWelcomeVersion.get() != WelcomeGUI.VERSION:
            base.cr.avChoice.welcomeGui.enter()
        base.cr.gameServicesManager.motdDialog = None
