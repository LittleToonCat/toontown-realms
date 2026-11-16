"""
Toontown Realms Scrolled Frame:
Wrapper for DirectScrolledFrame - but it auto sizes and places the elements and gets rid of the hassle of using it

item1 = OnscreenText('This is a text object'...)
item2 = AnimatedButton('Animated!!!', command = xxx...)
frame = ToontownScrolledFrame(
                        parent = x,
                        pos = Vec3(x,x,x),
                        width = ##,
                        height = ##)
frame.addItems(item1, item2, ...)

"""
from typing import Union, Tuple, Dict, Optional, List

from direct.gui import DirectGuiGlobals
from direct.gui.DirectScrolledFrame import DirectScrolledFrame
from direct.gui.DirectGuiBase import DirectGuiBase, DirectGuiWidget
from panda3d.core import NodePath, Vec3


class ToontownScrolledGridFrame(DirectScrolledFrame):

    def __init__(self, parent, **kwargs):
        optiondefs = (
            ('relief', None, None),
            ('state', DirectGuiGlobals.NORMAL, None),
            ('manageScrollBars', False, None),
            ('scrollBarWidth', 0.05, None),
            ('autoHideScrollBars', True, None),
            ('verticalScroll_relief', None, None),
            ('width', 1.0, None),
            ('height', 1.0, None),
            ('itemPadding', 0.05, None),
            ('itemsPerRow', 5, None),
            ('itemMargin', (0, 0), None),
            # If we have this, we can auto determine the z padding (we still will add itemPadding tho)
            ('useItemBoundsForPadding', False, None),
            ('numSelectedItems', 1, None),
            ('selectedItems', [], None),
            ('lastSelectedItem', None, None),
            ('scrollAmount', None, None)
        )
        self.defineoptions(kwargs, optiondefs)
        DirectScrolledFrame.__init__(self,parent, **kwargs)
        self.initialiseoptions(ToontownScrolledGridFrame)
        self['frameSize'] = (-self['width'], self['width'], -self['height'], self['height'])
        self['canvasSize'] = (-self['width'] + 0.05, self['width'] - 0.05, -self['height']+0.025, self['height'] - 0.025)

        self.verticalScroll.incButton.destroy()
        self.verticalScroll.decButton.destroy()
        self.horizontalScroll.incButton.destroy()
        self.horizontalScroll.decButton.destroy()

        self.items: List[Union[DirectGuiWidget, Tuple[DirectGuiWidget, Optional[Dict[str, float]]]]] = []

    def __scrollUp(self, task = None):
        # We don't gotta do anything if theres nothing to scroll
        if self.verticalScroll.isHidden():
            return

        if self.verticalScroll['value'] > 0:
            self.verticalScroll['value'] -= self['scrollAmount'] if self['scrollAmount'] else 1/(len(self.items) / self['itemsPerRow'])

    def __scrollDown(self, task = None):
        # We don't gotta do anything if theres nothing to scroll
        if self.verticalScroll.isHidden():
            return

        if self.verticalScroll['value'] < 1.0:
            self.verticalScroll['value'] += self['scrollAmount'] if self['scrollAmount'] else 1/(len(self.items) / self['itemsPerRow'])

    def destroy(self):
        for item in self.items:
            item[0].destroy()

        del self.items[:]
        DirectScrolledFrame.destroy(self)

    def getSelectedItem(self, index):
        """
        Get a selected item in the frame.
        """
        if 0 <= index < len(self['selectedItems']):
            return self['selectedItems'][index]
        return None

    def getSelectedItems(self):
        """
        Get all selected items in the frame.
        """
        return self['selectedItems']

    def selectItemByIndex(self, index):
        if 0 <= index < len(self.items):
            item = self.items[index]
            self.selectItem(item)

    def selectItem(self, item: Union[DirectGuiWidget, Tuple[DirectGuiWidget, Optional[Dict[str, float]]]]):
        """
        Select an item in the frame
        """
        if isinstance(item, tuple):
            item = item[0]

        if item not in self['selectedItems']:
            if len(self['selectedItems']) >= self['numSelectedItems']:
                self.unselectItem(self['lastSelectedItem'])
            item.select()
            self['lastSelectedItem'] = item
            self['selectedItems'].append(item)

    def unselectItem(self, item: Union[DirectGuiWidget, Tuple[DirectGuiWidget, Optional[Dict[str, float]]]]):
        """
        Unselect an item in the frame
        """
        if isinstance(item, tuple):
            item = item[0]

        if item in self['selectedItems']:
            if item == self['lastSelectedItem']:
                self['lastSelectedItem'] = None
            item.unselect()
            self['selectedItems'].remove(item)

    def clearItems(self):
        """
        Clears all items in the frame
        """
        for item in self.items:
            item[0].destroy()

        del self.items[:]
        self.items = []
        self['lastSelectedItem'] = None
        self['selectedItems'] = []

    def removeItem(self, item: Union[DirectGuiWidget, Tuple[DirectGuiWidget, Optional[Dict[str, float]]]]):
        """
        Removes an item from the frame.
        """
        self.unselectItem(item)
        if isinstance(item, tuple):
            if item in self.items:
                item[0].destroy()
                self.items.remove(item)
        else:
            for i in self.items:
                if item == i[0]:
                    item.destroy()
                    self.items.remove(i)

        self.buildFrame()

    def insertItems(self, *items: Union[DirectGuiWidget, Tuple[DirectGuiWidget, Optional[Dict[str, float]]]], index: int = 0):
        """
        Add items to the scrolled list, then we auto arrange them

        :param items: All items
        :param index: Position where all items should go.
        """
        for item in items:
            if isinstance(item, tuple):
                # If it's a tuple, we have added some sort of offset
                self.items.insert(
                        index,
                        (item[0], item[1])
                )
            else:
                self.items.insert(
                        index,
                        (item, None)
                )

        self.buildFrame()

    def addItems(self, *items: Union[DirectGuiWidget,
                                     Tuple[DirectGuiWidget, Optional[Dict[str, float]]]]):
        """
        Add items to the scrolled list, then we auto arrange them

        :param items: All items
        """
        for item in items:
            if isinstance(item, tuple):
                # If it's a tuple, we have added some sort of offset
                self.items.append(
                        (item[0], item[1])
                )
            else:
                self.items.append(
                        (item, None)
                )

        self.buildFrame()

    def buildFrame(self):
        """
        arranges the items into the frame
        """
        self.ignoreAll()
        self.accept(f'press-wheel_up-{self.guiId}', self.__scrollUp)
        self.accept(f'press-wheel_down-{self.guiId}', self.__scrollDown)
        x = self['itemMargin'][0] - self['itemPadding']/2.
        z = self['itemMargin'][1] + self['itemPadding']/2.

        buttonPos = Vec3(x, 0, z)
        for i, _i in enumerate(self.items):
            item, offsets = _i
            item.reparentTo(self.canvas)
            item.setPos(buttonPos)
            # stupid hack to allow scrolling while hovering over a btn
            if hasattr(item, 'guiId'):
                self.accept(f'press-wheel_up-{item.guiId}', self.__scrollUp)
                self.accept(f'press-wheel_down-{item.guiId}', self.__scrollDown)

            if not (i + 1) % self['itemsPerRow']:
                buttonPos.setX(self['itemMargin'][0] - self['itemPadding']/2.)
                buttonPos.addZ(-self['itemPadding'])
            else:
                buttonPos.addX(self['itemPadding'])
            if self['useItemBoundsForPadding']:
                buttonPos.addZ -= item.getHeight()
        self['canvasSize'] = (-self['width'] + 0.05, self['width'] - 0.05, buttonPos.getZ() - self['itemPadding']/2., 0)
