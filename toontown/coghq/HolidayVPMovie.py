from direct.gui.DirectGui import DirectFrame, DirectLabel
from direct.fsm.StateData import StateData
from direct.showbase.RandomNumGen import RandomNumGen

from panda3d.core import PlaneNode, TextNode, Plane

from toontown.toon import Toon, ToonDNA
from toontown.cogdominium.CogdoUtil import CogdoGameMovie
from toontown.cogdominium import CogdoUtil
from toontown.toonbase import TTLocalizer, ToontownGlobals


class HolidayVPMovie(CogdoGameMovie, StateData):
    def __init__(self, rng):
        CogdoGameMovie.__init__(self)
        StateData.__init__(self, 'HolidayVPMovieDone')

        self._rng = RandomNumGen(rng)

        self._toons = []

        self.head = None
        self.clipPlane = None
        self.gameTitleText = None
        self.frame = None

    def _getRandomLine(self, lineList):
        return CogdoUtil.getRandomDialogueLine(lineList, self._rng)

    def displayLine(self, who, text):
        self._dialogueLabel.node().setText(text)
        who.playDialogueForString(text)

    def changeHead(self, who):
        if self.head:
            self.head.reparentTo(hidden)
            if hasattr(who, 'suit') and who.suit:
                who.suit.reparentTo(hidden)
            self.head.clearClipPlane()
        self.head = who
        if not self.clipPlane:
            self.setupClipPlane()
        who.reparentTo(aspect2d)
        if hasattr(who, 'suit') and who.suit:
            who.suit.reparentTo(self.head)
        self.head.setClipPlane(self.clipPlane)

    def changeAndDisplay(self, who, text):
        self.changeHead(who)
        self.displayLine(who, text)

    def setupClipPlane(self):
        self.clipPlane = self.frame.attachNewNode(PlaneNode('clip'))
        self.clipPlane.node().setPlane(Plane(0, 0, 1, 0))
        self.clipPlane.setPos(0, 0, -.167)

    def makeToonForGui(self, dna):
        toonDNA = ToonDNA.ToonDNA()
        toonDNA.newToonFromProperties(*dna)
        toon = Toon.Toon()
        toon.setDNA(toonDNA)
        toon.getGeomNode().setDepthWrite(1)
        toon.getGeomNode().setDepthTest(1)
        toon.loop('neutral')
        toon.setPosHprScale(-0.73, 0, -1.27, 180, 0, 0, 0.14, 0.14, 0.14)
        # Adjust the position of the toon based on it's height
        # this helps keep it in frame especially if it's a really short toon
        toon.setZ(-.58-toon.getHeight()/7)
        toon.reparentTo(hidden)
        toon.startBlink()
        self._toons.append(toon)
        return toon

    def load(self):
        StateData.load(self)
        CogdoGameMovie.load(self)

        # Load and transform the GUI
        backgroundGui = loader.loadModel('phase_5/models/cogdominium/tt_m_gui_csa_flyThru')
        bg = backgroundGui.find('**/background')
        chatBubble = backgroundGui.find('**/chatBubble')
        chatBubble.setScale(6.5, 6.5, 7.3)
        chatBubble.setPos(0.32, 0, -0.78)
        bg.setScale(5.2)
        bg.setPos(0.14, 0, -0.6667)
        bg.reparentTo(aspect2d)
        chatBubble.reparentTo(aspect2d)
        self.frame = DirectFrame(geom=bg, relief=None, pos=(0.2, 0, -0.6667))
        bg.wrtReparentTo(self.frame)

        # Create the title label
        self.gameTitleText = DirectLabel(parent=self.frame, text='', scale=TTLocalizer.MRPgameTitleText * 0.8, text_align=TextNode.ACenter,
                                         text_font=ToontownGlobals.getSignFont(), text_fg=(1.0, 0.33, 0.33, 1.0), pos=TTLocalizer.MRgameTitleTextPos, relief=None)
        chatBubble.wrtReparentTo(self.frame)
        backgroundGui.removeNode()

        # Make dialogue label visible
        self._dialogueLabel.reparentTo(aspect2d)

    def unload(self):
        StateData.unload(self)

        if self.head:
            if hasattr(self.head, 'stopBlink'):
                self.head.stopBlink()
            if hasattr(self.head, 'stop'):
                self.head.stop()
            del self.head

        for toon in self._toons:
            if toon:
                toon.cleanup()
                toon.removeNode()
                toon.delete()
        self._toons = []

        if self.gameTitleText:
            self.gameTitleText.destroy()

        if self.frame:
            self.frame.destroy()

        CogdoGameMovie.unload(self)
