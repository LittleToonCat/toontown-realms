from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObjectGlobal
from direct.task.Task import Task

from otp.otpbase.OTPGlobals import ModeServer
from toontown.hood import ZoneUtil
from toontown.toonbase import ToontownGlobals, TTLocalizer, ClientSettings

if config.GetBool('want-discord-rpc', True):
    from direct import discord_rpc
from direct.discord_rpc.util.utils import get_executable_directory
import time
from os import path
from toontown.toontowngui.DiscordJoinDialog import DiscordJoinDialog


discordToken = '1297708552500154401'


class _Notifier(object):
    notify = None

    def __init__(self, notify_name):
        if notify_name is not None and len(notify_name) > 0:
            self.notify = DirectNotifyGlobal.directNotify.newCategory(notify_name)

    def info(self, *args):
        if self.notify is not None:
            self.notify.info(*args)

    def warning(self, *args):
        if self.notify is not None:
            self.notify.warning(*args)

    def debug(self, *args):
        if self.notify is not None:
            self.notify.debug(*args)

    def error(self, *args):
        if self.notify is not None:
            self.notify.error(*args)


class DiscordManager(DistributedObjectGlobal.DistributedObjectGlobal):
    notify = DirectNotifyGlobal.directNotify.newCategory('DiscordManager')
    notify.setDebug(True)
    neverDisable = 1

    def __init__(self, cr):
        DistributedObjectGlobal.DistributedObjectGlobal.__init__(self, cr)

        cr.discordManager = self

        if ClientSettings.DiscordRPC.get():
            self.discordRpc = discord_rpc
        else:
            self.discordRpc = None

        self.state = TTLocalizer.DiscordOffline             # Offline mode or Mini-Server IP
        self.details = TTLocalizer.DiscordPickAToon         # What you are doing
        self.largeImage = ToontownGlobals.DefaultIcon       # Zone Image
        self.largeImageText = TTLocalizer.DiscordPickAToon  # Zone Name
        self.partyId = '69'                                 # An ID specific to the Mini-Server
        self.districtAvatarCount = None                     # Current Toon count in the Mini-Server
        self.districtLimit = None                           # Max Toon count in the Mini-Server
        self.joinSecret = None                              # An ID specific to joining a Toon's current session
        self.requestingUsers = dict()                       # Users requesting to join the server we're on
        self.__rateLimit = None                             # Discord Avatar HTTP API rate limit
        self.__joinFrame = DiscordJoinDialog()              # The Join Request frame that'll show up when users request
                                                            # to join
        self.__drpcNotify = _Notifier('DiscordRichPresence')    # The notify class for the rich presence library
        self.__cacheDir = path.join(get_executable_directory(), "cache")

        self.start = time.time()
        if self.discordRpc:
            self.launchPresence()

    def readyCallback(self, current_user):
        self.notify.info('Our user: {}'.format(current_user))
        self.downloadAvatarImage(current_user['id'], current_user['discriminator'], current_user['avatar'])
        self.__joinFrame.setIcon(current_user['id'], current_user['username'], current_user['discriminator'],
                                 self.getAvatarImagePath(current_user['id'], current_user['discriminator'],
                                                         current_user['avatar']))

    def disconnectedCallback(self, codeno, codemsg):
        self.notify.warning('Disconnected from Discord rich presence RPC. Code {}: {}'.format(
            codeno, codemsg
        ))

    def joinCallback(self, joinSecret):
        # This is for us to join another game
        # TODO: make this allow us to join different games while playing, when user isn't busy with things (ex: CEO)
        self.notify.debug("go hypsinigrad yourself " + joinSecret)

    def joinRequestCallback(self, users):
        # This is for other users to join our game
        expire = time.time() + 25
        for user in users:
            self.requestingUsers[user['id']] = {'username': user['username'],
                                                'discriminator': user['discriminator'],
                                                'avatar': user['avatar'],
                                                'expire': expire}
            # remove user request after 25 seconds
            taskMgr.doMethodLater(expire - time.time(), self.respond, 'discord-respond-{}'.format(user['id']),
                                  extraArgs=[user['id'], self.discordRpc.DISCORD_REPLY_IGNORE, False])
            self.downloadAvatarImage(user['id'], user['discriminator'], user['avatar'])
        self.notify.info('Join request users: {}'.format(self.requestingUsers))
        self.nextUserRequest()

    def errorCallback(self, errno, errmsg):
        self.notify.warning('An error occurred! Error {}: {}'.format(
            errno, errmsg
        ))

    def launchPresence(self):
        callbacks = {
            'ready': self.readyCallback,
            'disconnected': self.disconnectedCallback,
            'joinGame': self.joinCallback,
            'spectateGame': None,
            'joinRequest': self.joinRequestCallback,
            'error': self.errorCallback,
        }
        if self.discordRpc:
            self.discordRpc.initialize(discordToken, callbacks=callbacks, log=True, logger=self.__drpcNotify,
                                       pipe_no=0)

            self.updatePresence()
            updateTask = Task.loop(Task(self.updateConnection), Task.pause(1.0), Task(self.runCallbacks))
            taskMgr.add(updateTask, 'update-presence-task')

    def updateConnection(self, task):
        if self.discordRpc:
            self.discordRpc.update_connection()
        return Task.done

    def runCallbacks(self, task):
        if self.discordRpc:
            self.discordRpc.run_callbacks()
        return Task.done

    def updatePresence(self):
        if self.discordRpc:
            presenceInfo = {
                'state': self.state,
                'details': self.details,
                'start_timestamp': self.start,
                'large_image_key': self.largeImage,
                'large_image_text': self.largeImageText,
                'party_id': self.partyId,
                'party_size': self.districtAvatarCount,
                'party_max': self.districtLimit,
                # don't set a join secret if we are in offline mode
                'join_secret': self.joinSecret if self.state != TTLocalizer.DiscordOffline else None
            }
            self.discordRpc.update_presence(**presenceInfo)

    def shutdownPresence(self):
        taskMgr.remove('update-presence-task')
        if self.discordRpc:
            self.discordRpc.shutdown()

    def setInfo(self, state=None, details=None, largeImage=None, largeImageText=None, smallImage=None,
                smallImageText=None, zoneId=None, joinSecret=None):
        if not details and zoneId:
            details = self.getDetailsByZoneId(zoneId)
        if not largeImageText and zoneId:
            largeImageText = self.getLargeImageTextByZoneId(zoneId)

        self.state = state
        self.details = details
        self.largeImage = largeImage
        self.largeImageText = largeImageText

        self.updatePresence()

    def setState(self, state):
        self.state = state
        self.updatePresence()

    def getState(self):
        if base.cr.getGamemode() == ModeServer:
            self.state = base.cr.serverName
            districtAvatarCount = self.getDistrictAvatarCount()
            if not hasattr(base, 'localAvatar'):
                districtAvatarCount += 1
            self.setDistrictAvatarCount(districtAvatarCount)
        else:
            self.state = TTLocalizer.DiscordOffline
            self.setDistrictAvatarCount(None)

        return self.state

    def setDetails(self, details):
        self.details = details
        self.updatePresence()

    def getDetailsByZoneId(self, zoneId):
        if zoneId in list(TTLocalizer.GlobalStreetNames.keys()):
            return TTLocalizer.GlobalStreetNames[zoneId][2]
        elif zoneId in list(TTLocalizer.zone2TitleDict.keys()):
            return TTLocalizer.zone2TitleDict[zoneId][0]

    def setLargeImage(self, largeImage):
        self.largeImage = largeImage
        self.updatePresence()

    def setLargeImageText(self, largeImageText):
        self.largeImageText = largeImageText
        self.updatePresence()

    def getLargeImageTextByZoneId(self, zoneId):
        # For welcome valley support
        zoneId = ZoneUtil.getCanonicalHoodId(zoneId)

        if zoneId in list(ToontownGlobals.hoodNameMap.keys()):
            return ToontownGlobals.hoodNameMap[zoneId][2]
        elif zoneId in list(TTLocalizer.zone2TitleDict.keys()):
            return TTLocalizer.zone2TitleDict[zoneId][0]
        elif not ZoneUtil.isDynamicZone(zoneId):
            return TTLocalizer.GlobalStreetNames[zoneId][2]

        return None

    def getAvId(self):
        return str(base.localAvatar.getDoId())

    def setDistrictLimit(self, districtLimit):
        self.districtLimit = districtLimit
        self.updatePresence()

    def getDistrictLimit(self):
        return self.districtLimit

    def setDistrictId(self, districtId):
        self.districtId = districtId
        self.updatePresence()

    def setDistrictAvatarCount(self, districtAvatarCount):
        self.districtAvatarCount = districtAvatarCount
        self.updatePresence()

    def getDistrictAvatarCount(self):
        return len(base.cr.onlineAvatars)

    def setPartyId(self, partyId):
        ipAddr = bboard.get('game-server', '127.0.0.1')
        self.notify.debug("Party ID: {}, join secret: {}, IP Addr: {}".format(partyId, bboard.get('discord-join-secret',
                                                                                                  '69-420'), ipAddr))
        self.partyId = partyId
        # we prepend the IP Address so the launcher knows where to connect
        self.joinSecret = bytes(ipAddr, 'utf-8') + b"&" + bboard.get('discord-join-secret', '69-420')
        self.updatePresence()

    def downloadAvatarImage(self, userId, discriminator, hash=None):
        if not config.GetBool('want-discord-avatars', False):
            return
        if base.certLocation is None:
            self.notify.debug('Phase_3 cacert.pem not ready yet.')
            return

        self.discordRpc.download_profile_picture(userId, discriminator, hash, cache_dir=self.__cacheDir,
                                                 game_name="ToontownOffline", game_url="https://toontownrealms.com",
                                                 game_version="1.0.0", cert_file=base.certLocation)

    def getAvatarImagePath(self, userId, discriminator, hash=None):
        if hash:
            avatarPath = path.join(self.__cacheDir, userId, hash) + '.png'
        else:
            avatarPath = path.join(self.__cacheDir, "default", str(int(discriminator) % 5)) + '.png'
        self.notify.debug("Discord User ID {}: calculated cached image path: {}".format(userId, avatarPath))
        if path.exists(avatarPath):
            self.notify.debug("Discord User ID {}: cached image exists.".format(userId))
            return avatarPath
        self.notify.debug("Discord User ID {}: cached image doesn't exist.".format(userId))
        return None

    def respond(self, userId, response, nextRequest=True):
        taskMgr.remove('discord-respond-{}'.format(userId))
        if userId in self.requestingUsers:
            del self.requestingUsers[userId]
            self.discordRpc.respond(userId, response)
        if nextRequest:
            self.nextUserRequest()
        else:
            if len(self.requestingUsers) == 0:
                self.__joinFrame.hide()

    def nextUserRequest(self):
        userId = None
        while userId is None:
            if len(self.requestingUsers) == 0:
                self.__joinFrame.hide()
                break
            userId = list(self.requestingUsers)[0]
            if self.requestingUsers[userId]['expire'] < time.time():
                self.respond(userId, self.discordRpc.DISCORD_REPLY_IGNORE, nextRequest=False)
                userId = None
        if userId:
            user = self.requestingUsers[userId]
            self.__joinFrame.setIcon(userId=userId, username=user['username'], discrim=user['discriminator'],
                                     iconFile=self.getAvatarImagePath(userId, user['discriminator'], user['avatar']))
            self.__joinFrame.show()
            self.notify.debug('Asking our user if they wish for {}#{} to join'.format(user['username'],
                                                                                      user['discriminator']))
        else:
            self.notify.debug('No users asking to join.')
