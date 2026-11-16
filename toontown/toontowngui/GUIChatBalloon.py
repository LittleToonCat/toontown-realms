""" Convenience Chat Balloon for GUIs """

from panda3d.core import *
from toontown.toonbase import ToontownGlobals, ClientSettings


class GUIChatBalloon(NodePath):
    BALLOON_MODEL = loader.loadModel('phase_3/models/props/chatbox') \
        if ClientSettings.ClassicChatBubbles.get() else \
        loader.loadModel('phase_3/models/gui/ttoff_m_gui_chat_bubbleGen')
    TEXT_OFFSET = (-0.05, -0.05, -.8)
    # Min Width / Height
    MIN_SIZE = (1.5, 1)
    PADDING = (0.4, 0.05)
    WORD_WRAP = 12.0
    
    def __init__(self, text, font = ToontownGlobals.getInterfaceFont(), reversed = False):
        NodePath.__init__(self, 'GUIChatBalloon')

        # Create balloon geom
        balloon = self.BALLOON_MODEL.copyTo(self)

        top = balloon.find('**/top')
        middle = balloon.find('**/middle')

        # Generate the text
        textNP = self.attachNewNode(TextNode('GUIChatBalloon_Text'))

        textNode = textNP.node()
        
        textNode.setText(text)
        textNode.setFont(font)
        textNode.setTextColor(VBase4(0.0, 0.0, 0.0, 1.0))
        textNode.setWordwrap(self.WORD_WRAP)
        
        # Bound the width and height
        textWidth = textNode.getWidth()
        if textWidth < self.MIN_SIZE[0]:
            textWidth = self.MIN_SIZE[0]
        textHeight = textNode.getHeight()
        if textHeight < self.MIN_SIZE[1]:
            textHeight = self.MIN_SIZE[1]

        # Add padding
        width = textWidth + self.PADDING[0]*2
        height = textHeight + self.PADDING[1]*2
        textNP.setZ(textNP, height)
        
        # Scale the balloon
        balloon.setSx(width/10)

        # Adjust the balloon parts
        middle.setSz(height)
        top.setZ(top, height-1)

        if reversed:
            # Invert the scale
            balloon.setSx(-balloon.getSx())
            # Render the backside
            balloon.setTwoSided(True)
        
        center = balloon.getBounds().getCenter()
        
        # Position the text
        textNP.setPos(center)
        textNP.setX(textNP, -(textWidth/2) + self.TEXT_OFFSET[0])
        textNP.setY(self.TEXT_OFFSET[1])
        textNP.setZ(top, self.TEXT_OFFSET[2] - self.PADDING[1])
