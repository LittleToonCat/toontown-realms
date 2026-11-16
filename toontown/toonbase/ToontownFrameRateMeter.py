from panda3d.core import TextNode

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.fsm.StateData import StateData
from direct.gui.DirectGui import OnscreenText

from toontown.toonbase import ToontownGlobals


class ToontownFrameRateMeter(StateData):
    """A replacement for Panda's FrameRateMeter that allows colored text
    based on the current frame rate."""

    notify = directNotify.newCategory('ToontownFrameRateMeter')

    MED_THRESHOLD = 45
    LOW_THRESHOLD = 30

    TASK_NAME = 'fpsMeterTask'

    METER_TEXT = '{} FPS'

    def __init__(self, base):
        self.base = base
        StateData.__init__(self, None)

    def load(self):
        self.meter = OnscreenText(parent=base.a2dTopRight, text='', pos=(-0.01, -0.05, 0.0),
                                  scale=0.05, style=3, bg=(0.15, 0.075, 0.25, 0.5), align=TextNode.ARight,
                                  fg = (0.95, 0.95, 0.95, 1), font=ToontownGlobals.getToonFont())
        self.meter.hide()

        return StateData.load(self)

    def enter(self):
        self.meter.show()
        self.addTask(self.__updateMeter, self.TASK_NAME)
        return StateData.enter(self)

    def __updateMeter(self, task):
        if not self.isEntered:
            return task.done

        fps = globalClock.getAverageFrameRate()

        text = self.METER_TEXT.format(round(fps, 1))

        self.meter.setText(text)

        return task.cont

    def exit(self):
        self.meter.hide()
        self.removeTask(self.TASK_NAME)
        return StateData.exit(self)

    def unload(self):
        self.removeTask(self.TASK_NAME)
        self.meter.destroy()
        del self.meter
        return StateData.unload(self)

    def clearWindow(self):
        # This needs to exist because ShowBase calls this
        # method on a FrameRateMeter when closing the window
        self.unload()

