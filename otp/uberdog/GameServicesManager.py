from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectGlobal import DistributedObjectGlobal

from otp.distributed.PotentialAvatar import PotentialAvatar
from otp.otpbase import OTPGlobals

import hashlib, hmac, json, uuid, random, subprocess, sys, os

FIXED_KEY = "My dark harvest awaits for the scum of society; repent now or I'll come a-knocking"


class GameServicesManager(DistributedObjectGlobal):
    notify = DirectNotifyGlobal.directNotify.newCategory('GameServicesManager')

    def __init__(self, cr):
        DistributedObjectGlobal.__init__(self, cr)
        self.doneEvent = None
        self._callback = None
        self.hwId = None
        self.uuid = None
        self.password = False

    def login(self, doneEvent):
        self.doneEvent = doneEvent

        # Our user's playtoken, aka username
        playToken = self.cr.playToken or 'dev'

        # Our user's hardware ID
        self.hwId = hex(uuid.getnode())

        # Let's check to make sure the hardware ID is legit.
        # This is probably a very, very shitty and hacky way of checking it, but whatever.
        # If it causes problems in the future we can always change it.
        # Right now, I just check to see if there is at least one integer in it.
        integer = None
        for letter in self.hwId:
            try:
                integer = int(letter)
            except:
                pass
            if integer:
                break

        if not integer:
            self.notify('Suspicious activity detected! Invalid Hardware ID being used! If you think this is invalid, please contact the Toontown Realms developers.')
            return

        # If our user in on Windows, we can get a unique identifier.
        # As for other platforms, let's figure those out later.
        # By the way, thanks Kingsisle for the inspiration!
        fallback = OTPGlobals.UUID_FALLBACK
        platform = sys.platform
        if platform == 'win32':
            try:
                self.uuid = str(subprocess.check_output('wmic csproduct get uuid').decode().split('\n')[1].strip())
                if not self.uuid:
                    self.uuid = fallback
            except Exception:
                self.uuid = fallback
        elif "linux" in platform:
            # it's not perfect, but it both doesn't require sudo privs
            # then again, you can't easily get a *good* unique UID on Linux anyways...
            try:
                mid_file = None
                if os.path.isfile("/etc/machine-id"):
                    mid_file = "/etc/machine-id"
                elif os.path.isfile("/var/lib/dbus/machine-id"):
                    mid_file = "/var/lib/dbus/machine-id"
                if mid_file is not None:
                    with open(mid_file, 'rb') as f:
                        output = f.read().strip().upper()
                        output.decode("utf-8")
                    self.uuid = f"{output[0:8]}-{output[8:12]}-{output[12:16]}-{output[16:20]}-{output[20:32]}"
                else:
                    self.uuid = fallback
            except Exception:
                self.uuid = fallback
        else:
            self.uuid = fallback

        # Here we generate a signature based off of a lot of randomness.
        # I think this is random enough? I'm not 100% sure honestly.

        # Key prefix as gotten from the prc file.
        keyPrefix = config.GetString('ttoff-words-of-wisdom', 'i-love-disyer')

        # Server version.
        version = self.cr.serverVersion

        # Seed random using the length of the user's playtoken multiplied by the first integer in their HWID.
        random.seed(len(playToken) * integer)

        # Get a random integer from 0 to 10.
        versionReplace = random.randrange(0, 10)

        # Replace every period in the version number with this random number.
        version.replace(".", str(versionReplace))

        # Seed random again, this time using the length of the user's playtoken multiplied by the first integer in their HWID plus the first integer in their HWID.
        random.seed(len(playToken) * integer + integer)

        # Get a random integer from 3 to 11.
        versions = random.randrange(3, 11)

        # Create a key with a bunch of randomness.
        key = keyPrefix[::-1] + version[::-1] + version + str(self.cr.hashVal) + FIXED_KEY
        for x in range(versions):
            key += version

        # Hash our key.
        key = hashlib.sha384(key.encode('utf-8')).hexdigest().encode('utf-8')

        # Create a signature with our key.
        signature = hmac.new(key, playToken.encode('utf-8'), hashlib.sha512).digest()

        # Finally, let's send the login update.
        self.d_login(playToken, self.hwId, self.uuid, signature, platform, self.cr.checkDiscordJoin())

    def d_login(self, playToken, hwId, uuid, sig, platform, joinSecret):
        self.sendUpdate('login', [playToken, hwId, uuid, sig, platform, joinSecret])

    def acceptLogin(self, joinSecret):
        # mainly for the users who login without joining via discord
        if bboard.get('discord-join-secret'):
            bboard.update('discord-join-secret', joinSecret)
        else:
            bboard.post('discord-join-secret', joinSecret)
        messenger.send(self.doneEvent, [{'mode': 'success'}])

    def requestAvatarList(self):
        self.sendUpdate('requestAvatarList')

    def avatarListResponse(self, avatarList):
        avList = []
        for avNum, avName, avDNA, avPosition, nameState, hat, glasses, backpack, shoes, lastZone, nametagStyle, nametagType, health, maxHealth in avatarList:
            nameOpen = int(nameState == 1)
            names = [avName, '', '', '']
            # Pending
            if nameState == 2:
                names[1] = avName
            # Approved
            elif nameState == 3:
                names[2] = avName
            # Rejected
            elif nameState == 4:
                names[3] = avName
            avList.append(
                PotentialAvatar(avNum,
                                names,
                                avDNA,
                                avPosition,
                                nameOpen,
                                hat,
                                glasses,
                                backpack,
                                shoes,
                                lastZone,
                                nametagStyle,
                                nametagType,
                                health,
                                maxHealth)
            )

        self.cr.handleAvatarsList(avList)

    def requestRemoveAvatar(self, avId):
        self.sendUpdate('requestRemoveAvatar', [avId])

    def requestPlayAvatar(self, avId):
        self.sendUpdate('requestPlayAvatar', [avId, self.hwId, self.uuid])

    def receiveAccountDays(self, accountDays):
        base.cr.accountDays = accountDays

    def showPasswordScreen(self):
        self.password = True
        messenger.send('showPasswordScreen', [])
        self.accept('authenticatePassword', self.authenticatePassword)

    def authenticatePassword(self, playToken, password):
        self.sendUpdate('authenticatePassword', [playToken, password, self.hwId])

    def authenticatePasswordResponse(self, state):
        messenger.send('authenticatePasswordResponse', [state])

    def requestChangeGamemode(self):
        self.sendUpdate('requestChangeGamemode', [])

    def gamemodeSuccessCallback(self):
        messenger.send('gamemodeSuccess')
