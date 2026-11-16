from panda3d.core import TextNode

from direct.gui.DirectGui import DirectFrame, DirectWaitBar, DirectLabel, DGG
from direct.directnotify.DirectNotifyGlobal import directNotify

DefaultHeight = 0.25
DefaultWidth = 1.0
DefaultTitleColor = (1.0, 1.0, 1.0, 1.0)


class BarChart(DirectFrame):
    notify = directNotify.newCategory('BarChart')

    def __init__(self, data, height=None, width=None, name='', titleColor=None, maxValue=None):
        self.width = DefaultWidth if width is None else width
        self.height = DefaultHeight if height is None else height
        self.barHeight = self.height / len(data) * 0.666
        self.titleColor = DefaultTitleColor if titleColor is None else titleColor
        self.maxValue = maxValue
        self.data = data
        self.name = name
        self.statBars = []

        DirectFrame.__init__(self, relief=None, state=DGG.NORMAL)
        self.initialiseoptions(BarChart)

        self.title = DirectFrame(parent=self, relief=None, text=self.name, text_align=TextNode.ALeft, text_scale=0.04,
                                 text_pos=(0.03, 0.01), text_fg=self.titleColor, text_shadow=(0, 0, 0, 1),
                                 textMayChange=1, pos=(0, 0, self.height + 0.02))

        self.loadStatBars(self.data)

    def loadStatBars(self, data):
        for item in data:
            self.addBar(item, repack=False)

        # Wait until all bars have been added to repack
        # it's faster for processing time
        self.repackBars()

    def addBar(self, data, repack=True):
        """
        Creates a new bar.

        :param data: A list with 3 elements - index 0 being a text string, 1 being the value, and 2 being the range.
        :param repack: Boolean whether to repack bars or not.
        """

        self.notify.debug('addBar({} {})'.format(data, repack))

        if self.maxValue:
            rangeVal = self.maxValue
        else:
            rangeVal = data[2]

        meter = DirectWaitBar(parent=self, relief=DGG.RAISED, borderWidth=(0.004, 0.004), range=rangeVal, value=data[1],
                              frameColor=(0, 0, 0, 0), barColor=(0.1, 0.7, 0.1, 1), text=str(data[1]), pos=(0, 0, 0),
                              frameSize=(0.17, self.width - 0.1, -self.barHeight * 0.25, self.barHeight * 0.75),
                              text_align=TextNode.ALeft, text_scale=0.03, text_fg=(1, 1, 1, 1), text_pos=(0, 0),
                              text_shadow=(0, 0, 0, 1))

        meterWidth = meter['frameSize'][1] - meter['frameSize'][0]
        percentFilled = float(meter['value']) / float(meter['range'])
        newTextPos = meterWidth * percentFilled + 0.18
        meter['text_pos'] = (newTextPos, 0)
        label = DirectLabel(parent=meter, relief=None, text=data[0], text_scale=0.03, text_align=TextNode.ALeft,
                            text_pos=(0, 0), text_fg=(1, 1, 1, 1))
        self.statBars.append([meter, label])

        if repack:
            self.repackBars()

    def clearAllBars(self):
        for i in range(len(self.statBars)):
            self.statBars[i][0].destroy()

        self.statBars = []

    def repackBars(self):
        for i in range(len(self.statBars)):
            self.statBars[i][0].setPos(0, 0, self.height + 0.02 - (i + 1) * (self.height - 0.02) / len(self.statBars))

    def refreshBars(self, data):
        """
        Update graph with new data.

        :param data: A list of items, each with 3 elements - index 0 being a text string, 1 being the value, and 2 being the range.
        """

        self.notify.debug('refreshBars({})'.format(data))

        for statBar, datum in zip(self.statBars, data):
            meter = statBar[0]
            label = statBar[1]
            label['text'] = datum[0]
            meter['text'] = str(datum[1])
            meter['value'] = datum[1]

            if self.maxValue:
                meter['range'] = self.maxValue
            else:
                meter['range'] = datum[2]

            meterWidth = meter['frameSize'][1] - meter['frameSize'][0]
            percentFilled = min(1.0, float(meter['value']) / float(meter['range']))
            newTextPos = meterWidth * percentFilled + 0.18
            meter['text_pos'] = (newTextPos, 0)

    def destroy(self):
        self.clearAllBars()
        DirectFrame.destroy(self)
