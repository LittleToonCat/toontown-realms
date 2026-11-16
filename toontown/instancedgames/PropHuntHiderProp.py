from panda3d.core import BitMask32, CollisionBox, CollisionNode, NodePath, Point3
from direct.interval.IntervalGlobal import *
from toontown.effects.DustCloud import DustCloud
from toontown.instancedgames import PropHuntGlobals
from toontown.sandbox import PropGlobals
from toontown.sandbox.PropGlobals import PropPool
from toontown.toonbase import ToontownGlobals

class PropHuntHiderProp(NodePath):

    def __init__(self, toon):
        NodePath.__init__(self, 'prop_hunt_prop')
        self.toon = toon
        self.doId = toon.doId
        self.collNodePath = None
        self.propModel = None
        self.reparentTo(toon)

    def destroyPropModel(self):
        self.destroyColl()
        if self.propModel:
            self.propModel.removeNode()
            self.propModel = None

    def destroyColl(self):
        if self.collNodePath:
            self.collNodePath.removeNode()
            self.collNodePath = None

    def handlePropCollisions(self):
        collisions = self.propModel.findAllMatches('**/+CollisionNode')

        if base.localAvatar.getDoId() == self.getDoId():
            collMask = BitMask32.allOff()
        else:
            collMask = (ToontownGlobals.WallBitmask | ToontownGlobals.PieBitmask)

        if collisions:
            for coll in collisions:
                coll.setCollideMask(collMask)
                coll.setTag('hiderDoId', str(self.getDoId()))
        else:
            # Some props don't have collisions, so gotta make one
            bMin, bMax = self.propModel.getTightBounds()
            collBox = CollisionBox(Point3(bMin), Point3(bMax))
            self.collNode = CollisionNode(f'disguisedProp-{self.getDoId()}')
            self.collNode.addSolid(collBox)
            self.collNode.setCollideMask(collMask)
            self.collNodePath = self.attachNewNode(self.collNode)
            self.collNodePath.setTag('hiderDoId', str(self.getDoId()))

    def getDustCloudIval(self, wantSound = 0, scale = 0.4):
        dustCloud = DustCloud(self.toon, fBillboard = 0, wantSound = wantSound)
        dustCloud.setBillboardAxis(2.0)
        dustCloud.setZ(3)
        dustCloud.setScale(scale)
        dustCloud.createTrack()
        cloudSeq = Sequence(
            Parallel(
                dustCloud.track,
                dustCloud.colorScaleInterval(0.5, (1, 1, 1, 0), blendType='easeInOut')
            ),
            Func(dustCloud.destroy),
            name='dustCloadIval'
        )
        return cloudSeq

    def transformProp(self, propName):
        # If we already were another prop, remove the prop.
        self.destroyPropModel()

        # Hide the Toon!
        toonGeom = self.toon.getGeomNode()
        toonGeom.hide()
        self.toon.hideNametag2d()
        self.toon.hideNametag3d()

        # Attach the Prop to the Toon
        self.propModel = PropPool.getProp(propName)
        self.propModel.setDepthTest(1)
        self.propModel.setDepthWrite(1)
        self.propModel.setPos(self.toon.getPos())
        self.propModel.setHpr(self.toon.getHpr())
        self.propModel.wrtReparentTo(self)

        self.handlePropCollisions()

        # Dust Cloud Interval
        dustCloudIval = self.getDustCloudIval(scale = self.propModel.getScale())
        dustCloudIval.start()

    def playDeathInterval(self, callback = None):
        # TODO: Add an exclamation point that jumps up above the prop
        self.destroyColl()

        sfx = loader.loadSfx('phase_5/audio/sfx/LB_receive_evidence.ogg')
        x, y, z = self.propModel.getPos()
        sX, sY, sZ = self.propModel.getScale()
        toonGeom = self.toon.getGeomNode()

        deathIval = Sequence(
            Parallel(
                SoundInterval(sfx, node=self.propModel, duration=0.3),
                Sequence(
                    self.propModel.posInterval(0.2, Point3(x, y, z + 1.25), blendType='easeInOut'),
                    self.propModel.posInterval(0.2, Point3(x, y, z), blendType='easeInOut')
                ),
                Sequence(
                    self.propModel.scaleInterval(0.2, (sX, sY, sZ + 0.7), blendType='easeIn'),
                    self.propModel.scaleInterval(0.2, (sX, sY, sZ - 0.4)),
                    self.propModel.scaleInterval(0.1, (sX, sY, sZ + 0.4)),
                    self.propModel.scaleInterval(0.1, (sX, sY, sZ))
                )
            ),
            Wait(0.5),
            Parallel(
                Func(self.destroyPropModel),
                Func(toonGeom.show),
                Func(self.toon.showNametag2d),
                Func(self.toon.showNametag3d),
                Func(self.toon.pose, 'slip-forward', 20),
                self.getDustCloudIval(wantSound = 1),
                Sequence(
                    Wait(0.5),
                    ActorInterval(self.toon, 'slip-forward', startFrame=20, endFrame=54),
                    self.toon.getTeleportOutTrack(),
                    Func(toonGeom.hide),
                    Func(self.toon.hideNametag2d),
                    Func(self.toon.hideNametag3d)
                )
            )
        )
        if callback:
            deathIval.append(Func(callback))
        deathIval.start()

    def getDoId(self):
        return self.doId

    @property
    def collisionName(self):
        return f'propHuntProp-{self.getDoId()}'