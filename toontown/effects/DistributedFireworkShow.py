from direct.distributed import DistributedObject
from toontown.effects.FireworkShowMixin import FireworkShowMixin

class DistributedFireworkShow(DistributedObject.DistributedObject, FireworkShowMixin):
    notify = directNotify.newCategory('DistributedFireworkShow')

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        FireworkShowMixin.__init__(self)

    def generate(self):
        DistributedObject.DistributedObject.generate(self)

    def disable(self):
        DistributedObject.DistributedObject.disable(self)
        FireworkShowMixin.disable(self)

    def delete(self):
        DistributedObject.DistributedObject.delete(self)

    def d_requestFirework(self, x, y, z, style, color1, color2):
        self.sendUpdate('requestFirework', (x,
         y,
         z,
         style,
         color1,
         color2))

    def startShow(self, eventId, style, timestamp, root = render):
        if self.getSky().getParent() == hidden:
            self.acceptOnce('resumeFireworks', self.runShow, [eventId, style, timestamp, root])
        else:
            self.runShow(eventId, style, timestamp, root)
