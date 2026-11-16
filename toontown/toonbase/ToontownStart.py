import sys

from panda3d.core import *

if __debug__:
    if len(sys.argv) == 2 and sys.argv[1] == '--dummy':
        loadPrcFile('config/general.prc')
        loadPrcFile('config/dev.prc')

        # The VirtualFileSystem, which has already initialized, doesn't see the mount
        # directives in the config(s) yet. We have to force it to load those manually:
        vfs = VirtualFileSystem.getGlobalPtr()
        mounts = ConfigVariableList('vfs-mount')
        for mount in mounts:
            mountFile, mountPoint = (mount.split(' ', 2) + [None, None, None])[:2]
            vfs.mount(Filename(mountFile), Filename(mountPoint), 0)

import builtins


class game:
    name = 'toontown'
    process = 'client'


builtins.game = game()
import builtins

try:
    launcher
except:
    from toontown.launcher.ToontownOfflineDummyLauncher import ToontownOfflineDummyLauncher

    launcher = ToontownOfflineDummyLauncher()
    builtins.launcher = launcher

launcher.setRegistry('EXIT_PAGE', 'normal')

print('ToontownStart: Starting the game.')
if launcher.isDummy():
    http = HTTPClient()
else:
    http = launcher.http
tempLoader = Loader()
from direct.gui import DirectGuiGlobals

print('ToontownStart: setting default font')

from toontown.toonbase.ClientSettings import *
print('ToontownStart: loading ClientSettings')

from toontown.toonbase.HotkeySettings import *
print('ToontownStart: loading HotkeySettings')
from . import ToontownGlobals

DirectGuiGlobals.setDefaultFontFunc(ToontownGlobals.getInterfaceFont)
launcher.setPandaErrorCode(7)
from . import ToonBase


print('ToontownStart: initializing ToonBase')
ToonBase.ToonBase()
if base.win == None:
    print('Unable to open window; aborting.')
    sys.exit()
launcher.setPandaErrorCode(0)

launcher.setPandaWindowOpen()

from . import TTLocalizer
loader.beginBulkLoad('init', TTLocalizer.LoaderLabel, 138, 0, TTLocalizer.TIP_NONE)
ConfigVariableDouble('decompressor-step-time').setValue(0.01)
ConfigVariableDouble('extractor-step-time').setValue(0.01)

DirectGuiGlobals.setDefaultRolloverSound(base.loader.loadSfx('phase_3/audio/sfx/GUI_rollover.ogg', manager = 'gui'))

DirectGuiGlobals.setDefaultClickSound(base.loader.loadSfx('phase_3/audio/sfx/GUI_create_toon_fwd.ogg', manager = 'gui'))

DirectGuiGlobals.setDefaultDialogGeom(base.loader.loadModel('phase_3/models/gui/dialog_box_gui'))

from otp.otpbase import OTPGlobals

OTPGlobals.setDefaultProductPrefix(TTLocalizer.ProductPrefix)

serverVersion = base.config.GetString('server-version', 'no_version_set')
print('ToontownStart: serverVersion: ', serverVersion)

print("ToontownStart: initializing CR")
from toontown.distributed import ToontownClientRepository
loader.tick()

cr = ToontownClientRepository.ToontownClientRepository(serverVersion, launcher)
loader.tick()
base.initNametagGlobals()
loader.tick()
base.cr = cr
loader.endBulkLoad('init')
from otp.distributed.OtpDoGlobals import *

cr.generateGlobalObject(OTP_DO_ID_FRIEND_MANAGER, 'FriendManager')

base.startShow(cr)


del tempLoader
base.loader = base.loader
builtins.loader = base.loader

# put _strptime in builtins, because Pypperoni apparently can't do this on their own.
import _strptime

builtins._strptime = _strptime

try:
    base.run()
except (SystemExit, KeyboardInterrupt):
    if hasattr(builtins, 'localServer') and localServer:
        localServer.killProcesses()
    raise
except:
    if hasattr(builtins, 'localServer') and localServer:
        localServer.killProcesses()
    import traceback

    traceback.print_exc()
    sys.exit(1)
