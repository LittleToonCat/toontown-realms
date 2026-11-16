from panda3d.core import TextNode, Vec2
from direct.gui.DirectButton import DirectButton, DGG
from direct.showbase.DirectObject import DirectObject
from toontown.toonbase import ToontownGlobals, TTLocalizer


class TTQTNode(DirectObject):
    font = ToontownGlobals.getToonFont()
    
    def __init__(self, name):
        DirectObject.__init__(self)
        self.name = name
        self.phraseList = []
        self.nodepath = hidden.attachNewNode('QTNode-' + name)
        self.buttons = []
        self.menu = None
        self.clearSelectionHandler()

    def __del__(self):
        self.deleteMenu()
        self.nodepath.removeNode()
        del self.nodepath

    def __findPhrasePair(self, key):
        phrasePair = None
        if isinstance(key, str):
            for pp in self.phraseList:
                if pp[0] == key:
                    phrasePair = pp
                    break
            
        elif key < len(self.phraseList):
            phrasePair = self.phraseList[key]
        
        return phrasePair

    def __getitem__(self, key):
        phrasePair = self.__findPhrasePair(key)
        if phrasePair:
            return phrasePair[1]

    def __setitem__(self, key, value):
        phrasePair = self.__findPhrasePair(key)
        if not phrasePair:
            self.phraseList.append([key, value])
        else:
            phrasePair[1] = value

    def getPhrase(self, index):
        pp = self.__findPhrasePair(index)
        if not pp:
            return ''
        else:
            return pp[0]

    def __createDisplayText(self, phrasePair):
        text = phrasePair[0]
        if phrasePair[1] != QTSend:
            text = text + TTLocalizer.QuickTalkerEllipse
        
        return text

    def __createButtonName(self, index):
        return 'QTMenu' + self.name + 'Button' + str(index)

    def createMenu(self):
        self.deleteMenu()

        z = 0
        dz = -0.065
        index = 0
        text = TextNode('widthCalculator')
        text.setFont(self.font)

        width = 0
        height = 0

        for pp in self.phraseList:
            dText = self.__createDisplayText(pp)
            text.setText(dText)
            bounds = text.getCardActual()
            newWidth = abs(bounds[1] - bounds[0]) + 0.25
            newHeight = abs(bounds[3] - bounds[2]) + 2.0 * 0.1
            if newWidth > width:
                width = newWidth
            if newHeight > height:
                height = newHeight

        for pp in self.phraseList:
            dText = self.__createDisplayText(pp)
            btn = DirectButton(parent=self.nodepath, relief=DGG.FLAT, guiId=self.__createButtonName(index), text=dText,
                               text_font=self.font, scale=0.055, text_align=TextNode.ACenter,
                               pos=(0, 0, z), pressEffect=0, frameSize=(0, width, -height, 0))
            btn['text_pos'] = Vec2(btn.getCenter()) - Vec2(0, 0.25)
            self.resetButtonFrameColor(btn)
            btn.bind(DGG.B1PRESS, self.__btnDown, extraArgs=[btn])
            btn.bind(DGG.B1RELEASE, self.__btnUp, extraArgs=[btn, index])
            self.buttons.append(btn)
            z = z + dz
            index = index + 1

    def resetButtonFrameColor(self, btn):
        frameColor = [(.8, .8, .8, 0.9)] * 3
        frameColor.insert(DGG.BUTTON_ROLLOVER_STATE, (1, 1, 0, 1))
        btn['frameColor'] = frameColor

    def deleteMenu(self):
        for button in self.buttons:
            button.destroy()
        self.buttons = []

    def setSelectionHandler(self, handler):
        self.selectionHandler = handler

    def clearSelectionHandler(self):
        self.setSelectionHandler(None)

    def __owns(self, item):
        return item in self.buttons

    def __buttonPressed(self, item, index):
        if self.__owns(item):
            if self.selectionHandler:
                self.selectionHandler(index)

    def __btnDown(self, btn, event):
        btn['text_fg'] = (1.0, 1.0, 1.0, 1.0)
        btn['frameColor'] = (0, 0, 0, 1.0)

    def __btnUp(self, btn, index, event):
        btn['text_fg'] = (0, 0, 0, 1)
        self.resetButtonFrameColor(btn)
        self.__buttonPressed(btn, index)


QTSend = TTQTNode('send')
