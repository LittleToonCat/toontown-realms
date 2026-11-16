from direct.gui.DirectGui import *
from panda3d.core import *
from . import FishPokerBase
from .FishPhoto import FishPhoto
from .FishBase import FishBase
from . import FishGlobals
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals


class FishPokerCard(DirectFrame):

    UnlockedColor = Vec4(*ToontownGlobals.GlobalDialogColor)
    LockedColor = Vec4(0.8, 0.4, 0.4, 1)
    
    def __init__(self, index, lockCallback, **kw):
        optiondefs = (
            ('relief',                                    None,    None),
            ('image',                   DGG.getDefaultDialogGeom(),    None),
            ('image_color',  ToontownGlobals.GlobalDialogColor,    None),
            ('image_scale',                    (0.35, 1, 0.45),    None),
            ('text',                                        '',    None),
            ('text_scale',                                0.06,    None),
            ('text_fg',                           (0, 0, 0, 1),    None),
            ('text_pos',                          (0, 0.35, 0),    None),
            ('text_font',   ToontownGlobals.getInterfaceFont(),    None),
            ('text_wordwrap',                             13.5,    None),
            )
        # Merge keyword options with default options
        self.defineoptions(kw, optiondefs)
        DirectFrame.__init__(self)
        self.initialiseoptions(FishPokerCard)
        self.index = index
        self.fish = None
        guiButton = loader.loadModel("phase_3/models/gui/quit_button")
        self.lockCallback = lockCallback
        self.lockButton = DirectButton(
            parent=self,
            relief=None,
            image=(guiButton.find("**/QuitBtn_UP"),
                   guiButton.find("**/QuitBtn_DN"),
                   guiButton.find("**/QuitBtn_RLVR"),
                   ),
            image_scale=1,
            text=TTLocalizer.FishPokerLock,
            text_scale=0.06,
            textMayChange=1,
            pos=(0, 0, 0.2),
            command=self.toggleLock,
            )
        self.fishFrame = DirectFrame(
            parent=self,
            relief=None,
            text='',
            text_scale=0.05,
            text_pos=(0, 0.05),
            pos=(0, 0, -0.2),
            text_wordwrap=8,
            )
        self.fishPhoto = FishPhoto(parent=self.fishFrame, wantSound=False)
        self.fishPhoto.setZ(0.25)
        self.fishPhoto.setSwimBounds(-0.15, 0.15, -0.15, 0.1)
        self.setFishColor(self.UnlockedColor)
        guiButton.removeNode()

    def toggleLock(self):
        # Call the callback, passing in our index
        self.lockCallback(self.index)

    def update(self, fish, lockedStatus):
        self.fish = fish
        if self.fish:
            self.lockButton['state'] = DGG.NORMAL
            self.fishFrame['text'] = fish.getGenusName()
            self.fishPhoto.update(fish)
            self.fishPhoto.show()
        else:
            self.lockButton['state'] = DGG.DISABLED
            self.fishFrame['text'] = ""
            self.fishPhoto.hide()
        self.setLockStatus(lockedStatus)

    def setLockStatus(self, lockStatus):
        if lockStatus:
            self.lockButton['text'] = TTLocalizer.FishPokerUnlock
            self['image_color'] = self.LockedColor
            self.setFishColor(self.LockedColor)
        else:
            self.lockButton['text'] = TTLocalizer.FishPokerLock
            self['image_color'] = self.UnlockedColor
            self.setFishColor(self.UnlockedColor)

    def setFishColor(self, color):
        if hasattr(self.fishPhoto, 'fishDisplayRegion'):
            fdr = self.fishPhoto.fishDisplayRegion
            if hasattr(fdr, 'card'):
                self.fishPhoto.fishDisplayRegion.card.setColor(*color)
            if hasattr(fdr, 'cDr'):
                self.fishPhoto.fishDisplayRegion.cDr.setClearColor(color)
        else:
            self.fishPhoto.setSwimColor(color)

    def clear(self):
        self.update(None, 0)

    def destroy(self):
        self.clear()
        self.fishPhoto.destroy()
        DirectFrame.destroy(self)
    

class FishPokerGui(FishPokerBase.FishPokerBase, DirectFrame):
    def __init__(self, lockCallback, cashInCallback):
        DirectFrame.__init__(self, parent=aspect2d, relief=None)
        self.initialiseoptions(FishPokerGui)
        self.setPos(0, 0, 0.8)
        self.setScale(0.7)
        self.lockCallback = lockCallback
        self.cashInCallback = cashInCallback

        self.__cardGuis = {}
        for i in range(self.NumSlots):
            card = FishPokerCard(i, self.toggleLock)
            card.reparentTo(self)
            card.setPos(-0.8 + i * 0.4, 0, 0)
            self.__cardGuis[i] = card

        guiButton = loader.loadModel("phase_3/models/gui/quit_button")
        self.cashInButton = DirectButton(
            parent=self,
            relief=None,
            image=(guiButton.find("**/QuitBtn_UP"),
                   guiButton.find("**/QuitBtn_DN"),
                   guiButton.find("**/QuitBtn_RLVR"),
                   ),
            image_scale=(1.5, 1.5, 2),
            text='',
            text_scale=0.06,
            text_pos=(0, 0.025),
            pos=(0, 0, -0.35),
            command=self.cashIn,
            )
        guiButton.removeNode()
        
        # Now update the base class, since it touched some of the
        # buttons on initialization
        FishPokerBase.FishPokerBase.__init__(self)

        self.updateCashIn()

    def updateCashIn(self):
        value, handName = self.getCurrentValue()
        self.cashInButton['text'] = TTLocalizer.FishPokerCashIn % (handName, value)

    def cashIn(self):
        # Gui will be update by the call to clear inside FishPokerBase
        result = FishPokerBase.FishPokerBase.cashIn(self)
        # Call back to the pond's mgr, which sends the update to the AI
        self.cashInCallback(result)
        return result

    def toggleLock(self, index):
        if self.isLocked(index):
            self.setLockStatus(index, 0)
        else:
            self.setLockStatus(index, 1)

    def setLockStatus(self, index, lockStatus):
        result = FishPokerBase.FishPokerBase.setLockStatus(self, index, lockStatus)
        # Update the gui
        self.__cardGuis[index].setLockStatus(lockStatus)
        # Call back to the pond's mgr, which sends the update to the AI
        self.lockCallback(index, lockStatus)
        return result

    def drawRandomCard(self):
        itemType, genus, species, weight = FishGlobals.getRandomFishVitals(base.localAvatar.zoneId,
                                                                           base.localAvatar.getFishingRod())
        self.drawCard(genus, species, weight)

    def drawCard(self, genus, species, weight):
        card = FishBase(genus, species, weight)
        index = FishPokerBase.FishPokerBase.drawCard(self, card)
        if index != -1:
            self.__cardGuis[index].update(card, 0)
        self.updateCashIn()
        return index

    def destroy(self):
        self.clear()
        DirectFrame.destroy(self)

    def clear(self):
        FishPokerBase.FishPokerBase.clear(self)
        # Update the gui
        for cardGui in self.__cardGuis.values():
            cardGui.clear()
        # Update value
        self.updateCashIn()
