from otp.speedchat.SCTerminal import SCTerminal

from toontown.toonbase import TTLocalizer


TTSCMagicWordClearRecentEvent = 'TTSCMagicWordClearRecent'


class TTSCMagicWordClearRecentTerminal(SCTerminal):

    def __init__(self):
        SCTerminal.__init__(self)
        self.text = TTLocalizer.MagicWordSpeedchatClearRecent

    def isWhisperable(self):
        return False

    def handleSelect(self, displayType=0):
        SCTerminal.handleSelect(self, displayType)
        messenger.send(self.getEventName(TTSCMagicWordClearRecentEvent))
