import time
import hmac, hashlib, json, os, uuid, random
import urllib
from datetime import datetime

from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectGlobalUD import DistributedObjectGlobalUD
from direct.distributed.PyDatagram import *
from direct.distributed.MsgTypes import *
from direct.fsm.FSM import FSM
from panda3d.core import URLSpec, HTTPClient, HTTPChannel

from otp.distributed import OtpDoGlobals
from otp.login import HTTPUtil
from otp.otpbase import OTPGlobals, OTPLocalizer
from otp.uberdog.GameServicesManager import FIXED_KEY

from toontown.toon.ToonDNA import ToonDNA
from toontown.episodes.EpisodeConfig import DefaultEpisodeStatuses
from copy import deepcopy

from toontown.toonbase import ServerSettings


# --- ACCOUNT DATABASES ---
# These classes make up the available account database interfaces for Toontown Realms.
# At the moment, there is only the LocalAccountDB interface.
# These will be explained further in their respective class definition.
class AccountDB:
    """
    AccountDB is the base class for all account database interface implementations. Inherit from this class when
    creating new account database interfaces, but DO NOT try to use this class on its own; you'll have a bad time!
    """
    notify = DirectNotifyGlobal.directNotify.newCategory('AccountDB')

    def __init__(self, gameServicesManager):
        self.gameServicesManager = gameServicesManager

        # This uses json, so we open the json file:
        self.accountDbPath = simbase.config.GetString('accountdb-local-file', 'astron/databases/accounts.json')

    def lookup(self, playToken, callback):
        raise NotImplementedError('Must be overridden by subclass.')

    def getAccountsList(self):
        # This function exists so we can load up any modification made to the
        # json file without having to reboot the UberDOG server.
        # Also, it saves up precious memory.
        if not os.path.exists(self.accountDbPath):
            # Return an empty dictionary.
            return {}
        with open(self.accountDbPath) as data:
            return json.load(data)

    def storeAccountID(self, databaseId, accountId, callback):
        accounts = self.getAccountsList()
        accounts[databaseId] = accountId
        try:
            with open(self.accountDbPath, 'w') as data:
                json.dump(accounts, data, indent=4)
                callback(True)
        except:
            self.notify.warning('Unable to associate user %s with account %d!' % (databaseId, accountId))
            callback(False)


class LocalAccountDB(AccountDB):
    """
    LocalAccountDB is the regular database interface implementation. This is the default account database
    interface when running a server. LocalAccountDB accepts a username, and assigns each new user with whatever
    the default access level specified is, or "SERVER_HOSTER" if they are the first user registered into the database.
    """
    notify = DirectNotifyGlobal.directNotify.newCategory('LocalAccountDB')

    def lookup(self, playToken, callback):
        # Check if this play token exists in the json file:
        accounts = self.getAccountsList()
        if str(playToken) not in accounts:
            # It is not, so we'll associate them with a brand new account object.
            accessLevel = "SERVER_HOSTER"
            if accounts.keys():
                accessLevel = ServerSettings.DefaultAccessLevel.get()
            callback({'success': True,
                      'accountId': 0,
                      'databaseId': playToken,
                      'accessLevel': accessLevel})
        else:
            def handleAccount(dclass, fields):
                if dclass != self.gameServicesManager.air.dclassesByName['AccountUD']:
                    result = {'success': False,
                              'reason': 'Your account object (%s) was not found in the database!' % dclass}
                else:
                    # We already have an account object, so we'll just return what we have.
                    result = {'success': True,
                              'accountId': int(accounts[playToken]),
                              'databaseId': playToken,
                              'accessLevel': fields.get('ACCESS_LEVEL', 'USER')}

                callback(result)

            self.gameServicesManager.air.dbInterface.queryObject(self.gameServicesManager.air.dbId,
                                                                 int(accounts[playToken]), handleAccount)


class GameOperation(FSM):
    """
    GameOperation is the base class for all other operations used by the GameServicesManager.
    """
    notify = DirectNotifyGlobal.directNotify.newCategory('GameOperation')
    targetConnection = False

    def __init__(self, gameServicesManager, target):
        FSM.__init__(self, self.__class__.__name__)
        self.gameServicesManager = gameServicesManager
        self.target = target

    def enterOff(self):
        # Deletes the target from either connection2fsm or account2fsm
        # depending on the value of self.targetConnection.
        if self.targetConnection:
            if self.target in self.gameServicesManager.connection2fsm:
                del self.gameServicesManager.connection2fsm[self.target]
        else:
            if self.target in self.gameServicesManager.account2fsm:
                del self.gameServicesManager.account2fsm[self.target]

    def enterKill(self, reason=''):
        # Kills either the target connection or the target account
        # depending on the value of self.targetConnection, and then
        # sets this FSM's state to Off.
        if self.targetConnection:
            self.gameServicesManager.killConnection(self.target, reason)
        else:
            self.gameServicesManager.killAccount(self.target, reason)

        self.demand('Off')


class LoginOperation(GameOperation):
    notify = DirectNotifyGlobal.directNotify.newCategory('LoginOperation')
    targetConnection = True

    def __init__(self, gameServicesManager, target):
        GameOperation.__init__(self, gameServicesManager, target)
        self.playToken = None
        self.account = None

    def enterStart(self, playToken):
        # Sets self.playToken, then enters the QueryAccountDB state.
        self.playToken = playToken
        self.demand('QueryAccountDB')

    def enterQueryAccountDB(self):
        # Calls the lookup function on the GameServicesManager's defined account DB interface.
        self.gameServicesManager.accountDb.lookup(self.playToken, self.__handleLookup)

    def __handleLookup(self, result):
        # This is a callback function that will be called by the lookup function
        # of the GameServicesManager's account DB interface. It processes the
        # lookup function's result & determines which operation should run next.
        if not result.get('success'):
            # The play token was rejected! Kill the connection.
            self.gameServicesManager.air.writeServerEvent('play-token-rejected', self.target, self.playToken)
            self.demand('Kill', result.get('reason', 'The accounts database rejected your play token.'))
            return

        # Grab the databaseId, accessLevel, and accountId from the result.
        self.databaseId = result.get('databaseId', 0)
        self.accessLevel = result.get('accessLevel', 'NO_ACCESS')
        accountId = result.get('accountId', 0)

        if accountId:
            # There is an account ID, so let's retrieve the associated account.
            self.accountId = accountId
            self.demand('RetrieveAccount')
        else:
            # There is no account ID, so let's create a new account.
            self.demand('CreateAccount')

    def enterCreateAccount(self):
        # Creates a brand new account & stores it in the database.
        self.account = {'ACCOUNT_AV_SET': [0] * 6,
                        'ESTATE_ID': 0,
                        'ACCOUNT_AV_SET_DEL': [],
                        'CREATED': time.ctime(),
                        'LAST_LOGIN': time.ctime(),
                        'ACCOUNT_ID': str(self.databaseId),
                        'ACCESS_LEVEL': self.accessLevel,
                        'NEW_USER': True,
                        'EPISODE_COMPLETIONS': deepcopy(DefaultEpisodeStatuses)}

        # Create the account object in the database using the data from self.account.
        # self.__handleCreate is the callback which will be called after createObject has completed.
        self.gameServicesManager.air.dbInterface.createObject(self.gameServicesManager.air.dbId,
                                                              self.gameServicesManager.air.dclassesByName['AccountUD'],
                                                              self.account, self.__handleCreate)

    def __handleCreate(self, accountId):
        # This function handles successful & unsuccessful account creations.
        if self.state != 'CreateAccount':
            # If we're not in the CreateAccount state, this request is invalid.
            self.notify.warning('Received CreateAccount response outside of the CreateAccount state.')
            return

        if not accountId:
            # If we don't have an accountId, then that means the database was unable
            # to create an account object for us, for whatever reason. Kill the connection.
            self.notify.warning('Database failed to create an account object!')
            self.demand('Kill', 'Your account object could not be created in the game database.')
            return

        # Otherwise, the account object was created successfully!
        self.gameServicesManager.air.writeServerEvent('account-created', accountId)

        # We can now enter the StoreAccountID state.
        self.accountId = accountId
        self.demand('StoreAccountID')

    def enterStoreAccountID(self):
        # Stores the account ID in the account bridge.
        # self.__handleStored is the callback which
        # will be called after storeAccountID has completed.
        self.gameServicesManager.accountDb.storeAccountID(self.databaseId, self.accountId, self.__handleStored)

    def __handleStored(self, success=True):
        if not success:
            # The account bridge was unable to store the account ID,
            # for whatever reason. Kill the connection.
            self.demand('Kill', 'The account server could not save your account DB ID!')
            return

        # We are all set with account creation now! It's time to enter the SetAccount state.
        self.demand('SetAccount')

    def enterRetrieveAccount(self):
        # Query the database object associated with self.accountId.
        # self.__handleRetrieve is the callback which will be called
        # after queryObject has completed.
        self.gameServicesManager.air.dbInterface.queryObject(self.gameServicesManager.air.dbId, self.accountId,
                                                             self.__handleRetrieve)

    def __handleRetrieve(self, dclass, fields):
        # Checks if the queried object is valid and if it is, enters
        # the SetAccount state. Otherwise, the connection is killed.
        if dclass != self.gameServicesManager.air.dclassesByName['AccountUD']:
            # This is not an account object! Kill the connection.
            self.demand('Kill', 'Your account object (%s) was not found in the database!' % dclass)
            return

        # We can now enter the SetAccount state.
        self.account = fields
        self.demand('SetAccount')

    def enterSetAccount(self):
        # If somebody's already logged into this account, disconnect them.
        datagram = PyDatagram()
        datagram.addServerHeader(self.gameServicesManager.GetAccountConnectionChannel(self.accountId),
                                 self.gameServicesManager.air.ourChannel, CLIENTAGENT_EJECT)
        datagram.addUint16(OTPGlobals.BootedLoggedInElsewhere)
        datagram.addString('This account has been logged into elsewhere.')
        self.gameServicesManager.air.send(datagram)

        # Now we'll add this connection to the account channel.
        datagram = PyDatagram()
        datagram.addServerHeader(self.target, self.gameServicesManager.air.ourChannel, CLIENTAGENT_OPEN_CHANNEL)
        datagram.addChannel(self.gameServicesManager.GetAccountConnectionChannel(self.accountId))
        self.gameServicesManager.air.send(datagram)

        # Set their sender channel to represent their account affiliation.
        datagram = PyDatagram()
        datagram.addServerHeader(self.target, self.gameServicesManager.air.ourChannel, CLIENTAGENT_SET_CLIENT_ID)
        datagram.addChannel(self.accountId << 32)  # accountId in high 32 bits, 0 in low (no avatar).
        self.gameServicesManager.air.send(datagram)

        # We can now un-sandbox the sender.
        self.gameServicesManager.air.setClientState(self.target, 2)  # ESTABLISHED state.

        # Update the last login timestamp.
        self.gameServicesManager.air.dbInterface.updateObject(self.gameServicesManager.air.dbId, self.accountId,
                                                              self.gameServicesManager.air.dclassesByName['AccountUD'],
                                                              {'LAST_LOGIN': time.ctime(),
                                                               'ACCOUNT_ID': str(self.databaseId),
                                                               'ACCESS_LEVEL': self.accessLevel})

        # We're done.
        self.gameServicesManager.air.writeServerEvent('account-login', clientId=self.target, accId=self.accountId,
                                                      dbId=self.databaseId, playToken=self.playToken)

        # Send the acceptLogin update through the GameServicesManager & set this operation's state to Off.
        self.gameServicesManager.sendUpdateToChannel(self.target, 'acceptLogin',
                                                     [self.gameServicesManager.air.serverJoinSecret])
        self.demand('Off')


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
        self.avList = self.avList[:6]
        self.avList += [0] * (6 - len(self.avList))

        # We're done; enter the postAccountState.
        self.demand(self.postAccountState)


class GetAvatarsOperation(AvatarOperation):
    notify = DirectNotifyGlobal.directNotify.newCategory('GetAvatarsOperation')
    postAccountState = 'QueryAvatars'

    def __init__(self, gameServicesManager, target):
        AvatarOperation.__init__(self, gameServicesManager, target)
        self.pendingAvatars = None
        self.avatarFields = None
        self.accountFields = None

    def enterStart(self):
        # First, retrieve the account.
        self.demand('RetrieveAccount')

    def enterQueryAvatars(self):
        # Now, we will query the avatars that exist in the account.
        self.pendingAvatars = set()
        self.avatarFields = {}

        def __handleAccountInfo(dclass, fields):
            # Set the account info
            self.accountFields = fields

            # Loop through the list of avatars:
            for avId in self.avList:
                if avId:
                    # This index contains an avatar! Add it to the pending avatars.
                    self.pendingAvatars.add(avId)

                    # This is our callback function that queryObject
                    # will call when done querying each avatar object.
                    def response(dclass, fields, avId=avId):
                        if self.state != 'QueryAvatars':
                            # We're not in the QueryAvatars state, so this request is invalid.
                            return

                        if dclass != self.gameServicesManager.air.dclassesByName[self.gameServicesManager.avatarDclass]:
                            # The dclass is invalid! Kill the connection.
                            self.demand('Kill', 'One of the account\'s avatars is invalid! dclass = %s, expected = %s' % (
                                dclass, self.gameServicesManager.avatarDclass))
                            return

                        # Otherwise, we're all set! Add the queried avatar fields to the
                        # avatarFields array, remove from the pending list, and set our
                        # state to SendAvatars.
                        self.avatarFields[avId] = fields
                        self.pendingAvatars.remove(avId)
                        if not self.pendingAvatars:
                            self.demand('SendAvatars')

                    # Query the avatar object.
                    self.gameServicesManager.air.dbInterface.queryObject(self.gameServicesManager.air.dbId, avId, response)

            if not self.pendingAvatars:
                # No pending avatars! Set our state to SendAvatars.
                self.demand('SendAvatars')

        data = self.gameServicesManager.air.dbInterface.queryObject(self.gameServicesManager.air.dbId, self.target,
                                                                    __handleAccountInfo)

    def enterSendAvatars(self):
        # Here is where we'll construct a list of potential avatars,
        # given the data from self.avatarFields, and send that to the client.
        potentialAvatars = []

        # Loop through the avatarFields array:
        for avId, fields in list(self.avatarFields.items()):
            # Get the appropriate values.
            index = self.avList.index(avId)
            wishNameState = fields.get('WishNameState', [''])[0]
            name = fields['setName'][0]
            nameState = 0
            if wishNameState == 'OPEN':
                nameState = 1
            elif wishNameState == 'PENDING':
                nameState = 2
            elif wishNameState == 'APPROVED':
                nameState = 3
                name = fields['WishName'][0]
            elif wishNameState == 'REJECTED':
                nameState = 4
            elif wishNameState == 'LOCKED':
                nameState = 0
            else:
                self.gameServicesManager.notify.warning(
                    'Avatar %s is in unknown name state %s.' % (avId, wishNameState))
                nameState = 0

            # Add those to potentialAvatars.
            potentialAvatars.append([
                avId, name, fields['setDNAString'][0], index, nameState,
                fields['setHat'], fields['setGlasses'], fields['setBackpack'], fields['setShoes'],
                fields['setLastZone'][0], fields.get('setNametagStyle', (100,))[0], fields.get('setNametagType', (0,))[0],
                fields['setHp'][0], fields['setMaxHp'][0]
            ])

        # Get our new user status
        newUser = self.accountFields.get('NEW_USER', True)
        if newUser:
            self.gameServicesManager.air.dbInterface.updateObject(self.gameServicesManager.air.dbId, self.target,
                                                                  self.gameServicesManager.air.dclassesByName['AccountUD'],
                                                                  {'NEW_USER': False})

        # We're done; send the avatarListResponse update through the
        # GameServicesManager, then we can set this operation's
        # state to Off.
        self.gameServicesManager.sendUpdateToAccountId(self.target, 'avatarListResponse', [potentialAvatars])
        self.demand('Off')


# n.b.: We inherit from GetAvatarsOperation here as the remove
# operation ends in a setAvatars message being sent to the client.
class RemoveAvatarOperation(GetAvatarsOperation):
    notify = DirectNotifyGlobal.directNotify.newCategory('RemoveAvatarOperation')
    postAccountState = 'ProcessRemove'

    def __init__(self, gameServicesManager, target):
        GetAvatarsOperation.__init__(self, gameServicesManager, target)
        self.avId = None

    def enterStart(self, avId):
        # Store this value & call the base function.
        self.avId = avId
        GetAvatarsOperation.enterStart(self)

    def enterProcessRemove(self):
        # Make sure that the target avatar is part of the account:
        if self.avId not in self.avList:
            # The sender tried to remove an avatar not on the account! Kill the connection.
            self.demand('Kill', 'Tried to remove an avatar not on the account!')
            return

        # Get the index of this avatar.
        index = self.avList.index(self.avId)
        self.avList[index] = 0

        # We will now add this avatar to ACCOUNT_AV_SET_DEL.
        avatarsRemoved = list(self.account.get('ACCOUNT_AV_SET_DEL', []))
        if len(avatarsRemoved) >= 100:
            avatarsRemoved.pop(0)
        avatarsRemoved.append([self.avId, int(time.time())])

        # Get the estate ID of this account.
        estateId = self.account.get('ESTATE_ID', 0)

        if estateId != 0:
            # The following will assume that the house already exists,
            # however it shouldn't be a problem if it doesn't.
            self.gameServicesManager.air.dbInterface.updateObject(self.gameServicesManager.air.dbId, estateId,
                                                                  self.gameServicesManager.air.dclassesByName[
                                                                      'DistributedEstateAI'],
                                                                  {'setSlot%sToonId' % index: [0],
                                                                   'setSlot%sItems' % index: [[]]})

        if self.gameServicesManager.air.ttrmSocialManager:
            self.gameServicesManager.air.ttrmSocialManager.clearList(self.avId)
        else:
            socialManagerDoId = OtpDoGlobals.OTP_DO_ID_TTRM_SOCIAL_MANAGER
            socialManagerDclass = self.gameServicesManager.air.dclassesByName['TTRMSocialManagerUD']
            datagram = socialManagerDclass.aiFormatUpdate('clearList', socialManagerDoId, socialManagerDoId,
                                                           self.gameServicesManager.air.ourChannel, [self.avId])
            self.gameServicesManager.air.send(datagram)

        # We can now update the account with the new data. self.__handleRemove is the
        # callback which will be called upon completion of updateObject.
        self.gameServicesManager.air.dbInterface.updateObject(self.gameServicesManager.air.dbId, self.target,
                                                              self.gameServicesManager.air.dclassesByName['AccountUD'],
                                                              {'ACCOUNT_AV_SET': self.avList,
                                                               'ACCOUNT_AV_SET_DEL': avatarsRemoved},
                                                              {'ACCOUNT_AV_SET': self.account['ACCOUNT_AV_SET'],
                                                               'ACCOUNT_AV_SET_DEL': self.account[
                                                                   'ACCOUNT_AV_SET_DEL']},
                                                              self.__handleRemove)

    def __handleRemove(self, fields):
        if fields:
            # The avatar was unable to be removed from the account! Kill the account.
            self.demand('Kill', 'Database failed to mark the avatar as removed!')
            return

        # Otherwise, we're done! We'll enter the QueryAvatars state now so that
        # the user is sent back to the avatar chooser.
        self.gameServicesManager.air.writeServerEvent('avatar-deleted', self.avId, self.target)
        self.demand('QueryAvatars')


class LoadAvatarOperation(AvatarOperation):
    notify = DirectNotifyGlobal.directNotify.newCategory('LoadAvatarOperation')
    postAccountState = 'GetTargetAvatar'

    def __init__(self, gameServicesManager, target):
        AvatarOperation.__init__(self, gameServicesManager, target)
        self.avId = None
        self.hwId = None
        self.uuid = None
        self.ip = None

    def enterStart(self, avId, hwId, uuid, ip):
        # Store this value & move on to RetrieveAccount
        self.avId = avId
        self.hwId = hwId
        self.uuid = uuid
        self.ip = ip
        self.demand('RetrieveAccount')

    def enterGetTargetAvatar(self):
        # Check if the target avatar is 6, meaning the requester wants a Temporary Toon.
        if self.avId == 6:
            # It is, allocate a Temporary Toon ID, and move on to SetAvatar.
            self.avId = self.gameServicesManager.curTempId
            self.gameServicesManager.curTempId += 1
            if self.gameServicesManager.curTempId > OTPGlobals.TempAvIdEnd:
                self.gameServicesManager.curTempId = OTPGlobals.TempAvIdBegin
            self.avatar = 'Temporary'
            self.demand('SetAvatar')
            return
        # Make sure that the target avatar is part of the account:
        if self.avId not in self.avList:
            # The sender tried to play on an avatar not on the account! Kill the connection.
            self.demand('Kill', 'Tried to play on an avatar not on the account!')
            return

        # Query the database for the avatar. self.__handleAvatar is
        # our callback which will be called upon queryObject's completion.
        self.gameServicesManager.air.dbInterface.queryObject(self.gameServicesManager.air.dbId, self.avId,
                                                             self.__handleAvatar)

    def __handleAvatar(self, dclass, fields):
        if dclass != self.gameServicesManager.air.dclassesByName[self.gameServicesManager.avatarDclass]:
            # This dclass is not a valid avatar! Kill the connection.
            self.demand('Kill', 'One of the account\'s avatars is invalid!')
            return

        # Store the avatar & move on to SetAvatar.
        self.avatar = fields
        self.demand('SetAvatar')

    def enterSetAvatar(self):
        # Get the client channel.
        channel = self.gameServicesManager.GetAccountConnectionChannel(self.target)

        # We will first assign a POST_REMOVE that will unload the
        # avatar in the event of them disconnecting while we are working.
        cleanupDatagram = PyDatagram()
        cleanupDatagram.addServerHeader(self.avId, channel, STATESERVER_OBJECT_DELETE_RAM)
        cleanupDatagram.addUint32(self.avId)
        datagram = PyDatagram()
        datagram.addServerHeader(channel, self.gameServicesManager.air.ourChannel, CLIENTAGENT_ADD_POST_REMOVE)
        datagram.addBlob(cleanupDatagram.getMessage())
        self.gameServicesManager.air.send(datagram)

        # We will now set the account's days since creation on the client.
        creationDate = self.getCreationDate()
        accountDays = -1
        if creationDate:
            now = datetime.fromtimestamp(time.mktime(time.strptime(time.ctime())))
            accountDays = abs((now - creationDate).days)

        if accountDays < 0 or accountDays > 4294967295:
            accountDays = 100000

        self.gameServicesManager.sendUpdateToAccountId(self.target, 'receiveAccountDays', [accountDays])

        gamemode = self.gameServicesManager.getGamemode()

        # Get the avatar's "true" access (that is, the integer value that corresponds to the assigned string value).
        accessLevel = self.account.get('ACCESS_LEVEL', 'NO_ACCESS')
        accessLevel = OTPGlobals.AccessLevelName2Int.get(accessLevel, 0)
        if gamemode == OTPGlobals.ModeOffline and accessLevel < 500:
            # If the server's running on Offline mode, grant the user with SERVER_HOSTER access
            # (It'll won't effect the one that's currently on database.).
            accessLevel = OTPGlobals.AccessLevelName2Int.get('SERVER_HOSTER', 0)

        episodeStatuses = None
        if self.avatar != 'Temporary':
            # set ze episode statuses to the AI
            episodeStatuses = list(self.account.get('EPISODE_COMPLETIONS', deepcopy(DefaultEpisodeStatuses)))
            self.notify.debug("SetAvatar(): Setting episode statuses \"{}\" for avatar \"{}\" from account \"{}\"".format(episodeStatuses, self.avId, self.target))

            # New user status
            newUserStatus = self.account.get('NEW_USER', True)
            # Our account id
            accountId = self.target

            # Send our muted status to the AI
            muted, minutes = 0, 0
            muteData = simbase.air.banManager.openMuteFile()
            if str(accountId) in list(muteData.keys()):
                muteInfo = muteData[str(accountId)]
                now = datetime.now()
                expire = muteInfo.get('expire', 0)
                if not isinstance(expire, int) and not expire == 0:
                    if not isinstance(expire, datetime):
                        expire = datetime.strptime(expire, "%Y-%m-%d %H:%M:%S.%f")
                    if expire < now:
                        simbase.air.banManager.handleUnmute(accountId)
                    else:
                        minutes = int((expire - now).total_seconds() / 60)
                        muted = 1
                else:
                    muted = 1
            username = self.account.get('ACCOUNT_ID', 'error somehow')

            endpoint = ServerSettings.AccessLevelEndpoint.get()
            if endpoint != 'localdb':
                resp = json.loads(
                    HTTPUtil.getHTTPResponse(
                        URLSpec(
                            f'{endpoint}{URLSpec.quotePlus(username.replace("/", ""))}'),
                        self.gameServicesManager.websiteChannel)[0]
                )

                self.notify.info(f'{username} logged in with access level {resp}')
                accessLevel = resp
            # We will now activate the avatar on the DBSS.
            self.gameServicesManager.air.sendActivate(self.avId, 0, 0, self.gameServicesManager.air.dclassesByName[
                self.gameServicesManager.avatarDclass], {'setAccessLevel': [accessLevel],
                                                         'setEpisodeStatuses': [episodeStatuses],
                                                         'setNewUserStatus': [newUserStatus],
                                                         'setMuted': [muted, minutes]})
        else:
            # TODO: Determine initial fields from episode config.
            dna = ToonDNA()
            dna.newToonFromProperties(*OTPGlobals.DefaultDNAString)

            # We will not generate a new temporary toon on the State Server.
            self.gameServicesManager.air.generateTemporaryAvatar(self.avId, 0, 0,
                {'setDNAString': [dna.makeNetString()], 'setAccessLevel': [accessLevel],
                 # we don't care for episode statuses here for now. we just need them to deal with some garbage related to trying to send this to both client and AI
                 'setEpisodeStatuses': [deepcopy(DefaultEpisodeStatuses)],
                 'setNewUserStatus': [False]})
        # Next, we will add them to the avatar channel.
        datagram = PyDatagram()
        datagram.addServerHeader(channel, self.gameServicesManager.air.ourChannel, CLIENTAGENT_OPEN_CHANNEL)
        datagram.addChannel(self.gameServicesManager.GetPuppetConnectionChannel(self.avId))
        self.gameServicesManager.air.send(datagram)

        # We will now set the avatar as the client's session object.
        self.gameServicesManager.air.clientAddSessionObject(channel, self.avId)

        # Now we need to set their sender channel to represent their account affiliation.
        datagram = PyDatagram()
        datagram.addServerHeader(channel, self.gameServicesManager.air.ourChannel, CLIENTAGENT_SET_CLIENT_ID)
        datagram.addChannel(self.target << 32 | self.avId)  # accountId in high 32 bits, avatar in low.
        self.gameServicesManager.air.send(datagram)

        # We will now grant ownership.
        self.gameServicesManager.air.setOwner(self.avId, channel)

        # Don't do any friends manager related stuff if we're going on a Temporary Toon...
        if self.avatar != 'Temporary':
            friendsList = self.avatar['setFriendsList'][0]
            # If there are any Temp Toon IDs in the friends list, remove them.
            modifiedFriendsList = False
            for friendEntry in friendsList[:]:
                if OTPGlobals.TempAvIdBegin <= friendEntry[0] <= OTPGlobals.TempAvIdEnd:
                    friendsList.remove(friendEntry)
                    modifiedFriendsList = True

            avDclass = self.gameServicesManager.air.dclassesByName['DistributedToonUD']
            if modifiedFriendsList:
                datagram = avDclass.aiFormatUpdate('setFriendsList', self.avId, self.avId,
                                                   self.gameServicesManager.air.ourChannel, [friendsList])
                self.gameServicesManager.air.send(datagram)

            # Tell the social manager that we are online.
            self.gameServicesManager.air.ttrmSocialManager.addOnlineAvatar(self.avId)

            if episodeStatuses is not None:
                # set ze episode statuses to the client
                datagramz = avDclass.aiFormatUpdate('setEpisodeStatuses',
                                                    self.avId,
                                                    self.avId,
                                                    self.gameServicesManager.air.ourChannel,
                                                    [episodeStatuses])
                self.gameServicesManager.air.send(datagramz)

            # Now we'll let the party manager update any party related fields (they're not stored in Astron's database).
            simbase.air.partyManager.updatePartyStatusForAvatar(self.avId)

        # Now, add the accountId to the ban manager. (Only for refering to it for banning)
        simbase.air.banManager.addClient(self.target, self.hwId, self.uuid, self.ip)

        # We can now finally shut down this operation.
        self.gameServicesManager.air.writeServerEvent('avatar-chosen', avId=self.avId, accId=self.target)
        self.demand('Off')

    def getCreationDate(self):
        # Based on game creation date:
        creationDate = self.account.get('CREATED', '')
        try:
            creationDate = datetime.fromtimestamp(time.mktime(time.strptime(creationDate)))
        except ValueError:
            creationDate = ''

        return creationDate


class UnloadAvatarOperation(GameOperation):
    notify = DirectNotifyGlobal.directNotify.newCategory('UnloadAvatarOperation')

    def __init__(self, gameServicesManager, target):
        GameOperation.__init__(self, gameServicesManager, target)
        self.avId = None

    def enterStart(self, avId):
        # Store the avId.
        self.avId = avId
        # We actually don't even need to query the account, as we know
        # that the avatar is being played, so let's just unload the avatar.
        self.demand('UnloadAvatar')

    def enterUnloadAvatar(self):
        # Get the client channel.
        channel = self.gameServicesManager.GetAccountConnectionChannel(self.target)

        if not OTPGlobals.TempAvIdBegin <= self.avId <= OTPGlobals.TempAvIdEnd:
            # Tell the social manager that we are no longer online.
            self.gameServicesManager.air.ttrmSocialManager.removeOnlineAvatar(self.avId)

        # First, remove our POST_REMOVES.
        datagram = PyDatagram()
        datagram.addServerHeader(channel, self.gameServicesManager.air.ourChannel, CLIENTAGENT_CLEAR_POST_REMOVES)
        self.gameServicesManager.air.send(datagram)

        # Next, remove the avatar channel.
        datagram = PyDatagram()
        datagram.addServerHeader(channel, self.gameServicesManager.air.ourChannel, CLIENTAGENT_CLOSE_CHANNEL)
        datagram.addChannel(self.gameServicesManager.GetPuppetConnectionChannel(self.avId))
        self.gameServicesManager.air.send(datagram)

        # Next, reset the sender channel.
        datagram = PyDatagram()
        datagram.addServerHeader(channel, self.gameServicesManager.air.ourChannel, CLIENTAGENT_SET_CLIENT_ID)
        datagram.addChannel(self.target << 32)  # accountId in high 32 bits, no avatar in low.
        self.gameServicesManager.air.send(datagram)

        # Reset the session object.
        datagram = PyDatagram()
        datagram.addServerHeader(channel, self.gameServicesManager.air.ourChannel, CLIENTAGENT_REMOVE_SESSION_OBJECT)
        datagram.addUint32(self.avId)
        self.gameServicesManager.air.send(datagram)

        # Unload the avatar object.
        datagram = PyDatagram()
        datagram.addServerHeader(self.avId, channel, STATESERVER_OBJECT_DELETE_RAM)
        datagram.addUint32(self.avId)
        self.gameServicesManager.air.send(datagram)

        simbase.air.banManager.removeClient(self.target)

        # We're done! We can now shut down this operation.
        self.gameServicesManager.air.writeServerEvent('avatar-unloaded', avId=self.avId)
        self.demand('Off')


class GameServicesManagerUD(DistributedObjectGlobalUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('GameServicesManagerUD')
    avatarDclass = None  # Must be overridden by subclass.

    def __init__(self, air):
        DistributedObjectGlobalUD.__init__(self, air)
        self.connection2fsm = {}
        self.account2fsm = {}
        self.recentAccounts = []
        self.accountDb = None
        self.curTempId = OTPGlobals.TempAvIdBegin
        self.sender = None
        self.playToken = None
        self.hwId = None
        self.uuid = None
        self.ip = None

        self.gamemode = int(os.getenv('TTOFF_GAME_MODE', OTPGlobals.ModeOffline))
        self.isOfficial = False

        if ServerSettings.AccessLevelEndpoint.get() != 'localdb':
            self.isOfficial = True

        if self.isOfficial:
            self.websiteChannel = HTTPClient.getGlobalPtr().makeChannel(True)  # type: HTTPChannel
            HTTPClient.getGlobalPtr().setVerifySsl(HTTPClient.VSNoDateCheck)
            self.notify.info("We're running the official server! (I HOPE)")

    def announceGenerate(self):
        DistributedObjectGlobalUD.announceGenerate(self)

        # The purpose of connection2fsm & account2fsm are to
        # keep track of the connection & account IDs that are
        # currently running an operation on the GameServicesManager.
        # Ideally, this will help us prevent clients from running
        # more than one operation at a time which could potentially
        # lead to race conditions & the exploitation of them.
        self.connection2fsm = {}
        self.account2fsm = {}

        # Instantiate the account database interface.
        self.accountDb = LocalAccountDB(self)

    def login(self, playToken, hwId, uuid, signature, platform, joinSecret):
        # Get the connection ID.
        self.sender = self.air.getMsgSender()

        # The user's playtoken, aka username.
        self.playToken = playToken

        # Notify that someone is trying to connect.
        self.notify.info('Play token {} received from {} under platform {}'.format(self.playToken.encode('utf-8'), self.sender, platform))

        # Save their hardware ID.
        self.hwId = hwId
        hwId = hwId.decode('utf-8')

        # Let's check to make sure the hardware ID is legit.
        # This is probably a very, very shitty and hacky way of checking it, but whatever.
        # If it causes problems in the future we can always change it.
        # Right now, I just check to see if there is at least one integer in it.
        integer = None
        for letter in hwId:
            try:
                integer = int(letter)
            except:
                pass
            if integer:
                break

        if not integer:
            self.killConnection(connectionId=self.sender, reason=OTPLocalizer.RejectInvalidHWID)
            return

        # And a universally unique identifier.
        if uuid:
            self.uuid = uuid
        else:
            self.killConnection(connectionId=self.sender, reason=OTPLocalizer.RejectInvalidHWID)
            return

        # Grab their IP Address and save that too.
        simbase.air.getNetworkAddress(self.sender, self.__setIpAddress)

        # Don't let them in if they are already logged in.
        if self.sender >> 32:
            self.killConnection(self.sender, OTPLocalizer.RejectAlreadyLoggedIn)
            return

        # Here we generate a signature based off of a lot of randomness.
        # I think this is random enough? I'm not 100% sure honestly.
        keyPrefix = config.GetString('ttoff-words-of-wisdom', 'i-love-disyer')
        version = config.GetString('server-version', 'no_version_set')
        random.seed(len(self.playToken) * integer)
        versionReplace = random.randrange(0, 10)
        version.replace(".", str(versionReplace))
        random.seed(len(self.playToken) * integer + integer)
        versions = random.randrange(3, 11)
        key = keyPrefix[::-1] + version[::-1] + version + str(self.air.hashVal) + FIXED_KEY
        for x in range(versions):
            key += version
        key = hashlib.sha384(key.encode('utf-8')).hexdigest().encode('utf-8')
        computedSignature = hmac.new(key, self.playToken.encode('utf-8'), hashlib.sha512).digest()

        # If the signature generated by the server does not match the one by the client, kick them out
        if signature != computedSignature:
            self.killConnection(connectionId=self.sender, reason=OTPLocalizer.RejectPlayCookie)
            return

        if joinSecret != b'' and joinSecret != self.air.serverJoinSecret:
            # Execute connections that try to fake a join secret
            self.killConnection(connectionId=self.sender, reason=OTPLocalizer.RejectJoinSecret)
            return

        self.accountDb.lookup(playToken, self.__loginResult)

    def __setIpAddress(self, remoteIp, remotePort, localIp, localPort):
        self.ip = remoteIp

    def __loginResult(self, result):
        # Open up our ban file and gather all the info related to our bans.
        bans = simbase.air.banManager.openBanFile()
        if isinstance(bans, list):
            self.killConnection(connectionId=self.sender, reason='', code=OTPGlobals.BootedOldVersion)
            self.notify.warning('The game was found to be installed alongside an old version of Toontown Realms!')
            return

        banInfo = list(bans.values())
        for info in banInfo:
            if isinstance(info, list):
                self.killConnection(connectionId=self.sender, reason='', code=OTPGlobals.BootedOldVersion)
                self.notify.warning('The game was found to be installed alongside an old version of Toontown Realms!')
                return

        accountIds = list(bans.keys())
        hardwareIds = []
        universalIds = []
        ipAddresses = []

        for accountId in accountIds:
            banInfo = bans.get(accountId)

            # The the ban time has expired, ignore this entry
            now = datetime.now()
            expire = banInfo.get('expire', 0)
            # If their expire time is 0, that means they are perma-banned
            if not isinstance(expire, int) and not expire == 0:
                expire = datetime.strptime(expire, "%Y-%m-%d %H:%M:%S.%f")
                if expire < now:
                    accountIds.remove(accountId)
                    continue

            hardwareId = banInfo.get('hwId')
            hardwareIds.append(hardwareId)
            universalId = banInfo.get('uuid')
            universalIds.append(universalId)
            ipAddress = banInfo.get('ip')
            ipAddresses.append(ipAddress)

        accId = str(result.get('accountId'))
        hwId = self.hwId.decode('utf-8')
        reason = 'Not specified.'

        # Load Ban Manager settings

        # If this account is banned, kick them out!
        if accId in accountIds:
            reason = bans[accId]['reason']
            self.killConnection(connectionId=self.sender, reason=reason, code=OTPGlobals.BootedBanned)
            self.notify.warning('User with playtoken {} was kicked out for logging into a banned account.'.format(self.playToken.encode('utf-8')))
            return

        # If the connecting user's HWID is banned, kick them out!
        if ServerSettings.BanHardwareIDs.get():
            hwId = hwId.encode('utf-8')
            if hwId in hardwareIds:
                self.killConnection(connectionId=self.sender, reason=reason, code=OTPGlobals.BootedBanned)
                self.notify.warning('User with playtoken {} was kicked out for logging in with a banned Hardware ID.'.format(self.playToken.encode('utf-8')))
                return

        # If the connecting user's UUID is banned, kick them out!
        if ServerSettings.BanUUIDs.get():
            universalIdentifier = self.uuid.decode('utf-8')
            universalIdentifier = hashlib.sha512(universalIdentifier.encode('utf-8')).hexdigest()

            self.notify.warning('User with playtoken {} has UUID of {}.'.format(self.playToken.encode('utf-8'), universalIdentifier))
            self.notify.warning('Fallback vs UUID: {} vs {}'.format(self.uuid.decode('utf-8'), OTPGlobals.UUID_FALLBACK))

            if universalIdentifier in universalIds and (self.uuid.decode('utf-8') != OTPGlobals.UUID_FALLBACK):
                self.killConnection(connectionId=self.sender, reason=reason, code=OTPGlobals.BootedBanned)
                self.notify.warning('User with playtoken {} was kicked out for logging in with a banned UUID.'.format(self.playToken.encode('utf-8')))
                return

        # If the connecting user's IP Address is banned, kick them out!
        if self.ip and ServerSettings.BanIPAddresses.get():
            if self.ip in ipAddresses:
                self.killConnection(connectionId=self.sender, reason=reason, code=OTPGlobals.BootedBanned)
                self.notify.warning('User with playtoken {} was kicked out for logging in with a banned IP Address.'.format(self.playToken.encode('utf-8')))
                return

        # Get the access level of the user.
        accessLevel = result.get('accessLevel', 'NO_ACCESS')

        # Get the hardware ID of the realm hoster.
        hwId = hex(uuid.getnode())

        # Check if this server is in Offline Mode or Mini-Server mode. Kick them out if they aren't the realm hoster, and it's the former.
        if self.getGamemode() == OTPGlobals.ModeOffline and self.hwId.decode('utf-8') != hwId and not __debug__:
            self.killConnection(connectionId=self.sender, reason='', code=OTPGlobals.BootedOfflineMode)
            return

        # Check if the username is on the whitelist.
        # Accounts with MODERATOR access or higher will automatically bypass this check.
        # This is so that accounts made before a whitelist was enabled can easily log in without the owner having to whitelist all their mods.
        accessLevel = OTPGlobals.AccessLevelName2Int.get(accessLevel)
        builderAccess = OTPGlobals.AccessLevelName2Int.get('BUILDER')
        if accessLevel <= builderAccess:
            if ServerSettings.WhitelistedUsers.get():
                if self.playToken not in ServerSettings.WhitelistedUsers.get():
                    self.killConnection(connectionId=self.sender, reason=ServerSettings.NotWhitelistedMessage.get())
                    return

        # If this server has a minimum Access Level required for entry, boot them out.
        if ServerSettings.MinimumAccessLevel.get():
            minimumAccessLevel = ServerSettings.MinimumAccessLevel.get()
            if minimumAccessLevel:
                minimumAccessLevel = OTPGlobals.AccessLevelName2Int.get(minimumAccessLevel)
                if accessLevel < minimumAccessLevel:
                    reason = OTPLocalizer.CRDefaultAccessLevel % (minimumAccessLevel, accessLevel)
                    self.killConnection(connectionId=self.sender, reason=reason)
                    return

        # If this server has a password, present the password screen.
        if ServerSettings.ServerPassword.get():
            self.sendUpdateToChannel(self.sender, 'showPasswordScreen', [])
            return

        # Run the login operation.
        self.connection2fsm[self.sender] = LoginOperation(self, self.sender)
        self.connection2fsm[self.sender].request('Start', self.playToken)

    def killConnection(self, connectionId, reason, code=OTPGlobals.BootedConnectionKilled):
        # Sends CLIENTAGENT_EJECT to the given connectionId with the given reason.
        datagram = PyDatagram()
        datagram.addServerHeader(connectionId, self.air.ourChannel, CLIENTAGENT_EJECT)
        datagram.addUint16(code)
        datagram.addString(reason)
        self.air.send(datagram)

    def killConnectionFSM(self, connectionId):
        # Kills the connection for duplicate FSMs.
        fsm = self.connection2fsm.get(connectionId)
        if not fsm:
            self.notify.warning('Tried to kill connection %s for duplicate FSMs, but none exist!' % connectionId)
            return

        self.killConnection(connectionId, 'An operation is already running: %s' % fsm.name)

    def killAccount(self, accountId, reason):
        # Kills the account's connection given an accountId & a reason.
        self.killConnection(self.GetAccountConnectionChannel(accountId), reason=reason)

    def killAccountFSM(self, accountId):
        # Kills the account for duplicate FSMs.
        fsm = self.account2fsm.get(accountId)
        if not fsm:
            self.notify.warning('Tried to kill account %s for duplicate FSMs, but none exist!' % accountId)
            return

        self.killAccount(accountId, 'An operation is already running: %s' % fsm.name)

    def runOperation(self, operationType, *args):
        # Runs an operation on the sender. First, get the sender.
        sender = self.air.getAccountIdFromSender()

        if not sender:
            # If the sender doesn't exist, they're not
            # logged in, so kill the connection.
            self.killAccount(sender, 'Client is not logged in.')

        if sender in self.account2fsm:
            # This account is already currently running an operation. Kill this connection.
            self.killAccountFSM(sender)
            return

        self.account2fsm[sender] = operationType(self, sender)
        self.account2fsm[sender].request('Start', *args)
        if sender not in self.recentAccounts:
            self.recentAccounts.append(sender)

    def requestAvatarList(self):
        # An account is requesting their avatar list;
        # let's run a GetAvatarsOperation.
        self.runOperation(GetAvatarsOperation)

    def requestRemoveAvatar(self, avId):
        # Someone is requesting to have an avatar removed; run a RemoveAvatarOperation.
        self.runOperation(RemoveAvatarOperation, avId)

    def requestPlayAvatar(self, avId, hwId, uuid):
        # Someone is requesting to play on an avatar.
        # First, let's get the senders avId & accId.
        currentAvId = self.air.getAvatarIdFromSender()
        accountId = self.air.getAccountIdFromSender()
        if currentAvId and avId:
            # An avatar has already been chosen! Kill the account.
            self.killAccount(accountId, 'An avatar is already chosen!')
            return
        elif not currentAvId and not avId:
            # The client is likely making sure that none of its
            # avatars are active, so this isn't really an error.
            return

        if avId:
            # If the avId is not a NoneType, that means the client wants
            # to load an avatar; run a LoadAvatarOperation.
            self.runOperation(LoadAvatarOperation, avId, hwId, uuid, self.ip)
        else:
            # Otherwise, the client wants to unload the avatar; run an UnloadAvatarOperation.
            self.runOperation(UnloadAvatarOperation, currentAvId)

    def authenticatePassword(self, playToken, password, hwId):
        sender = self.air.getMsgSender()

        if password == ServerSettings.ServerPassword.get():
            self.sendUpdateToChannel(sender, 'authenticatePasswordResponse', [True])
            self.connection2fsm[sender] = LoginOperation(self, sender)
            self.connection2fsm[sender].request('Start', playToken)
        else:
            self.sendUpdateToChannel(sender, 'authenticatePasswordResponse', [False])

    def requestChangeGamemode(self):
        sender = self.air.getMsgSender()
        accountId = self.air.getAccountIdFromSender()

        gamemode = self.getGamemode()
        if gamemode == OTPGlobals.ModeOffline:
            newMode = OTPGlobals.ModeServer
        elif gamemode == OTPGlobals.ModeServer:
            newMode = OTPGlobals.ModeOffline
        self.setGamemode(newMode)
        if self.getGamemode() == OTPGlobals.ModeOffline:
            accounts = self.recentAccounts[:]
            accounts.remove(accountId)
            for account in accounts:
                connection = self.GetAccountConnectionChannel(account)
                self.killConnection(connectionId=connection, reason='', code=OTPGlobals.BootedOfflineModeChange)
            self.recentAccounts = [accountId]

        self.sendUpdateToChannel(sender, 'gamemodeSuccessCallback', [])

    def setGamemode(self, gamemode):
        self.gamemode = gamemode
        self.air.netMessenger.send('SetGamemode')

    def getGamemode(self):
        return self.gamemode
