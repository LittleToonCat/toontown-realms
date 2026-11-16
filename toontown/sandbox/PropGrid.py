"""
Visual prop grid
"""
import math

from direct.directtools.DirectGeometry import LineNodePath
from direct.showbase.DirectObject import DirectObject
from panda3d.core import NodePath, VBase4


class PropGrid(NodePath, DirectObject):
    def __init__(self):
        NodePath.__init__(self, 'PropGrid')
        DirectObject.__init__(self)
        self.reparentTo(hidden)
        self.gridSpacing = 2

        self.lines = self.attachNewNode('gridLines')

        # make the center line thicker and more visible
        self.centerLineNP = LineNodePath(self.lines)
        self.centerLineNP.lineNode.setName('centerLines')
        self.centerLineNP.setColor(VBase4(0.3, 0.55, 1, 1.0))
        self.centerLineNP.setThickness(4)

        # all other lines are thinner and transparent
        self.lineNP = LineNodePath(self.lines)
        self.lineNP.lineNode.setName('lines')
        self.lineNP.setColor(VBase4(0.3, 0.55, 1, 0.5))
        self.lineNP.setThickness(1)

    def setGridSize(self, size = 2):
        self.gridSpacing = size
        self.updateGridSize()

    def updateGridSize(self):
        self.lineNP.reset()
        self.centerLineNP.reset()

        numLines = int(math.ceil(20 / self.gridSpacing))
        scaledSize = numLines * self.gridSpacing

        lines = self.lineNP
        centerLines = self.centerLineNP
        for i in range(-numLines, numLines + 1):
            if i == 0:
                centerLines.moveTo(i * self.gridSpacing, -scaledSize, 0)
                centerLines.drawTo(i * self.gridSpacing, scaledSize, 0)
                centerLines.moveTo(-scaledSize, i * self.gridSpacing, 0)
                centerLines.drawTo(scaledSize, i * self.gridSpacing, 0)
            else:
                lines.moveTo(i * self.gridSpacing, -scaledSize, 0)
                lines.drawTo(i * self.gridSpacing, scaledSize, 0)
                lines.moveTo(-scaledSize, i * self.gridSpacing, 0)
                lines.drawTo(scaledSize, i * self.gridSpacing, 0)

        lines.create()
        centerLines.create()

