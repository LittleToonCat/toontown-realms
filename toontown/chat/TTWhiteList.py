from direct.directnotify import DirectNotifyGlobal
from otp.chat.WhiteList import WhiteList
from otp.chat import WhiteListUtil
from toontown.toonbase import TTLocalizer


class TTWhiteList(WhiteList):
    notify = DirectNotifyGlobal.directNotify.newCategory('TTWhiteList')

    def __init__(self):
        """
        mode = WhiteListUtil.getWhitelistMode()
        if mode == WhiteListUtil.WHITELIST_OG:
            words = WhiteListUtil.getDefaultWhitelist()
        elif mode == WhiteListUtil.WHITELIST_CUSTOM:
            words = WhiteListUtil.getCustomWhitelist()
        elif mode == WhiteListUtil.WHITELIST_BOTH:
            words = WhiteListUtil.getWholeWhitelist()
        else:
            self.notify.error('Invalid whitelist mode %d! Valid modes are %d - %d.' % (mode, WhiteListUtil.WHITELIST_OG, WhiteListUtil.WHITELIST_BOTH))
        """
        WhiteList.__init__(self, WhiteListUtil.getDefaultWhitelist())

        self.defaultWord = TTLocalizer.ChatGarblerDefault[0]
