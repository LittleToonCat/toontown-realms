import sys
import time, json, os, functools
from datetime import datetime
from typing import Dict, List

from direct.directnotify import DirectNotifyGlobal
from direct.distributed.PyDatagram import *
from direct.task import Task
from panda3d.core import *
from panda3d.toontown import *

from panda3d.toontown import WhisperPopup

from otp.ai.AIZoneData import AIZoneDataStore
from otp.ai.TimeManagerAI import TimeManagerAI
from otp.distributed.OtpDoGlobals import *
from otp.distributed import CentralLoggerAI
from otp.friends.FriendManagerAI import FriendManagerAI
from otp.avatar.DistributedPlayerAI import DistributedPlayerAI
from otp.otpbase import OTPGlobals

from toontown.ai.DistributedAccessoryEffectMgrAI import DistributedAccessoryEffectMgrAI
from toontown.ai.DistributedPolarPlaceEffectMgrAI import DistributedPolarPlaceEffectMgrAI
from toontown.ai.DistributedResistanceEmoteMgrAI import DistributedResistanceEmoteMgrAI
from toontown.ai.DistributedMagicCatEffectMgrAI import DistributedMagicCatEffectMgrAI
from toontown.ai.HolidayManagerAI import HolidayManagerAI
from toontown.ai.NewsManagerAI import NewsManagerAI
from toontown.ai.MicroGameManagerAI import MicroGameManagerAI
from toontown.ai.BossPartyManagerAI import BossPartyManagerAI
from toontown.building.DistributedTrophyMgrAI import DistributedTrophyMgrAI
from toontown.catalog.CatalogManagerAI import CatalogManagerAI
from toontown.chat.ToontownOfflineChatManagerAI import ToontownOfflineChatManagerAI
from toontown.coghq.CogSuitManagerAI import CogSuitManagerAI
from toontown.coghq.CountryClubManagerAI import CountryClubManagerAI
from toontown.coghq.FactoryManagerAI import FactoryManagerAI
from toontown.coghq.LawOfficeManagerAI import LawOfficeManagerAI
from toontown.coghq.MintManagerAI import MintManagerAI
from toontown.coghq.PromotionManagerAI import PromotionManagerAI
from toontown.distributed.ToontownDistrictAI import ToontownDistrictAI
from toontown.distributed.ToontownInternalRepository import ToontownInternalRepository
from toontown.effects.FireworkManagerAI import FireworkManagerAI
from toontown.estate.EstateManagerAI import EstateManagerAI
from toontown.estate.DistributedBankMgrAI import DistributedBankMgrAI
from toontown.fishing.FishManagerAI import FishManagerAI
from toontown.fishing.FishPokerManagerAI import FishPokerManagerAI
from toontown.hood import ZoneUtil
from toontown.hood.BRHoodDataAI import BRHoodDataAI
from toontown.hood.BossbotHQDataAI import BossbotHQDataAI
from toontown.hood.CSHoodDataAI import CSHoodDataAI
from toontown.hood.CashbotHQDataAI import CashbotHQDataAI
from toontown.hood.DDHoodDataAI import DDHoodDataAI
from toontown.hood.DGHoodDataAI import DGHoodDataAI
from toontown.hood.DLHoodDataAI import DLHoodDataAI
from toontown.hood.GSHoodDataAI import GSHoodDataAI
from toontown.hood.GZHoodDataAI import GZHoodDataAI
from toontown.hood.LawbotHQDataAI import LawbotHQDataAI
from toontown.hood.MMHoodDataAI import MMHoodDataAI
from toontown.hood.OZHoodDataAI import OZHoodDataAI
from toontown.hood.TTHoodDataAI import TTHoodDataAI
from toontown.hood.TTBetaHoodDataAI import TTBetaHoodDataAI
from toontown.hood.DGBetaHoodDataAI import DGBetaHoodDataAI
from toontown.hood.MMBetaHoodDataAI import MMBetaHoodDataAI
from toontown.hood.DLBetaHoodDataAI import DLBetaHoodDataAI
from toontown.hood.BRBetaHoodDataAI import BRBetaHoodDataAI
from toontown.hood.DDBetaHoodDataAI import DDBetaHoodDataAI
from toontown.hood.CFHoodDataAI import CFHoodDataAI
from toontown.hood.TLFFHoodDataAI import TLFFHoodDataAI
from toontown.parties.ToontownTimeManager import ToontownTimeManager
from toontown.pets.PetManagerAI import PetManagerAI
from toontown.quest.QuestManagerAI import QuestManagerAI
from toontown.racing import RaceGlobals
from toontown.racing.DistributedLeaderBoardAI import DistributedLeaderBoardAI
from toontown.racing.DistributedRacePadAI import DistributedRacePadAI
from toontown.racing.DistributedStartingBlockAI import DistributedStartingBlockAI, DistributedViewingBlockAI
from toontown.racing.DistributedViewPadAI import DistributedViewPadAI
from toontown.racing.RaceManagerAI import RaceManagerAI
from toontown.safezone.DistributedPartyGateAI import DistributedPartyGateAI
from toontown.safezone.SafeZoneManagerAI import SafeZoneManagerAI
from toontown.safezone.PetParkManagerAI import PetParkManagerAI
from toontown.shtiker.CogPageManagerAI import CogPageManagerAI
from toontown.spellbook.ToontownRealmsMagicWordManagerAI import ToontownRealmsMagicWordManagerAI
from toontown.suit.SuitInvasionManagerAI import SuitInvasionManagerAI
from toontown.social.SocialGlobals import VisibilityTypes
from toontown.toon import NPCToons
from toontown.toonbase import ToontownGlobals, TTLocalizer, ServerSettings
from toontown.tutorial.TutorialManagerAI import TutorialManagerAI
from toontown.uberdog.DistributedInGameNewsMgrAI import DistributedInGameNewsMgrAI
from toontown.uberdog.DistributedPartyManagerAI import DistributedPartyManagerAI
from toontown.uberdog.ModdingManagerAI import ModdingManagerAI
from toontown.uberdog.DiscordManagerAI import DiscordManagerAI
from toontown.uberdog.EpisodeManagerAI import EpisodeManagerAI
from toontown.coderedemption.TTCodeRedemptionMgrAI import TTCodeRedemptionMgrAI
from toontown.parties.CalendarBackup import PartyBackup
from toontown.time.TimeUtil import EpochTime
from toontown.fishing import DistributedFishingPondAI
from toontown.safezone import DistributedFishingSpotAI
from toontown.classicfishing import DistributedClassicFishingSpotAI
from toontown.datapack import DataPackManagerAI
from toontown.sandbox.DistributedBuildLotManagerAI import DistributedBuildLotManagerAI


class ToontownAIRepository(ToontownInternalRepository):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownAIRepository')
    apinotify = DirectNotifyGlobal.directNotify.newCategory('MiniserverAPI')
    logMessages = []

    def __init__(self, baseChannel, serverId):
        ToontownInternalRepository.__init__(self, baseChannel, serverId, dcSuffix='AI')

        self.districtName = ServerSettings.ServerDisplayName.get()

        self.districtLimit = ServerSettings.MaxPlayers.get()

        self.districtDescription = ServerSettings.ServerDescription.get()
        self.districtPublic = ServerSettings.ShowInPublicServerBrowser.get()
        self.districtPublicPort = ServerSettings.ServerPort.get()
        self.districtIcon = ServerSettings.ServerIconURL.get()

        self.legitMode = ServerSettings.LegitMode.get()
        self.nerfsMode = ServerSettings.NerfsMode.get()
        self.propGenerator = ServerSettings.PropGenerator.get() if not self.legitMode else False
        self.classicFishing = ServerSettings.ClassicFishingDocks.get() if not self.legitMode else False
        self.disneyCharacters = ServerSettings.PlaygroundDisneyCharacters.get()
        self.jukebox = ServerSettings.ToontownCentralJukebox.get() if not self.legitMode else False
        self.classicAnimatedPropFaceoff = ServerSettings.ClassicAnimatedPropFaceOffDuration.get() if not self.legitMode else True

        self.onlineAvatars = {}

        self.doLiveUpdates = self.config.GetBool('want-live-updates', True)
        self.wantCogdominiums = ServerSettings.SpawnFieldOffices.get()
        self.wantEmblems = self.config.GetBool('want-emblems', False)
        self.useAllMinigames = self.config.GetBool('want-all-minigames', True)
        self.wantMicroGames = self.config.GetBool('want-micro-games', True)
        self.wantBossParties = ServerSettings.BossParties.get()
        self.wantFishPoker = self.config.GetBool('want-fish-poker', True)
        self.wantGlobalChat = ServerSettings.GlobalChat.get()
        self.districtId = None
        self.district = None
        self.districtStats = None
        self.districtFull = False
        self.timeManager = None
        self.newsManager = None
        self.holidayManager = None
        self.catalogManager = None
        self.zoneDataStore = None
        self.inGameNewsMgr = None
        self.trophyMgr = None
        self.petMgr = None
        self.dnaStoreMap = {}
        self.dnaDataMap = {}
        self.zoneTable = {}

        self.hoods = []
        self.buildingManagers = {}
        self.suitPlanners = {}

        # Guard for publish
        if simbase.wantBingo:
            self.bingoMgr = None

        self.suitInvasionManager = None
        self.zoneAllocator = None
        self.zoneId2owner = {}
        self.questManager = None
        self.cogPageManager = None
        self.fireworkManager = None
        self.fishManager = None
        self.fishBingoManager = None
        self.fishPokerManager = None
        self.factoryMgr = None
        self.mintMgr = None
        self.lawMgr = None
        self.countryClubMgr = None
        self.promotionMgr = None
        self.cogSuitMgr = None
        self.partyManager = None
        self.safeZoneManager = None
        self.raceMgr = None
        self.polarPlaceEffectMgr = None
        self.resistanceEmoteMgr = None
        self.magicCatEffectMgr = None
        self.aviatorEffectMgr = None
        self.tutorialManager = None
        self.friendManager = None
        self.chatManager = None
        self.toontownTimeManager = None
        self.estateMgr = None
        self.petParkMgr = None
        self.magicWordManager = None
        self.deliveryManager = None
        self.cogSuitMessageSent = False
        self.propGenerators = {}
        self.propGeneratorsLocked = False
        self.moddingManager = None
        self.discordManager = None
        self.episodeManager = None
        self.codeRedemptionManager = None
        self.microGameMgr = None
        self.bossPartyMgr = None
        self.buildLotMgr: DistributedBuildLotManagerAI = None
        self.websiteUrl = "https://toontownrealms.com/"
        self.websiteChannel = None
        self.websiteRequestNum = 0
        self.grabbedIp = -1
        self.partyBackups = None  # this is basically for calendars, for archived parties
        self.time = None  # simplifies datetime/epoch timestamp things
        self.gamemode = int(os.getenv('TTOFF_GAME_MODE', OTPGlobals.ModeOffline))
        self.centralLogger = None
        self.datapackMgr = None

        # We may want to force or disable some Mini-Server settings based on our gamemode.
        self.adjustSettingsBasedOnGamemode()

    def handleConnected(self):
        ToontownInternalRepository.handleConnected(self)
        self.notify.info(f'== Starting Miniserver "{self.districtName}"... ==')

        # Generate our district...
        self.districtId = self.allocateChannel()
        self.notify.info('Creating district (%d)...' % self.districtId)
        self.district = ToontownDistrictAI(self)
        self.district.setName(self.districtName)
        self.district.setDescription(self.districtDescription)
        self.district.setTimestamp(json.dumps(time.time()))
        self.district.setLegitMode(self.legitMode)
        self.district.setNerfsMode(self.nerfsMode)
        self.district.setClassicFishing(self.classicFishing)
        self.district.setCustomWhitelist([])
        self.district.setGlobalChat(ServerSettings.GlobalChat.get())
        self.district.setWhitelistMode(ServerSettings.ChatFilterMode.get())
        self.district.setPropFaceoffTime(self.classicAnimatedPropFaceoff)
        self.district.setSelfToonUp(ServerSettings.SelfToonUp.get())
        self.district.setPopulationLimit(self.districtLimit)
        self.district.setExperimentalFeatures(ServerSettings.ExperimentalFeatures.get())
        self.district.generateWithRequiredAndId(self.districtId, self.getGameDoId(), OTP_ZONE_ID_DISTRICTS)
        self.district.b_setIconPath(self.districtIcon)

        # Claim ownership of that district...
        self.notify.info(f'Claiming ownership of district ({self.districtId})...')
        datagram = PyDatagram()
        datagram.addServerHeader(self.districtId, self.ourChannel, STATESERVER_OBJECT_SET_AI)
        datagram.addChannel(self.ourChannel)
        self.send(datagram)

        # Create our local objects.
        self.notify.info('Creating local objects...')
        self.createLocals()

        # Create our global objects.
        self.notify.info('Creating global objects...')
        self.createGlobals()

        # Create our zones.
        self.notify.info('Creating zones (Playgrounds and Cog HQs)...')
        self.createZones()

        # Make our district available, and we're done.
        self.notify.info('Making district available...')
        self.district.b_setAvailable(1)
        self.notify.info('District is now ready. Have fun in Toontown Realms!')

        # Accept change of gamemode from UD.
        self.netMessenger.accept('SetGamemode', self, self.setGamemode)

        if ServerSettings.LoggingEndpoint.get():
            self.doMethodLater(25, self.postLogs, name = 'loggpost')

    def getTrackClsends(self):
        return False

    def createLocals(self):
        """
        Creates "local" objects.
        """

        # Create our holiday manager...
        self.holidayManager = HolidayManagerAI(self)

        # Create our zone data store...
        self.zoneDataStore = AIZoneDataStore()

        # Create our pet manager...
        self.petMgr = PetManagerAI(self)

        # Create our suit invasion manager...
        self.suitInvasionManager = SuitInvasionManagerAI(self)

        # Create our zone allocator...
        self.zoneAllocator = UniqueIdAllocator(ToontownGlobals.DynamicZonesBegin, ToontownGlobals.DynamicZonesEnd)

        # Create our quest manager...
        self.questManager = QuestManagerAI(self)

        # Create our Cog page manager...
        self.cogPageManager = CogPageManagerAI(self)

        # Create our Firework manager...
        self.fireworkManager = FireworkManagerAI(self)

        # Create our fish manager...
        self.fishManager = FishManagerAI(self)

        # Create our factory manager...
        self.factoryMgr = FactoryManagerAI(self)

        # Create our mint manager...
        self.mintMgr = MintManagerAI(self)

        # Create our law office manager...
        self.lawMgr = LawOfficeManagerAI(self)

        # Create our country club manager...
        self.countryClubMgr = CountryClubManagerAI(self)

        # Create our promotion manager...
        self.promotionMgr = PromotionManagerAI(self)

        # Create our Cog suit manager...
        self.cogSuitMgr = CogSuitManagerAI(self)

        # Create our race manager...
        self.raceMgr = RaceManagerAI(self)

        # Create our Toontown time manager...
        self.toontownTimeManager = ToontownTimeManager(serverTimeUponLogin=int(time.time()),
                                                       globalClockRealTimeUponLogin=globalClock.getRealTime())

        self.time = EpochTime()  # simplifies datetime/epoch timestamp things
        self.partyBackups = PartyBackup()  # this is basically for calendars, for archived parties

    def createGlobals(self):
        """
        Creates "global" objects.
        """

        # Generate our time manager...
        self.timeManager = TimeManagerAI(self)
        self.timeManager.generateWithRequired(OTP_ZONE_ID_MANAGEMENT)

        # Generate our news manager...
        self.newsManager = NewsManagerAI(self)
        self.newsManager.generateWithRequired(OTP_ZONE_ID_MANAGEMENT)
        self.newsManager.d_setExpSettings(ServerSettings.GagExperienceMultiplier.get(), ServerSettings.PerBattleGagExperienceLimit.get())

        # Generate our catalog manager...
        self.catalogManager = CatalogManagerAI(self)
        self.catalogManager.generateWithRequired(OTP_ZONE_ID_MANAGEMENT)

        # Generate our in-game news manager...
        self.inGameNewsMgr = DistributedInGameNewsMgrAI(self)
        self.inGameNewsMgr.setLatestIssueStr('2013-08-22 23:49:46')
        self.inGameNewsMgr.generateWithRequired(OTP_ZONE_ID_MANAGEMENT)

        # Generate our trophy manager...
        self.trophyMgr = DistributedTrophyMgrAI(self)
        self.trophyMgr.generateWithRequired(OTP_ZONE_ID_MANAGEMENT)

        # Generate our party manager...
        self.partyManager = DistributedPartyManagerAI(self)
        self.partyManager.generateWithRequired(OTP_ZONE_ID_MANAGEMENT)

        # Generate our safezone manager...
        self.safeZoneManager = SafeZoneManagerAI(self)
        self.safeZoneManager.generateWithRequired(OTP_ZONE_ID_MANAGEMENT)

        # Generate our Polar Place effect manager...
        self.polarPlaceEffectMgr = DistributedPolarPlaceEffectMgrAI(self)
        self.polarPlaceEffectMgr.generateWithRequired(3821)

        # Generate our resistance emote manager...
        self.resistanceEmoteMgr = DistributedResistanceEmoteMgrAI(self)
        self.resistanceEmoteMgr.generateWithRequired(9720)

        # Generate our Magic Cat effect manager...
        self.magicCatEffectMgr = DistributedMagicCatEffectMgrAI(self)
        self.magicCatEffectMgr.generateWithRequired(19501)
        
        # Generate our Aviator effect manager...
        self.aviatorEffectMgr = DistributedAccessoryEffectMgrAI(self, 316, 206)
        self.aviatorEffectMgr.generateWithRequired(9952)

        # Generate our tutorial manager...
        self.tutorialManager = TutorialManagerAI(self)
        self.tutorialManager.generateWithRequired(OTP_ZONE_ID_MANAGEMENT)

        # Generate our friend manager...
        self.friendManager = FriendManagerAI(self)
        self.friendManager.generateWithRequired(OTP_ZONE_ID_MANAGEMENT)

        # Generate our chat manager...
        self.chatManager = ToontownOfflineChatManagerAI(self)
        self.chatManager.generateWithRequired(OTP_ZONE_ID_MANAGEMENT)

        # Generate our estate manager...
        self.estateMgr = EstateManagerAI(self)
        self.estateMgr.generateWithRequired(OTP_ZONE_ID_MANAGEMENT)

        # HACK: Start listening to estate events in the pet manager...
        self.petMgr.listenEvents()

        # Generate our bank manager...
        self.bankMgr = DistributedBankMgrAI(self)
        self.bankMgr.generateWithRequired(OTP_ZONE_ID_MANAGEMENT)

        # Generate our Doodle Park manager...
        self.petParkMgr = PetParkManagerAI(self)
        self.petParkMgr.generateWithRequired(OTP_ZONE_ID_MANAGEMENT)

        # Generate our Magic Word manager...
        self.magicWordManager = ToontownRealmsMagicWordManagerAI(self)
        self.magicWordManager.generateWithRequired(OTP_ZONE_ID_MANAGEMENT)

        # Generate our delivery manager...
        self.deliveryManager = self.generateGlobalObject(OTP_DO_ID_TOONTOWN_DELIVERY_MANAGER,
                                                         'DistributedDeliveryManager')

        # Generate our ban manager...
        self.banManager = self.generateGlobalObject(OTP_DO_ID_BAN_MANAGER, 'BanManager')

        # Generate our social manager...
        self.socialManager = self.generateGlobalObject(OTP_DO_ID_TTRM_SOCIAL_MANAGER, 'TTRMSocialManager')

        # Generate our Modding manager...
        self.moddingManager = ModdingManagerAI(self)
        self.moddingManager.generateWithRequiredAndId(OTP_DO_ID_MODDING_MANAGER, self.getGameDoId(),
                                                      OTP_ZONE_ID_MANAGEMENT)
        self.moddingManager.setCardsAiToUd(self.moddingManager.getCards())
        self.moddingManager.b_loadCards()
        self.moddingManager.b_setProRacer(ServerSettings.ProRacerMode.get())
        self.moddingManager.b_setSendExtraData(ServerSettings.DetailedVehicleRotation.get())
        self.moddingManager.b_setTimezone(ServerSettings.TimeZone.get())

        # Generate our Discord manager...
        self.discordManager = DiscordManagerAI(self)
        self.discordManager.generateWithRequiredAndId(OTP_DO_ID_DISCORD_MANAGER, self.getGameDoId(),
                                                      OTP_ZONE_ID_MANAGEMENT)

        # Generate our Episode manager...
        self.episodeManager = EpisodeManagerAI(self)
        self.episodeManager.generateWithRequiredAndId(OTP_DO_ID_EPISODE_MANAGER, self.getGameDoId(),
                                                      OTP_ZONE_ID_MANAGEMENT)

        # Generate our Code Redemption manager...
        self.codeRedemptionManager = TTCodeRedemptionMgrAI(self)
        self.codeRedemptionManager.generateWithRequired(OTP_ZONE_ID_MANAGEMENT)

        # Generate Datapack Manager
        self.notify.info('Loading Data Packs...')
        self.datapackMgr = DataPackManagerAI.DataPackManagerAI(self)
        self.datapackMgr.generateWithRequiredAndId(OTP_DO_ID_DATAPACK_MANAGER, self.getGameDoId(),
                                                   OTP_ZONE_ID_MANAGEMENT)
        self.datapackMgr.loadDatapacks()
        self.datapackMgr.loadPropHuntMaps()
        self.datapackMgr.loadCogAppearances()
        self.datapackMgr.loadCogQuotes()
        self.datapackMgr.loadSuitZoneSpawns()
        self.datapackMgr.loadCogAttackQuotes()
        self.datapackMgr.loadCogAttacks()
        self.datapackMgr.loadStatusEffects()
        self.datapackMgr.loadCogBattleAttributes()

        # Generate our Micro Game manager...
        if self.wantMicroGames:
            self.microGameMgr = MicroGameManagerAI(self)

        # Generate our Boss Party...
        # This functions like a Micro Game but it's
        # a manager due to it needing to be server-wide
        if self.wantBossParties:
            self.bossPartyMgr = BossPartyManagerAI(self)
            self.bossPartyMgr.generateWithRequired(OTP_ZONE_ID_MANAGEMENT)

        # Generate our Fish Poker manager...
        if self.wantFishPoker:
            self.fishPokerManager = FishPokerManagerAI(self)
            self.fishPokerManager.generateWithRequired(OTP_ZONE_ID_MANAGEMENT)

        # Our logger for things like reports, hacker warnings, and more
        self.centralLogger = CentralLoggerAI.CentralLoggerAI(self)
        self.centralLogger.generateWithRequiredAndId(OTP_DO_ID_CENTRAL_LOGGER, self.getGameDoId(),
                                                     OTP_ZONE_ID_MANAGEMENT)
        # Generate our build lot manager...
        self.buildLotMgr = DistributedBuildLotManagerAI(self)
        self.buildLotMgr.generateWithRequired(OTP_ZONE_ID_MANAGEMENT)

    def createHood(self, hoodCtr, zoneId):
        # Bossbot HQ doesn't use DNA, so we skip over that.
        if zoneId != ToontownGlobals.BossbotHQ:
            self.dnaStoreMap[zoneId] = DNAStorage()
            self.dnaDataMap[zoneId] = self.loadDNAFileAI(self.dnaStoreMap[zoneId], ZoneUtil.genDNAFileName(zoneId))
            if zoneId in ToontownGlobals.HoodHierarchy:
                for streetId in ToontownGlobals.HoodHierarchy[zoneId]:
                    self.dnaStoreMap[streetId] = DNAStorage()
                    self.dnaDataMap[streetId] = self.loadDNAFileAI(self.dnaStoreMap[streetId],
                                                                   ZoneUtil.genDNAFileName(streetId))

        hood = hoodCtr(self, zoneId)
        hood.startup()
        self.hoods.append(hood)

    def createZones(self):
        # First, generate our zone2NpcDict...
        NPCToons.generateZone2NpcDict()

        # The zone table determines which dnaStores are created and
        # whether bulding manager or suit planner ai objects are created.
        # The elements consist of:
        # (int the_zone_ID, bool create_building_manager, bool create_suit_planner)
        # Toontown Central
        self.zoneTable[ToontownGlobals.ToontownCentral] = (
            (ToontownGlobals.ToontownCentral, 1, 0), (ToontownGlobals.SillyStreet, 1, 1),
            (ToontownGlobals.LoopyLane, 1, 1), (ToontownGlobals.PunchlinePlace, 1, 1)
        )
        self.createHood(TTHoodDataAI, ToontownGlobals.ToontownCentral)

        # Donald's Dock
        self.zoneTable[ToontownGlobals.DonaldsDock] = (
            (ToontownGlobals.DonaldsDock, 1, 0), (ToontownGlobals.BarnacleBoulevard, 1, 1),
            (ToontownGlobals.SeaweedStreet, 1, 1), (ToontownGlobals.LighthouseLane, 1, 1)
        )
        self.createHood(DDHoodDataAI, ToontownGlobals.DonaldsDock)

        # Daisy Gardens
        self.zoneTable[ToontownGlobals.DaisyGardens] = (
            (ToontownGlobals.DaisyGardens, 1, 0), (ToontownGlobals.ElmStreet, 1, 1),
            (ToontownGlobals.MapleStreet, 1, 1), (ToontownGlobals.OakStreet, 1, 1)
        )
        self.createHood(DGHoodDataAI, ToontownGlobals.DaisyGardens)

        # Minnie's Melodyland
        self.zoneTable[ToontownGlobals.MinniesMelodyland] = (
            (ToontownGlobals.MinniesMelodyland, 1, 0), (ToontownGlobals.AltoAvenue, 1, 1),
            (ToontownGlobals.BaritoneBoulevard, 1, 1), (ToontownGlobals.TenorTerrace, 1, 1)
        )
        self.createHood(MMHoodDataAI, ToontownGlobals.MinniesMelodyland)

        # The Brrrgh
        self.zoneTable[ToontownGlobals.TheBrrrgh] = (
            (ToontownGlobals.TheBrrrgh, 1, 0), (ToontownGlobals.WalrusWay, 1, 1),
            (ToontownGlobals.SleetStreet, 1, 1), (ToontownGlobals.PolarPlace, 1, 1)
        )
        self.createHood(BRHoodDataAI, ToontownGlobals.TheBrrrgh)

        # Donald's Dreamland
        self.zoneTable[ToontownGlobals.DonaldsDreamland] = (
            (ToontownGlobals.DonaldsDreamland, 1, 0), (ToontownGlobals.LullabyLane, 1, 1),
            (ToontownGlobals.PajamaPlace, 1, 1), (ToontownGlobals.DreamyDriveOutcove, 1, 0),
            (ToontownGlobals.DreamyDrive, 1, 1)
        )
        self.createHood(DLHoodDataAI, ToontownGlobals.DonaldsDreamland)

        # Sellbot HQ
        self.zoneTable[ToontownGlobals.SellbotHQ] = (
            (ToontownGlobals.SellbotHQ, 0, 1), (ToontownGlobals.SellbotFactoryExt, 0, 1)
        )
        self.createHood(CSHoodDataAI, ToontownGlobals.SellbotHQ)

        # Cashbot HQ
        self.zoneTable[ToontownGlobals.CashbotHQ] = (
            (ToontownGlobals.CashbotHQ, 0, 1),
        )
        self.createHood(CashbotHQDataAI, ToontownGlobals.CashbotHQ)

        # Lawbot HQ
        self.zoneTable[ToontownGlobals.LawbotHQ] = (
            (ToontownGlobals.LawbotHQ, 0, 1),
        )
        self.createHood(LawbotHQDataAI, ToontownGlobals.LawbotHQ)

        # Bossbot HQ
        self.zoneTable[ToontownGlobals.BossbotHQ] = (
            (ToontownGlobals.BossbotHQ, 0, 0),
        )
        self.createHood(BossbotHQDataAI, ToontownGlobals.BossbotHQ)

        # Goofy Speedway
        self.zoneTable[ToontownGlobals.GoofySpeedway] = (
            (ToontownGlobals.GoofySpeedway, 1, 0),
        )
        self.createHood(GSHoodDataAI, ToontownGlobals.GoofySpeedway)

        # Chip 'n Dale's Acorn Acres
        self.zoneTable[ToontownGlobals.OutdoorZone] = (
            (ToontownGlobals.OutdoorZone, 1, 0), (ToontownGlobals.HiddenCamp, 1, 0)
        )
        self.createHood(OZHoodDataAI, ToontownGlobals.OutdoorZone)

        # Chip 'n Dale's MiniGolf
        self.zoneTable[ToontownGlobals.GolfZone] = (
            (ToontownGlobals.GolfZone, 1, 0),
        )
        self.createHood(GZHoodDataAI, ToontownGlobals.GolfZone)

        # Toontown Fields
        self.zoneTable[ToontownGlobals.ToontownSkies] = (
            (ToontownGlobals.ToontownSkies, 1, 0),
        )
        self.createHood(CFHoodDataAI, ToontownGlobals.ToontownSkies)

        # Only generate the following playgrounds if the server is NOT in Legit Mode
        if not self.legitMode:
           # # Toontown Outskirts
           # self.zoneTable[ToontownGlobals.ToontownOutskirts] = (
           #     (ToontownGlobals.ToontownOutskirts, 1, 1), (ToontownGlobals.TutorialTerrace, 1, 1),
           #     (ToontownGlobals.CogtownCentral, 1, 0), (ToontownGlobals.SellbotHQFuture, 0, 0)
           # )
           # self.createHood(SpecialHoodDataAI, ToontownGlobals.ToontownOutskirts)

            # Toontown Central Beta
            self.zoneTable[ToontownGlobals.ToontownCentralBeta] = (
                (ToontownGlobals.ToontownCentralBeta, 1, 0),
                # (ToontownGlobals.SillyStreetBeta, 1, 1)
            )
            self.createHood(TTBetaHoodDataAI, ToontownGlobals.ToontownCentralBeta)

            # Daisy Gardens Beta
            self.zoneTable[ToontownGlobals.DaisyGardensBeta] = (
                (ToontownGlobals.DaisyGardensBeta, 1, 0), (ToontownGlobals.OakStreetBeta, 1, 0)
            )
            self.createHood(DGBetaHoodDataAI, ToontownGlobals.DaisyGardensBeta)

            # Minnie's Melodyland Beta
            self.zoneTable[ToontownGlobals.MinniesMelodylandBeta] = (
                (ToontownGlobals.MinniesMelodylandBeta, 1, 0),
            )
            self.createHood(MMBetaHoodDataAI, ToontownGlobals.MinniesMelodylandBeta)

            # Donald's Dreamland Beta
            self.zoneTable[ToontownGlobals.DonaldsDreamlandBeta] = (
                (ToontownGlobals.DonaldsDreamlandBeta, 1, 0),
            )
            self.createHood(DLBetaHoodDataAI, ToontownGlobals.DonaldsDreamlandBeta)
            # The Brrrgh Beta
            self.zoneTable[ToontownGlobals.TheBrrrghBeta] = (
                (ToontownGlobals.TheBrrrghBeta, 1, 0),
            )
            self.createHood(BRBetaHoodDataAI, ToontownGlobals.TheBrrrghBeta)
            # Donald's Dock Beta
            self.zoneTable[ToontownGlobals.DonaldsDockBeta] = (
                (ToontownGlobals.DonaldsDockBeta, 1, 0),
            )
            self.createHood(DDBetaHoodDataAI, ToontownGlobals.DonaldsDockBeta)

            # Toonland DLC Funny Farms
            self.zoneTable[ToontownGlobals.ToonLandFunnyFarm] = (
                (ToontownGlobals.ToonLandFunnyFarm, 1, 0),
                (ToontownGlobals.ToonLandBarkingBoulv, 1, 0),
            )
            self.createHood(TLFFHoodDataAI, ToontownGlobals.ToonLandFunnyFarm)


        # Assign the initial suit buildings.
        self.notify.info('Assigning initial Cog buildings and Field Offices...')
        for suitPlanner in list(self.suitPlanners.values()):
            suitPlanner.assignInitialSuitBuildings()

    def sendPing(self, task = None):
        ## removed for open source release
        return Task.done

    def sendPingToAPI(self, **kwargs):
        ## removed for open source release
        ...

    def httpRequest(self, url, callback, data = None, authHeader = None):
        self.apinotify.debug(data)
        # Encode our dictonary
        if type(data) in (dict, list):
            data = json.dumps(data)

        headers = {
                   "Accept": "application/json"}
        if authHeader:
            headers['Authorization'] = authHeader

        # Make our HTTPChannel if we haven't already.
        if not self.websiteChannel:
            self.websiteChannel = HTTPClient.getGlobalPtr().makeChannel(True)  # type: HTTPChannel

        # Insert our headers
        self.websiteChannel.clearExtraHeaders()
        self.websiteChannel.setContentType('application/json')
        for header in headers.items():
            self.websiteChannel.sendExtraHeader(*header)

        stream = StringStream()

        # Send info to the API and download output into stream.
        self.websiteChannel.beginPostForm(DocumentSpec(url), data)
        self.websiteChannel.downloadToStream(stream)

        # Since this is non-blocking function, we need to fire up a
        # task and come back to it asynchronously.
        def __task(task):
            # Returns True if there's things left to do and should be called,
            # each frame, False otherwise.
            if self.websiteChannel.run():
                return task.cont

            status = self.websiteChannel.getStatusCode()
            msg = self.websiteChannel.getStatusString()

            if not self.websiteChannel.isValid():
                callback({'status': status,
                          'message': f"{msg} ({status})  Make sure you are connected to the Internet."
                          })

            if stream.getDataSize():
                try:
                    resp = json.loads(stream.getData())
                except:
                    resp = {'status': status, 'message': "Returned an non-JSON response!"}
                callback(resp)
            else:
                callback({'status': status, 'message': "No data returned!"})

            return task.done

        taskMgr.add(__task, f'httpRequest-{self.websiteRequestNum}')
        # Count up for each task fired so they don't overlap.
        self.websiteRequestNum += 1

    def avatarCountCheck(self):
        if __debug__:
            return

        avatarCount = len(self.onlineAvatars)
        if not self.districtFull and avatarCount >= self.districtLimit:
            self.districtFull = True
            self.notify.warning('Reached player limit! Making district unavailable...')
            self.district.b_setFull(0)
            self.notify.warning('District is now unavailable. Incoming connections will be rejected.')

        if self.districtFull and avatarCount < self.districtLimit:
            self.districtFull = False
            self.notify.info('Player count dropped! Making district available...')
            self.district.b_setFull(1)
            self.notify.info('District is now available. Incoming connections will be accepted.')

    def getAvatarExitEvent(self, avId):
        return 'distObjDelete-%d' % avId

    def getZoneDataStore(self):
        return self.zoneDataStore

    @staticmethod
    def genDNAFileName(zoneId):
        return ZoneUtil.genDNAFileName(zoneId)

    def findFishingPonds(self, dnaGroup, zoneId, area, overrideDNAZone = 0):
        """
                Recursively scans the given DNA tree for fishing ponds.  These
                are defined as all the groups whose code includes the string
                "fishing_pond".  For each such group, creates a
                DistributedFishingPondAI.  Returns the list of distributed
                objects and a list of the DNAGroups so we can search them for
                spots and targets.
                """
        fishingPonds = []
        fishingPondGroups = []

        if ((isinstance(dnaGroup, DNAGroup)) and
                # If it is a DNAGroup, and the name starts with fishing_pond, count it
                (dnaGroup.getName().find('fishing_pond') >= 0)):
            # Here's a fishing pond!
            fishingPondGroups.append(dnaGroup)
            fp = DistributedFishingPondAI.DistributedFishingPondAI(self, area)
            fp.generateWithRequired(zoneId)
            fishingPonds.append(fp)
        else:
            # Now look in the children
            # Fishing ponds cannot have other ponds in them,
            # so do not search the one we just found:
            # If we come across a visgroup, note the zoneId and then recurse
            if (isinstance(dnaGroup, DNAVisGroup) and not overrideDNAZone):
                zoneId = int(dnaGroup.getName().split(':')[0])
            for i in range(dnaGroup.getNumChildren()):
                childFishingPonds, childFishingPondGroups = self.findFishingPonds(
                    dnaGroup.at(i), zoneId, area, overrideDNAZone)
                fishingPonds += childFishingPonds
                fishingPondGroups += childFishingPondGroups
        return fishingPonds, fishingPondGroups

    def findFishingSpots(self, dnaPondGroup, distPond):
        """
        Scans the given DNAGroup pond for fishing spots.  These
        are defined as all the props whose code includes the string
        "fishing_spot".  Fishing spots should be the only thing under a pond
        node. For each such prop, creates a DistributedFishingSpotAI.
        Returns the list of distributed objects created.
        """
        fishingSpots = []
        # Search the children of the pond
        for i in range(dnaPondGroup.getNumChildren()):
            dnaGroup = dnaPondGroup.at(i)
            if ((isinstance(dnaGroup, DNAProp)) and (dnaGroup.getCode().find('fishing_spot') >= 0)):
                if (dnaGroup.getCode().find('classic_fishing_spot') >= 0):
                    continue
                # Here's a fishing spot!
                pos = dnaGroup.getPos()
                hpr = dnaGroup.getHpr()
                fs = DistributedFishingSpotAI.DistributedFishingSpotAI(
                     self, distPond, pos[0], pos[1], pos[2], hpr[0], hpr[1], hpr[2])
                fs.generateWithRequired(distPond.zoneId)
                fishingSpots.append(fs)
            else:
                self.notify.debug("Found dnaGroup that is not a fishing_spot under a pond group")
        return fishingSpots

    def findClassicFishingSpots(self, dnaPondGroup, distPond):
        fishingSpots = []
        # Search the children of the pond
        for i in range(dnaPondGroup.getNumChildren()):
            dnaGroup = dnaPondGroup.at(i)
            if ((isinstance(dnaGroup, DNAProp)) and (dnaGroup.getCode().find('classic_fishing_spot') >= 0)):
                # Here's a fishing spot!
                pos = dnaGroup.getPos()
                hpr = dnaGroup.getHpr()
                fs = DistributedClassicFishingSpotAI.DistributedClassicFishingSpotAI(self, i)
                fs.setPondDoId(distPond.getDoId())
                fs.setPosHpr(*pos, *hpr)
                fs.generateWithRequired(distPond.zoneId)
                fishingSpots.append(fs)
            else:
                self.notify.debug("Found dnaGroup that is not a fishing_spot under a pond group")
        return fishingSpots

    def handleAvCatch(self, avId, zoneId, catch):
        """
        avId - ID of avatar to update
        zoneId - zoneId of the pond the catch was made in.
                This is used by the BingoManagerAI to
                determine which PBMgrAI needs to update
                the catch.
        catch - a fish tuple of (genus, species)
        returns: None

        This method instructs the BingoManagerAI to
        tell the appropriate PBMgrAI to update the
        catch of an avatar at the particular pond. This
        method is called in the FishManagerAI's
        RecordCatch method.
        """
        # Guard for publish
        if simbase.wantBingo:
            if self.bingoMgr:
                self.bingoMgr.setAvCatchForPondMgr(avId, zoneId, catch)

    def createPondBingoMgrAI(self, estate):
        """
        estate - the estate for which the PBMgrAI should
                be created.
        returns: None

        This method instructs the BingoManagerAI to
        create a new PBMgrAI for a newly generated
        estate.
        """
        # Guard for publish
        if simbase.wantBingo:
            if self.bingoMgr:
                self.notify.info('createPondBingoMgrAI: Creating a DPBMAI for Dynamic Estate')
                self.bingoMgr.createPondBingoMgrAI(estate, 1)

    def findPartyHats(self, dnaData, zoneId):
        partyHats = []
        if isinstance(dnaData, DNAGroup) and ('prop_party_gate' in dnaData.getName()):
            partyHat = DistributedPartyGateAI(self)
            partyHat.generateWithRequired(zoneId)
            partyHats.append(partyHat)

        for i in range(dnaData.getNumChildren()):
            foundPartyHats = self.findPartyHats(dnaData.at(i), zoneId)
            partyHats.extend(foundPartyHats)

        return partyHats

    def loadDNAFileAI(self, dnaStore, dnaFileName):
        return loadDNAFileAI(dnaStore, dnaFileName)

    def loadDNAFile(self, dnaStore, dnaFileName):
        """
        load everything, including geometry
        """
        return loadDNAFile(dnaStore, dnaFileName)

    def allocateZone(self, owner=None):
        zoneId = self.zoneAllocator.allocate()
        if owner:
            self.zoneId2owner[zoneId] = owner

        return zoneId

    def deallocateZone(self, zone):
        if self.zoneId2owner.get(zone):
            del self.zoneId2owner[zone]

        self.zoneAllocator.free(zone)

    def findRacingPads(self, dnaData, zoneId, area, type='racing_pad', overrideDNAZone=False):
        racingPads, racingPadGroups = [], []
        if type in dnaData.getName():
            if type == 'racing_pad':
                nameSplit = dnaData.getName().split('_')
                racePad = DistributedRacePadAI(self)
                racePad.setArea(area)
                racePad.index = int(nameSplit[2])
                racePad.genre = nameSplit[3]
                trackInfo = RaceGlobals.getNextRaceInfo(-1, racePad.genre, racePad.index)
                racePad.setTrackInfo([trackInfo[0], trackInfo[1]])
                racePad.laps = trackInfo[2]
                racePad.generateWithRequired(zoneId)
                racingPads.append(racePad)
                racingPadGroups.append(dnaData)
            elif type == 'viewing_pad':
                viewPad = DistributedViewPadAI(self)
                viewPad.setArea(area)
                viewPad.generateWithRequired(zoneId)
                racingPads.append(viewPad)
                racingPadGroups.append(dnaData)

        for i in range(dnaData.getNumChildren()):
            foundRacingPads, foundRacingPadGroups = self.findRacingPads(dnaData.at(i), zoneId, area, type,
                                                                        overrideDNAZone)
            racingPads.extend(foundRacingPads)
            racingPadGroups.extend(foundRacingPadGroups)

        return racingPads, racingPadGroups

    def findStartingBlocks(self, dnaData, pad):
        startingBlocks = []
        for i in range(dnaData.getNumChildren()):
            groupName = dnaData.getName()
            blockName = dnaData.at(i).getName()
            if 'starting_block' in blockName:
                cls = DistributedStartingBlockAI if 'racing_pad' in groupName else DistributedViewingBlockAI
                x, y, z = dnaData.at(i).getPos()
                h, p, r = dnaData.at(i).getHpr()
                padLocationId = int(dnaData.at(i).getName()[-1])
                startingBlock = cls(self, pad, x, y, z, h, p, r, padLocationId)
                startingBlock.generateWithRequired(pad.zoneId)
                startingBlocks.append(startingBlock)

        return startingBlocks

    def getAvatarDisconnectReason(self, avId):
        return self.timeManager.avId2disconnectcode.get(avId, ToontownGlobals.DisconnectUnknown)

    def findLeaderBoards(self, dnaData, zoneId):
        leaderboards = []
        if 'leaderBoard' in dnaData.getName():
            x, y, z = dnaData.getPos()
            h, p, r = dnaData.getHpr()
            leaderboard = DistributedLeaderBoardAI(self, dnaData.getName(), x, y, z, h, p, r)
            leaderboard.generateWithRequired(zoneId)
            leaderboards.append(leaderboard)

        for i in range(dnaData.getNumChildren()):
            foundLeaderBoards = self.findLeaderBoards(dnaData.at(i), zoneId)
            leaderboards.extend(foundLeaderBoards)

        return leaderboards

    def systemMessage(self, message):
        for doId, do in list(self.doId2do.items()):
            if isinstance(do, DistributedPlayerAI):
                if str(doId)[0] != str(self.districtId)[0]:
                    do.d_setSystemMessage(0, message, WhisperPopup.WTSystem)

    def maintenanceMessage(self, message):
        for doId, do in list(self.doId2do.items()):
            if isinstance(do, DistributedPlayerAI):
                if str(doId)[0] != str(self.districtId)[0]:
                    do.d_systemWarning(message)

    def announceMaintenance(self, reason, type, time):
        minute = 60
        minuteLess = time - minute
        msg = TTLocalizer.ServerShutdownAnnouncement.format(type, time)
        self.systemMessage(msg)
        messenger.send('maintenanceMessage')
        if minuteLess > 0:
            taskMgr.doMethodLater(minute, self.announceMaintenance, 'announceMaintenance', extraArgs=[reason, type, minuteLess])
        if time <= minute:
            taskMgr.doMethodLater(time, self.shutdownMaintenance, 'shutdownMaintenance', extraArgs=[reason])

    def shutdownMaintenance(self, reason):
        for doId, do in list(self.doId2do.items()):
            if isinstance(do, DistributedPlayerAI):
                if str(doId)[0] != str(self.districtId)[0]:
                    do.sendSetKick(reason=reason, target=do, silent=3)

    def updateOnlineAvatar(self, toon):
        if toon.isTemporaryToon():
            return
        previousVisibility = VisibilityTypes.INVISIBLE
        visibility = VisibilityTypes.ONLINE
        if toon.getDoId() in self.onlineAvatars:
            previousVisibility = self.onlineAvatars[toon.getDoId()][10]

        # We are a moderator who is now ghosted. We do not want others to know of our presense.
        if toon.ghostMode == 2:
            visibility = VisibilityTypes.INVISIBLE

        self.onlineAvatars[toon.getDoId()] = [toon.getDoId(),
                                              toon.getName(),
                                              toon.getDNAString(),
                                              toon.getPetId(),
                                              toon.getHat(),
                                              toon.getGlasses(),
                                              toon.getBackpack(),
                                              toon.getShoes(),
                                              toon.getProfileBackground(),
                                              toon.getProfilePose(),
                                              visibility]
        self.district.sendUpdate('updateOnlineAvatar', [self.onlineAvatars[toon.getDoId()]])

        # We were previously invisible or offline.
        if not previousVisibility and visibility:
            self.newsManager.d_setOnlineStatus(1, toon.getDoId(), toon.getName())
        # We were previously online, and now we need to disclose our intent to be invisible or offline. 
        elif previousVisibility and not visibility:
            self.newsManager.d_setOnlineStatus(0, toon.getDoId(), toon.getName())

    def removeOnlineAvatar(self, toon):
        if toon.isTemporaryToon():
            return
        if toon.getDoId() in self.onlineAvatars:
            visibility = self.onlineAvatars[toon.getDoId()][10]
            del self.onlineAvatars[toon.getDoId()]
            self.district.sendUpdate('removeOnlineAvatar', [toon.getDoId()])
            if visibility != VisibilityTypes.INVISIBLE:
                self.newsManager.d_setOnlineStatus(0, toon.getDoId(), toon.getName())

    def handlePlayerBanned(self, avId):
        self.district.sendUpdate('handlePlayerBanned', [avId])

    def getPlayerEnterZoneEventName(self, zoneId):
        return f"playerEnteredZone-{zoneId}"

    def adjustSettingsBasedOnGamemode(self):
        if self.gamemode == ToontownGlobals.ModeOffline:
            self.wantSelfToonUp = True
        else:
            self.wantSelfToonUp = self.config.GetBool('self-toon-up', True)

    def updateFieldsBasedOnGamemode(self):
        self.district.b_setSelfToonUp(self.wantSelfToonUp)

    def setGamemode(self):
        if self.gamemode == ToontownGlobals.ModeOffline:
            self.gamemode = ToontownGlobals.ModeServer
        elif self.gamemode == ToontownGlobals.ModeServer:
            self.gamemode = ToontownGlobals.ModeOffline

        # Adjust our Mini-Server settings based on our new gamemode.
        self.adjustSettingsBasedOnGamemode()
        self.updateFieldsBasedOnGamemode()

    def getEstate(self, avId, accId, zoneId, callback):
        self.notify.debug(f'getEstate avId={avId}, accId={accId}, zoneId={zoneId}, callback={callback}')
        estateId = 0
        estateVal = {} # {estateFieldName: packedValues}
        avIds = []

        avatars = {} # {avId: {fieldName: [fieldValue]}}

        def __handleGetEstate(dclass, fields):
            if dclass != self.dclassesByName['DistributedEstateAI']:
                self.notify.warning(
                    f'Account {accId} has non-estate dclass {dclass}!'
                )
                return

            nonlocal estateVal
            # Convert Astron response to OTP
            estateVal = self.packDclassValueDict(dclass, fields)

            # Now to do the houses:
            self.getHouses(avId, accId, zoneId, estateId, estateVal, avIds, avatars, callback)

        def __gotAllAvatars():
            self.notify.debug(f'__gotAllAvatars: {estateId, avIds, len(avatars)}')

            if estateId:
                self.dbInterface.queryObject(self.dbId, estateId, __handleGetEstate)
            else:
                def __handleEstateCreated(newEstateId):
                    nonlocal estateId
                    estateId = newEstateId
                    # Update Account object with the new estate id
                    self.dbInterface.updateObject(self.dbId, accId, self.dclassesByName['AccountAI'],
                                                          {'ESTATE_ID': estateId})

                    self.dbInterface.queryObject(self.dbId, estateId, __handleGetEstate)

                self.dbInterface.createObject(self.dbId, self.dclassesByName['DistributedEstateAI'], {},
                                                  __handleEstateCreated)


        def __handleGetAvatar(dclass, fields, index):
            if dclass != self.dclassesByName['DistributedToonAI']:
                self.notify.warning(
                    f'Account {accId} has avatar {avIds[index]} with non-Toon dclass {dclass}!')
                # FIXME: idk what to do here? ~LC
                return


            fields['avId'] = avIds[index]
            avatars[index] = fields
            if len(avatars) == 6:
                __gotAllAvatars()

        def __handleGetAccount(dclass, fields):
            if dclass != self.dclassesByName['AccountAI']:
                self.notify.warning(f'Account {accId} has non-account dclass {dclass}!')
                # FIXME: idk what to do here? ~LC
                return

            nonlocal estateId, avIds, avatars
            estateId = fields.get('ESTATE_ID', 0)
            avIds = fields.get('ACCOUNT_AV_SET', [0] * 6)
            # HACK: Sanitize the avIds list in case its too long/short
            avIds = avIds[:6]
            avIds += [0] * (6 - len(avIds))
            for index, avId in enumerate(avIds):
                if avId == 0:
                    avatars[index] = None
                    continue

                # Get the avatar object for each avId.
                self.dbInterface.queryObject(self.dbId, avId,
                                             functools.partial(__handleGetAvatar, index=index))

        # Get the account object.
        self.dbInterface.queryObject(self.dbId, accId, __handleGetAccount)


    def getHouses(self, avId, accId, zoneId, estateId, estateVal, avIds, avatars, callback):
        '''
        Continuation of getEstate
        '''
        self.notify.debug(f'getHouses avId={avId}, accId={accId}, zoneId={zoneId}, estateId={estateId}, avIds={avIds}, callback={callback}')

        # numHouses = 0
        houseIds = [0] * len(avIds)
        houseVal = [None] * len(avIds) # [packedHouseValues]

        def __gotAllHouses():
            # Get pet ids
            petIds = [0] * len(avIds)
            for index in avatars:
                if avatars[index] != None:
                    petId = avatars[index].get('setPetId', [0])[0]
                    if petId != 0:
                        petIds[index] = petId

            # Get Gardens started.
            gardensStarted = [False] * len(avIds)
            for index in avatars:
                if avatars[index] != None:
                    gardenStarted = avatars[index].get('setGardenStarted', [0])[0]
                    if gardenStarted:
                        gardensStarted[index] = True

            self.notify.debug(f'__gotAllHouses {estateId, estateVal, len(houseIds), houseIds, houseVal, petIds, gardensStarted, estateVal}')

            # That's a lot of work, time to finally call our callback.  Whew!
            callback(estateId, estateVal, len(houseIds), houseIds, houseVal,
                     petIds, gardensStarted, estateVal)

        def __handleGetHouse(dclass, fields, index):
            nonlocal houseVal
            if dclass != self.dclassesByName['DistributedHouseAI']:
                self.notify.warning(f'Avatar {avIds[index]} has non-house object {houseId} with dclass {dclass}!')
                return

            # Set the most important fields here.
            fields['setAvatarId'] = [avIds[index]]
            fields['setName'] = avatars[index]['setName']

            # Convert Astron response to OTP
            houseVal[index] = self.packDclassValueDict(dclass, fields)

            if None not in houseVal:
                __gotAllHouses()

        def __handleHouseCreated(houseId, index):
            nonlocal houseIds, houseVal

            houseIds[index] = houseId
            av = self.doId2do.get(avIds[index])
            if av:
                # Update house id
                av.b_setHouseId(houseId)
            else:
                self.dbInterface.updateObject(self.dbId, avIds[index],
                                                      self.dclassesByName['DistributedToonAI'],
                                                      {'setHouseId': [houseId]})

            # self.dbInterface.queryObject(self.dbId, houseId,
                                         # functools.partial(__handleGetHouse, index=index))
            __handleGetHouse(self.dclassesByName['DistributedHouseAI'], {}, index)


        for index in avatars:
            if avatars[index] == None:
                # No avatar, no house. Allocate an ID in it's place
                # (it'll be generated into an empty house)
                houseId = self.allocateChannel()
                houseIds[index] = houseId
                houseVal[index] = {}
                if None not in houseVal:
                    __gotAllHouses()
                    return
                else:
                    continue
            houseId = avatars[index].get('setHouseId', [0])[0]
            if houseId == 0:
                # No house
                self.dbInterface.createObject(self.dbId, self.dclassesByName['DistributedHouseAI'],
                                              {},
                                              #{'setName': [avatars[index]['setName'][0]],
                                              # 'setAvatarId': [avatars[index]['avId']]},
                                              functools.partial(__handleHouseCreated, index=index))
            else:
                houseIds[index] = houseId
                self.dbInterface.queryObject(self.dbId, houseId,
                                             functools.partial(__handleGetHouse, index=index))

    def logEvent(self, _type: int, toonId: int, toonName: str, accountId: int, contents: str, target = 0):
        ToontownAIRepository.logMessages.append(
            {
                "Type": _type,
                "SenderToonID": toonId,
                "SenderToonName": toonName,
                "SenderAccountID": accountId,
                "Target": target,
                "Contents": contents,
                "Time": datetime.utcnow().strftime(f"%Y%m%d%H%M%S000")
            }
        )

    def postLogs(self, task = None):
        __logs = ToontownAIRepository.logMessages
        if len(ToontownAIRepository.logMessages) == 0:
            return task.again
        self.sendLogsToApi(__logs)

        ToontownAIRepository.logMessages = []
        return task.again

    def sendLogsToApi(self, data: List[Dict]):
        def __callback(resp):
            if 'status' not in resp:
                self.apinotify.info('Successfully sent logs to the API')
                return  # ???
            status = resp['status']
            message = resp['message']

            if status != 200:
                self.apinotify.info('Could not send the logs to the API! (Message: %s)' % message)
                return

            self.apinotify.info('Successfully sent report to API')
        self.httpRequest(ServerSettings.LoggingEndpoint.get(),
                         __callback, data = data,
                         authHeader = ServerSettings.LoggingEndpointAuthHeader.get())


    if __debug__:
        def refresh(self):
            try:
                import limeade
            except ModuleNotFoundError:
                return 'Limeade must be installed to refresh.'
            # Refresh all the modules currently imported with Limeade.
            limeade.refresh()

            # Since Limeade refreshes the language module (e.g. TTLocalizerEnglish.py) and doesn't update
            # the both the OTPLocalizer and TTLocalizer module with the changes made to it,
            # we have to do so ourselves.

            # First the OTPLocalizer...
            from otp.otpbase import OTPLocalizer
            languageModule = OTPLocalizer.getLanguageModule()
            for key, val in languageModule.__dict__.items():
                if key in OTPLocalizer.__dict__:
                    OTPLocalizer.__dict__[key] = val

            # And now the TTLocalizer...
            languageModule = TTLocalizer.getLanguageModule()
            for key, val in languageModule.__dict__.items():
                if key in TTLocalizer.__dict__:
                    TTLocalizer.__dict__[key] = val

            return 'AI modules has been refreshed.'
