from panda3d.core import TextNode
from direct.gui.DirectGui import DirectFrame, DirectLabel
from direct.interval.IntervalGlobal import Func, Sequence, Wait
from toontown.toonbase import ToontownGlobals, ServerTime


class ServerTimeGui(ServerTime.ServerTime, DirectFrame):
    def __init__(self, parent, pos=(0, 0, 0), hourCallback=None):
        DirectFrame.__init__(self, parent=parent, pos=pos)
        ServerTime.ServerTime.__init__(self, hourCallback)

    def setup(self):
        textScale = 0.075
        timeFont = ToontownGlobals.getMinnieFont()
        self.hourLabel = DirectLabel(parent=self, pos=(-0.015, 0, 0), relief=None, text='', text_scale=textScale,
                                     text_align=TextNode.ARight, text_font=timeFont)
        self.colonLabel = DirectLabel(parent=self, relief=None, text=':', text_scale=textScale,
                                      text_align=TextNode.ACenter, text_font=timeFont)
        self.minutesLabel = DirectLabel(relief=None, parent=self, pos=(0.015, 0, 0), text='', text_scale=textScale,
                                        text_align=TextNode.ALeft, text_font=timeFont)
        self.amLabel = DirectLabel(relief=None, parent=self, pos=(0.14, 0, 0), text='', text_scale=textScale,
                                   text_align=TextNode.ALeft, text_font=timeFont)
        ServerTime.ServerTime.setup(self)

    def _createIval(self):
        return Sequence(Func(self.colonLabel.show), Wait(0.75), Func(self.colonLabel.hide), Wait(0.25),
                        Func(self.updateTime))

    def destroy(self):
        # Give option to call destroy() as that's customary for DirectGui classes
        self.cleanup()

    def cleanup(self):
        ServerTime.ServerTime.cleanup(self)
        DirectFrame.destroy(self)

    def updateTime(self):
        curServerDate = ServerTime.ServerTime.updateTime(self)
        if not curServerDate.minute == self.lastMinute:
            self.hourLabel['text'] = curServerDate.strftime('%I')
            self.lastHour = curServerDate.hour
            if self.hourLabel['text'][0] == '0':
                self.hourLabel['text'] = self.hourLabel['text'][1:]
            self.minutesLabel['text'] = curServerDate.strftime('%M')
            self.amLabel['text'] = curServerDate.strftime('%p')