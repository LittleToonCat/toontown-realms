from panda3d.core import *
from direct.gui.DirectGui import *
from toontown.suit import Suit, SuitDNA
from toontown.toonbase import ToontownGlobals
import random
from . import ShtikerPage


class RoguesGallery(ShtikerPage.ShtikerPage):

    def __init__(self, rognamestr=None, wantAnimate=True):
        ShtikerPage.ShtikerPage.__init__(self)
        self.rognamestr = rognamestr
        self.wantAnimate = wantAnimate

    def load(self):
        ShtikerPage.ShtikerPage.load(self)

        circleModel = loader.loadModel(
            'phase_3/models/gui/tt_m_gui_mat_nameShop')
        barTexture = loader.loadTexture('phase_3/maps/slider.png')

        self.frame = DirectScrolledFrame(
            parent=self, relief=None, frameSize=(-0.85, 0.85, -0.6, 0.725))

        self.frame.verticalScroll['frameTexture'] = barTexture
        self.frame.verticalScroll.setTransparency(True)
        self.frame.verticalScroll.incButton['relief'] = None
        self.frame.verticalScroll.decButton['relief'] = None
        self.frame.verticalScroll.thumb['geom'] = circleModel.find(
            '**/tt_t_gui_mat_namePanelCircle')
        self.frame.verticalScroll['resizeThumb'] = False
        self.frame.verticalScroll.incButton.reparentTo(hidden)
        self.frame.verticalScroll.decButton.reparentTo(hidden)

        self.frame.horizontalScroll['frameTexture'] = barTexture
        self.frame.horizontalScroll.setTransparency(True)
        self.frame.horizontalScroll.incButton['relief'] = None
        self.frame.horizontalScroll.decButton['relief'] = None
        self.frame.horizontalScroll.thumb['geom'] = circleModel.find(
            '**/tt_t_gui_mat_namePanelCircle')
        self.frame.horizontalScroll['resizeThumb'] = False
        self.frame.horizontalScroll.incButton.reparentTo(hidden)
        self.frame.horizontalScroll.decButton.reparentTo(hidden)

        circleModel.removeNode()
        loader.unloadTexture(barTexture)

        if self.rognamestr == None:
            self.numSuitTypes = SuitDNA.suitsPerDept
            self.numSuitDepts = len(SuitDNA.suitDepts)
        else:
            self.numSuitTypes = 1
            self.numSuitDepts = 1
        self.frame['canvasSize'] = (0, self.numSuitTypes, 0, self.numSuitDepts)
        self.__makeGallery()

    def unload(self):
        ShtikerPage.ShtikerPage.unload(self)
        del self.suits
        del self.actors
        self.frame.destroy()
        del self.frame

    def enter(self):
        ShtikerPage.ShtikerPage.enter(self)
        if self.wantAnimate:
            self.animate()
        else:
            self.pose()

    def exit(self):
        ShtikerPage.ShtikerPage.exit(self)
        self.stop()
        self.ignoreAll()

    def animate(self):
        for suit in self.actors:
            suit.loop('neutral')

    def pose(self):
        for suit in self.actors:
            suit.pose('neutral', 30)

    def stop(self):
        for suit in self.actors:
            suit.stop()

    def __makeGallery(self):
        self.suits = []
        self.actors = []
        self.text = TextNode('rogues')
        self.text.setFont(ToontownGlobals.getSuitFont())
        self.text.setAlign(TextNode.ACenter)
        self.text.setTextColor(0.5, 0.5, 0.5, 1.0)
        if self.rognamestr == None or len(self.rognamestr) == 0:
            for dept in SuitDNA.suitDepts:
                self.__makeDept(dept)

        else:
            self.suitRow = []
            self.__makeSuit(None, None, self.rognamestr)

            self.suits.append(self.suitRow)
            del self.suitRow
        self.__positionSuits()

    def __makeDept(self, dept):
        self.suitRow = []
        for type in range(self.numSuitTypes):
            self.__makeSuit(dept, type)

        self.suits.append(self.suitRow)
        del self.suitRow

    def __makeSuit(self, dept, type, name=None):
        dna = SuitDNA.SuitDNA()
        if name != None:
            dna.newSuit(name)
        else:
            dna.newSuitRandom(type + 1, dept)
        suit = Suit.Suit()
        suit.setDNA(dna)
        suit.update()
        suit.reparentTo(self.frame.getCanvas())
        suit.setHpr(180.0, 0.0, 0.0)
        suit.setScale(0.1)
        profile = Suit.Suit()
        profile.setDNA(dna)
        #profile.generateSuit()
        profile.reparentTo(self.frame.getCanvas())
        profile.setHpr(90.0, 0.0, 0.0)
        profile.setScale(0.1)
        self.suitRow.append((suit,
                             profile))
        self.actors.append(suit)
        self.actors.append(profile)
        suit.setDepthTest(1)
        suit.setDepthWrite(1)
        profile.setDepthTest(1)
        profile.setDepthWrite(1)

    def __positionSuits(self):
        y = self.numSuitDepts
        for suitRow in self.suits:
            x = 0.25
            y -= 1
            for entry in suitRow:
                suit = entry[0]
                profile = entry[1]
                suit.setPos(x, 10.0, y)
                profile.setPos(x + 0.5, 10.0, y)
                self.text.setText(suit.getName())
                name = self.frame.getCanvas().attachNewNode(self.text.generate())
                name.setPos(x + 0.25, 0.0, y + 0.05)
                name.setScale(0.1)
                x += 1
