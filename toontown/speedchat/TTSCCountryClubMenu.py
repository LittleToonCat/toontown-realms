from otp.speedchat.SCMenu import SCMenu
from otp.speedchat.SCStaticTextTerminal import SCStaticTextTerminal

GLOBAL_MSGS = (1700,
 1701,
 1702,
 1703,
 1704,
 6000,
 6001,
 6002)

class TTSCCountryClubMenu(SCMenu):

    def __init__(self):
        SCMenu.__init__(self)
        try:
            lt = base.localAvatar
        except:
            return

        for msg in GLOBAL_MSGS:
            self.append(SCStaticTextTerminal(msg))
