from direct.stdpy import file
from typing import Dict, List, Tuple

from otp.otpbase.PythonUtil import validateAll
from otp.uberdog.GameServicesManagerUD import *
from toontown.makeatoon.NameGenerator import NameGenerator
from toontown.toon.ToonDNA import ToonDNA
from toontown.toonbase import TTLocalizer
from toontown.toonbase.ToontownGlobals import ToonNameRegex, MaxCarryLimit, DefaultMaxBankMoney, MaxHpLimit, Hoods,\
    HoodsForTeleportAll, MaxCogSuitLevel, MaxQuestCarryLimit
from toontown.chat.ResistanceChat import resistanceMenu, getItems, encodeId
from toontown.coghq.CogDisguiseGlobals import PartsPerSuitBitmasks
from toontown.episodes.EpisodeConfig import DefaultEpisodeStatuses, EpisodeName2Id
from toontown.estate import GardenGlobals
from toontown.fishing.FishGlobals import getRandomWeight, MaxRodId, TrophyDict
from toontown.golf.GolfGlobals import MaxHistoryIndex
from toontown.quest.Quests import RewardDict, COG_NATION_TIER
from toontown.racing.KartDNA import KartDict
from toontown.racing.RaceGlobals import MaxTickets, NumTrophies, NumCups
from toontown.shtiker.CogPageGlobals import COG_QUOTAS, COG_COMPLETE2
from toontown.suit.SuitDNA import suitHeadTypes
from toontown.toon import Experience

import re
from copy import deepcopy
import os

from toontown.toonbase.ToontownTypes import TPickAToonProp, TPosHpr, TVec3, TColor, TSDRColor, TTypedKeyValuePair


def judgeName(name):
    # don't think the name len will ever be longer than 64 char from MAT anyways
    if len(name) == 0 or len(name) > 64:
        return False
    if not re.match(ToonNameRegex, name):
        return False
    # everything should be good here now
    return True


class AvatarOperation(GameOperation):
    notify = DirectNotifyGlobal.directNotify.newCategory('AvatarOperation')
    postAccountState = 'Off'  # Must be overridden by subclass.

    def enterRetrieveAccount(self):
        # Query the account. self.__handleRetrieve is the callback
        # which will be called after queryObject has completed.
        self.gameServicesManager.air.dbInterface.queryObject(self.gameServicesManager.air.dbId, self.target,
                                                             self.__handleRetrieve)

    def __handleRetrieve(self, dclass, fields):
        if dclass != self.gameServicesManager.air.dclassesByName['AccountUD']:
            # This is not an account object! Kill the connection.
            self.demand('Kill', 'Your account object (%s) was not found in the database!' % dclass)
            return

        # Set the account & avList.
        self.account = fields
        self.avList = self.account['ACCOUNT_AV_SET']

        # Sanitize the avList, just in case it is too long/short.
        self.avList = self.avList[:7]
        self.avList += [0] * (7 - len(self.avList))

        # We're done; enter the postAccountState.
        self.demand(self.postAccountState)


class SetNamePatternOperation(AvatarOperation):
    notify = DirectNotifyGlobal.directNotify.newCategory('SetNamePatternOperation')
    postAccountState = 'RetrieveAvatar'

    def __init__(self, gameServicesManager, target):
        AvatarOperation.__init__(self, gameServicesManager, target)
        self.avId = None
        self.pattern = None

    def enterStart(self, avId, pattern):
        # Store these values.
        self.avId = avId
        self.pattern = pattern

        # Retrieve the account.
        self.demand('RetrieveAccount')

    def enterRetrieveAvatar(self):
        # Retrieves the avatar from the database.
        if self.avId and self.avId not in self.avList:
            # The avatar exists, but it's not an avatar that is
            # associated with this account. Kill the connection.
            self.demand('Kill', 'Tried to name an avatar not in the account!')
            return

        # Query the database for the avatar. self.__handleAvatar is
        # our callback which will be called upon queryObject's completion.
        self.gameServicesManager.air.dbInterface.queryObject(self.gameServicesManager.air.dbId, self.avId,
                                                             self.__handleAvatar)

    def __handleAvatar(self, dclass, fields):
        if dclass != self.gameServicesManager.air.dclassesByName['DistributedToonUD']:
            # This dclass is not a valid avatar! Kill the connection.
            self.demand('Kill', 'One of the account\'s avatars is invalid!')
            return

        if fields['WishNameState'][0] != 'OPEN':
            # This avatar's wish name state is not set
            # to a nameable state. Kill the connection.
            self.demand('Kill', 'Avatar is not in a nameable state!')

        # Otherwise, we can set the name, so let's enter the SetName state.
        self.demand('SetName')

    def enterSetName(self):
        # Stringify this pattern.
        parts = []
        for p, f in self.pattern:
            part = self.gameServicesManager.nameGenerator.nameDictionary.get(p, ('', ''))[1]
            if f:
                part = part[:1].upper() + part[1:]
            else:
                part = part.lower()

            parts.append(part)

        # This will merge 2 & 3 (the last name), as there should be no space.
        parts[2] += parts.pop(3)
        while '' in parts:
            parts.remove('')

        # Construct the final name string.
        name = ' '.join(parts)

        # We can now update the avatar object with the name.
        self.gameServicesManager.air.dbInterface.updateObject(self.gameServicesManager.air.dbId, self.avId,
                                                              self.gameServicesManager.air.dclassesByName[
                                                                  'DistributedToonUD'], {'WishNameState': ('LOCKED',),
                                                                                         'WishName': ('',),
                                                                                         'setName': (name,)})

        # We're done. We can now send off the namePatternResponse update through
        # the GameServicesManager, and set this operation's state to Off.
        self.gameServicesManager.air.writeServerEvent('avatar-named', self.avId, name)
        self.gameServicesManager.sendUpdateToAccountId(self.target, 'namePatternResponse', [self.avId, 1])
        self.demand('Off')


class SetNameTypedOperation(AvatarOperation):
    notify = DirectNotifyGlobal.directNotify.newCategory('SetNameTypedOperation')
    postAccountState = 'RetrieveAvatar'

    def __init__(self, gameServicesManager, target):
        AvatarOperation.__init__(self, gameServicesManager, target)
        self.avId = None
        self.name = None

    def enterStart(self, avId, name):
        # SetNameTypedOperation judges the submitted name
        # & then sets the avatars wish name state accordingly.
        self.avId = avId
        self.name = name

        if self.avId:
            # If avId is not 0, the user is submitting this name,
            # so we need to retrieve the account.
            self.demand('RetrieveAccount')
            return

        # Otherwise, avId is 0, meaning that a check request was sent.
        self.demand('JudgeName')

    def enterRetrieveAvatar(self):
        # Retrieves the avatar from the database.
        if self.avId and self.avId not in self.avList:
            # The avatar exists, but it's not an avatar that is
            # associated with this account. Kill the connection.
            self.demand('Kill', 'Tried to name an avatar not in the account!')
            return

        # Query the database for the avatar. self.__handleAvatar is
        # our callback which will be called upon queryObject's completion.
        self.gameServicesManager.air.dbInterface.queryObject(self.gameServicesManager.air.dbId, self.avId,
                                                             self.__handleAvatar)

    def __handleAvatar(self, dclass, fields):
        if dclass != self.gameServicesManager.air.dclassesByName['DistributedToonUD']:
            # This dclass is not a valid avatar! Kill the connection.
            self.demand('Kill', 'One of the account\'s avatars is invalid!')
            return

        if fields['WishNameState'][0] != 'OPEN':
            # This avatar's wish name state is not set
            # to a nameable state. Kill the connection.
            self.demand('Kill', 'Avatar is not in a nameable state!')

        # Now we can move on to the judging!
        self.demand('JudgeName')

    def enterJudgeName(self):
        # Let's see if the name is valid.
        status = judgeName(self.name)

        # TODO: accept/reject server hoster option boolean.
        tempAutoAcceptBool = True

        if self.avId and status:
            # Cool, this is a valid name, and we have an avId.
            # Let's update their avatar with the new wish name & status.
            if tempAutoAcceptBool:
                self.gameServicesManager.air.dbInterface.updateObject(self.gameServicesManager.air.dbId, self.avId,
                                                                      self.gameServicesManager.air.dclassesByName[
                                                                          'DistributedToonUD'],
                                                                      {'WishNameState': ('LOCKED',),
                                                                       'WishName': ('',),
                                                                       'setName': (self.name,)})
            else:
                self.gameServicesManager.air.dbInterface.updateObject(self.gameServicesManager.air.dbId, self.avId,
                                                                      self.gameServicesManager.air.dclassesByName[
                                                                          'DistributedToonUD'],
                                                                      {'WishNameState': ('PENDING',),
                                                                       'WishName': (self.name,)})

        if self.avId:
            # If the avId is not 0, log this server event, as the avatar's
            # wish name & state have been modified.
            if tempAutoAcceptBool:
                if status:
                    self.gameServicesManager.air.writeServerEvent('avatar-name-accepted', self.avId, self.name)
                else:
                    self.gameServicesManager.air.writeServerEvent('avatar-name-rejected', self.avId, self.name)
            else:
                self.gameServicesManager.air.writeServerEvent('avatar-wish-name', self.avId, self.name)

        if status and tempAutoAcceptBool:
            status = 2
        elif not status and tempAutoAcceptBool:
            status = 0

        # Otherwise, we're done! We can now send the response update
        # through the GameServicesManager & set our state to Off.
        self.gameServicesManager.sendUpdateToAccountId(self.target, 'nameTypedResponse', [self.avId, status])
        self.demand('Off')


class CreateAvatarOperation(GameOperation):
    notify = DirectNotifyGlobal.directNotify.newCategory('CreateAvatarOperation')

    def __init__(self, gameServicesManager, target):
        GameOperation.__init__(self, gameServicesManager, target)
        self.index = None
        self.dna = None
        self.name = None
        self.account = None
        self.accountId = None

    def enterStart(self, dna, name, index, account = None, accountId = 0):
        # First, perform some basic sanity checking.
        if index >= 7:
            # This index is invalid! Kill the connection.
            self.demand('Kill', 'Invalid index specified!')
            return

        if not ToonDNA().isValidNetString(dna):
            # This DNA string is invalid! Kill the connection.
            self.demand('Kill', 'Invalid DNA specified!')
            return

        # Store these values.
        self.index = index
        self.dna = dna
        self.name = name
        self.account = account
        self.accountId = accountId

        # Now we can query their account.
        self.demand('RetrieveAccount')

    def enterRetrieveAccount(self):
        # Query the sender's account. self.__handleRetrieve is the
        # callback that will be called upon queryObject's competion.
        self.gameServicesManager.air.dbInterface.queryObject(self.gameServicesManager.air.dbId, self.target,
                                                             self.__handleRetrieve)

    def __handleRetrieve(self, dclass, fields):
        if not self.account:
            if dclass != self.gameServicesManager.air.dclassesByName['AccountUD']:
                # This is not an account object! Kill the connection.
                self.demand('Kill', 'Your account object (%s) was not found in the database!' % dclass)
                return

        # Now we will get our avList.
        if not self.account:
            self.account = fields
        self.avList = self.account['ACCOUNT_AV_SET']

        # We will now sanitize the avList.
        self.avList = self.avList[:7]
        self.avList += [0] * (7 - len(self.avList))

        # Check if the index is open:
        if self.avList[self.index]:
            # This index is not open! Kill the connection.
            self.demand('Kill', 'This avatar slot is already taken by another avatar!')
            return

        # All set, now let's create the avatar!
        self.demand('CreateAvatar')

    def enterCreateAvatar(self):
        # We will now construct a new Toon with the given values.
        dna = ToonDNA()
        dna.makeFromNetString(self.dna)
        try:
            colorString = TTLocalizer.NumToColor[dna.headColor]
        except:
            colorString = TTLocalizer.CustomColor
        animalType = TTLocalizer.AnimalToSpecies[dna.getAnimal()]
        name = ' '.join((colorString, animalType))
        accountId = self.target
        if not accountId and self.accountId:
            accountId = int(self.accountId)
        if self.name != '':
            toonFields = {'setName': (self.name,),
                          'WishNameState': ('LOCKED',),
                          'WishName': ('',),
                          'setDNAString': (self.dna,),
                          'setDISLid': (accountId,),
                          'setNametagStyle': (100,)}
        else:
            toonFields = {'setName': (name,),
                          'WishNameState': ('OPEN',),
                          'WishName': ('',),
                          'setDNAString': (self.dna,),
                          'setDISLid': (accountId,),
                          'setNametagStyle': (100,)}

        # Max the newly created toon if the server is maxing new toons by default
        if self.gameServicesManager.air.moddingManager.getDefaultMaxToon():
            gagTracks = [1, 1, 1, 1, 1, 1, 1]
            # There's no real way for the player to pick which track they
            # want to leave out here so we'll have to pick a random one
            # fortunately they can just use magic words if they want to
            # pick one after spawning into the game
            missingTrack = random.randint(0, len(gagTracks) - 1)
            gagTracks[missingTrack] = 0
            toonFields['setTrackAccess'] = (gagTracks,)
            toonFields['setMaxCarry'] = (MaxCarryLimit,)
            experience = Experience.Experience()
            for i, track in enumerate(gagTracks):
                if track:
                    experience.experience[i] = (Experience.MaxSkill - Experience.UberSkill)
            toonFields['setExperience'] = (experience.makeNetString(),)

            # We're gonna fill up the toon's inventory in the TutorialManager instead of doing it here

            maxMoney = (RewardDict[707][1],)
            toonFields['setMaxMoney'] = maxMoney
            toonFields['setMoney'] = maxMoney
            toonFields['setBankMoney'] = (DefaultMaxBankMoney,)

            newHp = (MaxHpLimit,)
            toonFields['setMaxHp'] = newHp
            toonFields['setHp'] = newHp

            toonFields['setHoodsVisited'] = (Hoods,)
            toonFields['setTeleportAccess'] = (HoodsForTeleportAll,)

            toonFields['setCogParts'] = ([PartsPerSuitBitmasks[0],
                                         PartsPerSuitBitmasks[1],
                                         PartsPerSuitBitmasks[2],
                                         PartsPerSuitBitmasks[3]],)
            toonFields['setCogLevels'] = ([MaxCogSuitLevel] * 4,)
            toonFields['setCogTypes'] = ([7] * 4,)

            toonFields['setCogRadar'] = ([1] * 4,)
            toonFields['setBuildingRadar'] = ([1] * 4,)
            cogCount = []
            for deptIndex in range(4):
                for cogIndex in range(8):
                    cogCount.append(COG_QUOTAS[1][cogIndex])
            toonFields['setCogCount'] = (cogCount,)
            toonFields['setCogStatus'] = (([COG_COMPLETE2] * 8) * 4,)

            toonFields['setQuests'] = ([],)
            toonFields['setQuestCarryLimit'] = (MaxQuestCarryLimit,)
            toonFields['setRewardHistory'] = (COG_NATION_TIER, [100])

            allFish = TTLocalizer.FishSpeciesNames
            fishLists = ([], [], [])
            for genus in list(allFish.keys()):
                for species in range(len(allFish[genus])):
                    fishLists[0].append(genus)
                    fishLists[1].append(species)
                    fishLists[2].append(getRandomWeight(genus, species))
            toonFields['setFishCollection'] = fishLists
            toonFields['setFishingRod'] = (MaxRodId,)
            toonFields['setFishingTrophies'] = (list(TrophyDict.keys()),)

            if simbase.wantKarts:
                toonFields['setKartBodyType'] = (list(KartDict.keys())[1],)
            toonFields['setTickets'] = (MaxTickets,)
            maxTrophies = NumTrophies + NumCups
            toonFields['setKartingTrophies'] = (list(range(1, maxTrophies + 1)),)
            toonFields['setTickets'] = (99999,)

            toonFields['setGolfHistory'] = ([600] * (MaxHistoryIndex * 2 + 2),)

            toonFields['setShovel'] = (3,)
            toonFields['setWateringCan'] = (3,)
            toonFields['setShovelSkill'] = (639,)
            toonFields['setWateringCanSkill'] = (999,)
            toonFields['setGardenTrophies'] = (list(GardenGlobals.TrophyDict.keys()),)

            sosIds = (4125, 2003, 1116, 2311, 4119, 4219, 4115, 3112, 1323, 2308, 2011, 2001, 2132, 2121, 5124, 4230)
            npcFriendsDict = []
            for sosId in sosIds:
                npcFriendsDict.append((sosId, 100))
            toonFields['setNPCFriendsDict'] = (npcFriendsDict,)

            msgs = []
            for menuIndex in resistanceMenu:
                for itemIndex in getItems(menuIndex):
                    textId = encodeId(menuIndex, itemIndex)
                    msgs.append([textId, 999])
            toonFields['setResistanceMessages'] = (msgs,)

            numSuits = len(suitHeadTypes)
            fullSetForSuit = 1 | 2 | 4
            allSummons = numSuits * [fullSetForSuit]
            toonFields['setCogSummonsEarned'] = (allSummons,)

            toonFields['setPinkSlips'] = (255,)

        # Create this new Toon object in the database. self.__handleCreate is the
        # callback that will be called upon the completion of createObject.
        self.gameServicesManager.air.dbInterface.createObject(self.gameServicesManager.air.dbId,
                                                              self.gameServicesManager.air.dclassesByName[
                                                                  'DistributedToonUD'], toonFields, self.__handleCreate)

    def __handleCreate(self, avId):
        if not avId:
            # The database was unable to create a new avatar object! Kill the connection.
            self.demand('Kill', 'Database failed to create the new avatar object!')
            return

        # We can now store the avatar.
        self.avId = avId
        self.demand('StoreAvatar')

    def enterStoreAvatar(self):
        # We will now associate the avatar with the account. self.__handleStoreAvatar is the
        # callback which will be called upon the completion of updateObject.
        self.avList[self.index] = self.avId
        accountId = self.target
        if self.accountId:
            accountId = self.accountId
        self.gameServicesManager.air.dbInterface.updateObject(self.gameServicesManager.air.dbId, accountId,
                                                              self.gameServicesManager.air.dclassesByName['AccountUD'],
                                                              {'ACCOUNT_AV_SET': self.avList},
                                                              {'ACCOUNT_AV_SET': self.account['ACCOUNT_AV_SET']},
                                                              self.__handleStoreAvatar)

    def __handleStoreAvatar(self, fields):
        if fields:
            # The new avatar was not associated with the account! Kill the connection.
            self.demand('Kill', 'Database failed to associate the new avatar to your account!')
            return

        # Otherwise, we're done! We can now send the createAvatarResponse update
        # through the GameServicesManager & set this operation's state to Off.
        self.gameServicesManager.air.writeServerEvent('avatar-created', self.avId, self.target, self.dna.hex(),
                                                      self.index)
        self.gameServicesManager.sendUpdateToAccountId(self.target, 'createAvatarResponse', [self.avId])
        self.demand('Off')


class AcknowledgeNameOperation(AvatarOperation):
    notify = DirectNotifyGlobal.directNotify.newCategory('AcknowledgeNameFSM')
    postAccountState = 'GetTargetAvatar'

    def __init__(self, gameServicesManager, target):
        AvatarOperation.__init__(self, gameServicesManager, target)
        self.avId = None

    def enterStart(self, avId):
        # Store this value & move on to RetrieveAccount.
        self.avId = avId
        self.demand('RetrieveAccount')

    def enterGetTargetAvatar(self):
        # Make sure that the target avatar is part of the account:
        if self.avId not in self.avList:
            # The sender tried to acknowledge name on an avatar not on the account!
            # Kill the connection.
            self.demand('Kill', 'Tried to acknowledge name on an avatar not in the account!')
            return

        # We can now query the database for the avatar. self.__handleAvatar is the
        # callback which will be called upon the completion of queryObject.
        self.gameServicesManager.air.dbInterface.queryObject(self.gameServicesManager.air.dbId, self.avId,
                                                             self.__handleAvatar)

    def __handleAvatar(self, dclass, fields):
        if dclass != self.gameServicesManager.air.dclassesByName['DistributedToonUD']:
            # This dclass is not a valid avatar! Kill the connection.
            self.demand('Kill', 'One of the account\'s avatars is invalid!')
            return

        # Process the WishNameState change.
        wishNameState = fields['WishNameState'][0]
        wishName = fields['WishName'][0]
        name = fields['setName'][0]

        if wishNameState == 'APPROVED':
            wishNameState = 'LOCKED'
            name = wishName
            wishName = ''
        elif wishNameState == 'REJECTED':
            wishNameState = 'OPEN'
            wishName = ''
        else:
            # The sender is trying to acknowledge name on avatar in invalid state! Kill the connection.
            self.demand('Kill', 'Tried to acknowledge name on an avatar in invalid state (%s) !' % wishNameState)
            return

        # We can now update the avatar object in the database with the changes!
        self.gameServicesManager.air.dbInterface.updateObject(self.gameServicesManager.air.dbId, self.avId,
                                                              self.gameServicesManager.air.dclassesByName[
                                                                  'DistributedToonUD'],
                                                              {'WishNameState': (wishNameState,),
                                                               'WishName': (wishName,),
                                                               'setName': (name,)},
                                                              {'WishNameState': fields['WishNameState'],
                                                               'WishName': fields['WishName'],
                                                               'setName': fields['setName']})

        # We're done. We can now send off the acknowledgeAvatarNameResponse update
        # through the GameServicesManager, and set this operation's state to Off.
        self.gameServicesManager.sendUpdateToAccountId(self.target, 'acknowledgeAvatarNameResponse', [])
        self.demand('Off')


class TTGameServicesManagerUD(GameServicesManagerUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('TTGameServicesManagerUD')
    notify.setDebug(True)
    avatarDclass = 'DistributedToonUD'

    def __init__(self, air):
        GameServicesManagerUD.__init__(self, air)
        self.nameGenerator = None

    def announceGenerate(self):
        GameServicesManagerUD.announceGenerate(self)

        # This is for processing name patterns.
        self.nameGenerator = NameGenerator()
        self.air.netMessenger.accept('SetEpisodeCompleted', self, self.__setEpisodeCompleted)

    def setNamePattern(self, avId, p1, f1, p2, f2, p3, f3, p4, f4):
        # Someone has used a pattern name; run a SetNamePatternOperation.
        self.runOperation(SetNamePatternOperation, avId, [(p1, f1), (p2, f2),
                                                          (p3, f3), (p4, f4)])

    def setNameTyped(self, avId, name):
        # Someone has typed a name; run a SetNameTypedOperation.
        self.runOperation(SetNameTypedOperation, avId, name)

    def createAvatar(self, dna, name, index, account=None, accountId=0):
        # Someone wants to create a new avatar;
        # run a CreateAvatarOperation.
        self.runOperation(CreateAvatarOperation, dna, name, index, account, accountId)

    def acknowledgeAvatarName(self, avId):
        # Someone has acknowledged their name; run an AcknowledgeNameOperation.
        self.runOperation(AcknowledgeNameOperation, avId)

    def requestAvatarList(self):
        GameServicesManagerUD.requestAvatarList(self)

        # TODO: We should only be loading this stuff on startup, then saving it in memory. no need to keep reading it everytime someone connects.
        sender = self.air.getAccountIdFromSender()
        if os.path.exists('config/motd.json'):
            if os.stat('config/motd.json').st_size > 5_000:
                raise Exception('MOTD File is over 5 KB.')
            with open('config/motd.json') as motd:
                text = motd.read()
                self.sendUpdateToAccountId(sender, 'setMotd', [text])

        # pick-a-toon background validation.
        # warning: lots and lots of validation since we dont want clients to crash, but we want server owners to know if theyve fucked up
        if os.path.exists('config/pickatoon.json'):
            with open('config/pickatoon.json') as patbg:
                bgInfo: Dict = json.loads(patbg.read())
                self.notify.debug(bgInfo)

                dnaStorages: List[str] = bgInfo.get('dna_storages', [])
                dnaFile: str = bgInfo.get('dna_file', '')
                sky: int = bgInfo.get('sky', -1)
                rawProps: List[Dict] = bgInfo.get('props', [])
                toonPositions: List[TPosHpr] = bgInfo.get('toon_positions', [])
                cameraPos: TPosHpr = bgInfo.get('camera_pos', (0, 0, 0))

                # validate!! horray!!
                errorPrefix = "Error loading Pick-A-Toon Background:\n\t"  # todo: just make a new exception type

                if len(dnaStorages) > 4:
                    raise Exception(f'{errorPrefix}You cannot load more than 4 DNA Storages. (You specified {len(dnaStorages)} storages)')
                for storage in dnaStorages:
                    _path = f'resources/{storage}' if __debug__ else storage
                    if not file.exists(_path):
                        raise Exception(f'{errorPrefix}DNA Storage "{storage}" does not exist.')

                if dnaFile:
                    _path = f'resources/{dnaFile}' if __debug__ else dnaFile
                    if not file.exists(_path):
                        raise Exception(f'{errorPrefix}DNA File "{dnaFile}" does not exist.')

                if not isinstance(sky, int):
                    raise Exception(f'{errorPrefix}Sky must be an integer between 0 and 4, or set to -1 to disable it.')
                if -1 > sky > 4:
                    raise Exception(f'{errorPrefix}Sky must be an integer between 0 and 4, or set to -1 to disable it.')

                if len(rawProps) > 300:  # 300 might be too high, i guess we'll see when someone breaks it!
                    raise Exception(f'{errorPrefix}You cannot load more than 300 props. (You specified {len(rawProps)})')

                # we must either have all 6, or none. None will use the original 2d toon pickers.
                if len(toonPositions) != 6 and toonPositions:
                    raise Exception(f'{errorPrefix}You must specify 6 Toon positions.')
                for toonPos in toonPositions:
                    if len(toonPos) != 6 or not validateAll((float, int), *toonPos):
                        raise Exception(f'{errorPrefix}Each Toon Position must have 6 float components - [x, y, z, h, p, r].')

                if len(cameraPos) != 6 or not validateAll((float, int), *cameraPos):
                    raise Exception(f'{cameraPos}The Camera Pos must have 6 float components - [x, y, z, h, p, r].')

                props: List[TPickAToonProp] = []
                for prop in rawProps:
                    modelPath: str = prop.get('model_path', None)
                    if not modelPath:
                        raise Exception(f'{errorPrefix}Each prop must specify a model_path.')
                    if not file.exists(modelPath):
                        self.notify.warning(f'[Pick-A-Toon Background] Model file "{modelPath}" does not exist on the server so it will likely not exist on the client. '
                                            f'\n\tIf the client does not have this model in their mounted resources, they will see an error model.')

                    nodePath: str = prop.get('node_path', '')

                    hideNodes: List[str] = prop.get('hide_nodes', [])

                    pos: TVec3 = prop.get('pos', (0, 0, 0))
                    if len(pos) != 3 or not validateAll((float, int), *pos):
                        raise Exception(f'{errorPrefix}Position of {modelPath} instance must have 3 float components - [x, y, z].')

                    hpr: TVec3 = prop.get('hpr', (0, 0, 0))
                    if len(hpr) != 3 or not validateAll((float, int), *hpr):
                        raise Exception(f'{errorPrefix}HPR of {modelPath} instance must have 3 float components - [h, p, r].')
                    # noinspection PyTypeChecker
                    posHpr: TPosHpr = (*pos, *hpr)

                    scale: TVec3 = prop.get('scale', (1, 1, 1))
                    if len(scale) != 3 or not validateAll((float, int), *scale):
                        raise Exception(f'{errorPrefix}Scale of {modelPath} instance must have 3 float components - [sx, sy, sz].')

                    color: TSDRColor = prop.get('color', (255, 255, 255, 255))
                    if len(color) != 4 or not validateAll(int, *color):
                        raise Exception(f'{errorPrefix}Color of {modelPath} instance must have 4 int components - [r, g, b, a].')

                    rawTextureOverrides: Dict = prop.get('texture_overrides', {})
                    textureOverrides: List[Tuple[str, str]] = []

                    for node, texturePath in rawTextureOverrides.items():
                        if not isinstance(node, str):
                            raise Exception(f'{errorPrefix}Texture Override for {prop} has an invalid nodepath reference. ({node})')
                        if not isinstance(texturePath, str):
                            raise Exception(f'{errorPrefix}Texture Override for {prop} has an invalid texture path reference. ({node})')

                        textureOverrides.append((node, texturePath))

                    props.append((modelPath, nodePath, hideNodes, posHpr, scale, color, textureOverrides))

                self.sendUpdateToAccountId(sender, 'setPickAToonBackground',
                                           [dnaStorages, dnaFile, sky, props, toonPositions, cameraPos])

                return
        self.sendUpdateToAccountId(sender, 'setPickAToonBackground', [[], '', -1, [], [], (0, 0, 0, 0, 0, 0)])

    def __setEpisodeCompleted(self, accId, episodeName, completed=True):
        self.notify.debug("__setEpisodeCompleted(): accId={}, episode name={}, completed={}".format(
            accId,
            episodeName,
            completed
        ))
        fieldName = 'EPISODE_COMPLETIONS'

        def handleAccount(dclass, fields):
            if dclass != self.air.dclassesByName['AccountUD']:
                self.notify.warning("Cannot save episode status for account ID {}; account doesn't exist!".format(
                    accId
                ))
            else:
                episodeStatuses = list(fields.get(fieldName, deepcopy(DefaultEpisodeStatuses)))
                self.notify.debug("_setEpisodeCompleted():handleAccount({}): fields={}, episode statuses={}".format(
                    accId,
                    fields,
                    episodeStatuses
                ))
                if episodeName in EpisodeName2Id:
                    episodeId = EpisodeName2Id[episodeName]
                    self.notify.debug("_setEpisodeCompleted():handleAccount({}): episodeId={}".format(
                        accId,
                        episodeId
                    ))
                    newStatuses = []
                    for episodeData in episodeStatuses:
                        episodeData = list(episodeData)
                        if episodeData[0] == episodeId:
                            episodeData[1] = 1 if completed else 0
                            self.notify.debug(
                                "_setEpisodeCompleted():handleAccount({}): setting episode \"{}\"({}) to {}".format(
                                    accId,
                                    episodeName,
                                    episodeId,
                                    episodeData[1]
                                ))
                            newStatuses.append(tuple(episodeData))
                        else:
                            # just append to new episode status list
                            newStatuses.append(tuple(episodeData))
                    self.notify.debug("_setEpisodeCompleted():handleAccount({}): new episode statuses={}".format(
                        accId,
                        newStatuses
                    ))
                    self.air.dbInterface.updateObject(self.air.dbId, accId,
                                                      self.air.dclassesByName['AccountUD'],
                                                      {fieldName: newStatuses})
                    self.notify.debug("Attempted to set account {}'s field {} to {}".format(
                        accId,
                        fieldName,
                        newStatuses
                    ))
                else:
                    self.notify.warning(
                        "Cannot save episode status for account ID {}; episode \"{}\" doesn't exist!".format(
                            accId,
                            episodeName
                        ))

        self.air.dbInterface.queryObject(self.air.dbId, accId, handleAccount)
