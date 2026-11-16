from direct.gui.DirectGui import DGG, DirectButton
from direct.gui.OnscreenImage import OnscreenImage
from direct.interval.LerpInterval import LerpScaleInterval
from direct.interval.MetaInterval import Sequence
from panda3d.core import PGButton, TransparencyAttrib

from toontown.toonbase import ClientSettings


class SelectableButton(DirectButton):
    """
    SelectableButton(parent) - Create a DirectGuiWidget which responds
    to mouse clicks by setting a state of True or False and executes
    a callback function if defined.
    Uses an image swap rather than a text change to indicate state.
    """
    def __init__(self, parent = None, scale = 1.0, **kw):

        optiondefs = (
            # Define type of DirectGuiWidget
            ('pgFunc',         PGButton,   None),
            ('numStates',      4,          None),
            ('state',          DGG.NORMAL, None),
            ('pressEffect',    False,      None),
            ('animated',       True,       None),
            ('scale',          scale,      None),
            ('relief',         DGG.RAISED, None),
            ('invertedFrames', (1,),       None),
            # Command to be called on button click
            ('command',        None,       None),
            ('extraArgs',      [],         None),
            # Which mouse buttons can be used to click the button
            ('commandButtons', (DGG.LMB,),     self.setCommandButtons),
            # Sounds to be used for button events
            ('rolloverSound', DGG.getDefaultRolloverSound(), self.setRolloverSound),
            ('clickSound',    DGG.getDefaultClickSound(),    self.setClickSound),
            # Can only be specified at time of widget contruction
            # Do the text/graphics appear to move when the button is clicked
            ('pressEffect',     1,         DGG.INITOPT),
            ('unselectedImage',  None,      None),
            ('selectedImage',    None,      None),
            ('selectedImageColor', (1, 1, 1, 1), None),
            ('unselectedImageColor', (1, 1, 1, 1), None),            
            ('selectedTextFg', (0, 0, 0, 1), None),
            ('unselectedTextFg', (0, 0, 0, 1), None),
            ('isSelected',       False,     None),
            ('selectedArgs',     [],        None),
            ('listInst',         None,      None)
            )
        self.scale = scale

        # Merge keyword options with default options
        self.defineoptions(kw, optiondefs)

        DirectButton.__init__(self,parent)

        self.initialiseoptions(SelectableButton)

        self.setTransparency(TransparencyAttrib.MAlpha)

        self.activeAnim = None
        self.isHovering = False

        if self['animated']:
            self.bind(DGG.ENTER, self.__hover)
            self.bind(DGG.EXIT, self.__unHover)
            self.bind(DGG.B1PRESS, self.__press)
            self.bind(DGG.B1RELEASE, self.__release)

    def destroy(self):
        self.removeAllTasks()
        self.unbind(DGG.ENTER)
        self.unbind(DGG.EXIT)
        self.unbind(DGG.B1PRESS)
        self.unbind(DGG.B1RELEASE)
        if self.activeAnim:
            self.activeAnim.finish()
        if self['listInst']:
            self['listInst'].unselectItem(self)
        OnscreenImage.destroy(self)

    ''' Button Animations '''

    def __hover(self, e):
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

    def select(self):
        self['isSelected'] = True
        if self['selectedImage']:
            self['image'] = self['selectedImage']
        self['image_color'] = self['selectedImageColor']
        self['text_fg'] = self['selectedTextFg']

    def unselect(self):
        self['isSelected'] = False
        if self['unselectedImage']:
            self['image'] = self['unselectedImage']
        self['image_color'] = self['unselectedImageColor']
        self['text_fg'] = self['unselectedTextFg']

    def commandFunc(self, event):
        # Note: we must let the list keep track of our item first, then we change the item image...
        if self['isSelected']:
            # If the number of items is 1, we don't want to allow deselection of the item.
            # Perhaps we could add a mode to change the behavior, but that will come later.
            if self['listInst'] and self['listInst']['numSelectedItems'] > 1:
                self['listInst'].unselectItem(self)
        elif self['listInst']:
            self['listInst'].selectItem(self)

        DirectButton.commandFunc(self, event)