from panda3d.core import *
from direct.interval.IntervalGlobal import *
from direct.fsm import ClassicFSM, State
from direct.gui.DirectGui import *
from panda3d.toontown import NametagFloat2d, NametagFloat3d, CFSpeech
from toontown.char import CharDNA, Char
from toontown.toon import ToonHead
from toontown.toonbase import ToontownTimer, TTLocalizer
from toontown.toonbase.ToontownGlobals import getSignFont
from .DistributedMinigame import DistributedMinigame
from . import ArrowKeys, PatternPad, PatternGameGlobals


class DistributedPatternGameBeta(DistributedMinigame):
    textColor = (0.9, 0.9, 0.9, 1.0)
    bgColor = Vec4(0.01, 0.2, 0.01, 1.0)
    phase3snd = 'phase_3/audio/sfx/'
    phase4snd = 'phase_4/audio/sfx/'
    TEXT_POS_ABOVE = (0, 0.45)
    TEXT_POS_ON = (0, 0)
    TEXT_SCALE_BIG = 0.2
    TEXT_SCALE_NORMAL = 0.15
    TEXT_SCALE_SMALL = 0.12
    ButtonSoundNames = (phase4snd + 'MG_cannon_hit_tower.ogg', phase3snd + 'GUI_create_toon_back.ogg',
                        phase3snd + 'GUI_create_toon_bodyshop.ogg', phase4snd + 'SZ_trolley_bell.ogg')
    strWatch = TTLocalizer.PatternGameWatchBeta
    strTryAgain = TTLocalizer.PatternGameTryAgainBeta
    strGo = TTLocalizer.PatternGameGoBeta
    strRight = TTLocalizer.PatternGameRightBeta
    strWrong = TTLocalizer.PatternGameWrong
    strTimeUp = TTLocalizer.PatternGameTimeUpBeta
    strWin = TTLocalizer.PatternGameWinBeta
    strPerfect = TTLocalizer.PatternGamePerfectBeta
    strBye = TTLocalizer.PatternGameBye
    strWaitingOtherPlayers = TTLocalizer.PatternGameWaitingOtherPlayers
    strPleaseWait = TTLocalizer.PatternGamePleaseWait

    def __init__(self, cr):
        DistributedMinigame.__init__(self, cr)
        self.gameFSM = ClassicFSM.ClassicFSM('DistributedPatternGameBeta', [
            State.State('off', self.enterOff, self.exitOff, [
                'readyForNextRound']),
            State.State('readyForNextRound', self.enterReadyForNextRound, self.exitReadyForNextRound, [
                'waitForServerPattern']),
            State.State('waitForServerPattern', self.enterWaitForServerPattern, self.exitWaitForServerPattern, [
                'showServerPattern']),
            State.State('showServerPattern', self.enterShowServerPattern, self.exitShowServerPattern, [
                'getUserInput']),
            State.State('getUserInput', self.enterGetUserInput, self.exitGetUserInput, [
                'waitForGameOverFlag',
                'finish']),
            State.State('waitForGameOverFlag', self.enterWaitForGameOverFlag, self.exitWaitForGameOverFlag, [
                'readyForNextRound',
                'finish']),
            State.State('finish', self.enterFinish, self.exitFinish, [
                'off'])], 'off', 'off')
        self.addChildGameFSM(self.gameFSM)
        self.oldBgColor = None

    def getTitle(self):
        return TTLocalizer.PatternGameTitle

    def getInstructions(self):
        return TTLocalizer.PatternGameInstructionsBeta

    def generate(self):
        DistributedMinigame.generate(self)

    def disable(self):
        DistributedMinigame.disable(self)

    def load(self):
        DistributedMinigame.load(self)
        self.timer = ToontownTimer.ToontownTimer()
        self.timer.posInTopRightCorner()
        self.timer.hide()
        self.localPatternPad = PatternPad.PatternPad()
        self.localPatternPad.setPressCallback(self.__pressHandler)
        self.localPatternPad.setReleaseCallback(self.__releaseHandler)
        self.localPatternPad.hide()
        self.buttonSounds = []
        for i in range(0, 4):
            self.buttonSounds.append(loader.loadSfx(self.ButtonSoundNames[i]))

        self.correctSound = loader.loadSfx('phase_4/audio/sfx/MG_pos_buzzer.ogg')
        self.winSound = loader.loadSfx('phase_4/audio/sfx/MG_win_beta.ogg')
        self.loseSound = loader.loadSfx('phase_4/audio/sfx/MG_lose_beta.ogg')
        self.titleText = DirectLabel(text = self.getTitle(), text_fg = (0.9, 0.9, 0.9, 1.0), frameColor = (1, 1, 1, 0), text_font = getSignFont(), pos = (0, 0, 0.8), scale = 0.14)
        self.waitingText = DirectLabel(text = self.strPleaseWait, text_fg = (0.9, 0.9, 0.9, 1.0), frameColor = (1, 1, 1, 0), text_font = getSignFont(), pos = (0, 0, -0.483333), scale = 0.107502)
        self.roundText = DirectLabel(parent = self.localPatternPad, text = '1', text_fg = (0.9, 0.9, 0.9, 1.0), frameColor = (1, 1, 1, 0), text_font = getSignFont(), pos = (0, 0, -0.05), scale = 0.15)
        self.titleText.hide()
        self.waitingText.hide()
        self.roundText.hide()
        self.checkMark = DirectLabel(parent=hidden, text = TTLocalizer.OL.DialogOK, text_fg = (0, 1, 0, 1), frameColor = (1, 1, 1, 0), text_font = getSignFont(), pos = (0, 0, -0.15), scale = 0.45)
        self.xMark = DirectLabel(parent=hidden, text = 'X', text_fg = (1, 0, 0, 1), frameColor = (1, 1, 1, 0), text_font = getSignFont(), pos = (0, 0, -0.3), scale = 0.8)
        self.minnie = Char.Char()
        m = self.minnie
        dna = CharDNA.CharDNA()
        dna.newChar('mn')
        m.setDNA(dna)
        m.setName('Minnie')
        m.reparentTo(hidden)

    def unload(self):
        DistributedMinigame.unload(self)
        self.timer.destroy()
        del self.timer
        for i in range(0, 4):
            loader.unloadSfx(self.buttonSounds[i])

        del self.buttonSounds
        loader.unloadSfx(self.correctSound)
        loader.unloadSfx(self.winSound)
        loader.unloadSfx(self.loseSound)
        del self.correctSound
        del self.winSound
        del self.loseSound
        self.titleText.destroy()
        self.waitingText.destroy()
        self.roundText.destroy()
        del self.titleText
        del self.waitingText
        del self.roundText
        self.checkMark.destroy()
        self.xMark.destroy()
        del self.checkMark
        del self.xMark
        self.localPatternPad.destroy()
        del self.localPatternPad
        del self.minnie
        self.removeChildGameFSM(self.gameFSM)
        del self.gameFSM

    def onstage(self):
        DistributedMinigame.onstage(self)
        self.arrowKeys = ArrowKeys.ArrowKeys()
        self.oldBgColor = base.getBackgroundColor()
        base.setBackgroundColor(self.bgColor)
        self.titleText.show()
        pad = self.localPatternPad
        pad.show()
        pad.disable()
        pad.setScale(1.3)
        pad.setZ(0.15)
        self.remotePatternPads = {}
        for i in range(0, len(self.remoteAvIdList)):
            avId = self.remoteAvIdList[i]
            pad = PatternPad.PatternPad()
            pad.show()
            pad.disable()
            pad.setScale(0.4)
            padSpacing = 0.65
            pad.setPos(0.12 + i * padSpacing - (len(self.remoteAvIdList) - 1) * padSpacing / 2.0, 0, -0.7)
            self.remotePatternPads[avId] = pad

        self.checkMarks = []
        self.xMarks = []
        self.toonHeadDict = {}
        if self.isSinglePlayer():
            WD = 1.0
            HT = 0.32
            self.chancesLeftFrame = DirectFrame(parent = aspect2d, frameColor = (0.1, 0.1, 0.1, 1), frameSize = (-WD / 2.0, WD / 2.0, -HT / 2.0, HT / 2.0), pos = (0, 0, -0.8))
            self.chancesLeftFrame.show()
            self.chancesLeftSlots = []
            self.chancesLeftToonHeads = []
            self.chancesLeftXMarks = []
            xMark = OnscreenText(parent = hidden, text = 'X', font = getSignFont(), fg = (1, 0, 0, 1), scale = 0.3)
            for i in range(0, PatternGameGlobals.SP_NUM_CHANCES):
                head = ToonHead.ToonHead()
                head.setupHead(self.getAvatar(self.localAvId).style, forGui = 1)
                head.setY(10)
                head.setScale(0.14)
                head.setH(180)
                head.startBlink()
                self.chancesLeftToonHeads.append(head)
                slotSpacing = 0.3
                WD = 0.25
                HT = 0.28
                dummyNode = hidden.attachNewNode('patternGameNullGeomNode')
                slot = DirectLabel(parent = self.chancesLeftFrame, pos = (slotSpacing * (float(i) - float(PatternGameGlobals.SP_NUM_CHANCES - 1) / 2.0), 0, 0), frameColor = (1, 1, 1, 0), frameSize = (-WD / 2.0, WD / 2.0, -HT / 2.0, HT / 2.0), geom = (dummyNode, xMark), numStates = 2)
                head.reparentTo(slot.stateNodePath[0])
                dummyNode.removeNode()
                del dummyNode
                slot['geom1_pos'] = (0, 0, -0.1)
                self.chancesLeftSlots.append(slot)

        lt = base.localAvatar
        lt.reparentTo(camera)
        lt.setPos(-4.8, 12.96, -1.64)
        lt.lookAt(camera)
        lt.setP(0)
        lt.setR(0)
        lt.loop('neutral')
        m = self.minnie
        m.reparentTo(camera)
        m.setPos(4.7, 12.96, -1.64)
        m.lookAt(camera)
        m.setP(0)
        m.setR(0)
        m.loop('neutral')
        m.startBlink()
        self.minnie.nametag.manage(base.marginManager)
        self.minnie.setPickable(0)
        self.minnie.nametag.getNametag3d().setChatWordwrap(5)
        camera.reparentTo(render)
        base.setCellsAvailable(base.leftCells + base.rightCells + base.bottomCells, 0)

    def offstage(self):
        DistributedMinigame.offstage(self)
        self.arrowKeys.destroy()
        del self.arrowKeys
        self.localPatternPad.disable()
        self.localPatternPad.hide()
        self.titleText.hide()
        self.__delMarks(self.checkMarks)
        self.__delMarks(self.xMarks)
        del self.checkMarks
        del self.xMarks
        for avId in list(self.remotePatternPads.keys()):
            self.remotePatternPads[avId].destroy()
            del self.remotePatternPads[avId]

        del self.remotePatternPads
        for avId in list(self.toonHeadDict.keys()):
            head = self.toonHeadDict[avId]
            head.stopBlink()
            head.stopLookAroundNow()
            head.delete()

        del self.toonHeadDict
        if self.isSinglePlayer():
            del self.chancesLeftXMarks
            for head in self.chancesLeftToonHeads:
                head.stopBlink()
                head.delete()

            del self.chancesLeftToonHeads
            for slot in self.chancesLeftSlots:
                slot.destroy()

            del self.chancesLeftSlots
            self.chancesLeftFrame.destroy()
            del self.chancesLeftFrame

        self.minnie.nametag.unmanage(base.marginManager)
        self.minnie.stop()
        self.minnie.stopBlink()
        self.minnie.reparentTo(hidden)
        base.localAvatar.reparentTo(render)
        base.setCellsAvailable(base.leftCells + base.rightCells + base.bottomCells, 1)
        if self.oldBgColor:
            base.setBackgroundColor(self.oldBgColor)

    def __addCheckMark(self, patternPad, instance=True):
        if not instance:
            self.checkMark.reparentTo(patternPad)
        else:
            mark = self.checkMark.instanceTo(patternPad)
            self.checkMarks.append(mark)

    def __addXMark(self, patternPad, instance=True):
        if not instance:
            self.xMark.reparentTo(patternPad)
        else:
            mark = self.xMark.instanceTo(patternPad)
            self.xMarks.append(mark)

    def __delMarks(self, list):
        for mark in list:
            mark.removeNode()
            del mark

    def __updateChancesLeftDisplay(self):
        if not self.isSinglePlayer():
            return None

        for i in range(0, PatternGameGlobals.SP_NUM_CHANCES):
            if i < self.__chances:
                state = 0
            else:
                state = 1
            self.chancesLeftSlots[i]['activeState'] = state

    def setGameReady(self):
        DistributedMinigame.setGameReady(self)
        for i in range(0, len(self.remoteAvIdList)):
            avId = self.remoteAvIdList[i]
            self.__createToonHead(avId, self.remotePatternPads[avId])

        if self.isSinglePlayer():
            self.waitingText['text'] = self.strPleaseWait
        else:
            self.waitingText['text'] = self.strWaitingOtherPlayers

    def setGameStart(self, timestamp):
        DistributedMinigame.setGameStart(self, timestamp)
        self.__initGameVars()
        self.gameFSM.request('readyForNextRound')

    def __initGameVars(self):
        self.__round = 0
        self.__madeAMistake = 0
        if self.isSinglePlayer():
            self.__chances = PatternGameGlobals.SP_NUM_CHANCES
            self.__updateChancesLeftDisplay()

        self.__sitOut = 0

    def __createToonHead(self, avId, patternPad):
        head = ToonHead.ToonHead()
        head.setupHead(self.getAvatar(avId).style, forGui = 1)
        head.reparentTo(patternPad)
        head.setPos(-0.7, 10, -0.25)
        head.setH(180)
        head.setScale(0.25)
        head.startBlink()
        head.startLookAround()
        self.toonHeadDict[avId] = head
        toon = self.getAvatar(avId)
        tag = NametagFloat2d()
        toon.nametag.addNametag(tag)
        tagPath = head.attachNewNode(tag.upcastToPandaNode())
        tagPath.setZ(1)
        tagPath.setH(180)
        tagPath.setScale(0.5)
        tagPath.setDepthWrite(0)
        tagPath.setDepthTest(0)
        head.tag = tag

    def __setMinnieChat(self, string, giggle):
        self.minnie.setChatAbsolute(string, CFSpeech)
        if giggle:
            self.minnie.playDialogue('statementA', 1)

    def __clearMinnieChat(self):
        self.minnie.clearChat()

    def enterOff(self):
        self.notify.debug('enterOff')

    def exitOff(self):
        pass

    def enterReadyForNextRound(self):
        self.notify.debug('enterReadyForNextRound')
        self.checkMark.reparentTo(hidden)
        self.sendUpdate('clientReadyForNextRound', [])
        self.gameFSM.request('waitForServerPattern')

    def exitReadyForNextRound(self):
        pass

    def enterWaitForServerPattern(self):
        self.notify.debug('enterWaitForServerPattern')
        self.checkMark.reparentTo(hidden)
        if not self.__madeAMistake:
            self.__round += 1

        self.roundText.show()
        self.roundText['text'] = str(self.__round)

    def setPattern(self, pattern):
        self.notify.debug('setPattern: ' + str(pattern))
        self.__serverPattern = pattern
        self.gameFSM.request('showServerPattern')

    def exitWaitForServerPattern(self):
        pass

    def enterShowServerPattern(self):
        self.notify.debug('enterShowServerPattern')
        self.checkMark.reparentTo(hidden)
        text = self.strWatch
        if self.isSinglePlayer() and self.__madeAMistake:
            text = self.strTryAgain

        showIntervals = Sequence(
            Func(self.__setMinnieChat, text, 1),
            WaitInterval(0.5))
        for buttonIndex in self.__serverPattern:
            showIntervals.append(self.__createShowButtonPressInterval(buttonIndex))

        showIntervals.append(Sequence(
            WaitInterval(0.2),
            Func(self.__clearMinnieChat),
            WaitInterval(0.2),
            Func(self.__doneShowingPattern),
            WaitInterval(0.001)))
        self.showTrack = Sequence(showIntervals)
        self.showTrack.start()

    def __createShowButtonPressInterval(self, index):
        longest = 0.65
        shortest = 0.3
        r = float(min(self.__round, 10) - 1) / 9.0
        buttonPeriod = shortest * r + longest * (1.0 - r)
        buttonLitPercent = 0.85
        waitTime = buttonPeriod * buttonLitPercent
        waitTime2 = buttonPeriod * (1 - buttonLitPercent)
        return Parallel(
            Sequence(
                Func(self.localPatternPad.simButtonPress, index),
                Func(base.playSfx, self.__getButtonSound(index)),
                WaitInterval(waitTime),
                Func(self.localPatternPad.simButtonRelease, index),
                WaitInterval(waitTime2)))

    def __doneShowingPattern(self):
        self.gameFSM.request('getUserInput')

    def exitShowServerPattern(self):
        self.showTrack.pause()
        del self.showTrack

    def enterGetUserInput(self):
        self.notify.debug('enterGetUserInput')
        self.setupTrack = None
        self.resultTrack = None
        if self.__sitOut:
            self.gameFSM.request('waitForGameOverFlag', enterArgList = [0])
        else:
            def startTimer(self = self):
                time = PatternGameGlobals.InputTime
                self.timer.show()
                self.timer.setTime(time)
                self.timer.countdown(time, self.__handleInputTimeout)

            def enableKeys(self = self):
                def keyPress(self, index):
                    self.localPatternPad.simButtonPress(index)
                    self.__pressHandler(index)

                def keyRelease(self, index):
                    self.localPatternPad.simButtonRelease(index)
                    self.__releaseHandler(index)

                self.arrowKeys.setPressHandlers([
                    (lambda self = self, keyPress = keyPress: keyPress(self, 0)),
                    (lambda self = self, keyPress = keyPress: keyPress(self, 2)),
                    (lambda self = self, keyPress = keyPress: keyPress(self, 3)),
                    (lambda self = self, keyPress = keyPress: keyPress(self, 1))])
                self.arrowKeys.setReleaseHandlers([
                    (lambda self = self, keyRelease = keyRelease: keyRelease(self, 0)),
                    (lambda self = self, keyRelease = keyRelease: keyRelease(self, 2)),
                    (lambda self = self, keyRelease = keyRelease: keyRelease(self, 3)),
                    (lambda self = self, keyRelease = keyRelease: keyRelease(self, 1))])

            self.__localPattern = []
            self.setupTrack = Sequence(
                Func(self.__setMinnieChat, self.strGo, 0),
                Func(self.localPatternPad.enable),
                Func(enableKeys),
                Func(startTimer),
                WaitInterval(0.8),
                Func(self.__clearMinnieChat))
            self.setupTrack.start()

    def __handleInputTimeout(self):
        self.__doneGettingInput(0, 1)

    def __pressHandler(self, index):
        self.__buttonPressed(index)
        self.sendUpdate('announceButtonPressed', [self.localAvId, index])

    def __releaseHandler(self, index):
        self.sendUpdate('announceButtonReleased', [self.localAvId, index])

    def announceButtonPressed(self, avId, button):
        if avId != self.localAvId:
            self.remotePatternPads[avId].simButtonPress(button)

    def announceButtonReleased(self, avId, button):
        if avId != self.localAvId:
            self.remotePatternPads[avId].simButtonRelease(button)

    def __getButtonSound(self, index):
        return self.buttonSounds[index]

    def __doneGettingInput(self, success, timeup = 0):
        self.localPatternPad.disable()
        self.arrowKeys.setPressHandlers(self.arrowKeys.NULL_HANDLERS)
        self.timer.stop()
        self.__madeAMistake = 0
        if not success:
            if self.isSinglePlayer():
                self.__madeAMistake = 1
                self.__chances -= 1
            else:
                self.__sitOut = 1

        def proceed(self = self, success = success):
            self.sendUpdate('reportPlayerResult', [success])
            self.timer.hide()
            self.gameFSM.request('waitForGameOverFlag', enterArgList = [
                success])

        if success:
            sound = self.correctSound
        else:
            sound = self.loseSound
        soundTrack = Sequence(
            Func(base.playSfx, sound),
            WaitInterval(1.6))
        delay = 1.5

        markFunc = lambda x: x
        if success:
            text = self.strRight
        elif timeup:
            text = self.strTimeUp
            delay = 2.0
            if not self.isSinglePlayer():
                markFunc = self.__addXMark
        else:
            text = self.strWrong
            if not self.isSinglePlayer():
                markFunc = self.__addXMark

        waitTime = delay - 0.2
        textTrack = Sequence(
            WaitInterval(0.2),
            Func(self.__setMinnieChat, text, 0),
            WaitInterval(waitTime),
            Func(self.__clearMinnieChat),
            Func(self.__updateChancesLeftDisplay),
            Func(markFunc, self.localPatternPad))
        self.resultTrack = Sequence(
            Parallel(
                soundTrack,
                textTrack),
            Func(proceed))
        self.resultTrack.start()

    def __validPattern(self, fullPattern, partialPattern):
        for i in range(0, len(partialPattern)):
            if partialPattern[i] != fullPattern[i]:
                return 0

        return 1

    def __buttonPressed(self, index):
        base.playSfx(self.__getButtonSound(index))
        self.__localPattern.append(index)
        if 0 == self.__validPattern(self.__serverPattern, self.__localPattern):
            self.__doneGettingInput(0)
        elif len(self.__localPattern) == len(self.__serverPattern):
            self.__doneGettingInput(1)

    def exitGetUserInput(self):
        self.arrowKeys.setPressHandlers(self.arrowKeys.NULL_HANDLERS)
        self.arrowKeys.setReleaseHandlers(self.arrowKeys.NULL_HANDLERS)
        if self.setupTrack:
            self.setupTrack.pause()

        if self.resultTrack:
            self.resultTrack.pause()

        del self.setupTrack
        del self.resultTrack
        self.__clearMinnieChat()

    def setPlayerResult(self, avId, success):
        self.notify.debug('setPlayerResult: ' + str(avId) + ' ' + str(success))
        if avId != self.localAvId:
            pp = self.remotePatternPads[avId]
            if success:
                self.__addCheckMark(pp, False)
            else:
                self.__addXMark(pp)

    def enterWaitForGameOverFlag(self, success):
        self.notify.debug('enterWaitForGameOverFlag')
        self.__success = success
        self.__winTrack = None
        self.waitingText.show()

    def setGameOver(self, flag):
        self.waitingText.hide()
        if flag:

            def proceed(self = self):
                self.gameFSM.request('finish')

            intervals = Sequence()
            if self.__success:
                if self.isSinglePlayer() and self.__chances == PatternGameGlobals.SP_NUM_CHANCES:
                    text = self.strPerfect
                else:
                    text = self.strWin
                sound = self.winSound
            else:
                text = self.strBye
                sound = None
            intervals.extend(Sequence(
                Func(self.__setMinnieChat, text, 1),
                Func(base.playSfx, sound),
                WaitInterval(2),
                Func(self.__clearMinnieChat)))
            intervals.append(Func(proceed))
            self.__winTrack = intervals
            self.__winTrack.start()
        else:
            self.gameFSM.request('readyForNextRound')

    def exitWaitForGameOverFlag(self):
        if self.__winTrack:
            self.__winTrack.pause()

        del self.__winTrack

    def enterFinish(self):
        self.notify.debug('enterFinish')
        self.gameOver()
        self.gameFSM.request('off')

    def exitFinish(self):
        pass
