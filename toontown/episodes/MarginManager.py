from panda3d.toontown import MarginManager as OtpMarginManager
from panda3d.core import NodePath

from direct.gui import DirectGuiGlobals

from copy import deepcopy


class EpisodeMarginManager(OtpMarginManager):
    def __init__(self):
        OtpMarginManager.__init__(self)
        """ Modify this chunk as you wish """
        self.__leftCells = [
            self.addGridCell(0, 1, -1.33333333333, 1.33333333333, -1.0, 1.0, base.a2dTopLeft, (0.222222, 0, -1.5)),
            self.addGridCell(0, 2, -1.33333333333, 1.33333333333, -1.0, 1.0, base.a2dTopLeft, (0.222222, 0, -1.16667)),
            self.addGridCell(0, 3, -1.33333333333, 1.33333333333, -1.0, 1.0, base.a2dTopLeft, (0.222222, 0, -0.833333))]
        self.__bottomCells = [self.addGridCell(0.5, 0, -1.33333333333, 1.33333333333, -1.0, 1.0, base.a2dBottomCenter,
                                               (-0.888889, 0, 0.166667)),
                              self.addGridCell(1.5, 0, -1.33333333333, 1.33333333333, -1.0, 1.0, base.a2dBottomCenter,
                                               (-0.444444, 0, 0.166667)),
                              self.addGridCell(2.5, 0, -1.33333333333, 1.33333333333, -1.0, 1.0, base.a2dBottomCenter,
                                               (0, 0, 0.166667)),
                              self.addGridCell(3.5, 0, -1.33333333333, 1.33333333333, -1.0, 1.0, base.a2dBottomCenter,
                                               (0.444444, 0, 0.166667)),
                              self.addGridCell(4.5, 0, -1.33333333333, 1.33333333333, -1.0, 1.0, base.a2dBottomCenter,
                                               (0.888889, 0, 0.166667))]
        self.__rightCells = [
            self.addGridCell(5, 2, -1.33333333333, 1.33333333333, -1.0, 1.0, base.a2dTopRight,
                             (-0.222222, 0, -1.16667)),
            self.addGridCell(5, 1, -1.33333333333, 1.33333333333, -1.0, 1.0, base.a2dTopRight, (-0.222222, 0, -1.5))]
        self.__topCells = []

        base.aspect2d.attachNewNode(self, DirectGuiGlobals.MIDGROUND_SORT_INDEX + 2)

    def setCellsAvailable(self, cell_list, available):
        for cell in cell_list:
            self.setCellAvailable(cell, available)

    def showNode(self):
        NodePath(self).show()

    def hideNode(self):
        NodePath(self).hide()

    """
    The following are for getting our cells; we deepcopy them so someone doesn't accidentally (or purposefully)
    modify our cells.
    """
    def getLeftCells(self):
        return deepcopy(self.__leftCells)

    leftCells = property(getLeftCells)

    def getBottomCells(self):
        return deepcopy(self.__bottomCells)

    bottomCells = property(getBottomCells)

    def getRightCells(self):
        return deepcopy(self.__rightCells)

    rightCells = property(getRightCells)

    def getTopCells(self):
        return deepcopy(self.__topCells)

    topCells = property(getTopCells)
