from direct.directnotify import DirectNotifyGlobal

from otp.avatar import Avatar

from toontown.toonbase import ToontownGlobals, ClientSettings


class StreetProp(Avatar.Avatar):
    notify = DirectNotifyGlobal.directNotify.newCategory('StreetProp')

    def __init__(self, type):
        Avatar.Avatar.__init__(self)
        self.initializeDropShadow()
        models = list(ToontownGlobals.StreetProps2Anim.keys())
        model = models[type]
        self.loadModel(model)
        collisions = self.findAllMatches('**/+CollisionNode')
        if collisions:
            for coll in collisions:
                coll.stash()
        self.loadAnims({'neutral': ToontownGlobals.StreetProps2Anim.get(model)})
        self.setBlend(frameBlend=ClientSettings.SmoothAnimations.get())
        return

    def getShadowJoint(self):
        return self.getGeomNode()
