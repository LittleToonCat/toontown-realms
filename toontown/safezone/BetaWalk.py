"""BetaWalk module: contains the BetaWalk class"""

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.fsm import State
from .PublicWalk import PublicWalk
from otp.avatar import Emote
from toontown.toonbase import ToontownGlobals, HotkeySettings


class BetaWalk(PublicWalk):
    """This replaces the normal walk speed with the older, pre-2012 walk speed,
    as well as the classic jump before the GravityWalker was implemented.
    Part of the authentic beta experience."""
    notify = directNotify.newCategory('BetaWalk')

    def __init__(self, parentFSM, doneEvent):
        PublicWalk.__init__(self, parentFSM, doneEvent)
        self.fsm.addState(State.State('jumping', self.enterJumping, self.exitJumping, ['walking', 'swimming']))
        state = self.fsm.getStateNamed('off')
        state.addTransition('jumping')
        state = self.fsm.getStateNamed('walking')
        state.addTransition('jumping')

    def enter(self, slowWalk=0):
        PublicWalk.enter(self, slowWalk)
        base.localAvatar.disableJump()
        self.accept(HotkeySettings.Jump.getPressed(), self.__handleJumpKey)

    def exit(self):
        self.ignore(HotkeySettings.Jump.getPressed())
        base.localAvatar.enableJump()
        PublicWalk.exit(self)

    def enterWalking(self):
        if base.localAvatar.hp > 0:
            base.localAvatar.startTrackAnimToSpeed()
            base.localAvatar.setWalkSpeedOld()
        else:
            self.fsm.request('slowWalking')

    def enterSwimming(self, swimSound):
        base.localAvatar.setWalkSpeedOld()
        self.swimSound = swimSound
        self.swimSoundPlaying = 0
        base.localAvatar.b_setAnimState('swim', base.localAvatar.animMultiplier)
        base.localAvatar.startSleepSwimTest()
        taskMgr.add(self._swim, 'localToonSwimming')

    def __handleJumpKey(self):
        state = self.fsm.getCurrentState().getName()
        if state == 'walking':
            self.fsm.request('jumping')

    def enterJumping(self):
        Emote.globalEmote.disableBody(base.localAvatar, 'BetaWalk, enterJumping')
        base.localAvatar.stopTrackAnimToSpeed()
        base.localAvatar.b_setAnimState('jump', 1.0)
        base.localAvatar.wakeUp()

        def returnToWalk(task):
            self.fsm.request('walking')
            return task.done

        jumpTime = base.localAvatar.getJumpDuration()
        taskMgr.doMethodLater(jumpTime, returnToWalk, base.localAvatar.uniqueName('walkReturnTask'))

    def exitJumping(self):
        taskMgr.remove(base.localAvatar.uniqueName('walkReturnTask'))
        Emote.globalEmote.releaseBody(base.localAvatar, 'BetaWalk, exitJumping')
