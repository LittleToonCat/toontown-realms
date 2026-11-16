from panda3d.core import TextNode
from direct.gui.DirectGui import DirectFrame, DirectLabel, OnscreenImage, DirectButton
from otp.avatar.AvatarPanel import AvatarPanel
from toontown.social import SocialMenu
from toontown.suit import SuitDNA
from toontown.toonbase import TTLocalizer, ToontownGlobals


class LawbotArenaLawyerInterface(AvatarPanel):
    def __init__(self, avatar, boss):
        AvatarPanel.__init__(self, avatar, socialMenu = SocialMenu)
        self.boss = boss
        self.buttons = []

        # Lawyer Frame
        gui = loader.loadModel('phase_3.5/models/gui/suit_detail_panel')
        self.frame = DirectFrame(parent=base.a2dTopRight, frameColor=(.9, .9, .9, 1), frameSize=(-1, 1, -1, 1),
                                 pos=(-0.25, 0.0, -0.45), scale=.09, geom=gui.find('**/avatar_panel'),
                                 geom_scale=(2.2, 1, 2.2))
        gui.removeNode()

        # Level & Exp Labels
        self.lawyerLevel = DirectLabel(parent=self.frame, relief=None, pos=(0.0, 0.0, -6.25), scale=0.625,
                                       text=TTLocalizer.TownBattleLevelText % 0,
                                       text_font=ToontownGlobals.getInterfaceFont(),
                                       text_fg=(1, 1, 1, 1))
        self.lawyerExp = DirectLabel(parent=self.frame, relief=None, pos=(0.0, 0.0, -7), scale=0.625,
                                     text=TTLocalizer.LawbotArenaToNextLevel % (0, 6),
                                     text_font=ToontownGlobals.getInterfaceFont(),
                                     text_fg=(1, 1, 1, 1))
        self.bonusWeight = DirectLabel(parent=self.frame, relief=None, pos=(0.0, 0.0, -5.5), scale=0.625,
                                       text=TTLocalizer.LawbotArenaBonusWeight % 0,
                                       text_font=ToontownGlobals.getInterfaceFont(), text_fg=(1, 1, 1, 1))
        self.closeButton = DirectButton(parent=self.frame, relief=None, pos=(0.0, 0, -4),
                                        text=TTLocalizer.AvatarPanelCogDetailClose, text_align=TextNode.ACenter,
                                        text_font=ToontownGlobals.getInterfaceFont(),
                                        text0_fg=(0.5, 0.5, 0.5, 1), text1_fg=(0.5, 0, 0, 1), scale=0.8,
                                        text2_fg=(1, 0, 0, 1), command=self.__handleClose)

        # Mode Buttons
        labels = (TTLocalizer.LawbotArenaAttackingBoth, TTLocalizer.LawbotArenaAttackingToon,
                  TTLocalizer.LawbotArenaAttackingBoss)
        for state in range(len(labels)):
            texture = loader.loadTexture('phase_11/maps/LB_Arena_Button_{}.png'.format(state + 1))
            texture = OnscreenImage(texture)
            texture.setTransparency(1)
            button = DirectButton(parent=self.frame, relief=None, image=texture,
                                  pos=(0.0, 0.0, 3 - (2.5 * state)),
                                  scale=1.15, text=('', labels[state]), text_font=ToontownGlobals.getInterfaceFont(),
                                  text_fg=(1, 1, 1, 1), text_pos=(-3.5, 0.0, 0.0), text_scale=0.5,
                                  command=self.changeLawyerMode, extraArgs=[state])
            self.buttons.append(button)
            texture.destroy()

            # Darken the two latter buttons to show they're disabled
            if state > 0:
                button.component('image0').setColorScale(0.5, 0.5, 0.5, 1.0)

            # "Hover" buttons should be nearly full brightness, but not quite
            button.component('image1').setColorScale(0.85, 0.85, 0.85, 1.0)

        self.show(avatar)

    def changeLawyerLevel(self, lawyer):
        # Set the level text
        level = lawyer.level
        levelText = TTLocalizer.TownBattleLevelText % level
        self.lawyerLevel['text'] = levelText

        # Set exp to next level text
        expText = TTLocalizer.LawbotArenaToNextLevel % (lawyer.currHP, lawyer.maxHp)
        self.lawyerExp['text'] = expText

        # Set bonus weight text
        self.updateLawyerDamage(lawyer)

    def updateLawyerDamage(self, lawyer=None):
        if not lawyer:
            lawyer = self.avatar

        damage = lawyer.level

        # If sudden death is active, increase the amount of exp given to a lawyer
        damage *= self.boss.suddenDealthMultiplier

        bonusText = TTLocalizer.LawbotArenaBonusWeight % round(damage, 2)

        # Just in case
        if self.bonusWeight:
            self.bonusWeight['text'] = bonusText

    def changeLawyerMode(self, state):
        lawyer = self.boss.activeLawyer
        if not lawyer:
            return

        if state != -1:
            self.boss.sendUpdate('setLawyerMode', [state, lawyer.getDoId()])
        else:
            state = lawyer.getMode()

        # Update the level and "exp" for our lawyer
        self.changeLawyerLevel(lawyer)

        # Reset all the button colors to half brightness
        for button in self.buttons:
            button.component('image0').setColorScale(0.5, 0.5, 0.5, 1.0)

        # Color the button for the mode our lawyer is currently in
        button = self.buttons[state]
        button.component('image0').setColorScale(1.0, 1.0, 1.0, 1.0)

    def show(self, lawyer):
        # Update the UI to match the info of this specific lawyer
        self.boss.activeLawyer = lawyer
        self.changeLawyerMode(ToontownGlobals.LawbotArenaInvalidMode)
        self.frame.show()

        # Explain how this works
        if not self.boss.foundLawyer:
            self.boss.lawyerTip()

        # Hide the right margins
        base.setCellsAvailable(base.rightCells, 0)

    def hide(self):
        # Hide the UI
        self.boss.activeLawyer = None
        self.frame.hide()

        # Show the right margins
        base.setCellsAvailable(base.rightCells, 1)

    def cleanup(self):
        if not self.frame:
            return
        self.hide()
        self.buttons = []
        self.frame.destroy()
        self.frame = None
        AvatarPanel.cleanup(self)

    def __handleClose(self):
        self.cleanup()
        AvatarPanel.currentAvatarPanel = None
