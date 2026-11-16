"""
All generic animated props for the prop generator will use this type

the 'anims' tag in the data field contains a list of animations
props with more than one animation can be changed via the prop's menu
"""
from typing import Optional, Dict

from direct.actor.Actor import Actor
from direct.gui import DirectGuiGlobals
from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectScrolledList import DirectScrolledList, DirectScrolledListItem
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import Vec3, TextNode, VBase4

from toontown.sandbox import PropGlobals
from toontown.sandbox.Prop import Prop
from toontown.sandbox.PropGlobals import LIST_MODEL, LIST_ATTRIBUTES, PropPool
from toontown.toonbase import TTLocalizer
from toontown.toontowngui.AnimatedButton import AnimatedButton


class PropAnimated(Prop):
    def __init__(self, generator, name, uuid, pos = Vec3(0, 0, 0), hpr = Vec3(0, 0, 0),
                 scale = Vec3(1.0, 1.0, 1.0), data: Optional[Dict] = None):
        Prop.__init__(self, generator, name, uuid, pos, hpr, scale, data)

        self.animStateButtons = None

        if 'anims' not in self.attributes:
            self.notify.error(f'Animated Prop {self.name} has no anims defined!')
            return
        self.anims = self.attributes['anims']  # type: dict[str, str]

        self.model = Actor(PropPool.getProp(name), self.anims)
        self.model.reparentTo(self)
        self.model.setBlend(frameBlend = True)

        # If we have a scale adjustment for a prop, apply that
        self.model.setScale(self.attributes.get('scale', 1.0))

        collisions = self.model.findAllMatches('**/+CollisionNode')
        if collisions:
            for coll in collisions:
                coll.stash()
        self.updateData()

    def createGui(self):
        Prop.createGui(self)
        # add an animations tab
        ''' Anim Page '''
        animPage = DirectFrame(parent = self.uiFrame, relief = None)
        animTitle = self.makeTitle(parent = animPage, text = TTLocalizer.PropEditorAnimsTitle)

        i = len(self.uiPages)
        self.pageButtons.append(AnimatedButton(
                parent = self.uiFrame,
                image = PropGlobals.PropUi.find(f'**/page_edit'),
                image_scale = 0.05,
                text = ('', TTLocalizer.PropEditorAnimsTitle, TTLocalizer.PropEditorAnimsTitle, ''),
                text_scale = 0.04,
                text_pos = (0, -0.06),
                image3_color = (0.8, 0.8, 0.8, 0.5),
                pos = (PropGlobals.UITabButtonStart + i / 20, 0, -0.46),
                command = self.selectPage,
                extraArgs = [i]
        ))

        animList = DirectScrolledList(
                parent = animPage,
                frameSize = (0.0, 0.0, 0.0, 0.0),
                pos = (0, 0, -.1),
                relief = None,
                numItemsVisible = 6,
                forceHeight = 0.07,
                itemFrame_frameSize = (-.2, .2, -.4, .05),
                itemFrame_pos = (0.0, 0.0, 0.2),
                itemFrame_relief = None,
                decButton_relief = None,
                incButton_relief = None,
        )
        for x in (self.anims.keys()):
            listItem = DirectScrolledListItem(relief = None,
                                              parent = animList,
                                              text = x,
                                              text_align = TextNode.ACenter,
                                              text_scale = 0.05,
                                              image = PropGlobals.PropUi.find('**/button_normal'),
                                              image_scale = (0.231, 1, 0.0605),
                                              image_pos = (0.0, 0.0, 0.013),
                                              image0_color = VBase4(0),
                                              image1_color = VBase4(0),
                                              image2_color = VBase4(1.0, 1.0, 1.0, 0.3),
                                              image3_color = VBase4(1),
                                              command = self.selectAnimation, extraArgs = [x])
            animList.addItem(listItem)
            if 'active_anim' in self.data:
                if x == self.data['active_anim']:
                    listItem['state'] = DirectGuiGlobals.DISABLED
                    animList.currentSelected = listItem

        animPause = AnimatedButton(
                parent = animPage,
                image = (
                    PropGlobals.PropUi.find(f'**/anim_pause'),
                    PropGlobals.PropUi.find(f'**/anim_pause'),
                    PropGlobals.PropUi.find(f'**/anim_pause'),
                    PropGlobals.PropUi.find(f'**/anim_pause_sel')
                ),
                image_scale = 0.078,
                pos = (-.15, 0, .25),
                command = self.selectAnimState,
                extraArgs = [0]
        )

        anim1x = AnimatedButton(
                parent = animPage,
                image = (
                    PropGlobals.PropUi.find(f'**/anim_1x'),
                    PropGlobals.PropUi.find(f'**/anim_1x'),
                    PropGlobals.PropUi.find(f'**/anim_1x'),
                    PropGlobals.PropUi.find(f'**/anim_1x_sel')
                ),
                image_scale = 0.078,
                pos = (-.05, 0, .25),
                command = self.selectAnimState,
                extraArgs = [1]
        )

        anim2x = AnimatedButton(
                parent = animPage,
                image = (
                    PropGlobals.PropUi.find(f'**/anim_2x'),
                    PropGlobals.PropUi.find(f'**/anim_2x'),
                    PropGlobals.PropUi.find(f'**/anim_2x'),
                    PropGlobals.PropUi.find(f'**/anim_2x_sel')
                ),
                image_scale = 0.078,
                pos = (.05, 0, .25),
                command = self.selectAnimState,
                extraArgs = [2]
        )

        anim3x = AnimatedButton(
                parent = animPage,
                image = (
                    PropGlobals.PropUi.find(f'**/anim_3x'),
                    PropGlobals.PropUi.find(f'**/anim_3x'),
                    PropGlobals.PropUi.find(f'**/anim_3x'),
                    PropGlobals.PropUi.find(f'**/anim_3x_sel')
                ),
                image_scale = 0.078,
                pos = (.15, 0, .25),
                command = self.selectAnimState,
                extraArgs = [3]
        )

        self.animStateButtons = (animPause, anim1x, anim2x, anim3x)
        for i, btn in enumerate(self.animStateButtons):
            btn['state'] = DirectGuiGlobals.DISABLED if i == self.data.get('anim_state', 0) \
                else DirectGuiGlobals.NORMAL

        self.uiPages.append(animPage)
        animPage.hide()

    def deselect(self):
        Prop.deselect(self)
        self.animStateButtons = None

    def removeNode(self):
        self.model.cleanup()
        Prop.removeNode(self)

    def selectAnimState(self, state):
        """
        Select which anim state
        :param state: Anim State (0: Pause, 1: 1x, 2: 2x, 3: 3x)
        :return:
        """
        self.data['anim_state'] = state
        self.generator.requestUpdateProp(self.uuid)

    def selectAnimation(self, anim):  # type: (str) -> None
        """
        Select which animation to play
        :param anim: Animation name
        """
        if anim in self.anims:
            self.data['active_anim'] = anim
            if 'anim_state' not in self.data:
                self.data['anim_state'] = 1

            self.generator.requestUpdateProp(self.uuid)

    def updateData(self):
        Prop.updateData(self)
        if 'active_anim' in self.data:
            if self.data['active_anim'] in self.anims:
                self.model.loop(self.data['active_anim'])
                if 'anim_state' not in self.data:
                    self.data['anim_state'] = 1
            if 'anim_state' in self.data:
                if self.data['anim_state'] == 0:
                    self.model.stop()
                else:
                    self.model.setPlayRate(self.data['anim_state'], self.data['active_anim'])
                if self.animStateButtons:
                    for i, btn in enumerate(self.animStateButtons):
                        btn['state'] = DirectGuiGlobals.DISABLED if i == self.data['anim_state'] \
                            else DirectGuiGlobals.NORMAL


