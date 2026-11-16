from panda3d.core import *
from panda3d.toontown import *
import random
from . import ToonInteriorColors
from toontown.hood import ZoneUtil
from toontown.building import DistributedToonInterior
from toontown.toonbase import ToontownGlobals, TTLocalizer
SIGN_LEFT = -4
SIGN_RIGHT = 4
SIGN_BOTTOM = -3.5
SIGN_TOP = 1.5
FrameScale = 1.4

class DistributedToonLandLibraryInterior(DistributedToonInterior.DistributedToonInterior):

    def setup(self):
        DistributedToonInterior.DistributedToonInterior.setup(self)
        # Add the credits
        creditsTN = TextNode('credits')
        creditsTN.setFont(ToontownGlobals.getRealmsFont())

        creditsTN.setText(
            """
Toon Land Credits
Playground Design:
  Mark/Doctor Leroy (Lead Playground Designer)
 
Street Design:
  Chris/Chris552299 (Lead Street Designer)
 
Graphics Design:
  Chris/Chris552299 (Lead Graphics Designer)
 
Programming:
  Cody/Fd Green Cat Fd (Lead Programmer)

Adapted to Toontown Realms by
  Drewcification
"""
        )

        text = self.interior.find('**/trophy_origin').attachNewNode(creditsTN.generate())

        text.setX(-1.8)
        text.setScale(0.3)
        text.setZ(3)
        text.setY(-0.05)

        del creditsTN

