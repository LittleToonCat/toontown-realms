from .AIBase import *
globals()['__builtins__']['simbase'] = AIBase()
globals()['__builtins__']['ostream'] = Notify.out()
globals()['__builtins__']['run'] = simbase.run
globals()['__builtins__']['taskMgr'] = simbase.taskMgr
globals()['__builtins__']['jobMgr'] = simbase.jobMgr
globals()['__builtins__']['eventMgr'] = simbase.eventMgr
globals()['__builtins__']['messenger'] = simbase.messenger
globals()['__builtins__']['bboard'] = simbase.bboard
globals()['__builtins__']['config'] = simbase.config
globals()['__builtins__']['directNotify'] = directNotify
from direct.showbase import Loader
simbase.loader = Loader.Loader(simbase)
globals()['__builtins__']['loader'] = simbase.loader
directNotify.setDconfigLevels()

def inspect(anObject):
    from direct.tkpanels import Inspector
    Inspector.inspect(anObject)


globals()['__builtins__']['inspect'] = inspect
if not __debug__ and __dev__:
    notify = directNotify.newCategory('ShowBaseGlobal')
    notify.error("You must set 'want-dev' to false in non-debug mode.")
taskMgr.finalInit()

# The VirtualFileSystem, which has already initialized, doesn't see the mount
# directives in the config(s) yet. We have to force it to load those manually:
vfs = VirtualFileSystem.getGlobalPtr()
mounts = ConfigVariableList('vfs-mount')
for mount in mounts:
    mountFile, mountPoint = (mount.split(' ', 2) + [None, None, None])[:2]
    vfs.mount(Filename(mountFile), Filename(mountPoint), 0)
