"""BodyShop module: contains the BodyShop class"""

from panda3d.core import TextNode
from otp.distributed import PotentialAvatar
from toontown.datapack.DataPackManager import DataPackManager
from toontown.suit import SuitDNA
from direct.fsm import StateData
from direct.gui.DirectGui import *
from toontown.makeatoon.MakeAToonGlobals import *
from toontown.toonbase import TTLocalizer, ToontownGlobals
from direct.directnotify import DirectNotifyGlobal
from toontown.makeatoon import ShuffleButton
from toontown.toonbase.ToontownTypes import CogAppearanceIndex
from toontown.toontowngui import TTDialog
from toontown.toon import ToonDNA
import time, random


class ClothesShop(StateData.StateData):
    """
    ClothesShop class: contains methods for changing the Avatar's
    suit texture via user input
    """

    notify = DirectNotifyGlobal.directNotify.newCategory('ClothesShop')

    def __init__(self, makeAToon, doneEvent, avList, index):
        """
        Set-up the body shop interface to change body parts on the
        given toon
        """
        StateData.StateData.__init__(self, doneEvent)
        self.makeAToon = makeAToon
        self.toon = None
        self.index = index
        self.avId = -1
        self.avList = avList
        self.typeChoice = 0

    def enter(self, toon):
        # turn off any user control
        base.disableMouse()

        # load up the given toon
        self.toon = toon
        self.dna = self.toon.getStyle()

        self.typeStart = SuitDNA.suitDepts.index(self.dna.dept)
        self.typeChoice = self.typeStart

        self.__swapType(0)

        choicePool = [SuitDNA.suitDepts]
        self.shuffleButton.setChoicePool(choicePool)
        self.accept(self.shuffleFetchMsg, self.changeBody)

        # set up the "last" button
        self.acceptOnce('last', self.__handleBackward)
        # set up the "next" button
        self.acceptOnce('next', self.__handleDone)
        self.acceptOnce('MAT-newToonCreated', self.shuffleButton.cleanHistory)
        # set up the "done" button
        self.acceptOnce('last', self.__handleBackward)
        self.acceptOnce('skipTutorial', self.__handleSkipTutorial)

    def showButtons(self):
        self.parentFrame.show()

    def hideButtons(self):
        self.parentFrame.hide()

    def exit(self):
        """
        Remove events and restore display
        """

        self.hideButtons()
        self.ignore('last')
        self.ignore('next')
        self.ignore('enter')
        self.ignore(self.shuffleFetchMsg)

    def load(self):
        self.gui = loader.loadModel('phase_3/models/gui/tt_m_gui_mat_mainGui')
        shuffleFrame = self.gui.find('**/tt_t_gui_mat_shuffleFrame')
        shuffleArrowUp = self.gui.find('**/tt_t_gui_mat_shuffleArrowUp')
        shuffleArrowDown = self.gui.find('**/tt_t_gui_mat_shuffleArrowDown')
        shuffleArrowRollover = self.gui.find('**/tt_t_gui_mat_shuffleArrowUp')
        shuffleArrowDisabled = self.gui.find('**/tt_t_gui_mat_shuffleArrowDisabled')
        self.parentFrame = DirectFrame(relief=DGG.RAISED, parent=base.a2dTopRight, pos=(-0.353333, 0, -0.584), frameColor=(1, 0, 0, 0))
        self.suitFrame = DirectFrame(parent=self.parentFrame, image=shuffleFrame, image_scale=halfButtonInvertScale, relief=None, pos=(0, 0, -0.073), hpr=(0, 0, 0), scale=1.3, frameColor=(1, 1, 1, 1), text=TTLocalizer.ColorShopToonFools, text_font=ToontownGlobals.getSuitFont(), text_scale=0.0625, text_pos=(-0.001, -0.015), text_fg=(1, 1, 1, 1))
        self.suitLButton = DirectButton(parent=self.suitFrame, relief=None, image=(shuffleArrowUp,
         shuffleArrowDown,
         shuffleArrowRollover,
         shuffleArrowDisabled), image_scale=halfButtonScale, image1_scale=halfButtonHoverScale, image2_scale=halfButtonHoverScale, pos=(-0.2, 0, 0), command=self.__swapType, extraArgs=[-1])
        self.suitRButton = DirectButton(parent=self.suitFrame, relief=None, image=(shuffleArrowUp,
         shuffleArrowDown,
         shuffleArrowRollover,
         shuffleArrowDisabled), image_scale=halfButtonInvertHoverScale, image1_scale=halfButtonInvertHoverScale, image2_scale=halfButtonInvertHoverScale, pos=(0.2, 0, 0), command=self.__swapType, extraArgs=[1])
        self.parentFrame.hide()
        self.shuffleFetchMsg = 'ClothesShopShuffle'
        self.shuffleButton = ShuffleButton.ShuffleButton(self, self.shuffleFetchMsg)
        self.shuffleButton.shuffleBtn['text_font'] = ToontownGlobals.getSuitFont()
        self.shuffleButton.shuffleBtn['text_scale'] = TTLocalizer.SBshuffleBtn * 0.8
        return

    def unload(self):
        self.gui.removeNode()
        del self.gui
        self.parentFrame.destroy()
        self.suitFrame.destroy()
        self.suitLButton.destroy()
        self.suitRButton.destroy()
        del self.parentFrame
        del self.suitFrame
        del self.suitLButton
        del self.suitRButton
        self.shuffleButton.unload()

        del self.toon

        self.ignore('MAT-newToonCreated')
        self.ignore('nameShopCreateAvatarDone')

        del self.makeAToon

    # event handlers

    def __swapType(self, offset):
        length = len(SuitDNA.suitDepts)
        self.typeChoice = (self.typeChoice + offset) % length
        self.__updateScrollButtons(self.typeChoice, length, self.typeStart, self.suitLButton, self.suitRButton)
        suitType = SuitDNA.suitDepts[self.typeChoice]
        self.__changeTypeName(suitType)
        self.dna.dept = suitType
        if self.toon.isSkeleton:
            self.toon.generateCorporateTie()
        else:
            self.toon.setSuitClothes()
        self.toon.generateCorporateMedallion()
        # tell MAT to move update the camera height
        messenger.send('mat-toon-updated')

    def __updateScrollButtons(self, choice, length, start, lButton, rButton):
        # ghost the pickers if at the end of the 'wheel'
        if choice == (start - 1) % length:
            rButton['state'] = DGG.DISABLED
        elif choice != (start - 1) % length:
            rButton['state'] = DGG.NORMAL
        if choice == start % length:
            lButton['state'] = DGG.DISABLED
        elif choice != start % length:
            lButton['state'] = DGG.NORMAL

        # RAU guard code against both buttons getting disabled, unable to reproduce, but
        # screen shot shows it can happen,  bug 15281
        if lButton['state'] == DGG.DISABLED and rButton['state'] == DGG.DISABLED:
            self.notify.info('Both buttons got disabled! Doing fallback code. choice%d, length=%d, start=%d, lButton=%s, rButton=%s' % (choice,
             length,
             start,
             lButton,
             rButton))
            if choice == start % length:
                lButton['state'] = DGG.DISABLED
                rButton['state'] = DGG.NORMAL
            elif choice == (start - 1) % length:
                lButton['state'] = DGG.NORMAL
                rButton['state'] = DGG.DISABLED
            else:
                lButton['state'] = DGG.NORMAL
                rButton['state'] = DGG.NORMAL

    def __handleBackward(self):
        self.doneStatus = 'last'
        messenger.send(self.doneEvent)

    def changeBody(self):
        newChoice = self.shuffleButton.getCurrChoice()
        newSuitType = newChoice[0]
        newSuitTypeIndex = SuitDNA.suitDepts.index(newSuitType)
        oldSuitType = self.toon.style.dept
        oldSuitTypeIndex = SuitDNA.suitDepts.index(oldSuitType)
        self.__swapType(newSuitTypeIndex - oldSuitTypeIndex)

    def getCurrToonSetting(self):
        return [self.toon.style.dept]

    def __changeTypeName(self, suitType):
        try:
            self.suitFrame['text'] = ToontownGlobals.Dept2Dept[suitType]
        except IndexError:
            self.notify.error('Invalid suitType %s' % suitType)

    def __handleDone(self):
        self.newName = TTLocalizer.SuitBaseNameWithLevel % {'name': DataPackManager.getLocalizedText(base.cr.dataPackMgr.getCogAppearance(self.toon.style.name)[CogAppearanceIndex.NAME]),
                                                            'dept': ToontownGlobals.Dept2Dept.get(self.toon.style.dept),
                                                            'level': random.randint(1, 12)}
        self.doAccept()

    def doAccept(self):
        self.notify.debug('doAccept')
        self.acceptedDialog = TTDialog.TTDialog(text=TTLocalizer.NameShopNameAcceptedFools % self.newName,
                                                style=TTDialog.YesNo, command=self.__handleAccepted)
        self.acceptedDialog.show()

    def __handleAccepted(self, value):
        if value > 0:
            self.__isFirstTime()
        else:
            self.acceptOnce('next', self.__handleDone)
        self.acceptedDialog.cleanup()

    def __isFirstTime(self):
        if base.cr.moddingManager.getDefaultMaxToon() and not base.cr.legitMode:
            self.promptMaxToon()
        else:
            self.promptTutorial()
        self.hideAll()

    def hideAll(self):
        self.hideButtons()
        self.makeAToon.guiCancelButton.hide()
        self.makeAToon.guiCheckButton.hide()
        self.makeAToon.guiLastButton.hide()

    def promptTutorial(self):
        self.promptTutorialDialog = TTDialog.TTDialog(parent=aspect2dp, text=TTLocalizer.PromptTutorial,
                                                      text_scale=0.06, text_align=TextNode.ACenter, text_wordwrap=22,
                                                      command=self.__openTutorialDialog, fadeScreen=0.5,
                                                      style=TTDialog.TwoChoice,
                                                      buttonTextList=[TTLocalizer.MakeAToonEnterTutorial,
                                                                      TTLocalizer.MakeAToonSkipTutorial],
                                                      button_text_scale=0.06, buttonPadSF=5.5,
                                                      sortOrder=DGG.NO_FADE_SORT_INDEX)
        self.promptTutorialDialog.show()

    def __openTutorialDialog(self, choice=0):
        if choice == 1:
            self.notify.debug('enterTutorial')
            if base.config.GetBool('want-qa-regression', 0):
                self.notify.info('QA-REGRESSION: ENTERTUTORIAL: Enter Tutorial')
            self.serverCreateAvatar()
        else:
            self.notify.debug('skipTutorial')
            if base.config.GetBool('want-qa-regression', 0):
                self.notify.info('QA-REGRESSION: SKIPTUTORIAL: Skip Tutorial')
            self.__handleSkipTutorial()
        self.promptTutorialDialog.destroy()

    def promptMaxToon(self):
        self.promptMaxToonDialog = TTDialog.TTDialog(parent=aspect2dp, text=TTLocalizer.PromptMaxToon,
                                                     text_scale=0.06, text_align=TextNode.ACenter, text_wordwrap=22,
                                                     command=self.__openMaxToonDialog, fadeScreen=0.5,
                                                     style=TTDialog.Acknowledge, sortOrder=DGG.NO_FADE_SORT_INDEX)
        self.promptMaxToonDialog.show()

    def __openMaxToonDialog(self, state):
        self.notify.debug('skipTutorial - maxToon')
        if base.config.GetBool('want-qa-regression', 0):
            self.notify.info('QA-REGRESSION: SKIPTUTORIAL: Skip Tutorial - Max Toon')
        self.__handleSkipTutorial()
        self.promptMaxToonDialog.destroy()

    def __handleSkipTutorial(self):
        self.serverCreateAvatar(True)

    def serverCreateAvatar(self, skipTutorial=False):
        self.notify.debug('serverCreateAvatar')

        # Make a random ToonDNA just so the server doesn't yell at us for giving it a SuitDNA
        style = ToonDNA.ToonDNA()
        style.newToonRandom(time.time(), random.choice(('m', 'f')))
        self.newDNA = style.makeNetString()

        if skipTutorial:
            self.requestingSkipTutorial = True
        else:
            self.requestingSkipTutorial = False

        base.cr.gameServicesManager.sendCreateAvatar(style, self.newName, self.index)
        self.accept('nameShopCreateAvatarDone', self.handleCreateAvatarResponse)
        self.notify.debug('Ending Make A Toon: %s' % style)
        base.cr.centralLogger.writeClientEvent('MAT - endingMakeAToon: %s' % style)

    def handleCreateAvatarResponse(self, avId):
        self.notify.debug('handleCreateAvatarResponse')
        self.notify.debug('avatar with default name accepted')
        self.avId = avId
        self.logAvatarCreation()
        self.toon.setName(self.newName)
        newPotAv = PotentialAvatar.PotentialAvatar(self.avId, (self.newName, '', '', ''), self.newDNA, self.index, 1, wishState="LOCKED")
        self.avList.append(newPotAv)
        self.doneStatus = 'done'
        self.storeSkipTutorialRequest()
        messenger.send(self.doneEvent)

    def storeSkipTutorialRequest(self):
        base.cr.skipTutorialRequest = self.requestingSkipTutorial

    def logAvatarCreation(self):
        dislId = 0
        try:
            dislId = launcher.getValue('GAME_DISL_ID')
        except:
            pass

        if not dislId:
            self.notify.warning('No dislId, using 0')
            dislId = 0
        gameSource = '0'
        try:
            gameSource = launcher.getValue('GAME_SOURCE')
        except:
            pass

        if not gameSource:
            gameSource = '0'
        else:
            self.notify.info('got GAME_SOURCE=%s' % gameSource)
        if self.avId > 0:
            base.cr.centralLogger.writeClientEvent('createAvatar %s-%s-%s' % (self.avId, dislId, gameSource))
            self.notify.debug('createAvatar %s-%s-%s' % (self.avId, dislId, gameSource))
        else:
            self.notify.warning('logAvatarCreation got self.avId =%s' % self.avId)
