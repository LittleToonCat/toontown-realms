"""GenderShop module: contains the GenderShop class"""

from panda3d.core import *
from direct.fsm import StateData
from direct.gui.DirectGui import *
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals
from toontown.toon import ToonDNA
from toontown.toon import Toon
from .MakeAToonGlobals import *
from direct.directnotify import DirectNotifyGlobal
import random
import time

from ..toontowngui.AnimatedButton import AnimatedButton


class GenderShop(StateData.StateData):
    """GenderShop class: contains methods for changing the Avatar's
    gender via user input"""

    notify = DirectNotifyGlobal.directNotify.newCategory('GenderShop')

    def __init__(self, makeAToon, doneEvent):
        """__init__(self, MakeAToon, Event)
        Set-up the gender to shop to query user about toons gender
        """
        StateData.StateData.__init__(self, doneEvent)
        self.shopsVisited = []
        self.toon = None
        self.gender = 'm'
        self.makeAToon = makeAToon
        return

    def enter(self):
        """enter(self)
        """
        base.disableMouse()
        self.accept('next', self.__handleForward)
        return None

    def exit(self):
        """exit(self)
        Remove events and restore display
        """
        self.ignore('next')

    def load(self):
        """load(self)
        """
        gui = loader.loadModel('phase_3/models/gui/tt_m_gui_mat_mainGui')
        guiBoyUp = gui.find('**/tt_t_gui_mat_boyUp')
        guiBoyDown = gui.find('**/tt_t_gui_mat_boyDown')
        guiGirlUp = gui.find('**/tt_t_gui_mat_girlUp')
        guiGirlDown = gui.find('**/tt_t_gui_mat_girlDown')
        self.boyButton = AnimatedButton(relief=None, image=(guiBoyUp,
         guiBoyDown,
         guiBoyUp,
         guiBoyDown), image_scale=halfButtonScale, image1_scale=halfButtonHoverScale, image2_scale=halfButtonHoverScale, pos=(-0.4, 0, -0.8), command=self.createRandomBoy, text=('',
         TTLocalizer.GenderShopBoyButtonText,
         TTLocalizer.GenderShopBoyButtonText,
         ''), text_font=ToontownGlobals.getInterfaceFont(), text_scale=0.08, text_pos=(0, 0.19), text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1))
        self.boyButton.hide()
        self.girlButton = AnimatedButton(relief=None, image=(guiGirlUp,
         guiGirlDown,
         guiGirlUp,
         guiGirlDown), image_scale=halfButtonScale, image1_scale=halfButtonHoverScale, image2_scale=halfButtonHoverScale, pos=(0.4, 0, -0.8), command=self.createRandomGirl, text=('',
         TTLocalizer.GenderShopGirlButtonText,
         TTLocalizer.GenderShopGirlButtonText,
         ''), text_font=ToontownGlobals.getInterfaceFont(), text_scale=0.08, text_pos=(0, 0.19), text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1))
        self.girlButton.hide()
        gui.removeNode()
        del gui
        self.toon = None
        return

    def unload(self):
        """unload(self)
        """
        self.boyButton.destroy()
        self.girlButton.destroy()
        del self.boyButton
        del self.girlButton
        if self.toon:
            self.toon.delete()
        self.makeAToon = None
        return

    def setGender(self, choice):
        self.__setGender(choice)

    def __setGender(self, choice):
        self.gender = 'm'
        if self.toon:
            self.gender = self.toon.style.gender
        messenger.send(self.doneEvent)

    # event handlers

    def hideButtons(self):
        self.boyButton.hide()
        self.girlButton.hide()

    def showButtons(self):
        self.boyButton.show()
        self.girlButton.show()

    def createRandomBoy(self):
        self._createRandomToon('m')

    def createRandomGirl(self):
        self._createRandomToon('f')

    def _createRandomToon(self, gender):
        if self.toon:
            self.toon.stopBlink()
            self.toon.stopLookAroundNow()
            self.toon.delete()
        self.dna = ToonDNA.ToonDNA()
        seed = int(round(time.time() * random.randrange(1, 100)))
        self.dna.newToonRandom(seed=seed, gender=gender, stage=1)
        self.toon = Toon.Toon()
        self.toon.setDNA(self.dna)
        self.toon.useLOD(1000)
        self.toon.setNameVisible(0)
        self.toon.startBlink()
        self.toon.startLookAround()
        self.toon.reparentTo(render)
        self.toon.setPos(self.makeAToon.toonPosition)
        self.toon.setHpr(self.makeAToon.toonHpr)
        self.toon.setScale(self.makeAToon.toonScale)
        self.toon.loop('neutral')
        self.makeAToon.setNextButtonState(DGG.NORMAL)
        self.makeAToon.setToon(self.toon)
        messenger.send('MAT-newToonCreated')

        # tell MAT to update the camera height
        messenger.send('mat-toon-updated')

    def __handleForward(self):
        self.doneStatus = 'next'
        messenger.send(self.doneEvent)
