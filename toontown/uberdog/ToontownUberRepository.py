import time

from direct.directnotify import DirectNotifyGlobal

from otp.distributed.DistributedDirectoryAI import DistributedDirectoryAI
from otp.distributed.OtpDoGlobals import *
from toontown.distributed.ToontownInternalRepository import ToontownInternalRepository
from toontown.parties.ToontownTimeManager import ToontownTimeManager
from toontown.time.TimeUtil import EpochTime

import string
import random

from toontown.toonbase import ServerSettings


class ToontownUberRepository(ToontownInternalRepository):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownUberRepository')

    def __init__(self, baseChannel, serverId):
        ToontownInternalRepository.__init__(self, baseChannel, serverId, dcSuffix='UD')
        self.gameServicesManager = None
        self.ttrmSocialManager = None
        self.deliveryManager = None
        self.partyManager = None
        self.toontownTimeManager = None
        self.banManager = None
        self.moddingManager = None
        self.time = None
        # discord stuff
        self.serverJoinSecret = ""

    def handleConnected(self):
        ToontownInternalRepository.handleConnected(self)

        # Create our root object.
        self.notify.info('Creating root object (%d)...' % self.getGameDoId())
        rootObj = DistributedDirectoryAI(self)
        rootObj.generateWithRequiredAndId(self.getGameDoId(), 0, 0)

        # Create our local objects.
        self.notify.info('Creating local objects...')
        self.createLocals()

        # Create our global objects.
        self.notify.info('Creating global objects...')
        self.createGlobals()

        self.notify.info('Done.')
        self.netMessenger.send('UdOnline')

    def createLocals(self):
        # Create our Toontown time manager...
        self.toontownTimeManager = ToontownTimeManager(serverTimeUponLogin=int(time.time()),
                                                       globalClockRealTimeUponLogin=globalClock.getRealTime())
        self.time = EpochTime()  # simplifies datetime/epoch timestamp things
        # discord stuff; not necessarily a 'local' thing per se, but might as well treat it like one
        tmp = string.ascii_lowercase + string.ascii_uppercase + string.digits
        for _ in range(64):
            # so people don't try to "guess" their way into a server
            self.serverJoinSecret += random.choice(tmp)

    def createGlobals(self):
        self.gameServicesManager = self.generateGlobalObject(OTP_DO_ID_TOONTOWN_GAME_SERVICES_MANAGER,
                                                             'TTGameServicesManager')
        self.ttrmSocialManager = self.generateGlobalObject(OTP_DO_ID_TTRM_SOCIAL_MANAGER, 'TTRMSocialManager')
        self.deliveryManager = self.generateGlobalObject(OTP_DO_ID_TOONTOWN_DELIVERY_MANAGER,
                                                         'DistributedDeliveryManager')
        self.partyManager = self.generateGlobalObject(OTP_DO_ID_TOONTOWN_PARTY_MANAGER, 'DistributedPartyManager')
        self.banManager = self.generateGlobalObject(OTP_DO_ID_BAN_MANAGER, 'BanManager')
        self.moddingManager = self.generateGlobalObject(OTP_DO_ID_MODDING_MANAGER, 'ModdingManager')
