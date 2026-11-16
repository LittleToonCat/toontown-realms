from direct.fsm import State
from typing import Optional, Dict

from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator
from direct.gui.DirectButton import DirectButton
from direct.gui.DirectLabel import DirectLabel
from direct.interval.IntervalManager import ivalMgr
from direct.showbase.MessengerGlobal import messenger
from direct.showbase.ShowBaseGlobal import aspect2d
from direct.task.TaskManagerGlobal import taskMgr
from panda3d.toontown import NametagGlobals

from otp.audio import AdaptiveMusic
from otp.avatar import Avatar
from otp.avatar.Avatar import teleportNotify
from otp.distributed import OTPClientRepository
from otp.distributed import OtpDoGlobals
from otp.distributed import PotentialAvatar
from otp.distributed.OtpDoGlobals import *
from otp.otpbase import OTPLocalizer, OTPGlobals
from otp.otpbase.PythonUtil import Queue, ScratchPad, safeRepr, itype, Functor
from toontown.distributed import DelayDelete
from toontown.episodes import EpisodeConfig
from toontown.hood import StreetSign, ZoneUtil
from toontown.launcher.DownloadForceAcknowledge import *
from toontown.login import AvatarChooser
from toontown.makeatoon import MakeAToon
from toontown.makeatoon.fools import MakeAToon as FoolsMakeAToon
from toontown.makeatoon.retro import MakeAToon as RetroMakeAToon
from toontown.moviemaker.MovieMakerMainMenu import MovieMakerMainMenu
from toontown.parties import ToontownTimeManager
from toontown.pets import PetDetail, PetHandle

from toontown.social import AvatarHandle
from toontown.social import SocialMenu
from toontown.social import ToontownFriendSecret
from toontown.social.SocialGlobals import VisibilityTypes
from toontown.toon import LocalToon
from toontown.toon import Toon
from toontown.toon import ToonDNA
from toontown.toonbase import ToonBaseGlobal, ClientSettings
from toontown.toonbase.ToontownGlobals import *
from toontown.toontowngui import TTDialog
from toontown.toontowngui import ToontownLoadingBlocker
from . import HoodMgr
from . import PlayGame
from .ToontownMsgTypes import *
from ..toonbase.ToonBaseGlobal import base

try:
    from os import unsetenv
except ImportError:
    pass


class ToontownClientRepository(OTPClientRepository.OTPClientRepository):
    SupportTutorial = 1
    GameGlobalsId = OTP_DO_ID_TOONTOWN
    SetZoneDoneEvent = 'TCRSetZoneDone'
    EmuSetZoneDoneEvent = 'TCREmuSetZoneDone'
    SetInterest = 'Set'
    ClearInterest = 'Clear'
    ClearInterestDoneEvent = 'TCRClearInterestDone'
    KeepSubShardObjects = False

    def __init__(self, serverVersion, launcher = None):
        OTPClientRepository.OTPClientRepository.__init__(self, serverVersion, launcher, playGame=PlayGame.PlayGame)
        self._playerAvDclass = self.dclassesByName['DistributedToon']

        self.toons = {}
        if self.http.getVerifySsl() != HTTPClient.VSNoVerify:
            self.http.setVerifySsl(HTTPClient.VSNoDateCheck)

        self.__forbidCheesyEffects = 0
        self.friendManager = None
        self.speedchatRelay = None
        self.trophyManager = None
        self.bankManager = None
        self.catalogManager = None
        self.welcomeValleyManager = None
        self.newsManager = None
        self.streetSign = None
        self.distributedDistrict = None
        self.partyManager = None
        self.inGameNewsMgr = None
        self.whitelistMgr = None
        self.propGenerator = None
        self.music: Optional[AdaptiveMusic.AdaptiveMusic] = None
        self.toontownTimeManager = ToontownTimeManager.ToontownTimeManager()
        self.gameServicesManager = self.generateGlobalObject(OtpDoGlobals.OTP_DO_ID_TOONTOWN_GAME_SERVICES_MANAGER, 'TTGameServicesManager')
        self.avatarFriendsManager = self.generateGlobalObject(OtpDoGlobals.OTP_DO_ID_AVATAR_FRIENDS_MANAGER, 'AvatarFriendsManager')
        self.playerFriendsManager = self.generateGlobalObject(OtpDoGlobals.OTP_DO_ID_PLAYER_FRIENDS_MANAGER, 'PlayerFriendsManager')
        self.ttrmSocialManager = self.generateGlobalObject(OtpDoGlobals.OTP_DO_ID_TTRM_SOCIAL_MANAGER, 'TTRMSocialManager')
        self.deliveryManager = self.generateGlobalObject(OtpDoGlobals.OTP_DO_ID_TOONTOWN_DELIVERY_MANAGER, 'DistributedDeliveryManager')
        self.codeRedemptionManager = None

        self.furnitureManager = None
        self.objectManager = None
        self.onlineAvatars = {}
        self.invisibleAvatars = []
        self.offlineAvatars = {}
        self.offlineFriends = {}
        self.petHandle = (0, None)
        self.__queryAvatarMap = {}
        self.hoodMgr = HoodMgr.HoodMgr(self)
        self.setZonesEmulated = 0
        self.old_setzone_interest_handle = None
        self.setZoneQueue = Queue()
        self.accept(ToontownClientRepository.SetZoneDoneEvent, self._handleEmuSetZoneDone)
        self._deletedSubShardDoIds = set()
        self.toonNameDict = {}
        self.gameFSM.addState(State.State('skipTutorialRequest', self.enterSkipTutorialRequest, self.exitSkipTutorialRequest, ['playGame', 'gameOff', 'tutorialQuestion']))
        state = self.gameFSM.getStateNamed('waitOnEnterResponses')
        state.addTransition('skipTutorialRequest')
        state = self.gameFSM.getStateNamed('playGame')
        state.addTransition('skipTutorialRequest')
        self.wantCogdominiums = base.config.GetBool('want-cogdominiums', 1)
        self.wantEmblems = base.config.GetBool('want-emblems', 0)
        self.karts = {}
        self.tutorialManager = None
        self.magicWordManager = None
        self.moddingManager = None
        self.discordManager = None
        self.episodeManager = None
        self.serverName = None
        self.serverDescription = None
        self.serverIconPath = None

        self.guiPopupShown = 0
        self.collisionsToggled = False
        self.renderCollisionsToggled = False
        self.vertexPaintingToggled = False
        self.SGMeterToggled = False
        self.tightboundsToggled = False
        self.boundsToggled = False
        self.frontfaceCullingEnabled = False

        # CommonFilters
        self.bloomEnabled = False
        self.HDREnabled = False
        self.ambientOcclusionEnabled = False
        self.cartoonInkEnabled = False
        self.sRGBEnabled = False
        self.invertedEnabled = False

        # Make-A-Cog Easter egg
        # enabled by setting all 3 sliders to 0 for the shticker book background option
        self.makeACogEgg = False

        self.buildLot = None

        self.gamemode = 0
        if base.config.GetBool('tt-node-check', 0):
            for species in ToonDNA.toonSpeciesTypes:
                for head in ToonDNA.getHeadList(species):
                    for torso in ToonDNA.toonTorsoTypes:
                        for legs in ToonDNA.toonLegTypes:
                            for gender in ('m', 'f'):
                                print('species: %s, head: %s, torso: %s, legs: %s, gender: %s' % (species,
                                 head,
                                 torso,
                                 legs,
                                 gender))
                                dna = ToonDNA.ToonDNA()
                                dna.newToon((head,
                                 torso,
                                 legs,
                                 gender))
                                toon = Toon.Toon()
                                try:
                                    toon.setDNA(dna)
                                except Exception as e:
                                    print(e)

    def congratulations(self, avatarChoice):
        self.acceptedScreen = loader.loadModel('phase_3/models/gui/toon_council')
        self.acceptedScreen.setScale(0.667)
        self.acceptedScreen.reparentTo(aspect2d)
        buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        self.acceptedBanner = DirectLabel(parent=self.acceptedScreen, relief=None, text=OTPLocalizer.CRNameCongratulations, text_scale=0.18, text_fg=Vec4(0.6, 0.1, 0.1, 1), text_pos=(0, 0.05), text_font=getMinnieFont())
        newName = avatarChoice.approvedName
        self.acceptedText = DirectLabel(parent=self.acceptedScreen, relief=None, text=OTPLocalizer.CRNameAccepted % newName, text_scale=0.125, text_fg=Vec4(0, 0, 0, 1), text_pos=(0, -0.15))
        self.okButton = DirectButton(parent=self.acceptedScreen, image=(buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr')), relief=None, text='Ok', scale=1.5, text_scale=0.05, text_pos=(0.0, -0.1), pos=(0, 0, -1), command=self.__handleCongrats, extraArgs=[avatarChoice])
        buttons.removeNode()
        base.transitions.noFade()

    def __handleCongrats(self, avatarChoice):
        self.acceptedBanner.destroy()
        self.acceptedText.destroy()
        self.okButton.destroy()
        self.acceptedScreen.removeNode()
        del self.acceptedScreen
        del self.okButton
        del self.acceptedText
        del self.acceptedBanner
        self.gameServicesManager.sendAcknowledgeAvatarName(avatarChoice.id,
                                                           lambda: self.loginFSM.request('waitForSetAvatarResponse', [avatarChoice]))

    def betterlucknexttime(self, avList, index):
        self.rejectDoneEvent = 'rejectDone'
        self.rejectDialog = TTDialog.TTGlobalDialog(doneEvent=self.rejectDoneEvent, message=TTLocalizer.NameShopNameRejected, style=TTDialog.Acknowledge)
        self.rejectDialog.show()
        self.acceptOnce(self.rejectDoneEvent, self.__handleReject, [avList, index])
        base.transitions.noFade()

    def __handleReject(self, avList, index):
        self.rejectDialog.cleanup()
        avid = 0
        for k in avList:
            if k.position == index:
                avid = k.id

        if avid == 0:
            self.notify.error('Avatar rejected not found in avList.  Index is: ' + str(index))
        self.gameServicesManager.sendAcknowledgeAvatarName(avid, lambda: self.loginFSM.request('waitForAvatarList'))

    def __doPlayMusic(self):
        if not self.music and base.musicManagerIsValid:
            retroMode = ClientSettings.ClassicLoadingScreen.get()
            if retroMode:
                music = AdaptiveMusic.AdaptiveMusic('phase_3/audio/bgm/tt_theme.ogg',
                                                    'phase_3/audio/bgm/tt_theme.ogg')
            else:
                music = AdaptiveMusic.AdaptiveMusic('phase_3/audio/bgm/ttrm_s_gen_mainTheme_primary.ogg',
                                                    'phase_3/audio/bgm/ttrm_s_gen_mainTheme_secondary.ogg')
                #music = AdaptiveMusic.AdaptiveMusic('phase_8/audio/bgm/ttrm_s_ara_bgm_ddlo_nbrhood_1.ogg',
                #                                    'phase_8/audio/bgm/ttrm_s_ara_bgm_ddlo_nbrhood_1.ogg')
            music.play(looping = True)
            self.music = music

    def enterMainMenu(self):
        OTPClientRepository.OTPClientRepository.enterMainMenu(self)

        self.__doPlayMusic()
        self.music.changeMix(AdaptiveMusic.FULL_A)

    def enterChooseAvatar(self, avList):
        self.mainMenu.unload()

        self.__doPlayMusic()
        self.music.changeMix(AdaptiveMusic.FULL_B)
        ModelPool.garbageCollect()
        TexturePool.garbageCollect()
        self.sendSetAvatarIdMsg(0)
        self.clearFriendState()

        self.discordManager.setInfo(self.discordManager.getState(), None, DefaultIcon,
                                    TTLocalizer.DiscordPickAToon, None, None)
        self.handler = self.handleMessageType
        self.avChoiceDoneEvent = 'avatarChooserDone'
        self.avChoice = AvatarChooser.AvatarChooser(avList, self.loginFSM, self.avChoiceDoneEvent)
        self.avChoice.load(self.isPaid())
        self.avChoice.enter()

        self.accept(self.avChoiceDoneEvent, self.__handleAvatarChooserDone, [avList])
        if base.config.GetBool('want-gib-loader', 1):
            self.loadingBlocker = ToontownLoadingBlocker.ToontownLoadingBlocker(avList)

    def enterMovieMaker(self):
        if self.music:
            self.music.stop()
            self.music = None
        self.mainMenu.unload()
        self.movieMakerMenu = MovieMakerMainMenu()
        self.movieMakerMenu.request('Home')

    def enterLevelEditor(self):
        if self.music:
            self.music.stop()
            self.music = None
        self.mainMenu.unload()

        from ..leveleditor.LevelEditorMainMenu import LevelEditorMainMenu
        self.levelEditorMenu = LevelEditorMainMenu()
        self.levelEditorMenu.request('Home')

    def __handleAvatarChooserDone(self, avList, doneStatus):
        done = doneStatus['mode']
        if done == 'exit':
            self.loginFSM.request('shutdown')
            return
        if base.cr.episodeManager.getEpisode():
            self.notify.info('================')
            self.notify.info('Chose episode: %s' % EpisodeConfig.EPISODES[base.cr.episodeManager.getEpisode()].get('name'))
            self.notify.info('Requesting Temporary Toon.')
            self.notify.info('================')
            avatarChoice = PotentialAvatar.PotentialAvatar(6, ['', '', '', ''], '', 6, '')
            self.loginFSM.request('waitForSetAvatarResponse', [avatarChoice])
            return
        else:
            index = self.avChoice.getChoice()
        for av in avList:
            if av.position == index:
                avatarChoice = av
                self.notify.info('================')
                self.notify.info('Chose avatar id: %s' % av.id)
                self.notify.info('Chose avatar name: %s' % av.name)
                dna = ToonDNA.ToonDNA()
                dna.makeFromNetString(av.dna)
                if base.logPrivateInfo:
                    self.notify.info('Chose avatar dna: %s' % (dna.asTuple(),))
                    self.notify.info('Chose avatar position: %s' % av.position)
                self.notify.info('================')

        if done == 'chose':
            self.avChoice.exit()
            if avatarChoice.approvedName != '':
                self.congratulations(avatarChoice)
                avatarChoice.approvedName = ''
            elif avatarChoice.rejectedName != '':
                avatarChoice.rejectedName = ''
                self.betterlucknexttime(avList, index)
            else:
                self.loginFSM.request('waitForSetAvatarResponse', [avatarChoice])
        elif done == 'nameIt':
            self.accept('downloadAck-response', self.__handleDownloadAck, [avList, index])
            self.downloadAck = DownloadForceAcknowledge('downloadAck-response')
            self.downloadAck.enter(4)
        elif done == 'create':
            self.loginFSM.request('createAvatar', [avList, index])
        elif done == 'delete':
            self.loginFSM.request('waitForDeleteAvatarResponse', [avatarChoice])

    def __handleDownloadAck(self, avList, index, doneStatus):
        if doneStatus['mode'] == 'complete':
            self.goToPickAName(avList, index)
        else:
            self.loginFSM.request('chooseAvatar', [avList])
        self.downloadAck.exit()
        self.downloadAck = None
        self.ignore('downloadAck-response')

    def exitChooseAvatar(self):
        self.handler = None
        self.avChoice.exit()
        self.avChoice.unload()
        self.avChoice = None
        self.ignore(self.avChoiceDoneEvent)

    def goToPickAName(self, avList, index):
        self.avChoice.exit()
        self.loginFSM.request('createAvatar', [avList, index])

    def enterCreateAvatar(self, avList, index, newDNA = None):
        if self.music:
            self.music.stop()
            self.music = None

        if newDNA != None:
            self.newPotAv = PotentialAvatar.PotentialAvatar('deleteMe', ['', '', '', ''], newDNA.makeNetString(), index, 1)
            avList.append(self.newPotAv)

        base.transitions.noFade()

        holidayIndex = loader.loadingScreen.getActiveHoliday()
        retroMode = ClientSettings.ClassicMakeAToon.get()
        if holidayIndex == HolidayAprilFools or self.makeACogEgg:
            self.avCreate = FoolsMakeAToon.MakeAToon(self.loginFSM, avList, 'makeAToonComplete', index)
        elif retroMode:
            self.avCreate = RetroMakeAToon.MakeAToon(self.loginFSM, avList, 'makeAToonComplete', index, self.isPaid())
        else:
            self.avCreate = MakeAToon.MakeAToon(self.loginFSM, avList, 'makeAToonComplete', index, self.isPaid())

        self.avCreate.load()
        self.avCreate.enter()

        self.accept('makeAToonComplete', self.__handleMakeAToon, [avList, index])
        self.accept('nameShopPost', self.relayMessage)

    def relayMessage(self, dg):
        self.send(dg)

    def __handleMakeAToon(self, avList, avPosition):
        done = self.avCreate.getDoneStatus()
        if done == 'cancel':
            if hasattr(self, 'newPotAv'):
                if self.newPotAv in avList:
                    avList.remove(self.newPotAv)
            self.avCreate.exit()
            self.loginFSM.request('chooseAvatar', [avList])
        elif done == 'created':
            self.avCreate.exit()
            if not base.launcher or base.launcher.getPhaseComplete(3.5):
                for i in avList:
                    if i.position == avPosition:
                        newPotAv = i

                self.loginFSM.request('waitForSetAvatarResponse', [newPotAv])
            else:
                self.loginFSM.request('chooseAvatar', [avList])
        else:
            self.notify.error('Invalid doneStatus from MakeAToon: ' + str(done))

    def exitCreateAvatar(self):
        self.ignore('makeAToonComplete')
        self.ignore('nameShopPost')
        self.avCreate.unload()
        self.avCreate = None
        self.handler = None
        if hasattr(self, 'newPotAv'):
            del self.newPotAv

    def handleAvatarResponseMsg(self, avatarId, di):
        self.cleanupWaitingForDatabase()
        dclass = self.dclassesByName['DistributedToon']
        NametagGlobals.setMasterArrowsOn(0)
        loader.beginBulkLoad('localAvatarPlayGame', OTPLocalizer.CREnteringToontown, 414, 1, TTLocalizer.TIP_GENERAL)
        localAvatar = LocalToon.LocalToon(self)
        localAvatar.dclass = dclass
        base.localAvatar = localAvatar
        ToonBaseGlobal.localAvatar = localAvatar
        __builtins__['localAvatar'] = base.localAvatar
        NametagGlobals.setToon(base.localAvatar)
        localAvatar.doId = avatarId
        self.localAvatarDoId = avatarId
        parentId = None
        zoneId = None
        localAvatar.setLocation(parentId, zoneId)
        localAvatar.generateInit()
        localAvatar.generate()
        dclass.receiveUpdateBroadcastRequiredOwner(localAvatar, di)
        localAvatar.announceGenerate()
        localAvatar.postGenerateMessage()
        self.doId2do[avatarId] = localAvatar
        localAvatar.initInterface()
        self.sendOfflineFriendsRequest()
        self.loginFSM.request('playingGame')

    def getAvatarDetails(self, avatar, func, *args):
        pad = ScratchPad()
        pad.func = func
        pad.args = args
        pad.avatar = avatar
        pad.delayDelete = DelayDelete.DelayDelete(avatar, 'getAvatarDetails')
        avId = avatar.doId
        self.__queryAvatarMap[avId] = pad
        self.__sendGetAvatarDetails(avId)

    def cancelAvatarDetailsRequest(self, avatar):
        avId = avatar.doId
        if avId in self.__queryAvatarMap:
            pad = self.__queryAvatarMap.pop(avId)
            pad.delayDelete.destroy()

    def __sendGetAvatarDetails(self, avId):
        self.ttrmSocialManager.d_getAvatarDetails(avId)

    def handleGetAvatarDetailsResp(self, avId, fields):
        self.notify.info('Got query response for avatar %d.' % avId)
        try:
            pad = self.__queryAvatarMap[avId]
        except:
            self.notify.warning('Received unexpected or outdated details for avatar %d.' % avId)
            return

        del self.__queryAvatarMap[avId]
        gotData = 0
        dclassName = pad.args[0]
        dclass = self.dclassesByName[dclassName]
        for currentField in fields:
            getattr(pad.avatar, currentField[0])(*currentField[1:])

        gotData = 1
        if isinstance(pad.func, bytes):
            messenger.send(pad.func, list((gotData, pad.avatar) + pad.args))
        else:
            pad.func(*(gotData, pad.avatar) + pad.args)

        pad.delayDelete.destroy()

    def enterPlayingGame(self, *args, **kArgs):
        OTPClientRepository.OTPClientRepository.enterPlayingGame(self, *args, **kArgs)
        self.gameFSM.request('waitOnEnterResponses', [None,
         base.localAvatar.defaultZone,
         base.localAvatar.defaultZone,
         -1])
        self._userLoggingOut = False
        if not self.streetSign:
            self.streetSign = StreetSign.StreetSign()

    def exitPlayingGame(self):
        ivalMgr.interrupt()
        if self.objectManager != None:
            self.objectManager.destroy()
            self.objectManager = None
        ToontownFriendSecret.unloadFriendSecret()
        SocialMenu.unloadSocialMenu()
        messenger.send('cancelFriendInvitation')
        base.removeGlitchMessage()
        taskMgr.remove('avatarRequestQueueTask')
        OTPClientRepository.OTPClientRepository.exitPlayingGame(self)
        if hasattr(base, 'localAvatar') and base.localAvatar is not None:
            base.camera.reparentTo(render)
            base.camera.setPos(0, 0, 0)
            base.camera.setHpr(0, 0, 0)
            del self.doId2do[base.localAvatar.getDoId()]
            if base.localAvatar.getDelayDeleteCount() != 0:
                self.notify.error('could not delete localAvatar, delayDeletes=%s' % (base.localAvatar.getDelayDeleteNames(),))
            base.localAvatar.deleteOrDelay()
            base.localAvatar.detectLeaks()
            NametagGlobals.setToon(base.cam)
            del base.localAvatar
            del __builtins__['localAvatar']
        loader.abortBulkLoad()
        base.transitions.noTransitions()
        if self._userLoggingOut:
            self.detectLeaks(okTasks=[], okEvents=['destroy-ToontownLoadingScreenTitle', 'destroy-ToontownLoadingScreenTip', 'destroy-ToontownLoadingScreenWaitBar'])

    def enterGameOff(self):
        OTPClientRepository.OTPClientRepository.enterGameOff(self)

    def enterWaitOnEnterResponses(self, shardId, hoodId, zoneId, avId):
        self.resetDeletedSubShardDoIds()
        OTPClientRepository.OTPClientRepository.enterWaitOnEnterResponses(self, shardId, hoodId, zoneId, avId)

    def enterSkipTutorialRequest(self, hoodId, zoneId, avId):
        self.handlerArgs = {'hoodId': hoodId,
         'zoneId': zoneId,
         'avId': avId}
        self.__requestSkipTutorial(hoodId, zoneId, avId)

    def __requestSkipTutorial(self, hoodId, zoneId, avId):
        self.notify.debug('requesting skip tutorial')
        self.acceptOnce('skipTutorialAnswered', self.__handleSkipTutorialAnswered, [hoodId, zoneId, avId])
        messenger.send('requestSkipTutorial')
        self.waitForDatabaseTimeout(requestName='RequestSkipTutorial')

    def __handleSkipTutorialAnswered(self, hoodId, zoneId, avId, allOk):
        if allOk:
            # Handle default zone
            defaultZone = self.moddingManager.getDefaultZone()
            if not self.legitMode and defaultZone != ToontownCentral:
                hoodId = ZoneUtil.getCanonicalHoodId(defaultZone)
                zoneId = ZoneUtil.getCanonicalZoneId(defaultZone)
                # This is necessary for the spawn points to be used
                base.queuedHood = hood2Id[zoneId][0]
            else:
                hoodId = self.handlerArgs['hoodId']
                zoneId = self.handlerArgs['zoneId']
            avId = self.handlerArgs['avId']
            self.gameFSM.request('playGame', [hoodId, zoneId, avId])
        else:
            self.notify.warning('allOk is false on skip tutorial, forcing the tutorial.')
            self.gameFSM.request('tutorialQuestion', [hoodId, zoneId, avId])

    def exitSkipTutorialRequest(self):
        self.cleanupWaitingForDatabase()
        self.handler = None
        self.handlerArgs = None
        self.ignore('skipTutorialAnswered')

    def enterTutorialQuestion(self, hoodId, zoneId, avId):
        self.__requestTutorial(hoodId, zoneId, avId)

    def __requestTutorial(self, hoodId, zoneId, avId):
        self.notify.debug('requesting tutorial')
        self.acceptOnce('startTutorial', self.__handleStartTutorial, [avId])
        messenger.send('requestTutorial')
        self.waitForDatabaseTimeout(requestName='RequestTutorial')

    def __handleStartTutorial(self, avId, zoneId):
        self.gameFSM.request('playGame', [Tutorial, zoneId, avId])

    def exitTutorialQuestion(self):
        self.cleanupWaitingForDatabase()
        self.handler = None
        self.handlerArgs = None
        self.ignore('startTutorial')
        taskMgr.remove('waitingForTutorial')

    def enterPlayEpisode(self, avId, episode):
        self.__requestEpisode(avId, episode)

    def __requestEpisode(self, avId, episode):
        self.notify.debug('requesting episode')
        self.acceptOnce('startEpisode', self.__handleStartEpisode, [avId])
        messenger.send('requestEpisode', [episode])
        self.waitForDatabaseTimeout(requestName='RequestEpisode')

    def __handleStartEpisode(self, avId, zoneId):
        self.gameFSM.request('playGame', [Episode, zoneId, avId])

    def enterCloseShard(self, loginState = None):
        OTPClientRepository.OTPClientRepository.enterCloseShard(self, loginState)
        self.handler = self.handleCloseShard
        self._removeLocalAvFromStateServer()

    def handleCloseShard(self, msgType, di):
        if msgType == CLIENT_ENTER_OBJECT_REQUIRED:
            di2 = PyDatagramIterator(di.getDatagram())
            parentId = di2.getUint32()
            if self._doIdIsOnCurrentShard(parentId):
                return
        elif msgType == CLIENT_ENTER_OBJECT_REQUIRED_OTHER:
            di2 = PyDatagramIterator(di.getDatagram())
            parentId = di2.getUint32()
            if self._doIdIsOnCurrentShard(parentId):
                return
        elif msgType == CLIENT_OBJECT_SET_FIELD:
            di2 = PyDatagramIterator(di.getDatagram())
            doId = di2.getUint32()
            if self._doIdIsOnCurrentShard(doId):
                return
        self.handleMessageType(msgType, di)

    def _logFailedDisable(self, doId, ownerView):
        if doId not in self.doId2do and doId in self._deletedSubShardDoIds:
            return
        OTPClientRepository.OTPClientRepository._logFailedDisable(self, doId, ownerView)

    def exitCloseShard(self):
        OTPClientRepository.OTPClientRepository.exitCloseShard(self)
        self.ignore(ToontownClientRepository.ClearInterestDoneEvent)
        self.handler = None

    def isShardInterestOpen(self):
        return self.old_setzone_interest_handle is not None or self.uberZoneInterest is not None

    def resetDeletedSubShardDoIds(self):
        self._deletedSubShardDoIds.clear()

    def dumpAllSubShardObjects(self):
        if self.KeepSubShardObjects:
            return
        isNotLive = not base.cr.isLive()
        if isNotLive:
            try:
                localAvatar
            except:
                self.notify.info('dumpAllSubShardObjects')
            else:
                self.notify.info('dumpAllSubShardObjects: defaultShard is %s' % localAvatar.defaultShard)

            ignoredClasses = ('MagicWordManager', 'TimeManager', 'DistributedDistrict', 'FriendManager', 'NewsManager', 'ToontownMagicWordManager', 'WelcomeValleyManager', 'DistributedTrophyMgr', 'CatalogManager', 'DistributedBankMgr', 'EstateManager', 'RaceManager', 'SafeZoneManager', 'DeleteManager', 'TutorialManager', 'ToontownDistrict', 'DistributedDeliveryManager', 'DistributedPartyManager', 'AvatarFriendsManager', 'InGameNewsMgr', 'WhitelistMgr', 'TTCodeRedemptionMgr')
        messenger.send('clientCleanup')
        for avId, pad in list(self.__queryAvatarMap.items()):
            pad.delayDelete.destroy()

        self.__queryAvatarMap = {}
        delayDeleted = []
        doIds = list(self.doId2do.keys())
        for doId in doIds:
            obj = self.doId2do[doId]
            if isNotLive:
                ignoredClass = obj.__class__.__name__ in ignoredClasses
                if not ignoredClass and obj.parentId != localAvatar.defaultShard:
                    self.notify.info('dumpAllSubShardObjects: %s %s parent %s is not defaultShard' % (obj.__class__.__name__, obj.doId, obj.parentId))
            if obj.parentId == localAvatar.defaultShard and obj is not localAvatar:
                if obj.neverDisable:
                    if isNotLive:
                        if not ignoredClass:
                            self.notify.warning('dumpAllSubShardObjects: neverDisable set for %s %s' % (obj.__class__.__name__, obj.doId))
                else:
                    self.deleteObject(doId)
                    self._deletedSubShardDoIds.add(doId)
                    if obj.getDelayDeleteCount() != 0:
                        delayDeleted.append(obj)

        delayDeleteLeaks = []
        for obj in delayDeleted:
            if obj.getDelayDeleteCount() != 0:
                delayDeleteLeaks.append(obj)

        if len(delayDeleteLeaks):
            s = 'dumpAllSubShardObjects:'
            for obj in delayDeleteLeaks:
                s += '\n  could not delete %s (%s), delayDeletes=%s' % (safeRepr(obj), itype(obj), obj.getDelayDeleteNames())

            self.notify.error(s)
        if isNotLive:
            self.notify.info('dumpAllSubShardObjects: doIds left: %s' % list(self.doId2do.keys()))

    def _removeCurrentShardInterest(self, callback):
        if self.old_setzone_interest_handle is None:
            self.notify.warning('removeToontownShardInterest: no shard interest open')
            callback()
            return
        self.acceptOnce(ToontownClientRepository.ClearInterestDoneEvent, Functor(self._tcrRemoveUberZoneInterest, callback))
        self._removeEmulatedSetZone(ToontownClientRepository.ClearInterestDoneEvent)

    def _tcrRemoveUberZoneInterest(self, callback):
        self.acceptOnce(ToontownClientRepository.ClearInterestDoneEvent, Functor(self._tcrRemoveShardInterestDone, callback))
        self.removeInterest(self.uberZoneInterest, ToontownClientRepository.ClearInterestDoneEvent)

    def _tcrRemoveShardInterestDone(self, callback):
        self.uberZoneInterest = None
        callback()

    def _doIdIsOnCurrentShard(self, doId):
        if doId == base.localAvatar.defaultShard:
            return True
        do = self.getDo(doId)
        if do:
            if do.parentId == base.localAvatar.defaultShard:
                return True
        return False

    def isFriend(self, doId):
        for friendId, flags in base.localAvatar.friendsList:
            if friendId == doId:
                self.identifyFriend(doId)
                return 1

        return 0

    def isAvatarFriend(self, doId):
        for friendId, flags in base.localAvatar.friendsList:
            if friendId == doId:
                self.identifyFriend(doId)
                return 1

        return 0

    def getFriendFlags(self, doId):
        for friendId, flags in base.localAvatar.friendsList:
            if friendId == doId:
                return flags

        return 0

    def getAvatarVisibility(self, doId, forceVisibility = False):
        if doId == base.localAvatar.doId:
            return VisibilityTypes.ONLINE
        handle = self.identifyFriend(doId)
        if handle:
            # The toon is in our cache, so we want to retrieve what we have set for the the toon.
            visibility = handle.getVisibility()
        else:
            # The toon is not in our cache, so we assume the avatar is offline.
            visibility = VisibilityTypes.INVISIBLE

        if doId in self.onlineAvatars:
            if forceVisibility:
                # Sometimes we want to our visibility to show when we're online, so FORCE it!
                return VisibilityTypes.ONLINE
            #accessLevel = base.localAvatar.getAccessLevel()
            #moderatorAccess = AccessLevelName2Int['MODERATOR']
            #if visibility == VisibilityTypes.INVISIBLE and accessLevel >= moderatorAccess:
                #return VisibilityTypes.ONLINE

        return visibility

    # TODO: rename to getHandle or something
    def identifyFriend(self, doId, source = None):
        if doId in self.onlineAvatars:
            teleportNotify.debug('toon %s in onlineAvatars' % doId)
            return self.onlineAvatars[doId]
        elif doId == base.localAvatar.doId:
            return base.localAvatar
        elif doId == self.petHandle[0]:
            return self.petHandle[1]
        elif doId in self.offlineFriends:
            return self.offlineFriends[doId]
        elif doId in self.offlineAvatars:
            return self.offlineAvatars[doId]

        self.notify.warning("Don't know who avatar %s is." % doId)
        return None

    def identifyPlayer(self, pId):
        return base.cr.playerFriendsManager.getFriendInfo(pId)

    def identifyAvatar(self, doId):
        if doId in self.doId2do:
            return self.doId2do[doId]
        else:
            return self.identifyFriend(doId)

    def removeFriend(self, avatarId):
        self.ttrmSocialManager.d_removeFriend(avatarId)

    def clearFriendState(self):
        self.offlineFriends = {}
        self.resetPetHandle()

    def sendOfflineFriendsRequest(self):
        if self.episodeManager.getEpisode():
            # Don't request for friends list if we're in a episode.
            return
        self.ttrmSocialManager.d_requestOfflineFriends()

    def resetPetHandle(self):
        self.petHandle = (0, None)

    def setPetHandle(self):
        doId = base.localAvatar.getPetId()
        if self.petHandle[0] == doId:
            return

        def petDetailsCallback(petAvatar):
            petAvatar.announceGenerate()
            petAvatar.postGenerateMessage()
            handle = PetHandle.PetHandle(petAvatar)
            self.petHandle = (doId, handle)
            petAvatar.disable()
            petAvatar.delete()
            messenger.send('petHandleChanged')
            if self._proactiveLeakChecks:
                petAvatar.detectLeaks()

        PetDetail.PetDetail(doId, petDetailsCallback)

    def updateOnlineAvatarHandle(self, toon):
        doId = toon[0]
        if hasattr(base, 'localAvatar') and doId == base.localAvatar.doId:
            return base.localAvatar
        name = toon[1]
        dnaString = toon[2]
        dna = ToonDNA.ToonDNA()
        dna.makeFromNetString(dnaString)
        petId = toon[3]
        handle = AvatarHandle.AvatarHandle(
                doId,
                name,
                dna,
                petId,
                accessories = (toon[4], toon[5], toon[6], toon[7]),
                profileBackground = toon[8],
                profilePose = toon[9],
                visibility = toon[10]
        )
        self.onlineAvatars[doId] = handle

        # a visibility of 0 means that we are INVISIBLE - either by avatar option or by ghost mode
        # if we are not visible, add us to the invisible list. otherwise, remove us if we were on the list
        if not handle.getVisibility() and doId not in self.invisibleAvatars:
            self.invisibleAvatars.append(doId)
        elif doId in self.invisibleAvatars:
            self.invisibleAvatars.remove(doId)

        if doId in self.offlineAvatars:
            del self.offlineAvatars[doId]
        if doId in self.offlineFriends:
            del self.offlineFriends[doId]

        return handle

    def handleGetOnlineAvatars(self, onlineAvatars):
        self.onlineAvatars = {}

        for toon in onlineAvatars:
            self.updateOnlineAvatarHandle(toon)

        messenger.send('onlineAvatarsChanged')

    def updateOnlineAvatar(self, toon):
        handle = self.updateOnlineAvatarHandle(toon)
        messenger.send(f'onlineAvatarChanged-{toon[0]}', [handle])
        messenger.send('onlineAvatarsChanged')

    def removeOnlineAvatar(self, doId):
        if doId in self.onlineAvatars:
            # This only matters if we are in game, as we will always request offline friends whenever logging in.
            if hasattr(base, 'localAvatar'):
                if self.isFriend(doId):
                    self.offlineFriends[doId] = self.onlineAvatars[doId]
                    self.offlineFriends[doId].visibility = VisibilityTypes.INVISIBLE
                # Cache every Toon that has logged off.
                # We might need them for scenerios such as friend request rejections.
                self.offlineAvatars[doId] = self.onlineAvatars[doId]
                self.offlineAvatars[doId].visibility = VisibilityTypes.INVISIBLE
            if doId in self.invisibleAvatars:
                self.invisibleAvatars.remove(doId)

            del self.onlineAvatars[doId]
            messenger.send('onlineAvatarsChanged')

    def handleGetOfflineFriends(self, resp):
        for toon in resp:
            doId = toon[0]
            name = toon[1]
            dnaString = toon[2]
            dna = ToonDNA.ToonDNA()
            dna.makeFromNetString(dnaString)
            petId = toon[3]
            handle = AvatarHandle.AvatarHandle(
                    doId,
                    name,
                    dna,
                    petId,
                    accessories = (toon[4], toon[5], toon[6], toon[7]),
                    profileBackground = toon[8],
                    profilePose = toon[9],
                    visibility = toon[10]
            )
            self.offlineFriends[doId] = handle

    def forbidCheesyEffects(self, forbid):
        wasAllowed = self.__forbidCheesyEffects
        self.__forbidCheesyEffects = forbid
        isAllowed = self.__forbidCheesyEffects
        if wasAllowed != isAllowed:
            for av in Avatar.Avatar.ActiveAvatars:
                if hasattr(av, 'reconsiderCheesyEffect'):
                    av.reconsiderCheesyEffect()

            base.localAvatar.reconsiderCheesyEffect()

    def areCheesyEffectsAllowed(self):
        return not self.__forbidCheesyEffects

    def getNextSetZoneDoneEvent(self):
        return '%s-%s' % (ToontownClientRepository.EmuSetZoneDoneEvent, self.setZonesEmulated + 1)

    def getLastSetZoneDoneEvent(self):
        return '%s-%s' % (ToontownClientRepository.EmuSetZoneDoneEvent, self.setZonesEmulated)

    def getQuietZoneLeftEvent(self):
        return 'leftQuietZone-%s' % (id(self),)

    def sendSetZoneMsg(self, zoneId, visibleZoneList = None):
        event = self.getNextSetZoneDoneEvent()
        self.setZonesEmulated += 1
        parentId = base.localAvatar.defaultShard
        self.sendSetLocation(base.localAvatar.doId, parentId, zoneId)
        localAvatar.setLocation(parentId, zoneId)
        interestZones = zoneId
        if visibleZoneList is not None:
            interestZones = visibleZoneList
        self._addInterestOpToQueue(ToontownClientRepository.SetInterest, [parentId, interestZones, 'OldSetZoneEmulator'], event)

    def resetInterestStateForConnectionLoss(self):
        OTPClientRepository.OTPClientRepository.resetInterestStateForConnectionLoss(self)
        self.old_setzone_interest_handle = None
        self.setZoneQueue.clear()

    def _removeEmulatedSetZone(self, doneEvent):
        self._addInterestOpToQueue(ToontownClientRepository.ClearInterest, None, doneEvent)

    def _addInterestOpToQueue(self, op, args, event):
        self.setZoneQueue.push([op, args, event])
        if len(self.setZoneQueue) == 1:
            self._sendNextSetZone()

    def _sendNextSetZone(self):
        op, args, event = self.setZoneQueue.top()
        if op == ToontownClientRepository.SetInterest:
            parentId, interestZones, name = args
            if self.old_setzone_interest_handle == None:
                self.old_setzone_interest_handle = self.addInterest(parentId, interestZones, name, ToontownClientRepository.SetZoneDoneEvent)
            else:
                self.alterInterest(self.old_setzone_interest_handle, parentId, interestZones, name, ToontownClientRepository.SetZoneDoneEvent)
        elif op == ToontownClientRepository.ClearInterest:
            self.removeInterest(self.old_setzone_interest_handle, ToontownClientRepository.SetZoneDoneEvent)
            self.old_setzone_interest_handle = None
        else:
            self.notify.error('unknown setZone op: %s' % op)

    def _handleEmuSetZoneDone(self):
        op, args, event = self.setZoneQueue.pop()
        queueIsEmpty = self.setZoneQueue.isEmpty()
        if event is not None:
            if not base.killInterestResponse:
                messenger.send(event)
            elif not hasattr(self, '_dontSendSetZoneDone'):
                import random
                if random.random() < 0.05:
                    self._dontSendSetZoneDone = True
                else:
                    messenger.send(event)
        if not queueIsEmpty:
            self._sendNextSetZone()

    def _isPlayerDclass(self, dclass):
        return dclass == self._playerAvDclass

    def _isValidPlayerLocation(self, parentId, zoneId):
        if not self.distributedDistrict:
            return False
        if parentId != self.distributedDistrict.doId:
            return False
        if parentId == self.distributedDistrict.doId and zoneId == OTPGlobals.UberZone:
            return False
        return True

    def sendQuietZoneRequest(self):
        self.sendSetZoneMsg(OTPGlobals.QuietZone, [])

    def handleQuietZoneGenerateWithRequired(self, di):
        doId = di.getUint32()
        parentId = di.getUint32()
        zoneId = di.getUint32()
        classId = di.getUint16()
        dclass = self.dclassesByNumber[classId]
        if dclass.getClassDef().neverDisable:
            dclass.startGenerate()
            distObj = self.generateWithRequiredFields(dclass, doId, di, parentId, zoneId)
            dclass.stopGenerate()

    def handleQuietZoneGenerateWithRequiredOther(self, di):
        doId = di.getUint32()
        parentId = di.getUint32()
        zoneId = di.getUint32()
        classId = di.getUint16()
        dclass = self.dclassesByNumber[classId]
        if dclass.getClassDef().neverDisable:
            dclass.startGenerate()
            distObj = self.generateWithRequiredOtherFields(dclass, doId, di, parentId, zoneId)
            dclass.stopGenerate()

    def handleQuietZoneUpdateField(self, di):
        di2 = DatagramIterator(di)
        doId = di2.getUint32()
        if doId in self.deferredDoIds:
            args, deferrable, dg0, updates = self.deferredDoIds[doId]
            dclass = args[2]
            if not dclass.getClassDef().neverDisable:
                return
        else:
            do = self.getDo(doId)
            if do:
                if not do.neverDisable:
                    return
        OTPClientRepository.OTPClientRepository.handleUpdateField(self, di)

    def handleDelete(self, di):
        doId = di.getUint32()
        self.deleteObject(doId)

    def deleteObject(self, doId, ownerView = False):
        if doId in self.doId2do:
            obj = self.doId2do[doId]
            del self.doId2do[doId]
            obj.deleteOrDelay()
            if obj.getDelayDeleteCount() <= 0:
                obj.detectLeaks()
        elif self.cache.contains(doId):
            self.cache.delete(doId)
        else:
            self.notify.warning('Asked to delete non-existent DistObj ' + str(doId))

    def _abandonShard(self):
        for doId, obj in list(self.doId2do.items()):
            if obj.parentId == localAvatar.defaultShard and obj is not localAvatar:
                self.deleteObject(doId)

    def requestAvatarInfo(self, avId):
        if avId == 0:
            return
        datagram = PyDatagram()
        # Add message type
        datagram.addUint16(CLIENT_GET_FRIEND_LIST_EXTENDED)
        datagram.addUint16(1)  # number of avIds
        datagram.addUint32(avId)
        # send the message
        base.cr.send(datagram)

    def queueRequestAvatarInfo(self, avId):
        removeTask = 0
        if not hasattr(self, 'avatarInfoRequests'):
            self.avatarInfoRequests = []
        if self.avatarInfoRequests:
            taskMgr.remove('avatarRequestQueueTask')
        if avId not in self.avatarInfoRequests:
            self.avatarInfoRequests.append(avId)
        taskMgr.doMethodLater(0.1, self.sendAvatarInfoRequests, 'avatarRequestQueueTask')

    def sendAvatarInfoRequests(self, task = None):
        print('Sending request Queue for AV Handles')
        if not hasattr(self, 'avatarInfoRequests'):
            return
        if len(self.avatarInfoRequests) == 0:
            return
        datagram = PyDatagram()
        # Add message type
        datagram.addUint16(CLIENT_GET_FRIEND_LIST_EXTENDED)
        datagram.addUint16(len(self.avatarInfoRequests))  # number of avIds
        for avId in self.avatarInfoRequests:
            datagram.addUint32(avId)
        # send the message
        base.cr.send(datagram)

    def handleGenerateWithRequiredOtherOwner(self, di):
        # OwnerViews are only used for LocalToon in Toontown.
        if self.loginFSM.getCurrentState().getName() == 'waitForSetAvatarResponse':
            doId = di.getUint32()
            parentId = di.getUint32()
            zoneId = di.getUint32()
            dclassId = di.getUint16()
            self.handleAvatarResponseMsg(doId, di)

    def checkDiscordJoin(self):
        # verify secrets here, to make sure they are real
        # check environ first, then check bboard
        joinSecret = b''
        #if joinSecret:
        #    try:
        #        unsetenv('DISCORD_JOIN_SECRET')
        #    except NameError:
        #        del environ['DISCORD_JOIN_SECRET']
        return joinSecret

    def getGamemode(self):
        try:
            if localServer:
                return self.gamemode
        except:
            return ModeServer
