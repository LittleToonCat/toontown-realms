from otp.speedchat.SCTerminal import SCTerminal

from toontown.toonbase import TTLocalizer


TTSCMagicWordRemoveEvent = 'TTSCMagicWordRemove'


class TTSCMagicWordRemoveTerminal(SCTerminal):

    def __init__(self):
        SCTerminal.__init__(self)
        self.text = TTLocalizer.MagicWordSpeedchatRemoveAll

    def isWhisperable(self):
        return False

    def handleSelect(self, displayType=0):
        SCTerminal.handleSelect(self, displayType)
        messenger.send(self.getEventName(TTSCMagicWordRemoveEvent))
