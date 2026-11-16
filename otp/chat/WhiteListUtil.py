from panda3d.core import ConfigVariableInt

from toontown.toonbase import ServerSettings
from .WhiteListGlobals import DefaultWhitelist

# Whitelist Modes
WHITELIST_OG = 0
WHITELIST_CUSTOM = 1
WHITELIST_BOTH = 2


def getCustomWhitelist():
    try:
        customList = base.cr.customWhitelist
    except (NameError, AttributeError):
        # This only runs on UD so we can do this
        customList = []
    return customList


def getWhitelistMode():
    try:
        mode = base.cr.whiteListMode
    except (NameError, AttributeError):
        mode = ConfigVariableInt('chat-whitelist-mode').getValue()
    return mode


def getDefaultWhitelist():
    return DefaultWhitelist


def getWholeWhitelist():
    return getDefaultWhitelist() + getCustomWhitelist()
