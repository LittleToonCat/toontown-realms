import datetime
import sys
import time

from panda3d.core import NodePath, TextNode, TransparencyAttrib, UniqueIdAllocator, Vec3, Vec4

from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectWaitBar import DirectWaitBar
from direct.gui.OnscreenText import OnscreenText

from direct.interval.IntervalGlobal import *

from otp.otpgui import OTPGUIUtils

from toontown.toonbase import TTLocalizer, ToontownGlobals, ClientSettings

from .AnimatedButton import AnimatedButton
from .ToontownScrolledFrame import ToontownScrolledFrame
from . import ToontownGUIUtils
from . import TTDialog

from typing import Union, Callable, Dict, Optional

from ..parties import PartyUtils
from ..parties.PartyUtils import getTimeDeltaInSeconds


class NotificationGUI(DirectFrame):
    notificationsModel = loader.loadModel('phase_3.5/models/gui/ttoff_m_gui_hud_actionBar')
    scrollbarModel = loader.loadModel('phase_3.5/models/gui/ttoff_m_gui_sbk_generic')

    def __init__(self):
        DirectFrame.__init__(
                self,
                parent = aspect2d,
                relief = None,
                image = NotificationGUI.notificationsModel.find('**/notifications_bg'),
                image_scale = OTPGUIUtils.getImageScale(744, 1008, 1),
                image_pos = (0, 0, .55),
                borderWidth = (0.01, 0.01),
        )
        self.initialiseoptions(NotificationGUI)

        self.isEntered: bool = False

        self.activeNotifications: Dict[int, DirectFrame] = {}
        self.id2Notifications: Dict[str, List[DirectFrame]] = {}
        self.notificationAllocator = UniqueIdAllocator(0, 10000)

        self.emptyNotice = OnscreenText(
                parent = self,
                text = TTLocalizer.NotificationEmptyNotice,
                font = ToontownGlobals.getInterfaceFont(),
                fg = (0.75, 0.44, 0.44, 1),
                scale = 0.06,
                pos = (0, 0.82),
                wordwrap = 11
        )

        self.scrolledFrame = ToontownScrolledFrame(parent = self, # TODO: find the correct pos, scale, height and margins
                                                   relief = None,
                                                   itemMargin = (0.05, 0),
                                                   useItemBoundsForPadding = False,
                                                   itemPadding = 0.25,
                                                   pos = (0, 0, 0.5295),
                                                   width = 0.379,
                                                   height = 0.375,
                                                   manageScrollBars = False,
                                                   verticalScroll_frameColor = (0, 0, 0, 0),
                                                   verticalScroll_manageButtons = False,
                                                   verticalScroll_thumb_geom = (
                                                       NotificationGUI.scrollbarModel.find('**/scrollbar_normal'),
                                                       NotificationGUI.scrollbarModel.find('**/scrollbar_press'),
                                                       NotificationGUI.scrollbarModel.find('**/scrollbar_hover')),
                                                   verticalScroll_thumb_geom_scale = OTPGUIUtils.getImageScale(130, 399, 0.15),
                                                   verticalScroll_thumb_geom_pos = (-0.006, 0, 0),
                                                   verticalScroll_thumb_relief = None,
                                                   verticalScroll_resizeThumb = False,
                                                   verticalScroll_decButton_relief = None,
                                                   verticalScroll_incButton_relief = None)

        self.setBin('gui-popup', 0)
        self.hide()

    def enter(self):
        if self.isEntered:
            return
        self.isEntered = True
        self.show()

        if ClientSettings.GUIAnimations.get():
            ToontownGUIUtils.Animations.popup(self, self.getScale()).start()

    def exit(self):
        if not self.isEntered:
            return
        self.isEntered = False
        self.hide()

    def isActive(self):
        return self.isEntered

    def refreshNotifications(self):
        pass

    def allocateNotificationId(self, owner=None) -> int:
        notificationId = self.notificationAllocator.allocate()
        return notificationId

    def deallocateNotificationId(self, notificationId: int):
        self.notificationAllocator.free(notificationId)

    def makeIconFrame(self) -> DirectFrame:
        frame = DirectFrame(parent = hidden, frameSize = (-1.0, 1.0, -1.0, 1.0), relief = None)
        return frame

    def makeIcon(self, ico: NodePath) -> NodePath:
        ico.setDepthTest(1)
        ico.setDepthWrite(1)
        ico.setTransparency(TransparencyAttrib.MDual)
        frame = self.makeIconFrame()
        scale = frame.attachNewNode('scale')
        ico.reparentTo(scale)
        bMin, bMax = ico.getTightBounds()
        center = (bMin + bMax) / 2.0
        ico.setPos(-center[0], 2, -center[2])
        corner = Vec3(bMax - center)
        scale.setScale(1.0 / max(corner[0], corner[1], corner[2]))
        return frame

    def removeNotificationsMatching(self, idStr):
        if idStr in self.id2Notifications:
            for i, notification in enumerate(self.id2Notifications[idStr]):
                # ASSUME that we don't have to do any dismiss action
                self.performDismissNotificationAction(None, notification)

    # TODO: there should be a Notification class
    def createNotification(self, title: str, body: str, ico: NodePath, id: str, subId: str, allowDuplicateIds: Optional[bool], dismissButton2Text: Optional[str],
                           dismissButton2Action: Optional[Callable], button2Text: Optional[str], button2Action: Optional[Callable]):
        if not allowDuplicateIds:
            self.removeNotificationsMatching(id)

        notification = DirectFrame(
                relief = None,
                image = NotificationGUI.notificationsModel.find('**/notifications_notificationbg'),
                image_scale = OTPGUIUtils.getImageScale(1093, 426, 0.265)
        )
        notification.id = id
        notification.subId = subId
        notification.uid = None
        icon = self.makeIcon(ico)
        icon.reparentTo(notification)
        icon.setPos(-0.245, 0, 0.03)
        icon.setScale(0.05)

        title = OnscreenText(
                parent = notification,
                text = title,
                scale = 0.05,
                pos = (-0.175, 0.075),
                align = TextNode.ALeft
        )
        body = OnscreenText(
                parent = notification,
                text = body,
                fg = Vec4(0.2, 0.2, 0.2, 1),
                scale = 0.035,
                pos = (-0.175, 0.0325),
                wordwrap = 14,
                align = TextNode.ALeft
        )
        serverDateTime = self.formatTime(base.cr.toontownTimeManager.getCurServerDateTime())

        timeText = OnscreenText(
                parent = notification,
                text = serverDateTime,
                fg = (0.0, 0.0, 0.0, 0.4),
                scale = 0.035,
                pos = (-0.295, -0.085),
                align = TextNode.ALeft
        )

        # TODO: there should be a Notification class
        notification.timeActiveBar = DirectWaitBar(
                parent = notification,
                relief = None,
                range = 100,
                value = 100,
                frameSize = (-1.2, 1.2, -0.01, 0.01),
                barColor = Vec4(0, 0, 0, 0.2),
                scale = 0.25,
                pos = (0, 0, -.11)
        )                

        notification.dismissButton = AnimatedButton(
                parent = notification,
                relief = None,
                pos = (0.225, 0, -0.076),
                image = NotificationGUI.notificationsModel.find('**/notifications_button'),
                image_scale = OTPGUIUtils.getImageScale(634, 227, 0.06),
                text = dismissButton2Text,
                text_scale = 0.035,
                text_pos = (0, -0.01),
                command = self.performDismissNotificationAction,
                extraArgs = [dismissButton2Action, notification]
        )

        if button2Text is not None:
            button2B = AnimatedButton(
                    parent = notification,
                    relief = None,
                    pos = (0.05, 0, -0.076),
                    image = NotificationGUI.notificationsModel.find('**/notifications_button'),
                    image_scale = OTPGUIUtils.getImageScale(634, 227, 0.06),
                    text = button2Text,
                    text_scale = 0.035,
                    text_pos = (0, -0.01),
                    command = self.performNotificationAction,
                    extraArgs = [button2Action, notification]
            )

        if id not in self.id2Notifications:
            self.id2Notifications[id] = []
        self.id2Notifications[id].append(notification)

        return notification

    def addNotificationToScrolledFrame(self, notification):
        if not hasattr(base, 'localAvatar'):
            return
        base.localAvatar.activeNotification = None

        uid = self.allocateNotificationId()

        notification.clearColorScale()
        notification.uid = uid
        notification.show()
        notification.timeActiveBar.destroy()

        self.scrolledFrame.insertItems(notification)
        self.activeNotifications[uid] = notification

        self.emptyNotice.hide()

    def __handleNotificationDialog(self, value: int, call: Callable, notification):
        if self.notificationDialog:
            self.notificationDialog.destroy()
            self.notificationDialog = None

        if value > 0:
            self.performDismissNotificationAction(call, notification)

    def performNotificationAction(self, call: Callable, notification): # TODO: notification: Notification
        # TODO: Move this to the friends list manager, we don't wanna act on this right here
        # TODO: this dialog should also dismiss without a call if our ID equals the id of this notification and the server or something decides to remove this notification from us.
        if notification.subId == "friend_request_add" and len(base.localAvatar.friendsList) >= ToontownGlobals.MaxFriends:
            self.notificationDialog = TTDialog.TTDialog(
                    style = TTDialog.YesNo,
                    text = TTLocalizer.NotiticationFriendsListFullNotice,
                    suppressKeys = 1,
                    command = self.__handleNotificationDialog,
                    extraArgs = [notification.dismissButton['extraArgs'][0], notification])
            self.notificationDialog.show()
            return
        self.performDismissNotificationAction(call, notification)

    def performDismissNotificationAction(self, call: Optional[Callable], notification):  # TODO: notification: Notification
        if call:
            call()
        if notification in base.localAvatar.notificationsQueue:
            base.localAvatar.notificationsQueue.remove(notification)
        if notification.uid != None:
            self.dismissNotification(notification.uid)
        else:
            self.dismissActiveNotification(notification)

    def dismissActiveNotification(self, notification):
        if notification.id in self.id2Notifications:
            if notification in self.id2Notifications[notification.id]:
                self.id2Notifications[notification.id].remove(notification)
        base.localAvatar.handleNotificationDismiss(notification)
        notification.destroy()
        base.localAvatar.processQueuedNotifications()

    def dismissNotification(self, uid: int):
        if uid in self.activeNotifications:
            notification = self.activeNotifications[uid]
            if notification.id in self.id2Notifications:
                if notification in self.id2Notifications[notification.id]:
                    self.id2Notifications[notification.id].remove(notification)
            self.scrolledFrame.removeItem(notification)
            notification.destroy()
            del self.activeNotifications[uid]
            self.deallocateNotificationId(uid)
        if not self.activeNotifications:
            self.emptyNotice.show()

    @staticmethod
    def formatTime(inTime):
        curServerTime = base.cr.toontownTimeManager.getCurServerDateTime()
        ltime = time.localtime()
        localTime = datetime.datetime(year=ltime.tm_year, month=ltime.tm_mon, day=ltime.tm_mday, hour=ltime.tm_hour, minute=ltime.tm_min, second=ltime.tm_sec)
        naiveServerTime = curServerTime.replace(tzinfo=None)
        newTimeDelta = localTime - naiveServerTime
        localDifference = getTimeDeltaInSeconds(newTimeDelta)
        inTime = inTime + datetime.timedelta(seconds=localDifference)

        # Realistically this won't be used at all right now, in
        # the future we will have it refresh the times when opening up
        # incase someone is playing thru to another day to show the date

        # why does datetime use different syntax on different platforms who designed this
        zeroCanceller = '#' if sys.platform == 'win32' else '-'

        if inTime.date() != datetime.datetime.today().date():
            return inTime.strftime(f'%b %{zeroCanceller}d %{zeroCanceller}I:%M %p')
        return inTime.strftime(f'%{zeroCanceller}I:%M %p')
