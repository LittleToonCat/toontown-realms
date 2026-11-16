"""
Special interior prop type
This will be a special prop with a menu which
allows you to change all aspects of the interiors appearance
TODO
"""
from typing import Optional, Dict

from direct.gui.DirectFrame import DirectFrame
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import Vec3, NodePath, NodePathCollection, VBase4, LColor, LColorf

from otp.otpbase.PythonUtil import bound
from toontown.catalog import CatalogWallpaperItem
from toontown.datapack.DataPackManager import DataPackManager
from toontown.sandbox import PropGlobals
from toontown.sandbox.PropGlobals import PropPool
from toontown.sandbox.PropSpecial import PropSpecial
from toontown.sandbox.PropUI import Dropdown, TexturePicker
from toontown.toonbase import TTLocalizer, ToontownGlobals, ClientSettings
from toontown.toonbase.ToonBaseGlobal import base
from toontown.toonbase.ToontownTypes import TColor
from toontown.toontowngui.AnimatedButton import AnimatedButton
from toontown.toontowngui.ColorPickerGUI import ColorPickerGUI
from toontown.toontowngui.SettingsGUI import ColorPickerOption

WALLPAPER_TEXTURES = (
    'phase_5.5/maps/flat_wallpaper1.png',
    'phase_3.5/maps/wall_paper_a1.png',
    'phase_3.5/maps/wall_paper_a2.png',
    'phase_3.5/maps/wall_paper_a3.png',
    'phase_3.5/maps/wall_paper_a4.png',
    'phase_3.5/maps/wall_paper_a5.png',
    'phase_5.5/maps/big_stripes1.png',
    'phase_5.5/maps/big_stripes2.png',
    'phase_5.5/maps/big_stripes3.png',
    'phase_5.5/maps/big_stripes4.png',
    'phase_5.5/maps/big_stripes5.png',
    'phase_5.5/maps/big_stripes6.png',
    'phase_5.5/maps/stripeB1.png',
    'phase_5.5/maps/stripeB2.png',
    'phase_5.5/maps/stripeB3.png',
    'phase_5.5/maps/stripeB4.png',
    'phase_3.5/maps/stripeB5.png',
    'phase_5.5/maps/stripeB6.png',
    'phase_5.5/maps/stripeB7.png',
    'phase_5.5/maps/squiggle1.png',
    'phase_5.5/maps/squiggle2.png',
    'phase_5.5/maps/squiggle3.png',
    'phase_5.5/maps/squiggle4.png',
    'phase_5.5/maps/squiggle5.png',
    'phase_5.5/maps/squiggle6.png',
    'phase_5.5/maps/stripes_cyan.png',
    'phase_5.5/maps/stripes_green.png',
    'phase_5.5/maps/stripes_magenta.png',
    'phase_5.5/maps/two_stripes1.png',
    'phase_5.5/maps/two_stripes2.png',
    'phase_5.5/maps/two_stripes3.png',
    'phase_5.5/maps/leaves1.png',
    'phase_5.5/maps/leaves2.png',
    'phase_5.5/maps/leaves3.png',
    'phase_5.5/maps/diamonds2_cherries.png',
    'phase_5.5/maps/diamonds3_cherries.png',
    'phase_5.5/maps/diamonds3_cherry.png',
    'phase_5.5/maps/diamonds4_cherries.png',
    'phase_5.5/maps/diamonds4_cherry.png',
    'phase_5.5/maps/diamonds5_cherries.png',
    'phase_5.5/maps/diamonds6_cherry.png',
    'phase_5.5/maps/moon1.png',
    'phase_5.5/maps/moon2.png',
    'phase_5.5/maps/moon3.png',
    'phase_5.5/maps/moon4.png',
    'phase_5.5/maps/moon5.png',
    'phase_5.5/maps/moon6.png',
    'phase_5.5/maps/moon7.png',
    'phase_5.5/maps/stars1.png',
    'phase_5.5/maps/stars2.png',
    'phase_5.5/maps/stars3.png',
    'phase_5.5/maps/stars4.png',
    'phase_5.5/maps/stars5.png',
    'phase_5.5/maps/stars6.png',
    'phase_5.5/maps/stars7.png',
    'phase_5.5/maps/wall_paper_flower1.png',
    'phase_5.5/maps/wall_paper_flower2.png',
    'phase_5.5/maps/wall_paper_flower3.png',
    'phase_5.5/maps/wall_paper_flower4.png',
    'phase_5.5/maps/wall_paper_flower5.png',
    'phase_5.5/maps/wall_paper_flower6.png',
    'phase_5.5/maps/wall_paper_car.png',
    'phase_5.5/maps/wall_paper_car_neutral.png',
    'phase_5.5/maps/wall_paper_football_neutral.png',
    'phase_5.5/maps/wall_paper_clouds.png',
    'phase_5.5/maps/wall_paper_vine_neutral.png',
    'phase_5.5/maps/basket.png',
    'phase_5.5/maps/basket_neutral.png',
    'phase_5.5/maps/doll.png',
    'phase_5.5/maps/doll_neutral.png',
    'phase_5.5/maps/littleFlowers.png',
    'phase_5.5/maps/littleFlowers_neutral.png',
    'phase_5.5/maps/UWwallPaperAngelFish.png',
    'phase_5.5/maps/UWwallPaperAngelFishColor.png',
    'phase_5.5/maps/UWwallPaperBubbles.png',
    'phase_5.5/maps/UWwallPaperBubbles2.png',
    'phase_5.5/maps/UWwallPaperGreenFish.png',
    'phase_5.5/maps/UWwallPaperRedFish.png',
    'phase_5.5/maps/UWwallPaperSea_horse.png',
    'phase_5.5/maps/UWwallPaperShells.png',
    'phase_5.5/maps/UWwaterFloor1.png',
    'phase_5.5/maps/WesternBootWallpaper1.png',
    'phase_5.5/maps/WesternCactusWallpaper1.png',
    'phase_5.5/maps/WesternHatWallpaper1.png',
    'phase_5.5/maps/cats1.png',
    'phase_5.5/maps/bats2.png',
    'phase_5.5/maps/wall_paper_snowflakes.png',
    'phase_5.5/maps/wall_paper_hollyleaf.png',
    'phase_5.5/maps/wall_paper_snowman.png',
    'phase_5.5/maps/VdayWall1.png',
    'phase_5.5/maps/VdayWall2.png',
    'phase_5.5/maps/VdayWall3.png',
    'phase_5.5/maps/VdayWall4.png',
    'phase_5.5/maps/StPatWallpaper1.png',
    'phase_5.5/maps/StPatWallpaper2.png',
    'phase_5.5/maps/StPatWallpaper3.png',
    'phase_5.5/maps/StPatWallpaper4.png'
)
WAINSCOTING_TEXTURES = (
    'phase_3.5/maps/wall_paper_b3.png',
    'phase_3.5/maps/wall_paper_b4.png',
    'phase_5.5/maps/wall_paper_b4_greyscale.png',
    'phase_5.5/maps/wainscotings_neutral.png',
)
FLOOR_TEXTURES = (
    'phase_3/maps/floor_create_toon.png',
    'phase_3.5/maps/carpet.png',
    'phase_5.5/maps/floor_wood_neutral.png',
    'phase_5.5/maps/flooring_carpetA_neutral.png',
    'phase_4/maps/flooring_tile_neutral.png',
    'phase_5.5/maps/flooring_tileB2.png',
    'phase_4/maps/grass.png',
    'phase_4/maps/floor_tile_brick_diagonal2.png',
    'phase_4/maps/floor_tile_brick_diagonal.png',
    'phase_4/maps/plazz_tile.png',
    'phase_4/maps/sidewalk.png',
    'phase_3.5/maps/boardwalk_floor.png',
    'phase_3.5/maps/dustroad.png',
    'phase_5.5/maps/floor_woodtile_neutral.png',
    'phase_5.5/maps/floor_tile_neutral.png',
    'phase_5.5/maps/floor_tile_honeycomb_neutral.png',
    'phase_5.5/maps/UWwaterFloor1.png',
    'phase_5.5/maps/UWtileFloor4.png',
    'phase_5.5/maps/UWtileFloor3.png',
    'phase_5.5/maps/UWtileFloor2.png',
    'phase_5.5/maps/UWtileFloor1.png',
    'phase_5.5/maps/UWsandyFloor1.png',
    'phase_5.5/maps/floor_icecube.png',
    'phase_5.5/maps/floor_snow.png',
    'phase_5.5/maps/StPatsFloor1.png',
    'phase_5.5/maps/StPatsFloor2.png'
)

MOULDING_TEXTURES = (
    'phase_3.5/maps/molding_wood1.png',
    'phase_3.5/maps/molding_wood2.png',
    'phase_5.5/maps/bd_grey_border1.png',
    'phase_5.5/maps/dental_Border_wood_neutral.png',
    'phase_5.5/maps/littleFlowers_border.png',
    'phase_5.5/maps/littleFlowers_border_neutral.png',
    'phase_5.5/maps/ladybugs2_Border.png',
    'phase_5.5/maps/bd_grey_border1.png',
    'phase_5.5/maps/tt_t_ara_int_border_winterLights1.png',
    'phase_5.5/maps/tt_t_ara_int_border_winterLights2.png',
    'phase_5.5/maps/tt_t_ara_int_border_winterLights3.png',
    'phase_5.5/maps/tt_t_ara_int_border_valentine_cupid.png',
    'phase_5.5/maps/tt_t_ara_int_border_valentine_heart1.png',
    'phase_5.5/maps/tt_t_ara_int_border_valentine_heart2.png'
)


class PropSpecialInterior(PropSpecial):

    def __init__(self, generator, name, uuid, pos = Vec3(0, 0, 0), hpr = Vec3(0, 0, 0), scale = Vec3(1.0, 1.0, 1.0),
                 data: Optional[Dict] = None):
        PropSpecial.__init__(self, generator, name, uuid, pos, hpr, scale, data)

        self.model = PropPool.getProp(name)
        self.model.reparentTo(self)
        self.addSnapPoints()
        if not generator.isBuildLotOrEstate or not ClientSettings.PropGeneratorCollisions.get():
            collisions: NodePathCollection = self.findAllMatches('**/+CollisionNode')
            if collisions:
                coll: NodePath
                for coll in collisions:
                    if coll.getCollideMask() != ToontownGlobals.PropGenSnapPointBitMask:
                        coll.stash()

        self.updateData()

        self.wallpaperLabel: Optional[OnscreenText] = None
        self.wallpaperTexturePicker: Optional[TexturePicker] = None
        self.wallpaperColorPicker: Optional[ColorPickerGUI] = None

        self.floorLabel: Optional[OnscreenText] = None
        self.floorTexturePicker: Optional[TexturePicker] = None
        self.floorColorPicker: Optional[ColorPickerGUI] = None

        self.wainscotingLabel: Optional[OnscreenText] = None
        self.wainscotingTexturePicker: Optional[TexturePicker] = None
        self.wainscotingColorPicker: Optional[ColorPickerGUI] = None

        self.mouldingLabel: Optional[OnscreenText] = None
        self.mouldingTexturePicker: Optional[TexturePicker] = None
        self.mouldingColorPicker: Optional[ColorPickerGUI] = None

    def createGui(self):
        PropSpecial.createGui(self)
        # add an edit tab
        ''' Edit Page '''
        editPage = DirectFrame(parent = self.uiFrame, relief = None)
        editTitle = self.makeTitle(parent = editPage, text = TTLocalizer.PropEditorEditTitle)

        i = len(self.uiPages)
        self.pageButtons.append(AnimatedButton(
            parent = self.uiFrame,
            image = PropGlobals.PropUi.find(f'**/page_edit'),
            image_scale = 0.05,
            text = ('', TTLocalizer.PropEditorEditTitle, TTLocalizer.PropEditorEditTitle, ''),
            text_scale = 0.04,
            text_pos = (0, -0.06),
            image3_color = (0.8, 0.8, 0.8, 0.5),
            pos = (PropGlobals.UITabButtonStart + i / 20, 0, -0.46),
            command = self.selectPage,
            extraArgs = [i]
        ))

        pickerOffset = Vec3(-.55, 0, -.05)

        # WALLPAPER
        self.wallpaperLabel = OnscreenText(
            parent = editPage,
            text = TTLocalizer.PropEditorInteriorLabelWallpaper,
            scale = 0.04,
            pos = (-.2, 0.2)
        )

        self.wallpaperTexturePicker = TexturePicker(
            parent = editPage,
            textures = WALLPAPER_TEXTURES,
            selectedTexture = self.data.get('wallpaper_texture', None),
            pos = (.025, 0.0, 0.21),
            onChange = self.__setWallpaperTexture,
            pickerOffset = pickerOffset,
            pickerParent = editPage,
            scale = 0.7
        )
        self.wallpaperColorPicker = ColorPickerOption(
            None,
            'psti_wallpaper',
            parent = editPage,
            pos = (0.225, 0.0, 0.21),
            scale = .95,
            isForSettings = False,
            pickerParent = editPage,
            fadeScreen = False,
            startRGBA = VBase4(*self.data.get('wallpaper_color', (1.0, 1.0, 1.0, 1.0))),
            onCloseRGBA = self.__setWallpaperColor
        )
        self.wallpaperColorPicker.label.hide()

        # FLOOR
        self.floorLabel = OnscreenText(
            parent = editPage,
            text = TTLocalizer.PropEditorInteriorLabelFloor,
            scale = 0.04,
            pos = (-.2, .04)
        )

        self.floorTexturePicker = TexturePicker(
            parent = editPage,
            textures = FLOOR_TEXTURES,
            selectedTexture = self.data.get('floor_texture', None),
            pos = (.025, 0.0, 0.05),
            onChange = self.__setFloorTexture,
            pickerOffset = pickerOffset,
            pickerParent = editPage,
            scale = 0.7
        )

        self.floorColorPicker = ColorPickerOption(
            None,
            'psti_floor',
            parent = editPage,
            pos = (0.225, 0.0, 0.05),
            scale = .95,
            isForSettings = False,
            pickerParent = editPage,
            fadeScreen = False,
            startRGBA = VBase4(*self.data.get('floor_color', (1.0, 1.0, 1.0, 1.0))),
            onCloseRGBA = self.__setFloorColor
        )
        self.floorColorPicker.label.hide()

        # wainscoting
        self.wainscotingLabel = OnscreenText(
            parent = editPage,
            text = TTLocalizer.PropEditorInteriorLabelWainscoting,
            scale = 0.04,
            pos = (-.2, -0.12)
        )

        self.wainscotingTexturePicker = TexturePicker(
            parent = editPage,
            textures = WAINSCOTING_TEXTURES,
            selectedTexture = self.data.get('wainscoting_texture', None),
            pos = (.025, 0.0, -.11),
            onChange = self.__setWainscotingTexture,
            pickerOffset = pickerOffset,
            pickerParent = editPage,
            scale = 0.7
        )

        self.wainscotingColorPicker = ColorPickerOption(
            None,
            'psti_wainscoting',
            parent = editPage,
            pos = (0.225, 0.0, -.11),
            scale = .95,
            isForSettings = False,
            pickerParent = editPage,
            fadeScreen = False,
            startRGBA = VBase4(*self.data.get('wainscoting_color', (1.0, 1.0, 1.0, 1.0))),
            onCloseRGBA = self.__setWainscotingColor
        )
        self.wainscotingColorPicker.label.hide()

        if self._name == 'T-Shaped Toon Building Interior':
            # moulding
            self.mouldingLabel = OnscreenText(
                parent = editPage,
                text = TTLocalizer.PropEditorInteriorLabelMoulding,
                scale = 0.04,
                pos = (-.2, -0.28)
            )

            self.mouldingTexturePicker = TexturePicker(
                parent = editPage,
                textures = MOULDING_TEXTURES,
                selectedTexture = self.data.get('moulding_texture', None),
                pos = (.025, 0.0, -0.27),
                onChange = self.__setMouldingTexture,
                pickerOffset = pickerOffset,
                pickerParent = editPage,
                scale = 0.7
            )

            self.mouldingColorPicker = ColorPickerOption(
                None,
                'psti_moulding',
                parent = editPage,
                pos = (0.225, 0.0, -0.27),
                scale = .95,
                isForSettings = False,
                pickerParent = editPage,
                fadeScreen = False,
                startRGBA = VBase4(*self.data.get('moulding_color', (1.0, 1.0, 1.0, 1.0))),
                onCloseRGBA = self.__setMouldingColor
            )
            self.mouldingColorPicker.label.hide()

        self.uiPages.append(editPage)
        editPage.hide()

    def __setWallpaperTexture(self, texture: str):
        self.data['wallpaper_texture'] = texture
        self.generator.requestUpdateProp(self.uuid)

    def __setWallpaperColor(self, color: LColorf):
        self.data['wallpaper_color'] = [*color]
        self.generator.requestUpdateProp(self.uuid)

    def __setFloorTexture(self, texture: str):
        self.data['floor_texture'] = texture
        self.generator.requestUpdateProp(self.uuid)

    def __setFloorColor(self, color: LColorf):
        self.data['floor_color'] = [*color]
        self.generator.requestUpdateProp(self.uuid)

    def __setMouldingTexture(self, texture: str):
        self.data['moulding_texture'] = texture
        self.generator.requestUpdateProp(self.uuid)

    def __setMouldingColor(self, color: LColorf):
        self.data['moulding_color'] = [*color]
        self.generator.requestUpdateProp(self.uuid)

    def __setWainscotingTexture(self, texture: str):
        self.data['wainscoting_texture'] = texture
        self.generator.requestUpdateProp(self.uuid)

    def __setWainscotingColor(self, color: LColorf):
        self.data['wainscoting_color'] = [*color]
        self.generator.requestUpdateProp(self.uuid)

    def updateData(self):
        PropSpecial.updateData(self)
        # WALLPAPER
        wpNode = self.model.find('**/**TI_wallpaper')
        wpNode.setTexture(
            DataPackManager.getTexture(self.data.get('wallpaper_texture', WALLPAPER_TEXTURES[0])), 1
        )
        wpNode.setColorScale(
            VBase4(*self.data.get('wallpaper_color', (1.0, 1.0, 1.0, 1.0)))
        )
        wpbNode = self.model.find('**/**TI_wallpaper_border')
        wpbNode.setTexture(
            DataPackManager.getTexture(self.data.get('wallpaper_texture', WALLPAPER_TEXTURES[0])), 1
        )
        wpbNode.setColorScale(
            VBase4(*self.data.get('wallpaper_color', (1.0, 1.0, 1.0, 1.0)))
        )

        # WAINSCOTING (incorrectly spelled by disney as wainscotting lol)
        wsNode = self.model.find('**/**TI_wainscotting')
        wsNode.setTexture(
            DataPackManager.getTexture(self.data.get('wainscoting_texture', WAINSCOTING_TEXTURES[0])), 1
        )
        wsNode.setColorScale(
            VBase4(*self.data.get('wainscoting_color', (1.0, 1.0, 1.0, 1.0)))
        )

        # FLOOR
        flNode = self.model.find('**/**TI_floor')
        flNode.setTexture(
            DataPackManager.getTexture(self.data.get('floor_texture', FLOOR_TEXTURES[0])), 1
        )
        flNode.setColorScale(
            VBase4(*self.data.get('floor_color', (1.0, 1.0, 1.0, 1.0)))
        )

        if self._name == 'T-Shaped Toon Building Interior':
            # MOULDING (incorrectly spelled yet again by disney as molding)
            mNode = self.model.find('**/**TI_molding')
            mNode.setTexture(
                DataPackManager.getTexture(self.data.get('moulding_texture', MOULDING_TEXTURES[0])), 1
            )
            mNode.setColorScale(
                VBase4(*self.data.get('moulding_color', (1.0, 1.0, 1.0, 1.0)))
            )