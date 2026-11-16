"""
Prop Spawner - Prop Item
This is the ui element for each individual prop
Initially displays a Loading icon, then loads the prop model asynchronously
"""
from typing import Optional

from direct.gui import DirectGuiGlobals
from direct.gui.DirectGui import *
from direct.interval.LerpInterval import LerpHprInterval
from direct.interval.MetaInterval import Parallel
from panda3d.core import TextNode, Vec3, NodePath, TransparencyAttrib, Vec4, Shader

from toontown.moviemaker.MovieMakerGUI import MovieMakerGUI
from toontown.sandbox import PropGlobals
from toontown.sandbox.PropGlobals import PropPool
from toontown.toonbase import TTLocalizer, ClientSettings
from toontown.toonbase.ToonBase import ToonBase
from toontown.battle import BattleProps
from toontown.toontowngui.AnimatedButton import AnimatedButton


class PropSpawnerItem(AnimatedButton):
    FavoriteStar: NodePath = loader.loadModel('phase_3/models/gui/ttrm_m_gui_chat_emojis').find("**/star")

    def __init__(self, spawnerGUI, propName, parent, **kwargs):
        self.spawnerGUI = spawnerGUI
        self.propName = propName
        self.prop = PropGlobals.PropList[self.propName]

        optiondefs = (
            ('image', MovieMakerGUI.iconBg, None),
            ('frameSize', (-0.07, 0.07, -0.07, 0.07), None),
            ('pos', (0, 0, 0), None),
            ('image_scale', 0.13, None),
            ('pressEffect', False, None),
            ('hoverEvent', self.__hoverTooltip, None),
            ('unHoverEvent', self.__unhoverTooltip, None),
            ('command', self.__selectProp, None)
        )

        self.defineoptions(kwargs, optiondefs)
        AnimatedButton.__init__(self, parent)
        self.initialiseoptions(PropSpawnerItem)

        # SHOW A MENU ON RIGHT CLICK
        self.bind(DirectGuiGlobals.B3PRESS, self.__toggleFavorite)

        nodeName = f"**/bsr_ico_{propName.lower().replace(' ', '_').replace('/', '_')}"
        node: NodePath = MovieMakerGUI.iconGui.find(nodeName)
        if node.isEmpty():
            print(f'Unable to locate icon for {nodeName} ({propName})')
            self.icon = None
            return
        self.icon: NodePath = node.instanceTo(self)
        self.icon.setScale(0.12)

        if propName in ClientSettings.FavoriteProps.get():
            self.star: NodePath = self.FavoriteStar.instanceTo(self)
            self.star.setScale(0.03)
            self.star.setPos(0.04, 0, -0.04)
        else:
            self.star: Optional[NodePath] = None

        #mdl = PropPool.getProp(self.propName)
        #mdl.setBin('unsorted', 0, 1)
        #self.loadPropCallback(mdl)
        ## loader.loadModel(self.prop[2][0], callback = self.loadPropCallback)

    def __hoverTooltip(self):
        self.spawnerGUI.showTooltip(self.propName)

    def __unhoverTooltip(self):
        self.spawnerGUI.hideTooltip()

    def __selectProp(self):
        messenger.send('wakeup')
        self.spawnerGUI.select(self.propName)

    def __toggleFavorite(self, e):
        if self.propName in ClientSettings.FavoriteProps.get():
            self.__removeFromFavorites()
            if self.star:
                self.star.removeNode()
        else:
            self.__addToFavorites()
            self.star: NodePath = self.FavoriteStar.instanceTo(self)
            self.star.setScale(0.03)
            self.star.setPos(0.04, 0, -0.04)

    def __addToFavorites(self):
        self.spawnerGUI.addToFavorites(self.propName)

    def __removeFromFavorites(self):
        self.spawnerGUI.removeFromFavorites(self.propName)

    def destroy(self):
        if self.icon:
            self.icon.removeNode()
        self.icon = None
        AnimatedButton.destroy(self)

    def loadPropCallback(self, model):  # type: (NodePath) -> None
        if model:
            self.preview, self.ival = self.makeFrameModel(model)
            self.preview.reparentTo(self)
            self.preview.setScale(0.1)
            self.ival.loop()

    def makeFrame(self):  # type: () -> DirectFrame
        # from direct.gui.DirectGui import DirectFrame
        frame = DirectFrame(parent = self, frameSize = (-1.0, 1.0, -1.0, 1.0), relief = None)
        return frame

    def makeFrameModel(self, model):  # type: (NodePath) -> (DirectFrame, LerpHprInterval)
        """
        Properly scale and position the model in the frame, and setup a rotation interval
        :param model:
        :return:
        """
        frame = self.makeFrame()
        ival = None
        if model:
            model.setDepthTest(1)
            model.setDepthWrite(1)
            # Small hack to fix billboards on the UI
            for np in model.findAllMatches('**/*'):
                if isinstance(np, NodePath):
                    if np.hasBillboard():
                        np.setBillboardPointEye()
            model.setTransparency(TransparencyAttrib.MDual)
            pitch = frame.attachNewNode('pitch')
            rotate = pitch.attachNewNode('rotate')
            scale = rotate.attachNewNode('scale')
            model.reparentTo(scale)
            bMin, bMax = model.getTightBounds()
            center = (bMin + bMax) / 2.0
            model.setPos(-center[0], -center[1], -center[2])
            pitch.setP(20)
            bMin, bMax = pitch.getTightBounds()
            center = (bMin + bMax) / 2.0
            corner = Vec3(bMax - center)
            scale.setScale(1.0 / max(corner[0], corner[1], corner[2]))
            pitch.setY(2)
            ival = LerpHprInterval(
                    nodePath = rotate,
                    duration = 10,
                    hpr = Vec3(-315, 0, 0),
                    startHpr = Vec3(45, 0, 0),
                    name = f'propmenu{self.propName}')
        return frame, ival
