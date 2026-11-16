from panda3d.core import *
from otp.otpbase import PythonUtil
import builtins

if __debug__:
    uberDogConfigs = ["config/general.prc", "config/dev.prc"]
    for prc in uberDogConfigs:
        loadPrcFile(prc)

class game:
    name = 'uberDog'
    process = 'server'


builtins.game = game

from otp.ai.AIBaseGlobal import *

from toontown.uberdog.ToontownUberRepository import ToontownUberRepository

simbase.air = ToontownUberRepository(1000000, 4002)
host = '127.0.0.1:7199'
port = 7199
if ':' in host:
    host, port = host.split(':', 1)
    port = int(port)

simbase.air.setEventLogHost(host, 7197)

simbase.air.connect(host, port)

try:
    run()
except SystemExit:
    raise
except Exception:
    if not __debug__:
        from __pypperoni__ import describeException
        info = describeException()
    else:
        info = PythonUtil.describeException()
    simbase.air.writeServerEvent('uberdog-exception', avId=simbase.air.getAvatarIdFromSender(),
                                 accId=simbase.air.getAccountIdFromSender(), info=info)
    raise
