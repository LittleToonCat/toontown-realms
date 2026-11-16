from direct.gui.DirectButton import DirectButton
from direct.gui.DirectGui import DGG
from direct.directnotify import DirectNotifyGlobal
# from direct.discord_rpc import DISCORD_REPLY_YES, DISCORD_REPLY_NO
DISCORD_REPLY_NO = 0
DISCORD_REPLY_YES = 1

from toontown.toonbase import ToontownGlobals, TTLocalizer
from toontown.toontowngui.AnnounceDialog import AnnounceDialog


class DiscordJoinDialog(AnnounceDialog):
    notify = DirectNotifyGlobal.directNotify.newCategory('DiscordJoinDialog')

    def __init__(self):
        AnnounceDialog.__init__(self)

        buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        okImageList = (buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'),
                      buttons.find('**/ChtBx_OKBtn_Rllvr'))
        self.okay = DirectButton(parent=self, relief=None, geom=okImageList, command=self.joinDone)
        buttons.removeNode()

        self.setDialogScale()

    def setDialogScale(self):
        if hasattr(self, 'okay') and self.okay:
            self.okay.setScale(0.75, 1.0, 0.75)
            AnnounceDialog.setDialogScale(self)

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
        b1bounds = self.okay.getBounds()
        b1scale = self.okay.getScale()

        b2bounds = self.cancel.getBounds()
        b2scale = self.cancel.getScale()

        uX = ubounds[1] * uscale[0]
        b1X = b1bounds[1] * b1scale[0]
        b2X = b2bounds[1] * b2scale[0]

        trueb1X = uX + b1X + spacing
        trueb2X = trueb1X + b2X + spacing
        trueb2X = min(base.getAspectRatio() - b2X, trueb2X)
        trueb1X = min(base.getAspectRatio() - b2X - b1X - spacing, trueb1X)

        self.okay.setPos(trueb1X, 0, 0)
        self.cancel.setPos(trueb2X, 0, 0)

    def unlockButtons(self, userId):
        self.okay['extraArgs'] = [userId, DISCORD_REPLY_YES]
        self.cancel['extraArgs'] = [userId, DISCORD_REPLY_NO]
        self.okay['state'] = DGG.NORMAL
        self.cancel['state'] = DGG.NORMAL

    def lockButtons(self):
        if hasattr(self, 'okay') and self.okay:
            self.okay['state'] = DGG.DISABLED
            self.cancel['state'] = DGG.DISABLED

    def joinDone(self, userId, response):
        self.lockButtons()
        base.cr.discordManager.respond(userId, response)
