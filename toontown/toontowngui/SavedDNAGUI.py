from panda3d.core import *

from direct.directnotify import DirectNotifyGlobal
from direct.gui.DirectGui import *
from direct.fsm import StateData

from toontown.toon import Toon
from toontown.spellbook.MagicWordIndex import *

DIRECTION_LEFT = -1
DIRECTION_RIGHT = 1


class SavedDNAGUI(DirectFrame, StateData.StateData):
    notify = DirectNotifyGlobal.directNotify.newCategory('SavedDNAGUI')

    def __init__(self):
        DirectFrame.__init__(self, parent=aspect2d, relief=None, image=DGG.getDefaultDialogGeom(), pos=(0.0, 0.0, 0.05),
                             image_scale=(1.2, 1, 1.2), image_pos=(0, 0, -0.05),
                             image_color=ToontownGlobals.GlobalDialogColor, text=TTLocalizer.SavedDNAGUITitle,
                             text_scale=0.12, text_pos=(0, 0.4), borderWidth=(0.01, 0.01))
        StateData.StateData.__init__(self, 'teleport-gui-done')
        self.isLoaded = False
        self.setBin('gui-popup', 0)
        self.initialiseoptions(SavedDNAGUI)

        self.selectedDNA = -1
        self.availableDNA = None
        self.toon = None

        self.deleteMode = 0

    def unload(self):
        if not self.isLoaded:
            return
        self.isLoaded = False

        self.exit()

        if self.toon:
            self.toon.stopBlink()
            self.toon.stopLookAroundNow()
            self.toon.delete()
            self.toon = None

        DirectFrame.destroy(self)

    def load(self):
        if self.isLoaded:
            return
        self.isLoaded = True

        guiButton = loader.loadModel('phase_3/models/gui/quit_button')
        guiClose = loader.loadModel('phase_3.5/models/gui/avatar_panel_gui')
        matModel = loader.loadModel('phase_3/models/gui/tt_m_gui_mat_mainGui')
        arrow = [matModel.find('**/tt_t_gui_mat_shuffleArrow' + name) for name in ('Up', 'Down', 'Up', 'Disabled')]
        self.cancel = DirectButton(parent=self, relief=None,
                                   image=(guiClose.find('**/CloseBtn_UP'),
                                          guiClose.find('**/CloseBtn_DN'),
                                          guiClose.find('**/CloseBtn_Rllvr'),
                                          guiClose.find('**/CloseBtn_UP')),
                                   pos=(0.5, 0, -0.55), scale=1.5, command=self.exit)
        self.select = DirectButton(parent=self, relief=None, text=TTLocalizer.SavedDNAGUISelect,
                                   image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')),
                                   image_scale=(0.7, 1, 1), text_scale=TTLocalizer.CSButton,
                                   text_pos=TTLocalizer.DSDcancelPos, pos=(0, 0, -0.55), scale=1.1, command=self.selectDNA)
        self.leftButton = DirectButton(self, relief=None, image_scale=0.7, image=arrow, pos=(-0.3550, 0.0, -0.2925),
                                       scale=1.2, command=self.advanceDNA, extraArgs=[DIRECTION_LEFT])
        self.rightButton = DirectButton(self, relief=None, image_scale=(-0.7, 1, 0.7), image=arrow, pos=(0.3550, 0, -0.2925),
                                        scale=1.2, command=self.advanceDNA, extraArgs=[DIRECTION_RIGHT])
        guiButton.removeNode()
        guiClose.removeNode()
        matModel.removeNode()
        self.hide()

        self.accept('toon-caged', self.exit)

    def enter(self, dna):
        if self.isEntered == 1:
            return
        self.isEntered = 1

        # Lock the Toon down
        base.localAvatar.setLocked(True)

        if self.isLoaded == 0:
            self.load()

        if self.deleteMode:
            self.select['text'] = TTLocalizer.SavedDNAGUIRemove
        else:
            self.select['text'] = TTLocalizer.SavedDNAGUISelect

        base.transitions.fadeScreen(0.5)

        self.availableDNA = dna
        self.selectedDNA = -1
        self.advanceDNA()

        self.show()

    def exit(self):
        if self.isEntered == 0:
            return
        self.isEntered = 0

        # Unlock the Toon down
        base.localAvatar.setLocked(False)

        base.transitions.noTransitions()

        self.ignoreAll()
        self.hide()

    def setDeleteMode(self, deleteMode):
        self.deleteMode = deleteMode

    def advanceDNA(self, direction=DIRECTION_RIGHT):
        # Wakeup the Toon
        messenger.send('wakeup')

        self.selectedDNA += direction

        maxIndex = len(self.availableDNA) - 1
        if self.selectedDNA <= -1:
            self.selectedDNA = maxIndex
        elif self.selectedDNA > maxIndex:
            self.selectedDNA = 0

        dna = self.verifyDNA(self.availableDNA[self.selectedDNA])
        if not dna:
            return

        if self.toon:
            self.toon.stopBlink()
            self.toon.stopLookAroundNow()
            self.toon.delete()

        self.toon = Toon.Toon()
        dna = ToonDNA.ToonDNA(dna)
        self.toon.setDNA(dna)
        self.toon.setPos(0, 0, -0.4)
        self.toon.setHpr(180, 0, 0)
        self.toon.setScale(0.2)
        self.toon.setDepthTest(True)
        self.toon.setDepthWrite(True)
        self.toon.loop('neutral')
        self.toon.reparentTo(self)

    def selectDNA(self):
        self.exit()

        if base.localAvatar.getTransitioning():
            return
        elif base.cr.legitMode:
            return

        if self.deleteMode:
            del self.availableDNA[self.selectedDNA]
            base.settings.updateSetting('game', 'saved-dna', self.availableDNA)
        else:
            dna = self.verifyDNA(self.availableDNA[self.selectedDNA])
            base.localAvatar.updateDNA(dna=dna, spellbook=False)

    def verifyDNA(self, dna):
        dna = dna.encode()
        dna = base64.b64decode(dna)

        valid = ToonDNA.ToonDNA().isValidNetString(dna)
        if not valid:
            return False

        return dna
