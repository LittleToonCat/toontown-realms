from direct.directnotify import DirectNotifyGlobal

from toontown.safezone import Walk
from toontown.toonbase import ToontownGlobals

class InstancedGameWalk(Walk.Walk):
    notify = DirectNotifyGlobal.directNotify.newCategory('InstancedGameWalk')

    def __init__(self, parentFSM, doneEvent):
        super().__init__(doneEvent)
        self.parentFSM = parentFSM

    def load(self):
        super().load()

    def unload(self):
        super().unload()
        del self.parentFSM

    def enter(self, slowWalk = 0):
        super().enter(slowWalk)

        base.localAvatar.disableSleeping()
        base.localAvatar.setPiePosType(ToontownGlobals.PIE_BTN_POS_INSTANCE)
        base.localAvatar.beginAllowPies()

    def exit(self):
        super().exit()

        base.localAvatar.enableSleeping()
        base.localAvatar.setPiePosType(ToontownGlobals.PIE_BTN_POS_NORMAL)
        base.localAvatar.endAllowPies()