from direct.gui import DirectGuiGlobals
from panda3d.core import *
from direct.directnotify import DirectNotifyGlobal
from direct.gui.DirectGui import *
from direct.fsm import StateData
from toontown.toonbase import ToontownGlobals, ClientSettings
from toontown.toonbase import TTLocalizer
from toontown.spellbook.MagicWordIndex import *
from toontown.toontowngui import ToontownGUIUtils
from toontown.toontowngui.AnimatedButton import AnimatedButton


class TeleportGUI(DirectFrame, StateData.StateData):
    notify = DirectNotifyGlobal.directNotify.newCategory('TeleportGUI')

    def __init__(self):
        DirectFrame.__init__(self, parent = aspect2d, relief = None, image = DGG.getDefaultDialogGeom(),
                             pos = (0.0, 0.0, 0.05),
                             image_scale = (1.8, 1, 1.4), image_pos = (0, 0, -0.05),
                             image_color = ToontownGlobals.GlobalDialogColor, text = TTLocalizer.TeleportGUITitle,
                             text_scale = 0.12, text_pos = (0, 0.5), borderWidth = (0.01, 0.01))
        StateData.StateData.__init__(self, 'teleport-gui-done')
        self.isLoaded = False
        self.setBin('gui-popup', 0)
        self.initialiseoptions(TeleportGUI)

        self.mode = ToontownGlobals.TeleportInterfaceModeMagicMenu

        self.textRolloverColor = Vec4(1, 1, 0, 1)
        self.textDownColor = Vec4(0.5, 0.9, 1, 1)
        self.textDisabledColor = Vec4(0.4, 0.8, 0.4, 1)

    def unload(self):
        if not self.isLoaded:
            return
        self.isLoaded = False
        self.exit()
        DirectFrame.destroy(self)

    def load(self):
        if self.isLoaded:
            return
        self.isLoaded = True

        self.zones = {}  # type: dict[int, str]
        self.iconButtons = []  # type: list[AnimatedButton]

        teleportZones = []
        zonesForTeleport = list(ToontownGlobals.hood2Id.keys())
        for zone in zonesForTeleport:
            if zone in ToontownGlobals.hoodExemptions:
                continue
            zoneInfo = (zone, ToontownGlobals.hood2Id.get(zone)[0])
            if zoneInfo not in teleportZones:
                teleportZones.append(zoneInfo)

        for zone in teleportZones:
            zoneId = zone[0]
            zoneText = TTLocalizer.GlobalStreetNames.get(zoneId, '???')[2]
            if zoneText == 'Playground':
                zoneText = ToontownGlobals.hoodNameMap.get(zoneId, '???')[2]
            if ZoneUtil.isBetaPlaygroundZone(zoneId) and ZoneUtil.isPlayground(zoneId):
                zoneText = zoneText + TTLocalizer.BetaSuffix
            self.zones[zone[0]] = zoneText
        gui = loader.loadModel('phase_3.5/models/gui/friendslist_gui')  # type: NodePath
        guiButton = loader.loadModel('phase_3/models/gui/quit_button')  # type: NodePath
        guiClose = loader.loadModel('phase_3.5/models/gui/avatar_panel_gui')  # type: NodePath
        guiIcons = loader.loadModel('phase_3/models/gui/ttoff_m_gui_mgmn_teleport_icons')  # type: NodePath

        def makeButton(zone):  # type: (str) -> AnimatedButton
            zoneString = f'zone_{zone}'
            if zone in ('19000', '19100'):
                zoneString += '_tt'
            btn = AnimatedButton(
                    relief = None,
                    parent = self,
                    image = guiIcons.find('**/' + zoneString),
                    scale = 0.2,
                    pressEffect = False,
                    text_fg = (1.0, 1.0, 1.0, 1.0),
                    text_style = 3,
                    command = self.__handleTeleport, extraArgs = [zone]
            )
            btn.bind(DirectGuiGlobals.WITHIN, lambda e: self.selectZone(int(zone)))
            return btn

        pos = Vec3(-0.6, 0, 0.36)
        for i in range(len(self.zones)):
            btn = makeButton(str(list(self.zones.keys())[i]))
            btn.setPos(pos)
            # Offset the position for the next item
            pos.addX(0.2)
            # Every 7 items we switch to a new row
            if not (i + 1) % 7:
                if i == 20:
                    # little hack to get the bottom row centered
                    pos.setX(-0.4)
                else:
                    pos.setX(-0.6)
                pos.addZ(-0.2)
            self.iconButtons.append(btn)
        self.cancel = DirectButton(
                parent = self,
                relief = None,
                image = (guiClose.find('**/CloseBtn_UP'),
                         guiClose.find('**/CloseBtn_DN'),
                         guiClose.find('**/CloseBtn_Rllvr'),
                         guiClose.find('**/CloseBtn_UP')),
                pos = (0.78, 0, -0.65),
                scale = 1.5,
                command = self.exit
        )
        self.zoneLabel = DirectLabel(
                parent = self,
                relief = None,
                text = '',
                text_scale = 0.05,
                text_pos = TTLocalizer.DSDcancelPos,
                pos = (0, 0, -0.45),
                scale = 1.5
        )

        self.zoneDescription = DirectLabel(
                parent = hidden,
                relief = None,
                text = '',
                text_scale = 0.03,
                text_pos = TTLocalizer.DSDcancelPos,
                text_align = TextNode.ACenter,
                text_wordwrap = 30.0,
                pos = (0.0, 0, -0.52),
                scale = 1.5
        )
        gui.removeNode()
        guiButton.removeNode()
        guiClose.removeNode()
        guiIcons.removeNode()
        self.hide()

        self.accept('toon-caged', self.exit)

    def enter(self, mode = ToontownGlobals.TeleportInterfaceModeMagicMenu):
        if self.isEntered == 1:
            return
        self.isEntered = 1

        # Lock the Toon down
        base.localAvatar.setLocked(True)

        if self.isLoaded == 0:
            self.load()

        # The way we cancel out of the interface is different depending on how we entered it
        self.mode = mode

        # If we entered via the Magic Menu, no need to dim the screen
        # if self.mode != ToontownGlobals.TeleportInterfaceModeMagicMenu:
        base.transitions.fadeScreen(0.5)

        self.show()

        if ClientSettings.GUIAnimations.get():
            ToontownGUIUtils.Animations.popup(self, self.getScale()).start()

        if base.cr.playGame.getPlace().getState() != 'battle':
            base.cr.playGame.getPlace().setState('stopped')

    def exit(self):
        if self.isEntered == 0:
            return
        self.isEntered = 0

        # Unlock the Toon
        if base.cr.playGame.getPlace().getState() == 'battle':
            # Don't allow the Toon to move around if in battle
            exception = ToontownGlobals.LockedStateFlagChangeOnly

            base.cr.playGame.getPlace().setState('walk')
        else:
            exception = 0
        base.localAvatar.setLocked(False, exception)

        # If we entered via the Magic Menu, keep the screen dimmed
        # if self.mode != ToontownGlobals.TeleportInterfaceModeMagicMenu:
        base.transitions.noTransitions()

        self.ignoreAll()
        self.hide()

    def selectZone(self, zone):  # type: (int) -> None
        # Wakeup the Toon
        messenger.send('wakeup')

        # Change the label above the thumbnail to our selected zone
        self.zoneLabel['text'] = self.zones[zone]

        # If we have a zone description, show it
        if zone in list(ToontownGlobals.hoodDescriptions.keys()):
            description = ToontownGlobals.hoodDescriptions.get(zone)
            self.zoneDescription['text'] = description
            self.zoneDescription.reparentTo(self)
        else:
            self.zoneDescription['text'] = ''
            self.zoneDescription.reparentTo(hidden)

    def __handleTeleport(self, zone):  # type: (int) -> None
        self.exit()

        if base.localAvatar.getTransitioning():
            return
        elif base.cr.legitMode:
            return

        base.localAvatar.doTeleport(zone)
