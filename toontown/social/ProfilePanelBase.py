from panda3d.core import *
from direct.gui.DirectGui import *
from direct.showbase import DirectObject
from toontown.toonbase import TTLocalizer
from toontown.toontowngui import TTDialog
from otp.distributed import CentralLogger

IGNORE_SCALE = 0.06
STOP_IGNORE_SCALE = 0.04


class ProfilePanelBase(DirectObject.DirectObject):
    currentProfilePanel = None

    def __init__(self, avatar, socialMenu = None):
        if ProfilePanelBase.currentProfilePanel:
            ProfilePanelBase.currentProfilePanel.cleanup()
        ProfilePanelBase.currentProfilePanel = self
        self.dialog = None
        self.category = None
        self.socialMenuShown = False
        self.socialMenu = socialMenu
        if socialMenu:
            self.socialMenuShown = socialMenu.isSocialMenuShown()
            socialMenu.hideSocialMenu()
        if avatar:
            self.avatar = avatar
            self.avName = avatar.getName()
        else:
            self.avatar = None
            self.avName = 'Player'
        if hasattr(avatar, 'uniqueName'):
            self.avId = avatar.doId
            self.avDisableName = avatar.uniqueName('disable')
            self.avGenerateName = avatar.uniqueName('generate')
            self.avHpChangeName = avatar.uniqueName('hpChange')
            if self.avId in base.cr.doId2do:
                self.avatar = base.cr.doId2do[self.avId]
        else:
            self.avDisableName = None
            self.avGenerateName = None
            self.avHpChangeName = None
            self.avId = None
        if self.avDisableName:
            self.accept(self.avDisableName, self.__handleDisableAvatar)

    def cleanup(self):
        if ProfilePanelBase.currentProfilePanel != self:
            return
        if self.avDisableName:
            self.ignore(self.avDisableName)
        if self.avGenerateName:
            self.ignore(self.avGenerateName)
        if self.avHpChangeName:
            self.ignore(self.avHpChangeName)
        ProfilePanelBase.currentProfilePanel = None

    def __handleDisableAvatar(self):
        if ProfilePanelBase.currentProfilePanel:
            ProfilePanelBase.currentProfilePanel.handleDisableAvatar()
        else:
            self.handleDisableAvatar()

    def handleDisableAvatar(self):
        self.cleanup()
        ProfilePanelBase.currentProfilePanel = None

    def isHidden(self):
        return 1

    def getType(self):
        return None

    def getIgnoreButtonInfo(self):
        if base.cr.avatarFriendsManager.checkIgnored(self.avId):
            return (TTLocalizer.AvatarPanelStopIgnoring, self.handleStopIgnoring, STOP_IGNORE_SCALE)
        else:
            return (TTLocalizer.AvatarPanelIgnore, self.handleIgnore, IGNORE_SCALE)

    def handleIgnore(self):
        isAvatarFriend = base.cr.isFriend(self.avatar.doId)
        isPlayerFriend = base.cr.playerFriendsManager.isAvatarOwnerPlayerFriend(self.avatar.doId)
        isFriend = isAvatarFriend or isPlayerFriend
        if isFriend:
            self.dialog = TTDialog.TTGlobalDialog(
                    style = TTDialog.CancelOnly,
                    text = TTLocalizer.IgnorePanelAddFriendAvatar % self.avName,
                    text_wordwrap = 18.5,
                    text_scale = 0.06,
                    cancelButtonText = TTLocalizer.lCancel,
                    doneEvent = 'IgnoreBlocked',
                    command = self.freeLocalAvatar)
        else:
            self.dialog = TTDialog.TTGlobalDialog(
                    style = TTDialog.TwoChoice,
                    text = TTLocalizer.IgnorePanelAddIgnore % self.avName,
                    text_wordwrap = 18.5,
                    text_scale = TTLocalizer.APBdialog,
                    okButtonText = TTLocalizer.AvatarPanelIgnore,
                    cancelButtonText = TTLocalizer.lCancel,
                    doneEvent = 'IgnoreConfirm',
                    command = self.handleIgnoreConfirm)
        DirectLabel(
                parent = self.dialog,
                relief = None,
                pos = (0, TTLocalizer.APBdirectLabelPosY, 0.125),
                text = TTLocalizer.IgnorePanelTitle,
                textMayChange = 0,
                text_scale = 0.08)
        self.dialog.show()
        self.__acceptStoppedStateMsg()
        self.requestStopped()

    def handleStopIgnoring(self):
        self.dialog = TTDialog.TTGlobalDialog(style = TTDialog.TwoChoice, text = TTLocalizer.IgnorePanelRemoveIgnore % self.avName, text_wordwrap = 18.5, text_scale = 0.06,
                                              okButtonText = TTLocalizer.AvatarPanelStopIgnoring, cancelButtonText = TTLocalizer.lCancel, buttonPadSF = 4.0,
                                              doneEvent = 'StopIgnoringConfirm', command = self.handleStopIgnoringConfirm)
        DirectLabel(parent = self.dialog, relief = None, pos = (0, TTLocalizer.APBdirectLabelPosY, 0.15), text = TTLocalizer.IgnorePanelTitle, textMayChange = 0, text_scale = 0.08)
        self.dialog.show()
        self.__acceptStoppedStateMsg()
        self.requestStopped()

    def handleIgnoreConfirm(self, value):
        if value == -1:
            self.freeLocalAvatar()
            return
        base.cr.ttrmSocialManager.d_handleIgnore(self.avId)
        base.cr.avatarFriendsManager.addIgnore(self.avId)
        self.dialog = TTDialog.TTGlobalDialog(style = TTDialog.Acknowledge, text = TTLocalizer.IgnorePanelIgnore % self.avName, text_wordwrap = 18.5, text_scale = 0.06,
                                              topPad = 0.1, doneEvent = 'IgnoreComplete', command = self.handleDoneIgnoring)
        DirectLabel(parent = self.dialog, relief = None, pos = (0, TTLocalizer.APBdirectLabelPosY, 0.15), text = TTLocalizer.IgnorePanelTitle, textMayChange = 0, text_scale = 0.08)
        self.dialog.show()
        self.__acceptStoppedStateMsg()
        self.requestStopped()

    def handleStopIgnoringConfirm(self, value):
        if value == -1:
            self.freeLocalAvatar()
            return
        base.cr.avatarFriendsManager.removeIgnore(self.avId)
        self.dialog = TTDialog.TTGlobalDialog(style = TTDialog.Acknowledge, text = TTLocalizer.IgnorePanelEndIgnore % self.avName, text_wordwrap = 18.5, text_scale = 0.06,
                                              topPad = 0.1, doneEvent = 'StopIgnoringComplete', command = self.handleDoneIgnoring)
        DirectLabel(parent = self.dialog, relief = None, pos = (0, TTLocalizer.APBdirectLabelPosY, 0.15), text = TTLocalizer.IgnorePanelTitle, textMayChange = 0, text_scale = 0.08)
        self.dialog.show()
        self.__acceptStoppedStateMsg()
        self.requestStopped()

    def handleDoneIgnoring(self, value):
        self.freeLocalAvatar()

    def handleReport(self):
        if base.cr.centralLogger.hasReportedPlayer(self.playerId, self.avId):
            self.alreadyReported()
        else:
            self.confirmReport()

    def confirmReport(self):
        if base.cr.isFriend(self.avId) or base.cr.playerFriendsManager.isPlayerFriend(self.avId):
            string = TTLocalizer.ReportPanelBodyFriends
            titlePos = 0.41
        else:
            string = TTLocalizer.ReportPanelBody
            titlePos = 0.35
        self.dialog = TTDialog.TTGlobalDialog(style = TTDialog.TwoChoice, text = string % self.avName, text_wordwrap = 18.5, text_scale = 0.06,
                                              okButtonText = TTLocalizer.AvatarPanelReport, cancelButtonText = TTLocalizer.lCancel, doneEvent = 'ReportConfirm',
                                              command = self.handleReportConfirm)
        DirectLabel(parent = self.dialog, relief = None, pos = (0, 0, titlePos), text = TTLocalizer.ReportPanelTitle, textMayChange = 0, text_scale = 0.08)
        self.dialog.show()
        self.__acceptStoppedStateMsg()
        self.requestStopped()
        return

    def handleReportConfirm(self, value):
        self.cleanupDialog()
        if value == 1:
            self.chooseReportCategory()
        else:
            self.requestWalk()

    def alreadyReported(self):
        self.dialog = TTDialog.TTGlobalDialog(style = TTDialog.Acknowledge, text = TTLocalizer.ReportPanelAlreadyReported % self.avName, text_wordwrap = 18.5, text_scale = 0.06,
                                              topPad = 0.1, doneEvent = 'AlreadyReported', command = self.handleAlreadyReported)
        DirectLabel(parent = self.dialog, relief = None, pos = (0, 0, 0.2), text = TTLocalizer.ReportPanelTitle, textMayChange = 0, text_scale = 0.08)
        self.dialog.show()
        self.__acceptStoppedStateMsg()
        self.requestStopped()

    def handleAlreadyReported(self, value):
        self.freeLocalAvatar()

    def chooseReportCategory(self):
        self.dialog = TTDialog.TTGlobalDialog(pos = (0, 0, 0.4), style = TTDialog.CancelOnly, text = TTLocalizer.ReportPanelCategoryBody % (self.avName, self.avName),
                                              text_wordwrap = 18.5, text_scale = 0.06, topPad = 0.05, midPad = 0.75, cancelButtonText = TTLocalizer.lCancel,
                                              doneEvent = 'ReportCategory', command = self.handleReportCategory)
        DirectLabel(parent = self.dialog, relief = None, pos = (0, 0, 0.225), text = TTLocalizer.ReportPanelTitle, textMayChange = 0, text_scale = 0.08)
        guiButton = loader.loadModel('phase_3/models/gui/quit_button')
        DirectButton(parent = self.dialog, relief = None, image = (guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')),
                     image_scale = (2.125, 1.0, 1.0), text = TTLocalizer.ReportPanelCategoryLanguage, text_scale = 0.06, text_pos = (0, -0.0124), pos = (0, 0, -0.3),
                     command = self.handleReportCategory, extraArgs = [0])
        DirectButton(parent = self.dialog, relief = None, image = (guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')),
                     image_scale = (2.15, 1.0, 1.0), text = TTLocalizer.ReportPanelCategoryPii, text_scale = 0.06, text_pos = (0, -0.0125), pos = (0, 0, -0.425),
                     command = self.handleReportCategory, extraArgs = [1])
        DirectButton(parent = self.dialog, relief = None, image = (guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')),
                     image_scale = (2.125, 1.0, 1.0), text = TTLocalizer.ReportPanelCategoryRude, text_scale = 0.06, text_pos = (0, -0.0125), pos = (0, 0, -0.55),
                     command = self.handleReportCategory, extraArgs = [2])
        DirectButton(parent = self.dialog, relief = None, image = (guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')),
                     image_scale = (2.125, 1.0, 1.0), text = TTLocalizer.ReportPanelCategoryName, text_scale = 0.06, text_pos = (0, -0.0125), pos = (0, 0, -0.675),
                     command = self.handleReportCategory, extraArgs = [3])
        DirectButton(parent = self.dialog, relief = None, image = (guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')),
                     image_scale = (2.125, 1.0, 1.0), text = TTLocalizer.ReportPanelCategoryHacking, text_scale = 0.06, text_pos = (0, -0.0125), pos = (0, 0, -0.8),
                     command = self.handleReportCategory, extraArgs = [4])
        guiButton.removeNode()
        self.dialog.show()
        self.__acceptStoppedStateMsg()
        self.requestStopped()

    def handleReportCategory(self, value):
        self.cleanupDialog()
        if value >= 0:
            cat = [CentralLogger.ReportFoulLanguage,
                   CentralLogger.ReportPersonalInfo,
                   CentralLogger.ReportRudeBehavior,
                   CentralLogger.ReportBadName,
                   CentralLogger.ReportHacking]
            self.category = cat[value]
            self.confirmReportCategory(value)
        else:
            self.requestWalk()

    def confirmReportCategory(self, category):
        string = TTLocalizer.ReportPanelConfirmations[category]
        string += '\n\n' + TTLocalizer.ReportPanelWarning
        self.dialog = TTDialog.TTGlobalDialog(style = TTDialog.TwoChoice, text = string % self.avName,
                                              text_wordwrap = 30, text_scale = 0.06, topPad = 0.15,
                                              midPad = 0.7,
                                              pos = (0, 0, 0.3),
                                              okButtonText = TTLocalizer.AvatarPanelReport, cancelButtonText = TTLocalizer.lCancel, doneEvent = 'ReportConfirmCategory',
                                              command = self.handleReportCategoryConfirm)
        DirectLabel(parent = self.dialog, relief = None, pos = (0, 0, 0.4), text = TTLocalizer.ReportPanelTitle, textMayChange = 0, text_scale = 0.08)
        DirectLabel(parent = self.dialog, relief = None, pos = (0, 0, -0.4), text = TTLocalizer.ReportPanelAddDetails, textMayChange = 0, text_scale = 0.08)
        self.reportDescriptionEntry = DirectEntry(relief = DGG.SUNKEN,
                                                  width = 20,
                                                  scale = 0.06,
                                                  parent = self.dialog,
                                                  pos = (-0.6, 0, -.5),
                                                  borderWidth = (0.1, 0.1),
                                                  numLines = 7,
                                                  cursorKeys = 1,
                                                  frameColor = (0.8, 0.8, 0.5, 1))
        self.dialog.show()
        self.__acceptStoppedStateMsg()

    def handleReportCategoryConfirm(self, value):
        self.cleanupDialog()
        removed = 0
        isPlayer = 0
        if value > 0:
            if self.category == CentralLogger.ReportHacking:
                base.cr.centralLogger.reportPlayer(self.category, self.playerId, self.avId, self.reportDescriptionEntry.get(True))
                self.category = CentralLogger.ReportRudeBehavior
            base.cr.centralLogger.reportPlayer(self.category, self.playerId, self.avId, self.reportDescriptionEntry.get(True))
            if base.cr.isFriend(self.avId):
                base.cr.removeFriend(self.avId)
                removed = 1
            if base.cr.playerFriendsManager.isPlayerFriend(self.playerId):
                if self.playerId:
                    base.cr.playerFriendsManager.sendRequestRemove(self.playerId)
                    removed = 1
                    isPlayer = 1
            self.reportComplete(removed, isPlayer)
        else:
            self.requestWalk()

    def reportComplete(self, removed, isPlayer):
        string = TTLocalizer.ReportPanelThanks
        titlePos = 0.25
        if removed:
            if isPlayer:
                string += ' ' + TTLocalizer.ReportPanelRemovedPlayerFriend % self.playerId
            else:
                string += ' ' + TTLocalizer.ReportPanelRemovedFriend % self.avName
            titlePos = 0.3
        self.dialog = TTDialog.TTGlobalDialog(style = TTDialog.Acknowledge, text = string, text_wordwrap = 18.5, text_scale = 0.06, topPad = 0.1, doneEvent = 'ReportComplete',
                                              command = self.handleReportComplete)
        DirectLabel(parent = self.dialog, relief = None, pos = (0, 0, titlePos), text = TTLocalizer.ReportPanelTitle, textMayChange = 0, text_scale = 0.08)
        self.dialog.show()
        self.__acceptStoppedStateMsg()

    def handleReportComplete(self, value):
        self.freeLocalAvatar()

    def freeLocalAvatar(self, value = None):
        self.cleanupDialog()
        self.requestWalk()

    def cleanupDialog(self):
        if self.dialog:
            self.dialog.ignore('exitingStoppedState')
            self.dialog.cleanup()
            self.dialog = None

    def requestStopped(self):
        if not base.cr.playGame.getPlace().fsm.getCurrentState().getName() == 'stickerBook':
            if base.cr.playGame.getPlace().fsm.hasStateNamed('stopped'):
                base.cr.playGame.getPlace().fsm.request('stopped')
            else:
                self.notify.warning('skipping request to stopped in %s' % base.cr.playGame.getPlace())
        else:
            self.cleanup()

    def requestWalk(self):
        if base.localAvatar.getLocked():
            return

        if base.cr.playGame.getPlace().fsm.hasStateNamed('finalBattle'):
            base.cr.playGame.getPlace().fsm.request('finalBattle')
        elif base.cr.playGame.getPlace().fsm.hasStateNamed('walk'):
            if base.cr.playGame.getPlace().getState() == 'stopped':
                base.cr.playGame.getPlace().fsm.request('walk')
        else:
            self.notify.warning('skipping request to walk in %s' % base.cr.playGame.getPlace())

    def __acceptStoppedStateMsg(self):
        self.dialog.ignore('exitingStoppedState')
        self.dialog.accept('exitingStoppedState', self.cleanupDialog)
