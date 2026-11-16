from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFileData

from toontown.server.DedicatedServer import DedicatedServer
import sys

loadPrcFileData('dedicated server config', '''
    window-type none
    audio-library-name null
    default-directnotify-level warning
''') # temporary set notify to warning (should be info) hopefully stop spam of console with miniserver api

if __debug__:
    if '--test' in sys.argv:
        loadPrcFileData('test server config', 'astron-config-path astron/config/astrond_test.yml')


ShowBase()

dedicatedServer = DedicatedServer(isLocal=False)
try:
    dedicatedServer.start()
    base.run()
except (SystemExit, KeyboardInterrupt):
    print('SystemExit')
    # these should be 'normal' exits, just kill things
    dedicatedServer.killProcesses()
    sys.exit(0)
except Exception:
    # print error here as well?
    import traceback
    traceback.print_exc()
    dedicatedServer.killProcesses()
    sys.exit(1)
