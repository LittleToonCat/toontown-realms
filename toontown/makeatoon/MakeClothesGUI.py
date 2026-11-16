from . import ClothesGUI
from toontown.toon import ToonDNA
from ..toon.ToonDNA import ClothesColors


class MakeClothesGUI(ClothesGUI.ClothesGUI):
    notify = directNotify.newCategory('MakeClothesGUI')

    def __init__(self, doneEvent):
        ClothesGUI.ClothesGUI.__init__(self, ClothesGUI.CLOTHES_MAKETOON,
                                       doneEvent)

    def setupScrollInterface(self):
        self.dna = self.toon.getStyle()
        gender = self.dna.getGender()
        self.topStyles = ToonDNA.getTopStyles(gender, tailorId=ToonDNA.MAKE_A_TOON)
        self.tops = ToonDNA.getTops(gender, tailorId=ToonDNA.MAKE_A_TOON)
        self.bottomStyles = ToonDNA.getBottomStyles(gender, tailorId=ToonDNA.MAKE_A_TOON)
        self.bottoms = ToonDNA.getBottoms(gender, tailorId=ToonDNA.MAKE_A_TOON)
        self.gender = gender
        if gender == "m":
            gId = "b"
        else:
            gId = "g"

        self.topChoice = 0
        self.topColorChoice = 0

        self.topStyleChoice = 0

        self.bottomChoice = 0
        self.bottomStyleChoice = 0

        # setup the buttons
        self.setupButtons()

    def setupButtons(self):
        ClothesGUI.ClothesGUI.setupButtons(self)

        # Cover thy nakedness
        # This only happens in MakeAToon
        if len(self.dna.torso) == 1:
            if self.gender == 'm':
                torsoStyle = 's'
            elif self.girlInShorts == 1:
                torsoStyle = 's'
            else:
                torsoStyle = 'd'
            self.toon.swapToonTorso(self.dna.torso[0] + torsoStyle)
            self.toon.loop('neutral', 0)
            self.toon.swapToonColor(self.dna)
            
            # Set texture to start of clothes choices
            self.swapTop(0)
            self.swapBottom(0)
        return None
