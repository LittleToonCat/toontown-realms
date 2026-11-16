from panda3d.core import TextNode

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.ClockDelta import globalClockDelta

from toontown.toonbase import TTLocalizer, ToontownGlobals
from toontown.parties.PartyGlobals import PhaseToMusicDataSz, ActivityIds, getMusicRepeatTimes, MUSIC_PATH
from toontown.parties.DistributedPartyJukeboxActivityBase import DistributedPartyJukeboxActivityBase
from toontown.parties.PartyUtils import getPartyActivityIcon


class DistributedSafezoneJukebox(DistributedPartyJukeboxActivityBase):
    notify = directNotify.newCategory('DistributedSafezoneJukebox')

    def __init__(self, cr):
        # The ID doesn't really matter either as long as it's a jukebox so it can have the correct sign
        DistributedPartyJukeboxActivityBase.__init__(self, cr, ActivityIds.PartyJukebox, PhaseToMusicDataSz)
        self.activityName = TTLocalizer.SafezoneJukeboxTitle
        self.localAvatarInBattle = False

    def announceGenerate(self):
        DistributedPartyJukeboxActivityBase.announceGenerate(self)
        self.root.setZ(self.z)
        self.accept('ToonBattleIdUpdate', self.__handleBattle)

    def disable(self):
        self.ignore('ToonBattleIdUpdate')
        self.localAvatarInBattle = False
        DistributedPartyJukeboxActivityBase.disable(self)

    def setZ(self, z):
        self.z = z

    def setPartyDoId(self, partyDoId):
        # Don't check for an actual party cuz
        # this isn't meant to be used in parties
        self.party = partyDoId

    def isUserHost(self):
        return base.localAvatar.getAccessLevel() >= 200

    def load(self):
        DistributedPartyJukeboxActivityBase.load(self)
        newTexture = loader.loadTexture('phase_13/maps/tt_t_ara_pty_jukeboxPurple.png')
        case = self.jukebox.find('**/jukeboxGlass')
        if not case.isEmpty():
            case.setTexture(newTexture, 1)
        body = self.jukebox.find('**/jukeboxBody')
        if not body.isEmpty():
            body.setTexture(newTexture, 1)

    def loadSign(self):
        self.sign = self.root.attachNewNode('%sSign' % self.activityName)
        self.signModel = loader.loadModel('phase_13/models/parties/eventSign')
        self.signModel.reparentTo(self.sign)
        self.signFlat = self.signModel.find('**/sign_flat')
        self.signFlatWithNote = self.signModel.find('**/sign_withNote')
        self.signTextLocator = self.signModel.find('**/signText_locator')
        activityIconsModel = loader.loadModel('phase_4/models/parties/eventSignIcons')
        textureNodePath = getPartyActivityIcon(activityIconsModel, 'PartyJukebox')
        textureNodePath.setPos(0.0, -0.02, 2.2)
        textureNodePath.setScale(2.35)
        textureNodePath.copyTo(self.signFlat)
        textureNodePath.copyTo(self.signFlatWithNote)
        text = TextNode('noteText')
        text.setTextColor(0.2, 0.1, 0.7, 1.0)
        text.setAlign(TextNode.ACenter)
        text.setFont(ToontownGlobals.getInterfaceFont())
        text.setWordwrap(10.0)
        text.setText('')
        self.noteText = self.signFlatWithNote.attachNewNode(text)
        self.noteText.setPosHpr(self.signTextLocator, 0.0, 0.0, 0.2, 0.0, 0.0, 0.0)
        self.noteText.setScale(0.2)
        self.signFlatWithNote.stash()
        self.signTextLocator.stash()
        activityIconsModel.removeNode()

    def _play(self, phase, filename, length, timestamp):
        self.music = base.loader.loadMusic((MUSIC_PATH + '%s') % (phase, filename))
        self.timestamp = timestamp
        self.length = length
        if self.music:
            if not self.localAvatarInBattle:
                self.__doPlay(timestamp, length)
            jukeboxAnimControl = self.jukebox.getAnimControl('dance')
            if not jukeboxAnimControl.isPlaying():
                self.jukebox.loop('dance', fromFrame=0, toFrame=48)
            self.currentSongData = (phase, filename)

    def __doPlay(self, timestamp, length):
        if self._checkPartyValidity() and hasattr(base.cr.playGame.getPlace().loader, 'music') and base.cr.playGame.getPlace().loader.music:
            base.cr.playGame.getPlace().loader.music.stop()
        ts = globalClockDelta.localElapsedTime(timestamp)
        self.music.setTime(ts)
        self.music.setLoopCount(getMusicRepeatTimes(length))
        self.music.play()

    def __handleBattle(self, doId):
        if doId == base.localAvatar.doId:
            battleFlag = base.localAvatar.battleId != 0
            self.localAvatarInBattle = battleFlag
            if not battleFlag and self.music:
                self.__doPlay(self.timestamp, self.length)
