from direct.directnotify.DirectNotifyGlobal import directNotify
from .DistributedMicroGame import DistributedMicroGame


class DistributedPieBlitz(DistributedMicroGame):
    notify = directNotify.newCategory('DistributedPieBlitz')

    def __init__(self, cr):
        DistributedMicroGame.__init__(self, cr)
        base.cr.pieBlitzGame = self

    def delete(self):
        del base.cr.pieBlitzGame
        DistributedMicroGame.delete(self)
