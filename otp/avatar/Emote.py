from otp.otpbase import OTPLocalizer
import types

class Emote:
    EmoteClear = -1
    EmoteEnableStateChanged = 'EmoteEnableStateChanged'

    def __init__(self):
        self.emoteFunc = None
        return

    def isEnabled(self, index):
        if isinstance(index, bytes):
            index = OTPLocalizer.EmoteFuncDict[index]
        if not self.emoteFunc:
            return False
        elif self.emoteFunc[index][1]:
            return True
        return False


globalEmote = None
