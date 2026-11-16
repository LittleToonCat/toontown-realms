"""
Special curb pile prop type
This will be a special prop with a menu which
allows you to choose between the different curb styles 
"""
from direct.gui.DirectFrame import DirectFrame
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import Vec3, NodePath

from otp.otpbase.PythonUtil import bound
from toontown.sandbox import PropGlobals
from toontown.sandbox.PropGlobals import PropPool
from toontown.sandbox.PropSpecial import PropSpecial
from toontown.sandbox.PropUI import Dropdown
from toontown.toonbase import TTLocalizer
from toontown.toontowngui.AnimatedButton import AnimatedButton
from typing import Optional, Dict


class PropSpecialCurbPile(PropSpecial):
    curbTextures = ('phase_3.5/maps/curb_brown_even.png', 'phase_3.5/maps/curb_boardwalk.png',
                    'phase_3.5/maps/grassDG.png', 'phase_3.5/maps/curb_red_even.png',
                    'phase_3.5/maps/snow.png', 'phase_3.5/maps/curb_blue_even.png',
                    'phase_3.5/maps/curb_purple_even.png')

    def __init__(self, generator, name, uuid, pos = Vec3(0, 0, 0), hpr = Vec3(0, 0, 0), scale = Vec3(1.0, 1.0, 1.0),
                 data: Optional[Dict] = None):
        PropSpecial.__init__(self, generator, name, uuid, pos, hpr, scale, data)
        self.model = PropPool.getProp(name)
        self.model.reparentTo(self)

        collisions = self.findAllMatches('**/+CollisionNode')
        if collisions:
            for coll in collisions:
                coll.stash()

        self.updateData()

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
                pos = (PropGlobals.UITabButtonStart + i / 20, 0, -0.56),
                command = self.selectPage,
                extraArgs = [i]
        ))

        curbStyle = Dropdown(
                parent = editPage,
                items = TTLocalizer.PropEditorSideTypes,
                pos = PropGlobals.UIStrCurbStyleDropPos,
                selected = self.data.get('curb_tex', 0),
                labelText = TTLocalizer.PropEditorStreetLabelCurb,
                onChangePassIndex = True,
                onChange = self.selectCurbStyle
        )

        self.uiPages.append(editPage)
        editPage.hide()

    def selectCurbStyle(self, textureIndex: int):
        """
        Select which effect to apply
        """

        self.data['curb_tex'] = textureIndex
        self.generator.requestUpdateProp(self.uuid)

    def updateData(self):
        PropSpecial.updateData(self)

        self.model.findAllMatches('**/brick*').setTexture(
            loader.loadTexture(self.curbTextures[bound(self.data.get('curb_tex', 0), 0,
                                                       len(self.curbTextures) - 1)]), 1
        )
