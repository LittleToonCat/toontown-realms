""" replacement of direct.controls.swimwalker to support strafing"""

from direct.showbase.InputStateGlobal import inputState
from direct.directnotify import DirectNotifyGlobal
from direct.controls import NonPhysicsWalker


class SwimWalker(NonPhysicsWalker.NonPhysicsWalker):
    notify = DirectNotifyGlobal.directNotify.newCategory("SwimWalker")

    def _calcSpeeds(self):
        # get the button states:
        forward = inputState.isSet("forward")
        reverse = inputState.isSet("reverse")
        turnLeft = inputState.isSet("turnLeft")
        turnRight = inputState.isSet("turnRight")
        slideLeft = inputState.isSet("slideLeft")
        slideRight = inputState.isSet("slideRight")

        # Check for Auto-Run
        if base.localAvatar.getAutoRun():
            forward = 1
            reverse = 0

        # Determine what the speeds are based on the buttons:
        self.speed = (forward and self.avatarControlForwardSpeed or
                      reverse and -self.avatarControlReverseSpeed)
        self.slideSpeed = (
                (slideLeft and -self.avatarControlReverseSpeed) or
                (slideRight and self.avatarControlReverseSpeed))
        self.rotationSpeed = (
                (turnLeft and self.avatarControlRotateSpeed) or
                (turnRight and -self.avatarControlRotateSpeed))
