from otp.speedchat.SCTerminal import SCTerminal
TTSCCogMsgEvent = 'TTSCCogEvent'


def decodeTTSCCogMsg(cogType: str, quoteTypeIndex: int, quoteIndex: int):
    quotes = base.cr.dataPackMgr.getCogQuotesByType(cogType, quoteTypeIndex)
    if quoteIndex > len(quotes) - 1:
        chatString = quotes[0]
    else:
        chatString = quotes[quoteIndex]

    return chatString


class TTSCCogTerminal(SCTerminal):

    def __init__(self, text: str, cogType: str, quoteTypeIndex: int, quoteIndex: int):
        SCTerminal.__init__(self)
        self.text = text
        self.cogType = cogType
        self.quoteTypeIndex = quoteTypeIndex
        self.quoteIndex = quoteIndex

    def handleSelect(self, displayType=0):
        SCTerminal.handleSelect(self, displayType)
        messenger.send(self.getEventName(TTSCCogMsgEvent), [self.cogType, self.quoteTypeIndex, self.quoteIndex, displayType])
