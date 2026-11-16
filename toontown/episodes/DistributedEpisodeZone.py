from panda3d.core import *

from direct.distributed import DistributedObject
from direct.gui.DirectGui import *
from direct.interval.IntervalGlobal import *

from panda3d.toontown import CFSpeech, CFTimeout

from otp.avatar.Avatar import Avatar

from toontown.episodes import EpisodeConfig
from toontown.toonbase import ToontownGlobals


class DistributedEpisodeZone(DistributedObject.DistributedObject):

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        self.geom = None
        self.story = None
        self.border = None
        self.movie = None
        self.toonId = None
        self.toon = None
        self.zoneConnections = None
        self.activeIntervals = {}

        self.episodeZoneId = EpisodeConfig.DEFAULT_EPISODE_ZONE

    def announceGenerate(self):
        DistributedObject.DistributedObject.announceGenerate(self)
        self.setup()

    def disable(self):
        self.cleanupIntervals()

        self.cleanupMovie()

        self.geom.removeNode()
        self.geom = None

        if self.story:
            self.story.destroy()
            del self.story

        if self.border:
            self.border.removeNode()
            del self.border

        if hasattr(self, 'music'):
            self.music.stop()
            del self.music

        self.ignoreAll()
        DistributedObject.DistributedObject.disable(self)

    def setToonId(self, toonId):
        self.toonId = toonId
        toon = base.cr.doId2do.get(toonId)
        if toon:
            self.toon = toon

    def setZoneConnections(self, zoneConnections):
        self.zoneConnections = zoneConnections

    def setup(self):
        self.generateGeom()

        place = base.cr.playGame.getPlace()
        if place and hasattr(place, 'fsm') and place.fsm.getCurrentState().getName()\
                and place.fsm.getCurrentState().getName() not in EpisodeConfig.DELAY_MOVIE_STATES:
            # play the movie immediately unless we're in above states (currently just 'doorIn' at the moment)
            self.notify.info('Episode Zone: Place ready. Starting Episode Movie.')
            self.playMovie()
        else:
            self.notify.info('Episode Zone: Waiting for place=%s, has fsm=%s' % (place, hasattr(place, 'fsm')))
            if hasattr(place, 'fsm'):
                self.notify.info('Episode Zone: place state=%s' % place.fsm.getCurrentState().getName())
            self.acceptOnce('enterEpisodeZone', self.playMovie)

    def generateGeom(self):
        self.geom = NodePath('episode-zone-geom')

    def generateMovie(self):
        self.movie = Sequence()

    def playMovie(self):
        self.notify.info('Episode Zone: Start Episode Movie.')
        self.toon.invPage.ignoreOnscreenHooks()
        self.toon.questPage.ignoreOnscreenHooks()
        self.generateMovie()
        if self.movie:
            self.movie.start()

        if __debug__:
            self.accept('advance-movie', self.advanceMovie)
            self._FAST_PLAYRATE = 10.0
            self._NORMAL_PLAYRATE = 1.0

    def advanceMovie(self, state):
        if not __debug__:
            self.notify.debug('Devs only.')
            return
        if not hasattr(self, 'movie') or self.movie is None:
            # don't attempt to set a play rate on a movie that doesn't exist!
            self.notify.debug('No movie to advance.')
            return
        if state:
            self.movie.setPlayRate(self._FAST_PLAYRATE)
        else:
            self.movie.setPlayRate(self._NORMAL_PLAYRATE)

    def lockToon(self, camera=True):
        self.toon.disableAvatarControls()
        self.toon.stopSound()
        self.toon.disableSleeping()

        if camera:
            base.camera.wrtReparentTo(render)
            self.toon.deactivateCamera()

    def releaseToon(self):
        self.toon.attachCamera()
        self.toon.activateCamera()

    def teleportToZone(self, zoneId):
        self.cr.episodeManager.setEpisodeZone(zoneId)
        place = self.cr.playGame.getPlace()
        hoodId = self.cr.playGame.hood.hoodId
        place.requestLeave({'loader': 'episodeLoader',
                            'where': 'episodeZone',
                            'how': 'teleportIn',
                            'hoodId': hoodId,
                            'zoneId': zoneId,
                            'avId': -1,
                            'allowRedirect': 0})

    def generateStory(self):
        geom = OnscreenImage('phase_14/maps/episode-box.png')
        self.story = DirectFrame(relief=None, parent=aspect2d, image=geom, pos=(0.8, 0.0, -0.5), scale=1.3,
                                 image_scale=(0.5, 1.0, 0.2), text='', text_font=ToontownGlobals.getEpisodeFont(),
                                 text_pos=(0, 0.08), text_scale=0.065, text_fg=(0, 0, 0, 1))
        geom.removeNode()

    def speakText(self, textObj, text, scale=0.065, zPos=0.08, delay=0.05):
        textSeq = Sequence()
        fullWord = ''
        for letter in range(len(text)):
            textSeq.append(Func(self.addText, textObj, (fullWord + text[letter]), scale, zPos))
            textSeq.append(Wait(delay))
            fullWord = fullWord + text[letter]
            textSeq.start()

    def addText(self, textObj, text, scale, zPos):
        if textObj:
            textObj['text'] = text
            textObj['text_scale'] = scale
            textObj['text_pos'] = (0, zPos)

    def enterText(self, textObj):
        textObj.setScale(0.1)
        seq = Sequence(Func(textObj.show), LerpScaleInterval(textObj, 0.4, scale=(1.4, 1.4, 1.4)),
                       LerpScaleInterval(textObj, 0.1, scale=(1.2, 1.2, 1.2)),
                       LerpScaleInterval(textObj, 0.1, scale=(1.3, 1.3, 1.3))).start()

    def leaveText(self, textObj):

        def hideText():
            if not textObj.isEmpty():
                textObj.hide()

        seq = Sequence(LerpScaleInterval(textObj, 0.1, scale=(1.4, 1.4, 1.4)),
                       LerpScaleInterval(textObj, 0.4, scale=(0.1, 0.1, 0.1)), Func(hideText)).start()

    def generateBorder(self, type):
        geom = loader.loadModel('phase_3/models/gui/episode_borders')
        self.border = NodePath('episode_border_%s' % type)
        self.border.reparentTo(render2d)
        top = OnscreenImage(parent=self.border, image=geom.find('episode_border_%s_top' % type), pos=(0.0, 0.0, 0.8),
                            scale=(0.125, 1.0, 0.175))
        bot = OnscreenImage(parent=self.border, image=geom.find('episode_border_%s_bot' % type), pos=(0.0, 0.0, -1.05),
                            scale=(0.125, 1.0, 0.175))
        geom.removeNode()

    def playZoneMusic(self):
        musicPath = EpisodeConfig.EPISODES.get(base.cr.episodeManager.episode).get('zone2Music').get(self.episodeZoneId)
        if musicPath:
            self.music = loader.loadMusic(musicPath)
            if self.music:
                base.playMusic(self.music, looping=1)

    def endEpisode(self):
        messenger.send('stopEpisode')

    def callback(self, *args):
        pass

    def storeInterval(self, interval, name):
        if name in self.activeIntervals:
            ival = self.activeIntervals[name]
            self.clearInterval(name, finish=1)
        self.activeIntervals[name] = interval

    def cleanupIntervals(self):
        for interval in list(self.activeIntervals.values()):
            interval.pause()

        self.activeIntervals = {}

    def clearInterval(self, name, finish = 1):
        if name in self.activeIntervals:
            ival = self.activeIntervals[name]
            if finish and self.clearToFinishInterval and ival.isPlaying():
                ival.finish()
            else:
                ival.pause()
            if name in self.activeIntervals:
                del self.activeIntervals[name]
        else:
            self.notify.debug('interval: %s already cleared' % name)

    def finishInterval(self, name):
        if name in self.activeIntervals:
            interval = self.activeIntervals[name]
            if self.clearToFinishInterval and interval.isPlaying():
                interval.finish()

    def cleanupMovie(self):
        if hasattr(self, 'movie') and self.movie is not None:
            if self.movie.isPlaying():
                self.movie.pause()
                if self.clearToFinishInterval:
                    self.movie.finish()
            self.movie = None

    def getChatSequence(self, obj, chat=None, chatType=EpisodeConfig.DISPLAYTALK, wait=0.0,
                        chatFlags=CFSpeech | CFTimeout, dialogue=None, interrupt=1, chatPage=0, preClear=False,
                        postClear=False, hiddenNametag=False):
        """
        Generates a chat sequence for an Avatar/Nametag object.
        """
        seq = Sequence()
        if chat is not None:
            chat = chat.strip()
        hasChat = chat is not None and chat != ''
        if all(x is False for x in (hasChat, preClear, postClear)):
            preClear = True
        hiddenNametag = hiddenNametag if not isinstance(obj, Avatar) else False
        if preClear:
            seq.append(Func(obj.clearChat))
        if hasChat:
            if isinstance(obj, Avatar):
                if chatType == EpisodeConfig.DISPLAYTALK and not hasattr(obj, 'doId'):
                    chatType = EpisodeConfig.CHATABSOLUTE
                if chatType == EpisodeConfig.DISPLAYTALK:
                    seq.append(Func(obj.displayTalk, chat))
                elif chatType == EpisodeConfig.CHATABSOLUTE:
                    seq.append(Func(obj.setChatAbsolute, chat, chatFlags, dialogue, interrupt))
                else:
                    self.notify.warning('ChatType not defined.')
            else:
                if hiddenNametag:
                    seq.append(obj.show)
                seq.append(Func(obj.setChat, chat, chatFlags, chatPage))
            if wait > 0.0:
                seq.append(Wait(wait))
                if postClear:
                    seq.append(Func(obj.clearChat))
                    if hiddenNametag:
                        seq.append(obj.hide)
        else:
            if wait > 0.0:
                seq.append(Wait(wait))
                if postClear and not preClear:
                    seq.append(Func(obj.clearChat))
                    if hiddenNametag:
                        seq.append(obj.hide)
            elif wait <= 0.0 and not preClear and postClear:
                seq.append(Func(obj.clearChat))
                if hiddenNametag:
                    seq.append(obj.hide)
        return seq

    def playChatSequence(self, obj, chat=None, chatType=EpisodeConfig.DISPLAYTALK, wait=0.0,
                        chatFlags=CFSpeech | CFTimeout, dialogue=None, interrupt=1, chatPage=0, preClear=False,
                        postClear=False, hiddenNametag=False):
        """
        Plays the chat sequence without returning it. Useful for things like clearing chat after a movie, I suppose.
        TODO(maybe): probably store this interval for cleanup later?
        """
        self.getChatSequence(obj, chat=chat, chatType=chatType, wait=wait, chatFlags=chatFlags, dialogue=dialogue,
                             interrupt=interrupt, chatPage=chatPage, preClear=preClear, postClear=postClear,
                             hiddenNametag=hiddenNametag).start()

    # in case somebody wants to use a shorter version of playChatSequence
    playChat = playChatSequence

    def setLocalPageChat(self, obj, message, quitButton, extraChatFlags=None, dialogueList=None):
        if not dialogueList:
            dialogueList = []
        if not isinstance(obj, Avatar):
            self.notify.warning("Cannot play page chat for non-Avatar objects!")
            return
        if isinstance(message, (tuple, list)):
            message = "\x07".join(message)
        if not isinstance(message, (bytes, str, bytearray)):
            self.notify.warning("Cannot use dialogue as is for page chat!")
            return
        obj.setLocalPageChat(message, quitButton, extraChatFlags=extraChatFlags, dialogueList=dialogueList)

    @property
    def clearToFinishInterval(self):
        try:
            return base.isPlayingGame()
        except Exception:
            return False

    @property
    def dnaStore(self):
        try:
            if base.cr.playGame.hood.dnaStore is not None:
                return base.cr.playGame.hood.dnaStore
            elif base.cr.playGame.dnaStore is not None:
                return base.cr.playGame.dnaStore
            else:
                self.notify.warning('Failed to acquire dnaStore!')
                return None
        except Exception:
            try:
                if base.cr.playGame.dnaStore:
                    return base.cr.playGame.dnaStore
                else:
                    self.notify.warning('Failed to acquire dnaStore!')
                    return None
            except Exception:
                self.notify.warning('Failed to acquire dnaStore!')
                return None
