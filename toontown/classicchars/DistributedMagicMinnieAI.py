from direct.directnotify import DirectNotifyGlobal
from toontown.classicchars.DistributedMinnieAI import DistributedMinnieAI

class DistributedMagicMinnieAI(DistributedMinnieAI):
    notify = DirectNotifyGlobal.directNotify.newCategory("DistributedMagicMinnieAI")

