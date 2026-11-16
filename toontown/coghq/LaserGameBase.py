from direct.distributed import ClockDelta
from direct.task import Task
import random

class LaserGameBase:

    def __init__(self, parent, funcSuccess, funcFail, funcSendGrid, funcSetGrid):
        self.parent = parent
        self.funcSuccess = funcSuccess
        self.funcFail = funcFail
        self.funcSendGrid = funcSendGrid
        self.funcSetGrid = funcSetGrid
        self.setGridSize(2, 2)
        self.blankGrid()
        self.finshed = 0

    def uniqueName(self, idStr):
        return self.parent.getUniqueName(idStr)

    def delete(self):
        del self.funcSuccess
        del self.funcFail
        del self.funcSendGrid
        del self.funcSetGrid
        del self.parent

    def setGridSize(self, x, y):
        self.gridNumX = x
        self.gridNumY = y

    def blankGrid(self):
        self.gridData = []
        for i in range(0, self.gridNumX):
            self.gridData.append([
                0] * self.gridNumY)

    def win(self):
        if not self.finshed:
            self.finshed = 1
            self.funcSuccess()

    def lose(self):
        if not self.finshed:
            self.finshed = 1
            self.funcFail()

    def startGrid(self):
        self.blankGrid()

    def hit(self, hitX, hitY, oldx = -1, oldy = -1):
        if self.finshed:
            return

        if self.checkForWin():
            self.win()
        else:
            self.funcSendGrid()

    def checkForWin(self):
        return 0
