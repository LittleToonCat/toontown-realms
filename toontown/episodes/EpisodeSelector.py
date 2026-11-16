from direct.directnotify import DirectNotifyGlobal
from direct.fsm import StateData
from direct.gui import DirectGuiGlobals
from direct.gui.DirectGui import *
from panda3d.core import Vec4, TextNode, PNMImage, Texture, TransparencyAttrib, Vec3

from toontown.episodes import EpisodeLocalizer
from toontown.episodes import EpisodeConfig
from toontown.toonbase import TTLocalizer, ClientSettings
from toontown.toonbase import ToontownGlobals
from toontown.toontowngui import ToontownGUIUtils
from toontown.toontowngui.AnimatedButton import AnimatedButton


class EpisodeSelector(DirectFrame, StateData.StateData):
    notify = DirectNotifyGlobal.directNotify.newCategory('EpisodeSelector')

    def __init__(self, avChooser):
        DirectFrame.__init__(self, pos = (0, 0, 0.05), relief = None, image = DGG.getDefaultDialogGeom(),
                             image_scale = (2.2, 1, 1.4), image_pos = (0, 0, -0.05),
                             image_color = ToontownGlobals.GlobalDialogColor, text = TTLocalizer.AvatarChooserEpisodes,
                             text_scale = 0.12, text_pos = (0, 0.5), borderWidth = (0.01, 0.01))
        StateData.StateData.__init__(self, 'episode-selector-done')
        self.isLoaded = False
        self.setBin('gui-popup', 0)
        self.initialiseoptions(EpisodeSelector)
        self.avChooser = avChooser
        self.textRolloverColor = Vec4(1, 1, 0, 1)
        self.textDownColor = Vec4(0.5, 0.9, 1, 1)
        self.textDisabledColor = Vec4(0.4, 0.8, 0.4, 1)
        self.descPos = (0.485, 0, -0.2)

    def unload(self):
        if not self.isLoaded:
            return
        self.isLoaded = False
        for btn in self.episodes:  # type: AnimatedButton
            btn.destroy()
        self.exit()
        DirectFrame.destroy(self)

    def load(self):
        if self.isLoaded:
            return
        self.isLoaded = True
        self.episodes = []
        self.descriptions = []
        self.thumbnails = []
        pos = Vec3(-0.7, 0, 0.27)
        for episode in EpisodeConfig.EPISODES:
            state = EpisodeConfig.EPISODES[episode].get('state')
            if state == EpisodeConfig.HIDDEN or (state == EpisodeConfig.DEV_OPEN and not __debug__):
                continue
            path = '/phase_3/maps/' + EpisodeConfig.EPISODES[episode].get('thumbnail', 'ttoff_t_gui_epThumb_unknown.png')
            thumb = PNMImage(path)
            thumb.addAlpha()
            thumbMask = PNMImage('/phase_3/maps/ttoff_t_gui_epThumb_mask.png')
            thumb.copyChannel(thumbMask, 0, 3)
            thumbMask.clear()
            del thumbMask
            image = Texture(f'episode{episode}')
            image.load(thumb)
            setattr(self, f'{episode}Thumb', image)
            episodeButton = AnimatedButton(parent = self,
                                           image = image,
                                           image_scale = (0.3, 1, 0.15),
                                           relief = None,
                                           textMayChange = 0,
                                           command = self.selectEpisode,
                                           extraArgs = [episode])
            episodeButton.setTransparency(TransparencyAttrib.MAlpha)
            episodeButton.setPos(pos)
            episodeButton.bind(DirectGuiGlobals.WITHIN, self.hoverEpisode, extraArgs = [episode])
            self.episodes.append(episodeButton)
            # Offset the position for the next item
            pos.addX(0.7)
            i = self.episodes.index(episodeButton)
            # Every 3 items we switch to a new row
            if not (i + 1) % 3:
                pos.setX(-0.7)
                pos.addZ(-0.35)

        self.nameLabel = DirectLabel(
                parent = self,
                relief = None,
                text = '',
                text_scale = 0.05,
                text_pos = TTLocalizer.DSDcancelPos,
                pos = (0, 0, -0.6),
                scale = 1.5
        )

        gui = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
        guiButton = loader.loadModel('phase_3/models/gui/quit_button')
        guiClose = loader.loadModel('phase_3.5/models/gui/avatar_panel_gui')
        self.cancel = DirectButton(parent = self, relief = None, image = (guiClose.find('**/CloseBtn_UP'),
                                                                          guiClose.find('**/CloseBtn_DN'),
                                                                          guiClose.find('**/CloseBtn_Rllvr'),
                                                                          guiClose.find('**/CloseBtn_UP')),
                                   pos = (0.98, 0, -0.65), scale = 1.5, command = self.__cancel)

        self.selectedEpisodeThumb = OnscreenImage(
                parent = hidden,
                image = 'phase_3/maps/ttoff_t_gui_epThumb_unknown.png',
                scale = (0.6, 1, 0.3),
                pos = (0, 0, .125)
        )
        self.descLabel = DirectLabel(
                parent = hidden,
                relief = None,
                text = '',
                text_scale = 0.035,
                text_pos = TTLocalizer.DSDcancelPos,
                text_align = TextNode.ACenter,
                text_wordwrap = 40.0,
                pos = (0, 0, -0.25),
                scale = 1.5
        )
        self.play = DirectButton(parent = hidden,
                                 relief = None,
                                 text = EpisodeLocalizer.EpisodePlay,
                                 image = (
                                     guiButton.find('**/QuitBtn_UP'),
                                     guiButton.find('**/QuitBtn_DN'),
                                     guiButton.find('**/QuitBtn_RLVR')),
                                 image_scale = (0.6, 1, 1),
                                 text_scale = TTLocalizer.DSDcancel,
                                 text_pos = TTLocalizer.DSDcancelPos,
                                 pos = (0, 0, -0.60),
                                 scale = 1.5)
        # self.scrollList.selectListItem(self.episodes[0])
        # self.selectEpisode('prologue')
        gui.removeNode()
        guiButton.removeNode()
        guiClose.removeNode()
        self.hide()

    def enter(self):
        if self.isEntered == 1:
            return
        self.isEntered = 1
        if self.isLoaded == 0:
            self.load()
        base.transitions.fadeScreen(0.5)
        self.show()
        if ClientSettings.GUIAnimations.get():
            ToontownGUIUtils.Animations.popup(self, self.getScale()).start()

    def exit(self):
        if self.isEntered == 0:
            return
        self.isEntered = 0
        base.transitions.noTransitions()
        self.ignoreAll()
        self.hide()

    def __cancel(self):
        self.exit()

    def hoverEpisode(self, episode, event):  # type: (str, None) -> None
        self.nameLabel['text'] = EpisodeConfig.EPISODES[episode].get('name')
        self.descLabel['text'] = EpisodeConfig.EPISODES[episode].get('desc')

    def selectEpisode(self, episode):
        # self.__handleEpisode(episode)
        for btn in self.episodes:  # type: AnimatedButton
            btn.reparentTo(hidden)

        self.nameLabel.reparentTo(hidden)
        self.descLabel.reparentTo(self)
        self['text'] = EpisodeConfig.EPISODES[episode].get('name')
        self.selectedEpisodeThumb.reparentTo(self)
        self.selectedEpisodeThumb['image'] = getattr(self, f'{episode}Thumb')
        self.selectedEpisodeThumb.setTransparency(TransparencyAttrib.MAlpha)
        self.play.reparentTo(self)
        self.play['command'] = self.__handleEpisode
        self.play['extraArgs'] = [episode]
        self.cancel['command'] = self.__backToMain

    def __backToMain(self):
        self.selectedEpisodeThumb.reparentTo(hidden)
        self.play.reparentTo(hidden)
        self.descLabel.reparentTo(hidden)
        self.nameLabel.reparentTo(self)
        self.cancel['command'] = self.__cancel
        self['text'] = TTLocalizer.AvatarChooserEpisodes
        for btn in self.episodes:  # type: AnimatedButton
            btn.reparentTo(self)

    def __handleEpisode(self, episode):
        self.unload()
        self.avChooser.handleEpisode(episode)
