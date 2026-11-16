from panda3d.core import TextNode
from toontown.toonbase import TTLocalizer
from toontown.toonbase.ToontownGlobals import *
from direct.interval.IntervalGlobal import *
from direct.directnotify import DirectNotifyGlobal
from direct.gui import OnscreenText

class PlayByPlayText(OnscreenText.OnscreenText):
    notify = DirectNotifyGlobal.directNotify.newCategory('PlayByPlayText')

    def __init__(self, scale = 0.4475, pos = (0, -0.15), fg=(1, 0, 0, 1)):
        # Create a node for our text to parent to.
        playByPlayNode = NodePath('playByPlay')
        playByPlayNode.reparentTo(base.a2dTopCenter)
        playByPlayNode.setPos(0, 0, -0.1825)

        # Create our text and parent it to the above node.
        # We lower it a little in order to create that effect where it scales in from the center.
        OnscreenText.OnscreenText.__init__(
            self, 
            parent = playByPlayNode, 
            mayChange = 1,
            pos = pos,
            scale = scale, 
            fg = fg, 
            font = getSignFont(), 
            wordwrap = 30,
            align = TextNode.ACenter
        )
        self.tScale = scale

    def getShowInterval(self, text, duration):
        # Our show interval should add up to our duration in total time.

        return Sequence(
            Func(self.hide),
            Wait(duration * 0.2),
            Func(self.setText, text),
            Func(self.setColorScale, (1, 1, 1, 1)),
            Func(self.show),
            LerpScaleInterval(self, duration * 0.075, self.tScale + 0.05, startScale = 0.01, blendType = 'easeInOut'),
            LerpScaleInterval(self, duration * 0.025, self.tScale, blendType = 'easeInOut'),
            Wait(duration * 0.65),
            LerpColorScaleInterval(self, duration * 0.05, (1, 1, 1, 0), blendType = 'easeInOut'),
            Func(self.hide)
            )

    def getToonsDiedInterval(self, textList, duration):
        track = Sequence(Func(self.hide), Wait(duration * 0.3))
        waitGap = 0.6 / len(textList) * duration
        for text in textList:
            newList = [Func(self.setText, text),
             Func(self.show),
             Wait(waitGap),
             Func(self.hide)]
            track += newList

        track.append(Wait(duration * 0.1))
        return track
