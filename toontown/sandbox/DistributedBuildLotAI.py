"""
DistributedBuildLot AI Side • Created by Drew @ 12/17/2022
Authorized for use ONLY in Toontown Realms
"""
import json
import os
import time
from collections import OrderedDict
from datetime import datetime

from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from typing import List, Optional, Dict

from toontown.sandbox import PropGlobals
from toontown.sandbox.BuildLotGlobals import BuildLotThemes, PRIVACY_MODE_PUBLIC, FLPermBuild, FLPermEditPerms, FLPermClearLoad, PRIVACY_MODE_FRIENDS_ONLY, AUTOSAVE_FILENAME, MaxLotCount, LOT_LIMIT_REACHED
from toontown.sandbox.DistributedPropGeneratorAI import DistributedPropGeneratorAI
from toontown.toon.DistributedToonAI import DistributedToonAI


class DistributedBuildLotAI(DistributedObjectAI):

    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBuildLotAI')
    notify.setDebug(1)

    def __init__(self, air, ownerAvId: int, zoneId: int, theme: BuildLotThemes = BuildLotThemes.TTC,
                 privacy: int = PRIVACY_MODE_PUBLIC, name: str = 'NAMES NOT IMPL', saveToLoad: Optional[str] = None):
        """
        :param air: active Toontown AI Repository
        :param ownerAvId: Avatar ID of the owner of this lot
        :param zoneId: Allocated zone ID of this lot
        :param theme: The selected theme
        :param saveToLoad: If the user has a previously saved lot build on our server, the unique filesave will be here
                           These lot saves will be saved in backups/lots/[avid]
        """
        DistributedObjectAI.__init__(self, air)

        self.canUsersJoin: bool = True
        self.ownerAvId: int = ownerAvId
        self.zoneId: int = zoneId
        self.theme: BuildLotThemes = theme
        self.privacy: int = privacy
        self.saveToLoad: Optional[str] = saveToLoad
        self.lotName: str = name

        self.allowedBuilderAvIds: List[int] = [self.ownerAvId]

        self.avIdsInZone: List[int] = []

        # AI OBJS
        self.propGenerator: Optional[DistributedPropGeneratorAI] = None

        self.notify.debug(f'Creating Build Lot from AV {ownerAvId} as zone {zoneId}')

    def generate(self):
        self.notify.debug(f'GENERATE {self.doId}')
        DistributedObjectAI.generate(self)

        self.notify.debug(f'Creating Prop Gen AI on {self.doId} ({self.zoneId}')

        self.propGenerator = DistributedPropGeneratorAI(self.air, self.zoneId, specialZone = 1)
        self.propGenerator.generateWithRequired(self.zoneId)
        self.propGenerator.setLotPrivilegesForAvatar(self.ownerAvId, FLPermBuild | FLPermClearLoad | FLPermEditPerms)
        self.air.propGenerators[self.zoneId] = self.propGenerator

        if self.privacy == PRIVACY_MODE_FRIENDS_ONLY:
            av: DistributedToonAI = self.air.doId2do.get(self.ownerAvId)
            if av:
                friends = av.getFriendsList()
                for friendAvid, _ in friends:
                    self.propGenerator.setLotPrivilegesForAvatar(friendAvid, FLPermBuild)

        if self.saveToLoad:
            if os.path.exists(f'buildlots/player/{self.ownerAvId}/{self.saveToLoad}'):
                self.propGenerator.loadFromLotFile(f'buildlots/player/{self.ownerAvId}/{self.saveToLoad}')
        # When we save a lot, we don't want to manually overwrite the autosave, so when we generate this lot, let's pretend it's a new one.
        if self.saveToLoad == AUTOSAVE_FILENAME:
            self.saveToLoad = ''
        elif self.saveToLoad is not None:
            # Update with our latest visit date.
            self.save()

        self.accept(self.air.getPlayerEnterZoneEventName(self.zoneId), self.avIdEnteredLot)
        self.accept(f'friendChange-{self.ownerAvId}', self.friendChange)

    def requestDelete(self):
        self.notify.debug(f'Deleting {self.doId}')
        # Save the autosave then cleanup prop generator
        self.ignoreAll()
        # TODO: Save an autosave of the user's build
        if self.propGenerator:
            self.propGenerator.requestDelete()
            self.propGenerator = None
            if self.zoneId in self.air.propGenerators:
                del self.air.propGenerators[self.zoneId]
        DistributedObjectAI.requestDelete(self)

    def requestChangeTheme(self, theme: BuildLotThemes):
        if self.air.getAvatarIdFromSender() == self.ownerAvId:
            self.b_setTheme(theme)

    def b_setTheme(self, theme: BuildLotThemes):
        self.setTheme(theme)
        self.d_setTheme(theme)

    def d_setTheme(self, theme: BuildLotThemes):
        self.sendUpdate('setTheme', [theme])

    def setTheme(self, theme: BuildLotThemes):
        self.theme = theme

    def getTheme(self) -> BuildLotThemes:
        return self.theme

    def getLotName(self) -> str:
        return self.lotName

    def avIdEnteredLot(self, avId: int):
        av = self.air.doId2do.get(avId)
        if not av:
            return
        if avId in self.avIdsInZone:
            return
        self.avIdsInZone.append(avId)

        if self.privacy == PRIVACY_MODE_PUBLIC and avId != self.ownerAvId:
            self.propGenerator.setLotPrivilegesForAvatar(avId, FLPermBuild)

        self.notify.debug(f'{avId} Entered lot {self.zoneId}.{self.doId}')
        self.notify.debug(f'\t\tToons in lot: {self.getToonsInLot()}')
        self.acceptOnce(av.getZoneChangeEvent(), self.avIdExitedLot, extraArgs=[avId])
        self.acceptOnce(self.air.getAvatarExitEvent(avId), self.__handleUnexpectedExit, extraArgs=[avId])

    def friendChange(self, friendId, unfriended = 0):
        if self.privacy == PRIVACY_MODE_FRIENDS_ONLY:
            if unfriended:
                self.propGenerator.setLotPrivilegesForAvatar(friendId, 0)
            else:
                self.propGenerator.setLotPrivilegesForAvatar(friendId, FLPermBuild)

    def avIdExitedLot(self, avId: int, _, __):
        av = self.air.doId2do.get(avId)
        if not av:
            return

        if avId not in self.avIdsInZone:
            return

        self.avIdsInZone.remove(avId)

        self.ignore(av.getZoneChangeEvent())
        self.ignore(self.air.getAvatarExitEvent(avId))
        self.notify.debug(f'{avId} Exited lot {self.zoneId} | {self.doId}')
        self.notify.debug(f'Toons in lot: {self.getToonsInLot()}')

        if avId == self.ownerAvId:
            self.notify.debug(f'Lot {self.zoneId}.{self.doId} Owner Left. Booting others')
            self.shutdownLot()

    def __handleUnexpectedExit(self, avId):
        if avId not in self.avIdsInZone:
            return
        self.notify.debug(f'{avId} Unexpectedly exited')
        self.notify.debug(f'Toons in lot: {self.getToonsInLot()}')

        self.avIdsInZone.remove(avId)
        self.ignore('DOChangeZone-%s' % avId)
        self.ignore(self.air.getAvatarExitEvent(avId))

        if avId == self.ownerAvId:
            self.notify.debug(f'Lot {self.zoneId}.{self.doId} Owner Left. Booting others')
            self.shutdownLot()

    def shutdownLot(self):
        self.notify.info(f'Shutting down lot {self.zoneId}.{self.doId}')
        self.canUsersJoin = False
        self.autosave()

        self.doMethodLater(5, self.destroyLot, name = f'destroyLot{self.zoneId}.{self.doId}')

    def destroyLot(self, task):
        if self.ownerAvId in self.getToonsInLot():
            self.notify.info("Attempted to shut down lot, but toon re-entered. Cancelling destruction.")
            return task.done
        for toon in self.getToonsInLot().values():
            self.sendUpdateToAvatarId(toon.doId, 'kickOut', [])

        self.air.buildLotMgr.destroyBuildLot(self.ownerAvId)
        return task.done

    def getToonsInLot(self) -> Dict[int, DistributedToonAI]:
        return self.air.getObjectsOfClassInZone(self.air.districtId, self.zoneId, DistributedToonAI)

    def generateLotFilename(self):
        ltime = time.localtime()
        return f'{ltime[0] - 2000}{ltime[1]}{ltime[2]}_{ltime[3]}{ltime[4]}{ltime[5]}.blot'

    def autosave(self):
        self.save(AUTOSAVE_FILENAME)

    def requestSaveLot(self, backup: bool = False):
        """
        There are two modes of saving in this case:
          - backup(True): A completely new file is saved to the Realm.
          - backup(False): A new save is created if the current Build Field is not saved, otherwise save to the current Build Field file.
        """
        avId = self.air.getAvatarIdFromSender()
        if avId == self.ownerAvId:
            lotName = self.lotName
            if backup:
                if os.path.exists(f'buildlots/player/{avId}'):
                    savesCount = len(os.listdir(f'buildlots/player/{avId}'))
                else:
                    savesCount = 0
                if savesCount >= MaxLotCount:
                    self.sendUpdateToAvatarId(avId, 'lotMessage', [LOT_LIMIT_REACHED])
                    return
                fileToSave = self.generateLotFilename()
                if not self.saveToLoad:
                    self.saveToLoad = fileToSave
            elif self.saveToLoad:
                fileToSave = self.saveToLoad
            else:
                if os.path.exists(f'buildlots/player/{avId}'):
                    savesCount = len(os.listdir(f'buildlots/player/{avId}'))
                else:
                    savesCount = 0
                if savesCount >= MaxLotCount:
                    self.sendUpdateToAvatarId(avId, 'lotMessage', [LOT_LIMIT_REACHED])
                    return
                fileToSave = self.generateLotFilename()
                self.saveToLoad = fileToSave
 
            self.save(fileToSave, lotName)

    def save(self, fileToSave: str = '', lotName: str = ''):
        if not fileToSave:
            fileToSave = self.saveToLoad
        if not lotName:
            lotName = self.lotName
        # If we don't yet have a backups/props directory, make one
        if not os.path.exists('buildlots/'):
            os.mkdir('buildlots/')
        if not os.path.exists('buildlots/player/'):
            os.mkdir('buildlots/player/')
        if not os.path.exists(f'buildlots/player/{self.ownerAvId}/'):
            os.mkdir(f'buildlots/player/{self.ownerAvId}/')
        propData = OrderedDict({'propgen_version': PropGlobals.PropGenVersion})
        for propID, prop in self.propGenerator.propInfo.items():
            propInfo = OrderedDict()
            propInfo['PropType'] = prop[0]
            propInfo['Position'] = prop[1]
            propInfo['Rotation'] = prop[2]
            propInfo['Scale'] = prop[3]
            propInfo['Data'] = prop[4]
            propData[propID] = propInfo

        file = {
            'name': lotName,
            'theme': self.theme,
            'privacy': self.privacy,
            'last_edit': datetime.now().timestamp(),
            'propgen_save': propData
        }
        with open(f'buildlots/player/{self.ownerAvId}/' + fileToSave, 'w') as data:
            json.dump(file, data, indent = 4)
