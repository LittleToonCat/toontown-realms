from direct.directnotify import DirectNotifyGlobal
from direct.gui.DirectGui import *
from direct.fsm import StateData

from panda3d.core import *

from toontown.toonbase import ToontownGlobals, ClientSettings
from toontown.toonbase import TTLocalizer

from . import TeleportGUI, ToontownGUIUtils
from . import SavedDNAGUI
from .AnimatedButton import AnimatedButton


class MagicMenu(DirectFrame, StateData.StateData):
    notify = DirectNotifyGlobal.directNotify.newCategory('MagicMenu')
    menuModel = loader.loadModel('phase_3.5/models/gui/ttoff_m_gui_hud_magicMenu')

    def __init__(self):
        DirectFrame.__init__(self, parent=aspect2d, relief=None,
                             image=MagicMenu.menuModel.find('**/magicmenu_bg'), scale=0.2,
                             image_scale=(2.9, 1, 1), image_pos=(0, 0, .8),
                             borderWidth=(0.01, 0.01))
        StateData.StateData.__init__(self, 'magic-menu-done')
        self.isLoaded = False
        self.setBin('gui-popup', 0)
        self.initialiseoptions(MagicMenu)

        self.teleportInterface = None
        self.savedDNAInterface = None

        self.noticeLabel = None
        self.buttons = []
        self.icons = []
        self.closeButton = None
        self.actionButton = None

        self.enterInvalidMode()

    def unload(self):
        # Set loaded status to false
        if not self.isLoaded:
            return
        self.isLoaded = False

        self.teleportInterface.unload()
        self.teleportInterface = None

        self.savedDNAInterface.unload()
        self.savedDNAInterface = None

        # Exit out before we unload anything
        self.exit()

        # Allow parent class to do everything else
        DirectFrame.destroy(self)

    def load(self):
        # Set loaded status to true
        if self.isLoaded:
            return
        self.isLoaded = True

        # Load the individual sub-interfaces
        self.loadInterfaces()

        # A label that pops up to give notices
        self.noticeLabel = DirectLabel(parent=self, relief=None, scale=0.6, pos=(0.0, 0.0, -0.725),
                                       text='', text_scale=0.12, text_pos=(0, 0.6), text_wordwrap=22)

        # Buttons in the Magic Menu that do stuff

        iconModels = loader.loadModel('phase_3.5/models/gui/sos_textures')

        teleportIcon = iconModels.find('**/teleportIcon')
        blotIcon = MagicMenu.menuModel.find('**/magicmenu_blot')
        kartIcon = MagicMenu.menuModel.find('**/magicmenu_kart')


        propIconTexture = loader.loadTexture('phase_3.5/maps/prop_icon.png')
        propIcon = OnscreenImage(image=propIconTexture)
        propIcon.setTransparency(TransparencyAttrib.MAlpha)

        self.tpButton = AnimatedButton(
                image = teleportIcon,
                scale = 0.4, parent = self,
                pos = (-0.9, 0, 0.95),
                text=('', '', TTLocalizer.MagicMenuButton_1, ''),
                text_align = TextNode.ACenter,
                text_scale = 0.6,
                text_fg = (1.0, 1.0, 1.0, 1.0),
                text_shadow = (0, 0, 0, 0.7),
                text_pos = (0, 1),
                textMayChange = 0,
                command=self.handleButton, extraArgs=[ToontownGlobals.MagicMenuTeleportMenu])

        self.propGenButton = AnimatedButton(
                image = propIcon,
                scale = 0.4, parent = self,
                pos = (-.3, 0, 0.95),
                image_scale = 0.5,
                text=('', '', TTLocalizer.MagicMenuButton_2, ''),
                text_align = TextNode.ACenter,
                text_scale = 0.6,
                text_fg = (1.0, 1.0, 1.0, 1.0),
                text_shadow = (0, 0, 0, 0.7),
                text_pos = (0, 1),
                textMayChange = 0,
                command=self.handleButton, extraArgs=[ToontownGlobals.MagicMenuPropGenerator])

        self.buildLotButton = AnimatedButton(
                image = blotIcon,
                scale = 0.4, parent = self,
                pos = (.3, 0, 0.95),
                text=('', '', TTLocalizer.MagicMenuButton_BuildLot, ''),
                text_align = TextNode.ACenter,
                text_scale = 0.6,
                text_fg = (1.0, 1.0, 1.0, 1.0),
                text_shadow = (0, 0, 0, 0.7),
                text_pos = (0, 1),
                textMayChange = 0,
                command=self.handleButton, extraArgs=[ToontownGlobals.MagicMenuBuildLots])

        self.kartButton = AnimatedButton(
                image = kartIcon,
                scale = 0.4, parent = self,
                pos = (.9, 0, 0.95),
                text=('', '', TTLocalizer.MagicMenuButton_3, ''),
                text_align = TextNode.ACenter,
                text_scale = 0.6,
                text_fg = (1.0, 1.0, 1.0, 1.0),
                text_shadow = (0, 0, 0, 0.7),
                text_pos = (0, 1),
                textMayChange = 1,
                command=self.handleButton, extraArgs=[ToontownGlobals.MagicMenuMountKart])

        # An extra button to perform an action for whatever "mode" the player is in
        self.actionButton = DirectButton(parent=self, relief=None, text=TTLocalizer.MagicMenuActionButton, pos=(0.0, 0.0, -0.1), scale=1.5,

                                         image_scale=(1, 1, 1), text_scale=0.05, text_pos=TTLocalizer.DSDcancelPos,
                                         command=self.handleActionButton)
        self.actionButton.hide()

        iconModels.removeNode()
        propIcon.destroy()

        self.hide()
        self.accept('toon-caged', self.exit)

    def loadInterfaces(self):
        # Teleport Interface
        self.teleportInterface = TeleportGUI.TeleportGUI()
        self.teleportInterface.hide()

        # Saved DNA Interface
        self.savedDNAInterface = SavedDNAGUI.SavedDNAGUI()
        self.savedDNAInterface.hide()

    def enter(self):
        # If our UI is hidden, don't even bother trying to open the Magic Menu
        if aspect2d.isHidden():
            return

        # Set entered status to true
        if self.isEntered == 1:
            return
        self.isEntered = 1

        # If we haven't loaded yet, do so
        if self.isLoaded == 0:
            self.load()

        # Disable or enable the Prop Generator button based on whether one exists in the zone
        button = self.propGenButton
        if hasattr(base.cr, 'propGenerator') and base.cr.propGenerator:
            button.setColorScale(1.0, 1.0, 1.0, 1.0)
        else:
            button.setColorScale(0.5, 0.5, 0.5, 1.0)

        self.adjustKartButton()

        # Show the interface
        self.show()

        self.accept(base.localAvatar.uniqueName('hpChange'), self.adjustKartButton)

        if ClientSettings.GUIAnimations.get():
            ToontownGUIUtils.Animations.popup(self, self.getScale()).start()

    def exit(self):
        # Set entered status to false
        if self.isEntered == 0:
            return
        self.isEntered = 0

        # Ignore all events
        self.ignoreAll()

        # Hide the interface
        self.hide()
        self.ignore(base.localAvatar.uniqueName('hpChange'))

    def getTeleportInterface(self):
        if not self.isLoaded:
            return None

        if not self.teleportInterface:
            return None

        return self.teleportInterface

    def getSavedDNAInterface(self):
        if not self.isLoaded:
            return None

        if not self.savedDNAInterface:
            return None

        return self.savedDNAInterface

    def handleButton(self, index):
        if not base.localAvatar.tutorialAck:
            return
        if index == ToontownGlobals.MagicMenuTeleportMenu:
            # Exit the Magic Menu interface
            self.exit()

            # Open the teleport interface
            self.teleportInterface.enter()
        elif index == ToontownGlobals.MagicMenuPropGenerator:
            # Open the prop generator interface if there is one in the zone
            if hasattr(base.cr, 'propGenerator') and base.cr.propGenerator:
                # Exit the Magic Menu interface
                self.exit()

                # Open the interface
                base.cr.propGenerator.openNewPropWindow()
            else:
                self.displayNotice(TTLocalizer.MagicMenuNoPropGenerator)
        elif index == ToontownGlobals.MagicMenuMountKart:
            # If no kart, pop up a notice saying they don't have a kart
            if not base.localAvatar.hasKart():
                self.displayNotice(TTLocalizer.MagicMenuNoKart)
            # Can't enter kart if laff is too low
            elif base.localAvatar.getHp() <= 10:
                self.displayNotice(TTLocalizer.HoldKartLowLaffMessage)
            # Some places don't allow karts
            elif not base.localAvatar.canRaceHere():
                self.displayNotice(TTLocalizer.HoldKartCantRaceHereMessage)
            # Can't enter a kart during hide and seek
            elif hasattr(base.cr, 'hideAndSeekGame') and base.cr.hideAndSeekGame.isActive():
                self.displayNotice(TTLocalizer.MagicMenuKartHideAndSeek)
            else:
                # Get in the Toon's kart if they have one

                # Exit the Magic Menu interface
                self.exit()

                # Getting in
                base.localAvatar.startupKart()
                self.enterKartMode()

        elif index == ToontownGlobals.MagicMenuBossParty:
            if not hasattr(base.cr, 'bossPartyManager') or not base.cr.bossPartyManager:
                # No boss party manager (this shouldn't happen under normal circumstances
                # but just in case)
                self.displayNotice(TTLocalizer.MagicMenuNoBossPartyManager)
            else:
                if base.cr.bossPartyManager.getCurrentOrNextState() in ('Start', 'Done'):
                    # Boss party already exists
                    self.displayNotice(TTLocalizer.BossPartyCreateError + TTLocalizer.BossPartyErrorBossParty)
                else:
                    # Boss party was created
                    self.exit()
                    base.cr.bossPartyManager.setState('Planning')
                    base.localAvatar.setLocked(True, ToontownGlobals.LockedStateMessengerExemption)
        elif index == ToontownGlobals.MagicMenuBuildLots:
            self.exit()
            base.cr.buildLotMgr.showList()

    def adjustKartButton(self, hp = 0, maxHp = 0, quietly = 0):
        # Disable or enable the Mount Kart button based on whether you can mount a kart in the zone
        button = self.kartButton
        if base.localAvatar.canRaceHere():
            button.setColorScale(1.0, 1.0, 1.0, 1.0)
        else:
            button.setColorScale(0.5, 0.5, 0.5, 1.0)

    def enterInvalidMode(self):
        self.mode = ToontownGlobals.MagicMenuInvalid

    def isInvalidMode(self):
        return self.mode == ToontownGlobals.MagicMenuInvalid

    def enterKartMode(self):
        self.kartButton.reparentTo(base.a2dBottomRight)
        if hasattr(self.kartButton, 'activeAnim') and self.kartButton.activeAnim != None:
            self.kartButton.activeAnim.finish()
        self.kartButton.setPos(-0.58, 0, 0.05)
        self.kartButton.scale = 0.1
        self.kartButton.setScale(0.1)
        self.kartButton['command'] = self.handleActionButton
        self.kartButton['extraArgs'] = []
        self.kartButton['text'] = ('', '', TTLocalizer.MagicMenuDismountButton, '')

        # Set the mode
        self.mode = ToontownGlobals.MagicMenuMountKart

    def exitKartMode(self):
        self.kartButton.reparentTo(self)
        if hasattr(self.kartButton, 'activeAnim') and self.kartButton.activeAnim != None:
            self.kartButton.activeAnim.finish()
        self.kartButton.setPos(0.9, 0, 0.95)
        self.kartButton.scale = 0.4
        self.kartButton.setScale(0.4)
        self.kartButton['command'] = self.handleButton
        self.kartButton['extraArgs'] = [2]
        self.kartButton['text'] = ('', '', TTLocalizer.MagicMenuButton_3, '')

        # Set the mode
        self.enterInvalidMode()

    def enterDisabledMode(self):
        self.mode = ToontownGlobals.MagicMenuDisabled

    def isDisabledMode(self):
        return self.mode == ToontownGlobals.MagicMenuDisabled

    def exitDisabledMode(self):
        self.enterInvalidMode()

    def handleActionButton(self):
        if self.mode == ToontownGlobals.MagicMenuMountKart:
            base.localAvatar.startupKart()
            self.exitKartMode()

            # Pressing the exit button while in kart mode obscures the friends list button
            # so we might have to manually show it
            if base.localAvatar.friendsListButtonObscured:
                base.localAvatar.obscureFriendsListButton(-1)

            self.exit()

    def displayNotice(self, text):
        self.noticeLabel.setText(text)
        self.noticeLabel.show()

        taskMgr.remove(self.uniqueName('hideNotice'))
        taskMgr.doMethodLater(3.0, self.hideNotice, self.uniqueName('hideNotice'), extraArgs=[])

    def hideNotice(self):
        self.noticeLabel.setText('')
        self.noticeLabel.hide()
