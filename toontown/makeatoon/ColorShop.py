"""ColorShop module: contains the ColorShop class"""
from typing import Tuple, List, Dict

from panda3d.core import *

from otp.otpgui import OTPGUIUtils
from toontown.toon import ToonDNA
from direct.fsm import StateData
from direct.gui.DirectGui import *
from .MakeAToonGlobals import *
from toontown.toonbase import TTLocalizer
from . import ShuffleButton
import random
from direct.directnotify import DirectNotifyGlobal

from ..toon.ToonDNA import allColorsList
from ..toontowngui.AnimatedButton import AnimatedButton

SHUFFLE_MODE = 1
class ColorShop(StateData.StateData):
    """ColorShop class: contains methods for changing the Avatar's
    color via user input"""

    notify = DirectNotifyGlobal.directNotify.newCategory('ColorShop')

    def __init__(self, doneEvent):
        """__init__(self, Event)
        Set-up the color shop interface to change the color of the
        parts of the given toon
        """
        StateData.StateData.__init__(self, doneEvent)
        self.toon = None
        self.colorAll = 1
        return

    def getGenderColorList(self, dna):
        if self.dna.getGender() == 'm':
            return ToonDNA.defaultBoyColorList
        else:
            return ToonDNA.defaultGirlColorList

    def enter(self, toon, shopsVisited = []):
        """enter(self, toon)
        """
        # turn off any user control
        base.disableMouse()

        # load up the given toon
        self.toon = toon
        self.dna = toon.getStyle()

        # try:
        #    # just make note of the curent color
        #    self.headChoice = allColorsList.index(self.dna.headColor)
        #    self.armChoice = allColorsList.index(self.dna.armColor)
        #    self.legChoice = allColorsList.index(self.dna.legColor)
        # except:
        #    # otherwise change toon from white to the start color the first time through
        #    self.headChoice = random.choice(allColorsList)
        #    self.armChoice = self.headChoice
        #    self.legChoice = self.headChoice
        #    self.__swapHeadColor(0)
        #    self.__swapArmColor(0)
        #    self.__swapLegColor(0)
        #
        # self.startColor = 0
        # set up the "done" button
        self.acceptOnce('last', self.__handleBackward)
        self.acceptOnce('next', self.__handleForward)
        self.shuffleButton.history[0] = [VBase4(1, 1, 1, 1), VBase4(1, 1, 1, 1), VBase4(1, 1, 1, 1)]
        self.accept(self.shuffleFetchMsg, self.changeColor)
        self.acceptOnce('MAT-newToonCreated', self.shuffleButton.cleanHistory)

    def showButtons(self):
        self.parentFrame.show()
        self.selectionFrame.show()
        self.swatchFrame.show()
        self.setPalette('tto')

    def hideButtons(self):
        self.parentFrame.hide()
        self.selectionFrame.hide()
        self.swatchFrame.hide()

    def exit(self):
        """exit(self)
        Remove events and restore display
        """
        self.ignore('last')
        self.ignore('next')
        self.ignore('enter')
        self.ignore(self.shuffleFetchMsg)
        try:
            del self.toon
        except:
            self.notify.warning('toon not found')

        self.hideButtons()

    def load(self):
        """load(self)
        """
        self.csGui = loader.loadModel('phase_3/models/gui/ttrm_m_gui_mat_colorShop')

        self.partSelection = [True, True, True]

        self.parentFrame = DirectFrame(relief = None, parent = base.a2dTopRight, pos = (-0.353333, 0, -0.584), frameColor = (1, 0, 0, 0))

        self.selectionFrame = DirectFrame(relief = None, parent = base.a2dLeftCenter,
                                          pos = (0.4, 0, 0))

        self.partPickerImages: Tuple[Tuple[Tuple[NodePath, NodePath], ...]] = (
            # === Head ===
            (
                # == Unselected ==
                (self.csGui.find('**/cs_selection_head_inactive'), self.csGui.find('**/cs_selection_head_inactive_h')),
                # == Selected ==
                (self.csGui.find('**/cs_selection_head_active'), self.csGui.find('**/cs_selection_head_active_h'))
            ),
            # === Torso ===
            (
                # == Unselected ==
                (self.csGui.find('**/cs_selection_torso_inactive'), self.csGui.find('**/cs_selection_torso_inactive_h')),
                # == Selected ==
                (self.csGui.find('**/cs_selection_torso_active'), self.csGui.find('**/cs_selection_torso_active_h'))
            ),
            # === Legs ===
            (
                # == Unselected ==
                (self.csGui.find('**/cs_selection_legs_inactive'), self.csGui.find('**/cs_selection_legs_inactive_h')),
                # == Selected ==
                (self.csGui.find('**/cs_selection_legs_active'), self.csGui.find('**/cs_selection_legs_active_h'))
            )
        )

        self.headToggle = AnimatedButton(
                parent = self.selectionFrame,
                relief = None,
                image = self.partPickerImages[0][1],
                image_scale = OTPGUIUtils.getImageScale(1551, 519, 0.208),
                pos = (-0.04, 0.0, 0.2),
                command = self.togglePartSelection,
                commandButtons = (DGG.LMB, DGG.RMB),
                extraArgs = [0]
        )

        self.torsoToggle = AnimatedButton(
                parent = self.selectionFrame,
                relief = None,
                image = self.partPickerImages[1][1],
                image_scale = OTPGUIUtils.getImageScale(1549, 487, 0.195),
                pos = (-0.04, 0.0, 0.0),
                command = self.togglePartSelection,
                commandButtons = (DGG.LMB, DGG.RMB),
                extraArgs = [1]
        )

        self.legsToggle = AnimatedButton(
                parent = self.selectionFrame,
                relief = None,
                image = self.partPickerImages[2][1],
                image_scale = OTPGUIUtils.getImageScale(1550, 497, 0.2),
                pos = (-0.04, 0.0, -0.2),
                command = self.togglePartSelection,
                commandButtons = (DGG.LMB, DGG.RMB),
                extraArgs = [2]
        )

        self.headToggle.bind(DGG.B3PRESS, self.headToggle._AnimatedButton__press)
        self.headToggle.bind(DGG.B3RELEASE, self.togglePartSelection, extraArgs = [0, True])
        self.torsoToggle.bind(DGG.B3PRESS, self.torsoToggle._AnimatedButton__press)
        self.torsoToggle.bind(DGG.B3RELEASE, self.togglePartSelection, extraArgs = [1, True])
        self.legsToggle.bind(DGG.B3PRESS, self.legsToggle._AnimatedButton__press)
        self.legsToggle.bind(DGG.B3RELEASE, self.togglePartSelection, extraArgs = [2, True])

        self.swatchFrame = DirectFrame(
                relief = None,
                parent = base.a2dRightCenter,
                pos = (-0.55, 0, 0),
                image = self.csGui.find('**/cs_panel_preset_bg'),
                image_scale = OTPGUIUtils.getImageScale(1564, 1776, 1.1)
        )

        self.ttoPalToggle = AnimatedButton(parent = self.swatchFrame,
                                           image = self.csGui.find('**/cs_preset_icon_classic'),
                                           image_scale = 0.1,
                                           pos = (-0.15, 0, -0.47),
                                           text = ('', TTLocalizer.ColorShopClassic),
                                           text_fg = Vec4(0.95, 0.95, 0.95, 1),
                                           text_shadow = Vec4(0, 0, 0, 1),
                                           text_scale = 0.06,
                                           text_pos = (0, 0.04),
                                           command = self.setPalette,
                                           extraArgs = ['tto'])
        self.pastelPalToggle = AnimatedButton(parent = self.swatchFrame,
                                              image = self.csGui.find('**/cs_preset_icon_pastel'),
                                              image_scale = 0.1,
                                              pos = (0.15, 0, -0.47),
                                              text = ('', TTLocalizer.ColorShopPastel),
                                              text_fg = Vec4(1, 1, 1, 1),
                                              text_shadow = Vec4(0, 0, 0, 1),
                                              text_scale = 0.06,
                                              text_pos = (0, 0.04),
                                              command = self.setPalette,
                                              extraArgs = ['pastel'])

        splatterImages: List[NodePath] = [self.csGui.find(f'**/cs_preset_splatter_{x}') for x in 'abcdefgh']
        self.swatches: Dict[str, List[AnimatedButton]] = {}

        for palette, colors in ToonDNA.colorPalettes.items():
            self.swatches[palette] = []
            _scale = 0.12
            _xOff = 0.13
            _xStart = -_xOff*2.5
            buttonPos = Vec3(_xStart, 0, 0.370)
            for i, color in enumerate(colors):
                splatter = random.choice(splatterImages)

                btn = AnimatedButton(
                        pos = buttonPos,
                        parent = self.swatchFrame,
                        relief = None,
                        scale = _scale,
                        image = splatter,
                        image_color = color,
                        command = self.__setColor,
                        extraArgs = [color]
                )
                buttonPos.addX(_xOff)
                if not (i + 1) % 6:
                    # Since the background is angled a bit, let's make the buttons follow that
                    _xOff /= 1.015
                    _xStart = _xOff*-2.5
                    _scale /= 1.015
                    buttonPos.setX(_xStart)
                    buttonPos.addZ(-0.15)
                self.swatches[palette].append(btn)

        self.parentFrame.hide()
        self.selectionFrame.hide()
        self.swatchFrame.hide()
        self.shuffleFetchMsg = 'ColorShopShuffle'
        self.shuffleButton = ShuffleButton.ShuffleButton(self, self.shuffleFetchMsg, pos = (-0.19, 0, -1.1))

        self.shuffleButton.overrideShuffleFunc = self.doShuffle
        return

    def unload(self):
        """unload(self)
        """
        self.parentFrame.destroy()
        del self.parentFrame
        self.selectionFrame.destroy()
        del self.selectionFrame

        self.swatchFrame.destroy()
        del self.swatchFrame

        self.shuffleButton.unload()
        self.ignore('MAT-newToonCreated')

    def togglePartSelection(self, partIndex: int, exclusive = False, e = None):
        """
        :param partIndex: Part Index (0-2: head,torso,legs)
        :param exclusive: whether we should disable all others when selecting, this happens when we right-click
        :param e: event passed when using the bound method, unused in this function but needs to be passed
        """

        if exclusive:
            (self.headToggle, self.torsoToggle, self.legsToggle)[partIndex]._AnimatedButton__release(e)
            for i in range(3):
                self.partSelection[i] = i == partIndex
                (self.headToggle, self.torsoToggle, self.legsToggle)[i]['image'] = self.partPickerImages[i][self.partSelection[i]]
            return

        self.partSelection[partIndex] = not self.partSelection[partIndex]

        (self.headToggle, self.torsoToggle, self.legsToggle)[partIndex]['image'] = self.partPickerImages[partIndex][self.partSelection[partIndex]]

    def __setColor(self, color: Vec4):
        if self.partSelection[0]:
            self.dna.headColor = color
        if self.partSelection[1]:
            self.dna.armColor = color
        if self.partSelection[2]:
            self.dna.legColor = color
        self.toon.swapToonColor(self.dna)

    def doShuffle(self):
        allColors = []
        for _, colors in ToonDNA.colorPalettes.items():
            allColors.extend(colors)

        if SHUFFLE_MODE == 1:
            if self.partSelection[0]:
                self.dna.headColor = random.choice(allColors)
            if self.partSelection[1]:
                self.dna.armColor = random.choice(allColors)
            if self.partSelection[2]:
                self.dna.legColor = random.choice(allColors)

            if len(self.shuffleButton.history) == self.shuffleButton.maxHistory:
                self.shuffleButton.history.remove(self.shuffleButton.history[0])
            self.shuffleButton.history.append((self.dna.headColor, self.dna.armColor, self.dna.legColor))
            self.shuffleButton.historyPtr = len(self.shuffleButton.history) - 1
            if len(self.shuffleButton.history) == 2:
                self.shuffleButton.startShowLerp()
            self.shuffleButton.updateArrows()

            self.toon.swapToonColor(self.dna)
            return
        color = random.choice(allColors)
        self.__setColor(color)

    def setPalette(self, palette: str):
        if palette not in ToonDNA.colorPalettes.keys():
            self.notify.error(f"Tried to select a color palette that doesn't exist ({palette})!")
        for _palette, buttons in self.swatches.items():
            for button in buttons:
                button.show() if _palette == palette else button.hide()

    def __handleForward(self):
        self.doneStatus = 'next'
        messenger.send(self.doneEvent)

    def __handleBackward(self):
        self.doneStatus = 'last'
        messenger.send(self.doneEvent)

    def changeColor(self):
        self.notify.debug('Entering changeColor')
        headColor, armColor, legColor = self.shuffleButton.history[self.shuffleButton.historyPtr]
        self.dna.headColor = headColor
        self.dna.armColor = armColor
        self.dna.legColor = legColor
        self.toon.swapToonColor(self.dna)

    def getCurrToonSetting(self):
        return [self.dna.headColor, self.dna.armColor, self.dna.legColor]
