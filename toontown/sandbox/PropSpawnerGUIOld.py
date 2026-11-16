"""
Prop Spawner - Main GUI
"""
from typing import Dict

from direct.gui.DirectGui import *
from panda3d.core import Vec3, NodePath, TextNode

from otp.otpbase.PythonUtil import bound
from toontown.sandbox import PropGlobals
from toontown.sandbox.PropGlobals import PropCategory
from toontown.toonbase import ToontownGlobals, ClientSettings
from toontown.toontowngui.AnimatedButton import AnimatedButton
from toontown.sandbox.PropSpawnerItem import PropSpawnerItem


# from toontown.hood.DistributedPropGenerator import DistributedPropGenerator


class PropSpawnerGUI(DirectFrame):
    page = 0
    propList = list(PropGlobals.PropList.keys())
    totalPages = len(propList) // 35
    category = PropCategory.All
    open = False

    def __init__(self, generator, **kwargs):  # type: (DistributedPropGenerator, []) -> None
        optiondefs = (
            ('pos', (0, 0, 0.05), None),
            ('relief', None, None),
            ('image', PropGlobals.PropUi.find('**/propui_bg'), None),
            ('image_pos', (0, 0, -0.09), None),
            ('image_scale', (2.63, 1, 1.98), None),
            ('image_color', ToontownGlobals.GlobalDialogColor, None)
        )

        self.defineoptions(kwargs, optiondefs)
        base.transitions.fadeScreen(0.5)
        DirectFrame.__init__(self, aspect2dp)
        self.initialiseoptions(PropSpawnerGUI)
        self.propButtons = []  # type: list[PropSpawnerItem]

        # Lock the Toon down
        base.localAvatar.setLocked(True)
        if base.cr.playGame.getPlace().getState() != 'battle':
            base.cr.playGame.getPlace().setState('stopped')

        self.generator = generator
        guiClose = loader.loadModel('phase_3.5/models/gui/avatar_panel_gui')  # type: NodePath
        self.cancel = AnimatedButton(
                parent = self,
                relief = None,
                image = (PropGlobals.PropUi.find('**/close_button_normal'),
                         PropGlobals.PropUi.find('**/close_button_click'),
                         PropGlobals.PropUi.find('**/close_button_hover'),
                         PropGlobals.PropUi.find('**/close_button_normal')),
                pos = (1.14, 0, -0.88),
                scale = 0.08,
                command = self.exit
        )

        self.categoryIndicator = OnscreenText(
                parent = self,
                text = '??',
                scale = 0.05,
                pos = (0.0, -0.84)
        )

        guiClose.removeNode()

        cdrGui = loader.loadModel('phase_3.5/models/gui/tt_m_gui_sbk_codeRedemptionGui')  # type: NodePath

        self.searchBar = DirectEntry(
                parent = hidden,
                text_align = TextNode.ACenter,
                relief = None,
                image = cdrGui.find('**/tt_t_gui_sbk_cdrCodeBox'),
                image_scale = (1.1, 1, 1),
                text_scale = 0.06, width = 12,
                textMayChange = 1,
                pos = (.5, 0, -0.88),
                scale = 0.5,
                backgroundFocus = 0,
                focusInCommand=self.__toggleSearchFocus,
                focusInExtraArgs=[True],
                focusOutCommand=self.__toggleSearchFocus,
                focusOutExtraArgs=[False]
        )
        self.searchBar.bind(DGG.TYPE, self.__updateSearch)
        self.searchBar.bind(DGG.ERASE, self.__updateSearch)
        self.categoryButtons: Dict[str, AnimatedButton] = {}
        for i, category in enumerate(PropCategory):
            icn = AnimatedButton(
                    parent = self,
                    image = PropGlobals.PropUi.find(f'**/category_{category.name.lower()}'),
                    image_scale = 0.085,
                    text = ('', category.name, category.name, ''),
                    text_scale = 0.04,
                    text_pos = (0, 0.07),
                    image3_color = (0.8, 0.8, 0.8, 0.5),
                    pos = (-1.14 + i / 10.5, 0, -0.88),
                    command = self.applyFilter,
                    extraArgs = [category]
            )
            self.categoryButtons[category] = icn
        if self.category == PropCategory.Search:
            self.applyFilter(PropCategory.All)
        else:
            self.loadProps()

        cdrGui.removeNode()

        PropSpawnerGUI.open = True

    def changePage(self, off = 0):
        messenger.send('wakeup')
        PropSpawnerGUI.page = bound(self.page + off, 0, self.totalPages)
        self.loadProps()

    def loadProps(self):
        self.__updatePageNumber()
        for btn in self.propButtons:
            btn.destroy()
            del btn
        pos = Vec3(-0.9, 0, .6)
        for i, prop in enumerate(self.propList[self.page * 35:(self.page + 1) * 35]):
            btn = PropSpawnerItem(self, prop, parent = self, pos = pos)

            pos.addX(0.3)
            if not (i + 1) % 7:
                pos.setX(-0.9)
                pos.addZ(-0.3)
            self.propButtons.append(btn)

    def applyFilter(self, category):  # type: (PropCategory) -> None
        self.__focusOutSearchBar()
        self.searchBar.reparentTo(hidden)
        if category == PropCategory.All:
            PropSpawnerGUI.propList = list(PropGlobals.PropList.keys())
        elif category == PropCategory.Favorites:
            PropSpawnerGUI.propList = []  # todo: save and load favotires
            favorites = ClientSettings.FavoriteProps.get()
            for i in favorites:
                if i in PropGlobals.PropList:
                    self.propList.append(i)
        elif category == PropCategory.Search:
            PropSpawnerGUI.propList = list(PropGlobals.PropList.keys())
            self.searchBar.reparentTo(self)
        else:
            PropSpawnerGUI.propList = []
            for i in PropGlobals.PropCategories[category]:
                if i in PropGlobals.PropList:
                    self.propList.append(i)
        PropSpawnerGUI.totalPages = len(self.propList) // 35
        PropSpawnerGUI.page = 0
        PropSpawnerGUI.category = category
        self.loadProps()

    def __updateSearch(self, e):
        PropSpawnerGUI.propList = []
        searchTerm = self.searchBar.get().lower()
        for prop in PropGlobals.PropList:
            if searchTerm in prop.lower():
                self.propList.append(prop)

        PropSpawnerGUI.page = 0
        if len(self.propList) == 0:
            PropSpawnerGUI.totalPages = 0
        else:
            PropSpawnerGUI.totalPages = len(self.propList) // 35

        self.loadProps()

    def __focusOutSearchBar(self):
        self.searchBar['focus'] = 0
        self.searchBar.setFocus()
        self.__toggleSearchFocus(False)

    def __toggleSearchFocus(self, state):
        if state:
            localAvatar.chatMgr.disableBackgroundFocus()
        else:
            localAvatar.chatMgr.setBackgroundFocus(base.controlManager.getChatDisabled(), True)

    def __updatePageNumber(self):
        self.categoryIndicator['text'] = self.category.name
        self.pageIndicator['text'] = f'{self.page+1} / {self.totalPages+1}'
        self.lArrow['state'] = DGG.DISABLED if self.page == 0 else DGG.NORMAL
        self.rArrow['state'] = DGG.DISABLED if self.page == self.totalPages else DGG.NORMAL

        for btn in self.categoryButtons:
            self.categoryButtons[btn]['state'] = DGG.DISABLED if btn == self.category else DGG.NORMAL

    def select(self, prop):
        self.generator.selectProp(list(PropGlobals.PropList.keys()).index(prop))
        self.exit()

    def exit(self):
        self.__focusOutSearchBar()
        for btn in self.propButtons:
            btn.destroy()
            del btn
        self.destroy()

        # Unlock the Toon
        if base.cr.playGame.getPlace().getState() == 'battle':
            # Don't allow the Toon to move around if in battle
            exception = ToontownGlobals.LockedStateFlagChangeOnly

            base.cr.playGame.getPlace().setState('walk')
        else:
            exception = 0
        base.localAvatar.setLocked(False, exception)

        base.transitions.noFade()

        PropSpawnerGUI.open = False

    def addToFavorites(self, prop):
        favoriteList = ClientSettings.FavoriteProps.get()
        if prop not in favoriteList:
            favoriteList.append(prop)
            ClientSettings.FavoriteProps.set(favoriteList)
        if self.category == PropCategory.Favorites:
            self.applyFilter(PropCategory.Favorites)

    def removeFromFavorites(self, prop):
        favoriteList = ClientSettings.FavoriteProps.get()
        if prop in favoriteList:
            favoriteList.remove(prop)
            ClientSettings.FavoriteProps.set(favoriteList)
        if self.category == PropCategory.Favorites:
            self.applyFilter(PropCategory.Favorites)
