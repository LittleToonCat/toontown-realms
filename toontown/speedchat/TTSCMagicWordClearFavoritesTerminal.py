from otp.speedchat.SCTerminal import SCTerminal

from toontown.toonbase import TTLocalizer


TTSCMagicWordClearFavoritesEvent = 'TTSCMagicWordClearFavorites'


class TTSCMagicWordClearFavoritesTerminal(SCTerminal):

    def __init__(self):
        SCTerminal.__init__(self)
        self.text = TTLocalizer.MagicWordSpeedchatClearFavorites

    def isWhisperable(self):
        return False

    def handleSelect(self, displayType=0):
        SCTerminal.handleSelect(self, displayType)
        messenger.send(self.getEventName(TTSCMagicWordClearFavoritesEvent))
