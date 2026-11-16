# CustomizeToonPage
# Created by drewc Dec 21 2023
import random
from enum import Enum, auto
from typing import Optional, List

from direct.fsm import FSM

from direct.gui import DirectGuiGlobals

from direct.directnotify import DirectNotifyGlobal
from direct.gui.DirectButton import DirectButton
from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectLabel import DirectLabel
from panda3d.core import TextNode, Vec4, Vec3, NodePath, TransparencyAttrib

from toontown.avatar import ToontownAvatarUtils
from toontown.makeatoon.ClothesGUI import ClothingGUIItem
from toontown.shtiker import ShtikerPage
from toontown.toon import ToonDNA
from toontown.toon.Toon import Toon
from toontown.toonbase import TTLocalizer
from toontown.toonbase.ToonBaseGlobal import base
from toontown.toonbase.ToontownTypes import TColor
from toontown.toontowngui.AnimatedButton import AnimatedButton
from toontown.toontowngui.ColorPickerGUI import ColorPickerGUI

GridItemScale = 0.07
GridXOffset = 0.14
GridXStart = (-GridXOffset * 2.5)

ITEMS_PER_PAGE = 36


class CustomizeToonPage(ShtikerPage.ShtikerPage, FSM.FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory("CustomizeToonEditor")
    notify.setDebug(True)

    class Tab(Enum):
        Body = auto()
        Clothing = auto()
        Accessory = auto()
        Saved = auto()

    class Grid(Enum):
        Species = auto()
        ClothingTops = auto()
        ClothingSleeves = auto()
        ClothingBottoms = auto()
        AccessoriesHat = auto()
        AccessoriesGlasses = auto()
        AccessoriesBack = auto()
        AccessoriesShoes = auto()

    def __init__(self):
        ShtikerPage.ShtikerPage.__init__(self)
        FSM.FSM.__init__(self, 'CustomizeToonPage')

        # all pages
        self.title: Optional[DirectLabel] = None
        self.bodyTabButton: Optional[DirectButton] = None
        self.clothingTabButton: Optional[DirectButton] = None
        self.accessoryTabButton: Optional[DirectButton] = None
        self.savedTabButton: Optional[DirectButton] = None
        self.toon: Optional[Toon] = None
        self.picker: Optional[ColorPickerGUI] = None

        self.gridHolder: Optional[DirectFrame] = None
        self.gridButtons: List[AnimatedButton] = []

        self.currentGrid: CustomizeToonPage.Grid = CustomizeToonPage.Grid.Species
        self.currentGridPage = {
            CustomizeToonPage.Grid.Species: 0,
            CustomizeToonPage.Grid.ClothingTops: 0,
            CustomizeToonPage.Grid.ClothingSleeves: 0,
            CustomizeToonPage.Grid.ClothingBottoms: 0,
            CustomizeToonPage.Grid.AccessoriesHat: 0,
            CustomizeToonPage.Grid.AccessoriesGlasses: 0,
            CustomizeToonPage.Grid.AccessoriesBack: 0,
            CustomizeToonPage.Grid.AccessoriesShoes: 0
        }

        # clothing
        self.clothingTopsButton: Optional[DirectButton] = None
        self.clothingSleevesButton: Optional[DirectButton] = None
        self.clothingBottomsButton: Optional[DirectButton] = None
        # accessories
        self.accessoryHatsButton: Optional[DirectButton] = None
        self.accessoryGlassesButton: Optional[DirectButton] = None
        self.accessoryBackButton: Optional[DirectButton] = None
        self.accessoryShoesButton: Optional[DirectButton] = None

    def load(self):
        self.title = DirectLabel(
            parent = self,
            relief = None,
            text = TTLocalizer.CustomizeToonPageTitle,
            text_scale = 0.05,
            pos = (0, 0, 0.64)
        )

        normalColor = (1, 1, 1, 1)
        clickColor = (0.8, 0.8, 0, 1)
        rolloverColor = (0.15, 0.82, 1.0, 1)
        disabledColor = (1.0, 0.98, 0.15, 1)
        gui = base.loader.loadModel('phase_3.5/models/gui/fishingBook')
        self.bodyTabButton = DirectButton(
            parent = self,
            relief = None,
            text = TTLocalizer.CustomizeToonPageTabBody,
            text_scale = 0.063,
            text_align = TextNode.ALeft,
            text_pos = (0.0, 0.0, 0.0),
            image = gui.find('**/tabs/polySurface1'),
            image_pos = (0.55, 1, -0.91),
            image_hpr = (0, 0, -90),
            image_scale = (0.033, 0.033, 0.035),
            image_color = normalColor, image1_color = clickColor, image2_color = rolloverColor, image3_color = disabledColor,
            text_fg = Vec4(0.2, 0.1, 0, 1),
            command = self.setTab, extraArgs = [CustomizeToonPage.Tab.Body],
            pos = (-0.83, 0, 0.77)
        )
        self.clothingTabButton = DirectButton(
            parent = self,
            relief = None,
            text = TTLocalizer.CustomizeToonPageTabClothing,
            text_scale = 0.065,
            text_align = TextNode.ALeft,
            text_pos = (0.0, 0.0, 0.0),
            image = gui.find('**/tabs/polySurface2'),
            image_pos = (0.12, 1, -0.91),
            image_hpr = (0, 0, -90),
            image_scale = (0.033, 0.033, 0.035),
            image_color = normalColor, image1_color = clickColor, image2_color = rolloverColor, image3_color = disabledColor,
            text_fg = Vec4(0.2, 0.1, 0, 1),
            command = self.setTab, extraArgs = [CustomizeToonPage.Tab.Clothing],
            pos = (-0.36, 0, 0.77)
        )
        self.accessoryTabButton = DirectButton(
            parent = self,
            relief = None,
            text = TTLocalizer.CustomizeToonPageTabAccessories,
            text_scale = 0.065,
            text_align = TextNode.ALeft,
            text_pos = (0.0, 0.0, 0.0),
            image = gui.find('**/tabs/polySurface2'),
            image_pos = (0.12, 1, -0.91),
            image_hpr = (0, 0, -90),
            image_scale = (0.033, 0.033, 0.035),
            image_color = normalColor, image1_color = clickColor, image2_color = rolloverColor, image3_color = disabledColor,
            text_fg = Vec4(0.2, 0.1, 0, 1),
            command = self.setTab, extraArgs = [CustomizeToonPage.Tab.Accessory],
            pos = (0.11, 0, 0.77)
        )
        self.savedTabButton = DirectButton(
            parent = self,
            relief = None,
            text = TTLocalizer.CustomizeToonPageTabSaved,
            text_scale = 0.065,
            text_align = TextNode.ALeft,
            text_pos = (0.0, 0.0, 0.0),
            image = gui.find('**/tabs/polySurface2'),
            image_pos = (0.12, 1, -0.91),
            image_hpr = (0, 0, -90),
            image_scale = (0.033, 0.033, 0.035),
            image_color = normalColor, image1_color = clickColor, image2_color = rolloverColor, image3_color = disabledColor,
            text_fg = Vec4(0.2, 0.1, 0, 1),
            command = self.setTab, extraArgs = [CustomizeToonPage.Tab.Saved],
            pos = (0.58, 0, 0.77)
        )
        self.gridHolder = DirectFrame(
            parent = self,
            frameSize = (-.42, .42, -.42, .42),
            pos = (-0.45, 0, .04)
        )

        self.picker = ColorPickerGUI('customize-toonpage',
                                     startHsva = (20, 20, 50, 100),
                                     parent = self, scale = 0.135)
        self.picker.alphaBar.hide()
        self.picker.closeButton.hide()
        self.picker.setPos(0.45, 0, 0)

    def unload(self):
        self.request('Off')
        self.title.destroy()
        self.title = None

        self.gridHolder.destroy()
        self.gridHolder = None

        ShtikerPage.ShtikerPage.unload(self)

    def setTab(self, tab: Tab):
        self.request(tab.name)

    async def enterBody(self):
        self.bodyTabButton['state'] = DirectGuiGlobals.DISABLED
        self.setGrid(CustomizeToonPage.Grid.Species)
        buttonPos = Vec3(GridXStart, 0, -GridXStart)
        # using async here simply to test if pyp can handle this, this will be removed after that test
        laffMeters = await base.loader.loadModel("phase_3/models/gui/laff_o_meter", blocking = False)
        for i, species in enumerate(ToonDNA.toonSpeciesTypes):
            spName = ToonDNA.getSpeciesName(species)
            if spName in ('gyro', 'scrooge'):
                spName = 'duck'
            elif spName == 'rabbit':
                spName = 'bunny'
            try:
                headIcon: NodePath = laffMeters.find(f'**/{spName}head')
                btn = AnimatedButton(
                    scale = GridItemScale*.5,
                    parent = self.gridHolder,
                    pos = buttonPos,
                    image = headIcon,
                    image_color = base.localAvatar.style.getHeadColor(),
                    text = ('', ToonDNA.getSpeciesName(species).capitalize()),
                    text_pos = (0, -.5)
                )
                self.gridButtons.append(btn)
                buttonPos.addX(GridXOffset)
                if not (i + 1) % 6:
                    buttonPos.setX(GridXStart)
                    buttonPos.addZ(-GridXOffset)
            except:
                raise NameError(f"Unable to find nodepath for species {spName}")

    def exitBody(self):
        self.clearGrid()
        self.bodyTabButton['state'] = DirectGuiGlobals.NORMAL

    def clearGrid(self):
        for btn in self.gridButtons:
            btn.destroy()
            del btn
        self.gridButtons = []

    def enterClothing(self):
        self.clothingTabButton['state'] = DirectGuiGlobals.DISABLED
        self.setGrid(CustomizeToonPage.Grid.ClothingTops)

        self.clothingTopsButton = DirectButton(
            parent = self,
            text = "Shirts",
            pos = (-0.8, 0, 0.5),
            scale = 0.05,
            command = self.setGrid,
            extraArgs = [CustomizeToonPage.Grid.ClothingTops]
        )

        self.clothingSleevesButton = DirectButton(
            parent = self,
            text = "Sleeves",
            pos = (-0.6, 0, 0.5),
            scale = 0.05,
            command = self.setGrid,
            extraArgs = [CustomizeToonPage.Grid.ClothingSleeves]
        )

        self.clothingBottomsButton = DirectButton(
            parent = self,
            text = "Bottoms",
            pos = (-0.4, 0, 0.5),
            scale = 0.05,
            command = self.setGrid,
            extraArgs = [CustomizeToonPage.Grid.ClothingBottoms]
        )
        self.accept('color-picked-customize-toonpage', self.__colorPicked)

    def exitClothing(self):
        self.ignore('color-picked-customize-toonpage')
        self.clothingTabButton['state'] = DirectGuiGlobals.NORMAL
        self.clearGrid()

        if self.clothingTopsButton:
            self.clothingTopsButton.destroy()
            self.clothingTopsButton = None
        if self.clothingSleevesButton:
            self.clothingSleevesButton.destroy()
            self.clothingSleevesButton = None
        if self.clothingBottomsButton:
            self.clothingBottomsButton.destroy()
            self.clothingBottomsButton = None

    def setGrid(self, grid: Grid):
        self.notify.debug(f'Changing GRID from {self.currentGrid} -> {grid}')
        self.clearGrid()
        self.currentGrid = grid
        base.messenger.send('wakeup')

        if grid == CustomizeToonPage.Grid.ClothingTops:
            self.picker.setFromRgbaFloat(*self.toon.style.topTexColor)
            self.refreshShirtGrid()
        elif grid == CustomizeToonPage.Grid.ClothingSleeves:
            self.picker.setFromRgbaFloat(*self.toon.style.sleeveTexColor)
            self.refreshSleevesGrid()
        elif grid == CustomizeToonPage.Grid.ClothingBottoms:
            self.picker.setFromRgbaFloat(*self.toon.style.botTexColor)
            self.refreshBottomsGrid()
        elif grid == CustomizeToonPage.Grid.AccessoriesHat:
            self.refreshHatGrid()
        elif grid == CustomizeToonPage.Grid.AccessoriesGlasses:
            self.refreshGlassesGrid()
        elif grid == CustomizeToonPage.Grid.AccessoriesBack:
            self.refreshBackGrid()
        elif grid == CustomizeToonPage.Grid.AccessoriesShoes:
            self.refreshShoesGrid()

    def refreshShirtGrid(self):
        buttonPos = Vec3(GridXStart, 0, -GridXStart)
        pageNum = self.currentGridPage.get(CustomizeToonPage.Grid.ClothingTops, 0)
        for i, style in enumerate(
                ToonDNA.Shirts[pageNum * ITEMS_PER_PAGE:ITEMS_PER_PAGE + (pageNum * ITEMS_PER_PAGE)]
        ):
            btn = AnimatedButton(
                scale = GridItemScale,
                parent = self.gridHolder,
                pos = buttonPos,
                image = 'phase_3/maps/namePanelCircle.png',
                image_color = Vec4(0),
                command = self.__setShirt,
                extraArgs = [ToonDNA.Shirts.index(style)]
            )
            shirtMdl = ClothingGUIItem(
                0,
                (
                    ToonDNA.Shirts.index(style), self.toon.style.topTexColor,
                    self.toon.style.sleeveTex, self.toon.style.sleeveTexColor
                ),
                self.toon.style.gender,
                self.toon.style.torso
            )

            shirtMdl.find('**/sleeves').removeNode()
            shirtMdl.reparentTo(btn)
            btn.shirtModel = shirtMdl
            btn.shirtTexture = style
            self.gridButtons.append(btn)
            buttonPos.addX(GridXOffset)
            if not (i + 1) % 6:
                buttonPos.setX(GridXStart)
                buttonPos.addZ(-GridXOffset)

    def __setShirt(self, shirt: int):
        assert isinstance(shirt, int)
        newDNA = ToonDNA.ToonDNA()
        newDNA.makeFromNetString(base.localAvatar.style.makeNetString())
        newDNA.topTex = shirt
        newDNA.topTexColor = self.picker.rgba
        base.localAvatar.updateDNA(dna = newDNA.makeNetString(), spellbook = False)
        self.__refreshToonPreview(newDNA)

    def refreshSleevesGrid(self):
        buttonPos = Vec3(GridXStart, 0, -GridXStart)
        pageNum = self.currentGridPage.get(CustomizeToonPage.Grid.ClothingTops, 0)
        for i, style in enumerate(
                ToonDNA.Sleeves[pageNum * ITEMS_PER_PAGE:ITEMS_PER_PAGE + (pageNum * ITEMS_PER_PAGE)]
        ):
            btn = AnimatedButton(
                scale = GridItemScale,
                parent = self.gridHolder,
                pos = buttonPos,
                image = 'phase_3/maps/namePanelCircle.png',
                image_color = Vec4(0),
                command = self.__setSleeves,
                extraArgs = [ToonDNA.Sleeves.index(style)]
            )
            shirtMdl = ClothingGUIItem(
                0,
                (
                    self.toon.style.topTex, self.toon.style.topTexColor,
                    ToonDNA.Sleeves.index(style), self.toon.style.sleeveTexColor
                ),
                self.toon.style.gender,
                self.toon.style.torso
            )
            shirtMdl.find('**/sleeves').wrtReparentTo(shirtMdl)
            shirtMdl.find('**/torso-top').removeNode()
            shirtMdl.setTransparency(TransparencyAttrib.MNone)
            shirtMdl.reparentTo(btn)
            btn.shirtModel = shirtMdl
            btn.shirtTexture = style
            self.gridButtons.append(btn)
            buttonPos.addX(GridXOffset)
            if not (i + 1) % 6:
                buttonPos.setX(GridXStart)
                buttonPos.addZ(-GridXOffset)

    def __setSleeves(self, sleeves: int):
        assert isinstance(sleeves, int)
        newDNA = ToonDNA.ToonDNA()
        newDNA.makeFromNetString(base.localAvatar.style.makeNetString())
        newDNA.sleeveTex = sleeves
        newDNA.sleeveTexColor = self.picker.rgba
        base.localAvatar.updateDNA(dna = newDNA.makeNetString(), spellbook = False)
        self.__refreshToonPreview(newDNA)

    def refreshBottomsGrid(self):
        buttonPos = Vec3(GridXStart, 0, -GridXStart)
        pageNum = self.currentGridPage.get(CustomizeToonPage.Grid.ClothingTops, 0)
        if self.toon.style.gender == 'm':
            bottomList = ToonDNA.BoyShorts
        else:
            bottomList = ToonDNA.GirlBottoms
        for i, style in enumerate(
                bottomList[pageNum * ITEMS_PER_PAGE:ITEMS_PER_PAGE + (pageNum * ITEMS_PER_PAGE)]
        ):
            btn = AnimatedButton(
                scale = GridItemScale,
                parent = self.gridHolder,
                pos = buttonPos,
                image = 'phase_3/maps/namePanelCircle.png',
                image_color = Vec4(0),
                command = self.__setBottoms,
                extraArgs = [bottomList.index(style)]
            )
            shirtMdl = ClothingGUIItem(
                1,
                (
                    bottomList.index(style), self.toon.style.botTexColor
                ),
                self.toon.style.gender,
                self.toon.style.torso
            )
            shirtMdl.reparentTo(btn)
            btn.shirtModel = shirtMdl
            btn.shirtTexture = style
            self.gridButtons.append(btn)
            buttonPos.addX(GridXOffset)
            if not (i + 1) % 6:
                buttonPos.setX(GridXStart)
                buttonPos.addZ(-GridXOffset)

    def __setBottoms(self, bottoms: int):
        assert isinstance(bottoms, int)
        newDNA = ToonDNA.ToonDNA()
        newDNA.makeFromNetString(base.localAvatar.style.makeNetString())
        newDNA.botTex = bottoms
        newDNA.botTexColor = self.picker.rgba
        base.localAvatar.updateDNA(dna = newDNA.makeNetString(), spellbook = False)
        self.__refreshToonPreview(newDNA)

    def __colorPicked(self):
        nodeName = {
            CustomizeToonPage.Grid.ClothingTops: "**/torso-top",
            CustomizeToonPage.Grid.ClothingSleeves: "**/sleeves",
            CustomizeToonPage.Grid.ClothingBottoms: "**/torso-bot"
        }.get(self.currentGrid, None)
        if nodeName is None:
            self.notify.warning(f"__colorPicked called on a screen we shouldn't be calling it from. (screen: {self.currentGrid})")
            return
        for button in self.gridButtons:
            button.shirtModel.find(nodeName).setColor(self.picker.rgba)

    def enterAccessory(self):
        self.accessoryTabButton['state'] = DirectGuiGlobals.DISABLED
        self.setGrid(CustomizeToonPage.Grid.AccessoriesHat)

        self.accessoryHatsButton = DirectButton(
            parent = self,
            text = "Hats",
            pos = (-0.8, 0, 0.5),
            scale = 0.05,
            command = self.setGrid,
            extraArgs = [CustomizeToonPage.Grid.AccessoriesHat]
        )

        self.accessoryGlassesButton = DirectButton(
            parent = self,
            text = "Glasses",
            pos = (-0.6, 0, 0.5),
            scale = 0.05,
            command = self.setGrid,
            extraArgs = [CustomizeToonPage.Grid.AccessoriesGlasses]
        )

        self.accessoryBackButton = DirectButton(
            parent = self,
            text = "Back",
            pos = (-0.4, 0, 0.5),
            scale = 0.05,
            command = self.setGrid,
            extraArgs = [CustomizeToonPage.Grid.AccessoriesBack]
        )

        self.accessoryShoesButton = DirectButton(
            parent = self,
            text = "Shoes",
            pos = (-0.2, 0, 0.5),
            scale = 0.05,
            command = self.setGrid,
            extraArgs = [CustomizeToonPage.Grid.AccessoriesShoes]
        )

    def refreshHatGrid(self):
        buttonPos = Vec3(GridXStart, 0, -GridXStart)
        pageNum = self.currentGridPage.get(CustomizeToonPage.Grid.AccessoriesHat, 0)
        for i, hat in enumerate(
                ToonDNA.HatModels[pageNum * ITEMS_PER_PAGE:ITEMS_PER_PAGE + (pageNum * ITEMS_PER_PAGE)]
        ):
            btn = AnimatedButton(
                scale = GridItemScale,
                parent = self.gridHolder,
                pos = buttonPos,
                image = 'phase_3/maps/namePanelCircle.png',
                image_color = Vec4(0),
                # command = self.setShirt,
                # extraArgs = [*style, (0, 0)]
            )

            def _cb(model: NodePath, _btn: AnimatedButton):
                self.notify.debug(f'loaded hat model {model}')

                model.setDepthTest(True)
                model.setDepthWrite(True)
                model.setScale(0.3)
                model.setH(30)
                model.reparentTo(_btn)

            if hat is not None:
                base.loader.loadModel(hat, callback = _cb, extraArgs = [btn])

            self.gridButtons.append(btn)
            buttonPos.addX(GridXOffset)
            if not (i + 1) % 6:
                buttonPos.setX(GridXStart)
                buttonPos.addZ(-GridXOffset)

    def refreshGlassesGrid(self):
        # TODO
        pass

    def refreshBackGrid(self):
        # TODO
        pass

    def refreshShoesGrid(self):
        # TODO
        pass

    def exitAccessory(self):
        self.accessoryTabButton['state'] = DirectGuiGlobals.NORMAL
        self.clearGrid()

        if self.accessoryHatsButton:
            self.accessoryHatsButton.destroy()
            self.accessoryHatsButton = None
        if self.accessoryGlassesButton:
            self.accessoryGlassesButton.destroy()
            self.accessoryGlassesButton = None
        if self.accessoryBackButton:
            self.accessoryBackButton.destroy()
            self.accessoryBackButton = None
        if self.accessoryShoesButton:
            self.accessoryShoesButton.destroy()
            self.accessoryShoesButton = None

    def enterSaved(self):
        self.savedTabButton['state'] = DirectGuiGlobals.DISABLED

    def exitSaved(self):
        self.savedTabButton['state'] = DirectGuiGlobals.NORMAL

    def enterOff(self):
        ...

    def exitOff(self):
        ...

    def enter(self):
        ShtikerPage.ShtikerPage.enter(self)
        lt = base.localAvatar

        self.toon = ToontownAvatarUtils.createUniqueToon(
            lt.getName(),
            lt.getStyle(),
            lt.getHat(),
            lt.getGlasses(),
            lt.getBackpack(),
            lt.getShoes(),
            0, 0, -.7,
            195, 0, 0,
            self
        )
        self.toon.setScale(0.1)
        self.toon.setDepthTest(True)
        self.toon.setDepthWrite(True)
        self.setTab(CustomizeToonPage.Tab.Body)

    def __refreshToonPreview(self, dna: ToonDNA):
        self.toon.setDNA(dna)

    def exit(self):
        ShtikerPage.ShtikerPage.exit(self)
        self.request('Off')
        self.toon.delete()
        self.toon = None
