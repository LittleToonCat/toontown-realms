from direct.controls import ControlManager
from typing import Dict

from direct.controls.InputState import InputStateToken
from direct.showbase.InputStateGlobal import inputState

from toontown.toonbase import HotkeySettings


class OTPControlManager(ControlManager.ControlManager):

    def __init__(self, enable = True):
        assert self.notify.debugCall(id(self))
        self.inputStateTokens: Dict[str, InputStateToken] = {}
        self.controls = {}
        self.currentControls = None
        self.currentControlsName = None
        self.isEnabled = False
        if enable:
            self.enable()
        self.forceAvJumpToken = None

    def enable(self):
        assert self.notify.debugCall(id(self))

        if self.isEnabled:
            assert self.notify.debug('already isEnabled')
            return

        self.isEnabled = True

        self.inputStateTokens['forward'] = inputState.watch(
            "forward",
            HotkeySettings.MoveForward.getPressed(),
            HotkeySettings.MoveForward.getReleased(),
            inputSource = 'OTPControls')
        self.inputStateTokens['reverse'] = inputState.watch(
            "reverse",
            HotkeySettings.MoveBackward.getPressed(),
            HotkeySettings.MoveBackward.getReleased(),
            inputSource = 'OTPControls')

        self.inputStateTokens['turnLeft'] = inputState.watch(
            "turnLeft",
            HotkeySettings.MoveLeft.getPressed(),
            HotkeySettings.MoveLeft.getReleased(),
            inputSource = 'OTPControls')
        self.inputStateTokens['turnRight'] = inputState.watch(
            "turnRight",
            HotkeySettings.MoveRight.getPressed(),
            HotkeySettings.MoveRight.getReleased(),
            inputSource = 'OTPControls')

        self.inputStateTokens['jump'] = inputState.watch(
            "jump",
            HotkeySettings.Jump.getPressed(),
            HotkeySettings.Jump.getReleased(),
            inputSource = 'OTPControls')

        self.inputStateTokens['descend'] = inputState.watch(
            'descend',
            HotkeySettings.FlyDescend.getPressed(),
            HotkeySettings.FlyDescend.getReleased(),
            inputSource = 'OTPControls'
        )

        if self.currentControls:
            self.currentControls.enableAvatarControls()

    def setStrafing(self, wantStrafe):
        """
        Toggles strafing
        Changes whether the left and right keys should rotate or strafe
        :type wantStrafe bool
        """
        if not self.isEnabled:
            return
        # Store the currently pressed state to seamlessly transition
        turnLeftSet = inputState.isSet("turnLeft", inputSource = 'OTPControls')
        turnRightSet = inputState.isSet("turnRight", inputSource = 'OTPControls')
        slideLeftSet = inputState.isSet("slideLeft", inputSource = 'OTPControls')
        slideRightSet = inputState.isSet("slideRight", inputSource = 'OTPControls')

        # Release the current tokens
        if 'turnLeft' in self.inputStateTokens:
            self.inputStateTokens['turnLeft'].release()
            del self.inputStateTokens['turnLeft']

        if 'turnRight' in self.inputStateTokens:
            self.inputStateTokens['turnRight'].release()
            del self.inputStateTokens['turnRight']

        if 'slideLeft' in self.inputStateTokens:
            self.inputStateTokens['slideLeft'].release()
            del self.inputStateTokens['slideLeft']

        if 'slideRight' in self.inputStateTokens:
            self.inputStateTokens['slideRight'].release()
            del self.inputStateTokens['slideRight']

        if wantStrafe:
            self.inputStateTokens['slideLeft'] = inputState.watch(
                "slideLeft",
                HotkeySettings.MoveLeft.getPressed(),
                HotkeySettings.MoveLeft.getReleased(),
                inputSource = 'OTPControls')
            self.inputStateTokens['slideRight'] = inputState.watch(
                "slideRight",
                HotkeySettings.MoveRight.getPressed(),
                HotkeySettings.MoveRight.getReleased(),
                inputSource = 'OTPControls')

            # If we were turning when we switched to strafing, we can seamlessly transition that to
            # strafing if we're still holding it down
            inputState.set("slideLeft", turnLeftSet, inputSource = 'OTPControls')
            inputState.set("slideRight", turnRightSet, inputSource = 'OTPControls')

            # Stop the toon from turning
            inputState.set("turnLeft", False, inputSource = 'OTPControls')
            inputState.set("turnRight", False, inputSource = 'OTPControls')

        else:
            self.inputStateTokens['turnLeft'] = inputState.watch(
                "turnLeft",
                HotkeySettings.MoveLeft.getPressed(),
                HotkeySettings.MoveLeft.getReleased(),
                inputSource = 'OTPControls')
            self.inputStateTokens['turnRight'] = inputState.watch(
                "turnRight",
                HotkeySettings.MoveRight.getPressed(),
                HotkeySettings.MoveRight.getReleased(),
                inputSource = 'OTPControls')
            # If we were strafing when we switched to turning, we can seamlessly transition that to
            # turning if we're still holding it down
            inputState.set("turnLeft", slideLeftSet, inputSource = 'OTPControls')
            inputState.set("turnRight", slideRightSet, inputSource = 'OTPControls')

            # Stop the toon from strafing
            inputState.set("slideLeft", False, inputSource = 'OTPControls')
            inputState.set("slideRight", False, inputSource = 'OTPControls')

    def addToken(self, tokenName, token):
        self.inputStateTokens[tokenName] = token

    def releaseToken(self, tokenName):
        if tokenName in self.inputStateTokens.keys():
            self.inputStateTokens[tokenName].release()
            del self.inputStateTokens[tokenName]

    def disable(self):
        assert self.notify.debugCall(id(self))
        self.isEnabled = False

        for tokenName in self.inputStateTokens.keys():
            inputState.set(tokenName, False, inputSource = 'OTPControls')

        for token in list(self.inputStateTokens.values()):
            token.release()
        self.inputStateTokens: Dict[str, InputStateToken] = {}

        if self.currentControls:
            self.currentControls.disableAvatarControls()

    def delete(self):
        assert self.notify.debugCall(id(self))
        self.disable()
        for controls in list(self.controls.keys()):
            self.remove(controls)
        del self.controls
        del self.currentControls
        del self.inputStateTokens
