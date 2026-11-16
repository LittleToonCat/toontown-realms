import random
from typing import Union, Tuple
from toontown.toonbase.ToontownTypes import TAccessory

from direct.gui.DirectButton import DirectButton
from panda3d.core import Vec3

from toontown.toon.DistributedToon import DistributedToon
from toontown.toon.Toon import Toon
from toontown.toon.ToonDNA import ToonDNA
from toontown.toon.ToonHead import ToonHead
SHOW_HEAD_ONLY = False


class ToonPortrait(DirectButton):
    uiModel = loader.loadModel('phase_3.5/models/gui/ttoff_m_gui_mgmn_bossParty')
    teamColors = (
        (0.8, 0.1, 0.1, 1.0),  # RED
        (0.1, 0.1, 0.8, 1.0),  # BLUE
        (0.1, 0.8, 0.1, 1.0),  # GREEN
        (0.6, 0.6, 0.6, 1.0)   # GRAY (SPECTATOR / DEAD)
    )

    def __init__(self, avatar: Union[DistributedToon, Tuple[str, TAccessory, TAccessory]], team: int = 0, **kwargs):
        optiondefs = (
            ('pos', (0, 0, 0), None),
            ('relief', None, None),
            ('image', ToonPortrait.uiModel.find('**/toonportrait_gen'), None),
            ('image_pos', (0, 0, 0), None),
            ('image_scale', (1.0, 1.0, 1.0), None),
            ('scale', 0.15, None),
            ('pressEffect', False, None)
        )

        self.defineoptions(kwargs, optiondefs)
        DirectButton.__init__(self, aspect2d)
        self.initialiseoptions(ToonPortrait)

        self.avatar = avatar
        self.team = team

        if SHOW_HEAD_ONLY:
            self.head = ToonHead()

            if isinstance(avatar, tuple):
                dna = ToonDNA()
                dna.makeFromNetString(avatar[0])
                self.head.setupHead(dna, forGui = True)
                self.head.generateHat(*avatar[1])
                self.head.generateGlasses(*avatar[2])
            else:
                self.head.setupHead(self.avatar.style, forGui = True)
                self.head.generateHat(*avatar.getHat())
                self.head.generateGlasses(*avatar.getGlasses())
            self.head.reparentTo(self)
            self.head.fitAndCenterHead(0.6, forGui = 1, rotationOffset = -35)
        else:
            self.toon = Toon()

            if isinstance(avatar, tuple):
                dna = ToonDNA()
                dna.makeFromNetString(avatar[0])
                self.toon.setDNA(dna)
                self.toon.setHat(*avatar[1])
                self.toon.setGlasses(*avatar[2])
            else:
                self.toon.setDNA(self.avatar.style)
                self.toon.generateHat(*avatar.getHat())
                self.toon.generateGlasses(*avatar.getGlasses())

            self.toon.reparentTo(self)
            self.toon.setZ(-self.toon.getHeight() / 2.35)
            self.toon.setH(200)
            self.toon.pose('neutral', random.randrange(0, self.toon.getNumFrames('neutral')))

            self.toon.setScale(0.5)
            self.toon.setDepthTest(1)
            self.toon.setDepthWrite(1)
            size = .465
            self.toon.setScissor(self, Vec3(-size), Vec3(size))

        self.setTeamColor(team)

    def setTeamColor(self, team = 0):
        self['image_color'] = ToonPortrait.teamColors[team]
