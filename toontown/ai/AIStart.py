from panda3d.core import *
from otp.otpbase import PythonUtil
import builtins

if __debug__:
    aiConfigs = ["config/general.prc", "config/dev.prc"]
    for prc in aiConfigs:
        loadPrcFile(prc)


class game:
    name = 'toontown'
    process = 'server'


builtins.game = game

from otp.ai.AIBaseGlobal import *

from toontown.ai.ToontownAIRepository import ToontownAIRepository

simbase.air = ToontownAIRepository(401000000,
                                   4002
                               )

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
    simbase.air.writeServerEvent('ai-exception', avId=simbase.air.getAvatarIdFromSender(),
                                 accId=simbase.air.getAccountIdFromSender(), exception=info)
    raise
