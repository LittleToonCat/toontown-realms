from otp.speedchat.SCTerminal import SCTerminal

from toontown.toonbase import TTLocalizer


TTSCMagicWordAddEvent = 'TTSCMagicWordAdd'


class TTSCMagicWordAddTerminal(SCTerminal):

    def __init__(self):
        SCTerminal.__init__(self)
        self.text = TTLocalizer.MagicWordSpeedchatAdd

    def isWhisperable(self):
        return False

    def handleSelect(self, displayType=0):
        SCTerminal.handleSelect(self, displayType)
        messenger.send(self.getEventName(TTSCMagicWordAddEvent))
