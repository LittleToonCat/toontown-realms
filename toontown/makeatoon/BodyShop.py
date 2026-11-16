"""BodyShop module: contains the BodyShop class"""

from panda3d.core import *
from toontown.toon import ToonDNA
from direct.fsm import StateData
from direct.gui.DirectGui import *
from .MakeAToonGlobals import *
import random
from toontown.toonbase import TTLocalizer
from direct.directnotify import DirectNotifyGlobal
from . import ShuffleButton
from ..toontowngui.AnimatedButton import AnimatedButton


class BodyShop(StateData.StateData):
    """
    BodyShop class: contains methods for changing the Avatar's
    head, torso, and legs via user input
    """

    notify = DirectNotifyGlobal.directNotify.newCategory('BodyShop')

    def __init__(self, doneEvent):
        """
        Set-up the body shop interface to change body parts on the
        given toon
        """
        StateData.StateData.__init__(self, doneEvent)
        self.toon = None
        self.torsoChoice = 0
        self.legChoice = 0
        self.headChoice = 0
        self.speciesChoice = 0
        return

    def enter(self, toon, shopsVisited = []):
        # turn off any user control
        base.disableMouse()

        # load up the given toon
        self.toon = toon
        self.dna = self.toon.getStyle()
        gender = self.toon.style.getGender()

        self.speciesStart = self.getSpeciesStart()
        self.speciesChoice = self.speciesStart
        self.headStart = 0
        self.headChoice = ToonDNA.toonHeadTypesMAT.index(self.dna.head) - ToonDNA.getHeadStartIndex(self.species)
        self.torsoStart = 0
        self.torsoChoice = ToonDNA.toonTorsoTypes.index(self.dna.torso) % 3
        self.legStart = 0
        self.legChoice = ToonDNA.toonLegTypes.index(self.dna.legs)
        if CLOTHESSHOP in shopsVisited:
            self.clothesPicked = 1
        else:
            self.clothesPicked = 0
        self.clothesPicked = 1

        # if we have visited the ClothesShop and the returned to the
        # GenderShop it's possible that our gender has changed and our DNA
        # has not. Update these bits...
        if gender == 'm' or ToonDNA.GirlBottoms[self.dna.botTex][1] == ToonDNA.SHORTS:
            torsoStyle = 's'
            torsoPool = ToonDNA.toonTorsoTypes[:3]
        else:
            torsoStyle = 'd'
            torsoPool = ToonDNA.toonTorsoTypes[3:6]

        # update the clothes and eye lashes, just in case
        self.__swapSpecies(0)
        self.__swapHead(0)
        self.__swapTorso(0)
        self.__swapLegs(0)

        choicePool = [ToonDNA.toonHeadTypesMAT, torsoPool, ToonDNA.toonLegTypes]
        self.shuffleButton.setChoicePool(choicePool)
        self.accept(self.shuffleFetchMsg, self.changeBody)

        # set up the "last" button
        self.acceptOnce('last', self.__handleBackward)
        # set up the "next" button
        self.accept('next', self.__handleForward)
        self.acceptOnce('MAT-newToonCreated', self.shuffleButton.cleanHistory)

    def getSpeciesStart(self):
        for species in ToonDNA.toonSpeciesTypesMAT:
            if species == self.dna.head[0]:
                self.species = species
                return ToonDNA.toonSpeciesTypesMAT.index(species)

    def showButtons(self):
        self.parentFrame.show()

    def hideButtons(self):
        self.parentFrame.hide()

    def exit(self):
        """
        Remove events and restore display
        """
        try:
            del self.toon
        except:
            self.notify.warning('BodyShop: toon not found')

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
        self.speciesFrame = DirectFrame(parent=self.parentFrame, image=shuffleFrame, image_scale=halfButtonInvertScale, relief=None, pos=(0, 0, -0.073), hpr=(0, 0, 0), scale=1.3, frameColor=(1, 1, 1, 1), text=TTLocalizer.BodyShopSpecies, text_scale=0.0625, text_pos=(-0.001, -0.015), text_fg=(1, 1, 1, 1))
        self.speciesLButton = AnimatedButton(parent=self.speciesFrame, relief=None, image=(shuffleArrowUp,
         shuffleArrowDown,
         shuffleArrowRollover,
         shuffleArrowDisabled), image_scale=halfButtonScale, image1_scale=halfButtonHoverScale, image2_scale=halfButtonHoverScale, pos=(-0.2, 0, 0), command=self.__swapSpecies, extraArgs=[-1])
        self.speciesRButton = AnimatedButton(parent=self.speciesFrame, relief=None, image=(shuffleArrowUp,
         shuffleArrowDown,
         shuffleArrowRollover,
         shuffleArrowDisabled), image_scale=halfButtonInvertScale, image1_scale=halfButtonInvertHoverScale, image2_scale=halfButtonInvertHoverScale, pos=(0.2, 0, 0), command=self.__swapSpecies, extraArgs=[1])
        self.headFrame = DirectFrame(parent=self.parentFrame, image=shuffleFrame, image_scale=halfButtonInvertScale, relief=None, pos=(0, 0, -0.3), hpr=(0, 0, 2), scale=0.9, frameColor=(1, 1, 1, 1), text=TTLocalizer.BodyShopHead, text_scale=0.0625, text_pos=(-0.001, -0.015), text_fg=(1, 1, 1, 1))
        self.headLButton = AnimatedButton(parent=self.headFrame, relief=None, image=(shuffleArrowUp,
         shuffleArrowDown,
         shuffleArrowRollover,
         shuffleArrowDisabled), image_scale=halfButtonScale, image1_scale=halfButtonHoverScale, image2_scale=halfButtonHoverScale, pos=(-0.2, 0, 0), command=self.__swapHead, extraArgs=[-1])
        self.headRButton = AnimatedButton(parent=self.headFrame, relief=None, image=(shuffleArrowUp,
         shuffleArrowDown,
         shuffleArrowRollover,
         shuffleArrowDisabled), image_scale=halfButtonInvertScale, image1_scale=halfButtonInvertHoverScale, image2_scale=halfButtonInvertHoverScale, pos=(0.2, 0, 0), command=self.__swapHead, extraArgs=[1])
        self.bodyFrame = DirectFrame(parent=self.parentFrame, image=shuffleFrame, image_scale=halfButtonScale, relief=None, pos=(0, 0, -0.5), hpr=(0, 0, -2), scale=0.9, frameColor=(1, 1, 1, 1), text=TTLocalizer.BodyShopBody, text_scale=0.0625, text_pos=(-0.001, -0.015), text_fg=(1, 1, 1, 1))
        self.torsoLButton = AnimatedButton(parent=self.bodyFrame, relief=None, image=(shuffleArrowUp,
         shuffleArrowDown,
         shuffleArrowRollover,
         shuffleArrowDisabled), image_scale=halfButtonScale, image1_scale=halfButtonHoverScale, image2_scale=halfButtonHoverScale, pos=(-0.2, 0, 0), command=self.__swapTorso, extraArgs=[-1])
        self.torsoRButton = AnimatedButton(parent=self.bodyFrame, relief=None, image=(shuffleArrowUp,
         shuffleArrowDown,
         shuffleArrowRollover,
         shuffleArrowDisabled), image_scale=halfButtonInvertScale, image1_scale=halfButtonInvertHoverScale, image2_scale=halfButtonInvertHoverScale, pos=(0.2, 0, 0), command=self.__swapTorso, extraArgs=[1])
        self.legsFrame = DirectFrame(parent=self.parentFrame, image=shuffleFrame, image_scale=halfButtonInvertScale, relief=None, pos=(0, 0, -0.7), hpr=(0, 0, 3), scale=0.9, frameColor=(1, 1, 1, 1), text=TTLocalizer.BodyShopLegs, text_scale=0.0625, text_pos=(-0.001, -0.015), text_fg=(1, 1, 1, 1))
        self.legLButton = AnimatedButton(parent=self.legsFrame, relief=None, image=(shuffleArrowUp,
         shuffleArrowDown,
         shuffleArrowRollover,
         shuffleArrowDisabled), image_scale=halfButtonScale, image1_scale=halfButtonHoverScale, image2_scale=halfButtonHoverScale, pos=(-0.2, 0, 0), command=self.__swapLegs, extraArgs=[-1])
        self.legRButton = AnimatedButton(parent=self.legsFrame, relief=None, image=(shuffleArrowUp,
         shuffleArrowDown,
         shuffleArrowRollover,
         shuffleArrowDisabled), image_scale=halfButtonInvertScale, image1_scale=halfButtonInvertHoverScale, image2_scale=halfButtonInvertHoverScale, pos=(0.2, 0, 0), command=self.__swapLegs, extraArgs=[1])
        self.parentFrame.hide()
        self.shuffleFetchMsg = 'BodyShopShuffle'
        self.shuffleButton = ShuffleButton.ShuffleButton(self, self.shuffleFetchMsg)
        return

    def unload(self):
        self.gui.removeNode()
        del self.gui
        self.parentFrame.destroy()
        self.speciesFrame.destroy()
        self.headFrame.destroy()
        self.bodyFrame.destroy()
        self.legsFrame.destroy()
        self.speciesLButton.destroy()
        self.speciesRButton.destroy()
        self.headLButton.destroy()
        self.headRButton.destroy()
        self.torsoLButton.destroy()
        self.torsoRButton.destroy()
        self.legLButton.destroy()
        self.legRButton.destroy()
        del self.parentFrame
        del self.speciesFrame
        del self.headFrame
        del self.bodyFrame
        del self.legsFrame
        del self.speciesLButton
        del self.speciesRButton
        del self.headLButton
        del self.headRButton
        del self.torsoLButton
        del self.torsoRButton
        del self.legLButton
        del self.legRButton
        self.shuffleButton.unload()
        self.ignore('MAT-newToonCreated')

    # event handlers

    def __swapTorso(self, offset):
        # if this is the first time through only choose from naked torsos
        # (they are at 6-8)
        gender = self.toon.style.getGender()
        if not self.clothesPicked:
            length = len(ToonDNA.toonTorsoTypes[6:])
            torsoOffset = 6
        # otherwise use either the male or female clothed torsos
        elif gender == 'm':
            # Note: we need to correct colors that are not cross-gender
            # male (0-2)
            length = len(ToonDNA.toonTorsoTypes[:3])
            torsoOffset = 0
            # Make sure the topTex, sleeveTex, and botTex are all within
            # valid index range for boys in case we're switching gender
            if self.toon.style.topTex not in ToonDNA.MakeAToonBoyShirts:
                randomShirt = ToonDNA.getRandomTop(gender, ToonDNA.MAKE_A_TOON)
                shirtTex, shirtColor, sleeveTex, sleeveColor = randomShirt
                self.toon.style.topTex = shirtTex
                self.toon.style.topTexColor = shirtColor
                self.toon.style.sleeveTex = sleeveTex
                self.toon.style.sleeveTexColor = sleeveColor
            # Only use the boy shorts used in MakeAToon
            if self.toon.style.botTex not in ToonDNA.MakeAToonBoyBottoms:
                # Pick one randomly
                botTex, botTexColor = ToonDNA.getRandomBottom(gender, ToonDNA.MAKE_A_TOON)
                self.toon.style.botTex = botTex
                self.toon.style.botTexColor = botTexColor

        # female (0-5)
        else:
            length = len(ToonDNA.toonTorsoTypes[3:6])
            if self.toon.style.torso[1] == 'd':
                torsoOffset = 3
            else:
                torsoOffset = 0
            if self.dna.armColor not in ToonDNA.defaultGirlColorList:
                self.dna.armColor = ToonDNA.defaultGirlColorList[0]
            if self.dna.legColor not in ToonDNA.defaultGirlColorList:
                self.dna.legColor = ToonDNA.defaultGirlColorList[0]
            if self.dna.headColor not in ToonDNA.defaultGirlColorList:
                self.dna.headColor = ToonDNA.defaultGirlColorList[0]
            # Make sure the topTex, sleeveTex, and botTex are all within
            # valid index range for girls in case we're switching gender
            if self.toon.style.topTex not in ToonDNA.MakeAToonGirlShirts:
                randomShirt = ToonDNA.getRandomTop(gender, ToonDNA.MAKE_A_TOON)
                shirtTex, shirtColor, sleeveTex, sleeveColor = randomShirt
                self.toon.style.topTex = shirtTex
                self.toon.style.topTexColor = shirtColor
                self.toon.style.sleeveTex = sleeveTex
                self.toon.style.sleeveTexColor = sleeveColor
            # Only use the girl bottoms used in MakeAToon
            if self.toon.style.botTex not in ToonDNA.MakeAToonGirlBottoms:
                if self.toon.style.torso[1] == 'd':
                    botTex, botTexColor = ToonDNA.getRandomBottom(gender, ToonDNA.MAKE_A_TOON, girlBottomType=ToonDNA.SKIRT)
                    self.toon.style.botTex = botTex
                    self.toon.style.botTexColor = botTexColor
                    torsoOffset = 3
                else:
                    botTex, botTexColor = ToonDNA.getRandomBottom(gender, ToonDNA.MAKE_A_TOON, girlBottomType=ToonDNA.SHORTS)
                    self.toon.style.botTex = botTex
                    self.toon.style.botTexColor = botTexColor
                    torsoOffset = 0

        self.notify.debug('torsoChoice before: %d' % self.torsoChoice)
        self.torsoChoice = (self.torsoChoice + offset) % length
        self.notify.debug('new torsoChoice: %d offset: %d length: %d torsoOffset: %d torsoStart: %d' % (self.torsoChoice, offset, length, torsoOffset, self.torsoStart))
        # ghost the pickers if at the end of the 'wheel'
        self.__updateScrollButtons(self.torsoChoice, length, self.torsoStart, self.torsoLButton, self.torsoRButton)
        torso = ToonDNA.toonTorsoTypes[torsoOffset + self.torsoChoice]
        self.dna.torso = torso
        self.toon.swapToonTorso(torso)
        self.toon.loop('neutral', 0)
        self.toon.swapToonColor(self.dna)
        # tell MAT to move update the camera height
        messenger.send('mat-toon-updated')

    def __swapLegs(self, offset):
        length = len(ToonDNA.toonLegTypes)
        self.legChoice = (self.legChoice + offset) % length
        # ghost the pickers if at the end of the 'wheel'
        self.notify.debug('self.legChoice=%d, length=%d, self.legStart=%d' % (self.legChoice, length, self.legStart))
        self.__updateScrollButtons(self.legChoice, length, self.legStart,
                                   self.legLButton, self.legRButton)
        newLeg = ToonDNA.toonLegTypes[self.legChoice]
        self.dna.legs = newLeg
        self.toon.swapToonLegs(newLeg)
        self.toon.loop('neutral', 0)
        self.toon.swapToonColor(self.dna)
        # tell MAT to move update the camera height
        messenger.send('mat-toon-updated')

    def __swapHead(self, offset):
        self.headList = ToonDNA.getHeadList(self.species)
        length = len(self.headList)
        self.headChoice = (self.headChoice + offset) % length
        self.__updateHead()
        # tell MAT to move update the camera height
        messenger.send('mat-toon-updated')

    def __swapSpecies(self, offset):
        length = len(ToonDNA.toonSpeciesTypesMAT)
        self.speciesChoice = (self.speciesChoice + offset) % length
        self.__updateScrollButtons(self.speciesChoice, length, self.speciesStart, self.speciesLButton, self.speciesRButton)
        self.species = ToonDNA.toonSpeciesTypesMAT[self.speciesChoice]
        self.headList = ToonDNA.getHeadList(self.species)
        self.__changeSpeciesName(self.species)
        maxHeadChoice = len(self.headList) - 1
        if self.headChoice > maxHeadChoice:
            self.headChoice = maxHeadChoice
        self.__updateHead()

    def __updateHead(self):
        self.__updateScrollButtons(self.headChoice, len(self.headList), self.headStart, self.headLButton, self.headRButton)
        headIndex = ToonDNA.getHeadStartIndexMAT(self.species) + self.headChoice
        newHead = ToonDNA.toonHeadTypesMAT[headIndex]
        self.dna.head = newHead
        self.toon.swapToonHead(newHead)
        self.toon.loop('neutral', 0)
        self.toon.swapToonColor(self.dna)
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

        #RAU guard code against both buttons getting disabled, unable to reproduce, but
        #screen shot shows it can happen,  bug 15281
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

    def __handleForward(self):
        self.doneStatus = 'next'
        messenger.send(self.doneEvent)

    def __handleBackward(self):
        self.doneStatus = 'last'
        messenger.send(self.doneEvent)

    def changeBody(self):
        newChoice = self.shuffleButton.getCurrChoice()
        newHead = newChoice[0]
        newSpeciesIndex = ToonDNA.toonSpeciesTypesMAT.index(ToonDNA.getSpecies(newHead))
        newHeadIndex = ToonDNA.toonHeadTypesMAT.index(newHead) - ToonDNA.getHeadStartIndexMAT(ToonDNA.getSpecies(newHead))
        newTorsoIndex = ToonDNA.toonTorsoTypes.index(newChoice[1])
        newLegsIndex = ToonDNA.toonLegTypes.index(newChoice[2])
        oldHead = self.toon.style.head
        oldSpeciesIndex = ToonDNA.toonSpeciesTypesMAT.index(ToonDNA.getSpecies(oldHead))
        oldHeadIndex = ToonDNA.toonHeadTypesMAT.index(oldHead) - ToonDNA.getHeadStartIndexMAT(ToonDNA.getSpecies(oldHead))
        oldTorsoIndex = ToonDNA.toonTorsoTypes.index(self.toon.style.torso)
        oldLegsIndex = ToonDNA.toonLegTypes.index(self.toon.style.legs)
        self.__swapSpecies(newSpeciesIndex - oldSpeciesIndex)
        self.__swapHead(newHeadIndex - oldHeadIndex)
        self.__swapTorso(newTorsoIndex - oldTorsoIndex)
        self.__swapLegs(newLegsIndex - oldLegsIndex)

    def getCurrToonSetting(self):
        return [self.toon.style.head, self.toon.style.torso, self.toon.style.legs]

    def __changeSpeciesName(self, species):
        if species == 'd':
            self.speciesFrame['text'] = TTLocalizer.AnimalToSpecies['dog']
        elif species == 'c':
            self.speciesFrame['text'] = TTLocalizer.AnimalToSpecies['cat']
        elif species == 'm':
            self.speciesFrame['text'] = TTLocalizer.AnimalToSpecies['mouse']
        elif species == 'h':
            self.speciesFrame['text'] = TTLocalizer.AnimalToSpecies['horse']
        elif species == 'r':
            self.speciesFrame['text'] = TTLocalizer.AnimalToSpecies['rabbit']
        elif species == 'f':
            self.speciesFrame['text'] = TTLocalizer.AnimalToSpecies['duck']
        elif species == 'p':
            self.speciesFrame['text'] = TTLocalizer.AnimalToSpecies['monkey']
        elif species == 'b':
            self.speciesFrame['text'] = TTLocalizer.AnimalToSpecies['bear']
        elif species == 's':
            self.speciesFrame['text'] = TTLocalizer.AnimalToSpecies['pig']
