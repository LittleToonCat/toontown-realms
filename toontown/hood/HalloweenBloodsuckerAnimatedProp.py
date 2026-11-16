from . import AnimatedProp
from direct.actor import Actor
from direct.interval.IntervalGlobal import *
from toontown.toonbase import ClientSettings

class HalloweenBloodsuckerAnimatedProp(AnimatedProp.AnimatedProp):

    def __init__(self, node):
        AnimatedProp.AnimatedProp.__init__(self, node)
        parent = node.getParent()
        self.tube = Actor.Actor(node, copy=0)
        self.tube.reparentTo(parent)
        # it wont work without this?
        self.tube.setPosHpr(render, node.getPos(render), node.getHpr(render))
        self.node = self.tube

    def delete(self):
        AnimatedProp.AnimatedProp.delete(self)
        self.tube.cleanup()
        del self.tube
        del self.node

    def enter(self):
        AnimatedProp.AnimatedProp.enter(self)
        # i cant put this in init for some stupid reason??????!?!?!??!?
        self.tube.loadAnims({'wave': 'phase_5.5/models/estate/tt_a_ara_pty_tubeCogVictory_wave'})
        self.tube.setBlend(frameBlend=ClientSettings.SmoothAnimations.get())
        self.tube.setPlayRate(0.8, 'wave')
        self.tube.loop('wave')

    def exit(self):
        AnimatedProp.AnimatedProp.exit(self)
        self.tube.stop()
