from direct.gui.DirectLabel import DirectLabel
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.DirectObject import DirectObject
from panda3d.core import NodePath, CollisionNode, CollisionSphere, Point3, Point2

from otp.otpbase.PythonUtil import bound
from toontown.hood import ZoneUtil
from toontown.toonbase import ToontownGlobals, TTLocalizer, HotkeySettings, ControlManager


class ToontownSkiesPortal(NodePath, DirectObject):

    def __init__(self):
        super(ToontownSkiesPortal, self).__init__('teleporter')

        ds = loader.loadModel('phase_4/models/props/ttrm_m_ara_ext_ttc_portal')
        ds.reparentTo(self)

        # Add the field label
        self.label = DirectLabel(parent = self, relief = None, text = f'toontownskies',
                                 text_fg = (1.0, 1.0, 0.6, 1.0), text_font = ToontownGlobals.getBuildingNametagFont(),
                                 scale = 0.6)
        self.label.setPos(0, 0, 5)
        self.label.setBillboardAxis()

        self.collSphere = CollisionSphere(0, 0, 4, 3)
        self.collSphere.setTangible(0)
        self.collNode = CollisionNode(self.collisionName)
        self.collNode.setCollideMask(ToontownGlobals.WallBitmask)
        self.collNode.addSolid(self.collSphere)
        self.collNodePath = self.attachNewNode(self.collNode)
        #self.collNodePath.show()

        self.accept(f'enter{self.collisionName}', self.__enterSphere)

    def __enterSphere(self, collEntry = None):
        """
        Toon has entered the trigger sphere
        """
        self.__createInteractHint()

    def __exitSphere(self, collEntry = None):
        self.ignore(f'exit{self.collisionName}')
        self.__destroyInteractHint()

    def __interact(self):
        """
        This is called when the user presses the Interact key
        """
        base.cr.playGame.getPlace().requestLeave({'loader': ZoneUtil.getBranchLoaderName(30000),
                                                  'where': ZoneUtil.getToonWhereName(30000),
                                                  'how': 'portalIn',
                                                  'hoodId': 30000,
                                                  'zoneId': 30000,
                                                  'avId': -1
                                                  })
        self.__exitSphere()

    def __createInteractHint(self):
        if not hasattr(self, "interactHint"):
            self.accept(HotkeySettings.Interact.getPressed(),
                        self.__interact)
            self.accept(f'exit{self.collisionName}', self.__exitSphere)
            self.accept('toonExitWalk', self.__exitSphere)

            text: str = ControlManager.ControlManager.parseHotkeyString(TTLocalizer.ActivityInteractPortal, useGlyphs=True)
            self.interactHint = OnscreenText(text, style = 3, scale = .065, parent = base.a2dBottomCenter,
                    font = ToontownGlobals.getFancyFont(),
                    fg = (0.92, 0.93, 0.56, 1.0),
                    pos = (0.0, 0.0))

            taskMgr.add(self.__alignInteractHint, self.alignInteractHintTaskName)

    def __destroyInteractHint(self):
        self.ignore(HotkeySettings.Interact.getPressed())
        self.ignore('toonExitWalk')
        # Remove interact hint
        if hasattr(self, "interactHint"):
            taskMgr.remove(self.alignInteractHintTaskName)
            self.interactHint.removeNode()
            del self.interactHint

    def __alignInteractHint(self, task):
        """
        Aligns the interact hint on the screen
        The hint should be positioned on the npc, then the position is projected to the aspect2d
        """
        if hasattr(self, 'interactHint'):
            center = base.cam.getRelativePoint(self, Point3(0, 0, 3))
            if base.camNode.isInView(center):
                center2d = Point2()
                base.camLens.project(center, center2d)

                center2d.x = bound(center2d.x, -0.7, 0.7)
                center2d.y = bound(center2d.y, -0.9, 0.95)
            else:
                # If the point isnt in the view, we set it to the 'default' position
                center2d = Point2(0.0, -0.45)

            self.interactHint.set_pos(render2d, Point3(center2d.x, 0, center2d.y))

        return task.cont

    def destroy(self):
        self.ignoreAll()
        self.collNodePath.removeNode()
        self.__exitSphere()
        self.removeNode()

    @property
    def alignInteractHintTaskName(self):
        return f'alignInteractHint-{self.getName()}'

    @property
    def collisionName(self):
        return f'skyPortal'
