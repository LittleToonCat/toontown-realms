from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectLabel import DirectLabel
from direct.gui.DirectButton import DirectButton
from direct.gui.DirectGui import DGG
from direct.directnotify import DirectNotifyGlobal
from direct.interval.LerpInterval import LerpPosInterval
from direct.interval.IntervalGlobal import Parallel, Func, Wait, Sequence

from toontown.toonbase import ToontownGlobals, TTLocalizer


class AnnounceDialog(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('AnnounceDialog')

    def __init__(self):
        # aspect2dp to render above ALL the things
        DirectFrame.__init__(self, parent=aspect2dp, pos=(0.0, 0.0, 0.95), frameColor=(0.0, 0.0, 0.0, 0.75),
                             frameSize=(-base.getAspectRatio(), base.getAspectRatio(), -0.05, 0.05), sortOrder=9001)
        self.username = DirectLabel(parent=self, text='ANNOUNCEMENT: N/A', text_bg=(0.0, 0.0, 0.0, 0.0),
                                      text_frame=(0.0, 0.0, 0.0, 0.0), relief=None,
                                      text_fg=(1.0, 1.0, 1.0, 1.0), pos=(0.0, 0.0, 0.0),
                                      text_font=ToontownGlobals.getToonFont(), textMayChange=1)
        self.icon = DirectFrame(parent=self, image=ToontownGlobals.DiscordDefaultAvatarFile)
        buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        cancelImageList = (buttons.find('**/CloseBtn_UP'), buttons.find('**/CloseBtn_DN'),
                           buttons.find('**/CloseBtn_Rllvr'))
        self.cancel = DirectButton(parent=self, relief=None, geom=cancelImageList, command=self.joinDone)
        buttons.removeNode()
        self.initialiseoptions(self.__class__)
        self.setDialogScale()
        self.accept('aspectRatioChanged', self.ratioChanged)
        self.seq = None
        self.notify.debug('Created frame; hiding.')
        self.hide()

    def destroy(self):
        self.ignoreAll()
        self.hide()     # cheat a cleanup, and might as well hide just in case
        DirectFrame.destroy(self)

    def show(self):
        self.setPos(0, 0, 1.5)
        DirectFrame.show(self)
        # lets make things... fancy
        sfx = loader.loadSfx('phase_3.5/audio/sfx/mailbox_alert.ogg')
        self.seq = Parallel(LerpPosInterval(self, duration=1.5, pos=(0, 0, 0.95), startPos=(0, 0, 1.5), fluid=1),
                              Sequence(Wait(1.0), Func(base.playSfx, sfx)))
        self.seq.start()

    def hide(self):
        self.lockButtons()
        if self.seq and self.seq.isPlaying():
            self.seq.pause()
            self.seq = None
        DirectFrame.hide(self)

    def ratioChanged(self):
        self['frameSize'] = (-base.getAspectRatio(), base.getAspectRatio(), -0.05, 0.05)
        self.resetFrameSize()
        self.calculatePositions()

    def setDialogScale(self):
        self.setScale(1, 1, 1)
        self.username.setScale(0.03, 1.0, 0.03)
        self.icon.setScale(0.05, 1.0, 0.05)
        self.cancel.setScale(0.75, 1.0, 0.75)
        self.calculatePositions()

    def setIcon(self, userId, username, discrim, iconFile):
        self.lockButtons()    # never hurts to lock down the buttons upon a change
        if len(username) > 64:
            # I dunno how long usernames can be, but truncate it after a certain length
            username = username[:61] + "..."
        self.username.setText(TTLocalizer.DiscordJoinRequest.format(username, discrim))
        self.username.resetFrameSize()
        if iconFile is not None:
            self.icon.setImage(iconFile)
        else:
            self.icon.setImage(ToontownGlobals.DiscordDefaultAvatarFile)

        # calculate button positions
        self.calculatePositions()

        # now, enable ze buttons!
        self.unlockButtons(userId)

    def calculatePositions(self):
        spacing = 0.025

        # calculate the position of the avatar image
        ubounds = self.username.getBounds()
        uscale = self.username.getScale()
        uX = ubounds[0] * uscale[0]

        abounds = self.icon.getBounds()
        ascale = self.icon.getScale()
        aX = abounds[0] * ascale[0]

        trueX = uX + aX - spacing
        trueX = max(-base.getAspectRatio() - aX, trueX)
        self.icon.setPos(trueX, 0, 0)

        # now calculate the buttons positions and enable them
        b2bounds = self.cancel.getBounds()
        b2scale = self.cancel.getScale()

        b2X = b2bounds[1] * b2scale[0]

        trueb2X = b2X + spacing
        trueb2X = min(base.getAspectRatio() - b2X, trueb2X)

        self.cancel.setPos(trueb2X, 0, 0)

    def unlockButtons(self, userId):
        self.cancel['state'] = DGG.NORMAL

    def lockButtons(self):
        self.cancel['state'] = DGG.DISABLED

    def joinDone(self):
        self.lockButtons()
        self.hide()
