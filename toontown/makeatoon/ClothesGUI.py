"""ClothesGUI is a base class that contains the clothes picking interface"""
import math
import random
from typing import Union, Tuple

from direct.gui import DirectGuiGlobals
from direct.interval.LerpInterval import LerpHprInterval
from panda3d.core import *

from otp.otpbase.PythonUtil import clamp
from otp.otpgui import OTPGUIUtils
from toontown.toon import ToonDNA
from direct.fsm import StateData
from direct.gui.DirectGui import *
from .MakeAToonGlobals import *
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals
from direct.directnotify import DirectNotifyGlobal
from random import choice

from ..toon.ToonDNA import getClothingColorFromLegacyIndex, ClothesColors
from ..toonbase.ToontownTypes import TShirt, TBottom
from ..toontowngui.AnimatedButton import AnimatedButton

CLOTHES_MAKETOON = 0  # used by MakeAToon
CLOTHES_TAILOR = 1  # used by DistributedNPCTailor
CLOTHES_CLOSET = 2  # used by DistributedCloset

ITEMS_PER_PAGE = 25

class ClothesGUI(StateData.StateData):
    """ClothesGUI class: contains methods for changing the Avatar's
    outfit via user input"""

    notify = DirectNotifyGlobal.directNotify.newCategory('ClothesGUI')

    def __init__(self, type, doneEvent, swapEvent = None):
        """"__init__(self, Event)
        """
        StateData.StateData.__init__(self, doneEvent)
        self.type = type
        self.toon = None
        self.swapEvent = swapEvent
        self.gender = '?'
        self.girlInShorts = 0
        self.swappedTorso = 0
        self.startColor = 0
        self.topColorChoice = 0
        self.bottomColorChoice = 0
        self.topPage = 0
        self.bottomPage = 0
        self.topColorPage = 0
        self.bottomColorPage = 0

        self.shirtButtons = []
        self.bottomButtons = []
        self.topStyles = []
        self.bottomStyles = []
        return

    def load(self):
        # the basic interface with always have scroll buttons for
        # the shirts and the shorts, some text saying "shirts" and
        # "bottoms", and some sort of accept button

        self.parentFrame = DirectFrame(relief = DGG.RAISED, parent = base.a2dTopRight, pos = (-0.353333, 0, -0.584), frameColor = (1, 0, 0, 0))

        if self.type == CLOTHES_MAKETOON:
            csgui = loader.loadModel('phase_3/models/gui/ttrm_m_gui_mat_colorShop')
            self.toggleColorScreen = AnimatedButton(parent = self.parentFrame, image = csgui.find('**/cs_preset_icon_classic'),
                                                    image_scale = 0.1, pos = (-0.19, 0, -0.975),
                                                    text_scale = 0.05, command = self.__setScreen, extraArgs = [1])
            self.toggleColorScreen.hide()
            csgui.removeNode()
            del csgui

        newGui: NodePath = loader.loadModel('phase_3/models/gui/ttrm_m_gui_mat_clothesShop')
        sbkGui: NodePath = loader.loadModel('phase_3.5/models/gui/ttoff_m_gui_sbk_generic')
        arrows = (
            (sbkGui.find('**/shtkr_arrow_L_OFF'), sbkGui.find('**/shtkr_arrow_L_ON'), sbkGui.find('**/shtkr_arrow_L_ON'), sbkGui.find('**/shtkr_arrow_L_OFF')),
            (sbkGui.find('**/shtkr_arrow_R_OFF'), sbkGui.find('**/shtkr_arrow_R_ON'), sbkGui.find('**/shtkr_arrow_R_ON'), sbkGui.find('**/shtkr_arrow_R_OFF')),
        )

        self.frameBgs: Tuple[Tuple[NodePath, NodePath], Tuple[NodePath, NodePath]] = (
            (newGui.find('**/cls_panel_shirt_bg'),
             newGui.find('**/cls_panel_shirtcolor_bg')
             ),
            (newGui.find('**/cls_panel_bottom_bg'),
             newGui.find('**/cls_panel_bottomcolor_bg')
             ),
        )

        self.shirtStyleFrame = DirectFrame(
                parent = base.a2dLeftCenter,
                relief = None,
                geom = self.frameBgs[0][0],
                geom_scale = OTPGUIUtils.getImageScale(1710, 1910, 1.1),
                pos = (0.55, 0, 0)
        )
        self.bottomStyleFrame = DirectFrame(
                parent = base.a2dRightCenter,
                relief = None,
                geom = self.frameBgs[1][0],
                geom_scale = OTPGUIUtils.getImageScale(1710, 1910, 1.1),
                pos = (-0.55, 0, 0),
        )

        self.shirtLeftArrow = DirectButton(
                parent = self.shirtStyleFrame,
                relief = None,
                image = arrows[0],
                pos = (-0.3, 0, 0.41),
                scale = 0.08,
                image3_color = (0, 0, 0, 0),
                command = self.page,
                extraArgs = [0, -1]
        )
        self.shirtRightArrow = DirectButton(
                parent = self.shirtStyleFrame,
                relief = None,
                image = arrows[1],
                pos = (0.3, 0, 0.41),
                scale = 0.08,
                image3_color = (0, 0, 0, 0),
                command = self.page,
                extraArgs = [0, 1]
        )

        self.bottomLeftArrow = DirectButton(
                parent = self.bottomStyleFrame,
                relief = None,
                image = arrows[0],
                pos = (-0.3, 0, 0.41),
                scale = 0.08,
                image3_color = (0, 0, 0, 0),
                command = self.page,
                extraArgs = [1, -1]
        )
        self.bottomRightArrow = DirectButton(
                parent = self.bottomStyleFrame,
                relief = None,
                image = arrows[1],
                pos = (0.3, 0, 0.41),
                scale = 0.08,
                image3_color = (0, 0, 0, 0),
                command = self.page,
                extraArgs = [1, 1]
        )

        self.shirtStyleFrame.hide()
        self.bottomStyleFrame.hide()
        self.parentFrame.hide()

    def __setScreen(self, screen: bool):
        if screen:
            self.toggleColorScreen['extraArgs'] = [0]
            self.setupColorInterface()
        else:
            self.toggleColorScreen['extraArgs'] = [1]
            self.setupClothingInterface()

    def unload(self):
        """unload(self)
        """

        self.parentFrame.destroy()
        for i, x in self.frameBgs:
            i.removeNode()
            x.removeNode()
        del self.frameBgs
        self.shirtStyleFrame.destroy()
        self.bottomStyleFrame.destroy()

        del self.shirtStyleFrame
        del self.bottomStyleFrame

        del self.parentFrame

        self.ignore('MAT-newToonCreated')

    def page(self, part: int, direction: int):
        """
        Navigate the page in the part you have selected
        :param part: Which part frame are we navigating? 0 = TOP, 1 = BOTTOM, 2 = TOP COL, 3 = BOTTOM COL
        :param direction: How much to increment the current page number by
        """
        if part == 0:
            maxPages = math.floor(len(self.topStyles)/25)
            self.topPage = clamp(self.topPage + direction, 0, maxPages)

            if self.topPage - 1 < 0:
                self.shirtLeftArrow['state'] = DirectGuiGlobals.DISABLED
            else:
                self.shirtLeftArrow['state'] = DirectGuiGlobals.NORMAL

            if self.topPage + 1 > maxPages:
                self.shirtRightArrow['state'] = DirectGuiGlobals.DISABLED
            else:
                self.shirtRightArrow['state'] = DirectGuiGlobals.NORMAL

            self.generateTopInterface()

        elif part == 1:
            maxPages = math.floor(len(self.bottomStyles)/25)
            self.bottomPage = clamp(self.bottomPage + direction, 0, maxPages)
            if self.bottomPage - 1 < 0:
                self.bottomLeftArrow['state'] = DirectGuiGlobals.DISABLED
            else:
                self.bottomLeftArrow['state'] = DirectGuiGlobals.NORMAL

            if self.bottomColorPage + 1 > maxPages:
                self.bottomRightArrow['state'] = DirectGuiGlobals.DISABLED
            else:
                self.bottomRightArrow['state'] = DirectGuiGlobals.NORMAL

            self.generateBottomInterface()
        elif part == 2:
            maxPages = math.floor(len(
                    ToonDNA.getTopColors(self.gender, self.topStyles[self.topStyleChoice],
                                         tailorId = self.tailorId if hasattr(self, 'tailorId') else ToonDNA.MAKE_A_TOON)
            )/25)
            self.topColorPage = clamp(self.topColorPage + direction, 0, maxPages)

            if self.topColorPage - 1 < 0:
                self.shirtLeftArrow['state'] = DirectGuiGlobals.DISABLED
            else:
                self.shirtLeftArrow['state'] = DirectGuiGlobals.NORMAL

            if self.topPage + 1 > maxPages:
                self.shirtRightArrow['state'] = DirectGuiGlobals.DISABLED
            else:
                self.shirtRightArrow['state'] = DirectGuiGlobals.NORMAL

            self.generateTopColorInterface()

        elif part == 3:
            maxPages = math.floor(len(
                    ToonDNA.getBottomColors(self.gender, self.bottomStyles[self.bottomStyleChoice],
                                            tailorId = self.tailorId if hasattr(self, 'tailorId') else ToonDNA.MAKE_A_TOON)
            )/25)
            self.bottomColorPage = clamp(self.bottomColorPage + direction, 0, maxPages)
            if self.bottomColorPage - 1 < 0:
                self.bottomLeftArrow['state'] = DirectGuiGlobals.DISABLED
            else:
                self.bottomLeftArrow['state'] = DirectGuiGlobals.NORMAL

            if self.bottomColorPage + 1 > maxPages:
                self.bottomRightArrow['state'] = DirectGuiGlobals.DISABLED
            else:
                self.bottomRightArrow['state'] = DirectGuiGlobals.NORMAL

            self.generateBottomColorInterface()

    def showButtons(self):
        self.parentFrame.show()
        self.shirtStyleFrame.show()
        self.bottomStyleFrame.show()
        if self.type == CLOTHES_MAKETOON:
            self.toggleColorScreen.show()

    def hideButtons(self):
        self.parentFrame.hide()
        self.shirtStyleFrame.hide()
        self.bottomStyleFrame.hide()
        if self.type == CLOTHES_MAKETOON:
            self.toggleColorScreen.hide()

    def setupClothingInterface(self):
        self.generateTopInterface()
        self.generateBottomInterface()
        self.page(0, 0)
        self.page(1, 0)

    def generateTopInterface(self):
        self.shirtLeftArrow['extraArgs'] = [0, -1]
        self.shirtRightArrow['extraArgs'] = [0, 1]
        for btn in self.shirtButtons:
            btn.destroy()
        self.shirtStyleFrame['geom'] = self.frameBgs[0][0]
        _scale = 0.07
        _xOff = 0.14
        _xStart = -_xOff * 2
        buttonPos = Vec3(_xStart, 0, 0.280)
        for i, style in enumerate(self.topStyles[self.topPage*ITEMS_PER_PAGE:ITEMS_PER_PAGE+(self.topPage*ITEMS_PER_PAGE)]):

            if self.type != CLOTHES_MAKETOON:
                btn = AnimatedButton(
                        scale = _scale,
                        parent = self.shirtStyleFrame,
                        pos = buttonPos,
                        image = 'phase_3/maps/namePanelCircle.png',
                        image_color = Vec4(0),
                        command = self.setShirt,
                        extraArgs = [*style, (0, 0)]
                )
                shirtMdl = ClothingGUIItem(0,
                                           style,
                                           self.gender,
                                           self.toon.style.torso
                                           )
            else:
                colors = ToonDNA.getTopColors(self.gender, style, tailorId = self.tailorId if hasattr(self, 'tailorId') else ToonDNA.MAKE_A_TOON)
                lastColor = min(self.topColorChoice, len(colors) - 1)

                btn = AnimatedButton(
                        scale = _scale,
                        parent = self.shirtStyleFrame,
                        pos = buttonPos,
                        image = 'phase_3/maps/namePanelCircle.png',
                        image_color = Vec4(0),
                        command = self.setShirt,
                        extraArgs = [style[0], getClothingColorFromLegacyIndex(colors[lastColor][0]),
                                     style[1], getClothingColorFromLegacyIndex(colors[lastColor][1]), (i, lastColor)]
                )
                shirtMdl = ClothingGUIItem(0,
                                           (style[0], getClothingColorFromLegacyIndex(colors[lastColor][0]),
                                            style[1], getClothingColorFromLegacyIndex(colors[lastColor][1])),
                                           self.gender,
                                           self.toon.style.torso
                                           )
            shirtMdl.reparentTo(btn)
            self.shirtButtons.append(btn)
            buttonPos.addX(_xOff)
            if not (i + 1) % 5:
                buttonPos.setX(_xStart)
                buttonPos.addZ(-_xOff)

    def generateBottomInterface(self):
        self.bottomLeftArrow['extraArgs'] = [1, -1]
        self.bottomRightArrow['extraArgs'] = [1, 1]
        for btn in self.bottomButtons:
            btn.destroy()
        self.bottomStyleFrame['geom'] = self.frameBgs[1][0]
        _scale = 0.07
        _xOff = -0.14
        _xStart = -_xOff * 2
        buttonPos = Vec3(_xStart, 0, 0.280)
        for i, style in enumerate(self.bottomStyles[self.bottomPage*ITEMS_PER_PAGE:ITEMS_PER_PAGE+(self.bottomPage*ITEMS_PER_PAGE)]):

            if self.type != CLOTHES_MAKETOON:
                btn = AnimatedButton(
                        scale = _scale,
                        parent = self.bottomStyleFrame,
                        pos = buttonPos,
                        image = 'phase_3/maps/namePanelCircle.png',
                        image_color = Vec4(0),
                        command = self.setBottoms,
                        extraArgs = [*style, (0, 0)]
                )
                bottomMdl = ClothingGUIItem(1,
                                            style,
                                            self.gender,
                                            self.toon.style.torso
                                            )
            else:
                colors = ToonDNA.getBottomColors(self.gender, style, tailorId = self.tailorId if hasattr(self, 'tailorId') else ToonDNA.MAKE_A_TOON)
                lastColor = min(self.bottomColorChoice, len(colors) - 1)
                btn = AnimatedButton(
                        scale = _scale,
                        parent = self.bottomStyleFrame,
                        pos = buttonPos,
                        image = 'phase_3/maps/namePanelCircle.png',
                        image_color = Vec4(0),
                        command = self.setBottoms,
                        extraArgs = [style, getClothingColorFromLegacyIndex(colors[lastColor]), (i, lastColor)]
                )
                bottomMdl = ClothingGUIItem(1,
                                            (style, getClothingColorFromLegacyIndex(colors[lastColor])),
                                            self.gender,
                                            self.toon.style.torso
                                            )
            bottomMdl.reparentTo(btn)
            self.bottomButtons.append(btn)
            buttonPos.addX(_xOff)
            if not (i + 1) % 5:
                buttonPos.setX(_xStart)
                buttonPos.addZ(_xOff)

    def setupColorInterface(self):
        self.generateTopColorInterface()
        self.generateBottomColorInterface()
        self.page(2, 0)
        self.page(3, 0)

    def generateTopColorInterface(self):
        self.shirtLeftArrow['extraArgs'] = [2, -1]
        self.shirtRightArrow['extraArgs'] = [2, 1]
        for btn in self.shirtButtons:
            btn.destroy()
        self.shirtStyleFrame['geom'] = self.frameBgs[0][1]
        _scale = 0.07
        _xOff = 0.14
        _xStart = -_xOff * 2
        buttonPos = Vec3(_xStart, 0, 0.280)
        for i, color in enumerate(ToonDNA.getTopColors(self.gender, self.topStyles[self.topStyleChoice],
                                                       tailorId = self.tailorId if hasattr(self, 'tailorId') else ToonDNA.MAKE_A_TOON)
                                  [self.topColorPage*ITEMS_PER_PAGE:ITEMS_PER_PAGE+(self.topColorPage*ITEMS_PER_PAGE)]):
            btn = AnimatedButton(
                    scale = _scale,
                    parent = self.shirtStyleFrame,
                    pos = buttonPos,
                    image = 'phase_3/maps/namePanelCircle.png',
                    image_color = Vec4(0),
                    command = self.setShirt,
                    extraArgs = [self.toon.style.topTex, getClothingColorFromLegacyIndex(color[0]),
                                 self.toon.style.sleeveTex, getClothingColorFromLegacyIndex(color[1]), (self.topStyleChoice, i)]
            )
            shirtMdl = ClothingGUIItem(0,
                                       (self.toon.style.topTex, getClothingColorFromLegacyIndex(color[0]),
                                        self.toon.style.sleeveTex, getClothingColorFromLegacyIndex(color[1])),
                                       self.gender,
                                       self.toon.style.torso
                                       )
            shirtMdl.reparentTo(btn)
            self.shirtButtons.append(btn)
            buttonPos.addX(_xOff)
            if not (i + 1) % 5:
                buttonPos.setX(_xStart)
                buttonPos.addZ(-_xOff)

    def generateBottomColorInterface(self):
        self.bottomLeftArrow['extraArgs'] = [3, -1]
        self.bottomRightArrow['extraArgs'] = [3, 1]
        for btn in self.bottomButtons:
            btn.destroy()
        self.bottomStyleFrame['geom'] = self.frameBgs[1][1]
        _scale = 0.07
        _xOff = -0.14
        _xStart = -_xOff * 2
        buttonPos = Vec3(_xStart, 0, 0.280)
        for i, color in enumerate(ToonDNA.getBottomColors(self.gender, self.bottomStyles[self.bottomStyleChoice],
                                                          tailorId = self.tailorId if hasattr(self, 'tailorId') else ToonDNA.MAKE_A_TOON)
                                  [self.bottomColorPage*ITEMS_PER_PAGE:ITEMS_PER_PAGE+(self.bottomColorPage*ITEMS_PER_PAGE)]):
            btn = AnimatedButton(
                    scale = _scale,
                    parent = self.bottomStyleFrame,
                    pos = buttonPos,
                    image = 'phase_3/maps/namePanelCircle.png',
                    image_color = Vec4(0),
                    command = self.setBottoms,
                    extraArgs = [self.toon.style.botTex, getClothingColorFromLegacyIndex(color), (self.bottomStyleChoice, i)]
            )
            bottomMdl = ClothingGUIItem(1,
                                        (self.toon.style.botTex, getClothingColorFromLegacyIndex(color)),
                                        self.gender,
                                        self.toon.style.torso
                                        )
            bottomMdl.reparentTo(btn)
            self.bottomButtons.append(btn)
            buttonPos.addX(_xOff)
            if not (i + 1) % 5:
                buttonPos.setX(_xStart)
                buttonPos.addZ(_xOff)

    def enter(self, toon):
        """enter(self, toon)
        """
        self.notify.debug('enter')
        # turn off any user control
        base.disableMouse()
        self.toon = toon

        # setup the scroll interface
        # including which set of clothes
        # we will be scrolling through
        # this method should be defined in the child
        # classes
        self.setupScrollInterface()

        self.setupClothingInterface()

        choicePool = [self.topStyles, self.bottomStyles]

    def exit(self):
        """exit(self)
        Remove events and restore display
        """
        try:
            del self.toon
        except:
            self.notify.warning('ClothesGUI: toon not found')

        self.hideButtons()
        # remove keyboard/gui events
        self.ignore('enter')
        self.ignore('next')
        self.ignore('last')

    def setupButtons(self):
        # set exit event
        self.acceptOnce('last', self.__handleBackward)
        self.acceptOnce('next', self.__handleForward)
        # This is not supported with the new running toons
        # self.acceptOnce("enter", self.__handleForward)
        return None

    # event handlers

    def swapTop(self, offset):
        length = len(self.tops)
        self.topChoice += offset
        if self.topChoice <= 0:
            self.topChoice = 0
        # ghost the pickers if at the end of the 'wheel'
        self.updateScrollButtons(self.topChoice, length, 0,
                                 self.topLButton, self.topRButton)
        # Put some index range checking here
        if self.topChoice < 0 or self.topChoice >= len(self.tops) or \
                len(self.tops[self.topChoice]) != 4:
            self.notify.warning('topChoice index is out of range!')
            return None

        self.toon.style.topTex = self.tops[self.topChoice][0]

        if isinstance(self.tops[self.topChoice][1], int):
            self.toon.style.topTexColor = getClothingColorFromLegacyIndex(self.tops[self.topChoice][1])
        else:
            self.toon.style.topTexColor = self.tops[self.topChoice][1]

        self.toon.style.sleeveTex = self.tops[self.topChoice][2]

        if isinstance(self.tops[self.topChoice][3], int):
            self.toon.style.sleeveTexColor = getClothingColorFromLegacyIndex(self.tops[self.topChoice][3])
        else:
            self.toon.style.sleeveTexColor = self.tops[self.topChoice][3]

        self.notify.debug("topChoice: %s" % (self.topChoice))
        self.notify.debug(f'shirt: {self.toon.style.topTex} color: {self.toon.style.topTexColor} sleeve color: {self.toon.style.sleeveTexColor}')
        self.toon.generateToonClothes()
        if self.swapEvent != None:
            messenger.send(self.swapEvent)
        messenger.send('wakeup')

    def swapBottom(self, offset):
        length = len(self.bottoms)
        self.bottomChoice += offset
        if self.bottomChoice <= 0:
            self.bottomChoice = 0
        # ghost the pickers if at the end of the 'wheel'
        self.notify.debug("bottoms: choice = %s, length = %s" % (self.bottomChoice, length))
        self.updateScrollButtons(self.bottomChoice, length, 0, self.bottomLButton, self.bottomRButton)
        if self.bottomChoice < 0 or self.bottomChoice >= len(self.bottoms) or \
                len(self.bottoms[self.bottomChoice]) != 2:
            self.notify.warning('bottomChoice index is out of range!')
            return None
        self.toon.style.botTex = self.bottoms[self.bottomChoice][0]
        if isinstance(self.bottoms[self.bottomChoice][1], int):
            self.toon.style.botTexColor = getClothingColorFromLegacyIndex(self.bottoms[self.bottomChoice][1])
        else:
            self.toon.style.botTexColor = self.bottoms[self.bottomChoice][1]
        if self.toon.generateToonClothes() == 1:
            self.toon.loop('neutral', 0)
            self.swappedTorso = 1
        if self.swapEvent != None:
            messenger.send(self.swapEvent)
        messenger.send('wakeup')

    def swapTopStyle(self, offset):
        length = len(self.topStyles)
        self.topStyleChoice += offset
        if self.topStyleChoice <= 0:
            self.topStyleChoice = 0
        # ghost the pickers if at the end of the 'wheel'
        self.updateScrollButtons(self.topStyleChoice, length, 0, self.shirtStyleLButton, self.shirtStyleRButton)
        if self.topStyleChoice < 0 or self.topStyleChoice >= length:
            self.notify.warning('topChoice index is out of range!')
            return None
        self.toon.style.topTex = self.topStyles[self.topStyleChoice][0]
        self.toon.style.sleeveTex = self.topStyles[self.topStyleChoice][1]
        colors = ToonDNA.getTopColors(self.gender, self.topStyles[self.topStyleChoice], tailorId = self.tailorId if hasattr(self, 'tailorId') else ToonDNA.MAKE_A_TOON)
        colorLength = len(colors)
        if self.topColorChoice < 0 or self.topColorChoice >= colorLength:
            self.topColorChoice = colorLength - 1
        self.updateScrollButtons(self.topColorChoice, colorLength, 0, self.topLButton, self.topRButton)
        self.toon.style.topTexColor = getClothingColorFromLegacyIndex(colors[self.topColorChoice][0])
        self.toon.style.sleeveTexColor = getClothingColorFromLegacyIndex(colors[self.topColorChoice][1])
        self.toon.generateToonClothes()
        if self.swapEvent != None:
            messenger.send(self.swapEvent)
        messenger.send('wakeup')

    def swapTopColor(self, offset):
        self.topColorChoice += offset
        colors = ToonDNA.getTopColors(self.gender, self.topStyles[self.topStyleChoice], tailorId = self.tailorId if hasattr(self, 'tailorId') else ToonDNA.MAKE_A_TOON)
        length = len(colors)
        if self.topColorChoice <= 0:
            self.topColorChoice = 0
        # ghost the pickers if at the end of the 'wheel'
        self.updateScrollButtons(self.topColorChoice, length, 0, self.topLButton, self.topRButton)
        if self.topColorChoice < 0 or self.topColorChoice >= length:
            self.notify.warning('topChoice index is out of range!')
            self.topColorChoice = len(colors)
            self.updateScrollButtons(self.topColorChoice, length, 0, self.topLButton, self.topRButton)
        self.toon.style.topTexColor = getClothingColorFromLegacyIndex(colors[self.topColorChoice][0])
        self.toon.style.sleeveTexColor = getClothingColorFromLegacyIndex(colors[self.topColorChoice][1])
        self.toon.generateToonClothes()
        if self.swapEvent != None:
            messenger.send(self.swapEvent)
        messenger.send('wakeup')

    def swapBottomStyle(self, offset):
        length = len(self.bottomStyles)
        self.bottomStyleChoice += offset
        if self.bottomStyleChoice <= 0:
            self.bottomStyleChoice = 0
        # ghost the pickers if at the end of the 'wheel'
        self.updateScrollButtons(self.bottomStyleChoice, length, 0, self.bottomStyleLButton, self.bottomStyleRButton)
        if self.bottomStyleChoice < 0 or self.bottomStyleChoice >= length:
            self.notify.warning('bottomChoice index is out of range!')
            return None
        self.toon.style.botTex = self.bottomStyles[self.bottomStyleChoice]
        colors = ToonDNA.getBottomColors(self.gender, self.bottomStyles[self.bottomStyleChoice], tailorId = self.tailorId if hasattr(self, 'tailorId') else ToonDNA.MAKE_A_TOON)
        colorLength = len(colors)
        if self.bottomColorChoice < 0 or self.bottomColorChoice >= colorLength:
            self.bottomColorChoice = colorLength - 1
        self.updateScrollButtons(self.bottomColorChoice, colorLength, 0, self.bottomLButton, self.bottomRButton)
        self.toon.style.botTexColor = getClothingColorFromLegacyIndex(colors[self.bottomColorChoice])
        if self.toon.generateToonClothes() == 1:
            self.toon.loop('neutral', 0)
            self.swappedTorso = 1
        if self.swapEvent != None:
            messenger.send(self.swapEvent)
        messenger.send('wakeup')

    def swapBottomColor(self, offset):
        self.bottomColorChoice += offset
        colors = ToonDNA.getBottomColors(self.gender, self.bottomStyles[self.bottomStyleChoice], tailorId = self.tailorId if hasattr(self, 'tailorId') else ToonDNA.MAKE_A_TOON)
        length = len(colors)
        if self.bottomColorChoice <= 0:
            self.bottomColorChoice = 0
        # ghost the pickers if at the end of the 'wheel'
        self.updateScrollButtons(self.bottomColorChoice, length, 0, self.bottomLButton, self.bottomRButton)
        if self.bottomColorChoice < 0 or self.bottomColorChoice >= length:
            self.notify.warning('bottomColor choice index is out of range!')
            self.bottomColorChoice = len(colors)
            self.updateScrollButtons(self.bottomColorChoice, length, 0, self.bottomLButton, self.bottomRButton)
        self.toon.style.botTexColor = getClothingColorFromLegacyIndex(colors[self.bottomColorChoice])
        if self.toon.generateToonClothes() == 1:
            self.toon.loop('neutral', 0)
            self.swappedTorso = 1
        if self.swapEvent != None:
            messenger.send(self.swapEvent)
        messenger.send('wakeup')

    def getGenderColorList(self, dna):
        if self.dna.getGender() == 'm':
            return ToonDNA.defaultBoyColorList
        else:
            return ToonDNA.defaultGirlColorList

    def updateScrollButtons(self, choice, length, startTex, lButton, rButton):
        # ghost the pickers if at the end of the 'wheel'
        if choice >= length - 1:
            rButton['state'] = DGG.DISABLED
        else:
            rButton['state'] = DGG.NORMAL
        if choice <= 0:
            lButton['state'] = DGG.DISABLED
        else:
            lButton['state'] = DGG.NORMAL

    def __handleForward(self):
        self.doneStatus = 'next'
        messenger.send(self.doneEvent)

    def __handleBackward(self):
        self.doneStatus = 'last'
        messenger.send(self.doneEvent)

    def resetClothes(self, style):
        if self.toon:
            self.toon.style.makeFromNetString(style.makeNetString())
            # In case we've switched to the skirt torso and are reverting back
            # to shorts, we need to regenerate clothes for the toon
            if self.swapEvent != None and self.swappedTorso == 1:
                self.toon.swapToonTorso(self.toon.style.torso, genClothes = 0)
                self.toon.generateToonClothes()
                self.toon.loop('neutral', 0)

    def setShirt(self, shirt: int, shirtColor: VBase4, sleeves: int, sleevesColor: VBase4, inds: Tuple[int, int]):
        # these two are the indexes of the choices within the self.topStyles and self.bottomStyles, not the actual ids themselves.
        # i might rework this later
        self.topStyleChoice = inds[0]
        self.topColorChoice = inds[1]
        self.toon.style.topTex = shirt
        self.toon.style.sleeveTex = sleeves
        if isinstance(shirtColor, int):
            shirtColor = ToonDNA.getClothingColorFromLegacyIndex(shirtColor)
        if isinstance(sleevesColor, int):
            sleevesColor = ToonDNA.getClothingColorFromLegacyIndex(sleevesColor)

        self.toon.style.topTexColor = shirtColor
        self.toon.style.sleeveTexColor = sleevesColor

        self.toon.generateToonClothes()
        if self.swapEvent is not None:
            messenger.send(self.swapEvent)
        messenger.send('wakeup')

    def setBottoms(self, bottom: int, bottomColor: VBase4, inds: Tuple[int, int]):
        self.bottomStyleChoice = inds[0]
        self.bottomColorChoice = inds[1]
        self.toon.style.botTex = bottom
        if isinstance(bottomColor, int):
            bottomColor = ToonDNA.getClothingColorFromLegacyIndex(bottomColor)

        self.toon.style.botTexColor = bottomColor

        # This will return true if we swapped the torso (switching from shorts to skirts / vice-versa)
        if self.toon.generateToonClothes():
            self.toon.loop('neutral', 0)
        if self.swapEvent is not None:
            messenger.send(self.swapEvent)
        messenger.send('wakeup')


class ClothingGUIItem(NodePath):

    def __init__(self, part: int, item: Union[TShirt, TBottom], gender = 'm', body = 's'):
        NodePath.__init__(self, f'cl{part}{str(item)}')
        # todo: make it choose based on the body type
        if gender == 'm' or not ToonDNA.GirlBottoms[item[0]][1] and part == 1:
            self.baseModel = loader.loadModel(f'phase_3/models/char/tt_a_chr_dg{body[0]}_shorts_torso_1000')
        else:
            self.baseModel = loader.loadModel(f'phase_3/models/char/tt_a_chr_dg{body[0]}_skirt_torso_1000')

        if part == 0:
            np = self.baseModel.find('**/torso-top')
            np.reparentTo(self)
            np.setH(135)
            bMin, bMax = np.getTightBounds()
            center = (bMin + bMax) / 2.0
            np.setPos(-center[0], 0, -center[2])
            np.setTransparency(0)
            self.baseModel.find('**/sleeves').reparentTo(np)
            if body[0] == 's':
                np.setScale(0.9)

            shirtTex = loader.loadTexture(ToonDNA.Shirts[item[0]])
            sleeveTex = loader.loadTexture(ToonDNA.Sleeves[item[2]])
            self.find('**/torso-top').setTexture(shirtTex, 1)
            self.find('**/torso-top').setColor(item[1])
            self.find('**/sleeves').setTexture(sleeveTex, 1)
            self.find('**/sleeves').setColor(item[3])

        else:
            np = self.baseModel.find('**/torso-bot')
            np.reparentTo(self)
            np.reparentTo(self)
            np.setH(135)
            bMin, bMax = np.getTightBounds()
            center = (bMin + bMax) / 2.0
            np.setPos(-center[0], 0, -center[2])
            botTex = loader.loadTexture(ToonDNA.BoyShorts[item[0]] if gender == 'm' else ToonDNA.GirlBottoms[item[0]][0])
            np.setTexture(botTex, 1)
            np.setColor(item[1])
            np.setTransparency(0)
            if body[0] == 's':
                np.setScale(0.8)

        self.setDepthWrite(1)
        self.setDepthTest(1)
        self.rotateIval = LerpHprInterval(self, 5, Vec3(0, 0, 0), Vec3(-360, 0, 0))
        self.rotateIval.loop()

    def removeNode(self):
        self.rotateIval.finish()
        del self.rotateIval
        NodePath.removeNode(self)
