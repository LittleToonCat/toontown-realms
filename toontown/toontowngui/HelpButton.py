""" GUI Help Button - 010121 """

from direct.gui.DirectGui import *
from panda3d.core import *
from toontown.toonbase import TTLocalizer, ToontownGlobals, ClientSettings
from direct.interval.IntervalGlobal import *

from toontown.toontowngui.GUIChatBalloon import GUIChatBalloon

HideHelpEvent = 'HideHelpBubble'


class HelpButton(DirectButton):
    gui = loader.loadModel('phase_3.5/models/gui/tt_m_gui_brd_help')
    
    def __init__(self, contents, parent = aspect2d, hoverText = '', inScroll = False, **kwargs):
        """
        :param contents: The text to be written inside the bubble
        :param parent: The parent of the bubble
        :param hoverText: The text to appear when hovering over the help button
        :param inScroll: Specifies whether the button is inside of a scrolled frame so we can override it
        :param kwargs: extra key word args if needed
        """
        self.inScroll = inScroll
        self.helpVisible = False

        optiondefs = (
            ('relief', None, None),
            ('text', ('', hoverText, hoverText), None),
            ('text_pos', (0.0, -0.15), None),
            ('text_fg', (1.0, 1.0, 1.0, 1.0), None),
            ('text_scale', 0.1, None),
            ('text_align', TextNode.ACenter, None),
            ('text_style', 3, None),
            ('image', (self.gui.find('**/tt_t_gui_brd_helpUp'),
                      self.gui.find('**/tt_t_gui_brd_helpDown'),
                      self.gui.find('**/tt_t_gui_brd_helpHover'),
                      self.gui.find('**/tt_t_gui_brd_helpDown')), None),
            ('scale', 0.4, None),
            ('reversed', True, None),
            ('command', self.toggleHelp, None)
        )
        self.defineoptions(kwargs, optiondefs)
        DirectButton.__init__(self, parent)
        self.initialiseoptions(HelpButton)
        
        # Generate a chat balloon for the help
        chatNode = GUIChatBalloon(text = contents, font = ToontownGlobals.getInterfaceFont(), reversed = self['reversed'])
        self.helpBubble = self.attachNewNode(chatNode.node(), 1000)
        self.helpBubble.setScale(0.05)
        self.helpBubble.reparentTo(hidden)

        # Listen for an event that hides our help button
        self.accept(HideHelpEvent, self.hideHelp)
        self.accept('stickerBookExited', self.hideHelp)

    def destroy(self):
        """
        Clean up and remove any tasks
        """
        self.hideHelp()
        self.ignoreAll()
        DirectButton.destroy(self)

    def hideHelp(self):
        self.helpVisible = False
        self.helpBubble.reparentTo(hidden)
        taskMgr.remove(f'helpBubble_{id(self)}')
        
    def toggleHelp(self):
        if self.helpVisible:
            self.helpBubble.reparentTo(hidden)
            taskMgr.remove(f'helpBubble_{id(self)}')
        else:
            messenger.send(HideHelpEvent)
            self.helpBubble.reparentTo(self, 1000)
            self.helpBubble.setScale(0, 0, 0)
            # We have to handle the bubble inside of scroll frames a bit differently
            if self.inScroll:
                self.helpBubble.reparentTo(aspect2d, 9000)
                taskMgr.add(self.positionBubbleTask, f'helpBubble_{id(self)}')
                if ClientSettings.GUIAnimations.get():
                    Sequence(
                        self.helpBubble.scaleInterval(.2, VBase3(.05), blendType = 'easeInOut'),
                        self.helpBubble.scaleInterval(.09, VBase3(.045), blendType = 'easeInOut')).start()
                else:
                    self.helpBubble.setScale(0.045)
            else:
                if ClientSettings.GUIAnimations.get():
                    Sequence(
                        self.helpBubble.scaleInterval(.2, VBase3(.12), blendType = 'easeInOut'),
                        self.helpBubble.scaleInterval(.09, VBase3(.11), blendType = 'easeInOut')).start()
                else:
                    self.helpBubble.setScale(0.11)
        self.helpVisible = not self.helpVisible

    def positionBubbleTask(self, task):
        """
        In case we are in a scroll frame, we have to do this bad solution
        """
        if self.helpVisible:
            self.helpBubble.setPos(self, 0, 0, 0)
            # If we go outside of the frame, we hide the bubble
            if self.helpBubble.getZ() > 0.59:
                self.hideHelp()
                return task.done
            return task.cont
        else:
            return task.done
