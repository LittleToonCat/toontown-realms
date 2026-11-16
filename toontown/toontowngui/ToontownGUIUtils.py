from direct.gui.DirectFrame import DirectFrame
from otp.otpgui.OTPGUIUtils import *

from toontown.toonbase import ToontownGlobals
from toontown.toontowngui.GUIChatBalloon import GUIChatBalloon


class ToolTip(DirectFrame):
    def __init__(self, contents):
        DirectFrame.__init__(self, parent = aspect2dp)
        # Generate a chat balloon for the help
        chatNode = GUIChatBalloon(text = contents, font = ToontownGlobals.getInterfaceFont(), reversed = True)
        self.helpBubble = self.attachNewNode(chatNode.node(), 1000)
        self.helpBubble.setScale(0.05)
        taskMgr.add(self.updatePosition, self.uniqueName('tooltip-pos-task'))

    def destroy(self):
        taskMgr.remove(self.uniqueName('tooltip-pos-task'))
        DirectFrame.destroy(self)

    def updatePosition(self, task):
        if base.mouseWatcherNode.hasMouse():
            mouse = base.mouseWatcherNode.getMouse()
            self.setPos(render2d, (mouse[0], 0, mouse[1]))
        return task.cont
