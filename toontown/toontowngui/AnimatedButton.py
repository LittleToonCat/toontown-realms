from direct.gui import DirectGuiGlobals
from direct.gui.DirectButton import DirectButton
from direct.gui.OnscreenImage import OnscreenImage
from direct.interval.LerpInterval import LerpScaleInterval
from direct.interval.MetaInterval import Sequence
from panda3d.core import TransparencyAttrib

from toontown.toonbase import ClientSettings


class AnimatedButton(DirectButton):

    def __init__(self, parent = aspect2d, scale = 1.0, **kwargs):
        optiondefs = (
            ('relief', None, None),
            ('pressEffect', False, None),
            ('scale', scale, None),
            ('hoverEvent', None, None),
            ('hoverEventArgs', [], None),
            ('unHoverEvent', None, None),
            ('unHoverEventArgs', [], None)
        )
        self.scale = scale
        self.defineoptions(kwargs, optiondefs)
        DirectButton.__init__(self, parent = parent)
        self.initialiseoptions(AnimatedButton)

        self.setTransparency(TransparencyAttrib.MAlpha)

        self.activeAnim = None
        self.isHovering = False

        self.bind(DirectGuiGlobals.ENTER, self.__hover)
        self.bind(DirectGuiGlobals.EXIT, self.__unHover)
        self.bind(DirectGuiGlobals.B1PRESS, self.__press)
        self.bind(DirectGuiGlobals.B1RELEASE, self.__release)

    def destroy(self):
        self.removeAllTasks()
        self.unbind(DirectGuiGlobals.ENTER)
        self.unbind(DirectGuiGlobals.EXIT)
        self.unbind(DirectGuiGlobals.B1PRESS)
        self.unbind(DirectGuiGlobals.B1RELEASE)
        if self.activeAnim:
            self.activeAnim.finish()
        OnscreenImage.destroy(self)

    ''' Button Animations '''

    def __hover(self, e):
        if self['hoverEvent']:
            self['hoverEvent'](*self['hoverEventArgs'])
        if not ClientSettings.GUIAnimations.get():
            self.setScale(self.scale * 1.06)
            return
        self.isHovering = True
        startScale = self.getScale()
        if self.activeAnim:
            self.activeAnim.finish()
        self.activeAnim = Sequence(
                LerpScaleInterval(
                        self,
                        0.1,
                        scale = self.scale * 1.1,
                        startScale = startScale,
                        blendType = 'easeInOut'
                ),
                LerpScaleInterval(
                        self,
                        0.1,
                        scale = self.scale * 1.06,
                        blendType = 'easeInOut'
                ),
                name = f'{self.guiId}.hover'
        )

        self.activeAnim.start()

    def __unHover(self, e):
        if self['unHoverEvent']:
            self['unHoverEvent'](*self['unHoverEventArgs'])
        if not ClientSettings.GUIAnimations.get():
            self.setScale(self.scale)
            return
        self.isHovering = False
        startScale = self.getScale()
        if self.activeAnim:
            self.activeAnim.finish()

        self.activeAnim = Sequence(
                LerpScaleInterval(
                        self,
                        0.1,
                        scale = self.scale * .98,
                        startScale = startScale,
                        blendType = 'easeInOut'
                ),
                LerpScaleInterval(
                        self,
                        0.1,
                        scale = self.scale,
                        blendType = 'easeInOut'
                ),
                name = f'{self.guiId}.unhover'
        )
        self.activeAnim.start()

    def __press(self, e):
        if not ClientSettings.GUIAnimations.get():
            self.setScale(self.scale * 0.9)
            return
        startScale = self.getScale()
        if self.activeAnim:
            self.activeAnim.finish()
        self.activeAnim = Sequence(
                LerpScaleInterval(
                        self,
                        0.1,
                        scale = self.scale * 0.85,
                        startScale = startScale,
                        blendType = 'easeInOut'
                ),
                LerpScaleInterval(
                        self,
                        0.1,
                        scale = self.scale * 0.9,
                        blendType = 'easeInOut'
                ),
                name = f'{self.guiId}.press'
        )
        self.activeAnim.start()

    def __unPress(self, e):
        if not ClientSettings.GUIAnimations.get():
            self.setScale(self.scale)
            return
        startScale = self.getScale()
        if self.activeAnim:
            self.activeAnim.finish()
        if startScale == self.scale:
            return
        self.activeAnim = Sequence(
                LerpScaleInterval(
                        self,
                        0.1,
                        scale = self.scale * 1.05,
                        startScale = startScale,
                        blendType = 'easeInOut'
                ),
                LerpScaleInterval(
                        self,
                        0.1,
                        scale = self.scale,
                        blendType = 'easeInOut'
                ),
                name = f'{self.guiId}.unPress'
        )
        self.activeAnim.start()

    def __release(self, e):
        if self.isHovering:
            self.__hover(None)
        else:
            self.__unPress(None)
