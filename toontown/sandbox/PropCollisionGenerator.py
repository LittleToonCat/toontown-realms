"""
COLLISION GENERATORS
"""
from panda3d.core import Vec3

from toontown.sandbox.Prop import Prop
from toontown.sandbox import PropGlobals
from toontown.sandbox.PropGlobals import LIST_MODEL, PropPool
from typing import Optional, Dict

from toontown.toonbase import ClientSettings


class PropCollisionGenerator(Prop):
    def __init__(self, generator, name, uuid, pos = Vec3(0, 0, 0), hpr = Vec3(0, 0, 0), scale = Vec3(1.0, 1.0, 1.0),
                 data: Optional[Dict] = None):
        Prop.__init__(self, generator, name, uuid, pos, hpr, scale, data)
        self.model = PropPool.getProp(name)
        self.model.reparentTo(self)
        self.notify.debug("SETTING ShADER")
        self.setShader(PropGlobals.CollisionVisualizerShader)
        if self.generator.windowOpen:
            self.updateVisualization(True)
        else:
            self.updateVisualization(False)
        self.accept('openPropGenUI', self.updateVisualization, extraArgs = [True])
        self.accept('closePropGenUI', self.updateVisualization, extraArgs = [False])

        self.accept('settings-updated', self.updateHidden)

        if not ClientSettings.PropGeneratorCollisions.get():
            collisions = self.findAllMatches('**/+CollisionNode')
            if collisions:
                for coll in collisions:
                    coll.stash()

    def removeNode(self):
        self.ignoreAll()
        Prop.removeNode(self)

    def propSelected(self, prop):
        Prop.propSelected(self, prop)
        self.updateVisualization(prop == self)

    def createGui(self):
        Prop.createGui(self)

    def deselect(self):
        if not self.generator.windowOpen:
            self.updateVisualization(False)
        Prop.deselect(self)

    def updateVisualization(self, state = False):
        """
        :param state: 0: DEFAULT (SHOW WHEN CLOSE) / 1: FORCE SHOW
        """
        self.setShaderInput('forceVisible', state)
        self.updateHidden()

    def updateHidden(self):
        self.setShaderInput('forceHide', not ClientSettings.VisualizeCollisionGenerators.get())

    def updateData(self):
        self.notify.debug(f'Updating data for {self.uuid}:\n      ->{self.data}')
        if 'color_scale' in self.data:
            self.setColorScale(*self.data['color_scale'])
