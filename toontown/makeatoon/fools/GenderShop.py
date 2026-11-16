from panda3d.core import Vec3
from direct.fsm import StateData
from direct.gui.DirectGui import *
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals
from toontown.makeatoon.MakeAToonGlobals import *
from direct.directnotify import DirectNotifyGlobal
from toontown.suit import Suit, SuitDNA
import random

cogIconHalfButtonScale = Vec3(halfButtonScale) / 2
cogIconHalfButtonHoverScale = Vec3(halfButtonHoverScale) / 2


class GenderShop(StateData.StateData):

    notify = DirectNotifyGlobal.directNotify.newCategory('GenderShop')

    def __init__(self, makeAToon, doneEvent):
        StateData.StateData.__init__(self, doneEvent)
        self.shopsVisited = []
        self.suit = None
        self.suitName = None
        self.makeAToon = makeAToon
        return

    def enter(self):
        base.disableMouse()
        self.accept('next', self.__handleForward)
        return None

    def exit(self):
        self.ignore('next')

    def load(self):
        gui = loader.loadModel('phase_3/models/gui/cog_icons')
        sellbotUp = gui.find('**/SalesIcon')
        cashbotUp = gui.find('**/MoneyIcon')
        lawbotUp = gui.find('**/LegalIcon')
        bossbotUp = gui.find('**/CorpIcon')

        self.sellbotButton = DirectButton(relief=None, image=(sellbotUp, sellbotUp, sellbotUp, sellbotUp), image_scale=cogIconHalfButtonScale, image1_scale=cogIconHalfButtonHoverScale,
                                      image2_scale=cogIconHalfButtonHoverScale, pos=(-0.6, 0, -0.8), command=self.createRandomSuit, extraArgs=[0],
                                      text=('', TTLocalizer.Sellbot, TTLocalizer.Sellbot, ''), text_font=ToontownGlobals.getSuitFont(), text_scale=0.08,
                                      text_pos=(0, 0.19), text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1))
        self.sellbotButton.hide()

        self.cashbotButton = DirectButton(relief=None, image=(cashbotUp, cashbotUp, cashbotUp, cashbotUp), image_scale=cogIconHalfButtonScale, image1_scale=cogIconHalfButtonHoverScale,
                                       image2_scale=cogIconHalfButtonHoverScale, pos=(-0.2, 0, -0.8), command=self.createRandomSuit, extraArgs=[1],
                                       text=('', TTLocalizer.Cashbot, TTLocalizer.Cashbot, ''), text_font=ToontownGlobals.getSuitFont(), text_scale=0.08,
                                       text_pos=(0, 0.19), text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1))
        self.cashbotButton.hide()

        self.lawbotButton = DirectButton(relief=None, image=(lawbotUp, lawbotUp, lawbotUp, lawbotUp), image_scale=cogIconHalfButtonScale, image1_scale=cogIconHalfButtonHoverScale,
                                          image2_scale=cogIconHalfButtonHoverScale, pos=(0.2, 0, -0.8), command=self.createRandomSuit, extraArgs=[2],
                                          text=('', TTLocalizer.Lawbot, TTLocalizer.Lawbot, ''), text_font=ToontownGlobals.getSuitFont(), text_scale=0.08,
                                          text_pos=(0, 0.19), text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1))
        self.lawbotButton.hide()

        self.bossbotButton = DirectButton(relief=None, image=(bossbotUp, bossbotUp, bossbotUp, bossbotUp), image_scale=cogIconHalfButtonScale, image1_scale=cogIconHalfButtonHoverScale,
                                          image2_scale=cogIconHalfButtonHoverScale, pos=(0.6, 0, -0.8), command=self.createRandomSuit, extraArgs=[3],
                                          text=('', TTLocalizer.Bossbot, TTLocalizer.Bossbot, ''), text_font=ToontownGlobals.getSuitFont(), text_scale=0.08,
                                          text_pos=(0, 0.19), text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1))
        self.bossbotButton.hide()

        gui.removeNode()
        del gui
        self.toon = None

    def unload(self):
        self.sellbotButton.destroy()
        self.cashbotButton.destroy()
        self.lawbotButton.destroy()
        self.bossbotButton.destroy()
        del self.sellbotButton
        del self.cashbotButton
        del self.lawbotButton
        del self.bossbotButton

        if self.toon:
            self.toon.delete()
        self.makeAToon = None

    def hideButtons(self):
        self.sellbotButton.hide()
        self.cashbotButton.hide()
        self.lawbotButton.hide()
        self.bossbotButton.hide()

    def showButtons(self):
        self.sellbotButton.show()
        self.cashbotButton.show()
        self.lawbotButton.show()
        self.bossbotButton.show()

    def createRandomSuit(self, dept):
        self._createRandomToon(dept)

    def _createRandomToon(self, dept):
        # Delete the previous suit
        if self.suit:
            self.suit.delete()

        self.suit = Suit.Suit()
        d = SuitDNA.SuitDNA()
        departmentSuits = ToontownGlobals.GreenEffectMassFlyCogs[dept]
        suitName = self.suitName
        while suitName == self.suitName:
            suitName = random.choice(departmentSuits)
        self.suitName = suitName
        d.newSuit(suitName)
        self.suit.setDNA(d)

        self.suit.reparentTo(self.makeAToon.background)
        self.suit.setPos(self.makeAToon.toonPosition)
        self.suit.setHpr(self.makeAToon.toonHpr)
        self.suit.setScale(self.makeAToon.toonScale)
        self.suit.loop('neutral')

        self.makeAToon.setNextButtonState(DGG.NORMAL)
        self.makeAToon.setToon(self.suit)
        messenger.send('MAT-newToonCreated')

        # tell MAT to update the camera height
        messenger.send('mat-toon-updated')

    def __handleForward(self):
        self.doneStatus = 'next'
        messenger.send(self.doneEvent)
