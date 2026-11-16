from panda3d.core import *
from toontown.toonbase.ToontownGlobals import *
from direct.directnotify import DirectNotifyGlobal
from . import Walk
from ..toonbase import HotkeySettings


class PublicWalk(Walk.Walk):
    notify = DirectNotifyGlobal.directNotify.newCategory('PublicWalk')

    def __init__(self, parentFSM, doneEvent):
        Walk.Walk.__init__(self, doneEvent)
        self.parentFSM = parentFSM

    def unload(self):
        Walk.Walk.unload(self)
        del self.parentFSM

    def enter(self, slowWalk = 0):
        Walk.Walk.enter(self, slowWalk)
        base.localAvatar.book.showButton()
        self.accept(HotkeySettings.ToggleBook.getPressed(), self.__handleStickerBookEntry)
        self.accept('enterStickerBook', self.__handleStickerBookEntry)
        self.accept(HotkeySettings.ExitActivity.getPressed(), self.__handleOptionsEntry)
        base.localAvatar.laffMeter.start()
        base.localAvatar.beginAllowPies()

    def exit(self):
        Walk.Walk.exit(self)
        base.localAvatar.book.hideButton()
        self.ignore(HotkeySettings.ToggleBook.getPressed())
        self.ignore('enterStickerBook')
        self.ignore(HotkeySettings.ExitActivity.getPressed())
        base.localAvatar.laffMeter.stop()
        base.localAvatar.endAllowPies()

    def __handleStickerBookEntry(self):
        currentState = base.localAvatar.animFSM.getCurrentState().getName()
        if currentState == 'jumpAirborne':
            return
        if base.localAvatar.book.isObscured():
            return
        else:
            doneStatus = {}
            doneStatus['mode'] = 'StickerBook'
            messenger.send(self.doneEvent, [doneStatus])

    def __handleOptionsEntry(self):
        currentState = base.localAvatar.animFSM.getCurrentState().getName()
        if currentState == 'jumpAirborne':
            return
        if base.localAvatar.book.isObscured():
            return
        else:
            doneStatus = {}
            doneStatus['mode'] = 'Options'
            messenger.send(self.doneEvent, [doneStatus])

    def toggleBook(self, state):
        if state == 'disable':
            self.ignore(HotkeySettings.ToggleBook.getPressed())
            self.ignore('enterStickerBook')
            self.ignore(HotkeySettings.ExitActivity.getPressed())
        elif state == 'enable':
            self.accept(HotkeySettings.ToggleBook.getPressed(), self.__handleStickerBookEntry)
            self.accept('enterStickerBook', self.__handleStickerBookEntry)
            self.accept(HotkeySettings.ExitActivity.getPressed(), self.__handleOptionsEntry)
