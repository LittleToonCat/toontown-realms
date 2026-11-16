from direct.showbase import PythonUtil

from otp.speedchat.SCMenu import SCMenu
from otp.speedchat.SCMenuHolder import SCMenuHolder

from .TTSCMagicWordTerminal import TTSCMagicWordTerminal
from .TTSCMagicWordAddTerminal import TTSCMagicWordAddTerminal
from .TTSCMagicWordRemoveTerminal import TTSCMagicWordRemoveTerminal
from .TTSCMagicWordClearRecentTerminal import TTSCMagicWordClearRecentTerminal
from .TTSCMagicWordClearFavoritesTerminal import TTSCMagicWordClearFavoritesTerminal

from toontown.toonbase import TTLocalizer


MAGIC_WORDS_COMMANDS = 0
MAGIC_WORDS_RECENT = 1
MAGIC_WORDS_FAVORITES = 2
MAGIC_WORDS_MENUS = {MAGIC_WORDS_COMMANDS: TTLocalizer.MagicWordSpeedchatMenuCommands,
                     MAGIC_WORDS_RECENT: TTLocalizer.MagicWordSpeedchatMenuRecent,
                     MAGIC_WORDS_FAVORITES: TTLocalizer.MagicWordSpeedchatMenuFavorites}


class TTSCMagicWordsMenu(SCMenu):

    def __init__(self):
        SCMenu.__init__(self)
        self.accept('magicWordsChanged', self.__magicWordsChanged)
        self.__magicWordsChanged()

    def destroy(self):
        SCMenu.destroy(self)

    def clearMenu(self):
        SCMenu.clearMenu(self)

    def __magicWordsChanged(self):
        if not hasattr(base.cr, 'magicWordManager') or not base.cr.magicWordManager:
            return

        # Reset the menu
        self.clearMenu()

        # Gather our recent words
        recentWords = base.cr.magicWordManager.getRecentWords()

        # Gather our favorite words
        favoriteWords = base.cr.magicWordManager.getFavoriteWords()

        # Iterate over all of the submenus we want
        for menuIndex in list(MAGIC_WORDS_MENUS.keys()):
            # Create a blank menu
            menu = SCMenu()

            # If we're the commands menu, we get some special command terminals to use
            if menuIndex == MAGIC_WORDS_COMMANDS:
                menu.append(TTSCMagicWordAddTerminal())
                menu.append(TTSCMagicWordRemoveTerminal())
                menu.append(TTSCMagicWordClearRecentTerminal())
                menu.append(TTSCMagicWordClearFavoritesTerminal())

            # For the recent menu, add our recently used Magic Words
            if menuIndex == MAGIC_WORDS_RECENT:
                for word in recentWords:
                    menu.append(TTSCMagicWordTerminal(word))

            # And if we're the favorites menu, add our favorite Magic Words
            if menuIndex == MAGIC_WORDS_FAVORITES:
                for word in favoriteWords:
                    menu.append(TTSCMagicWordTerminal(word))

            menuName = MAGIC_WORDS_MENUS.get(menuIndex)
            self.append(SCMenuHolder(menuName, menu))

        # Gather our saved phrases and append them
        savedWords = base.cr.magicWordManager.getSavedWords()
        for word in savedWords:
            self.append(TTSCMagicWordTerminal(word))

        # Reload all our saved Magic Words from settings, and then add them
        return
