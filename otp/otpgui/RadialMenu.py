""" Radial Menu - drewcification 091720/091720 """
import math

from panda3d.core import *
from direct.gui.DirectFrame import DirectFrame, OnscreenImage
from direct.showbase.DirectObject import DirectObject
from direct.task import Task

from toontown.effects.FilterManager import FilterManager


class RadialMenu(DirectObject):
    gui = loader.loadModel("phase_3.5/models/gui/ttoff_m_gui_hud_cameraRadialMenu")

    def __init__(self, *items):
        # type: (tuple[NodePath]) -> None
        DirectObject.__init__(self)
        # Initialize variables
        self.isActive = 0
        self.selected = -1

        # Load the palletized gui model

        # i sohuld separate camera stuff from general radial stuff but oh well

        # Create the frame
        self.frame = DirectFrame(geom = self.gui.find("**/radial_menu_bg"), parent = hidden, scale = 1,
                                 relief = None)
        # Create the selection indicator
        self.selector = OnscreenImage(image = self.gui.find("**/radial_menu_bg_quarter"), parent = self.frame)

        # Load all the and calculate their positions
        self.itemAngle = 360 / len(items)
        self.items = []
        for i in range(len(items)):
            img = OnscreenImage(image = items[i], scale = 0.2, parent = self.frame,
                                pos = (
                                    Point3(.46 * math.cos(i * deg2Rad(self.itemAngle)),
                                           0,
                                           (.46 * math.sin(i * deg2Rad(self.itemAngle))))
                                )
                                )
            self.items.append(img)

    def activate(self):
        """ Shows the menu and spawns the mouse reader task """
        self.frame.reparentTo(aspect2d)
        taskMgr.add(self.radialTask, 'cam-radialTask')
        self.isActive = 1
        if FilterManager.activeFilter and FilterManager.activeFilter.identifier != "ttoffline:radialOverlay":
            return

        _filter = FilterManager.findFilter('ttoffline:radialOverlay')
        if _filter:
            _filter.activate()

    def deactivate(self):
        """ Hides the menu and kills the mouse reader task """
        taskMgr.remove('cam-radialTask')
        self.frame.reparentTo(hidden)
        self.isActive = 0
        if FilterManager.activeFilter and FilterManager.activeFilter.identifier == "ttoffline:radialOverlay":
            FilterManager.activeFilter.deactivate()

    def getChoice(self):
        """ Convenience Function Get the selected item """
        return self.selected

    def radialTask(self, task):
        """ Reads the mouse position and calculates which object it is looking at """
        # Initialize these as 0 incase we can't read the mouses position
        mouseX = 0
        mouseY = 0
        # Read the mouse position
        if base.mouseWatcherNode.hasMouse():
            mouseX = base.mouseWatcherNode.getMouseX()
            mouseY = base.mouseWatcherNode.getMouseY()
        # Calculate the angle that the mouse is at from the cursor
        menuAngle = rad2Deg(math.atan2(mouseY, mouseX)) + 45

        # Get the index of the item at the mouse angle
        sel = int(math.floor((menuAngle % 360) / self.itemAngle))
        if self.selected == sel:
            return Task.cont
        self.selected = sel

        # Set the rotation of the selector
        # The selector image is from 12 o'clock to 3 o'clock, so we need to
        # rotate it counter clockwise 45 degrees
        self.selector.setR(-self.itemAngle * self.selected + 45)

        # Highlight the selected item
        for i in self.items:
            i.setColorScale(1.0, 1.0, 1.0, 1.0)
            i.setScale(0.2)
        self.items[self.selected].setScale(0.25)
        self.items[self.selected].setColorScale(0.3, 1.0, 1.0, 1.0)

        return Task.cont