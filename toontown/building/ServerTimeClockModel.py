from panda3d.core import NodePath
from toontown.toonbase import ServerTime
from direct.interval.IntervalGlobal import Func, Sequence, Wait


class ServerTimeClockModel(ServerTime.ServerTime, NodePath):
    def __init__(self, hourCallback=None, modelStr='phase_7/models/props/clock'):
        NodePath.__init__(self, 'clockNode')

        self.modelStr = modelStr

        ServerTime.ServerTime.__init__(self, hourCallback)

    def setup(self):
        self.clockModel = loader.loadModel(self.modelStr)
        self.clockModel.reparentTo(self)
        ServerTime.ServerTime.setup(self)

    def _createIval(self):
        return Sequence(Func(self.updateTime), Wait(1.0))

    def cleanup(self):
        ServerTime.ServerTime.cleanup(self)

        del self.clockModel
        del self.modelStr

        self.removeNode()

    def updateTime(self):
        curServerDate = ServerTime.ServerTime.updateTime(self)

        # Modulus operation is to show in increments of 12
        hour = curServerDate.hour % 12
        minute = curServerDate.minute
        second = curServerDate.second

        minuteHand = self.clockModel.find('**/minute_hand')
        hourHand = self.clockModel.find('**/hour_hand')
        secondHand = self.clockModel.find('**/second_hand')

        # The default model, the cog bldg clock, doesn't have a second hand
        # so we're just going to assume that not all models will have every hand
        if not hourHand.isEmpty():
            hourHand.setHpr(0, 0, -hour * 30 - (minute / 60.0) * 30)
        if not minuteHand.isEmpty():
            minuteHand.setHpr(0, 0, -minute * 6.05)
        if not secondHand.isEmpty():
            secondHand.setHpr(0, 0, -second * 6.05)