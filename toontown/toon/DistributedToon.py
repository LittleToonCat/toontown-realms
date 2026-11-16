from typing import List

from panda3d.core import *
from panda3d.toontown import *
from toontown.toonbase.ToontownGlobals import *
from direct.actor import Actor
from direct.distributed.ClockDelta import *
from direct.fsm import ClassicFSM
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import OnscreenText
from direct.showbase import Audio3DManager
from otp.otpbase import OTPGlobals
from direct.directnotify import DirectNotifyGlobal
from otp.avatar import DistributedPlayer
from otp.avatar import Avatar, DistributedAvatar
from otp.speedchat import SCDecoders
from otp.chat import TalkAssistant
from . import Toon
from direct.task.Task import Task
from direct.distributed import DistributedSmoothNode
from direct.distributed import DistributedObject
from toontown.hood import ZoneUtil
from toontown.distributed import DelayDelete
from toontown.distributed.DelayDeletable import DelayDeletable
from direct.showbase import PythonUtil
from toontown.catalog import CatalogItemList
from toontown.catalog import CatalogItem
from . import TTEmote
from toontown.toonbase.ToontownSettings import speedChatStyles
from toontown.toonbase import ClientSettings
from toontown.fishing import FishCollection
from toontown.fishing import FishTank
from toontown.suit import SuitDNA
from toontown.coghq import CogDisguiseGlobals
from toontown.toonbase import TTLocalizer
from . import Experience
from . import InventoryNew
from . import InventoryBase
from toontown.speedchat import TTSCDecoders
from toontown.chat import ToonChatGarbler
from toontown.chat import ResistanceChat
from toontown.chat import TTQTGraph
from direct.distributed.MsgTypes import *
from toontown.effects.ScavengerHuntEffects import *
from toontown.estate import FlowerCollection
from toontown.estate import FlowerBasket
from toontown.estate import GardenGlobals
from toontown.estate import DistributedGagTree
from toontown.golf import GolfGlobals
from toontown.parties.PartyGlobals import InviteStatus, PartyStatus
from toontown.parties.PartyInfo import PartyInfo
from toontown.parties.InviteInfo import InviteInfo
from toontown.parties.PartyReplyInfo import PartyReplyInfoBase
from toontown.parties.SimpleMailBase import SimpleMailBase
from toontown.parties import PartyGlobals
from direct.interval.IntervalGlobal import Sequence, Wait, Func, Parallel, SoundInterval
from toontown.distributed import DelayDelete
from otp.otpbase import OTPLocalizer
from direct.showbase.InputStateGlobal import inputState
from toontown.avatar import ToontownAvatarUtils
from toontown.toon import NPCToons
from toontown.toon import DropPropGlobals
from .ToonDNA import BlackColor
from toontown.battle.BattleProps import globalPropPool
from toontown.char import CharDNA
from toontown.episodes.EpisodeConfig import EpisodeName2Id, EpisodeId2Name
from toontown.social import AvatarHandle
from toontown.suit.DistributedSellbotBoss import DistributedSellbotBoss
from toontown.suit.DistributedCashbotBoss import DistributedCashbotBoss
from toontown.suit.DistributedLawbotBoss import DistributedLawbotBoss
from toontown.suit.DistributedBossbotBoss import DistributedBossbotBoss

import random
import copy
import time
import operator

from ..toonbase.ToonBaseGlobal import base, loader
from ..toonbase.ToontownTypes import TShirt, TBottom

if base.wantKarts:
    from toontown.racing.KartDNA import *
if (__debug__):
    import pdb


class DistributedToon(DistributedPlayer.DistributedPlayer, Toon.Toon, DistributedSmoothNode.DistributedSmoothNode, DelayDeletable):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedToon')
    partyNotify = DirectNotifyGlobal.directNotify.newCategory('DistributedToon_Party')
    chatGarbler = ToonChatGarbler.ToonChatGarbler()
    gmNameTag = None
    nameStar = loader.loadModel('phase_3.5/models/gui/ttrm_m_gui_nameStar', allowInstance = True)

    def __init__(self, cr, bFake = False):
        try:
            self.DistributedToon_initialized
            return
        except:
            self.DistributedToon_initialized = 1

        DistributedPlayer.DistributedPlayer.__init__(self, cr)
        Toon.Toon.__init__(self)
        DistributedSmoothNode.DistributedSmoothNode.__init__(self, cr)
        self.bFake = bFake
        self.kart = None
        self._isGM = False
        self._gmType = None
        self.trophyScore = 0
        self.trophyStar = None
        self.trophyStarSpeed = 0
        self.safeZonesVisited = []
        self.NPCFriendsDict = {}
        self.earnedExperience = None
        self.track = None
        self.effect = None
        self.jarEndPos: float = 0.5
        self.maxCarry = 0
        self.disguisePageFlag = 0
        self.sosPageFlag = 0
        self.disguisePage = None
        self.sosPage = None
        self.gardenPage = None
        self.roguesPage = None
        self.cogTypes = [0,
         0,
         0,
         0]
        self.cogLevels = [0,
         0,
         0,
         0]
        self.cogParts = [0,
         0,
         0,
         0]
        self.cogMerits = [0,
         0,
         0,
         0]
        self.laffMeterTextColor = (0, 0, 0)
        self.savedCheesyEffect = CENormal
        self.savedCheesyHoodId = 0
        self.savedCheesyExpireTime = 0
        if hasattr(base, 'wantPets') and base.wantPets:
            self.petTrickPhrases = []
            self.petDNA = None
        self.customMessages = []
        self.resistanceMessages = []
        self.cogSummonsEarned = []
        self.catalogNotify = ToontownGlobals.NoItems
        self.mailboxNotify = ToontownGlobals.NoItems
        self.simpleMailNotify = ToontownGlobals.NoItems
        self.inviteMailNotify = ToontownGlobals.NoItems
        self.catalogScheduleCurrentWeek = 0
        self.catalogScheduleNextTime = 0
        self.monthlyCatalog = CatalogItemList.CatalogItemList()
        self.weeklyCatalog = CatalogItemList.CatalogItemList()
        self.backCatalog = CatalogItemList.CatalogItemList()
        self.onOrder = CatalogItemList.CatalogItemList(store=CatalogItem.Customization | CatalogItem.DeliveryDate)
        self.onGiftOrder = CatalogItemList.CatalogItemList(store=CatalogItem.Customization | CatalogItem.DeliveryDate)
        self.mailboxContents = CatalogItemList.CatalogItemList(store=CatalogItem.Customization)
        self.deliveryboxContentsContents = CatalogItemList.CatalogItemList(store=CatalogItem.Customization | CatalogItem.GiftTag)
        self.awardMailboxContents = CatalogItemList.CatalogItemList(store=CatalogItem.Customization)
        self.onAwardOrder = CatalogItemList.CatalogItemList(store=CatalogItem.Customization | CatalogItem.DeliveryDate)
        self.splash = None
        self.tossTrack = None
        self.pieTracks = {}
        self.splatTracks = {}
        self.lastTossedPie = 0
        self.featherTrack = None
        self.clothesTopsList = []
        self.clothesBottomsList = []
        self.closetShirts: List[TShirt] = []
        self.closetBottoms: List[TBottom] = []
        self.hatList = []
        self.glassesList = []
        self.backpackList = []
        self.shoesList = []
        self.tunnelTrack = None
        self.tunnelPivotPos = [-14, -6, 0]
        self.tunnelCenterOffset = 9.0
        self.tunnelCenterInfluence = 0.6
        self.pivotAngle = 90 + 45
        self.posIndex = 0
        self.houseId = 0
        self.houseType = 0
        self.inventory = None
        self.money = 0
        self.bankMoney = 0
        self.maxMoney = 0
        self.maxBankMoney = 0
        self.gameTickets = 0
        self.emblems = [0, 0]
        self.maxNPCFriends = 16
        self.petId = 0
        self.bPetTutorialDone = False
        self.bFishBingoTutorialDone = False
        self.bFishBingoMarkTutorialDone = False
        self.accessories = []
        if base.wantKarts:
            self.kartDNA = [-1] * getNumFields()
        self.flowerCollection = None
        self.shovel = 0
        self.shovelSkill = 0
        self.shovelModel = None
        self.wateringCan = 0
        self.wateringCanSkill = 0
        self.wateringCanModel = None
        self.gardenSpecials = []
        self.unlimitedSwing = 0
        self.boardingParty = None
        self.__currentDialogue = None
        self.mail = None
        self.invites = []
        self.hostedParties = []
        self.partiesInvitedTo = []
        self.oldHostedParties = []
        self.oldPartiesInvitedTo = []
        self.partyReplyInfoBases = []
        self.gmState = 0
        self.gmNameTagEnabled = 0
        self.gmNameTagColor = 'whiteGM'
        self.gmNameTagString = ''
        self._lastZombieContext = None
        self.kartActive = False
        self.kartInterest = None
        self.activeIntervals = {}

        # Various misc flags, mainly related to Magic Word states
        self.locked = False
        self.muted = False
        self.transitioning = False
        self.immortalMode = False
        self.tempImmortalMode = False
        self.unlimitedGags = False
        self.instaKill = False
        self.run = None

        # For caging Toons
        self.cage = None

        # This next bit stores whether we have completed a certain episode yet on the account
        self.__episodeStatuses = {}
        for epName in EpisodeName2Id.keys():
            self.__episodeStatuses[epName] = False

        # Perhaps we shouldn't attach an interface to the Toon like this, but whatever
        # We can always move it to it's own class at a later point
        self.systemMessage = None

        self.profileBackground = 0
        self.profileBackgrounds = [0, 1, 2, 3, 4, 5]
        self.profilePose = 0
        self.profilePoses = [0, 1]

        self.nextKnockKnockHeal = 0

    def disable(self):
        self._stopZombieCheck()
        if self.boardingParty:
            self.boardingParty.demandDrop()
            self.boardingParty = None
        self.kartActive = False
        self.updateKartActive()
        self.ignore('clientCleanup')
        self.stopAnimations()
        self.clearCheesyEffect()
        self.stopBlink()
        self.stopSmooth()
        self.stopLookAroundNow()
        self.setGhostMode(0)
        if self.track != None:
            self.track.finish()
            DelayDelete.cleanupDelayDeletes(self.track)
            self.track = None
        if self.effect != None:
            self.effect.destroy()
            self.effect = None
        if self.splash != None:
            self.splash.destroy()
            self.splash = None
        if self.emote != None:
            self.emote.finish()
            self.emote = None
        self.cleanupPies()
        if self.getTransformationsIndex(ToontownGlobals.TransformationCog):
            self.takeOffTransformation()
        if self.tunnelTrack:
            self.tunnelTrack.finish()
            self.tunnelTrack = None
        self.setTrophyScore(0)
        self.removeGMIcon()
        self.removeCustomIcon()
        self.cleanupIntervals()
        if self.doId in self.cr.toons:
            del self.cr.toons[self.doId]

        if self.cage:
            self.cage.removeNode()
            self.cage = None

        if hasattr(self, 'systemMessage') and self.systemMessage:
            self.systemMessage.destroy()
            del self.systemMessage

        DistributedPlayer.DistributedPlayer.disable(self)
        return

    def delete(self):
        try:
            self.DistributedToon_deleted
        except:
            self.DistributedToon_deleted = 1
            del self.safeZonesVisited
            DistributedPlayer.DistributedPlayer.delete(self)
            Toon.Toon.delete(self)
            DistributedSmoothNode.DistributedSmoothNode.delete(self)

    def generate(self):
        DistributedPlayer.DistributedPlayer.generate(self)
        DistributedSmoothNode.DistributedSmoothNode.generate(self)
        self.cr.toons[self.doId] = self
        if base.cr.trophyManager != None:
            base.cr.trophyManager.d_requestTrophyScore()
        self.startBlink()
        self.startSmooth()
        self.accept('clientCleanup', self._handleClientCleanup)
        return

    def announceGenerate(self):
        DistributedPlayer.DistributedPlayer.announceGenerate(self)
        if self.animFSM.getCurrentState().getName() == 'off':
            self.setAnimState('neutral')
        self._startZombieCheck()
        self.updateKartActive()

    def initializeBodyCollisions(self, collIdStr):
        DistributedAvatar.DistributedAvatar.initializeBodyCollisions(self, collIdStr)

        if self.isPlayerControlled():
            self.collNode.setIntoCollideMask(ToontownGlobals.PieBitmask)

    def _handleClientCleanup(self):
        if self.track != None:
            DelayDelete.cleanupDelayDeletes(self.track)
        return

    def setDNAString(self, dnaString):
        if hasattr(self, 'savedCheesyEffect') and self.savedCheesyEffect == OTPGlobals.CENoTorso:
            self.clearCheesyEffect()
        Toon.Toon.setDNAString(self, dnaString)
        if hasattr(self, 'savedCheesyEffect') and self.savedCheesyEffect == OTPGlobals.CENoTorso:
            self.reconsiderCheesyEffect()

    def setDNA(self, dna):
        if base.cr.newsManager:
            if base.cr.newsManager.isHolidayRunning(ToontownGlobals.SPOOKY_BLACK_CAT):
                black = BlackColor
                heads = ['cls', 'css', 'csl', 'cll']
                dna.setTemporary(random.choice(heads), black, black, black)
            else:
                dna.restoreTemporary(self.style)
        Toon.Toon.setDNA(self, dna)

    def updateDNA(self, dna, spellbook):
        self.sendUpdate('updateDNA', [dna, spellbook])

    def updateHeadAccessories(self, h1, h2, g1, g2):
        self.sendUpdate('updateHeadAccessories', [h1, h2, g1, g2])

    def updateBodyAccessories(self, b1, b2, s1, s2):
        self.sendUpdate('updateBodyAccessories', [b1, b2, s1, s2])

    def setGM(self, type):
        wasGM = self._isGM
        self._isGM = type != 0
        self._gmType = None
        if self._isGM:
            self._gmType = type - 1
        if self._isGM != wasGM:
            self._handleGMName()
        return

    def setExperience(self, experience):
        self.experience = Experience.Experience(experience, self)
        if self.isInventoryNewLoaded():
            self.inventory.updateGUI()

    def setInventory(self, inventoryNetString):
        if not self.inventory:
            if self == base.localAvatar:
                self.inventory = InventoryNew.InventoryNew(self, inventoryNetString)
            else:
                self.inventory = InventoryBase.InventoryBase(self, inventoryNetString)

        self.inventory.updateInvString(inventoryNetString)

    def isInventoryNewLoaded(self):
        return isinstance(self.inventory, InventoryNew.InventoryNew)

    def setLastHood(self, lastHood):
        self.lastHood = lastHood

    def setLastZone(self, lastZone):
        self.lastZone = lastZone

    def setBattleId(self, battleId):
        self.battleId = battleId
        messenger.send('ToonBattleIdUpdate', [self.doId])

    def b_setSCToontask(self, taskId, toNpcId, toonProgress, msgIndex, displayType=0):
        self.setSCToontask(taskId, toNpcId, toonProgress, msgIndex, displayType)
        self.d_setSCToontask(taskId, toNpcId, toonProgress, msgIndex)
        return None

    def d_setSCToontask(self, taskId, toNpcId, toonProgress, msgIndex):
        messenger.send('wakeup')
        self.sendUpdate('setSCToontask', [taskId,
         toNpcId,
         toonProgress,
         msgIndex])

    def setSCToontask(self, taskId, toNpcId, toonProgress, msgIndex, displayType=0):
        if self.doId in base.localAvatar.ignoreList:
            return
        chatString = TTSCDecoders.decodeTTSCToontaskMsg(taskId, toNpcId, toonProgress, msgIndex)
        if chatString:
            if displayType == 1:
                self.setChatAbsolute(chatString, CFExclaim | CFQuicktalker | CFTimeout)
            elif displayType == 2:
                self.setChatAbsolute(chatString, CFThought | CFQuicktalker)
            else:
                self.setChatAbsolute(chatString, CFSpeech | CFQuicktalker | CFTimeout)

    def b_setSCSinging(self, msgIndex):
        self.setSCSinging(msgIndex)
        self.d_setSCSinging(msgIndex)
        return None

    def d_setSCSinging(self, msgIndex):
        messenger.send('wakeup')
        self.sendUpdate('setSCSinging', [msgIndex])

    def sendLogSuspiciousEvent(self, msg):
        localAvatar.sendUpdate('logSuspiciousEvent', ['%s for %s' % (msg, self.doId)])

    def setSCSinging(self, msgIndex):
        self.sendUpdate('logSuspiciousEvent', ['invalid msgIndex in setSCSinging: %s from %s' % (msgIndex, self.doId)])

    def d_reqSCResistance(self, msgIndex):
        messenger.send('wakeup')
        nearbyPlayers = self.getNearbyPlayers(ResistanceChat.EFFECT_RADIUS)
        self.sendUpdate('reqSCResistance', [msgIndex, nearbyPlayers])

    def getNearbyPlayers(self, radius, includeSelf = True):
        nearbyToons = []
        toonIds = self.cr.getObjectsOfExactClass(DistributedToon)
        for toonId, toon in list(toonIds.items()):
            if toon is not self:
                dist = toon.getDistance(self)
                if dist < radius:
                    nearbyToons.append(toonId)

        if includeSelf:
            nearbyToons.append(self.doId)
        return nearbyToons

    def setSCResistance(self, msgIndex, nearbyToons = []):
        chatString = TTSCDecoders.decodeTTSCResistanceMsg(msgIndex)
        if chatString:
            self.setChatAbsolute(chatString, CFSpeech | CFTimeout)
        ResistanceChat.doEffect(msgIndex, self, nearbyToons)

    def b_setQT(self, qtSequence):
        self.setQT(qtSequence)
        self.d_setQT(qtSequence)

    def d_setQT(self, qtSequence):
        self.sendUpdate('setQT', [
            qtSequence])

    def setQT(self, qtSequence):
        chatString = TTQTGraph.decodeQTMessage(qtSequence)
        self.setChatAbsolute(chatString, CFSpeech | CFQuicktalker | CFTimeout)

    def receiveBattleSOS(self, requesterId):
        avatar = base.cr.identifyAvatar(requesterId)
        if isinstance(avatar, DistributedToon) or isinstance(avatar, AvatarHandle.AvatarHandle):
            self.setSystemMessage(requesterId, TTLocalizer.MovieSOSWhisperHelp % avatar.getName(), whisperType=WhisperPopup.WTBattleSOS)
        elif avatar is not None:
            self.notify.warning('received battleSOS from non-toon %s' % requesterId)

    def getDialogueArray(self):
        return Toon.Toon.getDialogueArray(self)

    def setDefaultShard(self, shard):
        self.defaultShard = shard

    def setDefaultZone(self, zoneId):
        if 31000 <= zoneId < 40000:
            zoneId = zoneId + 2000
        try:
            hoodPhase = base.cr.hoodMgr.getPhaseFromHood(zoneId)
        except:
            self.defaultZone = ToontownCentral
            return

        if ZoneUtil.getCanonicalHoodId(zoneId) == FunnyFarm:
            self.defaultZone = ToontownCentral
            return
        if not base.cr.isPaid() or launcher and not launcher.getPhaseComplete(hoodPhase):
            self.defaultZone = ToontownCentral
        else:
            self.defaultZone = zoneId

    def setShtickerBook(self, string):
        pass

    def setAsGM(self, state):
        self.notify.debug('Setting GM State: %s' % state)
        DistributedPlayer.DistributedPlayer.setAsGM(self, state)

    def d_updateGMNameTag(self):
        self.refreshName()

    def updateGMNameTag(self, tagString, color, state):
        try:
            str(tagString, 'utf-8')
        except UnicodeDecodeError:
            self.sendUpdate('logSuspiciousEvent', ['invalid GM name tag: %s from %s' % (tagString, self.doId)])
            return

    def refreshName(self):
        return
        self.notify.debug('Refreshing GM Nametag String: %s Color: %s State: %s' % (self.gmNameTagString, self.gmNameTagColor, self.gmNameTagEnabled))
        if hasattr(self, 'nametag') and self.gmNameTagEnabled:
            self.setDisplayName(self.gmNameTagString)
            self.setName(self.gmNameTagString)
            self.trophyStar1 = loader.loadModel('models/misc/smiley')
            self.trophyStar1.reparentTo(self.nametag.getNameIcon())
            self.trophyStar1.setScale(1)
            self.trophyStar1.setZ(2.25)
            self.trophyStar1.setColor(Vec4(0.75, 0.75, 0.75, 0.75))
            self.trophyStar1.setTransparency(1)
            self.trophyStarSpeed = 15
        else:
            taskMgr.add(self.__refreshNameCallBack, self.uniqueName('refreshNameCallBack'))

    def __starSpin1(self, task):
        now = globalClock.getFrameTime()
        r = now * 90 % 360.0
        self.trophyStar1.setH(r)
        return Task.cont

    def __refreshNameCallBack(self, task):
        if hasattr(self, 'nametag') and self.nametag.getName() != '':
            self.refreshName()
            return Task.done
        else:
            return Task.cont

    def setTalk(self, fromAV, fromAC, avatarName, chatString):
        if base.cr.avatarFriendsManager.checkIgnored(fromAV):
            self.d_setWhisperIgnored(fromAV)
            return
        if fromAV in self.ignoreList:
            self.d_setWhisperIgnored(fromAV)
            return
        newChatString = self.filterChatString(chatString, fromAV)
        self.displayTalk(newChatString)
        base.talkAssistant.receiveOpenTalk(fromAV, avatarName, fromAC, None, newChatString)

    def setTalkCog(self, fromAv, cogType, quoteTypeIndex, quoteIndex, displayType):
        if base.cr.avatarFriendsManager.checkIgnored(fromAv):
            self.d_setWhisperIgnored(fromAv)
            return
        if fromAv in self.ignoreList:
            self.d_setWhisperIgnored(fromAv)
            return
        chatString = TTSCDecoders.decodeTTSCCogMsg(cogType, quoteTypeIndex, quoteIndex)
        if displayType == 2:
            self.setChatAbsolute(chatString, CFThought | CFQuicktalker)
        else:
            self.setChatAbsolute(chatString, CFSpeech | CFQuicktalker | CFTimeout)

    def isAvFriend(self, avId):
        return base.cr.isFriend(avId) or base.cr.playerFriendsManager.isAvatarOwnerPlayerFriend(avId)

    def setTalkWhisper(self, fromAV, fromAC, avatarName, chatString):
        if not localAvatar.acceptingNonFriendWhispers:
            if not self.isAvFriend(fromAV):
                return
        if base.cr.avatarFriendsManager.checkIgnored(fromAV):
            self.d_setWhisperIgnored(fromAV)
            return
        if fromAV in self.ignoreList:
            self.d_setWhisperIgnored(fromAV)
            return
        if base.config.GetBool('ignore-whispers', 0):
            return
        if base.localAvatar.sleepFlag == 1:
            if not base.cr.identifyAvatar(fromAV) == base.localAvatar:
                base.cr.chatManager.sendSleepAutoReply(fromAV)
        sender = base.cr.identifyAvatar(fromAV)
        if sender:
            newChatString = sender.filterChatString(chatString, fromAV)
        else:
            newChatString = self.filterChatString(chatString, fromAV)
        self.displayTalkWhisper(fromAV, avatarName, newChatString)
        base.talkAssistant.receiveWhisperTalk(fromAV, avatarName, fromAC, None, self.doId, self.getName(), newChatString)

    def setSleepAutoReply(self, fromId):
        pass

    def _isValidWhisperSource(self, source):
        return isinstance(source, AvatarHandle.AvatarHandle) or isinstance(source, DistributedToon)

    def setWhisperSCFrom(self, fromId, msgType, msgIndex):
        handle = base.cr.identifyFriend(fromId)
        if handle == None:
            return
        if not self._isValidWhisperSource(handle):
            self.notify.warning('setWhisperSCFrom non-toon %s' % fromId)
            return
        if not localAvatar.acceptingNonFriendWhispers:
            if not self.isAvFriend(fromId):
                return
        if base.cr.avatarFriendsManager.checkIgnored(fromId):
            self.d_setWhisperIgnored(fromId)
            return
        if fromId in self.ignoreList:
            self.d_setWhisperIgnored(fromId)
            return
        if base.localAvatar.sleepFlag == 1:
            if not base.cr.identifyAvatar(fromId) == base.localAvatar:
                base.cr.chatManager.sendSleepAutoReply(fromId)
        if msgType == TalkAssistant.SPEEDCHAT_EMOTE:
            chatString = SCDecoders.decodeSCEmoteWhisperMsg(msgIndex, handle.getName())
        elif msgType == TalkAssistant.SPEEDCHAT_CUSTOM:
            chatString = SCDecoders.decodeSCCustomMsg(msgIndex)
        else:
            chatString = SCDecoders.decodeSCStaticTextMsg(msgIndex)
        if chatString:
            self.displayWhisper(fromId, chatString, WhisperPopup.WTQuickTalker)
            base.talkAssistant.receiveAvatarWhisperSpeedChat(msgType, msgIndex, fromId)

    def setWhisperSCToontaskFrom(self, fromId, taskId, toNpcId, toonProgress, msgIndex):
        sender = base.cr.identifyFriend(fromId)
        if sender == None:
            return
        if not localAvatar.acceptingNonFriendWhispers:
            if not self.isAvFriend(fromId):
                return
        if fromId in self.ignoreList:
            self.d_setWhisperIgnored(fromId)
        chatString = TTSCDecoders.decodeTTSCToontaskMsg(taskId, toNpcId, toonProgress, msgIndex)
        if chatString:
            self.displayWhisper(fromId, chatString, WhisperPopup.WTQuickTalker)

    def setWhisperSCCogFrom(self, fromId, cogType, quoteTypeIndex, quoteIndex):
        sender = base.cr.identifyFriend(fromId)
        if sender == None:
            return
        if not localAvatar.acceptingNonFriendWhispers:
            if not self.isAvFriend(fromId):
                return
        if fromId in self.ignoreList:
            self.d_setWhisperIgnored(fromId)
        chatString = TTSCDecoders.decodeTTSCCogMsg(cogType, quoteTypeIndex, quoteIndex)
        if chatString:
            self.displayWhisper(fromId, chatString, WhisperPopup.WTQuickTalker)

    def setMaxNPCFriends(self, max):
        max &= 32767
        if max != self.maxNPCFriends:
            self.maxNPCFriends = max
            messenger.send(self.uniqueName('maxNPCFriendsChange'))
        else:
            self.maxNPCFriends = max

    def getMaxNPCFriends(self):
        return self.maxNPCFriends

    def getNPCFriendsDict(self):
        return self.NPCFriendsDict

    def setNPCFriendsDict(self, NPCFriendsList):
        NPCFriendsDict = {}
        for friendPair in NPCFriendsList:
            # Remove invalid NPCs
            if friendPair[0] not in NPCToons.npcFriends:
                continue
            NPCFriendsDict[friendPair[0]] = friendPair[1]

        self.NPCFriendsDict = NPCFriendsDict

    def setMaxAccessories(self, max):
        self.maxAccessories = max

    def getMaxAccessories(self):
        return self.maxAccessories

    def setHatList(self, clothesList):
        self.hatList = clothesList

    def getHatList(self):
        return self.hatList

    def setGlassesList(self, clothesList):
        self.glassesList = clothesList

    def getGlassesList(self):
        return self.glassesList

    def setBackpackList(self, clothesList):
        self.backpackList = clothesList

    def getBackpackList(self):
        return self.backpackList

    def setShoesList(self, clothesList):
        self.shoesList = clothesList

    def getShoesList(self):
        return self.shoesList

    def isTrunkFull(self, extraAccessories = 0):
        numAccessories = (len(self.hatList) + len(self.glassesList) + len(self.backpackList) + len(self.shoesList)) / 3
        return numAccessories + extraAccessories >= self.maxAccessories

    def setMaxClothes(self, max):
        self.maxClothes = max

    def getMaxClothes(self):
        return self.maxClothes

    def getClothesTopsList(self):
        return self.clothesTopsList

    def setClothesTopsList(self, clothesList):
        self.clothesTopsList = clothesList

    def getClothesBottomsList(self):
        return self.clothesBottomsList

    def setClothesBottomsList(self, clothesList):
        self.clothesBottomsList = clothesList

    def getClosetShirts(self) -> List[TShirt]:
        return self.closetShirts

    def setClosetShirts(self, shirts: List[TShirt]):
        self.closetShirts = shirts

    def getClosetBottoms(self) -> List[TBottom]:
        return self.closetBottoms

    def setClosetBottoms(self, bottoms: List[TBottom]):
        self.closetBottoms = bottoms

    def catalogGenClothes(self, avId):
        if avId == self.doId:
            self.generateToonClothes()
            self.loop('neutral')

    def catalogGenAccessories(self, avId):
        if avId == self.doId:
            self.generateToonAccessories()
            self.loop('neutral')

    def isClosetFull(self, extraClothes = 0):
        numClothes = len(self.closetShirts)+ len(self.closetBottoms)
        return numClothes + extraClothes >= self.maxClothes

    def setMaxHp(self, hitPoints):
        DistributedPlayer.DistributedPlayer.setMaxHp(self, hitPoints)
        if self.isInventoryNewLoaded():
            self.inventory.updateGUI()

    def setHp(self, hp):
        DistributedPlayer.DistributedPlayer.setHp(self, hp)
        if self.getTransformationsIndex(ToontownGlobals.TransformationCog):
            self.suit.currHP = self.hp
            self.suit.maxHP = self.maxHp
            if self.maxHp == self.hp:
                self.suit.showCorpMedallion()
                self.suit.healthBar.hide()
            else:
                self.suit.hideCorpMedallion()
                self.suit.healthBar.show()
                self.suit.updateHealthBar()

    def setLaffMeterTextColor(self, r, g, b):
        self.laffMeterTextColor = (r / 255, g / 255, b / 255)
        messenger.send(self.uniqueName('laffMeterTextColorChange'), [self.laffMeterTextColor])

    def getLaffMeterTextColor(self):
        return self.laffMeterTextColor

    def died(self):
        messenger.send(self.uniqueName('died'))
        if self.isLocal():
            target_sz = ZoneUtil.getSafeZoneId(self.defaultZone)
            place = self.cr.playGame.getPlace()
            if place and place.fsm:
                place.fsm.request('died', [{'loader': ZoneUtil.getLoaderName(target_sz),
                  'where': ZoneUtil.getWhereName(target_sz, 1),
                  'how': 'teleportIn',
                  'hoodId': target_sz,
                  'zoneId': target_sz,
                  'avId': -1,
                  'battle': 1}])

    def setInterface(self, string):
        pass

    def setZonesVisited(self, hoods):
        self.safeZonesVisited = hoods

    def setHoodsVisited(self, hoods):
        self.hoodsVisited = hoods
        if ToontownGlobals.SellbotHQ in hoods or ToontownGlobals.CashbotHQ in hoods or ToontownGlobals.LawbotHQ in hoods:
            self.setDisguisePageFlag(1)

    def wrtReparentTo(self, parent):
        DistributedSmoothNode.DistributedSmoothNode.wrtReparentTo(self, parent)

    def setTutorialAck(self, tutorialAck):
        self.tutorialAck = tutorialAck

    def setEarnedExperience(self, earnedExp):
        self.earnedExperience = earnedExp

    def b_setTunnelIn(self, endX, tunnelOrigin):
        timestamp = globalClockDelta.getFrameNetworkTime()
        if tunnelOrigin.isEmpty():
            self.notify.warning('tunnelOrigin was empty! resetting to origin')
            pos = (0, 0, 0)
            h = 0
        else:
            pos = tunnelOrigin.getPos(render)
            h = tunnelOrigin.getH(render)
        self.setTunnelIn(timestamp, endX, pos[0], pos[1], pos[2], h)
        self.d_setTunnelIn(timestamp, endX, pos[0], pos[1], pos[2], h)

    def d_setTunnelIn(self, timestamp, endX, x, y, z, h):
        self.sendUpdate('setTunnelIn', [timestamp,
         endX,
         x,
         y,
         z,
         h])

    def setTunnelIn(self, timestamp, endX, x, y, z, h):
        t = globalClockDelta.networkToLocalTime(timestamp)
        self.handleTunnelIn(t, endX, x, y, z, h)

    def getTunnelInToonTrack(self, endX, tunnelOrigin):
        pivotNode = tunnelOrigin.attachNewNode(self.uniqueName('pivotNode'))
        pivotNode.setPos(*self.tunnelPivotPos)
        pivotNode.setHpr(0, 0, 0)
        pivotY = pivotNode.getY(tunnelOrigin)
        endY = 5.0
        straightLerpDur = abs(endY - pivotY) / ToonForwardSpeed
        pivotDur = 2.0
        pivotLerpDur = pivotDur * (90.0 / self.pivotAngle)
        self.reparentTo(pivotNode)
        self.setPos(0, 0, 0)
        self.setX(tunnelOrigin, endX)
        targetX = self.getX()
        self.setX(self.tunnelCenterOffset + (targetX - self.tunnelCenterOffset) * (1.0 - self.tunnelCenterInfluence))
        self.setHpr(tunnelOrigin, 0, 0, 0)
        pivotNode.setH(-self.pivotAngle)
        return Sequence(Wait(0.8), Parallel(
            LerpHprInterval(pivotNode, pivotDur, hpr = Point3(0, 0, 0), name = self.uniqueName('tunnelInPivot')),
            Sequence(Wait(pivotDur - pivotLerpDur),
                     LerpPosInterval(self, pivotLerpDur, pos = Point3(targetX, 0, 0),
                                     name = self.uniqueName('tunnelInPivotLerpPos')))),
                        Func(self.wrtReparentTo, render), Func(pivotNode.removeNode),
                        LerpPosInterval(self, straightLerpDur, pos = Point3(endX, endY, 0), other = tunnelOrigin,
                                        name = self.uniqueName('tunnelInStraightLerp')))

    def handleTunnelIn(self, startTime, endX, x, y, z, h):
        self.stopSmooth()
        tunnelOrigin = render.attachNewNode('tunnelOrigin')
        tunnelOrigin.setPosHpr(x, y, z, h, 0, 0)
        self.tunnelTrack = Sequence(self.getTunnelInToonTrack(endX, tunnelOrigin), Func(tunnelOrigin.removeNode), Func(self.startSmooth))
        tOffset = globalClock.getFrameTime() - (startTime + self.smoother.getDelay())
        if tOffset < 0.0:
            self.tunnelTrack = Sequence(Wait(-tOffset), self.tunnelTrack)
            self.tunnelTrack.start()
        else:
            self.tunnelTrack.start(tOffset)

    def b_setTunnelOut(self, startX, startY, tunnelOrigin):
        timestamp = globalClockDelta.getFrameNetworkTime()
        pos = tunnelOrigin.getPos(render)
        h = tunnelOrigin.getH(render)
        self.setTunnelOut(timestamp, startX, startY, pos[0], pos[1], pos[2], h)
        self.d_setTunnelOut(timestamp, startX, startY, pos[0], pos[1], pos[2], h)

    def d_setTunnelOut(self, timestamp, startX, startY, x, y, z, h):
        self.sendUpdate('setTunnelOut', [timestamp,
         startX,
         startY,
         x,
         y,
         z,
         h])

    def setTunnelOut(self, timestamp, startX, startY, x, y, z, h):
        t = globalClockDelta.networkToLocalTime(timestamp)
        self.handleTunnelOut(t, startX, startY, x, y, z, h)

    def getTunnelOutToonTrack(self, startX, startY, tunnelOrigin):
        tunnelIval = Sequence()

        def getTargetPos(self=self):
            pos = self.getPos()
            return Point3(self.tunnelCenterOffset + (pos[0] - self.tunnelCenterOffset) * (1.0 - self.tunnelCenterInfluence), pos[1], pos[2])

        self.tunnelPivotPos = [-14, -6, 0]
        self.tunnelCenterOffset = 9.0
        self.tunnelCenterInfluence = 0.6

        startPos = self.getPos(tunnelOrigin)
        startHpr = self.getHpr(tunnelOrigin)
        reducedAvH = PythonUtil.fitDestAngle2Src(startHpr[0], 180)
        pivotNode = tunnelOrigin.attachNewNode(self.uniqueName('pivotNode'))
        pivotNode.setPos(*self.tunnelPivotPos)
        pivotNode.setHpr(0, 0, 0)
        pivotY = pivotNode.getY(tunnelOrigin)
        straightLerpDur = abs(startY - pivotY) / ToonForwardSpeed
        pivotDur = 2.0
        pivotLerpDur = pivotDur * (90.0 / self.pivotAngle)

        tunnelIval.append(Sequence(Parallel(LerpPosInterval(self, straightLerpDur, pos=Point3(startX, pivotY, 0.1), startPos=startPos,
                                                            other=tunnelOrigin, name=self.uniqueName('tunnelOutStraightLerp')),
                                   LerpHprInterval(self, straightLerpDur * 0.8, hpr=Point3(reducedAvH, 0, 0), startHpr=startHpr,
                                                   other=tunnelOrigin, name=self.uniqueName('tunnelOutStraightLerpHpr'))),
                          Func(self.wrtReparentTo, pivotNode), Parallel(LerpHprInterval(pivotNode, pivotDur, hpr=Point3(-self.pivotAngle, 0, 0),
                                                                                        name=self.uniqueName('tunnelOutPivot')),
                                                                        LerpPosInterval(self, pivotLerpDur, pos=getTargetPos,
                                                                                        name=self.uniqueName('tunnelOutPivotLerpPos'))),
                          Func(self.wrtReparentTo, render), Func(pivotNode.removeNode)))
        return tunnelIval

    def handleTunnelOut(self, startTime, startX, startY, x, y, z, h):
        tunnelOrigin = render.attachNewNode('tunnelOrigin')
        tunnelOrigin.setPosHpr(x, y, z, h, 0, 0)
        self.tunnelTrack = Sequence(Func(self.stopSmooth), self.getTunnelOutToonTrack(startX, startY, tunnelOrigin), Func(self.detachNode), Func(tunnelOrigin.removeNode))
        tOffset = globalClock.getFrameTime() - (startTime + self.smoother.getDelay())
        if tOffset < 0.0:
            self.tunnelTrack = Sequence(Wait(-tOffset), self.tunnelTrack)
            self.tunnelTrack.start()
        else:
            self.tunnelTrack.start(tOffset)

    def enterTeleportOut(self, *args, **kw):
        Toon.Toon.enterTeleportOut(self, *args, **kw)
        if self.track:
            self.track.delayDelete = DelayDelete.DelayDelete(self, 'enterTeleportOut')

    def exitTeleportOut(self):
        if self.track != None:
            DelayDelete.cleanupDelayDeletes(self.track)
        Toon.Toon.exitTeleportOut(self)
        return

    def b_setAnimState(self, animName, animMultiplier = 1.0, callback = None, extraArgs = []):
        self.d_setAnimState(animName, animMultiplier, None, extraArgs)
        self.setAnimState(animName, animMultiplier, None, None, callback, extraArgs)
        return

    def d_setAnimState(self, animName, animMultiplier = 1.0, timestamp = None, extraArgs = []):
        timestamp = globalClockDelta.getFrameNetworkTime()
        self.sendUpdate('setAnimState', [animName, animMultiplier, timestamp])

    def setAnimState(self, animName, animMultiplier = 1.0, timestamp = None, animType = None, callback = None, extraArgs = []):
        self.resetStrafeRotation()
        if not animName or animName == 'None':
            return
        if timestamp == None:
            ts = 0.0
        else:
            ts = globalClockDelta.localElapsedTime(timestamp)
        if base.config.GetBool('check-invalid-anims', True):
            if animMultiplier > 1.0 and animName in ['neutral']:
                animMultiplier = 1.0
        if hasattr(self, 'animFSM') and self.animFSM.getStateNamed(animName):
            self.animFSM.request(animName, [animMultiplier,
             ts,
             callback,
             extraArgs])
        self.cleanupPieInHand()
        return

    def b_setEmoteState(self, animIndex, animMultiplier):
        self.setEmoteState(animIndex, animMultiplier)
        self.d_setEmoteState(animIndex, animMultiplier)

    def d_setEmoteState(self, animIndex, animMultiplier):
        timestamp = globalClockDelta.getFrameNetworkTime()
        self.sendUpdate('setEmoteState', [animIndex, animMultiplier, timestamp])

    def setEmoteState(self, animIndex, animMultiplier, timestamp = None):
        if animIndex == TTEmote.EmoteClear:
            return
        if timestamp == None:
            ts = 0.0
        else:
            ts = globalClockDelta.localElapsedTime(timestamp)
        callback = None
        extraArgs = []
        extraArgs.insert(0, animIndex)
        if base.localAvatar.ghostMode or not self.ghostMode:
            self.doEmote(animIndex, animMultiplier, ts, callback, extraArgs)
        return

    def setCogStatus(self, cogStatusList):
        self.cogs = cogStatusList

    def setCogCount(self, cogCountList):
        self.cogCounts = cogCountList
        if hasattr(self, 'suitPage'):
            self.suitPage.updatePage()

    def setCogRadar(self, radar):
        self.cogRadar = radar
        if hasattr(self, 'suitPage'):
            self.suitPage.updateCogRadarButtons(radar)

    def setBuildingRadar(self, radar):
        self.buildingRadar = radar
        if hasattr(self, 'suitPage'):
            self.suitPage.updateBuildingRadarButtons(radar)

    def setCogTypes(self, types):
        self.cogTypes = types
        if self.disguisePage:
            self.disguisePage.updatePage()

    def setCogLevels(self, levels):
        self.cogLevels = levels
        if self.disguisePage:
            self.disguisePage.updatePage()

    def getCogLevels(self):
        return self.cogLevels

    def setCogParts(self, parts):
        self.cogParts = parts
        if self.disguisePage:
            self.disguisePage.updatePage()

    def getCogParts(self):
        return self.cogParts

    def setCogMerits(self, merits):
        self.cogMerits = merits
        if self.disguisePage:
            self.disguisePage.updatePage()

    def readyForPromotion(self, dept):
        merits = base.localAvatar.cogMerits[dept]
        totalMerits = CogDisguiseGlobals.getTotalMerits(self, dept)
        if merits >= totalMerits:
            return 1
        else:
            return 0

    def setCogIndex(self, cogShorthand, displayLevel = None, cogType=0, removed=0):
        if removed == 2:
            self.takeOffTransformation()
        if cogShorthand:
            self.putOnSuit(cogShorthand, displayLevel = displayLevel, cogType=cogType, rental = cogType in ToontownGlobals.PutOnSuitRental)
        self.setTransformationsIndex(ToontownGlobals.TransformationCog, cogShorthand)

    def getCogIndex(self):
        return self.getTransformationsIndex(ToontownGlobals.TransformationCog)

    def setCharIndex(self, index, removed=0):
        if removed == 2:
            self.takeOffTransformation()
        if index > 0:
            self.putOnChar(index - 1)
        self.setTransformationsIndex(ToontownGlobals.TransformationClassicChar, index)

    def getCharIndex(self):
        return self.getTransformationsIndex(ToontownGlobals.TransformationClassicChar)

    def setDoodleIndex(self, index, removed=0, petName="", petDNA=None):
        if removed == 2:
            self.takeOffTransformation()
        if index > 0:
            self.putOnDoodle(petName, petDNA)
        self.setTransformationsIndex(ToontownGlobals.TransformationDoodle, index)

    def getDoodleIndex(self):
        return self.getTransformationsIndex(ToontownGlobals.TransformationDoodle)

    def setGoonIndex(self, index, removed=0):
        if removed == 2:
            self.takeOffTransformation()
        if index > 0:
            self.putOnGoon(index - 1)
        self.setTransformationsIndex(ToontownGlobals.TransformationGoon, index)

    def getGoonIndex(self):
        return self.getTransformationsIndex(ToontownGlobals.TransformationGoon)

    def setPropIndex(self, propName, removed=0):
        if removed == 2:
            self.takeOffTransformation()
        if propName != '':
            self.putOnProp(propName)
        self.setTransformationsIndex(ToontownGlobals.TransformationProp, propName)

    def getPropIndex(self):
        return self.getTransformationsIndex(ToontownGlobals.TransformationProp)

    def setBossIndex(self, index, removed=0):
        if removed == 2:
            self.takeOffTransformation()
        if index > 0:
            if hasattr(base.cr, 'newsManager'):
                if base.cr.newsManager != None and base.cr.newsManager.initialized:
                    self.putOnBoss(index - 1)
                else:
                    self.acceptOnce('generateNewsManager', self.putOnBoss, extraArgs=[index - 1])
            else:
                self.acceptOnce('generateNewsManager', self.putOnBoss, extraArgs=[index - 1])
        self.setTransformationsIndex(ToontownGlobals.TransformationBoss, index)

    def getBossIndex(self):
        return self.getTransformationsIndex(ToontownGlobals.TransformationBoss)

    def setFishIndex(self, index, removed=0):
        if removed == 2:
            self.takeOffTransformation()
        if index > 0:
            self.putOnFish(index - 2)
        self.setTransformationsIndex(ToontownGlobals.TransformationFish, index)

    def getFishIndex(self):
        return self.getTransformationsIndex(ToontownGlobals.TransformationFish)

    def setButterflyIndex(self, index: int, r: int, g: int, b: int, removed: int = 0):
        if removed == 2:
            self.takeOffTransformation()
        if index > 0:
            self.putOnButterfly(index + 1, r / 255, g / 255, b / 244)
        self.setTransformationsIndex(ToontownGlobals.TransformationButterfly, index)

    def getButterflyIndex(self) -> int:
        return self.getTransformationsIndex(ToontownGlobals.TransformationButterfly)

    def setMiscIndex(self, index, removed=0):
        if removed == 2:
            bossIndex = self.getBossIndex()

            if hasattr(base.cr, 'newsManager'):
                if not base.cr.newsManager and bossIndex > 0:
                    self.acceptOnce('generateNewsManager', self.setMiscIndex, extraArgs=[index, removed])
                    return

            if bossIndex and not hasattr(self, 'bossGeom'):
                self.putOnBoss(bossIndex - 1)

            self.takeOffTransformation()
        if index > 0:
            self.putOnMisc(index - 1)
        self.setTransformationsIndex(ToontownGlobals.TransformationMisc, index)

    def getMiscIndex(self):
        return self.getTransformationsIndex(ToontownGlobals.TransformationMisc)

    def setStreetIndex(self, index, removed=0):
        if removed == 2:
            self.takeOffTransformation()
        if index > 0:
            self.putOnStreet(index - 1)
        self.setTransformationsIndex(ToontownGlobals.TransformationStreet, index)

    def getStreetIndex(self):
        return self.getTransformationsIndex(ToontownGlobals.TransformationStreet)

    def setMuzzle(self, muzzle):
        self.hideNormalMuzzle()
        self.hideSurpriseMuzzle()
        self.hideSadMuzzle()
        self.hideSmileMuzzle()
        self.hideAngryMuzzle()
        self.hideLaughMuzzle()
        if muzzle == 0:
            self.showNormalMuzzle()
        elif muzzle == 1:
            self.showSurpriseMuzzle()
        elif muzzle == 2:
            self.showSadMuzzle()
        elif muzzle == 3:
            self.showSmileMuzzle()
        elif muzzle == 4:
            self.showAngryMuzzle()
        elif muzzle == 5:
            self.showLaughMuzzle()

    def setEyes(self, eyes):
        Toon.Toon.setEyes(self, eyes)

    def isCog(self):
        return Toon.Toon.isCog(self)

    def setDisguisePageFlag(self, flag):
        if flag and hasattr(self, 'book'):
            self.loadDisguisePages()
        self.disguisePageFlag = flag

    def setSosPageFlag(self, flag):
        if flag and hasattr(self, 'book'):
            self.loadSosPages()
        self.sosPageFlag = flag

    def setFishCollection(self, genusList, speciesList, weightList):
        self.fishCollection = FishCollection.FishCollection()
        self.fishCollection.makeFromNetLists(genusList, speciesList, weightList)

    def getFishCollection(self):
        return self.fishCollection

    def setMaxFishTank(self, maxTank):
        self.maxFishTank = maxTank

    def getMaxFishTank(self):
        return self.maxFishTank

    def setFishTank(self, genusList, speciesList, weightList):
        self.fishTank = FishTank.FishTank()
        self.fishTank.makeFromNetLists(genusList, speciesList, weightList)
        messenger.send(self.uniqueName('fishTankChange'))

    def getFishTank(self):
        return self.fishTank

    def isFishTankFull(self):
        return len(self.fishTank) >= self.maxFishTank

    def setFishingRod(self, rodId):
        self.fishingRod = rodId

    def getFishingRod(self):
        return self.fishingRod

    def setFishingTrophies(self, trophyList):
        self.fishingTrophies = trophyList

    def getFishingTrophies(self):
        return self.fishingTrophies

    def setQuests(self, flattenedQuests):
        questList = []
        questLen = 5
        for i in range(0, len(flattenedQuests), questLen):
            questList.append(flattenedQuests[i:i + questLen])

        self.quests = questList
        if self == base.localAvatar:
            messenger.send('questsChanged')

    def setQuestCarryLimit(self, limit):
        self.questCarryLimit = limit
        if self == base.localAvatar:
            messenger.send('questsChanged')

    def getQuestCarryLimit(self):
        return self.questCarryLimit

    def d_requestDeleteQuest(self, questDesc):
        self.sendUpdate('requestDeleteQuest', [list(questDesc)])

    def setMaxCarry(self, maxCarry):
        self.maxCarry = maxCarry
        if self.isInventoryNewLoaded():
            self.inventory.updateGUI()

    def getMaxCarry(self):
        return self.maxCarry

    def setCheesyEffect(self, effect, hoodId, expireTime):
        self.savedCheesyEffect = effect
        self.savedCheesyHoodId = hoodId
        self.savedCheesyExpireTime = expireTime
        if self == base.localAvatar:
            self.notify.debug('setCheesyEffect(%s, %s, %s)' % (effect, hoodId, expireTime))
            if effect != ToontownGlobals.CENormal:
                serverTime = time.time() + self.cr.getServerDelta()
                duration = expireTime * 60 - serverTime
                if duration < 0:
                    self.notify.debug('effect should have expired %s ago.' % PythonUtil.formatElapsedSeconds(-duration))
                else:
                    self.notify.debug('effect will expire in %s.' % PythonUtil.formatElapsedSeconds(duration))
        if self.activeState == DistributedObject.ESGenerated:
            self.reconsiderCheesyEffect(lerpTime=0.5)
        else:
            self.reconsiderCheesyEffect()

    def reconsiderCheesyEffect(self, lerpTime = 0):
        effect = self.savedCheesyEffect
        hoodId = self.savedCheesyHoodId
        if not self.cr.areCheesyEffectsAllowed():
            effect = CENormal
        if hoodId != 0:
            try:
                currentHoodId = base.cr.playGame.hood.id
            except:
                currentHoodId = None

            if hoodId == 1:
                if currentHoodId == ToontownGlobals.ToontownCentral:
                    effect = CENormal
            elif currentHoodId != None and currentHoodId != hoodId:
                effect = CENormal
        if self.ghostMode:
            effect = CEGhost
        self.applyCheesyEffect(effect, lerpTime=lerpTime)

    def setGhostMode(self, flag):
        if self.ghostMode != flag:
            self.ghostMode = flag
            if not hasattr(self, 'cr'):
                return
            if self.activeState <= DistributedObject.ESDisabled:
                self.notify.debug('not applying cheesy effect to disabled Toon')
            elif self.activeState == DistributedObject.ESGenerating:
                self.reconsiderCheesyEffect()
            elif self.activeState == DistributedObject.ESGenerated:
                self.reconsiderCheesyEffect(lerpTime=0.5)
            else:
                self.notify.warning('unknown activeState: %s' % self.activeState)
            self.showNametag2d()
            self.showNametag3d()
            if hasattr(self, 'collNode'):
                if self.ghostMode:
                    self.collNode.setCollideMask(ToontownGlobals.GhostBitmask)
                else:
                    self.collNode.setCollideMask(ToontownGlobals.WallBitmask | ToontownGlobals.PieBitmask)
            if self.isLocal():
                if self.ghostMode:
                    self.useGhostControls()
                else:
                    self.useWalkControls()
            self.setRun(self.getRun(), base.debugRunningMultiplier)

    if hasattr(base, 'wantPets') and base.wantPets:

        def setPetTrickPhrases(self, petTricks):
            self.petTrickPhrases = petTricks
            if self.isLocal():
                messenger.send('petTrickPhrasesChanged')

    def setCustomMessages(self, customMessages):
        self.customMessages = customMessages
        if self.isLocal():
            messenger.send('customMessagesChanged')

    def setResistanceMessages(self, resistanceMessages):
        self.resistanceMessages = resistanceMessages
        if self.isLocal():
            messenger.send('resistanceMessagesChanged')

    def getResistanceMessageCharges(self, textId):
        msgs = self.resistanceMessages
        for i in range(len(msgs)):
            if msgs[i][0] == textId:
                return msgs[i][1]

        return 0

    def setCatalogSchedule(self, currentWeek, nextTime):
        self.catalogScheduleCurrentWeek = currentWeek
        self.catalogScheduleNextTime = nextTime
        if self.isLocal():
            self.notify.debug('setCatalogSchedule(%s, %s)' % (currentWeek, nextTime))
            if nextTime:
                serverTime = time.time() + self.cr.getServerDelta()
                duration = nextTime * 60 - serverTime
                self.notify.debug('next catalog in %s.' % PythonUtil.formatElapsedSeconds(duration))

    def setCatalog(self, monthlyCatalog, weeklyCatalog, backCatalog):
        self.monthlyCatalog = CatalogItemList.CatalogItemList(monthlyCatalog)
        self.weeklyCatalog = CatalogItemList.CatalogItemList(weeklyCatalog)
        self.backCatalog = CatalogItemList.CatalogItemList(backCatalog)
        if self.catalogNotify == ToontownGlobals.NewItems:
            self.catalogNotify = ToontownGlobals.OldItems

    def setCatalogNotify(self, catalogNotify, mailboxNotify):
        if len(self.weeklyCatalog) + len(self.monthlyCatalog) == 0:
            catalogNotify = ToontownGlobals.NoItems
        if len(self.mailboxContents) == 0:
            mailboxNotify = ToontownGlobals.NoItems
        self.catalogNotify = catalogNotify
        self.mailboxNotify = mailboxNotify
        if self.isLocal():
            self.gotCatalogNotify = 1
            self.refreshOnscreenButtons()

    def setDeliverySchedule(self, onOrder):
        self.onOrder = CatalogItemList.CatalogItemList(onOrder, store=CatalogItem.Customization | CatalogItem.DeliveryDate)
        if self == base.localAvatar:
            nextTime = self.onOrder.getNextDeliveryDate()
            if nextTime != None:
                serverTime = time.time() + self.cr.getServerDelta()
                duration = nextTime * 60 - serverTime
                self.notify.debug('next delivery in %s.' % PythonUtil.formatElapsedSeconds(duration))
            messenger.send('setDeliverySchedule-%s' % self.doId)
        return

    def setMailboxContents(self, mailboxContents):
        self.mailboxContents = CatalogItemList.CatalogItemList(mailboxContents, store=CatalogItem.Customization)
        messenger.send('setMailboxContents-%s' % self.doId)

    def setAwardSchedule(self, onOrder):
        self.onAwardOrder = CatalogItemList.CatalogItemList(onOrder, store=CatalogItem.Customization | CatalogItem.DeliveryDate)
        if self == base.localAvatar:
            nextTime = self.onAwardOrder.getNextDeliveryDate()
            if nextTime != None:
                serverTime = time.time() + self.cr.getServerDelta()
                duration = nextTime * 60 - serverTime
                self.notify.debug('next delivery in %s.' % PythonUtil.formatElapsedSeconds(duration))
            messenger.send('setAwardSchedule-%s' % self.doId)
        return

    def setAwardMailboxContents(self, awardMailboxContents):
        self.notify.debug('Setting awardMailboxContents to %s.' % awardMailboxContents)
        self.awardMailboxContents = CatalogItemList.CatalogItemList(awardMailboxContents, store=CatalogItem.Customization)
        self.notify.debug('awardMailboxContents is %s.' % self.awardMailboxContents)
        messenger.send('setAwardMailboxContents-%s' % self.doId)

    def setAwardNotify(self, awardNotify):
        self.notify.debug('setAwardNotify( %s )' % awardNotify)
        self.awardNotify = awardNotify
        if self.isLocal():
            self.gotCatalogNotify = 1
            self.refreshOnscreenButtons()

    def setGiftSchedule(self, onGiftOrder):
        self.onGiftOrder = CatalogItemList.CatalogItemList(onGiftOrder, store=CatalogItem.Customization | CatalogItem.DeliveryDate)
        if self == base.localAvatar:
            nextTime = self.onGiftOrder.getNextDeliveryDate()
            if nextTime != None:
                serverTime = time.time() + self.cr.getServerDelta()
                duration = nextTime * 60 - serverTime
                self.notify.debug('next delivery in %s.' % PythonUtil.formatElapsedSeconds(duration))
        return

    def playSplashEffect(self, x, y, z):
        if localAvatar.zoneId not in [ToontownGlobals.DonaldsDock, ToontownGlobals.OutdoorZone] and (not hasattr(localAvatar, 'inEstate') or localAvatar.inEstate != 1):
            if random.random() < 0.1:
                self.sendLogSuspiciousEvent('AvatarHackWarning! playing hacked splash effect')
            return
        from toontown.effects import Splash
        if self.splash == None:
            self.splash = Splash.Splash(render)
        self.splash.setPos(x, y, z)
        self.splash.setScale(2)
        self.splash.play()
        place = base.cr.playGame.getPlace()
        if place:
            if hasattr(place.loader, 'submergeSound'):
                base.playSfx(place.loader.submergeSound, node=self)
        return

    def d_playSplashEffect(self, x, y, z):
        self.sendUpdate('playSplashEffect', [x, y, z])

    def setTrackAccess(self, trackArray):
        self.trackArray = trackArray
        if self.isInventoryNewLoaded():
            self.inventory.updateGUI()

    def getTrackAccess(self):
        return self.trackArray

    def hasTrackAccess(self, track):
        return self.trackArray[track]

    def setTrackProgress(self, trackId, progress):
        self.trackProgressId = trackId
        self.trackProgress = progress
        if hasattr(self, 'trackPage'):
            self.trackPage.updatePage()

    def getTrackProgress(self):
        return [self.trackProgressId, self.trackProgress]

    def getTrackProgressAsArray(self, maxLength = 15):
        shifts = list(map(operator.rshift, maxLength * [self.trackProgress], range(maxLength - 1, -1, -1)))
        digits = list(map(operator.mod, shifts, maxLength * [2]))
        digits.reverse()
        return digits

    def setTeleportAccess(self, teleportZoneArray):
        self.teleportZoneArray = teleportZoneArray

    def getTeleportAccess(self):
        return self.teleportZoneArray

    def hasTeleportAccess(self, zoneId):
        return zoneId in self.teleportZoneArray

    def setQuestHistory(self, questList):
        self.questHistory = questList

    def getQuestHistory(self):
        return self.questHistory

    def setRewardHistory(self, rewardTier, rewardList):
        self.rewardTier = rewardTier
        self.rewardHistory = rewardList

    def getRewardHistory(self):
        return (self.rewardTier, self.rewardHistory)

    def doSmoothTask(self, task):
        self.smoother.computeAndApplySmoothPosHpr(self, self)
        self.setSpeed(self.smoother.getSmoothForwardVelocity(), self.smoother.getSmoothRotationalVelocity(),
                      self.smoother.getSmoothLateralVelocity())
        return Task.cont

    def d_setParent(self, parentToken):
        DistributedSmoothNode.DistributedSmoothNode.d_setParent(self, parentToken)

    def setEmoteAccess(self, bits):
        self.emoteAccess = bits
        if self == base.localAvatar:
            messenger.send('emotesChanged')

    def b_setHouseId(self, id):
        self.setHouseId(id)
        self.d_setHouseId(id)

    def d_setHouseId(self, id):
        self.sendUpdate('setHouseId', [id])

    def setHouseId(self, id):
        self.houseId = id

    def getHouseId(self):
        return self.houseId

    def setHouseType(self, index):
        self.houseType = index

    def getHouseType(self):
        return self.houseType

    def setPosIndex(self, index):
        self.posIndex = index

    def getPosIndex(self):
        return self.posIndex

    def b_setSpeedChatStyleIndex(self, index):
        realIndexToSend = 0
        if type(index) == type(0) and 0 <= index and index < len(speedChatStyles):
            realIndexToSend = index
        else:
            base.cr.centralLogger.writeClientEvent('Hacker alert b_setSpeedChatStyleIndex invalid')
        self.setSpeedChatStyleIndex(realIndexToSend)
        self.d_setSpeedChatStyleIndex(realIndexToSend)
        return None

    def d_setSpeedChatStyleIndex(self, index):
        realIndexToSend = 0
        if type(index) == type(0) and 0 <= index and index < len(speedChatStyles):
            realIndexToSend = index
        else:
            base.cr.centralLogger.writeClientEvent('Hacker alert d_setSpeedChatStyleIndex invalid')
        self.sendUpdate('setSpeedChatStyleIndex', [realIndexToSend])

    def setSpeedChatStyleIndex(self, index):
        realIndexToUse = 0
        if type(index) == type(0) and 0 <= index and index < len(speedChatStyles):
            realIndexToUse = index
        else:
            base.cr.centralLogger.writeClientEvent('Hacker victim setSpeedChatStyleIndex invalid attacking toon = %d' % self.doId)
        self.speedChatStyleIndex = realIndexToUse
        nameKey, arrowColor, rolloverColor, frameColor = speedChatStyles[realIndexToUse]
        self.nametag.setQtColor(VBase4(frameColor[0], frameColor[1], frameColor[2], 1))
        if self.isLocal():
            messenger.send('SpeedChatStyleChange', [])

    def getSpeedChatStyleIndex(self):
        return self.speedChatStyleIndex

    def setMaxMoney(self, maxMoney):
        self.maxMoney = maxMoney

    def getMaxMoney(self):
        return self.maxMoney

    def setMoney(self, money):
        if money != self.money:
            self.money = money
            messenger.send(self.uniqueName('moneyChange'), [self.money])

    def getMoney(self):
        return self.money

    def setMaxBankMoney(self, maxMoney):
        self.maxBankMoney = maxMoney

    def getMaxBankMoney(self):
        return self.maxBankMoney

    def setBankMoney(self, money):
        self.bankMoney = money
        messenger.send(self.uniqueName('bankMoneyChange'), [self.bankMoney])

    def getBankMoney(self):
        return self.bankMoney

    def getTotalMoney(self):
        return self.getBankMoney() + self.getMoney()

    def setEmblems(self, emblems):
        if self.emblems != emblems:
            self.emblems = emblems
            messenger.send(self.uniqueName('emblemsChange'), [self.emblems])

    def getEmblems(self):
        return self.emblems

    def setGameTickets(self, tickets):
        # type: (int) -> None
        if tickets != self.gameTickets:
            self.gameTickets = tickets
            messenger.send(self.uniqueName('gameTicketsChange'), [self.gameTickets])

    def getGameTickets(self):
        return self.gameTickets

    def isEnoughEmblemsToBuy(self, itemEmblemPrices):
        for emblemIndex, emblemPrice in enumerate(itemEmblemPrices):
            if emblemIndex >= len(self.emblems):
                return False
            if self.emblems[emblemIndex] < emblemPrice:
                return False

        return True

    def isEnoughMoneyAndEmblemsToBuy(self, moneyPrice, itemEmblemPrices):
        if self.getTotalMoney() < moneyPrice:
            return False
        for emblemIndex, emblemPrice in enumerate(itemEmblemPrices):
            if emblemIndex >= len(self.emblems):
                return False
            if self.emblems[emblemIndex] < emblemPrice:
                return False

        return True

    def presentPie(self, x, y, z, h, p, r, timestamp32):
        if self.numPies <= 0:
            return
        if not launcher.getPhaseComplete(5):
            return
        lastTossTrack = Sequence()
        if self.tossTrack:
            lastTossTrack = self.tossTrack
            tossTrack = None
        ts = globalClockDelta.localElapsedTime(timestamp32, bits=32)
        ts -= self.smoother.getDelay()
        ival = self.getPresentPieInterval(x, y, z, h, p, r)
        if ts > 0:
            startTime = ts
            lastTossTrack.finish()
        else:
            ival = Sequence(Wait(-ts), ival)
            lastTossTrack.finish()
            startTime = 0
        ival = Sequence(ival)
        ival.start(startTime)
        self.tossTrack = ival
        return

    def tossPie(self, x, y, z, h, p, r, sequence, power, timestamp32):
        if self.numPies <= 0:
            return
        if self.numPies != ToontownGlobals.FullPies:
            self.setNumPies(self.numPies - 1)
        self.lastTossedPie = globalClock.getFrameTime()
        if not launcher.getPhaseComplete(5):
            return
        lastTossTrack = Sequence()
        if self.tossTrack:
            lastTossTrack = self.tossTrack
            tossTrack = None
        lastPieTrack = Sequence()
        if sequence in self.pieTracks:
            lastPieTrack = self.pieTracks[sequence]
            del self.pieTracks[sequence]
        ts = globalClockDelta.localElapsedTime(timestamp32, bits=32)
        ts -= self.smoother.getDelay()
        toss, pie, flyPie = self.getTossPieInterval(x, y, z, h, p, r, power)
        if ts > 0:
            startTime = ts
            lastTossTrack.finish()
            lastPieTrack.finish()
        else:
            toss = Sequence(Wait(-ts), toss)
            pie = Sequence(Wait(-ts), pie)
            lastTossTrack.finish()
            lastPieTrack.finish()
            startTime = 0
        self.tossTrack = toss
        toss.start(startTime)
        pie = Sequence(pie, Func(self.pieFinishedFlying, sequence))
        self.pieTracks[sequence] = pie
        pie.start(startTime)
        return

    def pieFinishedFlying(self, sequence):
        if sequence in self.pieTracks:
            del self.pieTracks[sequence]

    def pieFinishedSplatting(self, sequence):
        if sequence in self.splatTracks:
            del self.splatTracks[sequence]

    def pieSplat(self, x, y, z, sequence, pieCode, timestamp32):
        if self.isLocal():
            return
        elapsed = globalClock.getFrameTime() - self.lastTossedPie
        if elapsed > 30:
            return
        if not launcher.getPhaseComplete(5):
            return
        lastPieTrack = Sequence()
        if sequence in self.pieTracks:
            lastPieTrack = self.pieTracks[sequence]
            del self.pieTracks[sequence]
        if sequence in self.splatTracks:
            lastSplatTrack = self.splatTracks[sequence]
            del self.splatTracks[sequence]
            lastSplatTrack.finish()
        ts = globalClockDelta.localElapsedTime(timestamp32, bits=32)
        ts -= self.smoother.getDelay()
        splat = self.getPieSplatInterval(x, y, z, pieCode)
        splat = Sequence(Func(messenger.send, 'pieSplat', [self, pieCode]), splat)
        if ts > 0:
            startTime = ts
            lastPieTrack.finish()
        else:
            splat = Sequence(Wait(-ts), splat)
            startTime = 0
        splat = Sequence(splat, Func(self.pieFinishedSplatting, sequence))
        self.splatTracks[sequence] = splat
        splat.start(startTime)

    def cleanupPies(self):
        for track in list(self.pieTracks.values()):
            track.finish()

        self.pieTracks = {}
        for track in list(self.splatTracks.values()):
            track.finish()

        self.splatTracks = {}
        self.cleanupPieInHand()

    def cleanupPieInHand(self):
        if self.tossTrack:
            self.tossTrack.finish()
            self.tossTrack = None
        self.cleanupPieModel()

    def useFeather(self, x, y, z, h, p, r, timestamp32):
        if self.numPies <= 0:
            return
        if not launcher.getPhaseComplete(5):
            return
        if self.featherTrack:
            self.featherTrack.finish()
            self.featherTrack = None
        ts = globalClockDelta.localElapsedTime(timestamp32, bits=32)
        ts -= self.smoother.getDelay()
        ival = self.getFeatherInterval()#(x, y, z, h, p, r)
        if ts > 0:
            startTime = ts
        else:
            ival = Sequence(Wait(-ts), ival)
            startTime = 0
        ival = Sequence(ival)
        ival.start(startTime)
        self.featherTrack = ival

    def setNumPies(self, numPies):
        self.numPies = numPies
        if self.isLocal():
            self.updatePieButton()
            if numPies == 0:
                self.interruptPie()

    def setPieType(self, pieType):
        self.pieType = pieType
        if self.isLocal():
            self.updatePieButton()

    def setTrophyScore(self, score):
        self.trophyScore = score
        if self.trophyStar != None:
            self.trophyStar.removeNode()
            self.trophyStar = None
        if self.trophyStarSpeed != 0:
            taskMgr.remove(self.uniqueName('starSpin'))
            self.trophyStarSpeed = 0
        if hasattr(self, 'gmIcon') and self.gmIcon:
            return
        if self.trophyScore >= ToontownGlobals.TrophyStarLevels[6]:
            self.trophyStar = DistributedToon.nameStar.find('**/star_diamond').copyTo(self.nametag.getNameIcon())
            self.trophyStar.setScale(2)
            self.trophyStar.setZ(2)
            self.trophyStarSpeed = ToontownGlobals.TrophyStarSpeed[7]
            if self.trophyScore >= ToontownGlobals.TrophyStarLevels[7]:
                taskMgr.add(self.__starSpin, self.uniqueName('starSpin'))
        elif self.trophyScore >= ToontownGlobals.TrophyStarLevels[4]:
            self.trophyStar = DistributedToon.nameStar.find('**/star_normal').copyTo(self.nametag.getNameIcon())
            self.trophyStar.setScale(2)
            self.trophyStar.setZ(2)
            self.trophyStar.setColor(ToontownGlobals.TrophyStarColors[4])
            self.trophyStarSpeed = ToontownGlobals.TrophyStarSpeed[5]
            if self.trophyScore >= ToontownGlobals.TrophyStarLevels[5]:
                taskMgr.add(self.__starSpin, self.uniqueName('starSpin'))
        elif self.trophyScore >= ToontownGlobals.TrophyStarLevels[2]:
            self.trophyStar = DistributedToon.nameStar.find('**/star_normal').copyTo(self.nametag.getNameIcon())
            self.trophyStar.setScale(1.5)
            self.trophyStar.setZ(1.6)
            self.trophyStarSpeed = ToontownGlobals.TrophyStarSpeed[3]
            if self.trophyScore >= ToontownGlobals.TrophyStarLevels[3]:
                taskMgr.add(self.__starSpin, self.uniqueName('starSpin'))
        elif self.trophyScore >= ToontownGlobals.TrophyStarLevels[0]:
            self.trophyStar = DistributedToon.nameStar.find('**/star_normal').copyTo(self.nametag.getNameIcon())
            self.trophyStar.setScale(1.5)
            self.trophyStar.setZ(1.6)
            self.trophyStar.setColor(ToontownGlobals.TrophyStarColors[0])
            self.trophyStarSpeed = ToontownGlobals.TrophyStarSpeed[1]
            if self.trophyScore >= ToontownGlobals.TrophyStarLevels[1]:
                taskMgr.add(self.__starSpin, self.uniqueName('starSpin'))
        return

    def __starSpin(self, task):
        now = globalClock.getFrameTime()
        r = now * self.trophyStarSpeed % 360.0
        self.trophyStar.setR(r)
        return Task.cont

    def getZoneId(self):
        place = base.cr.playGame.getPlace()
        if place:
            return place.getZoneId()
        else:
            return None
        return None

    def getRequestID(self):
        return CLIENT_GET_AVATAR_DETAILS

    def announceBingo(self):
        self.setChatAbsolute(TTLocalizer.FishBingoBingo, CFSpeech | CFTimeout)

    def playStunEffect(self):
        self.stunToon()

    def squish(self, damage, noAnim=False):
        if self == base.localAvatar:
            if not noAnim:
                base.cr.playGame.getPlace().fsm.request('squished')
            self.stunToon()
            self.setZ(self.getZ(render) + 0.025)

    def d_squish(self, damage):
        self.sendUpdate('squish', [damage])

    def b_squish(self, damage, noAnim=False):
        if not self.isStunned:
            self.squish(damage, noAnim)
            self.d_squish(damage)
            self.playDialogueForString('!')

    def getShadowJoint(self):
        return Toon.Toon.getShadowJoint(self)

    if base.wantKarts:

        def hasKart(self):
            return self.kartDNA[KartDNA.bodyType] != -1

        def getKartDNA(self):
            return self.kartDNA

        def setTickets(self, numTickets):
            self.tickets = numTickets

        def getTickets(self):
            return self.tickets

        def getAccessoryByType(self, accType):
            return self.kartDNA[accType]

        def setCurrentKart(self, avId):
            self.kartId = avId

        def releaseKart(self):
            self.kartId = None
            return

        def setKartBodyType(self, bodyType):
            self.kartDNA[KartDNA.bodyType] = bodyType

        def getKartBodyType(self):
            return self.kartDNA[KartDNA.bodyType]

        def setKartBodyColor(self, bodyColor):
            self.kartDNA[KartDNA.bodyColor] = bodyColor

        def getKartBodyColor(self):
            return self.kartDNA[KartDNA.bodyColor]

        def setKartAccessoryColor(self, accColor):
            self.kartDNA[KartDNA.accColor] = accColor

        def getKartAccessoryColor(self):
            return self.kartDNA[KartDNA.accColor]

        def setKartEngineBlockType(self, ebType):
            self.kartDNA[KartDNA.ebType] = ebType

        def getKartEngineBlockType(self):
            return self.kartDNA[KartDNA.ebType]

        def setKartSpoilerType(self, spType):
            self.kartDNA[KartDNA.spType] = spType

        def getKartSpoilerType(self):
            return self.kartDNA[KartDNA.spType]

        def setKartFrontWheelWellType(self, fwwType):
            self.kartDNA[KartDNA.fwwType] = fwwType

        def getKartFrontWheelWellType(self):
            return self.kartDNA[KartDNA.fwwType]

        def setKartBackWheelWellType(self, bwwType):
            self.kartDNA[KartDNA.bwwType] = bwwType

        def getKartBackWheelWellType(self):
            return self.kartDNA[KartDNA.bwwType]

        def setKartRimType(self, rimsType):
            self.kartDNA[KartDNA.rimsType] = rimsType

        def setKartDecalType(self, decalType):
            self.kartDNA[KartDNA.decalType] = decalType

        def getKartDecalType(self):
            return self.kartDNA[KartDNA.decalType]

        def getKartRimType(self):
            return self.kartDNA[KartDNA.rimsType]

        def setKartAccessoriesOwned(self, accessories):
            while len(accessories) < 16:
                accessories.append(-1)

            self.accessories = accessories

        def getKartAccessoriesOwned(self):
            owned = copy.deepcopy(self.accessories)
            while InvalidEntry in owned:
                owned.remove(InvalidEntry)

            return owned

        def requestKartDNAFieldUpdate(self, dnaField, fieldValue):
            self.notify.debug('requestKartDNAFieldUpdate - dnaField %s, fieldValue %s' % (dnaField, fieldValue))
            self.sendUpdate('updateKartDNAField', [dnaField, fieldValue])

        def requestAddOwnedAccessory(self, accessoryId):
            self.notify.debug('requestAddOwnedAccessor - purchased accessory %s' % accessoryId)
            self.sendUpdate('addOwnedAccessory', [accessoryId])

        def requestRemoveOwnedAccessory(self, accessoryId):
            self.notify.debug('requestRemoveOwnedAccessor - removed accessory %s' % accessoryId)
            self.sendUpdate('removeOwnedAccessory', [accessoryId])

        def setKartingTrophies(self, trophyList):
            self.kartingTrophies = trophyList

        def getKartingTrophies(self):
            return self.kartingTrophies

        def setKartingHistory(self, history):
            self.kartingHistory = history

        def getKartingHistory(self):
            return self.kartingHistory

        def setKartingPersonalBest(self, bestTimes):
            self.kartingPersonalBest = bestTimes

        def getKartingPersonalBest(self):
            return self.kartingPersonalBest

        def setKartingPersonalBest2(self, bestTimes2):
            self.kartingPersonalBest2 = bestTimes2

        def getKartingPersonalBest2(self):
            return self.kartingPersonalBest2

        def getKartingPersonalBestAll(self):
            return self.kartingPersonalBest + self.kartingPersonalBest2

    if hasattr(base, 'wantPets') and base.wantPets:

        def setPetId(self, petId):
            self.petId = petId
            if petId == 0:
                self.petDNA = None
            elif self.isLocal():
                base.cr.setPetHandle()

        def getPetId(self):
            return self.petId

        def hasPet(self):
            return self.petId != 0

        def b_setPetTutorialDone(self, bDone):
            self.d_setPetTutorialDone(bDone)
            self.setPetTutorialDone(bDone)

        def d_setPetTutorialDone(self, bDone):
            self.sendUpdate('setPetTutorialDone', [bDone])

        def setPetTutorialDone(self, bDone):
            self.bPetTutorialDone = bDone

        def b_setFishBingoTutorialDone(self, bDone):
            self.d_setFishBingoTutorialDone(bDone)
            self.setFishBingoTutorialDone(bDone)

        def d_setFishBingoTutorialDone(self, bDone):
            self.sendUpdate('setFishBingoTutorialDone', [bDone])

        def setFishBingoTutorialDone(self, bDone):
            self.bFishBingoTutorialDone = bDone

        def b_setFishBingoMarkTutorialDone(self, bDone):
            self.d_setFishBingoMarkTutorialDone(bDone)
            self.setFishBingoMarkTutorialDone(bDone)

        def d_setFishBingoMarkTutorialDone(self, bDone):
            self.sendUpdate('setFishBingoMarkTutorialDone', [bDone])

        def setFishBingoMarkTutorialDone(self, bDone):
            self.bFishBingoMarkTutorialDone = bDone

        def b_setPetMovie(self, petId, flag):
            self.d_setPetMovie(petId, flag)
            self.setPetMovie(petId, flag)

        def d_setPetMovie(self, petId, flag):
            self.sendUpdate('setPetMovie', [petId, flag])

        def setPetMovie(self, petId, flag):
            pass

        def lookupPetDNA(self):
            if self.petId and not self.petDNA:
                from toontown.pets import PetDetail
                PetDetail.PetDetail(self.petId, self.__petDetailsLoaded)

        def __petDetailsLoaded(self, pet):
            self.petDNA = pet.style

    def trickOrTreatTargetMet(self, beanAmount):
        self.effect = TrickOrTreatTargetEffect(beanAmount, self.getJarPos())
        self.effect.play()

    def winterCarolingTargetMet(self, beanAmount):
        self.effect = WinterCarolingEffect(beanAmount, self.getJarPos())
        self.effect.play()

    def d_reqCogSummons(self, type, suitIndex, invasionAmount):
        self.sendUpdate('reqCogSummons', [type, suitIndex, invasionAmount])

    def cogSummonsResponse(self, returnCode, suitIndex, doId):
        messenger.send('cog-summons-response', [returnCode, suitIndex, doId])

    def setCogSummonsEarned(self, cogSummonsEarned):
        self.cogSummonsEarned = cogSummonsEarned

    def getCogSummonsEarned(self):
        return self.cogSummonsEarned

    def hasCogSummons(self, suitIndex, type = None):
        summons = self.getCogSummonsEarned()
        curSetting = summons[suitIndex]
        if type == 'single':
            return curSetting & 1
        elif type == 'building':
            return curSetting & 2
        elif type == 'invasion':
            return curSetting & 4
        return curSetting

    def setFlowerCollection(self, speciesList, varietyList):
        self.flowerCollection = FlowerCollection.FlowerCollection()
        self.flowerCollection.makeFromNetLists(speciesList, varietyList)

    def getFlowerCollection(self):
        return self.flowerCollection

    def setMaxFlowerBasket(self, maxFlowerBasket):
        self.maxFlowerBasket = maxFlowerBasket

    def getMaxFlowerBasket(self):
        return self.maxFlowerBasket

    def isFlowerBasketFull(self):
        return len(self.flowerBasket) >= self.maxFlowerBasket

    def setFlowerBasket(self, speciesList, varietyList):
        self.flowerBasket = FlowerBasket.FlowerBasket()
        self.flowerBasket.makeFromNetLists(speciesList, varietyList)
        messenger.send('flowerBasketUpdated')

    def getFlowerBasket(self):
        return self.flowerBasket

    def setShovel(self, shovelId):
        self.shovel = shovelId

    def attachShovel(self):
        self.shovelModel = self.getShovelModel()
        self.shovelModel.reparentTo(self.rightHand)
        return self.shovelModel

    def detachShovel(self):
        if self.shovelModel:
            self.shovelModel.removeNode()

    def getShovelModel(self):
        shovels = loader.loadModel('phase_5.5/models/estate/shovels')
        shovelId = ['A',
         'B',
         'C',
         'D'][self.shovel]
        shovel = shovels.find('**/shovel' + shovelId)
        shovel.setH(-90)
        shovel.setP(216)
        shovel.setX(0.2)
        shovel.detachNode()
        shovels.removeNode()
        return shovel

    def setShovelSkill(self, skillLevel):
        self.shovelSkill = skillLevel

    def getBoxCapability(self):
        return GardenGlobals.getShovelPower(self.shovel, self.shovelSkill)

    def setWateringCan(self, wateringCanId):
        self.wateringCan = wateringCanId

    def attachWateringCan(self):
        self.wateringCanModel = self.getWateringCanModel()
        self.wateringCanModel.reparentTo(self.rightHand)
        return self.wateringCanModel

    def detachWateringCan(self):
        if self.wateringCanModel:
            self.wateringCanModel.removeNode()

    def getWateringCanModel(self):
        scalePosHprsTable = ((0.25, 0.1, 0, 0.2, -90, -125, -45),
         (0.2, 0.0, 0.25, 0.2, -90, -125, -45),
         (0.2, 0.2, 0.1, 0.2, -90, -125, -45),
         (0.2, 0.0, 0.25, 0.2, -90, -125, -45))
        cans = loader.loadModel('phase_5.5/models/estate/watering_cans')
        canId = ['A',
         'B',
         'C',
         'D'][self.wateringCan]
        can = cans.find('**/water_can' + canId)
        can.setScale(scalePosHprsTable[self.wateringCan][0])
        can.setPos(scalePosHprsTable[self.wateringCan][1], scalePosHprsTable[self.wateringCan][2], scalePosHprsTable[self.wateringCan][3])
        can.setHpr(scalePosHprsTable[self.wateringCan][4], scalePosHprsTable[self.wateringCan][5], scalePosHprsTable[self.wateringCan][6])
        can.detachNode()
        cans.removeNode()
        if hasattr(base, 'rwc'):
            if base.rwc:
                if hasattr(self, 'wateringCan2'):
                    self.wateringCan2.removeNode()
                self.wateringCan2 = can.copyTo(self.rightHand)
            else:
                self.wateringCan2.removeNode()
        return can

    def setWateringCanSkill(self, skillLevel):
        self.wateringCanSkill = skillLevel

    def setGardenSpecials(self, specials):
        self.gardenSpecials = specials
        if hasattr(self, 'gardenPage') and self.gardenPage:
            self.gardenPage.updatePage()

    def getGardenSpecials(self):
        return self.gardenSpecials

    def getMyTrees(self):
        treeDict = self.cr.getObjectsOfClass(DistributedGagTree.DistributedGagTree)
        trees = []
        for tree in list(treeDict.values()):
            if tree.getOwnerId() == self.doId:
                trees.append(tree)

        if not trees:
            pass
        return trees

    def isTreePlanted(self, track, level):
        trees = self.getMyTrees()
        for tree in trees:
            if tree.gagTrack == track and tree.gagLevel == level:
                return True

        return False

    def doIHaveRequiredTrees(self, track, level):
        trees = self.getMyTrees()
        trackAndLevelList = []
        for tree in trees:
            trackAndLevelList.append((tree.gagTrack, tree.gagLevel))

        haveRequired = True
        for curLevel in range(level):
            testTuple = (track, curLevel)
            if testTuple not in trackAndLevelList:
                haveRequired = False
                break

        return haveRequired

    def setTrackBonusLevel(self, trackArray):
        self.trackBonusLevel = trackArray
        if self.isInventoryNewLoaded():
            self.inventory.updateGUI()

    def getTrackBonusLevel(self, track = None):
        if track == None:
            return self.trackBonusLevel
        else:
            return self.trackBonusLevel[track]
        return

    def checkGagBonus(self, track, level):
        trackBonus = self.getTrackBonusLevel(track)
        return trackBonus >= level

    def setGardenTrophies(self, trophyList):
        self.gardenTrophies = trophyList

    def getGardenTrophies(self):
        return self.gardenTrophies

    def useSpecialResponse(self, returnCode):
        messenger.send('use-special-response', [returnCode])

    def setGardenStarted(self, bStarted):
        self.gardenStarted = bStarted

    def getGardenStarted(self):
        return self.gardenStarted

    def sendToGolfCourse(self, zoneId):
        print('sending to golfCourse')
        hoodId = self.cr.playGame.hood.hoodId
        golfRequest = {'loader': 'safeZoneLoader',
         'where': 'golfcourse',
         'how': 'teleportIn',
         'hoodId': hoodId,
         'zoneId': zoneId,
         'avId': -1}
        base.cr.playGame.getPlace().requestLeave(golfRequest)

    def getGolfTrophies(self):
        return self.golfTrophies

    def getGolfCups(self):
        return self.golfCups

    def setGolfHistory(self, history):
        self.golfHistory = history
        self.golfTrophies = GolfGlobals.calcTrophyListFromHistory(self.golfHistory)
        self.golfCups = GolfGlobals.calcCupListFromHistory(self.golfHistory)
        if hasattr(self, 'book'):
            self.addGolfPage()

    def getGolfHistory(self):
        return self.golfHistory

    def hasPlayedGolf(self):
        retval = False
        for historyValue in self.golfHistory:
            if historyValue:
                retval = True
                break

        return retval

    def setPackedGolfHoleBest(self, packedHoleBest):
        unpacked = GolfGlobals.unpackGolfHoleBest(packedHoleBest)
        self.setGolfHoleBest(unpacked)

    def setGolfHoleBest(self, holeBest):
        self.golfHoleBest = holeBest

    def getGolfHoleBest(self):
        return self.golfHoleBest

    def setGolfCourseBest(self, courseBest):
        self.golfCourseBest = courseBest

    def getGolfCourseBest(self):
        return self.golfCourseBest

    def setUnlimitedSwing(self, unlimitedSwing):
        self.unlimitedSwing = unlimitedSwing

    def getUnlimitedSwing(self):
        return self.unlimitedSwing

    def getPinkSlips(self):
        if hasattr(self, 'pinkSlips'):
            return self.pinkSlips
        else:
            return 0

    def setPinkSlips(self, pinkSlips):
        self.pinkSlips = pinkSlips

    def setAccess(self, access):
        self.setGameAccess(access)
        self.setDisplayName(self.getName())

    def setGameAccess(self, access):
        self.gameAccess = access

    def getGameAccess(self):
        if hasattr(self, 'gameAccess'):
            return self.gameAccess
        else:
            return 0

    def setDisplayName(self, str):
        if not self.getTransformationsIndex(ToontownGlobals.TransformationCog):
            self.setFancyNametag(name=str)
        else:
            self.removeFancyNametag()
            Avatar.Avatar.setDisplayName(self, str)

    def setFancyNametag(self, name = None):
        if name == None:
            name = self.getName()
        if self.getNametagStyle() == 100:
            self.setFont(ToontownGlobals.getToonFont(), False)
        else:
            self.setFont(ToontownGlobals.getNametagFont(self.getNametagStyle()), False)
        Avatar.Avatar.setDisplayName(self, name)
        self.setFont(ToontownGlobals.getToonFont(), False)
        return

    def removeFancyNametag(self):
        self.nametag.clearShadow()

    def getNametagStyle(self):
        if hasattr(self, 'nametagStyle'):
            return self.nametagStyle
        else:
            return 0

    def setNametagStyle(self, nametagStyle):
        if base.config.GetBool('want-nametag-avids', 0):
            nametagStyle = 0
        # Load suit font if it's not already
        if nametagStyle == TTLocalizer.NametagFonts.index(TTLocalizer.SuitFont):
            ToontownGlobals.getSuitFont()
        self.nametagStyle = nametagStyle
        self.setDisplayName(self.getName())

    def getNametagType(self):
        if hasattr(self, 'nametagType'):
            return self.nametagType
        else:
            return 0

    def setNametagType(self, type):
        self.nametagType = type
        if type == 0:
            self.considerUnderstandable()
        else:
            self.setPlayerType(type, True)
        self.setDisplayName(self.getName())
        if not self.isLocal():
            self.setPickable(1)

    def getNametagColor(self):
        if hasattr(self, 'nametagColor'):
            return self.nametagColor
        else:
            return (0, 0, 0)

    def setNametagColor(self, r, g, b):
        self.nametagColor = (r / 255, g / 255, b / 255)

        self.nametag.setCustomColor(Vec4(r, g, b, 1))
        self.setDisplayName(self.getName())
        if not self.isLocal():
            self.setPickable(1)

    def getAvIdName(self):
        paidStr = PythonUtil.choice(self.getGameAccess() == OTPGlobals.AccessFull, 'P', 'F')
        return '%s\n%s (%s)' % (self.getName(), self.doId, paidStr)

    def playCurrentDialogue(self, dialogue, chatFlags, interrupt = 1):
        DistributedAvatar.DistributedAvatar.playCurrentDialogue(self, dialogue, chatFlags, interrupt)

    def playDialogueForString(self, chatString, delay = 0.0, exclaim = False):
        if len(chatString) == 0:
            return
        DistributedAvatar.DistributedAvatar.playDialogueForString(self, chatString, delay, exclaim)

    def playDialogue(self, type, length, chatString = '', delay = 0.0):
        DistributedAvatar.DistributedAvatar.playDialogue(self, type, length, chatString, delay)

    def sendLogMessage(self, message):
        self.sendUpdate('logMessage', [message])

    def setChatAbsolute(self, chatString, chatFlags, dialogue = None, interrupt = 1):
        DistributedAvatar.DistributedAvatar.setChatAbsolute(self, chatString, chatFlags, dialogue, interrupt)

    def setChatMuted(self, chatString, chatFlags, dialogue = None, interrupt = 1):
        self.nametag.setChat(chatString, chatFlags)
        self.playCurrentDialogue(dialogue, chatFlags - CFSpeech, interrupt)

    def displayTalk(self, chatString, mods = None):
        DistributedAvatar.DistributedAvatar.displayTalk(self, chatString)
        flags = CFSpeech | CFTimeout
        if base.talkAssistant.isThought(chatString):
            flags = CFThought
        elif base.talkAssistant.isExclaim(chatString):
            flags = CFExclaim | CFTimeout
        self.playCurrentDialogue(None, flags, interrupt=1)
        return

    def setSystemMessage(self, aboutId, chatString, whisperType = WhisperPopup.WTSystem):
        for chat in base.emojis:
            chatString = chatString.replace(f':{chat}:', f'\x01white\x01\5{chat}\5\x02')
        if whisperType == WhisperPopup.WTAnnouncement:
            taskName = self.uniqueName('cleanupSystemMessage')
            taskMgr.remove(taskName)
            self.cleanupSystemMessage()

            self.systemMessage = OnscreenText(parent = base.a2dTopCenter,
                                              wordwrap = 22,
                                              scale = 0.1,
                                              fg = (1, 0, 0, 1),
                                              font = ToontownGlobals.getSignFont(),
                                              pos = (0, -0.12),
                                              text = chatString)
            ival = Parallel(
                    LerpColorScaleInterval(
                            self.systemMessage,
                            0.2,
                            colorScale = VBase4(1.0),
                            startColorScale = VBase4(1.0, 1.0, 1.0, 0.0)
                    ),
                    Sequence(
                            LerpScaleInterval(
                                    self.systemMessage,
                                    0.2,
                                    scale = 1.1,
                                    startScale = 0,
                                    blendType = 'easeInOut'
                            ),
                            LerpScaleInterval(
                                    self.systemMessage,
                                    0.1,
                                    scale = 1,
                                    blendType = 'easeInOut'
                            ),
                    ),
                    name = 'announcement-popup-anim'
            )
            self.systemMessage.setBin('gui-popup', 0)
            self.storeInterval(ival, self.uniqueName('systemMessage'))
            ival.start()
            sfx = self.soundSystemMessage
            base.playSfx(sfx)

            # HACK: This is taken from the old python-based libotp,
            # I don't want to struggle getting the getWhisperColor
            # function published in the new C based nametags right now.
            # ~Little Cat
            color = Vec4(0.8, 0.3, 0.6, 1.0)
            messenger.send('addToLog', [None, aboutId, None, None, color, chatString, WhisperPopup.WTAnnouncement])

            duration = len(chatString) * 0.1
            taskMgr.doMethodLater(duration, self.cleanupSystemMessage, taskName, extraArgs=[])
            return
        messenger.send('notifyMisc', [chatString])
        self.displayWhisper(aboutId, chatString, whisperType)

    def cleanupSystemMessage(self):
        if hasattr(self, 'systemMessage') and self.systemMessage:
            ival = Sequence(LerpColorScaleInterval(self.systemMessage, 0.5, (1.0, 1.0, 1.0, 0.0)), Func(self.systemMessage.destroy))
            self.storeInterval(ival, self.uniqueName('systemMessage'))
            ival.start()

    def setMail(self, mail):
        DistributedToon.partyNotify.debug('setMail called with %d mail items' % len(mail))
        self.mail = []
        for i in range(len(mail)):
            oneMailItem = mail[i]
            newMail = SimpleMailBase(*oneMailItem)
            self.mail.append(newMail)

    def setSimpleMailNotify(self, simpleMailNotify):
        DistributedToon.partyNotify.debug('setSimpleMailNotify( %s )' % simpleMailNotify)
        self.simpleMailNotify = simpleMailNotify
        if self.isLocal():
            self.gotCatalogNotify = 1
            self.refreshOnscreenButtons()

    def setInviteMailNotify(self, inviteMailNotify):
        DistributedToon.partyNotify.debug('setInviteMailNotify( %s )' % inviteMailNotify)
        self.inviteMailNotify = inviteMailNotify
        if self.isLocal():
            self.gotCatalogNotify = 1
            self.refreshOnscreenButtons()

    def setInvites(self, invites):
        DistributedToon.partyNotify.debug('setInvites called passing in %d invites.' % len(invites))
        self.invites = []
        for i in range(len(invites)):
            oneInvite = invites[i]
            newInvite = InviteInfo(*oneInvite)
            self.invites.append(newInvite)

    def updateInviteMailNotify(self):
        invitesInMailbox = self.getInvitesToShowInMailbox()
        newInvites = 0
        readButNotRepliedInvites = 0
        for invite in invitesInMailbox:
            if invite.status == PartyGlobals.InviteStatus.NotRead:
                newInvites += 1
            elif invite.status == PartyGlobals.InviteStatus.ReadButNotReplied:
                readButNotRepliedInvites += 1
            if __dev__:
                partyInfo = self.getOnePartyInvitedTo(invite.partyId)
                if not partyInfo:
                    self.notify.error('party info not found in partiesInvtedTo, partyId = %s' % str(invite.partyId))

        if newInvites:
            self.setInviteMailNotify(ToontownGlobals.NewItems)
        elif readButNotRepliedInvites:
            self.setInviteMailNotify(ToontownGlobals.OldItems)
        else:
            self.setInviteMailNotify(ToontownGlobals.NoItems)

    def getInvitesToShowInMailbox(self):
        result = []
        for invite in self.invites:
            appendInvite = True
            if invite.status == InviteStatus.Accepted or invite.status == InviteStatus.Rejected:
                appendInvite = False
            if appendInvite:
                partyInfo = self.getOnePartyInvitedTo(invite.partyId)
                if not partyInfo:
                    appendInvite = False
                if appendInvite:
                    if partyInfo.status == PartyGlobals.PartyStatus.Cancelled:
                        appendInvite = False
                if appendInvite:
                    endDate = partyInfo.endTime.date()
                    curDate = base.cr.toontownTimeManager.getCurServerDateTime().date()
                    if endDate < curDate:
                        appendInvite = False
            if appendInvite:
                result.append(invite)

        return result

    def getNumInvitesToShowInMailbox(self):
        result = len(self.getInvitesToShowInMailbox())
        return result

    def setOldHostedParties(self, hostedParties):
        DistributedToon.partyNotify.debug('setOldHostedParties called with {} parties.'.format(len(hostedParties)))
        self.oldHostedParties = []
        for i in range(len(hostedParties)):
            hostedData = hostedParties[i]
            newParty = PartyInfo(-1,                # party ID doesn't matter
                                 hostedData[0],
                                 hostedData[1][0],
                                 hostedData[1][1],
                                 hostedData[1][2],
                                 hostedData[1][3],
                                 hostedData[1][4],
                                 hostedData[2][0],
                                 hostedData[2][1],
                                 hostedData[2][2],
                                 hostedData[2][3],
                                 hostedData[2][4],
                                 hostedData[4],
                                 hostedData[5],
                                 [],                # activity list doesn't matter
                                 [],                # decor list doesn't matter
                                 hostedData[6]
                                 )
            self.oldHostedParties.append(newParty)

    def setOldPartiesInvitedTo(self, partiesInvitedTo):
        DistributedToon.partyNotify.debug('setOldPartiesInvitedTo called with {} parties.'.format(len(partiesInvitedTo)
                                                                                                  ))
        self.oldPartiesInvitedTo = []
        for i in range(len(partiesInvitedTo)):
            partyData = partiesInvitedTo[i]
            newParty = PartyInfo(-1,                # party ID doesn't matter
                                 partyData[0],
                                 partyData[1][0],
                                 partyData[1][1],
                                 partyData[1][2],
                                 partyData[1][3],
                                 partyData[1][4],
                                 partyData[2][0],
                                 partyData[2][1],
                                 partyData[2][2],
                                 partyData[2][3],
                                 partyData[2][4],
                                 partyData[4],
                                 partyData[5],
                                 [],                # activity list doesn't matter
                                 [],                # decor list doesn't matter
                                 partyData[6]
                                 )
            self.oldPartiesInvitedTo.append(newParty)

    def setHostedParties(self, hostedParties):
        DistributedToon.partyNotify.debug('setHostedParties called passing in %d parties.' % len(hostedParties))
        self.hostedParties = []
        for i in range(len(hostedParties)):
            hostedInfo = hostedParties[i]
            newParty = PartyInfo(*hostedInfo)
            self.hostedParties.append(newParty)

    def setPartiesInvitedTo(self, partiesInvitedTo):
        DistributedToon.partyNotify.debug('setPartiesInvitedTo called passing in %d parties.' % len(partiesInvitedTo))
        self.partiesInvitedTo = []
        for i in range(len(partiesInvitedTo)):
            partyInfo = partiesInvitedTo[i]
            newParty = PartyInfo(*partyInfo)
            self.partiesInvitedTo.append(newParty)

        self.updateInviteMailNotify()

    def getOnePartyInvitedTo(self, partyId):
        result = None
        for i in range(len(self.partiesInvitedTo)):
            partyInfo = self.partiesInvitedTo[i]
            if partyInfo.partyId == partyId:
                result = partyInfo
                break

        return result

    def getInviteForPartyId(self, partyId):
        result = None
        for invite in self.invites:
            if invite.partyId == partyId:
                result = invite
                break

        return result

    def setPartyReplies(self, replies):
        DistributedToon.partyNotify.debug('setPartyReplies called passing in %d parties.' % len(replies))
        self.partyReplyInfoBases = []
        for i in range(len(replies)):
            partyReply = replies[i]
            repliesForOneParty = PartyReplyInfoBase(*partyReply)
            self.partyReplyInfoBases.append(repliesForOneParty)

    def setPartyCanStart(self, partyId):
        DistributedToon.partyNotify.debug('setPartyCanStart called passing in partyId=%s' % partyId)
        for partyInfo in self.hostedParties:
            if partyInfo.partyId == partyId:
                partyInfo.status = PartyGlobals.PartyStatus.CanStart
                from toontown.shtiker import EventsPage
                if hasattr(self, 'eventsPage') and base.localAvatar.book.entered and base.localAvatar.book.isOnPage(self.eventsPage) and self.eventsPage.getMode() == EventsPage.EventsPage_Host:
                    base.localAvatar.eventsPage.loadHostedPartyInfo()
                if hasattr(self, 'displaySystemClickableWhisper'):
                    self.displaySystemClickableWhisper(0, TTLocalizer.PartyCanStart, whisperType=WhisperPopup.WTSystem)
                else:
                    self.setSystemMessage(0, TTLocalizer.PartyCanStart)

    def setPartyTimedOut(self):
        DistributedToon.partyNotify.debug('One of our parties timed out.')
        # hostedParties len should be 0, however, if we somehow get this message before the UD sends the updated
        # hostedParties, and we only had 1 party, then assume we'll get it anyways and disable the buttons
        # if, however, there are somehow more than 1 hosted parties, assume other parties will take care of buttons
        if len(self.hostedParties) in (0, 1):
            DistributedToon.partyNotify.debug('All parties timed out; alerting user.')
            self.hostedParties = []
            if hasattr(self, 'displaySystemClickableWhisper'):
                self.displaySystemClickableWhisper(0, TTLocalizer.PartyTimedOut, whisperType=WhisperPopup.WTSystem)
            else:
                self.setSystemMessage(0, TTLocalizer.PartyTimedOut)
        # do this after, for both cases (if there is an 'else' case)
        from toontown.shtiker import EventsPage
        if hasattr(self, 'eventsPage') and base.localAvatar.book.entered and base.localAvatar.book.isOnPage(
                self.eventsPage) and self.eventsPage.getMode() == EventsPage.EventsPage_Host:
            base.localAvatar.eventsPage.loadHostedPartyInfo()

    def setPartyStatus(self, partyId, newStatus):
        DistributedToon.partyNotify.debug('setPartyCanStatus called passing in partyId=%s status=%s' % (partyId, newStatus))
        found = False
        for partyInfo in self.hostedParties:
            if partyInfo.partyId == partyId:
                partyInfo.status = newStatus
                found = True
                break

        for partyInfo in self.partiesInvitedTo:
            if partyInfo.partyId == partyId:
                partyInfo.status = newStatus
                found = True
                from toontown.shtiker import EventsPage
                if hasattr(self, 'eventsPage') and base.localAvatar.book.entered and base.localAvatar.book.isOnPage(self.eventsPage) and self.eventsPage.getMode() == EventsPage.EventsPage_Invited:
                    base.localAvatar.eventsPage.loadInvitations()
                if newStatus == PartyStatus.Started and hasattr(self, 'displaySystemClickableWhisper'):
                    invite = self.getInviteForPartyId(partyId)
                    if invite:
                        name = ' '
                        host = base.cr.identifyAvatar(partyInfo.hostId)
                        if host:
                            name = host.getName()
                        if invite.status == InviteStatus.Accepted:
                            displayStr = TTLocalizer.PartyHasStartedAcceptedInvite % TTLocalizer.GetPossesive(name)
                            self.displaySystemClickableWhisper(-1, displayStr, whisperType=WhisperPopup.WTSystem)
                        else:
                            displayStr = TTLocalizer.PartyHasStartedNotAcceptedInvite % TTLocalizer.GetPossesive(name)
                            self.setSystemMessage(partyInfo.hostId, displayStr, whisperType=WhisperPopup.WTSystem)
                break

        if not found:
            self.notify.warning("setPartyCanStart can't find partyId=% status=%d" % (partyId, newStatus))

    def announcePartyStarted(self, partyId):
        DistributedToon.partyNotify.debug('announcePartyStarted')

    def updateInvite(self, inviteKey, newStatus):
        DistributedToon.partyNotify.debug('updateInvite( inviteKey=%d, newStatus=%s )' % (inviteKey, InviteStatus(newStatus).name))
        for invite in self.invites:
            if invite.inviteKey == inviteKey:
                invite.status = newStatus
                self.updateInviteMailNotify()
                break

    def updateReply(self, partyId, inviteeId, newStatus):
        DistributedToon.partyNotify.debug('updateReply( partyId=%d, inviteeId=%d, newStatus=%s )' % (partyId, inviteeId, InviteStatus(newStatus).name))
        for partyReplyInfoBase in self.partyReplyInfoBases:
            if partyReplyInfoBase.partyId == partyId:
                for reply in partyReplyInfoBase.replies:
                    if reply.inviteeId == inviteeId:
                        reply.status = newStatus
                        break

    def filterChatString(self, chatString, fromId):
        if base.cr.getChatFilterMode() == OTPGlobals.CHAT_FILTER_WHITELIST:
            if (fromId, 1) in base.localAvatar.friendsList:
                return chatString

            if fromId in base.cr.onlineAvatars:
                handle = base.cr.onlineAvatars[fromId]
                animalType = handle.style.getType()
            else:
                animalType = self.style.getType()

            words = chatString.split(' ')
            newWords = []
            i = 0
            for word in words:
                if word == '' or (word == '.' and len(words) == 1):
                    newWords.append(word)
                elif (word.startswith(".") or word.startswith("!")) and len(word) > 1 and i == 0:
                    if base.whiteList.isWord(word[1:]):
                        newWords.append(word)
                    else:
                        if fromId == base.localAvatar.doId:
                            garbledWord = word
                        else:
                            garbledWord = self.chatGarbler.garbleSingle(animalType, word)
                        newWords.append(word[0] + '\x01WLDisplay\x01' + garbledWord + '\x02')
                elif base.whiteList.isWord(word):
                    newWords.append(word)
                else:
                    if fromId == base.localAvatar.doId:
                        garbledWord = word
                    else:
                        garbledWord = self.chatGarbler.garbleSingle(animalType, word)
                    newWords.append('\x01WLDisplay\x01' + garbledWord + '\x02')
                i += 1

            return ' '.join(newWords)
        elif base.cr.getChatFilterMode() == OTPGlobals.CHAT_FILTER_CENSOR:
            return base.profanityFilter.censor(chatString)
        else:
            return chatString

    def toonUp(self, hpGained, hasInteractivePropBonus = False):
        if self.hp == None or hpGained < 0:
            return
        oldHp = self.hp
        if self.hp + hpGained <= 0:
            self.hp += hpGained
        else:
            self.hp = min(max(self.hp, 0) + hpGained, self.maxHp)
        hpGained = self.hp - max(oldHp, 0)
        if hpGained > 0:
            self.showHpText(hpGained, hasInteractivePropBonus=hasInteractivePropBonus)
            self.hpChange(quietly=0)
        return

    def showHpText(self, number, bonus = 0, scale = 1, hasInteractivePropBonus = False):
        if self.HpTextEnabled and not self.ghostMode:
            if number != 0:
                if self.hpText:
                    self.hideHpText()
                self.HpTextGenerator.setFont(OTPGlobals.getSignFont())
                if number < 0:
                    self.HpTextGenerator.setText(str(number))
                else:
                    hpGainedStr = '+' + str(number)
                    if hasInteractivePropBonus:
                        hpGainedStr += '\n' + TTLocalizer.InteractivePropTrackBonusTerms[0]
                    self.HpTextGenerator.setText(hpGainedStr)
                self.HpTextGenerator.clearShadow()
                self.HpTextGenerator.setAlign(TextNode.ACenter)
                if bonus == 1:
                    r = 1.0
                    g = 1.0
                    b = 0
                    a = 1
                elif bonus == 2:
                    r = 1.0
                    g = 0.5
                    b = 0
                    a = 1
                elif number < 0:
                    r = 0.9
                    g = 0
                    b = 0
                    a = 1
                else:
                    r = 0
                    g = 0.9
                    b = 0
                    a = 1
                self.HpTextGenerator.setTextColor(r, g, b, a)
                self.hpTextNode = self.HpTextGenerator.generate()
                self.hpText = self.attachNewNode(self.hpTextNode)
                self.hpText.setScale(scale)
                self.hpText.setBillboardPointEye()
                self.hpText.setBin('fixed', 100)
                self.hpText.setPos(0, 0, self.height / 2)
                self.hpTextSeq = Sequence(
                        self.hpText.posInterval(1.0, Point3(0, 0, self.height + 1.5), blendType='easeOut'),
                        Wait(0.85),
                        self.hpText.colorScaleInterval(0.1, Vec4(r, g, b, 0)),
                        Func(self.hideHpText))
                self.hpTextSeq.start()

    def setAnimPlayRate(self, rate):
        if self.getTransformed():
            actor = self.getActiveTransformation()
            if hasattr(actor, 'setPlayRate'):
                actor.setPlayRate(rate, self.playingAnim)
        elif not self.getTPose():
            self.setPlayRate(rate, self.playingAnim)
        if rate == 1:
            self.forcedRate = -1
        else:
            self.forcedRate = rate

    def setName(self, name = 'unknownDistributedAvatar'):
        DistributedPlayer.DistributedPlayer.setName(self, name)
        self._handleGMName(name)

    def _handleGMName(self, name=None):
        if not name:
           name = self.name
        self.setDisplayName(name)
        if self._isGM:
            self.setGMIcon(self._gmType)
        else:
            self.removeGMIcon()
        self.setNametagStyle(self.getNametagStyle())

    def setGMIcon(self, gmType = None):
        if hasattr(self, 'gmIcon') and self.gmIcon:
            return
        if not gmType:
            gmType = self._gmType
        iconInfo = (('phase_3.5/models/gui/tt_m_gui_gm_toontroop_whistle', '**/*whistleIcon*', 'phase_3.5/maps/gamegui_palette_3clla_1.png', 4),
         ('phase_3.5/models/gui/tt_m_gui_gm_toonResistance_fist', '**/*fistIcon*', 'phase_3.5/maps/gamegui_palette_3clla_1.png', 4),
         ('phase_3.5/models/gui/tt_m_gui_gm_toontroop_getConnected', '**/*whistleIcon*', 'phase_3.5/maps/gamegui_palette_3clla_1.png', 4),
         ('phase_3.5/models/gui/tt_m_gui_gm_toontroop_whistle', '**/*whistleIcon*', 'phase_3.5/maps/gamegui_palette_3clla_2.png', 4),
         ('phase_3.5/models/gui/tt_m_gui_gm_toonResistance_fist', '**/*fistIcon*', 'phase_3.5/maps/gamegui_palette_3clla_2.png', 4),
         ('phase_3.5/models/gui/tt_m_gui_gm_toontroop_getConnected', '**/*whistleIcon*', 'phase_3.5/maps/gamegui_palette_3clla_2.png', 4),
         ('phase_3.5/models/gui/tt_m_gui_gm_toonResistance_fist', '**/*fistIcon*', 'phase_3.5/maps/gamegui_palette_3clla_3.png', 4),
         ('phase_3.5/models/gui/tt_m_gui_gm_toontroop_getConnected', '**/*whistleIcon*', 'phase_3.5/maps/gamegui_palette_3clla_3.png', 4))
        if gmType > len(iconInfo) - 1:
            return
        modelName, searchString, texture, scale = iconInfo[gmType]
        icons = loader.loadModel(modelName)
        self.gmIcon = icons.find(searchString)
        ts = self.gmIcon.findTextureStage("*")
        tex = loader.loadTexture(texture)
        self.gmIcon.setTexture(ts, tex, 1)
        self.gmIcon.setScale(scale)
        self.gmIcon.reparentTo(self.nametag.getNameIcon())
        self.setTrophyScore(self.trophyScore)
        self.gmIcon.setZ(-2.5)
        self.gmIcon.setY(0.0)
        self.gmIcon.setColor(Vec4(1.0, 1.0, 1.0, 1.0))
        self.gmIcon.setTransparency(1)
        self.gmIconInterval = LerpHprInterval(self.gmIcon, 3.0, Point3(0, 0, 0), Point3(-360, 0, 0))
        self.gmIconInterval.loop()

    def setGMPartyIcon(self):
        gmType = self._gmType
        iconInfo = (('phase_3.5/models/gui/tt_m_gui_gm_toontroop_whistle', 'phase_3.5/maps/gamegui_palette_3clla_1.png'),
        ('phase_3.5/models/gui/tt_m_gui_gm_toonResistance_fist', 'phase_3.5/maps/gamegui_palette_3clla_1.png'),
        ('phase_3.5/models/gui/tt_m_gui_gm_toontroop_getConnected', 'phase_3.5/maps/gamegui_palette_3clla_1.png'),
        ('phase_3.5/models/gui/tt_m_gui_gm_toontroop_whistle', 'phase_3.5/maps/gamegui_palette_3clla_2.png'),
        ('phase_3.5/models/gui/tt_m_gui_gm_toonResistance_fist', 'phase_3.5/maps/gamegui_palette_3clla_2.png'),
        ('phase_3.5/models/gui/tt_m_gui_gm_toontroop_getConnected', 'phase_3.5/maps/gamegui_palette_3clla_2.png'),
        ('phase_3.5/models/gui/tt_m_gui_gm_toonResistance_fist', 'phase_3.5/maps/gamegui_palette_3clla_3.png'),
        ('phase_3.5/models/gui/tt_m_gui_gm_toontroop_getConnected', 'phase_3.5/maps/gamegui_palette_3clla_3.png'))
        if gmType > len(iconInfo) - 1:
            return
        modelName, texture = iconInfo[gmType]
        self.gmIcon = loader.loadModel(modelName)
        ts = self.gmIcon.findTextureStage("*")
        tex = loader.loadTexture(texture)
        self.gmIcon.setTexture(ts, tex, 1)
        self.gmIcon.reparentTo(self.nametag.getNameIcon())
        self.gmIcon.setScale(3.25)
        self.setTrophyScore(self.trophyScore)
        self.gmIcon.setZ(1.0)
        self.gmIcon.setY(0.0)
        self.gmIcon.setColor(Vec4(1.0, 1.0, 1.0, 1.0))
        self.gmIcon.setTransparency(1)
        self.gmIconInterval = LerpHprInterval(self.gmIcon, 3.0, Point3(0, 0, 0), Point3(-360, 0, 0))
        self.gmIconInterval.loop()

    def removeGMIcon(self):
        if hasattr(self, 'gmIconInterval') and self.gmIconInterval:
            self.gmIconInterval.finish()
            del self.gmIconInterval
        if hasattr(self, 'gmIcon') and self.gmIcon:
            self.gmIcon.detachNode()
            del self.gmIcon

    def _startZombieCheck(self):
        self._zombieCheckSerialGen = SerialNumGen(random.randrange(1 << 31))
        taskMgr.doMethodLater(2.0 + 60.0 * random.random(), self._doZombieCheck, self._getZombieCheckTaskName())

    def _stopZombieCheck(self):
        taskMgr.remove(self._getZombieCheckTaskName())

    def _getZombieCheckTaskName(self):
        return self.uniqueName('zombieCheck')

    def _doZombieCheck(self, task):
        self._lastZombieContext = next(self._zombieCheckSerialGen)
        self.cr.timeManager.checkAvOnDistrict(self, self._lastZombieContext)
        taskMgr.doMethodLater(60.0, self._doZombieCheck, self._getZombieCheckTaskName())
        return task.done

    def _zombieCheckResult(self, context, present):
        if context == self._lastZombieContext:
            print('_zombieCheckResult[%s]: %s' % (self.doId, present))
            if not present:
                self.notify.warning('hiding av %s because they are not on the district!' % self.doId)
                self.setParent(OTPGlobals.SPHidden)

    def setFriendsList(self, friendsList):
        DistributedPlayer.DistributedPlayer.setFriendsList(self, friendsList)

        for friendPair in self.oldFriendsList:
            if friendPair in self.friendsList:
                continue

            if type(friendPair) == tuple:
                friendId = friendPair[0]
            else:
                friendId = friendPair

            friend = self.cr.doId2do.get(friendId)
            if not friend:
                continue

            if hasattr(base.localAvatar, 'inEstate') and base.localAvatar.inEstate:
                base.cr.estateMgr.removeFriend(self.getDoId(), friendId)

    def setImmortalMode(self, flag):
        self.immortalMode = flag

    def getImmortalMode(self):
        return self.immortalMode

    def setTempImmortalMode(self, flag):
        self.tempImmortalMode = flag

    def getTempImmortalMode(self):
        return self.tempImmortalMode

    def setUnlimitedGags(self, flag):
        self.unlimitedGags = flag

    def getUnlimitedGags(self):
        return self.unlimitedGags

    def setInstaKill(self, flag):
        self.instaKill = flag

    def getInstaKill(self):
        return self.instaKill

    def setRun(self, state, multiplier = 3.2):
        self.run = state

        if self.isLocal():
            inputState.set('debugRunning', state)
            base.debugRunningMultiplier = multiplier

    def getRun(self):
        return self.run

    def generateRainbow(self):
        intervalName = 'RainbowSeq'
        if intervalName in self.activeIntervals:
            self.destroyRainbow()
            return

        red = (1.0, 0.0, 0.0, 1.0)
        orange = (0.898, 0.420, 0.024, 1.0)
        yellow = (0.945, 0.957, 0.259, 1.0)
        green = (0.0, 1.0, 0.0, 1.0)
        blue = (0.0, 0.0, 1.0, 1.0)
        indigo = (0.247, 0.0, 1.0, 1.0)
        violet = (0.498, 0.0, 1.0, 1.0)

        rainbowSeq = Parallel()
        for node in (render, render2d, aspect2d):
            rainbowSeq.append(
                Sequence(
                    LerpColorScaleInterval(node, 0.5, red),
                    LerpColorScaleInterval(node, 0.5, orange),
                    LerpColorScaleInterval(node, 0.5, yellow),
                    LerpColorScaleInterval(node, 0.5, green),
                    LerpColorScaleInterval(node, 0.5, blue),
                    LerpColorScaleInterval(node, 0.5, indigo),
                    LerpColorScaleInterval(node, 0.5, violet)
                )
            )
        rainbowSeq.loop()
        intervalName = 'RainbowSeq'
        self.storeInterval(rainbowSeq, intervalName)

    def destroyRainbow(self):
        intervalName = 'RainbowSeq'
        self.clearInterval(intervalName)
        for node in (render, render2d, aspect2d):
            node.clearColorScale()
        if self.book.entered and base.transparentBook:
            render.setColorScale(0.5, 0.5, 0.5, 1.0)
        elif self.zoneId == ToontownGlobals.HiddenCamp:
            render.setColorScale(0.65, 0.65, 0.65, 1.0)

    def generateFanfare(self):
        from toontown.battle import Fanfare
        fanfare = Sequence(Fanfare.makeFanfare(0, self)[0])
        fanfare.start()

    def generateDropProp(self, propName: str, timestamp: float):
        intervalName = 'DropPropSeq'

        dropProp = DropPropGlobals.DropPropList[propName]
        propModel = loader.loadModel(dropProp.modelPath)
        propModel.setHpr(*dropProp.hpr)
        propModel.setZ(100)
        propModel.reparentTo(self)

        sounds = []
        audio3d = Audio3DManager.Audio3DManager(base.sfxManagerList[0], camera)
        audio3d.setDropOffFactor(0.1)
        dropSfx = audio3d.loadSfx(dropProp.dropSfxPath)
        sounds.append(dropSfx)
        audio3d.attachSoundToObject(dropSfx, propModel)
        landSfx = audio3d.loadSfx(dropProp.landSfxPath)
        sounds.append(landSfx)
        audio3d.attachSoundToObject(landSfx, propModel)
        if dropProp.extraSfxPath:
            extraSfx = audio3d.loadSfx(dropProp.extraSfxPath)
            sounds.append(extraSfx)
            audio3d.attachSoundToObject(extraSfx, propModel)
        if dropProp.fadeSfxPath:
            fadeSfx = audio3d.loadSfx(dropProp.fadeSfxPath)
            sounds.append(fadeSfx)
            audio3d.attachSoundToObject(fadeSfx, propModel)

        track = Sequence(
            Func(base.playSfx, dropSfx), 
            Parallel(
                propModel.scaleInterval(7, (dropProp.scale, dropProp.scale, dropProp.scale)),
                propModel.posInterval(7, (0, 0, 0))
            ),
            Func(self.setAnimStateWithTransitionCheck, 'Squish'), 
            Func(base.playSfx, landSfx, volume = 0.7),
        )
        if dropProp.extraSfxPath:
            track.append(Func(base.playSfx, extraSfx, 0, 0.7, 1.5))
        track.append(propModel.posInterval(0.1, (0, 0, 0.5)))
        track.append(propModel.posInterval(0.1, (0, 0, 0)))
        track.append(Wait(0.4))
        if dropProp.fadeSfxPath:
            track.append(Func(base.playSfx, fadeSfx, 0, 0.7, 1.5))
        track.append(propModel.scaleInterval(1, (0, 0, 0)))
        track.append(Func(propModel.removeNode))
        track.append(Wait(1.3))
        track.append(Func(self.setAnimStateWithTransitionCheck, 'neutral'))
        track.append(Func(self.cleanupDropPropEffect, propModel, sounds, audio3d))

        ts = globalClockDelta.localElapsedTime(timestamp)
        track.start(ts)
        self.storeInterval(track, intervalName)

    def setAnimStateWithTransitionCheck(self, state):
        if not self.getTransitioning():
            self.setAnimState(state)
    
    def cleanupDropPropEffect(self, propModel, soundList, audio3d):
        if propModel:
            propModel.removeNode()

        for sound in soundList:
            audio3d.detachSound(sound)
            if sound.status() == sound.PLAYING:
                sound.stop()

        audio3d.disable()
        del audio3d

    def cleanupDropPropIntervals(self):
        intervalName = 'DropPropSeq'
        for key in list(self.activeIntervals.keys()):
            if intervalName in key:
                self.clearInterval(key)

    def generateGreenEffect(self, character='f', toonId=0):
        intervalName = 'GreenSeq'
        # Is this Green Effect an entire Cog Department?
        cogTypes = [TTLocalizer.SellbotP.lower(), TTLocalizer.CashbotP.lower(), TTLocalizer.LawbotP.lower(), TTLocalizer.BossbotP.lower()]
        if character in cogTypes:
            cogFlyInPos = ToontownGlobals.GreenEffectMassFlyPositions
            cogList = ToontownGlobals.GreenEffectMassFlyCogs
            seq = Parallel()
            for x in range(len(cogFlyInPos)):
                cog = ToontownAvatarUtils.createCog(cogList[cogTypes.index(character)][x],
                                                    self.getX() + cogFlyInPos[x][0], self.getY() + cogFlyInPos[x][1],
                                                    self.getZ(), 0, 0, 0, parent=hidden)
                cogFlyIn = cog.beginSupaFlyMove(VBase3(self.getX() + cogFlyInPos[x][0], self.getY() + cogFlyInPos[x][1],
                                                       self.getZ()), 1, 'flyIn')
                cogSeq = Sequence(Func(cog.addActive), Func(cog.headsUp, self), Func(cog.reparentTo, render), cogFlyIn,
                               Func(cog.setChatAbsolute, TTLocalizer.GreenEffectPhase, CFSpeech | CFTimeout),
                               ActorInterval(cog, 'victory'), Func(cog.loop, 'neutral'), Wait(1),
                               Func(self.cleanupGreenEffect, cog))
                seq.append(cogSeq)
            seq.start()
            self.storeInterval(seq, intervalName)
            return
        # Is this Green Effect a copy of your own Toon?
        elif toonId == 2:
            if self.getTransformationsIndex(ToontownGlobals.TransformationCog):
                if self.disguiseType not in ToontownGlobals.PutOnSuitToonHead:
                    cog = ToontownAvatarUtils.createCog(self.suit.style.name, 0, 8, self.getZ(self), self.getH(), 0, 0,
                                                        parent=self, isSkelecog=self.suit.isSkeleton,
                                                        isWaiter=self.suit.isWaiter, isVirtual=self.suit.isVirtual,
                                                        isSkeleRevive=self.suit.isSkeleRevive,
                                                        colorType=self.nametag.getColorCode(),
                                                        level=self.cogLevels[SuitDNA.suitDepts.index(
                                                            SuitDNA.getSuitDept(self.suit.style.name))] + 1)
                    cog.wrtReparentTo(hidden)
                    cogFlyIn = cog.beginSupaFlyMove(VBase3(cog.getX(), cog.getY(), cog.getZ()), 1, 'flyIn')
                    seq = Sequence(Func(cog.addActive), Func(cog.headsUp, self), Func(cog.reparentTo, render), cogFlyIn,
                                   Func(cog.setChatAbsolute, TTLocalizer.GreenEffectPhase, CFSpeech | CFTimeout),
                                   ActorInterval(cog, 'victory'), Func(cog.loop, 'neutral'), Wait(1),
                                   Func(self.cleanupGreenEffect, cog)
                    )
                    seq.start()
                    self.storeInterval(seq, intervalName)
                    return
                else:
                    toon = ToontownAvatarUtils.createUniqueToon(self.getName(), self.style.asTuple(), self.hat,
                                                                self.glasses, self.backpack, self.shoes, 0, 8,
                                                                self.getZ(self), self.getH(), parent=self,
                                                                isDisguised=True, suitType=self.suit.style.name,
                                                                suitDept = self.suit.style.dept,
                                                                isWaiter=self.suit.isWaiter,
                                                                isRental=self.suit.isRental,
                                                                colorType=self.nametag.getColorCode(),
                                                                cogLevels=self.getCogLevels(),
                                                                cheesyEffect=self.cheesyEffect)
                    toon.wrtReparentTo(hidden)
                    cogFlyIn = toon.getSuitTeleport(moveIn=1, startPos=(toon.getX(), toon.getY(), toon.getZ()))
                    seq = Sequence(Func(toon.addActive), Func(toon.headsUp, self), Func(toon.reparentTo, render),
                                   cogFlyIn, Func(toon.setChatAbsolute, TTLocalizer.GreenEffectPhase,
                                                  CFSpeech | CFTimeout),
                                   ActorInterval(toon.suit, 'victory'), Func(toon.suit.loop, 'neutral'), Wait(1),
                                   Func(self.cleanupGreenEffect, toon, 1))
                    seq.start()
                    self.storeInterval(seq, intervalName)
                    return
            else:
                toon = ToontownAvatarUtils.createUniqueToon(self.getName(), self.style.asTuple(), self.hat,
                                                            self.glasses, self.backpack, self.shoes, 0, 5,
                                                            self.getZ(self), self.getH(), 0, 0, parent=self,
                                                            colorType=self.nametag.getColorCode(),
                                                            cheesyEffect=self.cheesyEffect,
                                                            nametagStyle=self.nametagStyle)
                toon.wrtReparentTo(hidden)
                if toon.style.getAnimal() == 'bear':
                    angryToonSFX = loader.loadSfx('phase_3.5/audio/dial/AV_bear_exclaim.ogg')
                else:
                    angryToonSFX = loader.loadSfx('phase_3.5/audio/sfx/avatar_emotion_angry.ogg')
                toonTeleportIn = Sequence(Func(toon.animFSM.request, 'TeleportIn'), Wait(1.517),
                                          Func(toon.animFSM.request, 'neutral'))
                seq = Sequence(Parallel(Func(toon.reparentTo, render), Func(toon.addActive)), Func(toon.headsUp, self),
                               toonTeleportIn, Func(toon.setChatAbsolute, OTPLocalizer.SpeedChatStaticTextToontown.get(905),
                                                    CFSpeech | CFTimeout),
                               Parallel(SoundInterval(angryToonSFX, loop=1, node=toon),
                                        Sequence(Func(toon.angryEyes), Func(toon.blinkEyes),
                                                 ActorInterval(toon, 'angry'), Func(toon.normalEyes),
                                                 Func(toon.blinkEyes), Func(toon.loop, 'neutral')), Wait(3)),
                               Func(toon.setChatAbsolute, TTLocalizer.GreenEffectPhase, CFSpeech | CFTimeout),
                               ActorInterval(toon, 'hypnotize'), Func(self.cleanupGreenEffect, toon, 1))
                seq.start()
                self.storeInterval(seq, intervalName)
                return
        # Is this Green Effect a pre-determined Toon?
        elif toonId != 0:
            toon = ToontownAvatarUtils.createToon(toonId, 0, 5, self.getZ(self), self.getH(), 0, 0,
                                                  parent=self)
            toon.wrtReparentTo(hidden)
            if toon.style.getAnimal() == 'bear':
                angryToonSFX = loader.loadSfx('phase_3.5/audio/dial/AV_bear_exclaim.ogg')
            else:
                angryToonSFX = loader.loadSfx('phase_3.5/audio/sfx/avatar_emotion_angry.ogg')
            toonTeleportIn = Sequence(Func(toon.animFSM.request, 'TeleportIn'), Wait(1.517),
                                      Func(toon.animFSM.request, 'neutral'))
            seq = Sequence(Parallel(Func(toon.reparentTo, render), Func(toon.addActive)), Func(toon.headsUp, self),
                           toonTeleportIn, Func(toon.setChatAbsolute, OTPLocalizer.SpeedChatStaticTextToontown.get(905),
                                                CFSpeech | CFTimeout),
                           Parallel(SoundInterval(angryToonSFX, loop=1, node=toon),
                                    Sequence(Func(toon.angryEyes), Func(toon.blinkEyes),
                                             ActorInterval(toon, 'angry'), Func(toon.normalEyes),
                                             Func(toon.blinkEyes), Func(toon.loop, 'neutral')), Wait(3)),
                           Func(toon.setChatAbsolute, TTLocalizer.GreenEffectPhase, CFSpeech | CFTimeout),
                           ActorInterval(toon, 'hypnotize'), Func(self.cleanupGreenEffect, toon, 1))
            seq.start()
            self.storeInterval(seq, intervalName)
            return
        # Is this Green Effect the Panda3D mascot?
        elif character == 'panda':
            panda = Actor.Actor('phase_3/models/char/panda', {'walk': 'phase_3/models/char/panda-walk'})
            panda.setBlend(frameBlend=ClientSettings.SmoothAnimations.get())
            panda.setTransparency(1)
            panda.setPosHpr(self.getX(), self.getY(), self.getZ(), self.getH() - 180, 0, 0)
            panda.setScale(0.5)
            walkNode = NodePath('Panda3DWalkNode')
            walkNode.setPosHpr(self.getX(), self.getY(), self.getZ(), self.getH() - 180, 0, 0)
            seq = Sequence(Func(panda.reparentTo, render), Func(panda.loop, 'walk'),
                             Parallel(LerpColorScaleInterval(panda, 1.0, colorScale=VBase4(1, 1, 1, 1),
                                                             startColorScale=VBase4(1, 1, 1, 0)),
                                      LerpPosInterval(panda, 5.0, (0, -25, 0), other=walkNode),
                                      Sequence(Wait(4), LerpScaleInterval(panda, 1.0, 0))),
                             Func(self.cleanupGreenEffect, panda, 2))
            seq.start()
            self.storeInterval(seq, intervalName)
            return
        # This Green Effect must be a single Cog.
        else:
            cog = ToontownAvatarUtils.createCog(character, 0, 8, self.getZ(self), self.getH(), 0, 0, parent=self)
            cog.wrtReparentTo(hidden)
            cogFlyIn = cog.beginSupaFlyMove(VBase3(cog.getX(), cog.getY(), cog.getZ()), 1, 'flyIn')
            seq = Sequence(Func(cog.addActive), Func(cog.headsUp, self), Func(cog.reparentTo, render), cogFlyIn,
                           Func(cog.setChatAbsolute, TTLocalizer.GreenEffectPhase, CFSpeech | CFTimeout),
                           ActorInterval(cog, 'victory'), Func(cog.loop, 'neutral'), Wait(1),
                           Func(self.cleanupGreenEffect, cog))
            seq.start()
            self.storeInterval(seq, intervalName)
            return

    def cleanupGreenEffect(self, character, type=0):
        if character:

            def removeActiveIfAble():
                if hasattr(character, 'removeActive'):
                    character.removeActive()
                character.delete()

            def getIvalBasedOnCharType():
                if type == 0:
                    ival = character.beginSupaFlyMove(VBase3(character.getX(), character.getY(),
                                                             character.getZ()), 0, 'flyOut')
                elif type == 1:
                    if character.getTransformationsIndex(ToontownGlobals.TransformationCog):
                        if self.disguiseType != 0 and self.disguiseType != 5 and self.disguiseType != 9:
                            ival = character.beginSupaFlyMove(VBase3(character.getX(), character.getY(),
                                                                     character.getZ()), 0, 'flyOut')
                        else:
                            ival = character.getSuitTeleport(moveIn=0)
                    else:
                        ival = Sequence(Func(character.animFSM.request, 'TeleportOut'),
                                        Wait(character.getDuration('teleport') + 1.0),
                                        Func(character.stopBlink))
                else:
                    ival = Sequence()
                return ival
            seq = Sequence(getIvalBasedOnCharType(), Func(character.reparentTo, hidden), Func(removeActiveIfAble))
            seq.start()

    def cleanupGreenEffectIntervals(self):
        intervalName = 'GreenSeq'
        for key in list(self.activeIntervals.keys()):
            if intervalName in key:
                self.clearInterval(key)

    def generateSnapEffect(self):
        from toontown.battle import BattleParticles
        from toontown.battle import MovieSuitAttacks
        headEffect = BattleParticles.createParticleEffect('RubOut', color=(0, 0, 0, 1))
        torsoEffect = BattleParticles.createParticleEffect('RubOut', color=(0, 0, 0, 1))
        legsEffect = BattleParticles.createParticleEffect('RubOut', color=(0, 0, 0, 1))
        animal = self.style.getAnimal()
        bodyScale = ToontownGlobals.toonBodyScales[animal]

        def toonFacePoint(toon, zOffset=0, parent=render):
            pnt = toon.getPos(parent)
            pnt.setZ(pnt[2] + toon.shoulderHeight + 0.3 + zOffset)
            return Point3(pnt)

        headEffectHeight = toonFacePoint(self).getZ()
        legsHeight = ToontownGlobals.legHeightDict[self.style.legs] * bodyScale
        torsoEffectHeight = ToontownGlobals.torsoHeightDict[self.style.torso] * bodyScale / 2 + legsHeight
        legsEffectHeight = legsHeight / 2
        effectX = headEffect.getX()
        effectY = headEffect.getY()
        headEffect.setPos(effectX, effectY - 1.5, headEffectHeight)
        torsoEffect.setPos(effectX, effectY - 1, torsoEffectHeight)
        legsEffect.setPos(effectX, effectY - 0.6, legsEffectHeight)
        headParts = self.getHeadParts()
        torsoParts = self.getTorsoParts()
        legsParts = self.getLegsParts()
        headTrack = MovieSuitAttacks.getPartTrack(headEffect, 0, 2.0, [headEffect, self, 0])
        torsoTrack = MovieSuitAttacks.getPartTrack(torsoEffect, 0, 2.0, [torsoEffect, self, 0])
        legsTrack = MovieSuitAttacks.getPartTrack(legsEffect, 0, 2.0, [legsEffect, self, 0])

        def hideParts(parts):
            track = Parallel()
            for partNum in range(0, parts.getNumPaths()):
                nextPart = parts.getPath(partNum)
                track.append(Func(nextPart.setTransparency, 1))
                track.append(LerpFunctionInterval(nextPart.setAlphaScale, fromData=1, toData=0, duration=2.0))

            return track

        def showParts(parts):
            track = Sequence()
            for partNum in range(0, parts.getNumPaths()):
                nextPart = parts.getPath(partNum)
                track.append(LerpFunctionInterval(nextPart.setAlphaScale, fromData=0, toData=1, duration=2.0))
                track.append(Func(nextPart.clearTransparency))

            return track

        snap = Sequence(
            Wait(2.5),
            Parallel(
                hideParts(headParts), hideParts(torsoParts), hideParts(legsParts), headTrack, torsoTrack, legsTrack
            ),
            Wait(2),
            Parallel(showParts(headParts), showParts(torsoParts), showParts(legsParts))
        )
        snap.start()

    def generateOboeEffect(self):
        oboe = base.loader.loadSfx('phase_14.5/audio/sfx/oboe.ogg')
        base.playSfx(oboe, node=self)

    def generateScavengerEffect(self, amount: int):
        if self.isLocal():
            self.effect = ScavengerHuntEffect(amount, self.getJarPos())
            self.effect.play()

    def getJarPos(self):
        if hasattr(self.effect, 'npRoot'):
            jarEndPos = self.jarEndPos + 0.3
            self.jarEndPos = jarEndPos
        else:
            self.jarEndPos = 0.5

        if not base.taskMgr.hasTaskNamed('resetEffect'):
            self.doMethodLater(8, self.resetEffect, 'resetEffect')
        return self.jarEndPos

    def resetEffect(self, task):
        self.effect = None
        self.removeTask('resetEffect')

    def generateCage(self, doAnim=True):
        if self.getLocked():
            # This is a node we reparent both the cage and the player's camera to
            self.cage = self.attachNewNode('cage')
            self.cage.setZ(100)
            self.cage.wrtReparentTo(render)

            # Load the cage model
            model = loader.loadModel('phase_14.5/models/props/cage')
            model.setScale(0.01)
            model.reparentTo(self.cage)

            # Only do camera things if we're the toon being caged
            if self.isLocal():
                messenger.send('toon-caged')
                base.localAvatar.deactivateCamera()
                base.camera.reparentTo(self.cage)
                base.camera.setPosHpr(7.5, 15, 4, 150, 0, 0)
            # If we aren't the toon being caged, ignore collisions of the cage model
            else:
                collisions = model.findAllMatches('**/+CollisionNode')
                if collisions:
                    for coll in collisions:
                        coll.stash()

            # The caged Toon must be forced to LOD 1000
            self.useLOD(1000)

            # Setup an animation for the cage dropping
            if doAnim:
                dropSfx = loader.loadSfx('phase_5/audio/sfx/cogbldg_drop.ogg')
                dropSfx.setPlayRate(2)
                landSfx = loader.loadSfx('phase_5/audio/sfx/AA_drop_bigweight.ogg')

                ival = Sequence(Func(self.setAnimState, 'neutral'), Func(base.playSfx, dropSfx),
                                Parallel(model.scaleInterval(3.5, (0.2, 0.2, 0.2)),
                                         self.cage.posInterval(3.5, (self.getX(), self.getY(), self.getZ()))),
                                Func(self.setZ, self.getZ() + 1), Func(base.playSfx, landSfx), Wait(2.0),
                                Func(landSfx.stop))
            # The cage is already there, so show it as such
            else:
                model.setScale(0.2, 0.2, 0.2)
                self.cage.reparentTo(self)
                self.cage.setZ(-1)
                ival = None
        else:
            if self.isLocal():
                base.camera.reparentTo(base.localAvatar)
                base.localAvatar.activateCamera()

            self.resetLOD()

            if not self.cage:
                return

            kapow = globalPropPool.getProp('kapow')
            kapow.setBillboardPointWorld(2)
            kapow.setScale(0.75)
            kapow.setZ(2)
            kapow.reparentTo(self.cage)

            boomSfx = loader.loadSfx('phase_3.5/audio/sfx/ENC_cogfall_apart.ogg')
            ival = Parallel(Parallel(SoundInterval(boomSfx, node=kapow, volume=1), ActorInterval(kapow, 'kapow')),
                            Sequence(Wait(0.75), Func(kapow.delete), Func(self.cage.removeNode)))
        if ival:
            ival.start()
            self.storeInterval(ival, 'ival')

    def setLocked(self, locked, exemption=0):
        self.locked = locked

        # Just change the value of the main flag and do nothing else
        if exemption == ToontownGlobals.LockedStateFlagChangeOnly:
            return

        if not self.isLocal():
            if locked and not self.isGenerated() and exemption != ToontownGlobals.LockedStateCagedExemption:
                self.generateCage(False)
            return

        if self.isGenerated():
            if locked:
                if exemption not in (ToontownGlobals.LockedStateAvatarControlsExemption, ToontownGlobals.LockedStateDualExemption):
                    self.disableAvatarControls()
                self.collisionsOff()
                self.setPreventSleepWatch(True)
                self.hideClarabelleGui()
                self.laffMeter.hide()
                self.book.hideButton()
                self.ignoreOnscreenHooks()
                #base.disableToggleHotkeys()
                base.localAvatar.setTeleportAvailable(0)
                base.localAvatar.setTeleportAllowed(0)
                base.localAvatar.endAllowPies()
                place = base.cr.playGame.getPlace()
                if place:
                    place.walkStateData.toggleBook('disable')
                if not exemption:
                    self.kartActive = False
            else:
                self.collisionsOn()
                if exemption not in (ToontownGlobals.LockedStateAvatarControlsExemption, ToontownGlobals.LockedStateDualExemption):
                    self.enableAvatarControls()
                self.setPreventSleepWatch(False)
                self.refreshOnscreenButtons()
                self.laffMeter.show()
                self.book.showButton()
                self.acceptOnscreenHooks()
                #base.enableToggleHotkeys()
                base.localAvatar.setTeleportAvailable(1)
                base.localAvatar.setTeleportAllowed(1)
                base.localAvatar.beginAllowPies()
                place = base.cr.playGame.getPlace()
                if place:
                    place.walkStateData.toggleBook('enable')

                    if not exemption:
                        fsm = place.fsm
                        if fsm:
                            # ClassicFSM doesn't have a demand method
                            # but it does have forceTransition
                            if isinstance(fsm, ClassicFSM.ClassicFSM):
                                cmd = fsm.forceTransition
                            else:
                                cmd = fsm.demand
                            if fsm.hasStateNamed('finalBattle'):
                                cmd('finalBattle')
                            elif fsm.hasStateNamed('walk'):
                                if place.getState() == 'stopped':
                                    cmd('walk')
                            else:
                                self.notify.warning('skipping demand to walk in %s' % place)
                        else:
                            self.notify.warning('no fsm for place %s; skipping demand to walk' % place)

    def getLocked(self):
        return self.locked

    def setMuted(self, muted, minutes):
        self.muted = muted
        if self.isLocal():
            base.localAvatar.chatMgr.chatInputWhiteList.toggleMute(muted)

    def getMuted(self):
        return self.muted

    def setTransitioning(self, transitioning):
        self.transitioning = transitioning

    def getTransitioning(self):
        return self.transitioning

    def playSound(self, sound, loop=0):
        soundWithExt = sound + '.ogg'
        bgmPhases = [3, 3.5, 4, 5.5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 14.5]
        dialPhases = [3, 3.5, 4, 5.5, 6, 8]
        sfxPhases = [3, 3.5, 4, 5, 5.5, 6, 8, 9, 10, 11, 12, 13, 14, 14.5]

        bgmSearchPath = DSearchPath()
        for phase in bgmPhases:
            bgmSearchPath.appendDirectory('/phase_' + str(phase) + '/audio/bgm')
        dialSearchPath = DSearchPath()
        for phase in dialPhases:
            dialSearchPath.appendDirectory('/phase_' + str(phase) + '/audio/dial')
        sfxSearchPath = DSearchPath()
        for phase in sfxPhases:
            sfxSearchPath.appendDirectory('/phase_' + str(phase) + '/audio/sfx')

        filename = Filename(soundWithExt)
        found = vfs.resolveFilename(filename, bgmSearchPath)
        if found:
            music = base.loader.loadMusic(filename.getFullpath())
            base.playMusic(music, looping=loop, volume=0.8)
            if not music.getLoop():
                taskMgr.doMethodLater(music.length() + 1, self.playZoneMusic, self.taskName('play-zone-music'))
        else:
            found = vfs.resolveFilename(filename, dialSearchPath)
            if not found:
                found = vfs.resolveFilename(filename, sfxSearchPath)
            if not found:
                self.notify.warning('%s not found on:' % soundWithExt)
                print(bgmSearchPath)
                print(dialSearchPath)
                print(sfxSearchPath)
            else:
                sfx = base.loader.loadSfx(filename.getFullpath())
                base.playSfx(sfx, looping=loop, volume=0.8)

    def playZoneMusic(self, task):
        place = base.cr.playGame.getPlace()
        if place:
            base.playMusic(place.loader.music, looping=1, volume=0.8)
        return task.done

    def doTeleport(self, hood):
        if hood == 'gui' and self.isLocal():
            self.openTeleportGUI()
            return

        place = base.cr.playGame.getPlace()
        if place:
            place.doTeleport(hood)

    def setToonScale(self, scale):
        previousScale = self.toonScale
        self.toonScale = scale
        scaleTime = abs(previousScale - scale) / 2

        ival = self._Toon__doToonScale(scale, scaleTime)
        if self.isLocal():
            ival.append(Sequence(Func(self.initCameraPositions), Func(self.resetCameraPosition)))
        ival.start()

    def setKartActive(self, kartActive):
        self.kartActive = kartActive

        if self.isGenerated():
            self.updateKartActive()

    def getKartActive(self):
        return self.kartActive

    def canRaceHere(self):
        hp = self.getHp()
        if hp and hp <= 10:
            return False

        place = base.cr.playGame.place

        if not place:
            return False

        if base.cr.buildLot:
            return True

        from toontown.safezone.Playground import Playground
        from toontown.town.Street import Street
        from toontown.coghq.CogHQExterior import CogHQExterior
        from toontown.coghq.FactoryExterior import FactoryExterior
        from toontown.coghq.LawbotOfficeExterior import LawbotOfficeExterior

        return isinstance(
            place,
            (Playground, CogHQExterior, Street, FactoryExterior, LawbotOfficeExterior)
        )

    def updateKartActive(self):
        if self.kartActive:
            if (not self.kartInterest) and self.canRaceHere():
                self.getDustCloud(0.0, scale=0.8).start()
                self.kartInterest = base.cr.addInterest(self.doId, [100], 'kart-%d' % self.doId)
        else:
            if self.kartInterest:
                if self.isGenerated():
                    self.getDustCloud(0.0, scale=0.8).start()

                    # Exit car mode
                    if self.isLocal() and self.magicMenu.mode == ToontownGlobals.MagicMenuMountKart:
                        self.magicMenu.exitKartMode()
                        self.magicMenu.exit()

                base.cr.removeInterest(self.kartInterest)

            self.kartInterest = None

    def setLoop(self, anim, start, end, part):
        if self.getActiveTransformationIndex() == ToontownGlobals.TransformationProp:
            return
        start = start if start != -1 else None
        end = end if end != -1 else None
        part = part if part else None
        if self.getTransformed() or self.getTPose():
            geom = self.getActiveTransformation()
            geom.loop(anim, fromFrame=start, toFrame=end, partName=part)
        else:
            self.loop(anim, fromFrame = start, toFrame = end, partName = part)

    def setPingPong(self, anim, start, end, part):
        if self.getActiveTransformationIndex() == ToontownGlobals.TransformationProp:
            return
        start = start if start != -1 else None
        end = end if end != -1 else None
        part = part if part else None
        if self.getTransformed() or self.getTPose():
            geom = self.getActiveTransformation()
            geom.pingpong(anim, fromFrame=start, toFrame=end, partName=part)
        else:
            self.pingpong(anim, fromFrame = start, toFrame = end, partName = part)

    def setPose(self, anim, frame, part):
        if self.getActiveTransformationIndex() == ToontownGlobals.TransformationProp:
            return
        part = part if part else None
        if self.getTransformed() or self.getTPose():
            geom = self.getActiveTransformation()
            geom.pose(anim, frame, part)
        else:
            self.pose(anim, frame, part)

    def storeInterval(self, interval, name):
        if name in self.activeIntervals:
            name = name + str(len(list(self.activeIntervals.keys())))
        self.activeIntervals[name] = interval

    def cleanupIntervals(self):
        for interval in list(self.activeIntervals.values()):
            interval.finish()
            DelayDelete.cleanupDelayDeletes(interval)

        self.activeIntervals = {}

    def clearInterval(self, name, finish = 1):
        if name in self.activeIntervals:
            ival = self.activeIntervals[name]
            if finish:
                ival.finish()
            else:
                ival.pause()
            if name in self.activeIntervals:
                DelayDelete.cleanupDelayDeletes(ival)
                del self.activeIntervals[name]
        else:
            self.notify.debug('interval: %s already cleared' % name)

    def finishInterval(self, name):
        if name in self.activeIntervals:
            interval = self.activeIntervals[name]
            interval.finish()

    def displayMessage(self, message):
        self.messageDoneEvent = self.uniqueName('messageDoneEvent')
        self.acceptOnce(self.messageDoneEvent, self.__handleMessageDone)
        self.messageGui = TTDialog.TTGlobalDialog(doneEvent=self.messageDoneEvent, message=message, style=TTDialog.Acknowledge)

    def __handleMessageDone(self):
        self.ignore(self.messageDoneEvent)
        self.messageGui.cleanup()
        self.messageGui = None

    def setEpisodeStatuses(self, episodeStatuses):
        self.notify.debug("setEpisodeStatuses({}): Acquired episode statuses from UD: {}".format(
            self.getDoId(),
            episodeStatuses
        ))
        for episodeData in episodeStatuses:
            episodeName = EpisodeId2Name.get(episodeData[0])
            episodeCompleted = True if episodeData[1] else False
            if episodeName in self.__episodeStatuses:
                self.__episodeStatuses[episodeName] = episodeCompleted
                self.notify.debug("setEpisodeStatuses({}): Set \"{}\" completion to {}".format(
                    self.getDoId(),
                    episodeName,
                    episodeCompleted
                ))
            else:
                self.notify.warning("setEpisodeStatuses({}): Failed to set episode status for ID {}".format(
                    self.getDoId(),
                    episodeData[0]
                ))

    def isEpisodeComplete(self, episodeName):
        return self.__episodeStatuses.get(episodeName, False)

    def setCustomIcon(self, modelPath=None, texturePath=None, text=None, x=0, y=0, z=0, scale=1):
        self.removeCustomIcon()
        if modelPath:
            self.customIcon = loader.loadModel(modelPath)
        else:
            self.customIcon = NodePath(self.uniqueName('customIcon'))

        # Set a texture for our custom icon
        if texturePath:
            # For loading RGB files
            if isinstance(texturePath, (list, tuple)):
                texture = loader.loadTexture(texturePath[0], texturePath[1])
            else:
                texture = loader.loadTexture(texturePath)

            if isinstance(self.customIcon, NodePath):
                texture = OnscreenImage(texture)
                texture.setTransparency(1)
                texture.reparentTo(self.customIcon)
            else:
                self.customIcon.setTexture(texture)
                self.customIcon.setTransparency(1)

        # If we have no model or texture, but we do have text, make a label to put above us
        if not modelPath and not texturePath and text:
            label = DirectLabel(parent=self.customIcon, relief=None, text=text, text_scale=1.5, text_font=ToontownGlobals.getSignFont(), text_fg=Vec4(1, 1, 1, 1))

        # Reparent our custom icon to the nametag
        self.customIcon.reparentTo(self.nametag.getNameIcon())
        self.customIcon.setPos(x, y, z)
        self.customIcon.setScale(scale)

        # Update trophy score so that its position re-adjusts accoring to our custom icon
        self.setTrophyScore(self.trophyScore)

    def removeCustomIcon(self):
        if hasattr(self, 'customIcon') and self.customIcon:
            self.customIcon.removeNode()
            del self.customIcon

    def findBoss(self, dept=None):
        dept2Boss = {'s': DistributedSellbotBoss,
                     'm': DistributedCashbotBoss,
                     'l': DistributedLawbotBoss,
                     'c': DistributedBossbotBoss}

        bossObj = None
        if dept:
            bossClass = dept2Boss.get(dept)
            for do in list(base.cr.doId2do.values()):
                if isinstance(do, bossClass):
                    if self.doId in do.involvedToons:
                        bossObj = do
                        break
        else:
            bossClasses = list(dept2Boss.values())
            for do in list(base.cr.doId2do.values()):
                for bossClass in bossClasses:
                    if isinstance(do, bossClass):
                        if self.doId in do.involvedToons:
                            bossObj = do
                            break
                else:
                    continue
                break

        return bossObj

    def removeNotificationsMatching(self, idStr):
        if hasattr(base.localAvatar, 'notifications'):
            base.localAvatar.notifications.removeNotificationsMatching(idStr)

    def setProfilePose(self, profilePose: int):
        self.profilePose = profilePose

    def getProfilePose(self) -> int:
        return self.profilePose

    def setProfilePoses(self, profilePoses: List[int]):
        self.profilePoses = profilePoses

    def getProfilePoses(self) -> List[int]:
        return self.profilePoses

    def setProfileBackground(self, profileBackground: int):
        self.profileBackground = profileBackground

    def getProfileBackground(self) -> int:
        return self.profileBackground

    def setProfileBackgrounds(self, profileBackgrounds: List[int]):
        self.profileBackgrounds = profileBackgrounds

    def getProfileBackgrounds(self) -> List[int]:
        return self.profileBackgrounds

    def setNextKnockKnockHeal(self, nextKnockKnockHeal):
        self.nextKnockKnockHeal = nextKnockKnockHeal

    def getNextKnockKnockHeal(self) -> int:
        return self.nextKnockKnockHeal
