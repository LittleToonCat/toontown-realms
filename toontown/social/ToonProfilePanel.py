from typing import Optional

from direct.gui import DirectGuiGlobals
from panda3d.core import *
from direct.gui.DirectGui import *
from direct.interval.IntervalGlobal import *
from direct.fsm.FSM import FSM
from direct.showbase import DirectObject

from otp.otpbase.PythonUtil import bound
from otp.otpgui import OTPGUIUtils
from toontown.toon import Toon
from toontown.toon import LaffMeter
from otp.avatar import Avatar
from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownBattleGlobals
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from toontown.social import ToontownFriendSecret
from toontown.social import ProfilePanelBase
from toontown.social.ToonProfilePoses import ProfilePoses
from toontown.toon import DistributedToon
from toontown.toontowngui.AnimatedButton import AnimatedButton
from toontown.toontowngui import TTDialog
from otp.otpbase import OTPGlobals

import random


# todo: why won't this drag looool
class ToonProfileDetailPanel(DirectFrame, FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToonProfileDetailPanel')
    gui = loader.loadModel('phase_3.5/models/gui/ttrm_m_gui_soc_toonAvatarPanel', allowInstance = True)
    starGui = loader.loadModel('phase_3.5/models/gui/ttrm_m_gui_nameStar', allowInstance = True)
    defaultTransitions = {
        'Off': ['Begin'],
        'Begin': ['Query', 'Data', 'Off'],
        'Query': ['Data', 'Invalid', 'Off'],
        'Data': ['Off', 'Begin'],
        'Invalid': ['Off', 'Begin']
    }

    def __init__(self, profileInst, parent: NodePath, avId: int, avName: str, **kw):
        gui = loader.loadModel('phase_3.5/models/gui/ttrm_m_gui_soc_toonAvatarPanel')
        detailPanel = self.gui.find('**/detailpanel')
        optiondefs = (
            ('relief', None, None),
            ('image_scale', OTPGUIUtils.getImageScale(931, 1156, 1.4), None),
            ('pos', (-0.96, 100, 0), None),
            ('state', DGG.NORMAL, None),
        )
        self.defineoptions(kw, optiondefs)
        DirectFrame.__init__(self, parent)
        self['image'] = detailPanel
        FSM.__init__(self, 'ToonProfileDetailPanel')

        self.profileInst = profileInst
        self.avId = avId
        self.avName = avName
        self.avatar: Optional[Avatar] = None
        self.createdAvatar = None
        self.trackInfo = {}
        self.star: Optional[DirectLabel] = None
        self.starSpeed = 0

        self.dataText = DirectLabel(
                parent = self,
                relief = None,
                pos = (-0.43, 0, 0.525),
                text = '',
                text_scale = 0.06,
                text_fg = (0.95, 0.95, 0.95, 1),
                text_align = TextNode.ALeft,
                text_wordwrap = 13)

        self.exitButton = DirectButton(
                parent = self,
                image = (
                    self.gui.find('**/collapsebutton_n'),
                    self.gui.find('**/collapsebutton_d'),
                    self.gui.find('**/collapsebutton_h'),
                    self.gui.find('**/collapsebutton_d')),
                image_scale = OTPGUIUtils.getImageScale(85, 265, 0.3),
                relief = None,
                text = ('', '', TTLocalizer.AvatarPanelExitDetail, ''),
                text_fg = Vec4(1, 1, 1, 1),
                text_shadow = (0, 0, 0, 1),
                text_scale = 0.055,
                text_pos = (0, -0.2),
                text_align = TextNode.ACenter,
                pos = (-0.554, 0, -0.45),
                command = self.exit)

    def exit(self):
        self.hide()
        self.removeTask('profileStarSpin')
        self.profileInst.detailButton.show()

    def cleanup(self):
        if self.state != 'Off':
            self.demand('Off')
            base.cr.cancelAvatarDetailsRequest(self.avatar)
        if self.createdAvatar:
            self.avatar.delete()
            self.createdAvatar = None
        self.removeTask('profileStarSpin')
        self.destroy()

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    def enterBegin(self):
        if self.avId == base.localAvatar.doId:
            self.avatar = base.localAvatar
            self.createdAvatar = 0
            self.demand('Data')
        else:
            self.demand('Query')

    def exitBegin(self):
        pass

    def enterQuery(self):
        self.dataText['text'] = TTLocalizer.AvatarDetailPanelLookup % self.avName
        self.avatar = base.cr.doId2do.get(self.avId)
        if self.avatar != None and not self.avatar.ghostMode:
            self.createdAvatar = 0
        else:
            self.avatar = DistributedToon.DistributedToon(base.cr)
            self.createdAvatar = 1
            self.avatar.doId = self.avId
            self.avatar.forceAllowDelayDelete()
        base.cr.getAvatarDetails(self.avatar, self.__handleAvatarDetails, 'DistributedToon')

    def exitQuery(self):
        pass

    def enterData(self):
        self.__showData()

    def exitData(self):
        pass

    def enterInvalid(self):
        self.dataText['text'] = TTLocalizer.AvatarDetailPanelFailedLookup % self.avName

    def exitInvalid(self):
        pass

    def __handleAvatarDetails(self, gotData: bool, avatar: Avatar, dclass):
        if avatar != self.avatar:
            self.notify.warning('Ignoring unexpected request for avatar %s' % avatar.doId)
            return
        if gotData:
            self.demand('Data')
        else:
            self.demand('Invalid')

    def __showData(self):
        av = self.avatar
        online = base.cr.getAvatarVisibility(
                self.avId,
                forceVisibility = self.avId in base.cr.doId2do and base.cr.doId2do[self.avId].ghostMode != 2
        )
        if online:
            shardName = base.cr.getShardName()
            hoodName = base.cr.hoodMgr.getFullnameFromId(av.lastHood)
            accessLvl = base.localAvatar.getAccessLevel()
            moderatorAccess = OTPGlobals.AccessLevelName2Int['MODERATOR']
            if accessLvl >= moderatorAccess:
                text = TTLocalizer.AvatarDetailPanelOnlineModerator % {'location': hoodName,
                                                                       'avId': av.doId,
                                                                       'zoneId': av.lastZone
                                                                       }
            else:
                text = TTLocalizer.AvatarDetailPanelOnline % {'location': hoodName}
        else:
            text = TTLocalizer.AvatarDetailPanelOffline % {'avId': av.doId}
        self.dataText['text'] = text
        self.__updateTrackInfo()
        self.__updateTrophyInfo()
        self.__updateLaffInfo()

    def __updateLaffInfo(self):
        avatar = self.avatar
        messenger.send('updateLaffMeter', [avatar, avatar.hp, avatar.maxHp])

    def __updateTrackInfo(self):
        xOffset = -0.3675
        xSpacing = 0.1224
        yOffset = 0.105
        ySpacing = -0.0925
        inventory = self.avatar.inventory
        buttonModel = self.gui.find('**/panel_inventory_button')

        track2Gags = {}
        i = 0
        for track in range(0, len(ToontownBattleGlobals.Tracks)):
            if self.avatar.hasTrackAccess(track):
                curExp, nextExp = inventory.getCurAndNextExpValues(track)
                for item in range(0, len(ToontownBattleGlobals.Levels[track])):
                    level = ToontownBattleGlobals.Levels[track][item]
                    if curExp >= level:
                        numItems = inventory.numItem(track, item)
                        if numItems == 0:
                            image_color = Vec4(0.5, 0.5, 0.5, 1)
                            geom_color = Vec4(0.2, 0.2, 0.2, 0.5)
                        else:
                            image_color = Vec4(0, 0.6, 1, 1)
                            geom_color = Vec4(1, 1, 1, 1)
                        if i in self.trackInfo:
                            self.trackInfo[i]['image_color'] = image_color
                            self.trackInfo[i]['geom_color'] = geom_color
                            self.trackInfo[i]['text'] = '' if not numItems else str(numItems)
                        else:
                            self.trackInfo[i] = (
                                DirectLabel(
                                        parent = self,
                                        image = buttonModel,
                                        image_scale = OTPGUIUtils.getImageScale(88, 63, 0.075),
                                        image_color = image_color,
                                        geom = base.localAvatar.inventory.invModels[track][item],
                                        geom_color = geom_color,
                                        geom_scale = 0.525,
                                        text = '' if not numItems else str(numItems),
                                        text_scale = 0.04,
                                        text_pos = (0.04, -0.0295),
                                        text_fg = Vec4(0.95, 0.95, 0.95, 1),
                                        text_shadow = Vec4(0, 0, 0, 1),
                                        text_align = TextNode.ARight,
                                        relief = None,
                                        pos = (xOffset + item * xSpacing, 0, yOffset + track * ySpacing)
                                )
                            )
                        if track not in track2Gags:
                            track2Gags[track] = []
                        track2Gags[track].append(self.trackInfo[i])
                        i += 1
                    else:
                        # exp was lowered
                        # so lets continue looping through this track and remove the remaining track info
                        if i in self.trackInfo:
                            self.trackInfo[i].removeNode()
                            del self.trackInfo[i]
                            i += 1
                            continue
                        i += len(ToontownBattleGlobals.Levels[track]) - level
                        break

        for track, gags in list(track2Gags.items()):
            OTPGUIUtils.Animations.staggeredPopUp(gags)
        del track2Gags

    def __updateTrophyInfo(self):
        if self.avatar.trophyScore >= ToontownGlobals.TrophyStarLevels[6]:
            starImage = self.starGui.find('**/star_diamond')
            color = ToontownGlobals.TrophyStarColors[2]
            if self.avatar.trophyScore >= ToontownGlobals.TrophyStarLevels[7]:
                self.starSpeed = ToontownGlobals.TrophyStarSpeed[7]
            else:
                self.starSpeed = ToontownGlobals.TrophyStarSpeed[4]
        elif self.avatar.trophyScore >= ToontownGlobals.TrophyStarLevels[4]:
            starImage = self.starGui.find('**/star_normal')
            color = ToontownGlobals.TrophyStarColors[4]
            if self.avatar.trophyScore >= ToontownGlobals.TrophyStarLevels[5]:
                self.starSpeed = ToontownGlobals.TrophyStarSpeed[5]
            else:
                self.starSpeed = ToontownGlobals.TrophyStarSpeed[4]
        elif self.avatar.trophyScore >= ToontownGlobals.TrophyStarLevels[2]:
            starImage = self.starGui.find('**/star_normal')
            color = ToontownGlobals.TrophyStarColors[2]
            if self.avatar.trophyScore >= ToontownGlobals.TrophyStarLevels[3]:
                self.starSpeed = ToontownGlobals.TrophyStarSpeed[3]
            else:
                self.starSpeed = ToontownGlobals.TrophyStarSpeed[2]
        elif self.avatar.trophyScore >= ToontownGlobals.TrophyStarLevels[1]:
            starImage = self.starGui.find('**/star_normal')
            color = ToontownGlobals.TrophyStarColors[1]
            self.starSpeed = ToontownGlobals.TrophyStarSpeed[1]
        elif self.avatar.trophyScore >= ToontownGlobals.TrophyStarLevels[0]:
            starImage = self.starGui.find('**/star_normal')
            color = ToontownGlobals.TrophyStarColors[0]
            self.starSpeed = ToontownGlobals.TrophyStarSpeed[0]
        else:
            starImage = self.starGui.find('**/star_normal')
            color = Vec4(0, 0, 0, 0.2)
            self.starSpeed = ToontownGlobals.TrophyStarSpeed[0]

        if self.star:
            self.star['image'] = starImage
            self.star['image_color'] = color
            self.star.setR(0)
        else:
            gui = loader.loadModel('phase_3.5/models/gui/avatar_panel_gui')
            star = gui.find('**/avatarStar')
            self.star = DirectLabel(parent = self, image = starImage, image_color = color, pos = (0.4, 0, -0.5675), scale = 0.11, relief = None)
            gui.removeNode()
        self.removeTask('profileStarSpin')
        if self.starSpeed:
            self.addTask(self.__starSpin, 'profileStarSpin')

    def __starSpin(self, task):
        now = globalClock.getFrameTime()
        r = now * self.starSpeed % 360.0
        self.star.setR(r)
        return task.cont

class ToonProfilePanel(ProfilePanelBase.ProfilePanelBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToonProfilePanel')
    gui = loader.loadModel('phase_3.5/models/gui/ttrm_m_gui_soc_toonAvatarPanel', allowInstance = True)
    BTN_IMAGE_SCALE = 0.1
    BASE_BTN_X = -0.2725
    BTN_X_OFFSET = 0.11
    BTN_Y = -0.57
    BTN_TEXT_POS = (0, 0.06)
    BTN_TEXT_SCALE = 0.06

    def __init__(self, avatar: Avatar, playerId: Optional[int] = None):
        from toontown.social import SocialMenu

        if base.cr.doId2do.get(avatar.getDoId()):
            avatar = base.cr.doId2do.get(avatar.getDoId())  # type: DistributedToon
        ProfilePanelBase.ProfilePanelBase.__init__(self, avatar, socialMenu = SocialMenu)

        self.notify.debug('Opening toon panel, avId=%d' % self.avId)
        self.playerId = playerId

        if not self.playerId:
            av = base.cr.doId2do.get(self.avId)
            if av:
                self.playerId = avatar.DISLid
            else:
                self.playerId = 0

        self.playerInfo = None
        if self.playerId:
            self.playerInfo = base.cr.playerFriendsManager.playerId2Info.get(playerId)

        self.laffMeter = None
        wantsLaffMeter = hasattr(avatar, 'hp')

        if not hasattr(avatar, 'style'):
            self.notify.warning("Avatar has no 'style'. Abort initialization.")
            ProfilePanelBase.ProfilePanelBase.cleanup(self)
            return

        gui = loader.loadModel('phase_3.5/models/gui/ttrm_m_gui_soc_toonAvatarPanel')
        closeButtonGui = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        self.frame = DirectFrame(
                state = DirectGuiGlobals.NORMAL,
                image = gui.find('**/profilepanel'),
                image_scale = OTPGUIUtils.getImageScale(823, 1156, 1.4),
                scale = 0.8,
                relief = None,
                pos = (-0.375, 100, -0.55),
                parent = base.a2dTopRight)
        self.frame.setBin('fixed', 1)  # TODO: temp until the tab assets are fixed
        self.frame.bind(DGG.B1PRESS, self.dragStart)
        self.frame.bind(DGG.B1RELEASE, self.dragStop)

        self.createFrameBackground(avatar)

        self.disabledImageColor = Vec4(1, 1, 1, 0.4)
        self.text0Color = Vec4(1, 1, 1, 1)
        self.text1Color = Vec4(0.5, 1, 0.5, 1)
        self.text2Color = Vec4(1, 1, 0.5, 1)
        self.text3Color = Vec4(0.6, 0.6, 0.6, 1)

        self.lastPose = [-1, 0]
        self.toonModel: Optional[Toon] = None
        self.toonFrame: Optional[DirectFrame] = None
        self.createToon(avatar)
 
        self.nameLabel = DirectLabel(
                parent = self.frame,
                pos = (0, 0, 0.6),
                relief = None,
                text = self.avName,
                text_fg = Vec4(0.95, 0.95, 0.95, 1),
                text_pos = (0, 0),
                text_scale = 0.05,
                text_shadow = (0, 0, 0, 1),
                text_wordwrap = 12)

        self.closeButton = AnimatedButton(
                parent = self.frame,
                image = (
                    closeButtonGui.find('**/CloseBtn_UP'),
                    closeButtonGui.find('**/CloseBtn_DN'),
                    closeButtonGui.find('**/CloseBtn_Rllvr'),
                    closeButtonGui.find('**/CloseBtn_UP')),
                relief = None,
                pos = (0.3725, 0, 0.5825),
                command = self.__handleClose)

        if self.avId != base.localAvatar.doId:
            isFriend = base.cr.isFriend(self.avId)
            if isFriend:
                friendsText = TTLocalizer.ProfilePanelFriendsRemove
            else:
                friendsText = TTLocalizer.ProfilePanelFriendsAdd
            self.friendButton = AnimatedButton(
                    parent = self.frame,
                    image = (
                        gui.find('**/friend_n'),
                        gui.find('**/friend_h')),
                    image3_color = self.disabledImageColor,
                    image_scale = self.BTN_IMAGE_SCALE,
                    relief = None,
                    text = ('', '', friendsText, ''),
                    text_scale = self.BTN_TEXT_SCALE,
                    pos = (self.BASE_BTN_X, 0, self.BTN_Y),
                    text_fg = self.text0Color,
                    text_pos = self.BTN_TEXT_POS,
                    text_align = TextNode.ACenter,
                    command = self.__handleFriend,
                    extraArgs = [isFriend])
            # This is so that we can overlap the laff meter.
            self.friendButton.setBin('fixed', 3)
            if base.cr.avatarFriendsManager.checkIgnored(self.avId):
                self.friendButton['state'] = DGG.DISABLED
            # TEMP IMAGE, should be boxed shape
            propGui = loader.loadModel('phase_3.5/models/gui/ttoff_m_gui_propgen')
            self.unableToAddLabel = DirectLabel(
                    parent = self.frame,
                    pos = (0, 0, -0.375),
                    relief = None,
                    image = propGui.find('**/propui_bg'),
                    image_scale = (0.65, 1, 0.25),
                    text = '',
                    text_fg = Vec4(0.5, 0.5, 0.5, 1),
                    text_pos = (0, 0.055),
                    text_scale = 0.045,
                    text_wordwrap = 13)
            self.unableToAddLabel.setBin('fixed', 3)
            self.unableToAddLabel.hide()
            unableToAddReason = base.cr.ttrmSocialManager.getAvIdCooldown(self.avId)
            if unableToAddReason != None:
                self.unableToAddLabel['text'] = TTLocalizer.FriendRequestCooldownReasons[unableToAddReason]
                self.friendButton.bind(DGG.WITHIN, self.showUnableToAddLabel)
                self.friendButton.bind(DGG.WITHOUT, self.hideUnableToAddLabel)
                self.friendButton['text'] = ''
                self.friendButton['command'] = None
            self.friendButtonActionLabel = DirectLabel(
                    parent = self.frame,
                    pos = (0, 0, -0.61),
                    relief = None,
                    text = '',
                    text_fg = Vec4(0.95, 0.95, 0.95, 1),
                    text_pos = (0, 0),
                    text_scale = 0.07,
                    text_shadow = (0, 0, 0, 1),
                    text_wordwrap = 13)
            self.friendButtonActionLabel.setBin('fixed', 3)
            self.friendButtonActionLabel.hide()
            self.friendButtonActionLabelIval = None
            self.confirmFriendDialog = None

            self.goToButton = AnimatedButton(
                    parent = self.frame,
                    image = (
                        gui.find('**/teleport_n'),
                        gui.find('**/teleport_h')),
                    image3_color = self.disabledImageColor,
                    image_scale = self.BTN_IMAGE_SCALE,
                    relief = None,
                    pos = (self.BASE_BTN_X + self.BTN_X_OFFSET, 0, self.BTN_Y),
                    text = ('', '', TTLocalizer.AvatarPanelGoTo, ''),
                    text_fg = self.text0Color,
                    text_scale = self.BTN_TEXT_SCALE,
                    text_pos = self.BTN_TEXT_POS,
                    text_align = TextNode.ACenter,
                    command = self.__handleGoto)
            # This is so that we can overlap the laff meter.
            self.goToButton.setBin('fixed', 3)
            if base.cr.avatarFriendsManager.checkIgnored(self.avId):
                self.goToButton['state'] = DGG.DISABLED
            if not base.localAvatar.isTeleportAllowed():
                self.goToButton['state'] = DGG.DISABLED

            self.whisperButton = AnimatedButton(
                    parent = self.frame,
                    image = (
                        gui.find('**/whisper_n'),
                        gui.find('**/whisper_h')),
                    image3_color = self.disabledImageColor,
                    image_scale = self.BTN_IMAGE_SCALE,
                    relief = None,
                    pos = (self.BASE_BTN_X + (self.BTN_X_OFFSET * 2), 0, self.BTN_Y),
                    text = ('', '', TTLocalizer.AvatarPanelWhisper, ''),
                    text_fg = self.text0Color,
                    text_scale = self.BTN_TEXT_SCALE,
                    text_pos = self.BTN_TEXT_POS,
                    text_align = TextNode.ACenter,
                    command = self.__handleWhisper)
            # This is so that we can overlap the laff meter.
            self.whisperButton.setBin('fixed', 3)
            if base.cr.avatarFriendsManager.checkIgnored(self.avId):
                self.whisperButton['state'] = DGG.DISABLED

            self.secretsButton = AnimatedButton(
                    parent = self.frame,
                    image = (
                        gui.find('**/truefriend_n'),
                        gui.find('**/truefriend_h')),
                    image3_color = self.disabledImageColor,
                    image_scale = self.BTN_IMAGE_SCALE,
                    relief = None,
                    pos = (self.BASE_BTN_X + (self.BTN_X_OFFSET * 3), 0, self.BTN_Y),
                    text = ('', '', TTLocalizer.AvatarPanelSecrets, ''),
                    text_fg = self.text0Color,
                    text_scale = self.BTN_TEXT_SCALE,
                    text_pos = self.BTN_TEXT_POS,
                    text_align = TextNode.ACenter,
                    command = self.__handleSecrets)
            if base.cr.avatarFriendsManager.checkIgnored(self.avId):
                self.secretsButton['state'] = DGG.DISABLED
            from toontown.coghq import CogHQBossBattle
            if isinstance(base.cr.playGame.getPlace(), CogHQBossBattle.CogHQBossBattle) and \
                    base.localAvatar.getGameAccess() != OTPGlobals.AccessFull:
                self.secretsButton['state'] = DGG.DISABLED

            ignoreStr, ignoreCmd, ignoreScale = self.getIgnoreButtonInfo()

            self.ignoreButton = AnimatedButton(
                    parent = self.frame,
                    image = (
                        gui.find('**/ignore_n'),
                        gui.find('**/ignore_h')),
                    image3_color = self.disabledImageColor,
                    image_scale = self.BTN_IMAGE_SCALE,
                    relief = None,
                    pos = (self.BASE_BTN_X + (self.BTN_X_OFFSET * 4), 0, self.BTN_Y),
                    text = ('', '', ignoreStr, ''),
                    text_fg = self.text0Color,
                    text_scale = self.BTN_TEXT_SCALE,
                    text_pos = self.BTN_TEXT_POS,
                    text_align = TextNode.ACenter,
                    command = ignoreCmd)
            if base.localAvatar.getLocked() or playerId == base.localAvatar.getDoId():
                self.ignoreButton['state'] = DGG.DISABLED

            self.reportButton = AnimatedButton(
                    parent = self.frame,
                    image = (
                        gui.find('**/report_n'),
                        gui.find('**/report_h')),
                    image3_color = self.disabledImageColor,
                    image_scale = self.BTN_IMAGE_SCALE,
                    relief = None,
                    pos = (self.BASE_BTN_X + (self.BTN_X_OFFSET * 5), 0, self.BTN_Y),
                    text = ('', '', TTLocalizer.AvatarPanelReport, ''),
                    text_fg = self.text0Color,
                    text_scale = self.BTN_TEXT_SCALE,
                    text_pos = self.BTN_TEXT_POS,
                    text_align = TextNode.ACenter,
                    command = self.handleReport)
            if base.localAvatar.getLocked():
                self.reportButton['state'] = DGG.DISABLED

            self.petButton = AnimatedButton(
                    parent = self.frame,
                    image = (
                        gui.find('**/doodle_n'),
                        gui.find('**/doodle_h')),
                    image3_color = self.disabledImageColor,
                    image_scale = self.BTN_IMAGE_SCALE,
                    relief = None,
                    pos = (-0.3725, 0, 0.5825),
                    text = ('', '', TTLocalizer.AvatarPanelPet, ''),
                    text_fg = self.text0Color,
                    text_scale = self.BTN_TEXT_SCALE,
                    text_pos = (0, -0.1),
                    text_align = TextNode.ACenter,
                    command = self.__handleToPet)
            self.petButton.setBin('fixed', 3)
            if not (base.wantPets and avatar.hasPet()):
                self.petButton['state'] = DGG.DISABLED
                self.petButton.hide()
            propGui.removeNode()
        else:
            self.yourselfLabel = DirectLabel(
                    parent = self.frame,
                    pos = (0, 0, self.BTN_Y),
                    relief = None,
                    text = TTLocalizer.AvatarPanelYourself,
                    text_fg = Vec4(0.95, 0.95, 0.95, 1),
                    text_pos = (0, 0),
                    text_scale = 0.04,
                    text_shadow = (0, 0, 0, 1))

        self.detailButton = DirectButton(
                parent = self.frame,
                image = (
                    gui.find('**/expandbutton_n'),
                    gui.find('**/expandbutton_p'),
                    gui.find('**/expandbutton_h')),
                image_scale = OTPGUIUtils.getImageScale(85, 265, 0.3),
                relief = None,
                text = ('', '', TTLocalizer.AvatarPanelDetail, ''),
                text_fg = self.text0Color,
                text_shadow = (0, 0, 0, 1),
                text_scale = 0.055,
                text_pos = (0, -0.2),
                text_align = TextNode.ACenter,
                pos = (-0.487, 0, -0.45),
                command = self.__handleDetails)

        self.detailFrame = ToonProfileDetailPanel(self, self.frame, self.avId, self.avName)
        self.detailFrame.hide()
        self.detailFrame.bind(DGG.B1PRESS, self.dragStart)
        self.detailFrame.bind(DGG.B1RELEASE, self.dragStop)

        if self.avId != base.localAvatar.doId:
            self.groupFrame = DirectFrame(
                    parent = self.frame,
                    relief = None,
                    image = gui.find('**/brdgroup'),
                    image_scale = OTPGUIUtils.getImageScale(546, 289, 0.35),
                    textMayChange = 1,
                    text = TTLocalizer.BoardingPartyTitle,
                    text_wordwrap = 16,
                    text_scale = 0.0725,
                    text_pos = (0, 0.0475),
                    pos = (0, 0, -0.815))
            self.__makeBoardingGui()

            self.__checkGroupStatus()

        gui.removeNode()
        closeButtonGui.removeNode()

        if wantsLaffMeter:
            self.__makeLaffMeter(avatar)
            self.__updateHp(avatar.hp, avatar.maxHp)
            self.laffMeter.show()

        if self.avGenerateName:
            self.accept(self.avGenerateName, self.__handleGenerateAvatar)
        if self.avHpChangeName:
            self.accept(self.avHpChangeName, self.__updateHp)
        self.accept('updateLaffMeter', self.__updateLaffMeter)

        self.accept('updateGroupStatus', self.__checkGroupStatus)

        self.accept(f'friend-request-success-{self.avId}', self.__handleSuccessfulFriendRequest)
        self.accept(f'friend-request-cooldown-{self.avId}', self.__handleFriendRequestCooldown)
        self.accept(f'friend-removed-{self.avId}', self.__handleFriendRemoved)

        self.accept(f'onlineAvatarChanged-{self.avId}', self.__handleAvatarHandleChange)

        self.frame.show()
        messenger.send('avPanelDone')

    def disableAll(self):
        if self.avId == base.localAvatar.doId:
            return
        self.detailButton['state'] = DGG.DISABLED
        self.reportButton['state'] = DGG.DISABLED
        self.ignoreButton['state'] = DGG.DISABLED
        self.goToButton['state'] = DGG.DISABLED
        self.secretsButton['state'] = DGG.DISABLED
        self.whisperButton['state'] = DGG.DISABLED
        self.petButton['state'] = DGG.DISABLED
        self.friendButton['state'] = DGG.DISABLED
        self.closeButton['state'] = DGG.DISABLED
        self.groupButton['state'] = DGG.DISABLED
        self.boardingInfoButton['state'] = DGG.DISABLED

    def cleanup(self):
        if not hasattr(self, 'frame') or self.frame == None:
            return
        self.notify.debug('Clean up toon panel, avId=%d' % self.avId)
        if self.avId != base.localAvatar.doId:
            if self.friendButtonActionLabelIval:
                self.friendButtonActionLabelIval.finish()
                self.friendButtonActionLabelIval = None
            if self.groupButton:
                self.groupButton.destroy()
                del self.groupButton
            self.groupButton = None
            if self.boardingInfoButton:
                self.boardingInfoButton.destroy()
                del self.boardingInfoButton
            self.boardingInfoButton = None
            if self.boardingInfoText:
                self.boardingInfoText.destroy()
                del self.boardingInfoText
            self.boardingInfoText = None
            if self.groupFrame:
                self.groupFrame.destroy()
                del self.groupFrame
            self.groupFrame = None
        self.detailFrame.cleanup()
        if self.frame:
            self.frame.destroy()
            del self.frame
        self.frame = None
        self.toonFrame.destroy()
        del self.toonFrame
        self.toonModel.cleanup()
        del self.toonModel
        self.frameBackground.destroy()
        del self.frameBackground
        self.laffMeter = None
        self.ignore('updateLaffMeter')
        self.ignoreAll()
        if hasattr(self.avatar, 'bFake') and self.avatar.bFake:
            self.avatar.delete()
        base.setCellsAvailable([base.rightCells[0]], 1)
        ProfilePanelBase.ProfilePanelBase.cleanup(self)

    def createFrameBackground(self, avatar):
        bg = avatar.getProfileBackground()
        if bg > len(TTLocalizer.ProfileBackgroundNames) - 1:
            bg = 0
        bgModel = self.gui.find(f'**/panelbg_{bg}').copyTo(hidden)

        if hasattr(self, 'frameBackground'):
            self.frameBackground['image'] = bgModel
        else:
            self.frameBackground = OnscreenImage(
                    parent = self.frame,
                    image = bgModel,
                    scale = OTPGUIUtils.getImageScale(554, 852, 1.0375),
                    pos = (0.0025, 0, 0.005))
        self.frameBackground.setBin('fixed', 0)

    def createToon(self, avatar):
        if self.toonFrame is not None:
            self.toonFrame.destroy()
            self.toonFrame = None
        self.toonModel = Toon.Toon()
        self.toonModel.setDNA(avatar.style)
        self.toonModel.setHat(*avatar.getHat())
        self.toonModel.setGlasses(*avatar.getGlasses())
        self.toonModel.setBackpack(*avatar.getBackpack())
        self.toonModel.setShoes(*avatar.getShoes())
        self.toonModel.reparentTo(self.frame)

        pose = avatar.getProfilePose()
        if pose > len(ProfilePoses) - 1:
            pose = 0
        if self.lastPose[0] == pose:
            self.toonModel.pose(ProfilePoses[pose][0], self.lastPose[1])
        else:
            poseName, poseFrame = ProfilePoses[pose]
            if poseFrame == 'random':
                poseFrame = random.randrange(0, self.toonModel.getNumFrames(poseName))
            elif isinstance(poseFrame, list):
                poseFrame = random.randint(poseFrame[0], poseFrame[1])

            self.toonModel.pose(poseName, poseFrame)

            self.lastPose = [pose, poseFrame]

        self.toonFrame = self.makeFrameModel(self.toonModel)
        self.toonFrame.reparentTo(self.frame)
        self.toonFrame.setPosHpr(0, 0, 0, 180, 0, 0)
        self.toonFrame.setScale(0.45)

    def makeFrame(self) -> DirectFrame:
        frame = DirectFrame(parent = hidden, frameSize = (-1.0, 1.0, -1.0, 1.0), relief = None)
        return frame

    def makeFrameModel(self, model: NodePath) -> NodePath:
        model.setDepthTest(1)
        model.setDepthWrite(1)
        frame = self.makeFrame()
        scale = frame.attachNewNode('scale')
        model.reparentTo(scale)
        bMin, bMax = model.getTightBounds()
        center = (bMin + bMax) / 2.0
        model.setPos(-center[0], 2, -center[2])
        corner = Vec3(bMax - center)
        scale.setScale(1.0 / max(corner[0], corner[1], corner[2]))
        return frame

    def __handleAvatarHandleChange(self, handle):
        self.avName = handle.getName()
        self.nameLabel['text'] = handle.getName()
        self.createFrameBackground(handle)
        self.createToon(handle)

    def __handleGoto(self):
        if base.localAvatar.isTeleportAllowed():
            base.localAvatar.chatMgr.noWhisper()
            messenger.send('gotoAvatar', [self.avId, self.avName, self.avDisableName])

    def __handleToPet(self):
        toonAvatar = self.avatar
        if base.cr.doId2do.get(toonAvatar.getDoId()):
            toonAvatar = base.cr.doId2do.get(toonAvatar.getDoId())
        self.disableAll()
        from toontown.pets import PetDetail
        PetDetail.PetDetail(toonAvatar.getPetId(), self.__petDetailsLoaded)

    def __petDetailsLoaded(self, avatar):
        self.cleanup()
        if avatar:
            avatar.announceGenerate()
            avatar.postGenerateMessage()
            self.notify.debug("Looking at someone's pet. pet doId = %s" % avatar.doId)
            messenger.send('clickedNametag', [avatar])

    def __handleWhisper(self):
        base.localAvatar.chatMgr.whisperTo(self.avName, self.avId, None)

    def __handleSecrets(self):
        base.localAvatar.chatMgr.noWhisper()
        ToontownFriendSecret.showFriendSecret(ToontownFriendSecret.AvatarSecret)

    def __confirmRemoveFriend(self, value: int):
        if self.confirmFriendDialog:
            self.confirmFriendDialog.destroy()
            self.confirmFriendDialog = None

        if value > 0:
            base.cr.removeFriend(self.avId)

    def __acknowledgeFullFriendsList(self):
        if self.confirmFriendDialog:
            self.confirmFriendDialog.destroy()
            self.confirmFriendDialog = None

    def __handleFriend(self, remove: int = 0):
        if remove:
            self.confirmFriendDialog = TTDialog.TTDialog(
                    style = TTDialog.YesNo,
                    text = TTLocalizer.ProfilePanelFriendsRemoveConfirm.format(self.avName),
                    suppressKeys = 1,
                    command = self.__confirmRemoveFriend)
            self.confirmFriendDialog.show()
        else:
            if self.avId not in base.cr.onlineAvatars:
                self.friendButtonActionLabel['text'] = TTLocalizer.ProfilePanelToonOffline
                self.__handleFriendButtonActionSuccessful()
                return
            if len(base.localAvatar.friendsList) >= ToontownGlobals.MaxFriends:
                self.confirmFriendDialog = TTDialog.TTDialog(
                        style = TTDialog.Acknowledge,
                        text = TTLocalizer.ProfilePanelFriendsFullAck,
                        suppressKeys = 1,
                        command = self.__acknowledgeFullFriendsList)
                return
            base.cr.ttrmSocialManager.d_sendFriendRequest(self.avId)
            self.friendButton['state'] = DGG.DISABLED

    def __handleSuccessfulFriendRequest(self):
        self.friendButton['state'] = DGG.NORMAL
        self.friendButton['text'] = ('', '', TTLocalizer.ProfilePanelFriendsRemove, '')
        self.friendButton['extraArgs'] = [1]
        self.friendButtonActionLabel['text'] = TTLocalizer.ProfilePanelFriendAdded
        self.__handleFriendButtonActionSuccessful()

    def __handleFriendRemoved(self, wantIval):
        # we might have the remove friend dialog opened. if so, remove it.
        self.__acknowledgeFullFriendsList()
        self.friendButton['text'] = ('', '', TTLocalizer.ProfilePanelFriendsAdd, '')
        self.friendButton['extraArgs'] = [0]
        if wantIval:
            self.friendButtonActionLabel['text'] = TTLocalizer.ProfilePanelFriendRemoved
            self.__handleFriendButtonActionSuccessful()

    def __handleFriendRequestCooldown(self, reason, add):
        if not base.cr.avatarFriendsManager.checkIgnored(self.avId):
            self.friendButton['state'] = DGG.NORMAL
        if add:
            self.unableToAddLabel['text'] = TTLocalizer.FriendRequestCooldownReasons[reason]
            self.friendButton.bind(DGG.WITHIN, self.showUnableToAddLabel)
            self.friendButton.bind(DGG.WITHOUT, self.hideUnableToAddLabel)
            self.friendButton['text'] = ''
            self.friendButton['command'] = None
        else:
            self.friendButton.unbind(DGG.WITHIN)
            self.friendButton.unbind(DGG.WITHOUT)
            self.unableToAddLabel.hide()
            isFriend = base.cr.isFriend(self.avId)
            if isFriend:
                friendsText = TTLocalizer.ProfilePanelFriendsRemove
            else:
                friendsText = TTLocalizer.ProfilePanelFriendsAdd
            self.friendButton['text'] = ('', '', friendsText, '')
            self.friendButton['command'] = self.__handleFriend
            self.friendButton['extraArgs'] = [isFriend]

    def __handleFriendButtonActionSuccessful(self):
        if self.friendButtonActionLabelIval:
            self.friendButtonActionLabelIval.finish()
            self.friendButtonActionLabelIval = None
        self.friendButtonActionLabelIval = Sequence(
                Func(self.friendButtonActionLabel.show),
                Func(self.friendButtonActionLabel.setColorScale, Vec4(1, 1, 1, 1)),
                LerpPosInterval(
                        nodePath = self.friendButtonActionLabel,
                        duration = 1.5,
                        startPos = (0, 0, -0.53),
                        pos = (0, 0, -0.49),
                        blendType = 'easeInOut'
                ),
                LerpColorScaleInterval(
                        nodePath = self.friendButtonActionLabel,
                        duration = .2,
                        colorScale = Vec4(1, 1, 1, 0),
                        blendType = 'easeInOut'
                ),
                Func(self.friendButtonActionLabel.hide)
        )
        self.friendButtonActionLabelIval.start()

    def showUnableToAddLabel(self, _):
        self.unableToAddLabel.show()

    def hideUnableToAddLabel(self, _):
        self.unableToAddLabel.hide()

    def __exitDetailFrame(self):
        self.detailFrame.hide()
        self.detailButton.show()

    def __handleDetails(self):
        self.detailButton.hide()
        self.detailFrame.show()
        self.detailFrame.demand('Begin')

    def __handleDisableAvatar(self):
        if self.laffMeter != None:
            self.laffMeter.stop()
            self.laffMeter.destroy()
            self.laffMeter = None

    def __handleGenerateAvatar(self, avatar):
        newAvatar = base.cr.doId2do.get(self.avatar.doId)
        if newAvatar:
            self.avatar = newAvatar
        self.__updateLaffMeter(avatar, avatar.hp, avatar.maxHp)
        self.__checkGroupStatus()

    def __updateLaffMeter(self, avatar, hp, maxHp):
        if self.laffMeter == None:
            self.__makeLaffMeter(avatar)
        self.__updateHp(avatar.hp, avatar.maxHp)
        self.laffMeter.show()

    def __makeLaffMeter(self, avatar):
        self.laffMeter = LaffMeter.LaffMeter(avatar.style, avatar.hp, avatar.maxHp, avatar.laffMeterTextColor)
        self.laffMeter.reparentTo(self.frame)
        if avatar.style.getAnimal() == 'monkey':
            self.laffMeter.setPos(-0.195, 0, -0.4)
        else:
            self.laffMeter.setPos(-0.225, 0, -0.4)
        self.laffMeter.setScale(0.06)
        self.laffMeter.setBin('fixed', 2)

    def __updateHp(self, hp, maxHp, quietly = 0):
        if self.laffMeter != None and hp != None and maxHp != None:
            self.laffMeter.adjustFace(hp, maxHp)

    def __handleClose(self):
        self.cleanup()
        messenger.send('focusOut')
        ProfilePanelBase.currentProfilePanel = None

    def getAvId(self) -> Optional[int]:
        if hasattr(self, 'avatar'):
            if self.avatar:
                return self.avatar.doId
        return None

    def getPlayerId(self):
        if hasattr(self, 'playerId'):
            return self.playerId
        return None

    def isHidden(self) -> bool:
        if not hasattr(self, 'frame') or not self.frame:
            return True
        return self.frame.isHidden()

    def getType(self):
        return 'toon'

    def handleInvite(self):
        if localAvatar.boardingParty.isInviteePanelUp():
            localAvatar.boardingParty.showMe(TTLocalizer.BoardingPendingInvite, pos = (0, 0, 0))
        else:
            self.groupButton['state'] = DGG.DISABLED
            localAvatar.boardingParty.requestInvite(self.avId)

    def handleKick(self):
        if not base.cr.playGame.getPlace().getState() == 'elevator':
            self.confirmKickOutDialog = TTDialog.TTDialog(style = TTDialog.YesNo, text = TTLocalizer.BoardingKickOutConfirm % self.avName, command = self.__confirmKickOutCallback)
            self.confirmKickOutDialog.show()

    def __confirmKickOutCallback(self, value):
        if self.confirmKickOutDialog:
            self.confirmKickOutDialog.destroy()
        self.confirmKickOutDialog = None
        if value > 0:
            if self.groupButton:
                self.groupButton['state'] = DGG.DISABLED
            localAvatar.boardingParty.requestKick(self.avId)

    def __checkGroupStatus(self):
        self.groupFrame.hide()
        if hasattr(self, 'avatar'):
            if self.avatar and hasattr(self.avatar, 'getZoneId') and localAvatar.getZoneId() == self.avatar.getZoneId():
                if localAvatar.boardingParty:
                    if self.avId in localAvatar.boardingParty.getGroupMemberList(localAvatar.doId):
                        if localAvatar.boardingParty.getGroupLeader(localAvatar.doId) == localAvatar.doId:
                            self.groupButton['text'] = ('', TTLocalizer.AvatarPanelGroupMemberKick, TTLocalizer.AvatarPanelGroupMemberKick)
                            self.groupButton['image'] = self.kickOutImageList
                            self.groupButton['command'] = self.handleKick
                            self.groupButton['state'] = DGG.NORMAL
                        else:
                            self.groupButton['text'] = ('', TTLocalizer.AvatarPanelGroupMember, TTLocalizer.AvatarPanelGroupMember)
                            self.groupButton['command'] = None
                            self.groupButton['image'] = self.inviteImageDisabled
                            self.groupButton['image_color'] = Vec4(1, 1, 1, 0.4)
                            self.groupButton['state'] = DGG.NORMAL
                    else:
                        self.groupButton['text'] = ('', TTLocalizer.AvatarPanelGroupInvite, TTLocalizer.AvatarPanelGroupInvite)
                        self.groupButton['command'] = self.handleInvite
                        self.groupButton['image'] = self.inviteImageList
                        self.groupButton['state'] = DGG.NORMAL
                    if base.config.GetBool('want-boarding-groups', 1):
                        base.setCellsAvailable([base.rightCells[0]], 0)
                        self.groupFrame.show()

    def handleReadInfo(self, task = None):
        self.boardingInfoButton['state'] = DGG.DISABLED
        if self.boardingInfoText:
            self.boardingInfoText.destroy()
        self.boardingInfoText = TTDialog.TTDialog(style = TTDialog.Acknowledge, text = TTLocalizer.BoardingPartyInform % localAvatar.boardingParty.maxSize,
                                                  command = self.handleCloseInfo)

    def handleCloseInfo(self, *extraArgs):
        self.boardingInfoButton['state'] = DGG.NORMAL
        if self.boardingInfoText:
            self.boardingInfoText.destroy()
            del self.boardingInfoText
        self.boardingInfoText = None

    def __makeBoardingGui(self):
        self.confirmKickOutDialog = None
        groupInviteGui = loader.loadModel('phase_3.5/models/gui/tt_m_gui_brd_inviteButton')
        self.inviteImageList = (groupInviteGui.find('**/tt_t_gui_brd_inviteUp'),
                                groupInviteGui.find('**/tt_t_gui_brd_inviteDown'),
                                groupInviteGui.find('**/tt_t_gui_brd_inviteHover'),
                                groupInviteGui.find('**/tt_t_gui_brd_inviteUp'))
        self.kickOutImageList = (groupInviteGui.find('**/tt_t_gui_brd_kickoutUp'),
                                 groupInviteGui.find('**/tt_t_gui_brd_kickoutDown'),
                                 groupInviteGui.find('**/tt_t_gui_brd_kickoutHover'),
                                 groupInviteGui.find('**/tt_t_gui_brd_kickoutUp'))
        self.inviteImageDisabled = groupInviteGui.find('**/tt_t_gui_brd_inviteDisabled')
        self.groupButton = DirectButton(
                parent = self.groupFrame,
                image = self.inviteImageList,
                image3_color = self.disabledImageColor,
                image_scale = (1.14, 0, 0.8),
                relief = None,
                text = ('', TTLocalizer.AvatarPanelGroupInvite, TTLocalizer.AvatarPanelGroupInvite),
                text0_fg = self.text0Color,
                text1_fg = self.text1Color,
                text2_fg = self.text2Color,
                text3_fg = self.text3Color,
                text_scale = TTLocalizer.TAPgroupButton,
                text_pos = (-0.0, -0.1),
                text_align = TextNode.ACenter,
                command = self.handleInvite,
                pos = (0, 0, -0.0725))
        helpGui = loader.loadModel('phase_3.5/models/gui/tt_m_gui_brd_help')
        helpImageList = (helpGui.find('**/tt_t_gui_brd_helpUp'),
                         helpGui.find('**/tt_t_gui_brd_helpDown'),
                         helpGui.find('**/tt_t_gui_brd_helpHover'),
                         helpGui.find('**/tt_t_gui_brd_helpDown'))
        self.boardingInfoButton = DirectButton(
                parent = self.groupFrame,
                relief = None,
                text_pos = (-0.05, 0.05),
                text_scale = 0.06,
                text_align = TextNode.ALeft,
                text_fg = Vec4(1, 1, 1, 1),
                text_shadow = Vec4(0, 0, 0, 1),
                image = helpImageList,
                image_scale = (0.5, 1, 0.5),
                image3_color = self.disabledImageColor,
                scale = 1.1,
                command = self.handleReadInfo,
                pos = (0.27, 0, -0.019))
        self.boardingInfoText = None
        groupInviteGui.removeNode()
        helpGui.removeNode()

    def dragStart(self, event):
        self.removeTask('dragTask')
        vWidget2render2d = self.frame.getPos(render2d)
        vMouse2render2d = Point3(event.getMouse()[0], 0, event.getMouse()[1])
        editVec = Vec3(vWidget2render2d - vMouse2render2d)
        task = self.addTask(self.dragTask, 'dragTask', appendTask = True)
        task.editVec = editVec

    def dragTask(self, task):
        if not hasattr(self, 'frame') or not self.frame:
            return task.done
        mwn = base.mouseWatcherNode
        if mwn.hasMouse():
            vMouse2render2d = Point3(mwn.getMouse()[0], 0, mwn.getMouse()[1])
            newPos = vMouse2render2d + task.editVec
            newPos[0] = bound(newPos[0], -.5, 0.79)
            newPos[2] = bound(newPos[2], -.45, .45)
            if newPos[0] < 0.5:
                self.frame.wrtReparentTo(base.a2dBottomLeft)
            else:
                self.frame.wrtReparentTo(base.a2dBottomRight)

            self.frame.setPos(render2d, newPos)
        return task.cont

    def dragStop(self, event):
        self.removeTask('dragTask')
