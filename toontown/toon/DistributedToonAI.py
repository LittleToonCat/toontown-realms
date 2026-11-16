from typing import Tuple, List

from otp.ai.AIBaseGlobal import *
from panda3d.core import *
from otp.otpbase import OTPGlobals
from direct.directnotify import DirectNotifyGlobal
from . import ToonDNA
from toontown.suit import SuitDNA
from . import InventoryBase
from . import Experience
from otp.avatar import DistributedAvatarAI
from otp.avatar import DistributedPlayerAI
from direct.distributed import DistributedSmoothNodeAI
from toontown.toonbase import ToontownGlobals, ServerSettings
from toontown.quest import QuestRewardCounter
from toontown.quest import Quests
from toontown.toonbase import ToontownBattleGlobals
from direct.task import Task
from toontown.catalog import CatalogItemList
from toontown.catalog import CatalogItem
from direct.showbase import PythonUtil
from direct.distributed.ClockDelta import *
from toontown.toonbase.ToontownGlobals import *
import types
from toontown.fishing import FishGlobals
from toontown.fishing import FishCollection
from toontown.fishing import FishTank
from .NPCToons import npcFriends, isZoneProtected
from toontown.coghq import CogDisguiseGlobals
import random
import re
from toontown.chat import ResistanceChat
from toontown.racing import RaceGlobals
from toontown.hood import ZoneUtil
from toontown.toon import NPCToons
from toontown.estate import FlowerCollection
from toontown.estate import FlowerBasket
from toontown.estate import GardenGlobals
from toontown.golf import GolfGlobals
from toontown.parties import PartyGlobals
from toontown.parties.PartyInfo import PartyInfoAI
from toontown.parties.InviteInfo import InviteInfoBase
from toontown.parties.PartyReplyInfo import PartyReplyInfoBase
from toontown.parties.PartyGlobals import InviteStatus
from toontown.toonbase import ToontownAccessAI
from toontown.toonbase import TTLocalizer
from toontown.catalog import CatalogAccessoryItem
from toontown.minigame import MinigameCreatorAI
from toontown.shtiker import CogPageGlobals
from toontown.episodes.EpisodeConfig import EpisodeName2Id, EpisodeId2Name
from . import ModuleListAI
import json
from functools import reduce
from typing import List

from ..toonbase.ToontownTypes import TColor, TShirt, TBottom

if simbase.wantPets:
    from toontown.pets import PetLookerAI, PetObserve
else:
    class PetLookerAI:
        class PetLookerAI:
            pass

if simbase.wantKarts:
    from toontown.racing.KartDNA import *

import pickle


class DistributedToonAI(DistributedPlayerAI.DistributedPlayerAI, DistributedSmoothNodeAI.DistributedSmoothNodeAI, PetLookerAI.PetLookerAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedToonAI')
    maxCallsPerNPC = 100
    partTypeIds = {ToontownGlobals.FT_FullSuit: (CogDisguiseGlobals.leftLegIndex,
                                   CogDisguiseGlobals.rightLegIndex,
                                   CogDisguiseGlobals.torsoIndex,
                                   CogDisguiseGlobals.leftArmIndex,
                                   CogDisguiseGlobals.rightArmIndex),
     ToontownGlobals.FT_Leg: (CogDisguiseGlobals.leftLegIndex, CogDisguiseGlobals.rightLegIndex),
     ToontownGlobals.FT_Arm: (CogDisguiseGlobals.leftArmIndex, CogDisguiseGlobals.rightArmIndex),
     ToontownGlobals.FT_Torso: (CogDisguiseGlobals.torsoIndex,)}
    lastFlagAvTime = globalClock.getFrameTime()
    flagCounts = {}
    WantTpTrack = simbase.config.GetBool('want-tptrack', False)

    BlockNames = ['nigger', '#unbanconnor', 'unbanconnor', 'kike', 'twitch.tv/rconnor', 'nigga', 'nlgga',
                  'nlgger', 'n1gger', 'n1gga', 'nigg3r', 'n1gg3r', 'nlgg3r', 'n1gg@', 'nlgg@']
    MaxNameLength = 140
    ToonUpTaskAmount = simbase.config.GetInt('playground-passive-healing-amount', 1)

    def __init__(self, air):
        DistributedPlayerAI.DistributedPlayerAI.__init__(self, air)
        DistributedSmoothNodeAI.DistributedSmoothNodeAI.__init__(self, air)
        if simbase.wantPets:
            PetLookerAI.PetLookerAI.__init__(self)
        self.air = air
        self.dna = ToonDNA.ToonDNA()
        self.inventory = None
        self.fishCollection = None
        self.fishTank = None
        self.experience = None
        self.quests = []
        self.cogs = []
        self.cogCounts = []
        self.NPCFriendsDict = {}
        self.clothesTopsList = []
        self.clothesBottomsList = []
        self.closetShirts: List[TShirt] = []
        self.closetBottoms: List[TBottom] = []
        self.hatList = []
        self.glassesList = []
        self.backpackList = []
        self.shoesList = []
        self.hat = (0, 0, 0)
        self.glasses = (0, 0, 0)
        self.backpack = (0, 0, 0)
        self.shoes = (0, 0, 0)
        self.cogTypes = [0,
         0,
         0,
         0]
        self.cogLevel = [0,
         0,
         0,
         0]
        self.cogParts = [0,
         0,
         0,
         0]
        self.cogRadar = [0,
         0,
         0,
         0]
        self.disguisePageFlag = 0
        self.sosPageFlag = 0
        self.buildingRadar = [0,
         0,
         0,
         0]
        self.fishingRod = 0
        self.fishingTrophies = []
        self.trackArray = []
        self.emoteAccess = [0] * len(TTLocalizer.OL.EmoteFuncDict)
        self.maxBankMoney = ToontownGlobals.DefaultMaxBankMoney
        self.gardenSpecials = []
        self.houseId = 0
        self.houseType = 0
        self.posIndex = 0
        self.savedCheesyEffect = ToontownGlobals.CENormal
        self.savedCheesyHoodId = 0
        self.savedCheesyExpireTime = 0
        self.ghostMode = 0
        self.immortalMode = 0
        self.tempImmortalMode = 0
        self.treasureDamage: bool = False
        self.numPies = 0
        self.pieType = 0
        self.pieTimestamp = 0
        self._isGM = False
        self._gmType = None
        self.hpOwnedByBattle = 0
        if simbase.wantPets:
            self.petTrickPhrases = []
        self.collNodePath = None
        if simbase.wantBingo:
            self.bingoCheat = False
        self.customMessages = []
        self.catalogNotify = ToontownGlobals.NoItems
        self.mailboxNotify = ToontownGlobals.NoItems
        self.catalogScheduleCurrentWeek = 0
        self.catalogScheduleNextTime = 0
        self.monthlyCatalog = CatalogItemList.CatalogItemList()
        self.weeklyCatalog = CatalogItemList.CatalogItemList()
        self.backCatalog = CatalogItemList.CatalogItemList()
        self.onOrder = CatalogItemList.CatalogItemList(store=CatalogItem.Customization | CatalogItem.DeliveryDate)
        self.onGiftOrder = CatalogItemList.CatalogItemList(store=CatalogItem.Customization | CatalogItem.DeliveryDate)
        self.mailboxContents = CatalogItemList.CatalogItemList(store=CatalogItem.Customization)
        self.awardMailboxContents = CatalogItemList.CatalogItemList(store=CatalogItem.Customization)
        self.onAwardOrder = CatalogItemList.CatalogItemList(store=CatalogItem.Customization | CatalogItem.DeliveryDate)
        self.kart = None
        if simbase.wantKarts:
            self.kartDNA = [-1] * getNumFields()
            self.tickets = 200
            self.allowSoloRace = False
            self.allowRaceTimeout = True
        self.setBattleId(0)
        self.gardenStarted = False
        self.flowerCollection = None
        self.shovel = 0
        self.shovelSkill = 0
        self.wateringCan = 0
        self.wateringCanSkill = 0
        self.hatePets = 1
        self.golfHistory = None
        self.golfHoleBest = None
        self.golfCourseBest = None
        self.unlimitedSwing = False
        self.previousAccess = None
        self.numMailItems = 0
        self.simpleMailNotify = ToontownGlobals.NoItems
        self.inviteMailNotify = ToontownGlobals.NoItems
        self.invites = []
        self.hostedParties = []
        self.partiesInvitedTo = []
        self.partyReplyInfoBases = []
        self.modulelist = ModuleListAI.ModuleList()
        self.redeemedCodes = []
        self.emblems = []
        self.unlimitedGags = False
        self.instaKill = False
        self.autoJoin = False
        self.timeouts = {}
        self.kartActive = False
        self.instantDelivery = False
        self.alwaysHitSuits = False
        self.cogsAlwaysMiss = False
        self.cogsAlwaysHit = False
        self.toonDownDamage = False
        self.locked = False
        self.exemption = 0
        self.mutedMinutes = 0
        self.mutedTask = None
        self.cogIndex = ''
        self.charIndex = 0
        self.doodleIndex = 0
        self.goonIndex = 0
        self.propIndex = ''
        self.bossIndex = 0
        self.fishIndex = 0
        self.miscIndex = 0
        self.butterflyIndex: int = 0
        self.streetIndex = 0
        self.petId = 0
        self.run = False
        self.runMultiplier = 1.0
        self.scavengerProgress = {
            ToontownGlobals.WINTER_CAROLING: [0, []],
            ToontownGlobals.WACKY_WINTER_CAROLING: [0, []],
            ToontownGlobals.SPOOKY_TRICK_OR_TREAT: [0, []],
            ToontownGlobals.TRICK_OR_TREAT: [0, []],
        }
        self.gameTickets = 0
        # this next bit stores whether we have completed a certain episode yet on the account
        self.__episodeStatuses = {}
        for epName in EpisodeName2Id.keys():
            self.__episodeStatuses[epName] = False

        self.profileBackground = 0
        self.profileBackgrounds = [0, 1, 2, 3, 4, 5]
        self.profilePose = 0
        self.profilePoses = [0, 1]

        self.nextKnockKnockHeal = 0
        self.numRequestedBldgCogs = 0

    def generate(self):
        DistributedPlayerAI.DistributedPlayerAI.generate(self)
        DistributedSmoothNodeAI.DistributedSmoothNodeAI.generate(self)

    def announceGenerate(self):
        DistributedPlayerAI.DistributedPlayerAI.announceGenerate(self)
        DistributedSmoothNodeAI.DistributedSmoothNodeAI.announceGenerate(self)
        if self.isPlayerControlled():
            messenger.send('avatarEntered', [self])
            self.sendUpdate('setDefaultShard', [self.air.districtId])
            self.accept('archivedPartyDataUpdate', self.__updateArchivedParties)
            self.__updateArchivedParties()
            if self.air.legitMode:
                self.correctLaff()
            self.air.updateOnlineAvatar(self)
            self.air.avatarCountCheck()

    def setLocation(self, parentId, zoneId):
        DistributedPlayerAI.DistributedPlayerAI.setLocation(self, parentId, zoneId)
        if self.isPlayerControlled():
            if hasattr(self, 'air'):
                messenger.send(self.air.getPlayerEnterZoneEventName(zoneId), [self.doId])

            self.sendUpdate('setLastZone', [zoneId])
            if 100 <= zoneId < ToontownGlobals.DynamicZonesBegin:
                hood = ZoneUtil.getHoodId(zoneId)
                self.sendUpdate('setLastHood', [hood])
                self.b_setDefaultZone(hood)

                hoodsVisited = list(self.getHoodsVisited())
                if hood not in hoodsVisited:
                    hoodsVisited.append(hood)
                    self.b_setHoodsVisited(hoodsVisited)

                if zoneId in (ToontownGlobals.OutdoorZone, ToontownGlobals.GoofySpeedway):
                    tpAccess = self.getTeleportAccess()
                    if zoneId not in tpAccess:
                        tpAccess.append(zoneId)
                        self.b_setTeleportAccess(tpAccess)

    def sendDeleteEvent(self):
        if simbase.wantPets:
            isInEstate = self.isInEstate()
            wasInEstate = self.wasInEstate()
            isInPark = self.isInPark()
            wasInPark = self.wasInPark()
            if isInEstate or wasInEstate and hasattr(self, 'estateZones'):
                zones = self.estateZones
            elif isInPark or wasInPark:
                zones = ZoneUtil.getPetParkZones()
            else:
                zones = []
            PetObserve.send(zones, PetObserve.PetActionObserve(PetObserve.Actions.LOGOUT, self.doId))
            if wasInEstate:
                self.cleanupEstateData()
        DistributedAvatarAI.DistributedAvatarAI.sendDeleteEvent(self)

    def delete(self):
        self.notify.debug('----Deleting DistributedToonAI %d ' % self.doId)
        if self.isPlayerControlled():
            messenger.send('avatarExited', [self])
            self.air.removeOnlineAvatar(self)
            self.air.avatarCountCheck()
        if simbase.wantPets:
            if self.isInEstate():
                print('ToonAI - Exit estate toonId:%s' % self.doId)
                self.exitEstate()
            if self.zoneId != ToontownGlobals.QuietZone:
                self.announceZoneChange(ToontownGlobals.QuietZone, self.zoneId)
        taskName = self.uniqueName('cheesy-expires')
        taskMgr.remove(taskName)
        taskName = self.uniqueName('next-catalog')
        taskMgr.remove(taskName)
        taskName = self.uniqueName('next-delivery')
        taskMgr.remove(taskName)
        taskName = self.uniqueName('next-award-delivery')
        taskMgr.remove(taskName)
        taskName = 'next-bothDelivery-%s' % self.doId
        taskMgr.remove(taskName)
        taskName = self.uniqueName('muted-expires')
        taskMgr.remove(taskName)
        self.mutedTask = None
        self.stopToonUp()
        del self.dna
        if self.inventory:
            self.inventory.unload()
        del self.inventory
        del self.experience
        if simbase.wantPets:
            PetLookerAI.PetLookerAI.destroy(self)
        del self.kart
        self.ignore('archivedPartyDataUpdate')
        self._sendExitServerEvent()
        DistributedSmoothNodeAI.DistributedSmoothNodeAI.delete(self)
        DistributedPlayerAI.DistributedPlayerAI.delete(self)

    def deleteDummy(self):
        self.notify.debug('----deleteDummy DistributedToonAI %d ' % self.doId)
        if self.inventory:
            self.inventory.unload()
        del self.inventory
        self.experience = None
        taskName = self.uniqueName('next-catalog')
        taskMgr.remove(taskName)

    def ban(self, comment):
        simbase.air.banManager.ban(self.doId, self.DISLid, comment)

    def disconnect(self):
        self.requestDelete()

    def patchDelete(self):
        del self.dna
        if self.inventory:
            self.inventory.unload()
        del self.inventory
        del self.experience
        if simbase.wantPets:
            PetLookerAI.PetLookerAI.destroy(self)
        self.doNotDeallocateChannel = True
        self.zoneId = None
        DistributedSmoothNodeAI.DistributedSmoothNodeAI.delete(self)
        DistributedPlayerAI.DistributedPlayerAI.delete(self)

    def handleLogicalZoneChange(self, newZoneId, oldZoneId):
        DistributedAvatarAI.DistributedAvatarAI.handleLogicalZoneChange(self, newZoneId, oldZoneId)
        if self.isPlayerControlled():  # and self.WantTpTrack: uncomment to break doodles and micro games
            if self.air.microGameMgr:
                # Don't constantly change the zone if we're running down a street
                try:
                    if oldZoneId is not None:
                        canonicalBranchOldZoneId = ZoneUtil.getCanonicalBranchZone(oldZoneId)
                    else:
                        canonicalBranchOldZoneId = oldZoneId
                    if newZoneId is not None:
                        canonicalBranchNewZoneId = ZoneUtil.getCanonicalBranchZone(newZoneId)
                    else:
                        canonicalBranchNewZoneId = newZoneId
                    if canonicalBranchNewZoneId != canonicalBranchOldZoneId:
                        if oldZoneId is not None:
                            self.air.microGameMgr.toonLeaveOldZone(self.getDoId(), oldZoneId)
                        if newZoneId is not None:
                            self.air.microGameMgr.toonSetNewZone(self.getDoId(), newZoneId)
                    elif newZoneId is not None and ZoneUtil.getToonWhereName(newZoneId) == 'toonInterior':
                        # Special case for interiors because the branch zone calculation
                        # will count them as part of the street or playground but we
                        # don't want that here
                        if oldZoneId is not None:
                            self.air.microGameMgr.toonLeaveOldZone(self.getDoId(), oldZoneId)
                    elif oldZoneId is not None and ZoneUtil.getToonWhereName(oldZoneId) == 'toonInterior':
                        # Special case for interiors because the branch zone calculation
                        # will count them as part of the street or playground but we
                        # don't want that here
                        if newZoneId is not None:
                            self.air.microGameMgr.toonSetNewZone(self.getDoId(), newZoneId)
                except TypeError:
                    pass
            messenger.send(self.staticGetLogicalZoneChangeAllEvent(), [newZoneId, oldZoneId, self])
            self.announceZoneChange(newZoneId, oldZoneId)

    def announceZoneChange(self, newZoneId, oldZoneId):
        from toontown.pets import PetObserve
        broadcastZones = [oldZoneId, newZoneId]
        if self.isInEstate() or self.wasInEstate() and hasattr(self, 'estateZones'):
            broadcastZones.append(self.estateZones)
        elif self.isInPark() or self.wasInPark():
            broadcastZones.append(ZoneUtil.getPetParkZones())
        PetObserve.send(broadcastZones, PetObserve.PetActionObserve(PetObserve.Actions.CHANGE_ZONE, self.doId,
                                                                    (oldZoneId, newZoneId)))

    def checkAccessorySanity(self, accessoryType, idx, textureIdx, colorIdx):
        if idx == 0 and textureIdx == 0 and colorIdx == 0:
            return 1
        if accessoryType == ToonDNA.HAT:
            stylesDict = ToonDNA.HatStyles
            accessoryTypeStr = 'Hat'
        elif accessoryType == ToonDNA.GLASSES:
            stylesDict = ToonDNA.GlassesStyles
            accessoryTypeStr = 'Glasses'
        elif accessoryType == ToonDNA.BACKPACK:
            stylesDict = ToonDNA.BackpackStyles
            accessoryTypeStr = 'Backpack'
        elif accessoryType == ToonDNA.SHOES:
            stylesDict = ToonDNA.ShoesStyles
            accessoryTypeStr = 'Shoes'
        else:
            return 0
        try:
            styleStr = list(stylesDict.keys())[list(stylesDict.values()).index([idx, textureIdx, colorIdx])]
            accessoryItemId = 0
            for itemId in list(CatalogAccessoryItem.AccessoryTypes.keys()):
                if styleStr == CatalogAccessoryItem.AccessoryTypes[itemId][CatalogAccessoryItem.ATString]:
                    accessoryItemId = itemId
                    break

            if accessoryItemId == 0:
                self.air.writeServerEvent('suspicious', self.doId, 'Toon tried to wear invalid %s %d %d %d' % (accessoryTypeStr,
                 idx,
                 textureIdx,
                 colorIdx))
                return 0
            if not simbase.config.GetBool('want-check-accessory-sanity', False):
                return 1
            accessoryItem = CatalogAccessoryItem.CatalogAccessoryItem(accessoryItemId)
            result = self.air.catalogManager.isItemReleased(accessoryItem)
            if result == 0:
                self.air.writeServerEvent('suspicious', self.doId, 'Toon wore unreleased accessoryItem %d' % accessoryItemId)
            return result
        except:
            self.air.writeServerEvent('suspicious', self.doId, 'Toon tried to wear invalid %s %d %d %d' % (accessoryTypeStr,
             idx,
             textureIdx,
             colorIdx))
            return 0

    def b_setHat(self, idx, textureIdx, colorIdx):
        self.d_setHat(idx, textureIdx, colorIdx)
        self.setHat(idx, textureIdx, colorIdx)

    def d_setHat(self, idx, textureIdx, colorIdx):
        if not self.checkAccessorySanity(ToonDNA.HAT, idx, textureIdx, colorIdx):
            pass
        self.sendUpdate('setHat', [idx, textureIdx, colorIdx])

    def setHat(self, idx, textureIdx, colorIdx):
        if not self.checkAccessorySanity(ToonDNA.HAT, idx, textureIdx, colorIdx):
            pass
        self.hat = (idx, textureIdx, colorIdx)

    def getHat(self):
        return self.hat

    def b_setGlasses(self, idx, textureIdx, colorIdx):
        self.d_setGlasses(idx, textureIdx, colorIdx)
        self.setGlasses(idx, textureIdx, colorIdx)

    def d_setGlasses(self, idx, textureIdx, colorIdx):
        if not self.checkAccessorySanity(ToonDNA.GLASSES, idx, textureIdx, colorIdx):
            pass
        self.sendUpdate('setGlasses', [idx, textureIdx, colorIdx])

    def setGlasses(self, idx, textureIdx, colorIdx):
        if not self.checkAccessorySanity(ToonDNA.GLASSES, idx, textureIdx, colorIdx):
            pass
        self.glasses = (idx, textureIdx, colorIdx)

    def getGlasses(self):
        return self.glasses

    def b_setBackpack(self, idx, textureIdx, colorIdx):
        self.d_setBackpack(idx, textureIdx, colorIdx)
        self.setBackpack(idx, textureIdx, colorIdx)

    def d_setBackpack(self, idx, textureIdx, colorIdx):
        if not self.checkAccessorySanity(ToonDNA.BACKPACK, idx, textureIdx, colorIdx):
            pass
        self.sendUpdate('setBackpack', [idx, textureIdx, colorIdx])

    def setBackpack(self, idx, textureIdx, colorIdx):
        if not self.checkAccessorySanity(ToonDNA.BACKPACK, idx, textureIdx, colorIdx):
            pass
        self.backpack = (idx, textureIdx, colorIdx)

    def getBackpack(self):
        return self.backpack

    def b_setShoes(self, idx, textureIdx, colorIdx):
        self.d_setShoes(idx, textureIdx, colorIdx)
        self.setShoes(idx, textureIdx, colorIdx)

    def d_setShoes(self, idx, textureIdx, colorIdx):
        if not self.checkAccessorySanity(ToonDNA.SHOES, idx, textureIdx, colorIdx):
            pass
        self.sendUpdate('setShoes', [idx, textureIdx, colorIdx])

    def setShoes(self, idx, textureIdx, colorIdx):
        if not self.checkAccessorySanity(ToonDNA.SHOES, idx, textureIdx, colorIdx):
            pass
        self.shoes = (idx, textureIdx, colorIdx)

    def getShoes(self):
        return self.shoes

    def updateDNA(self, newDNA, spellbook):
        self.b_setDNAString(newDNA)
        dna = ToonDNA.ToonDNA()
        dna.makeFromNetString(newDNA)

        if spellbook:
            if len(dna.torso) == 1:
                self.d_setSystemMessage(0, "Clothing removed successfully!")
            else:
                self.d_setSystemMessage(0, "Clothing changed successfully!")

    def updateHeadAccessories(self, h1, h2, g1, g2):
        self.b_setHat(h1, h2, 0)
        self.b_setGlasses(g1, g2, 0)
        self.d_setSystemMessage(0, "Hat and glasses changed successfully!")
        self.air.updateOnlineAvatar(self)

    def updateBodyAccessories(self, b1, b2, s1, s2):
        self.b_setBackpack(b1, b2, 0)
        self.b_setShoes(s1, s2, 0)
        self.d_setSystemMessage(0, "Backpack and shoes changed successfully!")
        self.air.updateOnlineAvatar(self)

    def b_setDNAString(self, string):
        self.d_setDNAString(string)
        self.setDNAString(string)
        self.air.updateOnlineAvatar(self)

    def d_setDNAString(self, string):
        self.sendUpdate('setDNAString', [string])

    def setDNAString(self, string):
        self.dna.makeFromNetString(string)

    def getDNAString(self):
        return self.dna.makeNetString()

    def getStyle(self):
        return self.dna

    def b_setExperience(self, experience):
        self.d_setExperience(experience)
        self.setExperience(experience)

    def d_setExperience(self, experience):
        self.sendUpdate('setExperience', [experience])

    def setExperience(self, experience):
        self.experience = Experience.Experience(experience, self)

    def getExperience(self):
        return self.experience.makeNetString()

    def b_setInventory(self, inventory):
        self.setInventory(inventory)
        self.d_setInventory(self.getInventory())

    def d_setInventory(self, inventory):
        self.sendUpdate('setInventory', [inventory])

    def setInventory(self, inventoryNetString):
        if self.inventory:
            self.inventory.updateInvString(inventoryNetString)
        else:
            self.inventory = InventoryBase.InventoryBase(self, inventoryNetString)
        emptyInv = InventoryBase.InventoryBase(self)
        emptyString = emptyInv.makeNetString()
        lengthMatch = len(inventoryNetString) - len(emptyString)
        if lengthMatch != 0:
            if len(inventoryNetString) == 42:
                oldTracks = 7
                oldLevels = 6
            elif len(inventoryNetString) == 49:
                oldTracks = 7
                oldLevels = 7
            else:
                oldTracks = 0
                oldLevels = 0
            if oldTracks == 0 and oldLevels == 0:
                self.notify.warning('reseting invalid inventory to MAX on toon: %s' % self.doId)
                self.inventory.zeroInv()
                self.inventory.maxOutInv(1, 1)
            else:
                newInventory = InventoryBase.InventoryBase(self)
                oldList = emptyInv.makeFromNetStringForceSize(inventoryNetString, oldTracks, oldLevels)
                for indexTrack in range(0, oldTracks):
                    for indexGag in range(0, oldLevels):
                        newInventory.addItems(indexTrack, indexGag, oldList[indexTrack][indexGag])

                self.inventory.unload()
                self.inventory = newInventory
            self.d_setInventory(self.getInventory())

    def getInventory(self):
        return self.inventory.makeNetString()

    def doRestock(self, noUber = 1, noPaid = 1):
        self.inventory.zeroInv()
        self.inventory.maxOutInv(noUber, noPaid)
        self.d_setInventory(self.inventory.makeNetString())

    def setDefaultShard(self, shard):
        self.defaultShard = shard
        self.notify.debug('setting default shard to %s' % shard)

    def getDefaultShard(self):
        return self.defaultShard

    def setDefaultZone(self, zone):
        self.defaultZone = zone
        self.notify.debug('setting default zone to %s' % zone)

    def d_setDefaultZone(self, zone):
        self.sendUpdate('setDefaultZone', [zone])

    def b_setDefaultZone(self, zone):
        self.setDefaultZone(zone)
        self.d_setDefaultZone(zone)

    def getDefaultZone(self):
        return self.defaultZone

    def setShtickerBook(self, string):
        self.notify.debug('setting shticker book to %s' % string)

    def getShtickerBook(self):
        return ''

    def d_setFriendsList(self, friendsList):
        self.sendUpdate('setFriendsList', [friendsList])
        return None

    def setFriendsList(self, friendsList):
        self.notify.debug('setting friends list to %s' % self.friendsList)
        self.friendsList = friendsList
        if friendsList:
            friendId = friendsList[-1]
            otherAv = self.air.doId2do.get(friendId)
            self.air.questManager.toonMadeFriend(self, otherAv)

    def getFriendsList(self):
        return self.friendsList

    def extendFriendsList(self, friendId, friendCode):
        for i in range(len(self.friendsList)):
            friendPair = self.friendsList[i]
            if friendPair[0] == friendId:
                self.friendsList[i] = (friendId, friendCode)
                return

        self.friendsList.append((friendId, friendCode))

    def d_setMaxNPCFriends(self, max):
        self.sendUpdate('setMaxNPCFriends', [max])

    def setMaxNPCFriends(self, max):
        if max & 32768:
            self.b_setSosPageFlag(1)
            max &= 32767
        configMax = simbase.config.GetInt('max-sos-cards', 16)
        if configMax != max:
            if self.sosPageFlag == 0:
                self.b_setMaxNPCFriends(configMax)
            else:
                self.b_setMaxNPCFriends(configMax | 32768)
        else:
            self.maxNPCFriends = max
        if self.maxNPCFriends != 8 and self.maxNPCFriends != 16:
            self.notify.warning('Wrong max SOS cards %s, %d' % (self.maxNPCFriends, self.doId))

    def b_setMaxNPCFriends(self, max):
        self.setMaxNPCFriends(max)
        self.d_setMaxNPCFriends(max)

    def getMaxNPCFriends(self):
        return self.maxNPCFriends

    def getBattleId(self):
        if self.battleId >= 0:
            return self.battleId
        else:
            return 0

    def b_setBattleId(self, battleId):
        self.setBattleId(battleId)
        self.d_setBattleId(battleId)

    def d_setBattleId(self, battleId):
        if self.battleId >= 0:
            self.sendUpdate('setBattleId', [battleId])
        else:
            self.sendUpdate('setBattleId', [0])

    def setBattleId(self, battleId):
        self.battleId = battleId

    def d_setNPCFriendsDict(self, NPCFriendsDict):
        NPCFriendsList = []
        for friend in list(NPCFriendsDict.keys()):
            NPCFriendsList.append((friend, NPCFriendsDict[friend]))

        self.sendUpdate('setNPCFriendsDict', [NPCFriendsList])
        return None

    def setNPCFriendsDict(self, NPCFriendsList):
        self.NPCFriendsDict = {}
        for friendPair in NPCFriendsList:
            # Remove invalid NPCs
            if friendPair[0] not in NPCToons.npcFriends:
                continue
            self.NPCFriendsDict[friendPair[0]] = friendPair[1]

        self.notify.debug('setting NPC friends dict to %s' % self.NPCFriendsDict)

    def getNPCFriendsDict(self):
        return self.NPCFriendsDict

    def b_setNPCFriendsDict(self, NPCFriendsList):
        self.setNPCFriendsDict(NPCFriendsList)
        self.d_setNPCFriendsDict(self.NPCFriendsDict)

    def attemptAddNPCFriend(self, npcFriend, numCalls = 1):
        if numCalls <= 0:
            self.notify.warning('invalid numCalls: %d' % numCalls)
            return 0
        if npcFriend in self.NPCFriendsDict:
            self.NPCFriendsDict[npcFriend] += numCalls
        elif npcFriend in npcFriends:
            if len(list(self.NPCFriendsDict.keys())) >= self.maxNPCFriends:
                return 0
            self.NPCFriendsDict[npcFriend] = numCalls
        else:
            self.notify.warning('invalid NPC: %d' % npcFriend)
            return 0
        if self.NPCFriendsDict[npcFriend] > self.maxCallsPerNPC:
            self.NPCFriendsDict[npcFriend] = self.maxCallsPerNPC
        self.d_setNPCFriendsDict(self.NPCFriendsDict)
        if self.sosPageFlag == 0:
            self.b_setMaxNPCFriends(self.maxNPCFriends | 32768)
        return 1

    def attemptSubtractNPCFriend(self, npcFriend):
        if npcFriend not in self.NPCFriendsDict:
            self.notify.warning('attemptSubtractNPCFriend: invalid NPC %s' % npcFriend)
            return 0
        if hasattr(self, 'autoRestockSOS') and self.autoRestockSOS:
            cost = 0
        else:
            cost = 1
        self.NPCFriendsDict[npcFriend] -= cost
        if self.NPCFriendsDict[npcFriend] <= 0:
            del self.NPCFriendsDict[npcFriend]
        self.d_setNPCFriendsDict(self.NPCFriendsDict)
        return 1

    def d_setMaxAccessories(self, max):
        self.sendUpdate('setMaxAccessories', [self.maxAccessories])

    def setMaxAccessories(self, max):
        self.maxAccessories = max

    def b_setMaxAccessories(self, max):
        self.setMaxAccessories(max)
        self.d_setMaxAccessories(max)

    def getMaxAccessories(self):
        return self.maxAccessories

    def isTrunkFull(self, extraAccessories = 0):
        numAccessories = (len(self.hatList) + len(self.glassesList) + len(self.backpackList) + len(self.shoesList)) / 3
        return numAccessories + extraAccessories >= self.maxAccessories

    def d_setHatList(self, clothesList):
        self.sendUpdate('setHatList', [clothesList])
        return None

    def setHatList(self, clothesList):
        self.hatList = clothesList

    def b_setHatList(self, clothesList):
        self.setHatList(clothesList)
        self.d_setHatList(clothesList)

    def getHatList(self):
        return self.hatList

    def d_setGlassesList(self, clothesList):
        self.sendUpdate('setGlassesList', [clothesList])
        return None

    def setGlassesList(self, clothesList):
        self.glassesList = clothesList

    def b_setGlassesList(self, clothesList):
        self.setGlassesList(clothesList)
        self.d_setGlassesList(clothesList)

    def getGlassesList(self):
        return self.glassesList

    def d_setBackpackList(self, clothesList):
        self.sendUpdate('setBackpackList', [clothesList])
        return None

    def setBackpackList(self, clothesList):
        self.backpackList = clothesList

    def b_setBackpackList(self, clothesList):
        self.setBackpackList(clothesList)
        self.d_setBackpackList(clothesList)

    def getBackpackList(self):
        return self.backpackList

    def d_setShoesList(self, clothesList):
        self.sendUpdate('setShoesList', [clothesList])
        return None

    def setShoesList(self, clothesList):
        self.shoesList = clothesList

    def b_setShoesList(self, clothesList):
        self.setShoesList(clothesList)
        self.d_setShoesList(clothesList)

    def getShoesList(self):
        return self.shoesList

    def addToAccessoriesList(self, accessoryType, geomIdx, texIdx, colorIdx):
        if self.isTrunkFull():
            return 0
        if accessoryType == ToonDNA.HAT:
            itemList = self.hatList
        elif accessoryType == ToonDNA.GLASSES:
            itemList = self.glassesList
        elif accessoryType == ToonDNA.BACKPACK:
            itemList = self.backpackList
        elif accessoryType == ToonDNA.SHOES:
            itemList = self.shoesList
        else:
            return 0
        index = 0
        for i in range(0, len(itemList), 3):
            if itemList[i] == geomIdx and itemList[i + 1] == texIdx and itemList[i + 2] == colorIdx:
                return 0

        if accessoryType == ToonDNA.HAT:
            self.hatList.append(geomIdx)
            self.hatList.append(texIdx)
            self.hatList.append(colorIdx)
        elif accessoryType == ToonDNA.GLASSES:
            self.glassesList.append(geomIdx)
            self.glassesList.append(texIdx)
            self.glassesList.append(colorIdx)
        elif accessoryType == ToonDNA.BACKPACK:
            self.backpackList.append(geomIdx)
            self.backpackList.append(texIdx)
            self.backpackList.append(colorIdx)
        elif accessoryType == ToonDNA.SHOES:
            self.shoesList.append(geomIdx)
            self.shoesList.append(texIdx)
            self.shoesList.append(colorIdx)
        return 1

    def replaceItemInAccessoriesList(self, accessoryType, geomIdxA, texIdxA, colorIdxA, geomIdxB, texIdxB, colorIdxB):
        if accessoryType == ToonDNA.HAT:
            itemList = self.hatList
        elif accessoryType == ToonDNA.GLASSES:
            itemList = self.glassesList
        elif accessoryType == ToonDNA.BACKPACK:
            itemList = self.backpackList
        elif accessoryType == ToonDNA.SHOES:
            itemList = self.shoesList
        else:
            return 0
        index = 0
        for i in range(0, len(itemList), 3):
            if itemList[i] == geomIdxA and itemList[i + 1] == texIdxA and itemList[i + 2] == colorIdxA:
                if accessoryType == ToonDNA.HAT:
                    self.hatList[i] = geomIdxB
                    self.hatList[i + 1] = texIdxB
                    self.hatList[i + 2] = colorIdxB
                elif accessoryType == ToonDNA.GLASSES:
                    self.glassesList[i] = geomIdxB
                    self.glassesList[i + 1] = texIdxB
                    self.glassesList[i + 2] = colorIdxB
                elif accessoryType == ToonDNA.BACKPACK:
                    self.backpackList[i] = geomIdxB
                    self.backpackList[i + 1] = texIdxB
                    self.backpackList[i + 2] = colorIdxB
                else:
                    self.shoesList[i] = geomIdxB
                    self.shoesList[i + 1] = texIdxB
                    self.shoesList[i + 2] = colorIdxB
                return 1

        return 0

    def hasAccessory(self, accessoryType, geomIdx, texIdx, colorIdx):
        if accessoryType == ToonDNA.HAT:
            itemList = self.hatList
            cur = self.hat
        elif accessoryType == ToonDNA.GLASSES:
            itemList = self.glassesList
            cur = self.glasses
        elif accessoryType == ToonDNA.BACKPACK:
            itemList = self.backpackList
            cur = self.backpack
        elif accessoryType == ToonDNA.SHOES:
            itemList = self.shoesList
            cur = self.shoes
        else:
            raise 'invalid accessory type %s' % accessoryType
        if cur == (geomIdx, texIdx, colorIdx):
            return True
        for i in range(0, len(itemList), 3):
            if itemList[i] == geomIdx and itemList[i + 1] == texIdx and itemList[i + 2] == colorIdx:
                return True

        return False

    def isValidAccessorySetting(self, accessoryType, geomIdx, texIdx, colorIdx):
        if not geomIdx and not texIdx and not colorIdx:
            return True
        return self.hasAccessory(accessoryType, geomIdx, texIdx, colorIdx)

    def removeItemInAccessoriesList(self, accessoryType, geomIdx, texIdx, colorIdx):
        if accessoryType == ToonDNA.HAT:
            itemList = self.hatList
        elif accessoryType == ToonDNA.GLASSES:
            itemList = self.glassesList
        elif accessoryType == ToonDNA.BACKPACK:
            itemList = self.backpackList
        elif accessoryType == ToonDNA.SHOES:
            itemList = self.shoesList
        else:
            return 0
        listLen = len(itemList)
        if listLen < 3:
            self.notify.warning('Accessory list is not long enough to delete anything')
            return 0
        index = 0
        for i in range(0, len(itemList), 3):
            if itemList[i] == geomIdx and itemList[i + 1] == texIdx and itemList[i + 2] == colorIdx:
                itemList = itemList[0:i] + itemList[i + 3:listLen]
                if accessoryType == ToonDNA.HAT:
                    self.hatList = itemList[:]
                    styles = ToonDNA.HatStyles
                    descDict = TTLocalizer.HatStylesDescriptions
                elif accessoryType == ToonDNA.GLASSES:
                    self.glassesList = itemList[:]
                    styles = ToonDNA.GlassesStyles
                    descDict = TTLocalizer.GlassesStylesDescriptions
                elif accessoryType == ToonDNA.BACKPACK:
                    self.backpackList = itemList[:]
                    styles = ToonDNA.BackpackStyles
                    descDict = TTLocalizer.BackpackStylesDescriptions
                elif accessoryType == ToonDNA.SHOES:
                    self.shoesList = itemList[:]
                    styles = ToonDNA.ShoesStyles
                    descDict = TTLocalizer.ShoesStylesDescriptions
                styleName = 'none'
                for style in list(styles.items()):
                    if style[1] == [geomIdx, texIdx, colorIdx]:
                        styleName = style[0]
                        break

                if styleName == 'none' or styleName not in descDict:
                    self.air.writeServerEvent('suspicious', self.doId, ' tried to remove wrong accessory code %d %d %d' % (geomIdx, texIdx, colorIdx))
                else:
                    self.air.writeServerEvent('accessory', self.doId, ' removed accessory %s' % descDict[styleName])
                return 1

        return 0

    def d_setMaxClothes(self, max):
        self.sendUpdate('setMaxClothes', [self.maxClothes])

    def setMaxClothes(self, max):
        self.maxClothes = max

    def b_setMaxClothes(self, max):
        self.setMaxClothes(max)
        self.d_setMaxClothes(max)

    def getMaxClothes(self):
        return self.maxClothes

    """ New Closet Stuff """
    def d_setClosetShirts(self, shirts: List[TShirt]):
        self.sendUpdate('setClosetShirts', [shirts])

    def setClosetShirts(self, shirts: List[TShirt]):
        self.closetShirts = shirts

    def b_setClosetShirts(self, shirts: List[TShirt]):
        self.setClosetShirts(shirts)
        self.d_setClosetShirts(shirts)

    def getClosetShirts(self) -> List[TShirt]:
        return self.closetShirts

    def d_setClosetBottoms(self, bottoms: List[TBottom]):
        self.sendUpdate('setClosetBottoms', [bottoms])

    def setClosetBottoms(self, bottoms: List[TBottom]):
        self.closetBottoms = bottoms

    def b_setClosetBottoms(self, bottoms: List[TBottom]):
        self.setClosetBottoms(bottoms)
        self.d_setClosetBottoms(bottoms)

    def getClosetBottoms(self) -> List[TBottom]:
        return self.closetBottoms

    def isClosetFull(self, extraClothes = 0) -> bool:
        numClothes = len(self.closetShirts) + len(self.closetBottoms)
        return numClothes + extraClothes >= self.maxClothes

    def addShirtToCloset(self, shirt: TShirt) -> bool:
        if self.isClosetFull() or shirt in self.getClosetShirts():
            return False
        self.closetShirts.append(shirt)
        return True

    def removeShirtFromCloset(self, shirt: TShirt) -> bool:
        if shirt in self.getClosetShirts():
            del self.closetShirts[self.closetShirts.index(shirt)]
            return True
        return False

    def replaceShirtFromCloset(self, inShirt: TShirt, outShirt: TShirt) -> bool:
        if inShirt not in self.getClosetShirts():
            return False

        self.removeShirtFromCloset(inShirt)
        self.addShirtToCloset(outShirt)
        return True

    def addBottomsToCloset(self, bottom: TBottom) -> bool:
        if self.isClosetFull() or bottom in self.getClosetBottoms():
            return False
        self.closetBottoms.append(bottom)
        return True

    def removeBottomsFromCloset(self, bottom: TBottom) -> bool:
        if bottom in self.getClosetBottoms():
            del self.closetBottoms[self.closetBottoms.index(bottom)]
            return True
        return False

    def replaceBottomsFromCloset(self, inBottoms: TBottom, outBottoms: TBottom) -> bool:
        if inBottoms not in self.getClosetBottoms():
            return False
        self.removeBottomsFromCloset(inBottoms)
        self.addBottomsToCloset(outBottoms)
        return True

    """ Old Closet Stuff TODO: Deprecate """
    def d_setClothesTopsList(self, clothesList):
        self.sendUpdate('setClothesTopsList', [clothesList])
        return None

    def setClothesTopsList(self, clothesList):
        self.clothesTopsList = clothesList

    def b_setClothesTopsList(self, clothesList):
        self.setClothesTopsList(clothesList)
        self.d_setClothesTopsList(clothesList)

    def getClothesTopsList(self):
        return self.clothesTopsList

    def addToClothesTopsList(self, topTex, topTexColor, sleeveTex, sleeveTexColor):
        if self.isClosetFull():
            return 0
        index = 0
        for i in range(0, len(self.clothesTopsList), 4):
            if self.clothesTopsList[i] == topTex and self.clothesTopsList[i + 1] == topTexColor and self.clothesTopsList[i + 2] == sleeveTex and self.clothesTopsList[i + 3] == sleeveTexColor:
                return 0

        self.clothesTopsList.append(topTex)
        self.clothesTopsList.append(topTexColor)
        self.clothesTopsList.append(sleeveTex)
        self.clothesTopsList.append(sleeveTexColor)
        return 1

    def replaceItemInClothesTopsList(self, topTexA, topTexColorA, sleeveTexA, sleeveTexColorA, topTexB, topTexColorB, sleeveTexB, sleeveTexColorB):
        index = 0
        for i in range(0, len(self.clothesTopsList), 4):
            if self.clothesTopsList[i] == topTexA and self.clothesTopsList[i + 1] == topTexColorA and self.clothesTopsList[i + 2] == sleeveTexA and self.clothesTopsList[i + 3] == sleeveTexColorA:
                self.clothesTopsList[i] = topTexB
                self.clothesTopsList[i + 1] = topTexColorB
                self.clothesTopsList[i + 2] = sleeveTexB
                self.clothesTopsList[i + 3] = sleeveTexColorB
                return 1

        return 0

    def removeItemInClothesTopsList(self, topTex, topTexColor, sleeveTex, sleeveTexColor):
        listLen = len(self.clothesTopsList)
        if listLen < 4:
            self.notify.warning('Clothes top list is not long enough to delete anything')
            return 0
        index = 0
        for i in range(0, listLen, 4):
            if self.clothesTopsList[i] == topTex and self.clothesTopsList[i + 1] == topTexColor and self.clothesTopsList[i + 2] == sleeveTex and self.clothesTopsList[i + 3] == sleeveTexColor:
                self.clothesTopsList = self.clothesTopsList[0:i] + self.clothesTopsList[i + 4:listLen]
                return 1

        return 0

    def d_setClothesBottomsList(self, clothesList):
        self.sendUpdate('setClothesBottomsList', [clothesList])
        return None

    def setClothesBottomsList(self, clothesList):
        self.clothesBottomsList = clothesList

    def b_setClothesBottomsList(self, clothesList):
        self.setClothesBottomsList(clothesList)
        self.d_setClothesBottomsList(clothesList)

    def getClothesBottomsList(self):
        return self.clothesBottomsList

    def addToClothesBottomsList(self, botTex, botTexColor):
        if self.isClosetFull():
            self.notify.warning('clothes bottoms list is full')
            return 0
        index = 0
        for i in range(0, len(self.clothesBottomsList), 2):
            if self.clothesBottomsList[i] == botTex and self.clothesBottomsList[i + 1] == botTexColor:
                return 0

        self.clothesBottomsList.append(botTex)
        self.clothesBottomsList.append(botTexColor)
        return 1

    def replaceItemInClothesBottomsList(self, botTexA, botTexColorA, botTexB, botTexColorB):
        index = 0
        for i in range(0, len(self.clothesBottomsList), 2):
            if self.clothesBottomsList[i] == botTexA and self.clothesBottomsList[i + 1] == botTexColorA:
                self.clothesBottomsList[i] = botTexB
                self.clothesBottomsList[i + 1] = botTexColorB
                return 1

        return 0

    def removeItemInClothesBottomsList(self, botTex, botTexColor):
        listLen = len(self.clothesBottomsList)
        if listLen < 2:
            self.notify.warning('Clothes bottoms list is not long enough to delete anything')
            return 0
        index = 0
        for i in range(0, len(self.clothesBottomsList), 2):
            if self.clothesBottomsList[i] == botTex and self.clothesBottomsList[i + 1] == botTexColor:
                self.clothesBottomsList = self.clothesBottomsList[0:i] + self.clothesBottomsList[i + 2:listLen]
                return 1

        return 0

    def d_catalogGenClothes(self):
        self.sendUpdate('catalogGenClothes', [self.doId])

    def d_catalogGenAccessories(self):
        self.sendUpdate('catalogGenAccessories', [self.doId])

    def getRedeemedCodes(self):
        return self.redeemedCodes

    def setRedeemedCodes(self, redeemedCodes):
        self.redeemedCodes = redeemedCodes

    def b_setRedeemedCodes(self, redeemedCodes):
        self.setRedeemedCodes(redeemedCodes)
        self.d_setRedeemedCodes(redeemedCodes)

    def d_setRedeemedCodes(self, redeemedCodes):
        self.sendUpdate('setRedeemedCodes', [redeemedCodes])

    def b_setHp(self, hp):
        if hp <= 5 and self.getKartActive():
            if self.kart:
                self.kart.requestDelete()
                self.kart = None

            self.b_setKartActive(False)
        DistributedAvatarAI.DistributedAvatarAI.b_setHp(self, hp)

    def takeDamage(self, hpLost, quietly = 0, sendTotal = 1):
        if not (self.immortalMode or self.tempImmortalMode):
            if not quietly:
                self.sendUpdate('takeDamage', [hpLost])
            if hpLost > 0 and self.hp > 0:
                self.hp -= hpLost
                if self.hp <= 0:
                    self.hp = -1
                    messenger.send(self.getGoneSadMessage())
        if not self.hpOwnedByBattle:
            self.hp = min(self.hp, self.maxHp)
            if self.hp <= 5 and self.getKartActive():
                if self.kart:
                    self.kart.requestDelete()
                    self.kart = None

                self.b_setKartActive(False)
            if sendTotal:
                self.d_setHp(self.hp)

    @staticmethod
    def getGoneSadMessageForAvId(avId):
        return 'goneSad-%s' % avId

    def getGoneSadMessage(self):
        return self.getGoneSadMessageForAvId(self.doId)

    def setHp(self, hp):
        DistributedPlayerAI.DistributedPlayerAI.setHp(self, hp)
        if hp <= 0:
            messenger.send(self.getGoneSadMessage())

    def b_setLaffMeterTextColor(self, r, g, b):
        self.d_setLaffMeterTextColor(r, g, b)
        self.setLaffMeterTextColor(r, g, b)

    def d_setLaffMeterTextColor(self, r, g, b):
        self.sendUpdate('setLaffMeterTextColor', [r, g ,b])

    def setLaffMeterTextColor(self, r, g, b):
        self.laffMeterTextColor = (r, g, b)

    def getLaffMeterTextColor(self):
        return self.self.laffMeterTextColor

    def b_setTutorialAck(self, tutorialAck):
        self.d_setTutorialAck(tutorialAck)
        self.setTutorialAck(tutorialAck)

    def d_setTutorialAck(self, tutorialAck):
        self.sendUpdate('setTutorialAck', [tutorialAck])

    def setTutorialAck(self, tutorialAck):
        self.tutorialAck = tutorialAck

    def getTutorialAck(self):
        return self.tutorialAck

    def d_setEarnedExperience(self, earnedExp):
        self.sendUpdate('setEarnedExperience', [earnedExp])

    def setInterface(self, string):
        self.notify.debug('setting interface to %s' % string)

    def getInterface(self):
        return ''

    def setZonesVisited(self, hoods):
        self.safeZonesVisited = hoods
        self.notify.debug('setting safe zone list to %s' % self.safeZonesVisited)

    def getZonesVisited(self):
        return self.safeZonesVisited

    def setHoodsVisited(self, hoods):
        self.hoodsVisited = hoods
        self.notify.debug('setting hood zone list to %s' % self.hoodsVisited)

    def getHoodsVisited(self):
        return self.hoodsVisited

    def setLastHood(self, hood):
        self.lastHood = hood

    def getLastHood(self):
        return self.lastHood

    def setLastZone(self, zone):
        self.lastZone = zone

    def getLastZone(self):
        return self.lastZone

    def b_setAnimState(self, animName, animMultiplier):
        self.setAnimState(animName, animMultiplier)
        self.d_setAnimState(animName, animMultiplier)

    def d_setAnimState(self, animName, animMultiplier):
        timestamp = globalClockDelta.getRealNetworkTime()
        self.sendUpdate('setAnimState', [animName, animMultiplier, timestamp])
        return None

    def setAnimState(self, animName, animMultiplier, timestamp = 0):
        if animName not in ToontownGlobals.ToonAnimStates:
            desc = 'tried to set invalid animState: %s' % (animName,)
            self.air.writeServerEvent('suspicious', self.doId, desc)
            return
        self.animName = animName
        self.animMultiplier = animMultiplier

    def b_setCogStatus(self, cogStatusList):
        self.setCogStatus(cogStatusList)
        self.d_setCogStatus(cogStatusList)

    def setCogStatus(self, cogStatusList):
        self.notify.debug('setting cogs to %s' % cogStatusList)
        self.cogs = cogStatusList

    def d_setCogStatus(self, cogStatusList):
        self.sendUpdate('setCogStatus', [cogStatusList])

    def getCogStatus(self):
        return self.cogs

    def b_setCogCount(self, cogCountList):
        self.setCogCount(cogCountList)
        self.d_setCogCount(cogCountList)

    def setCogCount(self, cogCountList):
        self.notify.debug('setting cogCounts to %s' % cogCountList)
        self.cogCounts = cogCountList

    def d_setCogCount(self, cogCountList):
        self.sendUpdate('setCogCount', [cogCountList])

    def getCogCount(self):
        return self.cogCounts

    def b_setCogRadar(self, radar):
        self.setCogRadar(radar)
        self.d_setCogRadar(radar)

    def setCogRadar(self, radar):
        if not radar:
            self.notify.warning('cogRadar set to bad value: %s. Resetting to [0,0,0,0]' % radar)
            self.cogRadar = [0,
             0,
             0,
             0]
        else:
            self.cogRadar = radar

    def d_setCogRadar(self, radar):
        self.sendUpdate('setCogRadar', [radar])

    def getCogRadar(self):
        return self.cogRadar

    def b_setBuildingRadar(self, radar):
        self.setBuildingRadar(radar)
        self.d_setBuildingRadar(radar)

    def setBuildingRadar(self, radar):
        if not radar:
            self.notify.warning('buildingRadar set to bad value: %s. Resetting to [0,0,0,0]' % radar)
            self.buildingRadar = [0,
             0,
             0,
             0]
        else:
            self.buildingRadar = radar

    def d_setBuildingRadar(self, radar):
        self.sendUpdate('setBuildingRadar', [radar])

    def getBuildingRadar(self):
        return self.buildingRadar

    def b_setCogTypes(self, types):
        self.setCogTypes(types)
        self.d_setCogTypes(types)

    def setCogTypes(self, types):
        if not types:
            self.notify.warning('cogTypes set to bad value: %s. Resetting to [0,0,0,0]' % types)
            self.cogTypes = [0,
             0,
             0,
             0]
        else:
            self.cogTypes = types

    def d_setCogTypes(self, types):
        self.sendUpdate('setCogTypes', [types])

    def getCogTypes(self):
        return self.cogTypes

    def b_setCogLevels(self, levels):
        self.setCogLevels(levels)
        self.d_setCogLevels(levels)

    def setCogLevels(self, levels):
        if not levels:
            self.notify.warning('cogLevels set to bad value: %s. Resetting to [0,0,0,0]' % levels)
            self.cogLevels = [0,
             0,
             0,
             0]
        else:
            self.cogLevels = levels

    def d_setCogLevels(self, levels):
        self.sendUpdate('setCogLevels', [levels])

    def getCogLevels(self):
        return self.cogLevels

    def incCogLevel(self, dept):
        newLevel = self.cogLevels[dept] + 1
        lastCog = self.cogTypes[dept] >= SuitDNA.suitsPerDept - 1
        if not lastCog:
            maxLevel = self.cogTypes[dept] + 4
        else:
            maxLevel = ToontownGlobals.MaxCogSuitLevel
        if newLevel > maxLevel:
            if not lastCog:
                self.cogTypes[dept] += 1
                self.d_setCogTypes(self.cogTypes)
                self.cogLevels[dept] = self.cogTypes[dept]
                self.d_setCogLevels(self.cogLevels)
        else:
            self.cogLevels[dept] += 1
            self.d_setCogLevels(self.cogLevels)
            if lastCog:
                if self.cogLevels[dept] in ToontownGlobals.CogSuitHPLevels:
                    maxHp = self.getMaxHp()
                    maxHp = min(ToontownGlobals.MaxHpLimit, maxHp + 1)
                    self.b_setMaxHp(maxHp)
                    self.toonUp(maxHp)
        self.air.writeServerEvent('cogSuit', self.doId, '%s|%s|%s' % (dept, self.cogTypes[dept], self.cogLevels[dept]))

    def getNumPromotions(self, dept):
        if dept not in SuitDNA.suitDepts:
            self.notify.warning('getNumPromotions: Invalid parameter dept=%s' % dept)
            return 0
        deptIndex = SuitDNA.suitDepts.index(dept)
        cogType = self.cogTypes[deptIndex]
        multiple = 5 * cogType
        additional = self.cogLevels[deptIndex] - cogType
        numPromotions = multiple + additional
        return numPromotions

    def b_setCogParts(self, parts):
        self.setCogParts(parts)
        self.d_setCogParts(parts)

    def setCogParts(self, parts):
        if not parts:
            self.notify.warning('cogParts set to bad value: %s. Resetting to [0,0,0,0]' % parts)
            self.cogParts = [0,
             0,
             0,
             0]
        else:
            self.cogParts = parts

    def d_setCogParts(self, parts):
        self.sendUpdate('setCogParts', [parts])

    def getCogParts(self):
        return self.cogParts

    def giveCogPart(self, part, dept):
        dept = CogDisguiseGlobals.dept2deptIndex(dept)
        parts = self.getCogParts()
        parts[dept] = parts[dept] | part
        self.b_setCogParts(parts)

    def hasCogPart(self, part, dept):
        dept = CogDisguiseGlobals.dept2deptIndex(dept)
        if self.cogParts[dept] & part:
            return 1
        else:
            return 0

    def giveGenericCogPart(self, factoryType, dept):
        for partTypeId in self.partTypeIds[factoryType]:
            nextPart = CogDisguiseGlobals.getNextPart(self.getCogParts(), partTypeId, dept)
            if nextPart:
                break

        if nextPart:
            self.giveCogPart(nextPart, dept)
            return nextPart
        else:
            return None
        return None

    def takeCogPart(self, part, dept):
        dept = CogDisguiseGlobals.dept2deptIndex(dept)
        parts = self.getCogParts()
        if parts[dept] & part:
            parts[dept] = parts[dept] ^ part
            self.b_setCogParts(parts)

    def loseCogParts(self, dept):
        loseCount = random.randrange(CogDisguiseGlobals.MinPartLoss, CogDisguiseGlobals.MaxPartLoss + 1)
        parts = self.getCogParts()
        partBitmask = parts[dept]
        partList = list(range(17))
        while loseCount > 0 and partList:
            losePart = random.choice(partList)
            partList.remove(losePart)
            losePartBit = 1 << losePart
            if partBitmask & losePartBit:
                partBitmask &= ~losePartBit
                loseCount -= 1

        parts[dept] = partBitmask
        self.b_setCogParts(parts)

    def b_setCogMerits(self, merits):
        self.setCogMerits(merits)
        self.d_setCogMerits(merits)

    def setCogMerits(self, merits):
        if not merits:
            self.notify.warning('cogMerits set to bad value: %s. Resetting to [0,0,0,0]' % merits)
            self.cogMerits = [0,
             0,
             0,
             0]
        else:
            self.cogMerits = merits

    def d_setCogMerits(self, merits):
        self.sendUpdate('setCogMerits', [merits])

    def getCogMerits(self):
        return self.cogMerits

    def b_promote(self, dept):
        self.promote(dept)
        self.d_promote(dept)

    def promote(self, dept):
        if self.cogLevels[dept] < ToontownGlobals.MaxCogSuitLevel:
            self.cogMerits[dept] = 0
        self.incCogLevel(dept)

    def d_promote(self, dept):
        merits = self.getCogMerits()
        if self.cogLevels[dept] < ToontownGlobals.MaxCogSuitLevel:
            merits[dept] = 0
        self.d_setCogMerits(merits)

    def readyForPromotion(self, dept):
        merits = self.cogMerits[dept]
        totalMerits = CogDisguiseGlobals.getTotalMerits(self, dept)
        if merits >= totalMerits:
            return 1
        else:
            return 0

    def b_setCogIndex(self, cogShorthand, displayLevel = 50, cogType=0, removed=0):
        self.setCogIndex(cogShorthand, cogType, removed)
        if not cogShorthand and removed == 2:
            self.b_setName(self.getName())
        self.d_setCogIndex(cogShorthand, displayLevel, cogType, removed)

    def setCogIndex(self, cogShorthand, displayLevel, cogType=0, removed=0):
        # We must maintain backwards compatibility with toons running on the old setCogIndex field
        if cogShorthand not in SuitDNA.suitHeadTypes or isinstance(cogShorthand, int):
            cogShorthand = ''
        self.cogIndex = cogShorthand

    def d_setCogIndex(self, cogShorthand, displayLevel = 50, cogType = 0, removed = 0):
        self.sendUpdate('setCogIndex', [cogShorthand, displayLevel, cogType, removed])
        if cogShorthand:
            self.takeOffTransformation(ToontownGlobals.TransformationCog)

    def getCogIndex(self):
        return self.cogIndex

    def b_setCharIndex(self, index, removed=0):
        self.setCharIndex(index, removed)
        self.d_setCharIndex(index, removed)

    def setCharIndex(self, index, removed=0):
        self.charIndex = index

    def d_setCharIndex(self, index, removed=0):
        self.sendUpdate('setCharIndex', [index, removed])
        if index > 0:
            self.takeOffTransformation(ToontownGlobals.TransformationClassicChar)

    def getCharIndex(self):
        return self.charIndex

    def b_setDoodleIndex(self, index, removed = 0, petName = "", petDNA = None):
        self.setDoodleIndex(index, removed, petName, petDNA)
        self.d_setDoodleIndex(index, removed, petName, petDNA)

    def setDoodleIndex(self, index, removed = 0, petName = "", petDNA = None):
        self.doodleIndex = index

    def d_setDoodleIndex(self, index, removed = 0, petName = "", petDNA = None):
        self.sendUpdate('setDoodleIndex', [index, removed, petName, petDNA])
        if index > 0:
            self.takeOffTransformation(ToontownGlobals.TransformationDoodle)

    def getDoodleIndex(self):
        return self.doodleIndex

    def b_setGoonIndex(self, index, removed=0):
        self.setGoonIndex(index, removed)
        self.d_setGoonIndex(index, removed)

    def setGoonIndex(self, index, removed=0):
        self.goonIndex = index

    def d_setGoonIndex(self, index, removed=0):
        self.sendUpdate('setGoonIndex', [index, removed])
        if index > 0:
            self.takeOffTransformation(ToontownGlobals.TransformationGoon)

    def getGoonIndex(self):
        return self.goonIndex

    def b_setPropIndex(self, propName, removed=0):
        self.setPropIndex(propName, removed)
        self.d_setPropIndex(propName, removed)

    def setPropIndex(self, propName, removed=0):
        self.propIndex = propName

    def d_setPropIndex(self, propName, removed=0):
        self.sendUpdate('setPropIndex', [propName, removed])
        if propName != '':
            self.takeOffTransformation(ToontownGlobals.TransformationProp)

    def getPropIndex(self):
        return self.propIndex

    def b_setBossIndex(self, index, removed=0):
        self.setBossIndex(index, removed)
        self.d_setBossIndex(index, removed)

    def setBossIndex(self, index, removed=0):
        self.bossIndex = index

    def d_setBossIndex(self, index, removed=0):
        self.sendUpdate('setBossIndex', [index, removed])
        if index > 0:
            self.takeOffTransformation(ToontownGlobals.TransformationBoss)

    def getBossIndex(self):
        return self.bossIndex

    def b_setFishIndex(self, index, removed=0):
        self.setFishIndex(index, removed)
        self.d_setFishIndex(index, removed)

    def setFishIndex(self, index, removed=0):
        self.fishIndex = index

    def d_setFishIndex(self, index, removed=0):
        self.sendUpdate('setFishIndex', [index, removed])
        if index > 0:
            self.takeOffTransformation(ToontownGlobals.TransformationFish)

    def getFishIndex(self):
        return self.fishIndex

    def b_setButterflyIndex(self, index: int, r: int, g: int, b: int, removed: int = 0):
        self.setButterflyIndex(index, r, g, b, removed)
        self.d_setButterflyIndex(index, r, g, b, removed)

    def setButterflyIndex(self, index: int, r: int, g: int, b: int, removed: int = 0):
        self.butterflyIndex = index

    def d_setButterflyIndex(self, index, r: int, g: int, b: int, removed: int = 0):
        self.sendUpdate('setButterflyIndex', [index, r, g, b, removed])
        if index > 0:
            self.takeOffTransformation(ToontownGlobals.TransformationButterfly)

    def getButterflyIndex(self) -> int:
        return self.butterflyIndex

    def b_setMiscIndex(self, index, removed=0):
        self.setMiscIndex(index, removed)
        self.d_setMiscIndex(index, removed)

    def setMiscIndex(self, index, removed=0):
        self.miscIndex = index

    def d_setMiscIndex(self, index, removed=0):
        self.sendUpdate('setMiscIndex', [index, removed])
        if index > 0:
            self.takeOffTransformation(ToontownGlobals.TransformationMisc)

    def getMiscIndex(self):
        return self.miscIndex

    def b_setStreetIndex(self, index, removed=0):
        self.setStreetIndex(index, removed)
        self.d_setStreetIndex(index, removed)

    def setStreetIndex(self, index, removed=0):
        self.streetIndex = index

    def d_setStreetIndex(self, index, removed=0):
        self.sendUpdate('setStreetIndex', [index, removed])
        if index > 0:
            self.takeOffTransformation(ToontownGlobals.TransformationStreet)

    def getStreetIndex(self):
        return self.streetIndex

    def takeOffTransformation(self, exclusionIndex):
        if self.isPlayerControlled():
            transformations = [self.b_setCogIndex, self.b_setCharIndex, self.b_setDoodleIndex, self.b_setGoonIndex,
                               self.b_setPropIndex, self.b_setBossIndex, self.b_setFishIndex, self.b_setButterflyIndex,
                               self.b_setMiscIndex, self.b_setStreetIndex]
            transformations.remove(transformations[exclusionIndex])
            for x in range(len(transformations)):
                transformation = transformations[x]
                if transformation == self.b_setPropIndex:
                    transformation('', 1)
                elif transformation == self.b_setCogIndex:
                    transformation('', 0, 0, 1)
                elif transformation == self.b_setDoodleIndex:
                    transformation(0, 0, '', [])
                elif transformation == self.b_setButterflyIndex:
                    transformation(0, 0, 0, 0, 1)
                else:
                    transformation(0, 1)

    def getIsTransformed(self):
        transformations = (self.cogIndex, self.charIndex, self.doodleIndex, self.goonIndex, self.propIndex,
                           self.bossIndex, self.fishIndex, self.butterflyIndex, self.miscIndex, self.streetIndex)
        for x in range(len(transformations)):
            transformation = transformations[x]
            if transformation != '' and x in (ToontownGlobals.TransformationCog, ToontownGlobals.TransformationProp):
                return True
            elif transformation == '':
                continue
            elif transformation > 0 and x not in (ToontownGlobals.TransformationCog, ToontownGlobals.TransformationProp):
                return True
        return False

    def b_setDisguisePageFlag(self, flag):
        self.setDisguisePageFlag(flag)
        self.d_setDisguisePageFlag(flag)

    def setDisguisePageFlag(self, flag):
        self.disguisePageFlag = flag

    def d_setDisguisePageFlag(self, flag):
        self.sendUpdate('setDisguisePageFlag', [flag])

    def getDisguisePageFlag(self):
        return self.disguisePageFlag

    def b_setSosPageFlag(self, flag):
        self.setSosPageFlag(flag)
        self.d_setSosPageFlag(flag)

    def setSosPageFlag(self, flag):
        self.sosPageFlag = flag

    def d_setSosPageFlag(self, flag):
        self.sendUpdate('setSosPageFlag', [flag])

    def getSosPageFlag(self):
        return self.sosPageFlag

    def b_setFishCollection(self, genusList, speciesList, weightList):
        self.setFishCollection(genusList, speciesList, weightList)
        self.d_setFishCollection(genusList, speciesList, weightList)

    def d_setFishCollection(self, genusList, speciesList, weightList):
        self.sendUpdate('setFishCollection', [genusList, speciesList, weightList])

    def setFishCollection(self, genusList, speciesList, weightList):
        self.fishCollection = FishCollection.FishCollection()
        self.fishCollection.makeFromNetLists(genusList, speciesList, weightList)

    def getFishCollection(self):
        return self.fishCollection.getNetLists()

    def b_setMaxFishTank(self, maxTank):
        self.d_setMaxFishTank(maxTank)
        self.setMaxFishTank(maxTank)

    def d_setMaxFishTank(self, maxTank):
        self.sendUpdate('setMaxFishTank', [maxTank])

    def setMaxFishTank(self, maxTank):
        self.maxFishTank = maxTank

    def getMaxFishTank(self):
        return self.maxFishTank

    def b_setFishTank(self, genusList, speciesList, weightList):
        self.setFishTank(genusList, speciesList, weightList)
        self.d_setFishTank(genusList, speciesList, weightList)

    def d_setFishTank(self, genusList, speciesList, weightList):
        self.sendUpdate('setFishTank', [genusList, speciesList, weightList])

    def setFishTank(self, genusList, speciesList, weightList):
        self.fishTank = FishTank.FishTank()
        self.fishTank.makeFromNetLists(genusList, speciesList, weightList)

    def getFishTank(self):
        return self.fishTank.getNetLists()

    def makeRandomFishTank(self):
        self.fishTank.generateRandomTank()
        self.d_setFishTank(*self.fishTank.getNetLists())

    def addFishToTank(self, fish):
        numFish = len(self.fishTank)
        if numFish >= self.maxFishTank:
            self.notify.warning('addFishToTank: cannot add fish, tank is full')
            return 0
        elif self.fishTank.addFish(fish):
            self.d_setFishTank(*self.fishTank.getNetLists())
            return 1
        else:
            self.notify.warning('addFishToTank: addFish failed')
            return 0

    def removeFishFromTankAtIndex(self, index):
        if self.fishTank.removeFishAtIndex(index):
            self.d_setFishTank(*self.fishTank.getNetLists())
            return 1
        else:
            self.notify.warning('removeFishFromTank: cannot find fish')
            return 0

    def b_setFishingRod(self, rodId):
        self.d_setFishingRod(rodId)
        self.setFishingRod(rodId)

    def d_setFishingRod(self, rodId):
        self.sendUpdate('setFishingRod', [rodId])

    def setFishingRod(self, rodId):
        self.fishingRod = rodId

    def getFishingRod(self):
        return self.fishingRod

    def b_setFishingTrophies(self, trophyList):
        self.setFishingTrophies(trophyList)
        self.d_setFishingTrophies(trophyList)

    def setFishingTrophies(self, trophyList):
        self.notify.debug('setting fishingTrophies to %s' % trophyList)
        self.fishingTrophies = trophyList

    def d_setFishingTrophies(self, trophyList):
        self.sendUpdate('setFishingTrophies', [trophyList])

    def getFishingTrophies(self):
        return self.fishingTrophies

    def b_setQuests(self, questList):
        flattenedQuests = []
        for quest in questList:
            flattenedQuests.extend(quest)

        self.setQuests(flattenedQuests)
        self.d_setQuests(flattenedQuests)

    def d_setQuests(self, flattenedQuests):
        self.sendUpdate('setQuests', [flattenedQuests])

    def setQuests(self, flattenedQuests):
        self.notify.debug('setting quests to %s' % flattenedQuests)
        questList = []
        questLen = 5
        for i in range(0, len(flattenedQuests), questLen):
            questList.append(flattenedQuests[i:i + questLen])

        self.quests = questList

    def getQuests(self):
        flattenedQuests = []
        for quest in self.quests:
            flattenedQuests.extend(quest)

        return flattenedQuests

    def getQuest(self, questId, visitNpcId = None, rewardId = None):
        for quest in self.quests:
            if quest[0] != questId:
                continue
            if visitNpcId != None:
                if visitNpcId != quest[1] and visitNpcId != quest[2]:
                    continue
            if rewardId != None:
                if rewardId != quest[3]:
                    continue
            return quest

        return

    def hasQuest(self, questId, visitNpcId = None, rewardId = None):
        if self.getQuest(questId, visitNpcId=visitNpcId, rewardId=rewardId) == None:
            return False
        else:
            return True
        return

    def removeQuest(self, id, visitNpcId = None):
        index = -1
        for i in range(len(self.quests)):
            if self.quests[i][0] == id:
                if visitNpcId:
                    otherId = self.quests[i][2]
                    if visitNpcId == otherId:
                        index = i
                        break
                else:
                    index = i
                    break

        if index >= 0:
            del self.quests[i]
            self.b_setQuests(self.quests)
            return 1
        else:
            return 0

    def addQuest(self, quest, finalReward, recordHistory = 1):
        self.quests.append(quest)
        self.b_setQuests(self.quests)
        if recordHistory:
            if quest[0] != Quests.VISIT_QUEST_ID:
                newQuestHistory = self.questHistory + [quest[0]]
                while newQuestHistory.count(Quests.VISIT_QUEST_ID) != 0:
                    newQuestHistory.remove(Quests.VISIT_QUEST_ID)

                self.b_setQuestHistory(newQuestHistory)
                if finalReward:
                    newRewardHistory = self.rewardHistory + [finalReward]
                    self.b_setRewardHistory(self.rewardTier, newRewardHistory)

    def removeAllTracesOfQuest(self, questId, rewardId):
        self.notify.debug('removeAllTracesOfQuest: questId: %s rewardId: %s' % (questId, rewardId))
        self.notify.debug('removeAllTracesOfQuest: quests before: %s' % self.quests)
        removedQuest = self.removeQuest(questId)
        self.notify.debug('removeAllTracesOfQuest: quests after: %s' % self.quests)
        self.notify.debug('removeAllTracesOfQuest: questHistory before: %s' % self.questHistory)
        removedQuestHistory = self.removeQuestFromHistory(questId)
        self.notify.debug('removeAllTracesOfQuest: questHistory after: %s' % self.questHistory)
        self.notify.debug('removeAllTracesOfQuest: reward history before: %s' % self.rewardHistory)
        removedRewardHistory = self.removeRewardFromHistory(rewardId)
        self.notify.debug('removeAllTracesOfQuest: reward history after: %s' % self.rewardHistory)
        return (removedQuest, removedQuestHistory, removedRewardHistory)

    def requestDeleteQuest(self, questDesc):
        if len(questDesc) != 5:
            self.air.writeServerEvent('suspicious', self.doId, 'Toon tried to delete invalid questDesc %s' % str(questDesc))
            self.notify.warning('%s.requestDeleteQuest(%s) -- questDesc has incorrect params' % (self, str(questDesc)))
            return
        questId = questDesc[0]
        rewardId = questDesc[3]
        if not self.hasQuest(questId, rewardId=rewardId):
            self.air.writeServerEvent('suspicious', self.doId, "Toon tried to delete quest they don't have %s" % str(questDesc))
            self.notify.warning("%s.requestDeleteQuest(%s) -- Toon doesn't have that quest" % (self, str(questDesc)))
            return
        if not Quests.isQuestJustForFun(questId, rewardId):
            self.air.writeServerEvent('suspicious', self.doId, 'Toon tried to delete non-Just For Fun quest %s' % str(questDesc))
            self.notify.warning('%s.requestDeleteQuest(%s) -- Tried to cancel non-Just For Fun quest' % (self, str(questDesc)))
            return
        removedStatus = self.removeAllTracesOfQuest(questId, rewardId)
        if 0 in removedStatus:
            self.notify.warning('%s.requestDeleteQuest(%s) -- Failed to remove quest, status=%s' % (self, str(questDesc), removedStatus))

    def b_setQuestCarryLimit(self, limit):
        self.setQuestCarryLimit(limit)
        self.d_setQuestCarryLimit(limit)

    def d_setQuestCarryLimit(self, limit):
        self.sendUpdate('setQuestCarryLimit', [limit])

    def setQuestCarryLimit(self, limit):
        self.notify.debug('setting questCarryLimit to %s' % limit)
        self.questCarryLimit = limit

    def getQuestCarryLimit(self):
        return self.questCarryLimit

    def b_setMaxCarry(self, maxCarry):
        self.setMaxCarry(maxCarry)
        self.d_setMaxCarry(maxCarry)

    def d_setMaxCarry(self, maxCarry):
        self.sendUpdate('setMaxCarry', [maxCarry])

    def setMaxCarry(self, maxCarry):
        self.maxCarry = maxCarry

    def getMaxCarry(self):
        return self.maxCarry

    def b_setCheesyEffect(self, effect, hoodId, expireTime):
        self.setCheesyEffect(effect, hoodId, expireTime)
        self.d_setCheesyEffect(effect, hoodId, expireTime)

    def d_setCheesyEffect(self, effect, hoodId, expireTime):
        self.sendUpdate('setCheesyEffect', [effect, hoodId, expireTime])

    def setCheesyEffect(self, effect, hoodId, expireTime):
        self.savedCheesyEffect = effect
        self.savedCheesyHoodId = hoodId
        self.savedCheesyExpireTime = expireTime
        if self.air.doLiveUpdates:
            taskName = self.uniqueName('cheesy-expires')
            taskMgr.remove(taskName)
            if effect != ToontownGlobals.CENormal:
                duration = expireTime * 60 - time.time()
                if duration > 0:
                    taskMgr.doMethodLater(duration, self.__undoCheesyEffect, taskName)
                else:
                    self.__undoCheesyEffect(None)
        return

    def getCheesyEffect(self):
        return (self.savedCheesyEffect, self.savedCheesyHoodId, self.savedCheesyExpireTime)

    def __undoCheesyEffect(self, task):
        self.b_setCheesyEffect(ToontownGlobals.CENormal, 0, 0)
        return Task.cont

    def b_setTrackAccess(self, trackArray):
        self.setTrackAccess(trackArray)
        self.d_setTrackAccess(trackArray)

    def d_setTrackAccess(self, trackArray):
        self.sendUpdate('setTrackAccess', [trackArray])

    def setTrackAccess(self, trackArray):
        self.trackArray = trackArray

    def getTrackAccess(self):
        return self.trackArray

    def addTrackAccess(self, track):
        self.trackArray[track] = 1
        self.b_setTrackAccess(self.trackArray)

    def removeTrackAccess(self, track):
        self.trackArray[track] = 0
        self.b_setTrackAccess(self.trackArray)

    def hasTrackAccess(self, track):
        if self.trackArray and track < len(self.trackArray):
            return self.trackArray[track]
        else:
            return 0

    def fixTrackAccess(self):
        fixed = 0
        healExp, trapExp, lureExp, soundExp, throwExp, squirtExp, dropExp = self.experience.experience
        numTracks = reduce(lambda a, b: a + b, self.trackArray)
        if self.rewardTier in [0,
         1,
         2,
         3]:
            if numTracks != 2:
                self.notify.warning('bad num tracks in tier: %s, %s' % (self.rewardTier, self.trackArray))
                self.b_setTrackAccess([0, 0, 0, 0, 1, 1, 0])
                fixed = 1
        elif self.rewardTier in [4, 5, 6]:
            if numTracks != 3:
                self.notify.warning('bad num tracks in tier: %s, %s' % (self.rewardTier, self.trackArray))
                if self.trackArray[ToontownBattleGlobals.SOUND_TRACK] and not self.trackArray[ToontownBattleGlobals.HEAL_TRACK]:
                    self.b_setTrackAccess([0, 0, 0, 1, 1, 1, 0])
                elif self.trackArray[ToontownBattleGlobals.HEAL_TRACK] and not self.trackArray[ToontownBattleGlobals.SOUND_TRACK]:
                    self.b_setTrackAccess([1, 0, 0, 0, 1, 1, 0])
                elif soundExp >= healExp:
                    self.b_setTrackAccess([0, 0, 0, 1, 1, 1, 0])
                else:
                    self.b_setTrackAccess([1, 0, 0, 0, 1, 1, 0])
                fixed = 1
        elif self.rewardTier in [7, 8, 9, 10]:
            if numTracks != 4:
                self.notify.warning('bad num tracks in tier: %s, %s' % (self.rewardTier, self.trackArray))
                if self.trackArray[ToontownBattleGlobals.SOUND_TRACK] and not self.trackArray[ToontownBattleGlobals.HEAL_TRACK]:
                    if dropExp >= lureExp:
                        self.b_setTrackAccess([0, 0, 0, 1, 1, 1, 1])
                    else:
                        self.b_setTrackAccess([0, 0, 1, 1, 1, 1, 0])
                elif self.trackArray[ToontownBattleGlobals.HEAL_TRACK] and not self.trackArray[ToontownBattleGlobals.SOUND_TRACK]:
                    if dropExp >= lureExp:
                        self.b_setTrackAccess([1, 0, 0, 0, 1, 1, 1])
                    else:
                        self.b_setTrackAccess([1, 0, 1, 0, 1, 1, 0])
                elif soundExp >= healExp:
                    if dropExp >= lureExp:
                        self.b_setTrackAccess([0, 0, 0, 1, 1, 1, 1])
                    else:
                        self.b_setTrackAccess([0, 0, 1, 1, 1, 1, 0])
                elif dropExp >= lureExp:
                    self.b_setTrackAccess([1, 0, 0, 0, 1, 1, 1])
                else:
                    self.b_setTrackAccess([1, 0, 1, 0, 1, 1, 0])
                fixed = 1
        elif self.rewardTier in [11, 12, 13]:
            if numTracks != 5:
                self.notify.warning('bad num tracks in tier: %s, %s' % (self.rewardTier, self.trackArray))
                if self.trackArray[ToontownBattleGlobals.SOUND_TRACK] and not self.trackArray[ToontownBattleGlobals.HEAL_TRACK]:
                    if self.trackArray[ToontownBattleGlobals.DROP_TRACK] and not self.trackArray[ToontownBattleGlobals.LURE_TRACK]:
                        if healExp >= trapExp:
                            self.b_setTrackAccess([1, 0, 0, 1, 1, 1, 1])
                        else:
                            self.b_setTrackAccess([0, 1, 0, 1, 1, 1, 1])
                    elif healExp >= trapExp:
                        self.b_setTrackAccess([1, 0, 1, 1, 1, 1, 0])
                    else:
                        self.b_setTrackAccess([0, 1, 1, 1, 1, 1, 0])
                elif self.trackArray[ToontownBattleGlobals.HEAL_TRACK] and not self.trackArray[ToontownBattleGlobals.SOUND_TRACK]:
                    if self.trackArray[ToontownBattleGlobals.DROP_TRACK] and not self.trackArray[ToontownBattleGlobals.LURE_TRACK]:
                        if soundExp >= trapExp:
                            self.b_setTrackAccess([1, 0, 0, 1, 1, 1, 1])
                        else:
                            self.b_setTrackAccess([1, 1, 0, 0, 1, 1, 1])
                    elif soundExp >= trapExp:
                        self.b_setTrackAccess([1, 0, 1, 1, 1, 1, 0])
                    else:
                        self.b_setTrackAccess([1, 1, 1, 0, 1, 1, 0])
                fixed = 1
        elif numTracks != 6:
            self.notify.warning('bad num tracks in tier: %s, %s' % (self.rewardTier, self.trackArray))
            sortedExp = [healExp,
             trapExp,
             lureExp,
             soundExp,
             dropExp]
            sortedExp.sort()
            if trapExp == sortedExp[0]:
                self.b_setTrackAccess([1, 0, 1, 1, 1, 1, 1])
            elif lureExp == sortedExp[0]:
                self.b_setTrackAccess([1, 1, 0, 1, 1, 1, 1])
            elif dropExp == sortedExp[0]:
                self.b_setTrackAccess([1, 1, 1, 1, 1, 1, 0])
            elif soundExp == sortedExp[0]:
                self.b_setTrackAccess([1, 1, 1, 0, 1, 1, 1])
            elif healExp == sortedExp[0]:
                self.b_setTrackAccess([0, 1, 1, 1, 1, 1, 1])
            else:
                self.notify.warning('invalid exp?!: %s, %s' % (sortedExp, self.trackArray))
                self.b_setTrackAccess([1, 0, 1, 1, 1, 1, 1])
            fixed = 1
        if fixed:
            self.inventory.zeroInv()
            self.inventory.maxOutInv()
            self.d_setInventory(self.inventory.makeNetString())
            self.notify.info('fixed tracks: %s' % self.trackArray)
        return fixed

    def b_setTrackProgress(self, trackId, progress):
        self.setTrackProgress(trackId, progress)
        self.d_setTrackProgress(trackId, progress)

    def d_setTrackProgress(self, trackId, progress):
        self.sendUpdate('setTrackProgress', [trackId, progress])

    def setTrackProgress(self, trackId, progress):
        self.trackProgressId = trackId
        self.trackProgress = progress

    def addTrackProgress(self, trackId, progressIndex):
        if self.trackProgressId != trackId:
            self.notify.warning('tried to update progress on a track toon is not training')
        newProgress = self.trackProgress | 1 << progressIndex - 1
        self.b_setTrackProgress(self.trackProgressId, newProgress)

    def clearTrackProgress(self):
        self.b_setTrackProgress(-1, 0)

    def getTrackProgress(self):
        return [self.trackProgressId, self.trackProgress]

    def d_setAnimPlayRate(self, rate):
        self.sendUpdate('setAnimPlayRate', [rate])

    def b_setHoodsVisited(self, hoodsVisitedArray):
        self.hoodsVisited = hoodsVisitedArray
        self.d_setHoodsVisited(hoodsVisitedArray)

    def d_setHoodsVisited(self, hoodsVisitedArray):
        self.sendUpdate('setHoodsVisited', [hoodsVisitedArray])

    def b_setTeleportAccess(self, teleportZoneArray):
        self.setTeleportAccess(teleportZoneArray)
        self.d_setTeleportAccess(teleportZoneArray)

    def d_setTeleportAccess(self, teleportZoneArray):
        self.sendUpdate('setTeleportAccess', [teleportZoneArray])

    def setTeleportAccess(self, teleportZoneArray):
        self.teleportZoneArray = teleportZoneArray

    def getTeleportAccess(self):
        return self.teleportZoneArray

    def hasTeleportAccess(self, zoneId):
        return zoneId in self.teleportZoneArray

    def addTeleportAccess(self, zoneId):
        if zoneId not in self.teleportZoneArray:
            self.teleportZoneArray.append(zoneId)
            self.b_setTeleportAccess(self.teleportZoneArray)

    def removeTeleportAccess(self, zoneId):
        if zoneId in self.teleportZoneArray:
            self.teleportZoneArray.remove(zoneId)
            self.b_setTeleportAccess(self.teleportZoneArray)

    def checkTeleportAccess(self, zoneId):
        if zoneId not in self.getTeleportAccess():
            simbase.air.writeServerEvent('suspicious', self.doId, 'Toon teleporting to zone %s they do not have access to.' % zoneId)
            if simbase.config.GetBool('want-ban-teleport', False):
                commentStr = 'Toon %s teleporting to a zone %s they do not have access to' % (self.doId, zoneId)
                simbase.air.banManager.ban(self.doId, self.DISLid, commentStr)

    def b_setQuestHistory(self, questList):
        self.setQuestHistory(questList)
        self.d_setQuestHistory(questList)

    def d_setQuestHistory(self, questList):
        self.sendUpdate('setQuestHistory', [questList])

    def setQuestHistory(self, questList):
        self.notify.debug('setting quest history to %s' % questList)
        self.questHistory = questList

    def getQuestHistory(self):
        return self.questHistory

    def removeQuestFromHistory(self, questId):
        if questId in self.questHistory:
            self.questHistory.remove(questId)
            self.d_setQuestHistory(self.questHistory)
            return 1
        else:
            return 0

    def removeRewardFromHistory(self, rewardId):
        rewardTier, rewardHistory = self.getRewardHistory()
        if rewardId in rewardHistory:
            rewardHistory.remove(rewardId)
            self.b_setRewardHistory(rewardTier, rewardHistory)
            return 1
        else:
            return 0

    def b_setRewardHistory(self, tier, rewardList):
        self.setRewardHistory(tier, rewardList)
        self.d_setRewardHistory(tier, rewardList)

    def d_setRewardHistory(self, tier, rewardList):
        if tier > 255:
            tier = 255 # temp fix, remove after test server
        self.sendUpdate('setRewardHistory', [tier, rewardList])

    def setRewardHistory(self, tier, rewardList):
        self.air.writeServerEvent('questTier', self.getDoId(), str(tier))
        self.notify.debug('setting reward history to tier %s, %s' % (tier, rewardList))
        self.rewardTier = tier
        self.rewardHistory = rewardList

    def getRewardHistory(self):
        return (self.rewardTier, self.rewardHistory)

    def getRewardTier(self):
        return self.rewardTier

    def fixAvatar(self):
        anyChanged = 0
        qrc = QuestRewardCounter.QuestRewardCounter()
        if qrc.fixAvatar(self):
            self.notify.info("Fixed avatar %d's quest rewards." % self.doId)
            anyChanged = 1
        if self.hp > self.maxHp:
            self.notify.info('Changed avatar %d to have hp %d instead of %d, to fit with maxHp' % (self.doId, self.maxHp, self.hp))
            self.b_setHp(self.maxHp)
            anyChanged = 1
        inventoryChanged = 0
        carry = self.maxCarry
        for track in range(len(ToontownBattleGlobals.Tracks)):
            if not self.hasTrackAccess(track):
                for level in range(len(ToontownBattleGlobals.Levels[track])):
                    count = self.inventory.inventory[track][level]
                    if count != 0:
                        self.notify.info('Changed avatar %d to throw away %d items in track %d level %d; no access to track.' % (self.doId,
                         count,
                         track,
                         level))
                        self.inventory.inventory[track][level] = 0
                        inventoryChanged = 1

            else:
                curSkill = self.experience.getExp(track)
                for level in range(len(ToontownBattleGlobals.Levels[track])):
                    count = self.inventory.inventory[track][level]
                    if curSkill < ToontownBattleGlobals.Levels[track][level]:
                        if count != 0:
                            self.notify.info('Changed avatar %d to throw away %d items in track %d level %d; no access to level.' % (self.doId,
                             count,
                             track,
                             level))
                            self.inventory.inventory[track][level] = 0
                            inventoryChanged = 1
                    else:
                        newCount = min(count, carry)
                        newCount = min(count, self.inventory.getMax(track, level))
                        if count != newCount:
                            self.notify.info('Changed avatar %d to throw away %d items in track %d level %d; too many gags.' % (self.doId,
                             count - newCount,
                             track,
                             level))
                            self.inventory.inventory[track][level] = newCount
                            inventoryChanged = 1
                        carry -= newCount

        self.inventory.calcTotalProps()
        if inventoryChanged:
            self.d_setInventory(self.inventory.makeNetString())
            anyChanged = 1
        if len(self.quests) > self.questCarryLimit:
            self.notify.info('Changed avatar %d to throw out %d quests; too many quests.' % (self.doId, len(self.quests) - self.questCarryLimit))
            self.b_setQuests(self.quests[:self.questCarryLimit])
            self.fixAvatar()
            anyChanged = 1
        if not (self.emoteAccess[0] and self.emoteAccess[1] and self.emoteAccess[2] and self.emoteAccess[3] and self.emoteAccess[4]):
            self.emoteAccess[0] = 1
            self.emoteAccess[1] = 1
            self.emoteAccess[2] = 1
            self.emoteAccess[3] = 1
            self.emoteAccess[4] = 1
            self.b_setEmoteAccess(self.emoteAccess)
            self.notify.info('Changed avatar %d to have emoteAccess: %s' % (self.doId, self.emoteAccess))
            anyChanged = 1
        return anyChanged

    def b_setEmoteAccess(self, bits):
        self.setEmoteAccess(bits)
        self.d_setEmoteAccess(bits)

    def d_setEmoteAccess(self, bits):
        self.sendUpdate('setEmoteAccess', [bits])

    def setEmoteAccess(self, bits):
        if len(bits) == 19:
            bits.extend([0,
             0,
             0,
             0,
             0])
            self.b_setEmoteAccess(bits)
        elif len(bits) != len(self.emoteAccess):
            self.notify.warning('New emote access list must be the same size as the old one.')
            return
        self.emoteAccess = bits

    def getEmoteAccess(self):
        return self.emoteAccess

    def setEmoteAccessId(self, id, bit):
        self.emoteAccess[id] = bit
        self.d_setEmoteAccess(self.emoteAccess)

    def b_setHouseId(self, id):
        self.setHouseId(id)
        self.d_setHouseId(id)

    def d_setHouseId(self, id):
        self.sendUpdate('setHouseId', [id])

    def setHouseId(self, id):
        self.houseId = id

    def getHouseId(self):
        return self.houseId

    def b_setHouseType(self, index):
        self.setHouseType(index)
        self.d_setHouseType(index)

    def d_setHouseType(self, index):
        self.sendUpdate('setHouseType', [index])

    def setHouseType(self, index):
        self.houseType = index

    def getHouseType(self):
        return self.houseType

    def setPosIndex(self, index):
        self.posIndex = index

    def getPosIndex(self):
        return self.posIndex

    def b_setCustomMessages(self, customMessages):
        self.d_setCustomMessages(customMessages)
        self.setCustomMessages(customMessages)

    def d_setCustomMessages(self, customMessages):
        self.sendUpdate('setCustomMessages', [customMessages])

    def setCustomMessages(self, customMessages):
        self.customMessages = customMessages

    def getCustomMessages(self):
        return self.customMessages

    def b_setResistanceMessages(self, resistanceMessages):
        self.d_setResistanceMessages(resistanceMessages)
        self.setResistanceMessages(resistanceMessages)

    def d_setResistanceMessages(self, resistanceMessages):
        self.sendUpdate('setResistanceMessages', [resistanceMessages])

    def setResistanceMessages(self, resistanceMessages):
        self.resistanceMessages = resistanceMessages

    def getResistanceMessages(self):
        return self.resistanceMessages

    def addResistanceMessage(self, textId):
        msgs = self.getResistanceMessages()
        for i in range(len(msgs)):
            if msgs[i][0] == textId:
                msgs[i][1] += 1
                self.b_setResistanceMessages(msgs)
                return

        msgs.append([textId, 1])
        self.b_setResistanceMessages(msgs)

    def removeResistanceMessage(self, textId):
        msgs = self.getResistanceMessages()
        for i in range(len(msgs)):
            if msgs[i][0] == textId:
                msgs[i][1] -= 1
                if msgs[i][1] <= 0:
                    del msgs[i]
                self.b_setResistanceMessages(msgs)
                return 1

        self.notify.warning("Toon %s doesn't have resistance message %s" % (self.doId, textId))
        return 0

    def restockAllResistanceMessages(self, charges = 1):
        from toontown.chat import ResistanceChat
        msgs = []
        for menuIndex in ResistanceChat.resistanceMenu:
            for itemIndex in ResistanceChat.getItems(menuIndex):
                textId = ResistanceChat.encodeId(menuIndex, itemIndex)
                msgs.append([textId, charges])

        self.b_setResistanceMessages(msgs)

    def b_setCatalogSchedule(self, currentWeek, nextTime):
        self.setCatalogSchedule(currentWeek, nextTime)
        self.d_setCatalogSchedule(currentWeek, nextTime)

    def d_setCatalogSchedule(self, currentWeek, nextTime):
        self.sendUpdate('setCatalogSchedule', [currentWeek, nextTime])

    def setCatalogSchedule(self, currentWeek, nextTime):
        self.catalogScheduleCurrentWeek = currentWeek
        self.catalogScheduleNextTime = nextTime
        if self.air.doLiveUpdates:
            taskName = self.uniqueName('next-catalog')
            taskMgr.remove(taskName)
            duration = max(10.0, nextTime * 60 - time.time())
            taskMgr.doMethodLater(duration, self.__deliverCatalog, taskName)

    def getCatalogSchedule(self):
        return (self.catalogScheduleCurrentWeek, self.catalogScheduleNextTime)

    def __deliverCatalog(self, task):
        self.air.catalogManager.deliverCatalogFor(self)
        return Task.done

    def b_setCatalog(self, monthlyCatalog, weeklyCatalog, backCatalog):
        self.setCatalog(monthlyCatalog, weeklyCatalog, backCatalog)
        self.d_setCatalog(monthlyCatalog, weeklyCatalog, backCatalog)

    def d_setCatalog(self, monthlyCatalog, weeklyCatalog, backCatalog):
        self.sendUpdate('setCatalog', [monthlyCatalog.getBlob(), weeklyCatalog.getBlob(), backCatalog.getBlob()])

    def setCatalog(self, monthlyCatalog, weeklyCatalog, backCatalog):
        self.monthlyCatalog = CatalogItemList.CatalogItemList(monthlyCatalog)
        self.weeklyCatalog = CatalogItemList.CatalogItemList(weeklyCatalog)
        self.backCatalog = CatalogItemList.CatalogItemList(backCatalog)

    def getCatalog(self):
        return (self.monthlyCatalog.getBlob(), self.weeklyCatalog.getBlob(), self.backCatalog.getBlob())

    def b_setCatalogNotify(self, catalogNotify, mailboxNotify):
        self.setCatalogNotify(catalogNotify, mailboxNotify)
        self.d_setCatalogNotify(catalogNotify, mailboxNotify)

    def d_setCatalogNotify(self, catalogNotify, mailboxNotify):
        self.sendUpdate('setCatalogNotify', [catalogNotify, mailboxNotify])

    def setCatalogNotify(self, catalogNotify, mailboxNotify):
        self.catalogNotify = catalogNotify
        self.mailboxNotify = mailboxNotify

    def getCatalogNotify(self):
        return (self.catalogNotify, self.mailboxNotify)

    def b_setDeliverySchedule(self, onOrder, doUpdateLater = True):
        self.setDeliverySchedule(onOrder, doUpdateLater)
        self.d_setDeliverySchedule(onOrder)

    def d_setDeliverySchedule(self, onOrder):
        self.sendUpdate('setDeliverySchedule', [onOrder.getBlob(store=CatalogItem.Customization | CatalogItem.DeliveryDate)])

    def setDeliverySchedule(self, onOrder, doUpdateLater = True):
        self.setBothSchedules(onOrder, None)
        return
        self.onOrder = CatalogItemList.CatalogItemList(onOrder, store=CatalogItem.Customization | CatalogItem.DeliveryDate)
        if hasattr(self, 'name'):
            if doUpdateLater and self.air.doLiveUpdates and hasattr(self, 'air'):
                taskName = self.uniqueName('next-delivery')
                taskMgr.remove(taskName)
                now = int(time.time() / 60 + 0.5)
                nextItem = None
                nextTime = self.onOrder.getNextDeliveryDate()
                nextItem = self.onOrder.getNextDeliveryItem()
                if nextItem != None:
                    pass
                if nextTime != None:
                    duration = max(10.0, nextTime * 60 - time.time())
                    taskMgr.doMethodLater(duration, self.__deliverPurchase, taskName)
        return

    def getDeliverySchedule(self):
        return self.onOrder.getBlob(store=CatalogItem.Customization | CatalogItem.DeliveryDate)

    def b_setBothSchedules(self, onOrder, onGiftOrder, doUpdateLater = True):
        self.setBothSchedules(onOrder, onGiftOrder, doUpdateLater)
        self.d_setDeliverySchedule(onOrder)

    def setBothSchedules(self, onOrder, onGiftOrder, doUpdateLater = True):
        if onOrder != None:
            self.onOrder = CatalogItemList.CatalogItemList(onOrder, store=CatalogItem.Customization | CatalogItem.DeliveryDate)
        if onGiftOrder != None:
            self.onGiftOrder = CatalogItemList.CatalogItemList(onGiftOrder, store=CatalogItem.Customization | CatalogItem.DeliveryDate)
        if not hasattr(self, 'air') or self.air == None:
            return
        if doUpdateLater and self.air.doLiveUpdates and hasattr(self, 'name'):
            taskName = 'next-bothDelivery-%s' % self.doId
            now = int(time.time() / 60 + 0.5)
            nextItem = 0
            nextGiftItem = 0
            nextTime = 0
            nextGiftTime = 0
            if self.onOrder:
                nextTime = self.onOrder.getNextDeliveryDate()
                nextItem = self.onOrder.getNextDeliveryItem()
            if self.onGiftOrder:
                nextGiftTime = self.onGiftOrder.getNextDeliveryDate()
                nextGiftItem = self.onGiftOrder.getNextDeliveryItem()
            if nextItem:
                pass
            if nextGiftItem:
                pass
            if nextTime == 0:
                nextTime = nextGiftTime
            if nextGiftTime == 0:
                nextGiftTime = nextTime
            if nextGiftTime < nextTime:
                nextTime = nextGiftTime
            existingDuration = 0
            checkTaskList = taskMgr.getTasksNamed(taskName)
            if checkTaskList:
                currentTime = globalClock.getFrameTime()
                checkTask = checkTaskList[0]
                existingDuration = checkTask.wakeTime - currentTime
            if nextTime:
                newDuration = max(10.0, nextTime * 60 - time.time())
                if existingDuration and existingDuration >= newDuration:
                    taskMgr.remove(taskName)
                    taskMgr.doMethodLater(newDuration, self.__deliverBothPurchases, taskName)
                elif existingDuration and existingDuration < newDuration:
                    pass
                else:
                    taskMgr.doMethodLater(newDuration, self.__deliverBothPurchases, taskName)
        return

    def __deliverBothPurchases(self, task):
        now = int(time.time() / 60 + 0.5)
        delivered, remaining = self.onOrder.extractDeliveryItems(now)
        deliveredGifts, remainingGifts = self.onGiftOrder.extractDeliveryItems(now)
        simbase.air.deliveryManager.sendDeliverGifts(self.getDoId(), now)
        giftItem = CatalogItemList.CatalogItemList(deliveredGifts, store=CatalogItem.Customization | CatalogItem.DeliveryDate)
        if len(giftItem) > 0:
            self.air.writeServerEvent('Getting Gift', self.doId, 'sender %s receiver %s gift %s' % (giftItem[0].giftTag, self.doId, giftItem[0].getName()))
        self.b_setMailboxContents(self.mailboxContents + delivered + deliveredGifts)
        self.b_setCatalogNotify(self.catalogNotify, ToontownGlobals.NewItems)
        self.b_setBothSchedules(remaining, remainingGifts)
        return Task.done

    def setGiftSchedule(self, onGiftOrder, doUpdateLater = True):
        self.setBothSchedules(None, onGiftOrder)
        return
        self.onGiftOrder = CatalogItemList.CatalogItemList(onGiftOrder, store=CatalogItem.Customization | CatalogItem.DeliveryDate)
        if doUpdateLater and self.air.doLiveUpdates and hasattr(self, 'air') and hasattr(self, 'name'):
            taskName = self.uniqueName('next-gift')
            taskMgr.remove(taskName)
            now = int(time.time() / 60 + 0.5)
            nextItem = None
            nextTime = self.onGiftOrder.getNextDeliveryDate()
            nextItem = self.onGiftOrder.getNextDeliveryItem()
            if nextItem != None:
                pass
            if nextTime != None:
                duration = max(10.0, nextTime * 60 - time.time())
                duration += 30
                taskMgr.doMethodLater(duration, self.__deliverGiftPurchase, taskName)
        return

    def getGiftSchedule(self):
        return self.onGiftOrder.getBlob(store=CatalogItem.Customization | CatalogItem.DeliveryDate)

    def __deliverGiftPurchase(self, task):
        now = int(time.time() / 60 + 0.5)
        delivered, remaining = self.onGiftOrder.extractDeliveryItems(now)
        self.notify.info('Gift Delivery for %s: %s.' % (self.doId, delivered))
        self.b_setMailboxContents(self.mailboxContents + delivered)
        simbase.air.deliveryManager.sendDeliverGifts(self.getDoId(), now)
        self.b_setCatalogNotify(self.catalogNotify, ToontownGlobals.NewItems)
        return Task.done

    def __deliverPurchase(self, task):
        now = int(time.time() / 60 + 0.5)
        delivered, remaining = self.onOrder.extractDeliveryItems(now)
        self.notify.info('Delivery for %s: %s.' % (self.doId, delivered))
        self.b_setMailboxContents(self.mailboxContents + delivered)
        self.b_setDeliverySchedule(remaining)
        self.b_setCatalogNotify(self.catalogNotify, ToontownGlobals.NewItems)
        return Task.done

    def b_setMailboxContents(self, mailboxContents):
        self.setMailboxContents(mailboxContents)
        self.d_setMailboxContents(mailboxContents)

    def d_setMailboxContents(self, mailboxContents):
        self.sendUpdate('setMailboxContents', [mailboxContents.getBlob(store=CatalogItem.Customization)])
        if len(mailboxContents) == 0:
            self.b_setCatalogNotify(self.catalogNotify, ToontownGlobals.NoItems)
        self.checkMailboxFullIndicator()

    def checkMailboxFullIndicator(self):
        if self.houseId and hasattr(self, 'air'):
            if self.air:
                house = self.air.doId2do.get(self.houseId)
                if house and house.mailbox:
                    house.mailbox.b_setFullIndicator(len(self.mailboxContents) != 0 or self.numMailItems or self.getNumInvitesToShowInMailbox() or len(self.awardMailboxContents) != 0)

    def setMailboxContents(self, mailboxContents):
        self.notify.debug('Setting mailboxContents to %s.' % mailboxContents)
        self.mailboxContents = CatalogItemList.CatalogItemList(mailboxContents, store=CatalogItem.Customization)
        self.notify.debug('mailboxContents is %s.' % self.mailboxContents)

    def getMailboxContents(self):
        return self.mailboxContents.getBlob(store=CatalogItem.Customization)

    def b_setGhostMode(self, flag):
        self.setGhostMode(flag)
        self.d_setGhostMode(flag)
        self.air.updateOnlineAvatar(self)

    def d_setGhostMode(self, flag):
        self.sendUpdate('setGhostMode', [flag])

    def setGhostMode(self, flag):
        self.ghostMode = flag

    def b_setImmortalMode(self, flag):
        self.setImmortalMode(flag)
        self.d_setImmortalMode(flag)

    def d_setImmortalMode(self, flag):
        self.sendUpdate('setImmortalMode', [flag])

    def setImmortalMode(self, flag):
        self.immortalMode = flag

    def getImmortalMode(self):
        return self.immortalMode

    def b_setTempImmortalMode(self, flag):
        self.setTempImmortalMode(flag)
        self.d_setTempImmortalMode(flag)

    def d_setTempImmortalMode(self, flag):
        self.sendUpdate('setTempImmortalMode', [flag])

    def setTempImmortalMode(self, flag):
        self.tempImmortalMode = flag

    def getTempImmortalMode(self):
        return self.tempImmortalMode

    def setTreasureDamage(self, treasureDamage: bool):
        self.treasureDamage = treasureDamage

    def getTreasureDamage(self) -> bool:
        return self.treasureDamage

    def b_setSpeedChatStyleIndex(self, index):
        self.setSpeedChatStyleIndex(index)
        self.d_setSpeedChatStyleIndex(index)

    def d_setSpeedChatStyleIndex(self, index):
        self.sendUpdate('setSpeedChatStyleIndex', [index])

    def setSpeedChatStyleIndex(self, index):
        self.speedChatStyleIndex = index

    def getSpeedChatStyleIndex(self):
        return self.speedChatStyleIndex

    def b_setMaxMoney(self, maxMoney):
        self.d_setMaxMoney(maxMoney)
        self.setMaxMoney(maxMoney)

    def d_setMaxMoney(self, maxMoney):
        self.sendUpdate('setMaxMoney', [maxMoney])

    def setMaxMoney(self, maxMoney):
        self.maxMoney = maxMoney

    def getMaxMoney(self):
        return self.maxMoney

    def addMoney(self, deltaMoney):
        money = deltaMoney + self.money
        pocketMoney = min(money, self.maxMoney)
        self.b_setMoney(pocketMoney)
        overflowMoney = money - self.maxMoney
        if overflowMoney > 0:
            bankMoney = self.bankMoney + overflowMoney
            self.b_setBankMoney(bankMoney)

    def takeMoney(self, deltaMoney, bUseBank = True):
        totalMoney = self.money
        if bUseBank:
            totalMoney += self.bankMoney
        if deltaMoney > totalMoney:
            self.notify.warning('Not enough money! AvId: %s Has:%s Charged:%s' % (self.doId, totalMoney, deltaMoney))
            return False
        if bUseBank and deltaMoney > self.money:
            self.b_setBankMoney(self.bankMoney - (deltaMoney - self.money))
            self.b_setMoney(0)
        else:
            self.b_setMoney(self.money - deltaMoney)
        return True

    def b_setMoney(self, money):
        if bboard.get('autoRich-%s' % self.doId, False):
            money = self.getMaxMoney()
        self.setMoney(money)
        self.d_setMoney(money)

    def d_setMoney(self, money):
        self.sendUpdate('setMoney', [money])

    def setMoney(self, money):
        if money < 0:
            simbase.air.writeServerEvent('suspicious', self.doId, 'toon has invalid money %s, forcing to zero' % money)
            money = 0
            commentStr = 'User %s has negative money %s' % (self.doId, money)
            dislId = self.DISLid
            if simbase.config.GetBool('want-ban-negative-money', False):
                simbase.air.banManager.ban(self.doId, dislId, commentStr)
        self.money = money

    def getMoney(self):
        return self.money

    def getTotalMoney(self):
        return self.money + self.bankMoney

    def setTotalMoney(self, cost):
        if self.getTotalMoney() >= cost:
            bankPrice = min(self.getBankMoney(), cost)
            walletPrice = cost - bankPrice
            self.b_setBankMoney(self.getBankMoney() - bankPrice)
            self.b_setMoney(self.getMoney() - walletPrice)
            return True

        return False

    def b_setMaxBankMoney(self, maxMoney):
        self.d_setMaxBankMoney(maxMoney)
        self.setMaxBankMoney(maxMoney)

    def d_setMaxBankMoney(self, maxMoney):
        self.sendUpdate('setMaxBankMoney', [maxMoney])

    def setMaxBankMoney(self, maxMoney):
        self.maxBankMoney = maxMoney

    def getMaxBankMoney(self):
        return self.maxBankMoney

    def b_setBankMoney(self, money):
        bankMoney = min(money, self.maxBankMoney)
        self.setBankMoney(bankMoney)
        self.d_setBankMoney(bankMoney)

    def d_setBankMoney(self, money):
        self.sendUpdate('setBankMoney', [money])

    def setBankMoney(self, money):
        self.bankMoney = money

    def getBankMoney(self):
        return self.bankMoney

    def b_setEmblems(self, emblems):
        self.setEmblems(emblems)
        self.d_setEmblems(emblems)

    def setEmblems(self, emblems):
        self.emblems = emblems

    def d_setEmblems(self, emblems):
        if simbase.air.wantEmblems:
            self.sendUpdate('setEmblems', [emblems])

    def getEmblems(self):
        return self.emblems

    def addEmblems(self, emblemsToAdd):
        newEmblems = self.emblems[:]
        for i in range(ToontownGlobals.NumEmblemTypes):
            newEmblems[i] += emblemsToAdd[i]

        self.b_setEmblems(newEmblems)

    def subtractEmblems(self, emblemsToSubtract):
        newEmblems = self.emblems[:]
        for i in range(ToontownGlobals.NumEmblemTypes):
            newEmblems[i] -= emblemsToSubtract[i]

        self.b_setEmblems(newEmblems)

    def isEnoughEmblemsToBuy(self, itemEmblemPrices):
        for emblemIndex, emblemPrice in enumerate(itemEmblemPrices):
            if emblemIndex >= len(self.emblems):
                return False
            if self.emblems[emblemIndex] < emblemPrice:
                return False

        return True

    def b_setGameTickets(self, tickets):
        # type: (int) -> None
        self.setGameTickets(tickets)
        self.d_setGameTickets(tickets)

    def d_setGameTickets(self, tickets):
        # type: (int) -> None
        self.sendUpdate('setGameTickets', [tickets])

    def setGameTickets(self, tickets):
        # type: (int) -> None
        if tickets < 0:
            simbase.air.writeServerEvent('suspicious', self.doId,
                                         f'toon tried to set gameticket count to {tickets}, forcing to zero')
            tickets = 0
        self.gameTickets = tickets

    def getGameTickets(self):
        # type: () -> int
        return self.gameTickets

    def addGameTickets(self, tickets):
        # type: (int) -> None
        """
        Adds [tickets] amount of gametickets to the players inventory, then updates it
        :param tickets: number of tickets to add
        """
        tickets = tickets + self.gameTickets
        self.b_setGameTickets(tickets)

    def takeGameTickets(self, tickets):
        # type: (int) -> bool
        """
        Takes [tickets] amount of gametickets from the players inventory, then updates it
        :param tickets: number of tickets to take
        :return: True if successful, false if the player doesn't have enough
        """
        if self.gameTickets - tickets < 0:
            # player doesnt have enough tickets, return false
            return False

        else:
            self.b_setGameTickets(self.gameTickets - tickets)
            return True

    def tossPie(self, x, y, z, h, p, r, sequence, power, timestamp32):
        if not self.validate(self.doId, self.numPies > 0, 'tossPie with no pies available'):
            return
        if self.numPies != ToontownGlobals.FullPies:
            self.b_setNumPies(self.numPies - 1)

    def useFeather(self, x, y, z, h, p, r, timestamp32):
        if not self.validate(self.doId, self.numPies > 0, 'useFeather with no feathers available'):
            return
        self.pieTimestamp = timestamp32
        if self.numPies != ToontownGlobals.FullPies:
            self.b_setNumPies(self.numPies - 1)

    def b_setNumPies(self, numPies):
        self.setNumPies(numPies)
        self.d_setNumPies(numPies)

    def d_setNumPies(self, numPies):
        self.sendUpdate('setNumPies', [numPies])

    def setNumPies(self, numPies):
        self.numPies = numPies

    def b_setPieType(self, pieType):
        self.setPieType(pieType)
        self.d_setPieType(pieType)

    def d_setPieType(self, pieType):
        self.sendUpdate('setPieType', [pieType])

    def setPieType(self, pieType):
        self.pieType = pieType

    def d_setTrophyScore(self, score):
        self.sendUpdate('setTrophyScore', [score])

    def stopToonUp(self):
        taskMgr.remove(self.uniqueName('safeZoneToonUp'))
        self.ignore(self.air.getAvatarExitEvent(self.getDoId()))

    def startToonUp(self, healFrequency):
        self.stopToonUp()
        self.healFrequency = healFrequency
        self.__waitForNextToonUp()

    def __waitForNextToonUp(self):
        taskMgr.doMethodLater(self.healFrequency, self.toonUpTask, self.uniqueName('safeZoneToonUp'))

    def toonUpTask(self, task):
        if not self.isToonedUp():
            self.toonUp(self.ToonUpTaskAmount)
        self.__waitForNextToonUp()
        return Task.done

    def toonUp(self, hpGained, quietly = 0, sendTotal = 1):
        if hpGained > self.maxHp:
            hpGained = self.maxHp
        if not quietly:
            self.sendUpdate('toonUp', [hpGained])
        if self.hp + hpGained <= 0:
            self.hp += hpGained
        else:
            self.hp = max(self.hp, 0) + hpGained
        clampedHp = min(self.hp, self.maxHp)
        if not self.hpOwnedByBattle:
            self.hp = clampedHp
        if sendTotal and not self.hpOwnedByBattle:
            self.d_setHp(clampedHp)

    def isToonedUp(self):
        return self.hp >= self.maxHp

    def makeBlackCat(self):
        if self.dna.getAnimal() != 'cat':
            return 'not a cat'
        self.air.writeServerEvent('blackCat', self.doId, '')
        newDna = ToonDNA.ToonDNA()
        newDna.makeFromNetString(self.dna.makeNetString())
        black = ToonDNA.BlackColor
        newDna.updateToonProperties(armColor=black, legColor=black, headColor=black)
        self.b_setDNAString(newDna.makeNetString())
        return None

    def b_announceBingo(self):
        self.d_announceBingo()
        self.announceBingo()

    def d_announceBingo(self):
        self.sendUpdate('announceBingo', [])

    def announceBingo(self):
        pass

    if __dev__:

        def _logGarbage(self):
            if self.isPlayerControlled():
                DistributedPlayerAI.DistributedPlayerAI._logGarbage(self)

    def reqSCResistance(self, msgIndex, nearbyPlayers):
        self.d_setSCResistance(msgIndex, nearbyPlayers)

    def d_setSCResistance(self, msgIndex, nearbyPlayers):
        if not ResistanceChat.validateId(msgIndex):
            self.air.writeServerEvent('suspicious', self.doId, 'said resistance %s, which is invalid.' % msgIndex)
            return
        if not self.removeResistanceMessage(msgIndex):
            self.air.writeServerEvent('suspicious', self.doId, 'said resistance %s, but does not have it.' % msgIndex)
            return
        if hasattr(self, 'autoResistanceRestock') and self.autoResistanceRestock:
            self.restockAllResistanceMessages(1)
        affectedPlayers = []
        msgType, itemIndex = ResistanceChat.decodeId(msgIndex)
        for toonId in nearbyPlayers:
            toon = self.air.doId2do.get(toonId)
            if not toon:
                self.notify.warning('%s said resistance %s for %s; not on server' % (self.doId, msgIndex, toonId))
            elif toon.__class__ != DistributedToonAI:
                self.air.writeServerEvent('suspicious', self.doId, 'said resistance %s for %s; object of type %s' % (msgIndex, toonId, toon.__class__.__name__))
            elif toonId in affectedPlayers:
                self.air.writeServerEvent('suspicious', self.doId, 'said resistance %s for %s twice in same message.' % (msgIndex, toonId))
            else:
                canTakeToonDownDamage = toon.getTakeToonDownDamage() or self.getAccessLevel() >= 200 and toonId != self.doId
                if msgType != ResistanceChat.RESISTANCE_GREEN or (msgType == ResistanceChat.RESISTANCE_GREEN and canTakeToonDownDamage):
                    toon.doResistanceEffect(msgIndex)
                affectedPlayers.append(toonId)

        if len(affectedPlayers) > 50:
            self.air.writeServerEvent('suspicious', self.doId, 'said resistance %s for %s toons.' % (msgIndex, len(affectedPlayers)))
            self.notify.warning('%s said resistance %s for %s toons: %s' % (self.doId, msgIndex, len(affectedPlayers), affectedPlayers))
        self.sendUpdate('setSCResistance', [msgIndex, affectedPlayers])
        uniteType = ResistanceChat.getMenuName(msgIndex)
        value = ResistanceChat.getItemValue(msgIndex)
        self.air.writeServerEvent('resistanceChat', self.zoneId, '%s|%s|%s|%s' % (self.doId, uniteType, value, affectedPlayers))

    def doResistanceEffect(self, msgIndex):
        msgType, itemIndex = ResistanceChat.decodeId(msgIndex)
        msgValue = ResistanceChat.getItemValue(msgIndex)
        if msgType == ResistanceChat.RESISTANCE_TOONUP:
            if msgValue == -1:
                self.toonUp(self.maxHp)
            else:
                self.toonUp(msgValue)
            self.notify.debug('Toon-up for ' + self.name)
        elif msgType == ResistanceChat.RESISTANCE_RESTOCK:
            self.inventory.NPCMaxOutInv(msgValue)
            self.d_setInventory(self.inventory.makeNetString())
            self.notify.debug('Restock for ' + self.name)
        elif msgType == ResistanceChat.RESISTANCE_MONEY:
            if msgValue == -1:
                self.addMoney(999999)
            else:
                self.addMoney(msgValue)
            self.notify.debug('Money for ' + self.name)
        elif msgType == ResistanceChat.RESISTANCE_GREEN:
            if msgValue == -1:
                self.takeDamage(self.maxHp)
            else:
                self.takeDamage(msgValue)
            self.notify.debug('Toon-down for ' + self.name)

    def squish(self, damage):
        self.takeDamage(damage)

    if simbase.wantKarts:

        def hasKart(self):
            return self.kartDNA[KartDNA.bodyType] != -1

        def b_setTickets(self, numTickets):
            if numTickets > RaceGlobals.MaxTickets:
                numTickets = RaceGlobals.MaxTickets
            self.d_setTickets(numTickets)
            self.setTickets(numTickets)

        def d_setTickets(self, numTickets):
            if numTickets > RaceGlobals.MaxTickets:
                numTickets = RaceGlobals.MaxTickets
            self.sendUpdate('setTickets', [numTickets])

        def setTickets(self, numTickets):
            if numTickets > RaceGlobals.MaxTickets:
                numTickets = RaceGlobals.MaxTickets
            self.tickets = numTickets

        def getTickets(self):
            return self.tickets

        def b_setKartingTrophies(self, trophyList):
            self.setKartingTrophies(trophyList)
            self.d_setKartingTrophies(trophyList)

        def setKartingTrophies(self, trophyList):
            self.notify.debug('setting kartingTrophies to %s' % trophyList)
            self.kartingTrophies = trophyList

        def d_setKartingTrophies(self, trophyList):
            self.sendUpdate('setKartingTrophies', [trophyList])

        def getKartingTrophies(self):
            return self.kartingTrophies

        def b_setKartingHistory(self, history):
            self.setKartingHistory(history)
            self.d_setKartingHistory(history)

        def setKartingHistory(self, history):
            self.notify.debug('setting kartingHistory to %s' % history)
            self.kartingHistory = history

        def d_setKartingHistory(self, history):
            self.sendUpdate('setKartingHistory', [history])

        def getKartingHistory(self):
            return self.kartingHistory

        def b_setKartingPersonalBest(self, bestTimes):
            best1 = bestTimes[0:6]
            best2 = bestTimes[6:]
            self.setKartingPersonalBest(best1)
            self.setKartingPersonalBest2(best2)
            self.d_setKartingPersonalBest(bestTimes)

        def d_setKartingPersonalBest(self, bestTimes):
            best1 = bestTimes[0:6]
            best2 = bestTimes[6:]
            self.sendUpdate('setKartingPersonalBest', [best1])
            self.sendUpdate('setKartingPersonalBest2', [best2])

        def setKartingPersonalBest(self, bestTimes):
            self.notify.debug('setting karting to %s' % bestTimes)
            self.kartingPersonalBest = bestTimes

        def setKartingPersonalBest2(self, bestTimes2):
            self.notify.debug('setting karting2 to %s' % bestTimes2)
            self.kartingPersonalBest2 = bestTimes2

        def getKartingPersonalBest(self):
            return self.kartingPersonalBest

        def getKartingPersonalBest2(self):
            return self.kartingPersonalBest2

        def getKartingPersonalBestAll(self):
            return self.kartingPersonalBest + self.kartingPersonalBest2

        def setKartDNA(self, kartDNA):
            self.b_setKartBodyType(kartDNA[KartDNA.bodyType])
            self.b_setKartBodyColor(kartDNA[KartDNA.bodyColor])
            self.b_setKartAccColor(kartDNA[KartDNA.accColor])
            self.b_setKartEngineBlockType(kartDNA[KartDNA.ebType])
            self.b_setKartSpoilerType(kartDNA[KartDNA.spType])
            self.b_setKartFrontWheelWellType(kartDNA[KartDNA.fwwType])
            self.b_setKartBackWheelWellType(kartDNA[KartDNA.bwwType])
            self.b_setKartRimType(kartDNA[KartDNA.rimsType])
            self.b_setKartDecalType(kartDNA[KartDNA.decalType])

        def b_setKartBodyType(self, bodyType):
            self.d_setKartBodyType(bodyType)
            self.setKartBodyType(bodyType)

        def d_setKartBodyType(self, bodyType):
            self.sendUpdate('setKartBodyType', [bodyType])

        def setKartBodyType(self, bodyType):
            self.kartDNA[KartDNA.bodyType] = bodyType

        def getKartBodyType(self):
            return self.kartDNA[KartDNA.bodyType]

        def b_setKartBodyColor(self, bodyColor):
            self.d_setKartBodyColor(bodyColor)
            self.setKartBodyColor(bodyColor)

        def d_setKartBodyColor(self, bodyColor):
            self.sendUpdate('setKartBodyColor', [bodyColor])

        def setKartBodyColor(self, bodyColor):
            self.kartDNA[KartDNA.bodyColor] = bodyColor

        def getKartBodyColor(self):
            return self.kartDNA[KartDNA.bodyColor]

        def b_setKartAccessoryColor(self, accColor):
            self.d_setKartAccessoryColor(accColor)
            self.setKartAccessoryColor(accColor)

        def d_setKartAccessoryColor(self, accColor):
            self.sendUpdate('setKartAccessoryColor', [accColor])

        def setKartAccessoryColor(self, accColor):
            self.kartDNA[KartDNA.accColor] = accColor

        def getKartAccessoryColor(self):
            return self.kartDNA[KartDNA.accColor]

        def b_setKartEngineBlockType(self, ebType):
            self.d_setKartEngineBlockType(ebType)
            self.setKartEngineBlockType(ebType)

        def d_setKartEngineBlockType(self, ebType):
            self.sendUpdate('setKartEngineBlockType', [ebType])

        def setKartEngineBlockType(self, ebType):
            self.kartDNA[KartDNA.ebType] = ebType

        def getKartEngineBlockType(self):
            return self.kartDNA[KartDNA.ebType]

        def b_setKartSpoilerType(self, spType):
            self.d_setKartSpoilerType(spType)
            self.setKartSpoilerType(spType)

        def d_setKartSpoilerType(self, spType):
            self.sendUpdate('setKartSpoilerType', [spType])

        def setKartSpoilerType(self, spType):
            self.kartDNA[KartDNA.spType] = spType

        def getKartSpoilerType(self):
            return self.kartDNA[KartDNA.spType]

        def b_setKartFrontWheelWellType(self, fwwType):
            self.d_setKartFrontWheelWellType(fwwType)
            self.setKartFrontWheelWellType(fwwType)

        def d_setKartFrontWheelWellType(self, fwwType):
            self.sendUpdate('setKartFrontWheelWellType', [fwwType])

        def setKartFrontWheelWellType(self, fwwType):
            self.kartDNA[KartDNA.fwwType] = fwwType

        def getKartFrontWheelWellType(self):
            return self.kartDNA[KartDNA.fwwType]

        def b_setKartBackWheelWellType(self, bwwType):
            self.d_setKartBackWheelWellType(bwwType)
            self.setKartBackWheelWellType(bwwType)

        def d_setKartBackWheelWellType(self, bwwType):
            self.sendUpdate('setKartBackWheelWellType', [bwwType])

        def setKartBackWheelWellType(self, bwwType):
            self.kartDNA[KartDNA.bwwType] = bwwType

        def getKartBackWheelWellType(self):
            return self.kartDNA[KartDNA.bwwType]

        def b_setKartRimType(self, rimsType):
            self.d_setKartRimType(rimsType)
            self.setKartRimType(rimsType)

        def d_setKartRimType(self, rimsType):
            self.sendUpdate('setKartRimType', [rimsType])

        def setKartRimType(self, rimsType):
            self.kartDNA[KartDNA.rimsType] = rimsType

        def getKartRimType(self):
            return self.kartDNA[KartDNA.rimsType]

        def b_setKartDecalType(self, decalType):
            self.d_setKartDecalType(decalType)
            self.setKartDecalType(decalType)

        def d_setKartDecalType(self, decalType):
            self.sendUpdate('setKartDecalType', [decalType])

        def setKartDecalType(self, decalType):
            self.kartDNA[KartDNA.decalType] = decalType

        def getKartDecalType(self):
            return self.kartDNA[KartDNA.decalType]

        def b_setKartAccessoriesOwned(self, accessories):
            self.d_setKartAccessoriesOwned(accessories)
            self.setKartAccessoriesOwned(accessories)

        def d_setKartAccessoriesOwned(self, accessories):
            self.sendUpdate('setKartAccessoriesOwned', [accessories])

        def setKartAccessoriesOwned(self, accessories):
            if (__debug__):
                import pdb
            self.accessories = accessories

        def getKartAccessoriesOwned(self):
            owned = copy.deepcopy(self.accessories)
            while InvalidEntry in owned:
                owned.remove(InvalidEntry)

            return owned

        def addOwnedAccessory(self, accessoryId):
            print('in add owned accessory')
            if accessoryId in AccessoryDict:
                if self.accessories.count(accessoryId) > 0:
                    self.air.writeServerEvent('suspicious', self.doId, 'attempt to add accessory %s which is already owned!' % accessoryId)
                    return
                if self.accessories.count(InvalidEntry) > 0:
                    accList = list(self.accessories)
                    index = self.accessories.index(InvalidEntry)
                    accList[index] = accessoryId
                    self.b_setKartAccessoriesOwned(accList)
                else:
                    self.air.writeServerEvent('suspicious', self.doId, 'attempt to add accessory %s when accessory inventory is full!' % accessoryId)
                    return
            else:
                self.air.writeServerEvent('suspicious', self.doId, 'attempt to add accessory %s which is not a valid accessory.' % accessoryId)
                return

        def removeOwnedAccessory(self, accessoryId):
            if accessoryId in AccessoryDict:
                if self.accessories.count(accessoryId) == 0:
                    self.air.writeServerEvent('suspicious', self.doId, 'attempt to remove accessory %s which is not currently owned!' % accessoryId)
                    return
                else:
                    accList = list(self.accessories)
                    index = self.accessories.index(accessoryId)
                    accList[index] = InvalidEntry
                    self.air.writeServerEvent('deletedKartingAccessory', self.doId, '%s' % accessoryId)
                    self.b_setKartAccessoriesOwned(accList)
            else:
                self.air.writeServerEvent('suspicious', self.doId, 'attempt to remove accessory %s which is not a valid accessory.' % accessoryId)
                return

        def updateKartDNAField(self, dnaField, fieldValue):
            if not checkKartFieldValidity(dnaField):
                self.air.writeServerEvent('suspicious', self.doId, 'attempt to update to dna value  %s in the invalid field %s' % (fieldValue, dnaField))
                return
            if dnaField == KartDNA.bodyType:
                if fieldValue not in list(KartDict.keys()) and fieldValue != InvalidEntry:
                    self.air.writeServerEvent('suspicious', self.doId, 'attempt to update kart body to invalid body %s.' % fieldValue)
                    return
                self.b_setKartBodyType(fieldValue)
            else:
                accFields = [KartDNA.ebType,
                 KartDNA.spType,
                 KartDNA.fwwType,
                 KartDNA.bwwType,
                 KartDNA.rimsType,
                 KartDNA.decalType]
                colorFields = [KartDNA.bodyColor, KartDNA.accColor]
                if dnaField in accFields:
                    if fieldValue == InvalidEntry:
                        self.__updateKartDNAField(dnaField, fieldValue)
                    else:
                        if fieldValue not in self.accessories:
                            self.air.writeServerEvent('suspicious', self.doId, 'attempt to update to accessory %s which is not currently owned.' % fieldValue)
                            return
                        field = getAccessoryType(fieldValue)
                        if field == InvalidEntry:
                            self.air.writeServerEvent('suspicious', self.doId, 'attempt to update accessory %s in an illegal field %s' % (fieldValue, field))
                            return
                        elif field != dnaField:
                            self.air.writeServerEvent('suspicious', self.doId, 'attempt to update accessory %s in a field %s that does not match client specified field %s' % (fieldValue, field, dnaField))
                            return
                        self.__updateKartDNAField(dnaField, fieldValue)
                elif dnaField in colorFields:
                    if fieldValue == InvalidEntry:
                        self.__updateKartDNAField(dnaField, fieldValue)
                    else:
                        if fieldValue not in self.accessories:
                            if fieldValue != getDefaultColor():
                                self.air.writeServerEvent('suspicious', self.doId, 'attempt to update to color %s which is not owned!' % fieldValue)
                                return
                            elif fieldValue == getDefaultColor() and self.kartDNA[dnaField] != InvalidEntry:
                                self.air.writeServerEvent('suspicious', self.doId, 'attempt to update to default color %s which is not owned!' % fieldValue)
                                return
                        if getAccessoryType(fieldValue) != KartDNA.bodyColor:
                            self.air.writeServerEvent('suspicious', self.doId, 'attempt to update invalid color %s for dna field %s' % (fieldValue, dnaField))
                            return
                        self.__updateKartDNAField(dnaField, fieldValue)
                else:
                    self.air.writeServerEvent('suspicious', self.doId, 'attempt to udpate accessory %s in the invalid field %s' % (fieldValue, dnaField))
                    return

        def __updateKartDNAField(self, dnaField, fieldValue):
            if dnaField == KartDNA.bodyColor:
                self.b_setKartBodyColor(fieldValue)
            elif dnaField == KartDNA.accColor:
                self.b_setKartAccessoryColor(fieldValue)
            elif dnaField == KartDNA.ebType:
                self.b_setKartEngineBlockType(fieldValue)
            elif dnaField == KartDNA.spType:
                self.b_setKartSpoilerType(fieldValue)
            elif dnaField == KartDNA.fwwType:
                self.b_setKartFrontWheelWellType(fieldValue)
            elif dnaField == KartDNA.bwwType:
                self.b_setKartBackWheelWellType(fieldValue)
            elif dnaField == KartDNA.rimsType:
                self.b_setKartRimType(fieldValue)
            elif dnaField == KartDNA.decalType:
                self.b_setKartDecalType(fieldValue)

        def setAllowSoloRace(self, allowSoloRace):
            self.allowSoloRace = allowSoloRace

        def setAllowRaceTimeout(self, allowRaceTimeout):
            self.allowRaceTimeout = allowRaceTimeout

    if simbase.wantPets:

        def getPetId(self):
            return self.petId

        def b_setPetId(self, petId):
            self.d_setPetId(petId)
            self.setPetId(petId)
            self.air.updateOnlineAvatar(self)

        def d_setPetId(self, petId):
            self.sendUpdate('setPetId', [petId])

        def setPetId(self, petId):
            self.petId = petId

        def getPetTrickPhrases(self):
            return self.petTrickPhrases

        def b_setPetTrickPhrases(self, tricks):
            self.setPetTrickPhrases(tricks)
            self.d_setPetTrickPhrases(tricks)

        def d_setPetTrickPhrases(self, tricks):
            self.sendUpdate('setPetTrickPhrases', [tricks])

        def setPetTrickPhrases(self, tricks):
            self.petTrickPhrases = tricks

        def deletePet(self):
            if self.petId == 0:
                self.notify.warning("this toon doesn't have a pet to delete!")
                return
            simbase.air.petMgr.deleteToonsPet(self.doId)

        def setPetMovie(self, petId, flag):
            self.notify.debug('setPetMovie: petId: %s, flag: %s' % (petId, flag))
            pet = simbase.air.doId2do.get(petId)
            if pet is not None:
                if pet.__class__.__name__ == 'DistributedPetAI':
                    pet.handleAvPetInteraction(flag, self.getDoId())
                else:
                    self.air.writeServerEvent('suspicious', self.doId, 'setPetMovie: playing pet movie %s on non-pet object %s' % (flag, petId))
            return

        def setPetTutorialDone(self, bDone):
            self.notify.debug('setPetTutorialDone')
            self.bPetTutorialDone = True

        def setFishBingoTutorialDone(self, bDone):
            self.notify.debug('setFishBingoTutorialDone')
            self.bFishBingoTutorialDone = True

        def setFishBingoMarkTutorialDone(self, bDone):
            self.notify.debug('setFishBingoMarkTutorialDone')
            self.bFishBingoMarkTutorialDone = True

        def enterEstate(self, ownerId, zoneId):
            DistributedToonAI.notify.debug('enterEstate: %s %s %s' % (self.doId, ownerId, zoneId))
            if self.wasInEstate():
                self.cleanupEstateData()
            collSphere = CollisionSphere(0, 0, 0, self.getRadius())
            collNode = CollisionNode('toonColl-%s' % self.doId)
            collNode.addSolid(collSphere)
            collNode.setFromCollideMask(BitMask32.allOff())
            collNode.setIntoCollideMask(ToontownGlobals.WallBitmask)
            self.collNodePath = self.attachNewNode(collNode)
            taskMgr.add(self._moveSphere, self._getMoveSphereTaskName(), priority=OTPGlobals.AICollMovePriority)
            self.inEstate = 1
            self.estateOwnerId = ownerId
            self.estateZones = simbase.air.estateMgr.getEstateZones(ownerId)
            self.estateHouseZones = simbase.air.estateMgr.getEstateHouseZones(ownerId)
            if self.isPlayerControlled():
                self.enterPetLook()

        def enterPark(self):
            collSphere = CollisionSphere(0, 0, 0, self.getRadius())
            collNode = CollisionNode('toonColl-%s' % self.doId)
            collNode.addSolid(collSphere)
            collNode.setFromCollideMask(BitMask32.allOff())
            collNode.setIntoCollideMask(ToontownGlobals.WallBitmask)
            self.collNodePath = self.attachNewNode(collNode)
            taskMgr.add(self._moveSphere, self._getMoveSphereTaskName(), priority=OTPGlobals.AICollMovePriority)
            self.inPark = 1
            if self.isPlayerControlled():
                self.enterPetLook()

        def _getPetLookerBodyNode(self):
            return self.collNodePath

        def _getMoveSphereTaskName(self):
            return 'moveSphere-%s' % self.doId

        def _moveSphere(self, task):
            try:
                self.collNodePath.setZ(self.getRender(), 0)
            except AttributeError:
                return Task.done
            return Task.cont

        def isInEstate(self):
            return hasattr(self, 'inEstate') and self.inEstate

        def isInPark(self):
            return hasattr(self, 'inPark') and self.inPark

        def exitEstate(self, ownerId = None, zoneId = None):
            DistributedToonAI.notify.debug('exitEstate: %s %s %s' % (self.doId, ownerId, zoneId))
            DistributedToonAI.notify.debug('current zone: %s' % self.zoneId)
            if self.isPlayerControlled():
                self.exitPetLook()
            taskMgr.remove(self._getMoveSphereTaskName())
            if self.collNodePath:
                self.collNodePath.removeNode()
            del self.estateOwnerId
            del self.estateHouseZones
            del self.inEstate
            self._wasInEstate = 1

        def exitPark(self):
            if self.isPlayerControlled():
                self.exitPetLook()
            taskMgr.remove(self._getMoveSphereTaskName())
            if self.collNodePath:
                self.collNodePath.removeNode()
            self._wasInPark = 1

        def wasInEstate(self):
            return hasattr(self, '_wasInEstate') and self._wasInEstate

        def wasInPark(self):
            return hasattr(self, '_wasInPark') and self._wasInPark

        def cleanupEstateData(self):
            del self.estateZones
            del self._wasInEstate

        def setSC(self, msgId):
            DistributedToonAI.notify.debug('setSC: %s' % msgId)
            from toontown.pets import PetObserve
            PetObserve.send(self.zoneId, PetObserve.getSCObserve(msgId, self.doId))
            messenger.send('speedchat-phrase-said', [self.doId, self.zoneId, msgId])
            if msgId in [21006]:
                self.setHatePets(1)
            elif msgId in [21000,
             21001,
             21003,
             21004,
             21200,
             21201,
             21202,
             21203,
             21204,
             21205,
             21206]:
                self.setHatePets(0)
            # This method is a new feature we're adding to help people out who are playing Legit Mode
            # It can get quite annoying when your task building is taken over and there is no option to switch districts
            # So why not call an NPC Toon for help? Well now you can! At least, as long as this setting is enabled)
            elif msgId == 1410 and ServerSettings.BuildingHelpers.get():
                # If we're in the Outskirts, be lenient with the visgroups
                # Use the branch zone because sometimes we can be in other zones
                lenient = False
                if ZoneUtil.getCanonicalBranchZone(self.zoneId) == ToontownGlobals.ToontownOutskirts:
                    lenient = True
                self.helperRecoverBuilding(lenient)

        def setSCCustom(self, msgId):
            DistributedToonAI.notify.debug('setSCCustom: %s' % msgId)
            from toontown.pets import PetObserve
            PetObserve.send(self.zoneId, PetObserve.getSCObserve(msgId, self.doId))

    def setHatePets(self, hate):
        self.hatePets = hate

    def takeOutKart(self, zoneId = None):
        if not self.kart:
            from toontown.racing import DistributedVehicleAI
            self.kart = DistributedVehicleAI.DistributedVehicleAI(self.air, self.doId)
            if zoneId:
                self.kart.generateWithRequired(zoneId)
            else:
                self.kart.generateWithRequired(self.zoneId)

    def reqCogSummons(self, type, suitIndex, invasionAmount):
        if type not in ('single', 'building', 'invasion'):
            self.air.writeServerEvent('suspicious', self.doId, 'invalid cog summons type: %s' % type)
            self.sendUpdate('cogSummonsResponse', ['fail', suitIndex, 0])
            return
        if suitIndex >= len(SuitDNA.suitHeadTypes):
            self.air.writeServerEvent('suspicious', self.doId, 'invalid suitIndex: %s' % suitIndex)
            self.sendUpdate('cogSummonsResponse', ['fail', suitIndex, 0])
            return
        if not self.hasCogSummons(suitIndex, type):
            self.air.writeServerEvent('suspicious', self.doId, 'bogus cog summons')
            self.sendUpdate('cogSummonsResponse', ['fail', suitIndex, 0])
            return
        returnCode = None
        if type == 'single':
            returnCode = self.doSummonSingleCog(suitIndex)
        elif type == 'building':
            # If we're in the Outskirts, be lenient with the visgroups
            # Use the branch zone because sometimes we can be in other zones
            lenient = False
            if ZoneUtil.getCanonicalBranchZone(self.zoneId) == ToontownGlobals.ToontownOutskirts:
                lenient = True
            returnCode = self.doBuildingTakeover(suitIndex, lenient)
        elif type == 'invasion':
            returnCode = self.doCogInvasion(suitIndex, invasionAmount)
        if returnCode:
            if returnCode[0] == 'success':
                self.air.writeServerEvent('cogSummoned', self.doId, '%s|%s|%s' % (type, suitIndex, self.zoneId))
                self.removeCogSummonsEarned(suitIndex, type)
            self.sendUpdate('cogSummonsResponse', returnCode)
        return

    def doSummonSingleCog(self, suitIndex):
        if suitIndex >= len(SuitDNA.suitHeadTypes):
            self.notify.warning('Bad suit index: %s' % suitIndex)
            return ['badIndex', suitIndex, 0]
        suitName = SuitDNA.suitHeadTypes[suitIndex]
        streetId = ZoneUtil.getBranchZone(self.zoneId)
        if streetId not in self.air.suitPlanners:
            return ['badlocation', suitIndex, 0]
        sp = self.air.suitPlanners[streetId]
        map = sp.getZoneIdToPointMap()
        zones = [self.zoneId, self.zoneId - 1, self.zoneId + 1]
        for zoneId in zones:
            if zoneId in map:
                points = map[zoneId][:]
                suit = sp.createNewSuit([], points, suitName=suitName)
                if suit:
                    return ['success', suitIndex, 0]

        return ['badlocation', suitIndex, 0]

    def doBuildingTakeover(self, suitIndex, lenient=False, extraTracks=[]):
        streetId = ZoneUtil.getBranchZone(self.zoneId)
        if streetId not in self.air.suitPlanners:
            self.notify.warning('Street %d is not known.' % streetId)
            return ['badlocation', suitIndex, 0]
        sp = self.air.suitPlanners[streetId]
        building = self.findClosestDoor(lenient)
        if building == None:
            return ['badlocation', suitIndex, 0]
        if suitIndex >= len(SuitDNA.suitHeadTypes):
            self.notify.warning('Bad suit index: %s' % suitIndex)
            return ['badIndex', suitIndex, 0]
        suitName = SuitDNA.suitHeadTypes[suitIndex]
        track = SuitDNA.getSuitDept(suitName)
        tracks = [track]
        tracks.extend(extraTracks)
        level = sp.pickLevel()
        building.suitTakeOver(tracks, level, None)
        self.notify.warning('cogTakeOver %s %s %d %d' % (track,
         level,
         building.block,
         self.zoneId))
        return ['success', suitIndex, building.doId]

    def doCogInvasion(self, suitIndex, invasionAmount):
        invMgr = self.air.suitInvasionManager
        if invMgr.getInvading():
            returnCode = 'busy'
        elif not 1000 <= invasionAmount <= 25000:
            returnCode = 'tooManyCogs'
        else:
            if suitIndex >= len(SuitDNA.suitHeadTypes):
                self.notify.warning('Bad suit index: %s' % suitIndex)
                return ['badIndex', suitIndex, 0]
            cogList = [SuitDNA.suitHeadTypes[suitIndex]]
            if invMgr.startInvasion(cogList, invasionAmount, False, False, summonerId = self.getDoId()):
                returnCode = 'success'
            else:
                returnCode = 'fail'
        return [returnCode, suitIndex, 0]

    def b_setCogSummonsEarned(self, cogSummonsEarned):
        self.d_setCogSummonsEarned(cogSummonsEarned)
        self.setCogSummonsEarned(cogSummonsEarned)

    def d_setCogSummonsEarned(self, cogSummonsEarned):
        self.sendUpdate('setCogSummonsEarned', [cogSummonsEarned])

    def setCogSummonsEarned(self, cogSummonsEarned):
        self.cogSummonsEarned = cogSummonsEarned

    def getCogSummonsEarned(self):
        return self.cogSummonsEarned

    def restockAllCogSummons(self):
        numSuits = len(SuitDNA.suitHeadTypes)
        fullSetForSuit = 1 | 2 | 4
        allSummons = numSuits * [fullSetForSuit]
        self.b_setCogSummonsEarned(allSummons)

    def addCogSummonsEarned(self, suitIndex, type):
        summons = self.getCogSummonsEarned()
        curSetting = summons[suitIndex]
        if type == 'single':
            curSetting |= 1
        elif type == 'building':
            curSetting |= 2
        elif type == 'invasion':
            curSetting |= 4
        summons[suitIndex] = curSetting
        self.b_setCogSummonsEarned(summons)

    def removeCogSummonsEarned(self, suitIndex, type):
        summons = self.getCogSummonsEarned()
        curSetting = summons[suitIndex]
        if self.hasCogSummons(suitIndex, type):
            if type == 'single':
                curSetting &= -2
            elif type == 'building':
                curSetting &= -3
            elif type == 'invasion':
                curSetting &= -5
            summons[suitIndex] = curSetting
            self.b_setCogSummonsEarned(summons)
            if hasattr(self, 'autoRestockSummons') and self.autoRestockSummons:
                self.restockAllCogSummons()
            return True
        self.notify.warning("Toon %s doesn't have a %s summons for %s" % (self.doId, type, suitIndex))
        return False

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

    def hasParticularCogSummons(self, deptIndex, level, type):
        if deptIndex not in range(len(SuitDNA.suitDepts)):
            self.notify.warning('invalid parameter deptIndex %s' % deptIndex)
            return False
        if level not in range(SuitDNA.suitsPerDept):
            self.notify.warning('invalid parameter level %s' % level)
            return False
        suitIndex = deptIndex * SuitDNA.suitsPerDept + level
        retval = self.hasCogSummons(suitIndex, type)
        return retval

    def assignNewCogSummons(self, level = None, summonType = None, deptIndex = None):
        if level != None:
            if deptIndex in range(len(SuitDNA.suitDepts)):
                dept = deptIndex
            else:
                numDepts = len(SuitDNA.suitDepts)
                dept = random.randrange(0, numDepts)
            suitIndex = dept * SuitDNA.suitsPerDept + level
        elif deptIndex in range(len(SuitDNA.suitDepts)):
            randomLevel = random.randrange(0, SuitDNA.suitsPerDept)
            suitIndex = deptIndex * SuitDNA.suitsPerLevel + randomLevel
        else:
            numSuits = len(SuitDNA.suitHeadTypes)
            suitIndex = random.randrange(0, numSuits)
        if summonType in ['single', 'building', 'invasion']:
            type = summonType
        else:
            typeWeights = ['single'] * 70 + ['building'] * 25 + ['invasion'] * 5
            type = random.choice(typeWeights)
        if suitIndex >= len(SuitDNA.suitHeadTypes):
            self.notify.warning('Bad suit index: %s' % suitIndex)
        self.addCogSummonsEarned(suitIndex, type)
        return (suitIndex, type)

    def findClosestDoor(self, lenient=False):
        zoneId = self.zoneId
        streetId = ZoneUtil.getBranchZone(zoneId)
        sp = self.air.suitPlanners[streetId]
        if not sp:
            return None
        bm = sp.buildingMgr
        if not bm:
            return None
        if lenient:
            zones = range(zoneId - 50, zoneId + 51)
        else:
            zones = range(zoneId - 1, zoneId + 3)
        for zone in zones:
            for i in bm.getToonBlocks():
                building = bm.getBuilding(i)
                extZoneId, intZoneId = building.getExteriorAndInteriorZoneId()
                if not NPCToons.isZoneProtected(intZoneId):
                    if hasattr(building, 'door'):
                        if building.door.zoneId == zone or intZoneId == zoneId:
                            return building

        return None

    def helperRecoverBuilding(self, lenient=False):
        zoneId = self.zoneId
        streetId = ZoneUtil.getBranchZone(zoneId)
        sp = self.air.suitPlanners.get(streetId)
        if not sp:
            return
        bm = sp.buildingMgr
        if not bm:
            return

        if lenient:
            zones = range(zoneId - 50, zoneId + 51)
        else:
            zones = range(zoneId - 5, zoneId + 6)

        # Get all taken over buildings
        for i in bm.getSuitBlocks() + bm.getCogdoBlocks():
            building = bm.getBuilding(i)

            # Building must be close
            if zoneId not in zones:
                continue

            # Interior exists? Toons must be inside
            if hasattr(building, 'interior') and building.interior:
                continue

            # Is this a valid building?
            validBuilding = False
            # Get NPC IDs and compare to the ones in our avatar's quests
            npcsIds = building.getNpcIds()
            for questDesc in self.quests:
                toNpcId = questDesc[2]
                if toNpcId in npcsIds:
                    validBuilding = True
                    break

            if not validBuilding:
                continue

            building.fsm.request('saveByNpc', [building.isCogdo(), self.doId])
            break

    def b_setGardenTrophies(self, trophyList):
        self.setGardenTrophies(trophyList)
        self.d_setGardenTrophies(trophyList)

    def setGardenTrophies(self, trophyList):
        self.notify.debug('setting gardenTrophies to %s' % trophyList)
        self.gardenTrophies = trophyList

    def d_setGardenTrophies(self, trophyList):
        self.sendUpdate('setGardenTrophies', [trophyList])

    def getGardenTrophies(self):
        return self.gardenTrophies

    def setGardenSpecials(self, specials):
        for special in specials:
            if special[1] > 255:
                special[1] = 255

        self.gardenSpecials = specials

    def getGardenSpecials(self):
        return self.gardenSpecials

    def d_setGardenSpecials(self, specials):
        self.sendUpdate('setGardenSpecials', [specials])

    def b_setGardenSpecials(self, specials):
        for special in specials:
            if special[1] > 255:
                newCount = 255
                index = special[0]
                self.gardenSpecials.remove(special)
                self.gardenSpecials.append((index, newCount))
                self.gardenSpecials.sort()

        self.setGardenSpecials(specials)
        self.d_setGardenSpecials(specials)

    def addGardenItem(self, index, count):
        for item in self.gardenSpecials:
            if item[0] == index:
                newCount = item[1] + count
                self.gardenSpecials.remove(item)
                self.gardenSpecials.append((index, newCount))
                self.gardenSpecials.sort()
                self.b_setGardenSpecials(self.gardenSpecials)
                return

        self.gardenSpecials.append((index, count))
        self.gardenSpecials.sort()
        self.b_setGardenSpecials(self.gardenSpecials)

    def removeGardenItem(self, index, count):
        for item in self.gardenSpecials:
            if item[0] == index:
                newCount = item[1] - count
                self.gardenSpecials.remove(item)
                if newCount > 0:
                    self.gardenSpecials.append((index, newCount))
                self.gardenSpecials.sort()
                self.b_setGardenSpecials(self.gardenSpecials)
                return 1

        self.notify.warning("removing garden item %d that toon doesn't have" % index)
        return 0

    def b_setFlowerCollection(self, speciesList, varietyList):
        self.setFlowerCollection(speciesList, varietyList)
        self.d_setFlowerCollection(speciesList, varietyList)

    def d_setFlowerCollection(self, speciesList, varietyList):
        self.sendUpdate('setFlowerCollection', [speciesList, varietyList])

    def setFlowerCollection(self, speciesList, varietyList):
        self.flowerCollection = FlowerCollection.FlowerCollection()
        self.flowerCollection.makeFromNetLists(speciesList, varietyList)

    def getFlowerCollection(self):
        return self.flowerCollection.getNetLists()

    def b_setMaxFlowerBasket(self, maxFlowerBasket):
        self.d_setMaxFlowerBasket(maxFlowerBasket)
        self.setMaxFlowerBasket(maxFlowerBasket)

    def d_setMaxFlowerBasket(self, maxFlowerBasket):
        self.sendUpdate('setMaxFlowerBasket', [maxFlowerBasket])

    def setMaxFlowerBasket(self, maxFlowerBasket):
        self.maxFlowerBasket = maxFlowerBasket

    def getMaxFlowerBasket(self):
        return self.maxFlowerBasket

    def b_setFlowerBasket(self, speciesList, varietyList):
        self.setFlowerBasket(speciesList, varietyList)
        self.d_setFlowerBasket(speciesList, varietyList)

    def d_setFlowerBasket(self, speciesList, varietyList):
        self.sendUpdate('setFlowerBasket', [speciesList, varietyList])

    def setFlowerBasket(self, speciesList, varietyList):
        self.flowerBasket = FlowerBasket.FlowerBasket()
        self.flowerBasket.makeFromNetLists(speciesList, varietyList)

    def getFlowerBasket(self):
        return self.flowerBasket.getNetLists()

    def makeRandomFlowerBasket(self):
        self.flowerBasket.generateRandomBasket()
        self.d_setFlowerBasket(*self.flowerBasket.getNetLists())

    def addFlowerToBasket(self, species, variety):
        numFlower = len(self.flowerBasket)
        if numFlower >= self.maxFlowerBasket:
            self.notify.warning('addFlowerToBasket: cannot add flower, basket is full')
            return 0
        elif self.flowerBasket.addFlower(species, variety):
            self.d_setFlowerBasket(*self.flowerBasket.getNetLists())
            return 1
        else:
            self.notify.warning('addFlowerToBasket: addFlower failed')
            return 0

    def removeFlowerFromBasketAtIndex(self, index):
        if self.flowerBasket.removeFlowerAtIndex(index):
            self.d_setFlowerBasket(*self.flowerBasket.getNetLists())
            return 1
        else:
            self.notify.warning('removeFishFromTank: cannot find fish')
            return 0

    def b_setShovel(self, shovelId):
        self.d_setShovel(shovelId)
        self.setShovel(shovelId)

    def d_setShovel(self, shovelId):
        self.sendUpdate('setShovel', [shovelId])

    def setShovel(self, shovelId):
        self.shovel = shovelId

    def getShovel(self):
        return self.shovel

    def b_setShovelSkill(self, skillLevel):
        self.sendGardenEvent()
        if skillLevel >= GardenGlobals.ShovelAttributes[self.shovel]['skillPts']:
            if self.shovel < GardenGlobals.MAX_SHOVELS - 1:
                self.b_setShovel(self.shovel + 1)
                self.setShovelSkill(0)
                self.d_setShovelSkill(0)
                self.sendUpdate('promoteShovel', [self.shovel])
                self.air.writeServerEvent('garden_new_shovel', self.doId, '%d' % self.shovel)
        else:
            self.setShovelSkill(skillLevel)
            self.d_setShovelSkill(skillLevel)

    def d_setShovelSkill(self, skillLevel):
        self.sendUpdate('setShovelSkill', [skillLevel])

    def setShovelSkill(self, skillLevel):
        self.shovelSkill = skillLevel

    def getShovelSkill(self):
        return self.shovelSkill

    def b_setWateringCan(self, wateringCanId):
        self.d_setWateringCan(wateringCanId)
        self.setWateringCan(wateringCanId)

    def d_setWateringCan(self, wateringCanId):
        self.sendUpdate('setWateringCan', [wateringCanId])

    def setWateringCan(self, wateringCanId):
        self.wateringCan = wateringCanId

    def getWateringCan(self):
        return self.wateringCan

    def b_setWateringCanSkill(self, skillLevel):
        self.sendGardenEvent()
        if skillLevel >= GardenGlobals.WateringCanAttributes[self.wateringCan]['skillPts']:
            if self.wateringCan < GardenGlobals.MAX_WATERING_CANS - 1:
                self.b_setWateringCan(self.wateringCan + 1)
                self.setWateringCanSkill(0)
                self.d_setWateringCanSkill(0)
                self.sendUpdate('promoteWateringCan', [self.wateringCan])
                self.air.writeServerEvent('garden_new_wateringCan', self.doId, '%d' % self.wateringCan)
            else:
                skillLevel = GardenGlobals.WateringCanAttributes[self.wateringCan]['skillPts'] - 1
                self.setWateringCanSkill(skillLevel)
                self.d_setWateringCanSkill(skillLevel)
        else:
            self.setWateringCanSkill(skillLevel)
            self.d_setWateringCanSkill(skillLevel)

    def d_setWateringCanSkill(self, skillLevel):
        self.sendUpdate('setWateringCanSkill', [skillLevel])

    def setWateringCanSkill(self, skillLevel):
        self.wateringCanSkill = skillLevel

    def getWateringCanSkill(self):
        return self.wateringCanSkill

    def b_setTrackBonusLevel(self, trackBonusLevelArray):
        self.setTrackBonusLevel(trackBonusLevelArray)
        self.d_setTrackBonusLevel(trackBonusLevelArray)

    def d_setTrackBonusLevel(self, trackBonusLevelArray):
        self.sendUpdate('setTrackBonusLevel', [trackBonusLevelArray])

    def setTrackBonusLevel(self, trackBonusLevelArray):
        self.trackBonusLevel = trackBonusLevelArray

    def getTrackBonusLevel(self, track = None):
        if track == None:
            return self.trackBonusLevel
        else:
            return self.trackBonusLevel[track]
        return

    def checkGagBonus(self, track, level):
        trackBonus = self.getTrackBonusLevel(track)
        return trackBonus >= level

    def giveMeSpecials(self, id = None):
        print('Specials Go!!')
        self.b_setGardenSpecials([(0, 3),
         (1, 2),
         (2, 3),
         (3, 2),
         (4, 3),
         (5, 2),
         (6, 3),
         (7, 2),
         (100, 1),
         (101, 3),
         (102, 1)])

    def reqUseSpecial(self, special):
        response = self.tryToUseSpecial(special)
        self.sendUpdate('useSpecialResponse', [response])

    def tryToUseSpecial(self, special):
        estateOwnerDoId = simbase.air.estateMgr.zone2owner.get(self.zoneId)
        response = 'badlocation'
        doIHaveThisSpecial = False
        for curSpecial in self.gardenSpecials:
            if curSpecial[0] == special and curSpecial[1] > 0:
                doIHaveThisSpecial = True
                break

        if not doIHaveThisSpecial:
            return response
        if not self.doId == estateOwnerDoId:
            self.notify.warning("how did this happen, planting an item you don't own")
            return response
        if estateOwnerDoId:
            estate = simbase.air.estateMgr.estate.get(estateOwnerDoId)
            if estate and hasattr(estate, 'avIdList'):
                ownerIndex = estate.avIdList.index(estateOwnerDoId)
                if ownerIndex >= 0:
                    estate.doEpochNow(onlyForThisToonIndex=ownerIndex)
                    self.removeGardenItem(special, 1)
                    response = 'success'
                    self.air.writeServerEvent('garden_fertilizer', self.doId, '')
        return response

    def sendGardenEvent(self):
        if hasattr(self, 'estateZones') and hasattr(self, 'doId'):
            if simbase.wantPets and self.hatePets:
                PetObserve.send(self.estateZones, PetObserve.PetActionObserve(PetObserve.Actions.GARDEN, self.doId))

    def setGardenStarted(self, bStarted):
        self.gardenStarted = bStarted

    def d_setGardenStarted(self, bStarted):
        self.sendUpdate('setGardenStarted', [bStarted])

    def b_setGardenStarted(self, bStarted):
        self.setGardenStarted(bStarted)
        self.d_setGardenStarted(bStarted)

    def getGardenStarted(self):
        return self.gardenStarted

    def logSuspiciousEvent(self, eventName):
        senderId = self.air.getAvatarIdFromSender()
        eventStr = 'senderId=%s ' % senderId
        eventStr += eventName
        strSearch = re.compile('AvatarHackWarning! nodename')
        if strSearch.search(eventName, 0, 100):
            self.air.district.recordSuspiciousEventData(len(eventStr))
        self.air.writeServerEvent('suspicious', self.doId, eventStr)
        if simbase.config.GetBool('want-ban-setSCSinging', True):
            if 'invalid msgIndex in setSCSinging:' in eventName:
                if senderId == self.doId:
                    commentStr = 'Toon %s trying to call setSCSinging' % self.doId
                    simbase.air.banManager.ban(self.doId, self.DISLid, commentStr)
                else:
                    self.notify.warning('logSuspiciousEvent event=%s senderId=%s != self.doId=%s' % (eventName, senderId, self.doId))
        if simbase.config.GetBool('want-ban-setAnimState', True):
            if eventName.startswith('setAnimState: '):
                if senderId == self.doId:
                    commentStr = 'Toon %s trying to call setAnimState' % self.doId
                    simbase.air.banManager.ban(self.doId, self.DISLid, commentStr)
                else:
                    self.notify.warning('logSuspiciousEvent event=%s senderId=%s != self.doId=%s' % (eventName, senderId, self.doId))

    def getGolfTrophies(self):
        return self.golfTrophies

    def getGolfCups(self):
        return self.golfCups

    def b_setGolfHistory(self, history):
        self.setGolfHistory(history)
        self.d_setGolfHistory(history)

    def d_setGolfHistory(self, history):
        self.sendUpdate('setGolfHistory', [history])

    def setGolfHistory(self, history):
        self.notify.debug('setting golfHistory to %s' % history)
        self.golfHistory = history
        self.golfTrophies = GolfGlobals.calcTrophyListFromHistory(self.golfHistory)
        self.golfCups = GolfGlobals.calcCupListFromHistory(self.golfHistory)

    def getGolfHistory(self):
        return self.golfHistory

    def b_setGolfHoleBest(self, holeBest):
        self.setGolfHoleBest(holeBest)
        self.d_setGolfHoleBest(holeBest)

    def d_setGolfHoleBest(self, holeBest):
        packed = GolfGlobals.packGolfHoleBest(holeBest)
        self.sendUpdate('setPackedGolfHoleBest', [packed])

    def setGolfHoleBest(self, holeBest):
        self.golfHoleBest = holeBest

    def getGolfHoleBest(self):
        return self.golfHoleBest

    def getPackedGolfHoleBest(self):
        packed = GolfGlobals.packGolfHoleBest(self.golfHoleBest)
        return packed

    def setPackedGolfHoleBest(self, packedHoleBest):
        unpacked = GolfGlobals.unpackGolfHoleBest(packedHoleBest)
        self.setGolfHoleBest(unpacked)

    def b_setGolfCourseBest(self, courseBest):
        self.setGolfCourseBest(courseBest)
        self.d_setGolfCourseBest(courseBest)

    def d_setGolfCourseBest(self, courseBest):
        self.sendUpdate('setGolfCourseBest', [courseBest])

    def setGolfCourseBest(self, courseBest):
        self.golfCourseBest = courseBest

    def getGolfCourseBest(self):
        return self.golfCourseBest

    def setUnlimitedSwing(self, unlimitedSwing):
        self.unlimitedSwing = unlimitedSwing

    def getUnlimitedSwing(self):
        return self.unlimitedSwing

    def b_setUnlimitedSwing(self, unlimitedSwing):
        self.setUnlimitedSwing(unlimitedSwing)
        self.d_setUnlimitedSwing(unlimitedSwing)

    def d_setUnlimitedSwing(self, unlimitedSwing):
        self.sendUpdate('setUnlimitedSwing', [unlimitedSwing])

    def b_setPinkSlips(self, pinkSlips):
        self.d_setPinkSlips(pinkSlips)
        self.setPinkSlips(pinkSlips)

    def d_setPinkSlips(self, pinkSlips):
        self.sendUpdate('setPinkSlips', [pinkSlips])

    def setPinkSlips(self, pinkSlips):
        self.pinkSlips = pinkSlips

    def getPinkSlips(self):
        return self.pinkSlips

    def addPinkSlips(self, amountToAdd):
        pinkSlips = min(self.pinkSlips + amountToAdd, 255)
        self.b_setPinkSlips(pinkSlips)

    def removePinkSlips(self, amount):
        if hasattr(self, 'autoRestockPinkSlips') and self.autoRestockPinkSlips:
            amount = 0
        pinkSlips = max(self.pinkSlips - amount, 0)
        self.b_setPinkSlips(pinkSlips)

    def setPreviousAccess(self, access):
        self.previousAccess = access

    def b_setAccess(self, access):
        self.setAccess(access)
        self.d_setAccess(access)

    def d_setAccess(self, access):
        self.sendUpdate('setAccess', [access])

    def setAccess(self, access):
        paidStatus = simbase.config.GetString('force-paid-status', 'none')
        if paidStatus == 'unpaid':
            access = 1
        if access == OTPGlobals.AccessInvalid:
            if not __dev__:
                self.air.writeServerEvent('Setting Access', self.doId, 'setAccess not being sent by the OTP Server, changing access to unpaid')
                access = OTPGlobals.AccessVelvetRope
            elif __dev__:
                access = OTPGlobals.AccessFull
        self.setGameAccess(access)

    def setGameAccess(self, access):
        self.gameAccess = access

    def getGameAccess(self):
        return self.gameAccess

    def d_setTPose(self):
        self.sendUpdate('setTPose')

    def b_setMuzzle(self, muzzle):
        self.sendUpdate('setMuzzle', [muzzle])

    def b_setEyes(self, eyes):
        self.sendUpdate('setEyes', [eyes])

    def d_setAnimalSound(self, animalSound):
        self.sendUpdate('setAnimalSound', [animalSound])

    def d_playSound(self, sound, loop=0):
        self.sendUpdateToAvatarId(self.doId, 'playSound', [sound, loop])

    def b_setNametagStyle(self, nametagStyle):
        self.d_setNametagStyle(nametagStyle)
        self.setNametagStyle(nametagStyle)

    def d_setNametagStyle(self, nametagStyle):
        self.sendUpdate('setNametagStyle', [nametagStyle])

    def setNametagStyle(self, nametagStyle):
        self.nametagStyle = nametagStyle

    def getNametagStyle(self):
        return self.nametagStyle

    def b_setNametagType(self, nametagType):
        self.d_setNametagType(nametagType)
        self.setNametagType(nametagType)

    def d_setNametagType(self, type):
        self.sendUpdate('setNametagType', [type])

    def setNametagType(self, nametagType):
        self.nametagType = nametagType

    def getNametagType(self):
        return self.nametagType

    def b_setNametagColor(self, r, g, b):
        self.d_setNametagColor(r, g, b)
        self.setNametagColor(r, g, b)

    def d_setNametagColor(self, r, g, b):
        self.sendUpdate('setNametagColor', [r, g ,b])

    def setNametagColor(self, r, g, b):
        self.nametagColor = (r, g, b)

    def getNametagColor(self):
        return self.nametagColor

    def logMessage(self, message):
        avId = self.air.getAvatarIdFromSender()
        if __dev__:
            print('CLIENT LOG MESSAGE %s %s' % (avId, message))
        try:
            self.air.writeServerEvent('clientLog', avId, message)
        except:
            self.air.writeServerEvent('suspicious', avId, 'client sent us a clientLog that caused an exception')

    def b_setMail(self, mail):
        self.d_setMail(mail)
        self.setMail(mail)

    def d_setMail(self, mail):
        self.sendUpdate('setMail', [mail])

    def setMail(self, mail):
        self.mail = mail

    def setNumMailItems(self, numMailItems):
        self.numMailItems = numMailItems

    def setSimpleMailNotify(self, simpleMailNotify):
        self.simpleMailNotify = simpleMailNotify

    def b_setInviteMailNotify(self, inviteMailNotify):
        self.d_setInviteMailNotify(inviteMailNotify)
        self.setInviteMailNotify(inviteMailNotify)

    def d_setInviteMailNotify(self, inviteMailNotify):
        self.sendUpdate('setInviteMailNotify', [inviteMailNotify])

    def setInviteMailNotify(self, inviteMailNotify):
        self.inviteMailNotify = inviteMailNotify

    def setInvites(self, invites):
        self.invites = []
        for i in range(len(invites)):
            oneInvite = invites[i]
            newInvite = InviteInfoBase(*oneInvite)
            self.invites.append(newInvite)

    def d_setInvites(self, invites):
        self.sendUpdate('setInvites', [invites])

    def b_setInvites(self, invites):
        self.setInvites(invites)
        self.d_setInvites(invites)

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
            self.b_setInviteMailNotify(ToontownGlobals.NewItems)
        elif readButNotRepliedInvites:
            self.b_setInviteMailNotify(ToontownGlobals.OldItems)
        else:
            self.b_setInviteMailNotify(ToontownGlobals.NoItems)

    def getNumNonResponseInvites(self):
        count = 0
        for i in range(len(self.invites)):
            if self.invites[i].status == InviteStatus.NotRead or self.invites[i].status == InviteStatus.ReadButNotReplied:
                count += 1

        return count

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
                    curDate = simbase.air.toontownTimeManager.getCurServerDateTime().date()
                    if endDate < curDate:
                        appendInvite = False
            if appendInvite:
                result.append(invite)

        return result

    def getNumInvitesToShowInMailbox(self):
        result = len(self.getInvitesToShowInMailbox())
        return result

    def getOldHostedParties(self):
        return [self.air.partyBackups.getData(hostId=self.doId)]

    def getOldPartiesInvitedTo(self):
        return [self.air.partyBackups.getData(inviteeId=self.doId)]

    def setOldHostedParties(self, hostedParties=None):
        self.sendUpdate('setOldHostedParties', self.getOldHostedParties())

    def setOldPartiesInvitedTo(self, partiesInvitedTo=None):
        self.sendUpdate('setOldPartiesInvitedTo', self.getOldPartiesInvitedTo())

    def __updateArchivedParties(self):
        self.setOldHostedParties()
        self.setOldPartiesInvitedTo()

    def setHostedParties(self, hostedParties):
        self.hostedParties = []
        for i in range(len(hostedParties)):
            hostedInfo = hostedParties[i]
            newParty = PartyInfoAI(*hostedInfo)
            self.hostedParties.append(newParty)

    def setPartiesInvitedTo(self, partiesInvitedTo):
        self.partiesInvitedTo = []
        for i in range(len(partiesInvitedTo)):
            partyInfo = partiesInvitedTo[i]
            newParty = PartyInfoAI(*partyInfo)
            self.partiesInvitedTo.append(newParty)

        self.updateInviteMailNotify()
        self.checkMailboxFullIndicator()

    def getOnePartyInvitedTo(self, partyId):
        result = None
        for i in range(len(self.partiesInvitedTo)):
            partyInfo = self.partiesInvitedTo[i]
            if partyInfo.partyId == partyId:
                result = partyInfo
                break

        return result

    def setPartyReplyInfoBases(self, replies):
        self.partyReplyInfoBases = []
        for i in range(len(replies)):
            partyReply = replies[i]
            repliesForOneParty = PartyReplyInfoBase(*partyReply)
            self.partyReplyInfoBases.append(repliesForOneParty)

    def updateInvite(self, inviteKey, newStatus):
        for invite in self.invites:
            if invite.inviteKey == inviteKey:
                invite.status = newStatus
                self.updateInviteMailNotify()
                self.checkMailboxFullIndicator()
                break

    def updateReply(self, partyId, inviteeId, newStatus):
        for partyReply in self.partyReplyInfoBases:
            if partyReply.partyId == partyId:
                for reply in partyReply.replies:
                    if reply.inviteeId == inviteeId:
                        reply.inviteeId = newStatus
                        break

    def canPlanParty(self):
        nonCancelledPartiesInTheFuture = 0
        for partyInfo in self.hostedParties:
            if partyInfo.status not in (PartyGlobals.PartyStatus.Cancelled, PartyGlobals.PartyStatus.Finished, PartyGlobals.PartyStatus.NeverStarted):
                nonCancelledPartiesInTheFuture += 1
                if nonCancelledPartiesInTheFuture >= PartyGlobals.MaxHostedPartiesPerToon:
                    break

        result = nonCancelledPartiesInTheFuture < PartyGlobals.MaxHostedPartiesPerToon
        return result

    def setPartyCanStart(self, partyId):
        self.notify.debug('setPartyCanStart called passing in partyId=%s' % partyId)
        found = False
        for partyInfo in self.hostedParties:
            if partyInfo.partyId == partyId:
                partyInfo.status = PartyGlobals.PartyStatus.CanStart
                found = True
                break

        if not found:
            self.notify.warning("setPartyCanStart can't find partyId %s" % partyId)

    def setPartyStatus(self, partyId, newStatus):
        self.notify.debug('setPartyStatus  called passing in partyId=%s newStauts=%d' % (partyId, newStatus))
        found = False
        for partyInfo in self.hostedParties:
            if partyInfo.partyId == partyId:
                partyInfo.status = newStatus
                found = True
                break

        info = self.getOnePartyInvitedTo(partyId)
        if info:
            found = True
            info.status = newStatus
        if not found:
            self.notify.warning("setPartyCanStart can't find hosted or invitedTO partyId %s" % partyId)

    def b_setAwardMailboxContents(self, awardMailboxContents):
        self.setAwardMailboxContents(awardMailboxContents)
        self.d_setAwardMailboxContents(awardMailboxContents)

    def d_setAwardMailboxContents(self, awardMailboxContents):
        self.sendUpdate('setAwardMailboxContents', [awardMailboxContents.getBlob(store=CatalogItem.Customization)])

    def setAwardMailboxContents(self, awardMailboxContents):
        self.notify.debug('Setting awardMailboxContents to %s.' % awardMailboxContents)
        self.awardMailboxContents = CatalogItemList.CatalogItemList(awardMailboxContents, store=CatalogItem.Customization)
        self.notify.debug('awardMailboxContents is %s.' % self.awardMailboxContents)
        if len(awardMailboxContents) == 0:
            self.b_setAwardNotify(ToontownGlobals.NoItems)
        self.checkMailboxFullIndicator()

    def getAwardMailboxContents(self):
        return self.awardMailboxContents.getBlob(store=CatalogItem.Customization)

    def b_setAwardSchedule(self, onOrder, doUpdateLater = True):
        self.setAwardSchedule(onOrder, doUpdateLater)
        self.d_setAwardSchedule(onOrder)

    def d_setAwardSchedule(self, onOrder):
        self.sendUpdate('setAwardSchedule', [onOrder.getBlob(store=CatalogItem.Customization | CatalogItem.DeliveryDate)])

    def setAwardSchedule(self, onAwardOrder, doUpdateLater = True):
        self.onAwardOrder = CatalogItemList.CatalogItemList(onAwardOrder, store=CatalogItem.Customization | CatalogItem.DeliveryDate)
        if hasattr(self, 'name'):
            if doUpdateLater and self.air.doLiveUpdates and hasattr(self, 'air'):
                taskName = self.uniqueName('next-award-delivery')
                taskMgr.remove(taskName)
                now = int(time.time() / 60 + 0.5)
                nextItem = None
                nextTime = self.onAwardOrder.getNextDeliveryDate()
                nextItem = self.onAwardOrder.getNextDeliveryItem()
                if nextItem != None:
                    pass
                if nextTime != None:
                    duration = max(10.0, nextTime * 60 - time.time())
                    taskMgr.doMethodLater(duration, self.__deliverAwardPurchase, taskName)
        return

    def __deliverAwardPurchase(self, task):
        now = int(time.time() / 60 + 0.5)
        delivered, remaining = self.onAwardOrder.extractDeliveryItems(now)
        self.notify.info('Award Delivery for %s: %s.' % (self.doId, delivered))
        self.b_setAwardMailboxContents(self.awardMailboxContents + delivered)
        self.b_setAwardSchedule(remaining)
        if delivered:
            self.b_setAwardNotify(ToontownGlobals.NewItems)
        return Task.done

    def b_setAwardNotify(self, awardMailboxNotify):
        self.setAwardNotify(awardMailboxNotify)
        self.d_setAwardNotify(awardMailboxNotify)

    def d_setAwardNotify(self, awardMailboxNotify):
        self.sendUpdate('setAwardNotify', [awardMailboxNotify])

    def setAwardNotify(self, awardNotify):
        self.awardNotify = awardNotify

    def b_setGM(self, type, updateName=False):
        self.sendUpdate('setGM', [type])
        self.setGM(type, updateName)

    def setGM(self, type, updateName=False):
        wasGM = self._isGM
        formerType = self._gmType
        self._isGM = type != 0
        self._gmType = None
        if self._isGM:
            self._gmType = type - 1
            MaxGMType = len(TTLocalizer.GM_NAMES) - 1
            if self._gmType > MaxGMType:
                self.notify.warning('toon %s has invalid GM type: %s' % (self.doId, self._gmType))
                self._gmType = MaxGMType
        if updateName:
            self._updateGMName(formerType)
        return

    def isGM(self):
        return self._isGM

    def _nameIsPrefixed(self, prefix):
        if len(self.name) > len(prefix):
            if self.name[:len(prefix)] == prefix:
                return True
        return False

    def _updateGMName(self, formerType = None):
        if formerType is None:
            formerType = self._gmType
        name = self.name
        if formerType is not None:
            gmPrefix = TTLocalizer.GM_NAMES[formerType] + ' '
            if self._nameIsPrefixed(gmPrefix):
                name = self.name[len(gmPrefix):]
        if self._isGM:
            gmPrefix = TTLocalizer.GM_NAMES[self._gmType] + ' '
            newName = gmPrefix + name
        else:
            newName = name
        if self.name != newName:
            self.b_setName(newName)

    def b_setName(self, name):
        if config.GetBool('want-revoke-inappropriate-name', True):
            # Temporary until we fix the botting problem.
            nameList = name.lower().split(' ')
            for blockedName in self.BlockNames:
                if blockedName in nameList:
                    message = '%s found in toon name: %s' % (blockedName, name)
                    self.notify.warning(message + ' | %s' % self.doId)
                    self.air.writeServerEvent('suspicious', self.doId, message)
                    sysMsg = TTLocalizer.SetNameRevokedInappropriate + TTLocalizer.SetNameRevoked
                    self.b_setName('Toon')
                    if config.GetBool('want-kick-inappropriate-name', False):
                        self.sendSetKick(sysMsg, self)
                    else:
                        self.d_setSystemMessage(0, sysMsg)
                    return
            if len(name) > self.MaxNameLength:
                message = 'very long toon name attempt toon name: %s' % name
                self.notify.warning(message + ' | %s' % self.doId)
                self.air.writeServerEvent('suspicious', self.doId, message)
                sysMsg = TTLocalizer.SetNameRevokedTooLong % name
                sysMsg += TTLocalizer.SetNameRevoked
                self.b_setName('Toon')
                self.d_setSystemMessage(0, sysMsg)
                return
        DistributedPlayerAI.DistributedPlayerAI.b_setName(self, name)
        self.air.updateOnlineAvatar(self)
        messenger.send('toon-name-update', [self.doId, name])

    def setName(self, name):
        DistributedPlayerAI.DistributedPlayerAI.setName(self, name)

    def setModuleInfo(self, info):
        avId = self.air.getAvatarIdFromSender()
        key = config.getString('module-info-key', 'outrageous')
        self.moduleWhitelist = self.modulelist.loadWhitelistFile()
        self.moduleBlacklist = self.modulelist.loadBlacklistFile()
        for obfuscatedModule in info:
            module = ''
            p = 0
            for ch in obfuscatedModule:
                ic = ord(ch) ^ ord(key[p])
                p += 1
                if p >= len(key):
                    p = 0
                module += chr(ic)

            if module not in self.moduleWhitelist:
                if module in self.moduleBlacklist:
                    self.air.writeServerEvent('suspicious', avId, 'Black List module %s loaded into process.' % module)
                    if simbase.config.GetBool('want-ban-blacklist-module', False):
                        commentStr = 'User has blacklist module: %s attached to their game process' % module
                        dislId = self.DISLid
                        simbase.air.banManager.ban(self.doId, dislId, commentStr)
                else:
                    self.air.writeServerEvent('suspicious', avId, 'Unknown module %s loaded into process.' % module)

    def reflectTeleportQuery(self, receiverAvId):
        dg = self.dclass.aiFormatUpdate('teleportQuery', receiverAvId, receiverAvId, self.air.ourChannel, [self.doId, self.getAccessLevel() >= OTPGlobals.AccessLevelName2Int['MODERATOR']])
        self.air.send(dg)

    def reflectTeleportResponse(self, receiverAvId, available, hoodId, zoneId):
        dg = self.dclass.aiFormatUpdate('teleportResponse', receiverAvId, receiverAvId, self.air.ourChannel, [self.doId,
                                                                                                              available,
                                                                                                              hoodId,
                                                                                                              zoneId])
        self.air.send(dg)

    def reflectTeleportGiveup(self, receiverAvId):
        dg = self.dclass.aiFormatUpdate('teleportGiveup', receiverAvId, receiverAvId, self.air.ourChannel, [self.doId])
        self.air.send(dg)

    @staticmethod
    def staticGetLogicalZoneChangeAllEvent():
        return 'DOLogicalChangeZone-all'

    def _garbageInfo(self):
        if hasattr(self, 'inventory'):
            if not hasattr(self.inventory, '_createStack'):
                return 'inventory has no create stack'
            else:
                return self.inventory._createStack
        return 'no inventory'

    def b_setUnlimitedGags(self, flag):
        self.setUnlimitedGags(flag)
        self.d_setUnlimitedGags(flag)

    def d_setUnlimitedGags(self, flag):
        self.sendUpdate('setUnlimitedGags', [flag])

    def setUnlimitedGags(self, flag):
        self.unlimitedGags = flag
        if self.unlimitedGags:
            self.inventory.NPCMaxOutInv(targetTrack=-1, maxLevelIndex=6)
            self.b_setInventory(self.inventory.makeNetString())

    def getUnlimitedGags(self):
        return self.unlimitedGags

    def b_setInstaKill(self, flag):
        self.setInstaKill(flag)
        self.d_setInstaKill(flag)

    def d_setInstaKill(self, flag):
        self.sendUpdate('setInstaKill', [flag])

    def setInstaKill(self, flag):
        self.instaKill = flag

    def getInstaKill(self):
        return self.instaKill

    def b_setAutoJoin(self, flag):
        self.setAutoJoin(flag)
        self.d_setAutoJoin(flag)

    def d_setAutoJoin(self, flag):
        self.sendUpdate('setAutoJoin', [flag])

    def setAutoJoin(self, flag):
        self.autoJoin = flag

    def getAutoJoin(self):
        return self.autoJoin

    def setAlwaysHitSuits(self, alwaysHitSuits):
        self.alwaysHitSuits = alwaysHitSuits

    def getAlwaysHitSuits(self):
        return self.alwaysHitSuits

    def setCogsAlwaysMiss(self, cogsAlwaysMiss):
        self.cogsAlwaysMiss = cogsAlwaysMiss

    def getCogsAlwaysMiss(self):
        return self.cogsAlwaysMiss

    def setCogsAlwaysHit(self, cogsAlwaysHit):
        self.cogsAlwaysHit = cogsAlwaysHit

    def getCogsAlwaysHit(self):
        return self.cogsAlwaysHit

    def setTakeToonDownDamage(self, toonDownDamage):
        self.toonDownDamage = toonDownDamage

    def getTakeToonDownDamage(self):
        return self.toonDownDamage

    def b_setRun(self, state, multiplier = 3.0):
        self.setRun(state, multiplier)
        self.d_setRun(state, multiplier)

    def d_setRun(self, state, multiplier):
        self.sendUpdate('setRun', [state, multiplier])

    def setRun(self, state, multiplier):
        self.run = state
        self.runMultiplier = multiplier

    def getRun(self):
        return (self.run, self.runMultiplier)

    def d_doTeleport(self, hood):
        self.sendUpdateToAvatarId(self.doId, 'doTeleport', [hood])

    def d_setToonScale(self, scale):
        self.sendUpdate('setToonScale', [scale])

    def checkTimeout(self, timeoutName, timeout):
        if timeoutName in self.timeouts and self.timeouts[timeoutName] > time.time():
            return False
        else:
            self.timeouts[timeoutName] = time.time() + timeout
            return True

    def b_setKartActive(self, kartActive):
        self.setKartActive(kartActive)
        self.d_setKartActive(kartActive)

    def d_setKartActive(self, kartActive):
        self.sendUpdate('setKartActive', [kartActive])

    def setKartActive(self, kartActive):
        self.kartActive = kartActive

    def getKartActive(self):
        return self.kartActive

    def requestKart(self, active):
        if self.kartActive == active or not self.hasKart():
            return

        if self.air.legitMode:
            return

        self.b_setKartActive(active)

        if self.kartActive:
            if not self.kart:
                from toontown.racing import DistributedVehicleAI
                self.kart = DistributedVehicleAI.DistributedVehicleAI(self.air, self.doId)
                self.kart.setControlled(True)
                self.kart.generateWithRequiredAndId(self.air.allocateChannel(), self.doId, 100)
                self.kart.d_setNonRace(True)
                self.kart.start()
        else:
            if self.kart:
                self.kart.requestDelete()
                self.kart = None

    def sendSetBan(self, reason='', target=None, invoker=None, minutes=0):
        invokerAvId = 0
        invokerName = ''
        if invoker:
            invokerAvId = invoker.getDoId()
            invokerName = invoker.getName()
        self.air.banManager.sendBan(accId=target.DISLid, avId=target.getDoId(), name=target.getName(),
                                    modAvId=invokerAvId, modName=invokerName, reason=reason, minutes=minutes)
        self.air.handlePlayerBanned(target.getDoId())

    def sendSetKick(self, reason='', target=None, silent=0):
        self.air.banManager.sendKick(avId=target.getDoId(), reason=reason, silent=silent)

    def d_generateRainbow(self):
        self.sendUpdateToAvatarId(self.doId, 'generateRainbow', [])

    def d_generateFanfare(self):
        self.sendUpdate('generateFanfare', [])

    def d_generateDropProp(self, propName: str):
        self.sendUpdate('generateDropProp', [propName, globalClockDelta.getRealNetworkTime()])

    def d_generateGreenEffect(self, character, toonId):
        self.sendUpdate('generateGreenEffect', [character, toonId])

    def d_generateSnapEffect(self):
        self.sendUpdate('generateSnapEffect', [])

    def d_generateOboeEffect(self):
        self.sendUpdate('generateOboeEffect', [])

    def d_generateScavengerEffect(self, amount):
        self.sendUpdate('generateScavengerEffect', [amount])

    def d_generateCage(self):
        self.sendUpdate('generateCage', [])

    def b_setLocked(self, locked, exemption=0):
        self.setLocked(locked, exemption)
        self.d_setLocked(locked, exemption)

    def d_setLocked(self, locked, exemption):
        self.sendUpdate('setLocked', [locked, exemption])

    def setLocked(self, locked, exemption=None):
        self.locked = locked
        self.exemption = exemption

        self.requestKart(False)

    def getLocked(self):
        return self.locked

    def getExemption(self):
        return self.exemption

    def b_setMuted(self, muted, minutes):
        self.setMuted(muted, minutes)
        self.d_setMuted(muted, minutes)

    def d_setMuted(self, muted, minutes):
        self.sendUpdate('setMuted', [muted, minutes])

    def setMuted(self, muted, minutes):
        sendSystemMessage = 0
        if hasattr(self, 'muted'):
            sendSystemMessage = 1

        self.muted = muted
        self.mutedMinutes = minutes
        taskName = self.uniqueName('muted-expires')
        taskMgr.remove(taskName)
        self.mutedTask = None

        # If we are muted and have 0 minutes, it means we are permanently muted
        if muted and minutes > 0:
            self.mutedTask = taskMgr.doMethodLater(minutes * 60, self.sendSetUnmute, taskName, extraArgs=[self])

        if sendSystemMessage:
            self.sendMutedSystemMessage(muted, minutes)

    def sendMutedSystemMessage(self, muted, minutes):
        if muted:
            if minutes:
                if minutes == 1:
                    message = TTLocalizer.MutedTimedSingular % minutes
                else:
                    message = TTLocalizer.MutedTimedPlural % minutes
            else:
                message = TTLocalizer.MutedTrue
        else:
            message = TTLocalizer.MutedFalse

        self.d_setSystemMessage(0, message)

    def getMuted(self):
        return (self.muted, self.mutedMinutes)

    def sendSetMute(self, reason='', target=None, invoker=None, minutes=0):
        invokerAvId = 0
        invokerName = ''
        if invoker:
            invokerAvId = invoker.getDoId()
            invokerName = invoker.getName()
        self.air.banManager.sendMute(accId=target.DISLid, avId=target.getDoId(), name=target.getName(),
                                    modAvId=invokerAvId, modName=invokerName, reason=reason, minutes=minutes)
        self.b_setMuted(1, minutes)

    def sendSetUnmute(self, target):
        self.air.banManager.sendUnmute(accId=target.DISLid)
        self.b_setMuted(0, 0)

    def findClosestSuitDoor(self, lenient=False):
        zoneId = self.zoneId
        streetId = ZoneUtil.getBranchZone(zoneId)
        sp = self.air.suitPlanners[streetId]
        if not sp:
            return None
        bm = sp.buildingMgr
        if not bm:
            return None
        if lenient:
            zones = range(zoneId - 50, zoneId + 51)
        else:
            zones = range(zoneId - 1, zoneId + 3)
        for zone in zones:
            for i in bm.getSuitBlocks():
                building = bm.getBuilding(i)
                extZoneId, intZoneId = building.getExteriorAndInteriorZoneId()
                if not isZoneProtected(intZoneId):
                    if hasattr(building, 'elevator'):
                        if building.elevator.zoneId == zone:
                            return building

        return None

    def doBuildingFree(self, lenient=False):
        streetId = ZoneUtil.getBranchZone(self.zoneId)
        if streetId not in self.air.suitPlanners:
            self.notify.warning('Street %d is not known.' % streetId)
            return ['badlocation', 0]
        building = self.findClosestSuitDoor(lenient)
        if building is None:
            return ['badlocation', 0]
        if hasattr(building, 'elevator'):
            if building.elevator.getState() == "waitEmpty" and building.getState() != "becomingToon":
                building.buildingDefeated = 1
                building.toonTakeOver()
                return ['success', 0]
            else:
                return ['busy', 0]
        return ['fail', 0]

    def d_setLoop(self, anim, start, end, part):
        self.sendUpdate('setLoop', [anim, start, end, part])

    def d_setPingPong(self, anim, start, end, part):
        self.sendUpdate('setPingPong', [anim, start, end, part])

    def d_setPose(self, anim, frame, part):
        self.sendUpdate('setPose', [anim, frame, part])

    def setAccessLevel(self, access):
        DistributedPlayerAI.DistributedPlayerAI.setAccessLevel(self, access)

        if access >= OTPGlobals.AccessLevelName2Int['MODERATOR']:
            self.toonDownDamage = True

    def b_setAccessLevel(self, access):
        self.air.dbInterface.updateObject(self.air.dbId, self.DISLid, self.air.dclassesByName['AccountAI'],
                                          {'ACCESS_LEVEL': access})
        self.d_setSystemMessage(0, 'Your Access Level has been changed. Please restart your game.')

    def execChatUse(self):
        self.notify.info('execChatUse: Executive chat has been used.')

    def b_setScavengerProgress(self, holidayId, year, visitedZones=[]):
        if not isinstance(visitedZones, (list, tuple)):
            self.notify.error('b_setScavengerProgress(): visitedZones must be of type list/tuple!')
        self.scavengerProgress[holidayId] = [year, visitedZones]
        self.d_setScavengerProgress(self.getScavengerProgress())

    def d_setScavengerProgress(self, progressString):
        if not isinstance(progressString, (type(b''), type(''))):
            self.notify.error('d_setScavengerProgress(): progressString must be of type bytes/unicode!')
        self.sendUpdate('setScavengerProgress', [progressString])

    def setScavengerProgress(self, progressString):
        if not isinstance(progressString, (type(b''), type(''))):
            self.notify.error('setScavengerProgress(): progressString must be of type bytes/unicode!')
        if progressString.strip() != b'':
            self.scavengerProgress = pickle.loads(progressString)

    def getScavengerProgress(self, pickled=True):
        if pickled:
            return pickle.dumps(self.scavengerProgress)
        else:
            return self.scavengerProgress

    def d_systemWarning(self, message):
        self.sendUpdate('systemWarning', [message])

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
        # now send the same data our client
        self.sendUpdate('setEpisodeStatuses', [episodeStatuses])

    def isEpisodeComplete(self, episodeName):
        return self.__episodeStatuses.get(episodeName, False)

    def hitToon(self, toonId):
        avId = self.air.getAvatarIdFromSender()
        if avId == toonId:
            return

        toon = self.air.doId2do.get(toonId)
        if toon:
            microGameMgr = self.air.microGameMgr
            if microGameMgr:
                microGame, active = microGameMgr.getActiveMicroGame(toon.zoneId)
                if active and microGame.getName() == 'Pie Blitz':
                    if ZoneUtil.isDynamicZone(self.zoneId) or self.getImmortalMode():
                        return

                    toon.takeDamage(microGame.getDamage())
                else:
                    toon.toonUp(1)
            else:
                toonupValue = 1
                boss = self.findBoss('l')
                if boss:
                    toonupValue = boss.toonupValue
                toon.toonUp(toonupValue)

    def getNearbyPlayers(self, radius, includeSelf=True):
        nearbyToons = []
        toonIds = []
        for doId, do in list(self.air.doId2do.items()):
            if isinstance(do, DistributedToonAI):
                if str(doId)[0] != str(self.air.districtId)[0]:
                    if do.zoneId == self.zoneId:
                        toonIds.append((doId, do))
        for toonPair in toonIds:
            toonId = toonPair[0]
            toon = toonPair[1]
            if toon is not self:
                dist = toon.getDistance(self)
                if dist < radius:
                    nearbyToons.append(toonId)

        if includeSelf:
            nearbyToons.append(self.doId)
        return nearbyToons

    def correctLaff(self):
        # This is used to correct a Toon's laff points, for situations like toggling nerfs mode
        # Get the amount of golfing laff a Toon should have based on their trophy count
        golfingTrophies = 0
        for trophy in GolfGlobals.calcTrophyListFromHistory(self.golfHistory):
            if trophy:
                golfingTrophies += 1
        golfingLaff = int(golfingTrophies / 10)

        # Get the amount of racing laff a Toon should have based on their trophy count
        racingLaff = int(len(self.getKartingTrophies()) / 10)

        # Get the amount of fishing laff a Toon should have based on their trophy count
        fishingLaff = len(self.getFishingTrophies())

        # Get the amount of gardening laff a Toon should have based on their trophy count
        gardeningLaff = int(len(self.getGardenTrophies()))

        # Fix a Toon's quest history before we use it to determine laff points
        rewardIds = self.getRewardHistory()[1]

        for tierNum in range(self.rewardTier):
            for rewardId in Quests.getRewardsInTier(tierNum):
                rewardIds.append(rewardId)

        # Iterate over all the toontasks in our quest history and grant laff rewards
        questLaff = 0
        for rewardId in rewardIds:
            if rewardId in range(100, 104):
                rewardedLaff = rewardId - 100 + 1
                questLaff += rewardedLaff

        # Iterate over all their cog disguises and grant laff rewards
        HQdepts = (ToontownGlobals.cogHQZoneId2deptIndex(ToontownGlobals.SellbotHQ), ToontownGlobals.cogHQZoneId2deptIndex(ToontownGlobals.LawbotHQ),
                   ToontownGlobals.cogHQZoneId2deptIndex(ToontownGlobals.CashbotHQ), ToontownGlobals.cogHQZoneId2deptIndex(ToontownGlobals.BossbotHQ))
        levels = self.getCogLevels()
        cogTypes = self.getCogTypes()
        suitLaff = 0
        for dept in HQdepts:
            level = levels[dept]
            cogType = cogTypes[dept]
            if cogType >= SuitDNA.suitsPerDept - 1:
                for milestoneLevel in ToontownGlobals.CogSuitHPLevels:
                    if level >= milestoneLevel:
                        suitLaff += 1
                    else:
                        break

        # Correct the Toon's laff
        newHp = 15 + golfingLaff + racingLaff + fishingLaff + gardeningLaff + questLaff + suitLaff
        oldHp = self.getMaxHp()
        if newHp != oldHp:
            self.b_setMaxHp(newHp)
            self.b_setHp(newHp)

    def findBoss(self, dept=None):
        from toontown.suit.DistributedSellbotBossAI import DistributedSellbotBossAI
        from toontown.suit.DistributedSellbotArenaAI import DistributedSellbotArenaAI
        from toontown.suit.DistributedCashbotBossAI import DistributedCashbotBossAI
        from toontown.suit.DistributedLawbotBossAI import DistributedLawbotBossAI
        from toontown.suit.DistributedBossbotBossAI import DistributedBossbotBossAI
        from toontown.suit.DistributedLawbotArenaAI import DistributedLawbotArenaAI
        dept2Boss = {'s': DistributedSellbotBossAI,
                     'ss': DistributedSellbotArenaAI,
                     'm': DistributedCashbotBossAI,
                     'l': DistributedLawbotBossAI,
                     'c': DistributedBossbotBossAI,
                     'cc': DistributedLawbotArenaAI}

        bossObj = None
        if dept:
            bossClass = dept2Boss.get(dept)
            for do in list(self.air.doId2do.values()):
                if isinstance(do, bossClass):
                    if self.doId in do.involvedToons:
                        bossObj = do
                        break
        else:
            bossClasses = list(dept2Boss.values())
            for do in list(self.air.doId2do.values()):
                for bossClass in bossClasses:
                    if isinstance(do, bossClass):
                        if self.doId in do.involvedToons:
                            bossObj = do
                            break
                else:
                    continue
                break

        return bossObj

    def d_removeNotificationsMatching(self, idStr):
        self.sendUpdate('removeNotificationsMatching', [idStr])

    def setProfilePose(self, profilePose: int):
        self.profilePose = profilePose

    def d_setProfilePose(self, profilePose: int):
        self.sendUpdate('setProfilePose', [profilePose])

    def b_setProfilePose(self, profilePose: int):
        self.setProfilePose(profilePose)
        self.d_setProfilePose(profilePose)
        self.air.updateOnlineAvatar(self)

    def getProfilePose(self) -> int:
        return self.profilePose

    def setProfilePoses(self, profilePoses: List[int]):
        self.profilePoses = profilePoses

    def d_setProfilePoses(self, profilePoses: List[int]):
        self.sendUpdate('setProfilePoses', [profilePoses])

    def b_setProfilePoses(self, profilePoses: List[int]):
        self.setProfilePoses(profilePoses)
        self.d_setProfilePoses(profilePoses)

    def getProfilePoses(self) -> List[int]:
        return self.profilePoses

    def setProfileBackground(self, profileBackground: int):
        self.profileBackground = profileBackground

    def d_setProfileBackground(self, profileBackground: int):
        self.sendUpdate('setProfileBackground', [profileBackground])

    def b_setProfileBackground(self, profileBackground: int):
        self.setProfileBackground(profileBackground)
        self.d_setProfileBackground(profileBackground)
        self.air.updateOnlineAvatar(self)

    def getProfileBackground(self) -> int:
        return self.profileBackground

    def setProfileBackgrounds(self, profileBackgrounds: List[int]):
        self.profileBackgrounds = profileBackgrounds

    def d_setProfileBackgrounds(self, profileBackgrounds: List[int]):
        self.sendUpdate('setProfileBackgrounds', [profileBackgrounds])

    def b_setProfileBackgrounds(self, profileBackgrounds: List[int]):
        self.setProfileBackgrounds(profileBackgrounds)
        self.d_setProfileBackgrounds(profileBackgrounds)

    def getProfileBackgrounds(self) -> List[int]:
        return self.profileBackgrounds

    def setNextKnockKnockHeal(self, nextKnockKnockHeal) -> int:
        self.nextKnockKnockHeal = nextKnockKnockHeal

    def d_setNextKnockKnockHeal(self, nextKnockKnockHeal) -> int:
        self.sendUpdate('setNextKnockKnockHeal', [nextKnockKnockHeal])

    def b_setNextKnockKnockHeal(self, nextKnockKnockHeal) -> int:
        self.setNextKnockKnockHeal(nextKnockKnockHeal)
        self.d_setNextKnockKnockHeal(nextKnockKnockHeal)

    def getNextKnockKnockHeal(self) -> int:
        return self.nextKnockKnockHeal

    def setNumRequestedBldgCogs(self, numRequestedBldgCogs):
        self.numRequestedBldgCogs = numRequestedBldgCogs

    def getNumRequestedBldgCogs(self) -> int:
        return self.numRequestedBldgCogs

    def isTemporaryToon(self):
        return False