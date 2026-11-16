from otp.speedchat.SCMenu import SCMenu
from toontown.toonbase.ToontownTypes import CogQuoteIndex

from .TTSCCogTerminal import TTSCCogTerminal

class TTSCCogMenu(SCMenu):

    def __init__(self, cogType):
        SCMenu.__init__(self)

        brushOffs = base.cr.dataPackMgr.getCogQuotesByType(cogType, CogQuoteIndex.BRUSH_OFFS)
        faceoffTaunts = base.cr.dataPackMgr.getCogQuotesByType(cogType, CogQuoteIndex.FACEOFF_TAUNTS)
        for i in range(len(brushOffs)):
            phrase = brushOffs[i]
            self.append(TTSCCogTerminal(phrase, cogType, CogQuoteIndex.BRUSH_OFFS, i))
        for i in range(len(faceoffTaunts)):
            phrase = faceoffTaunts[i]
            self.append(TTSCCogTerminal(phrase, cogType, CogQuoteIndex.FACEOFF_TAUNTS, i))

    def destroy(self):
        SCMenu.destroy(self)
