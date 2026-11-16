from otp.speedchat.SCTerminal import SCTerminal

from toontown.toonbase import TTLocalizer


TTSCMagicWordEvent = 'TTSCMagicWord'


class TTSCMagicWordTerminal(SCTerminal):

    def __init__(self, text):
        SCTerminal.__init__(self)
        self.text = text

    def isWhisperable(self):
        return False

    def handleSelect(self, displayType=0):
        SCTerminal.handleSelect(self, displayType)
        messenger.send(TTSCMagicWordEvent, [self.text])
