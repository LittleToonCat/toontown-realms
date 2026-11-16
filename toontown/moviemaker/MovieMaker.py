from typing import Dict, Union, Optional, Tuple, List

from direct.fsm.FSM import FSM
from panda3d.core import NodePath, CSDefault, CollisionNode, GeomNode, CollisionTraverser, CollisionHandlerQueue, CollisionRay, PointerData, CollisionEntry, BitMask32, \
    KeyboardButton
from panda3d.toontown import DNAStorage, loadDNAFile

from toontown.moviemaker.MovieMakerActor import MovieMakerToon, MovieMakerActor, MovieMakerCog
from toontown.moviemaker.MovieMakerCamera import MovieMakerCamera
from toontown.moviemaker.MovieMakerData import MovieMakerData
from toontown.moviemaker.MovieMakerGUI import MovieMakerGUI, BROWSER_OPEN
from toontown.suit.SuitDNA import SuitDNA
from toontown.toon.NPCToons import NPCToonDict
from toontown.toon.ToonDNA import ToonDNA
from toontown.toonbase import HotkeySettings


class MovieMaker(FSM):
    DNAStorage = DNAStorage()

    def __init__(self):
        FSM.__init__(self, 'MovieMakerFSM')
        self.gui: MovieMakerGUI = MovieMakerGUI(self)
        self.sceneData: MovieMakerData = MovieMakerData(self)

        self.actorLayer: NodePath = base.render.attachNewNode('MovieMaker.actorLayer')

        self.camera = MovieMakerCamera()

        self.currentTimestamp: float = 0.0

        self.grabbedActor: Optional[MovieMakerActor] = None
        self.selectedActor: Optional[MovieMakerActor] = None
        self.ccTrav = CollisionTraverser('MovieMaker.ccTrav')
        self.ccQueue = CollisionHandlerQueue()

        pickerNode = CollisionNode('mouseRay')
        pickerNP = base.camera.attachNewNode(pickerNode)
        pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
        pickerNode.setIntoCollideMask(BitMask32.allOn())
        self.pickerRay = CollisionRay()
        pickerNode.addSolid(self.pickerRay)
        self.ccTrav.addCollider(pickerNP, self.ccQueue)

        self.accept('mouse1', self.attemptSelect)

    def loadEnvironment(self, environmentData: Dict):
        storages: List[str] = environmentData.get('storage_files', [])
        dna: Optional[str] = environmentData.get('dna_file', None)
        skyModel: Optional[str] = environmentData.get('sky_model', None)

        if dna:
            loadDNAFile(self.DNAStorage, 'phase_4/dna/ttrm_d_strg.dna', CSDefault, 1)

            for storage in storages:
                loadDNAFile(self.DNAStorage, storage, CSDefault, 1)
                base.loader.tick()

            np: NodePath = loadDNAFile(self.DNAStorage, dna, CSDefault, 1)
            if np.getNumParents() == 1:
                self.geom = NodePath(np.getParent(0))
                self.geom.reparentTo(render)
            else:
                self.geom: NodePath = render.attachNewNode(np)
        else:
            self.geom: NodePath = base.render.attachNewNode('moviemakergeom')
        base.loader.tick()
        self.sky: NodePath = base.loader.loadModel(skyModel)
        self.sky.setScale(5)
        base.camLens.setFar(9999)
        self.sky.reparentTo(self.geom)

        # Hide the black parts in the doors
        doorHoles = self.geom.findAllMatches('**/doorFrameHole*')
        for hole in doorHoles:
            hole.removeNode()

    def placeToon(self, dna: Union[str, Tuple, int]):
        if self.grabbedActor:
            self.sceneData.addActor(self.grabbedActor)
            self.removeTask('moveGrabbedActor')
            self.grabbedActor.delete()
            self.grabbedActor = None
        if dna == 'random':
            d = ToonDNA()
            d.newToonRandom()
            newToon = MovieMakerToon(self)
            newToon.setDNA(d)
        if isinstance(dna, int):
            desc = NPCToonDict[dna]
            if len(desc) == 10:
                _, name, dnaType, gender, _, _, hat, glasses, backpack, shoes = desc
            else:
                _, name, dnaType, gender, _, _ = desc
            newDna = ToonDNA()
            newDna.newToonFromProperties(*dnaType)
            newToon = MovieMakerToon(self)
            newToon.setDNAString(newDna.makeNetString())
            if len(desc) == 10:
                a, b, c = hat
                newToon.setHat(a, b, c)
                a, b, c = backpack
                newToon.setBackpack(a, b, c)
                a, b, c = glasses
                newToon.setGlasses(a, b, c)
                a, b, c = shoes
                newToon.setShoes(a, b, c)
            newToon.setName(name)
        else:
            d = ToonDNA()
            d.newToonFromProperties(*dna)
            newToon = MovieMakerToon(self)
            newToon.setDNA(d)
        self.sceneData.addActor(newToon)
        self.grabActor(newToon)

    def placeCog(self, dna: str):
        if self.grabbedActor:
            self.sceneData.addActor(self.grabbedActor)
            self.removeTask('moveGrabbedActor')
            self.grabbedActor.delete()
            self.grabbedActor = None
        newCog = MovieMakerCog(self)
        nDna = SuitDNA()
        nDna.newSuit(dna)
        newCog.setDNA(nDna)

        self.sceneData.addActor(newCog)
        self.grabActor(newCog)

    def grabActor(self, actor: MovieMakerActor):
        self.ignore('mouse1')
        self.deselect()
        self.grabbedActor = actor

        self.addTask(self.__moveGrabbedTask, 'moveGrabbedActor')
        self.accept('mouse1', self.finishMoving)

    def __moveGrabbedTask(self, task):
        if not self.grabbedActor:
            return task.done
        if not base.mouseWatcherNode.hasMouse():
            return task.cont

        mouse: PointerData = base.mouseWatcherNode.getMouse()
        self.pickerRay.setFromLens(base.camNode, mouse.getX(), mouse.getY())

        self.ccTrav.traverse(render)
        if self.ccQueue.getNumEntries() > 0:
            self.ccQueue.sortEntries()
            entry: CollisionEntry = self.ccQueue.getEntry(0)
            if entry.hasSurfacePoint():
                pos = entry.getSurfacePoint(render)
                if base.mouseWatcherNode.isButtonDown(KeyboardButton.asciiKey(HotkeySettings.PropGeneratorRotateModifier.get())):
                    self.grabbedActor.lookAt(pos[0], pos[1], pos[2])
                    self.grabbedActor.setP(0)
                    self.grabbedActor.setR(0)
                else:
                    self.grabbedActor.setPos(pos[0], pos[1], pos[2] + 6)

        return task.cont

    def finishMoving(self):
        if not self.grabbedActor:
            return
        if not base.mouseWatcherNode.hasMouse():
            return
        self.ignore('mouse1')
        self.removeTask('moveGrabbedActor')

        self.accept('mouse1', self.attemptSelect)

        mouse: PointerData = base.mouseWatcherNode.getMouse()
        self.pickerRay.setFromLens(base.camNode, mouse.getX(), mouse.getY())

        self.ccTrav.traverse(render)
        if self.ccQueue.getNumEntries() > 0:
            self.ccQueue.sortEntries()
            entry: CollisionEntry = self.ccQueue.getEntry(0)
            if entry.hasSurfacePoint():
                pos = entry.getSurfacePoint(render)
                self.grabbedActor.setPos(pos[0], pos[1], pos[2])
                self.grabbedActor.reparentTo(self.actorLayer)
                self.select(self.grabbedActor)
                self.grabbedActor = None

    def attemptSelect(self):
        mouse: PointerData = base.mouseWatcherNode.getMouse()
        self.pickerRay.setFromLens(base.camNode, mouse.getX(), mouse.getY())

        self.ccTrav.traverse(render)
        if self.ccQueue.getNumEntries() > 0:
            self.ccQueue.sortEntries()
            entry: CollisionEntry = self.ccQueue.getEntry(0)
            findTag = entry.getIntoNodePath().findNetTag('actor')
            if findTag.isEmpty():
                self.deselect()
            else:
                sel = self.sceneData.getActorFromHash(findTag.getTag('actor'))
                if sel == self.selectedActor:
                    return
                self.deselect()
                self.select(self.sceneData.getActorFromHash(findTag.getTag('actor')))

    def select(self, actor: MovieMakerActor):
        self.selectedActor = actor
        self.selectedActor.openEditor()

    def deselect(self):
        if self.selectedActor:
            self.selectedActor.closeEditor()
            self.selectedActor = None

    def printJson(self):
        print(self.sceneData.toJson())

    def screenshot(self):
        base.aspect2d.hide()
        base.takeScreenShot()
        base.aspect2d.show()
