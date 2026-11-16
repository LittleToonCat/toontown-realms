from panda3d.core import CollisionNode, CollisionTube, Point3
from direct.interval.IntervalGlobal import *
from direct.distributed import DistributedObject
from toontown.toonbase import ToontownGlobals


class DistributedLawbotBossGavel(DistributedObject.DistributedObject):
    notify = directNotify.newCategory('DistributedLawbotBossGavel')

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        self.boss = None
        self.index = None
        self.avId = 0
        self.modelPath = 'phase_11/models/lawbotHQ/LB_gavel'
        self.nodePath = None
        self.ival = None
        self.origHpr = Point3(0, 0, 0)
        self.downTime = 0.5
        self.upTime = 5
        self.gavelSfx = None

    def announceGenerate(self):
        self.notify.debug('announceGenerate: %s' % self.doId)
        DistributedObject.DistributedObject.announceGenerate(self)
        self.name = 'gavel-%s' % self.doId
        self.loadModel(self.modelPath)
        self.nodePath.wrtReparentTo(render)
        self.gavelSfx = loader.loadSfx('phase_11/audio/sfx/LB_gavel.ogg')
        # Pretty hacky way of determining if we're in the Lawbot Arena
        if hasattr(self.boss, 'activeLawyer'):
            tempTuple = ToontownGlobals.LawbotArenaGavelPosHprs[self.index]
        else:
            tempTuple = ToontownGlobals.LawbotBossGavelPosHprs[self.index]
        self.nodePath.setPosHpr(*tempTuple)
        self.origHpr = Point3(tempTuple[3], tempTuple[4], tempTuple[5])
        self.downTime = ToontownGlobals.LawbotBossGavelTimes[self.index][0]
        self.upTime = ToontownGlobals.LawbotBossGavelTimes[self.index][1]
        self.stayDownTime = ToontownGlobals.LawbotBossGavelTimes[self.index][2]
        self.boss.gavels[self.index] = self

    def delete(self):
        DistributedObject.DistributedObject.delete(self)
        loader.unloadModel(self.modelPath)
        self.nodePath.removeNode()

    def loadModel(self, modelPath):
        if not self.nodePath:
            self.makeNodePath()
        else:
            self.gavel.getChildren().detach()
        model = loader.loadModel(modelPath)
        model.instanceTo(self.gavel)
        self.attachColTube()
        self.scale = 3.0
        self.nodePath.setScale(self.scale)

    def attachColTube(self):
        gavelTop = self.nodePath.find('**/top*')
        self.gavelTop = gavelTop
        gavelHandle = self.nodePath.find('**/handle*')
        collNode = CollisionNode(self.uniqueName('headSphere'))
        topBounds = gavelTop.getBounds()
        center = topBounds.getCenter()
        tube1 = CollisionTube(0, -1, center.getZ(), 0, 1, center.getZ(), 1)
        tube1.setTangible(0)
        collNode.addSolid(tube1)
        collNode.setTag('attackCode', str(ToontownGlobals.BossCogGavelStomp))
        collNode.setName('GavelZap')
        self.collNodePath = self.nodePath.attachNewNode(collNode)
        handleBounds = gavelHandle.getBounds()
        handleCenter = handleBounds.getCenter()
        handleRadius = handleBounds.getRadius()
        tube2 = CollisionTube(0, 0, handleCenter.getZ() + handleRadius, 0, 0, handleCenter.getZ() - handleRadius, 0.25)
        tube2.setTangible(0)
        handleCollNode = CollisionNode(self.uniqueName('gavelHandle'))
        handleCollNode.addSolid(tube2)
        handleCollNode.setTag('attackCode', str(ToontownGlobals.BossCogGavelHandle))
        handleCollNode.setName('GavelHandleZap')
        self.handleCollNodePath = self.nodePath.attachNewNode(handleCollNode)

    def makeNodePath(self):
        self.nodePath = render.attachNewNode(self.uniqueName('lawbotGavelNode'))
        self.gavel = self.nodePath.attachNewNode('myGavel')

    def disable(self):
        DistributedObject.DistributedObject.disable(self)
        self.nodePath.detachNode()
        if self.ival:
            self.ival.finish()
            self.ival = None
        self.ignoreAll()
        del self.boss.gavels[self.index]
        self.cleanup()

    def cleanup(self):
        self.boss = None

    def setBossCogId(self, bossCogId):
        self.bossCogId = bossCogId
        self.boss = base.cr.doId2do[bossCogId]

    def setIndex(self, index):
        self.index = index

    def activate(self):
        self.notify.debug('enterOn for gavel %d' % self.index)
        # Pretty hacky way of determining if we're in the Lawbot Arena
        if hasattr(self.boss, 'activeLawyer'):
            myHeadings = ToontownGlobals.LawbotArenaGavelHeadings[self.index]
        else:
            myHeadings = ToontownGlobals.LawbotBossGavelHeadings[self.index]
        seqName = 'LawbotBossGavel-%s' % self.doId
        self.ival = Sequence(name=seqName)
        downAngle = -80
        for index in range(len(myHeadings)):
            nextIndex = index + 1
            if nextIndex == len(myHeadings):
                nextIndex = 0
            goingDown = self.nodePath.hprInterval(self.downTime, Point3(myHeadings[index] + self.origHpr[0], downAngle, self.origHpr[2]), startHpr=Point3(myHeadings[index] + self.origHpr[0], 0, self.origHpr[2]))
            self.ival.append(goingDown)
            self.ival.append(SoundInterval(self.gavelSfx, node=self.gavelTop, volume = 0.5))
            self.ival.append(Wait(self.stayDownTime))
            goingUp = self.nodePath.hprInterval(self.upTime, Point3(myHeadings[nextIndex] + self.origHpr[0], 0, self.origHpr[2]), startHpr=Point3(myHeadings[index] + self.origHpr[0], downAngle, self.origHpr[2]))
            self.ival.append(goingUp)

        self.ival.loop()
        self.accept('enterGavelZap', self.__touchedGavel)
        self.accept('enterGavelHandleZap', self.__touchedGavelHandle)

    def enterOff(self):
        if self.ival:
            self.ival.finish()
        tempTuple = ToontownGlobals.LawbotBossGavelPosHprs[self.index]
        self.nodePath.setPosHpr(*tempTuple)

    def __touchedGavel(self, entry):
        self.notify.debug('__touchedGavel')
        self.notify.debug('self=%s entry=%s' % (self, entry))
        self.boss.touchedGavel(self, entry)

    def __touchedGavelHandle(self, entry):
        self.notify.debug('__touchedGavelHandle')
        self.boss.touchedGavelHandle(self, entry)
