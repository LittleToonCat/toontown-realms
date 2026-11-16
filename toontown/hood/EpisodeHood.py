from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State
from direct.gui import OnscreenText

from toontown.episodes import EpisodeConfig
from toontown.episodes import EpisodeLoader
from toontown.toonbase import TTLocalizer, ToontownGlobals
from . import Hood


class EpisodeHood(Hood.Hood):
    notify = DirectNotifyGlobal.directNotify.newCategory('EpisodeHood')

    def __init__(self, parentFSM, doneEvent, dnaStore, hoodId):
        Hood.Hood.__init__(self, parentFSM, doneEvent, dnaStore, hoodId)
        self.id = ToontownGlobals.Episode
        self.fsm = ClassicFSM.ClassicFSM('Hood', [State.State('start', self.enterStart, self.exitStart, ['episodeLoader']),
         State.State('episodeLoader', self.enterEpisodeLoader, self.exitEpisodeLoader, ['quietZone']),
         State.State('quietZone', self.enterQuietZone, self.exitQuietZone, ['episodeLoader']),
         State.State('final', self.enterFinal, self.exitFinal, [])], 'start', 'final')
        self.fsm.enterInitialState()
        self.episodeLoaderClass = EpisodeLoader.EpisodeLoader

    def load(self):
        pass

    def enter(self, requestStatus):
        zoneId = requestStatus['zoneId']
        hoodText = self.getHoodText(zoneId)
        if hoodText:
            self.titleText = OnscreenText.OnscreenText(hoodText, fg=self.titleColor, font=ToontownGlobals.getSignFont(),
                                                       pos=(0, -0.5), scale=TTLocalizer.HtitleText, drawOrder=0,
                                                       mayChange=1)
        self.fsm.request(requestStatus['loader'], [requestStatus])

    def getHoodText(self, zoneId):
        if base.cr.episodeManager.episodeZoneId:
            episodeZoneId = base.cr.episodeManager.episodeZoneId
            hoodText = EpisodeConfig.EPISODES.get(base.cr.episodeManager.episode).get('zoneId2String').get(episodeZoneId)
            if hoodText == '':
                return None
            hoodText = hoodText + '\n' + EpisodeConfig.EPISODES.get(base.cr.episodeManager.episode).get('zone2Subzone').get(hoodText)
            self.titleColor = EpisodeConfig.EPISODES.get(base.cr.episodeManager.episode).get('zoneTitleColors').get(episodeZoneId)
            return hoodText
        return None

    def loadLoader(self, requestStatus):
        loaderName = requestStatus['loader']
        if loaderName == 'episodeLoader':
            self.loader = self.episodeLoaderClass(self, self.fsm.getStateNamed('episodeLoader'), self.loaderDoneEvent)
            self.loader.load(requestStatus['zoneId'])

    def enterEpisodeLoader(self, requestStatus):
        self.accept(self.loaderDoneEvent, self.handleEpisodeLoaderDone)
        self.loader.enter(requestStatus)

    def exitEpisodeLoader(self):
        self.ignore(self.loaderDoneEvent)
        self.loader.exit()
        self.loader.unload()
        del self.loader

    def handleEpisodeLoaderDone(self):
        doneStatus = self.loader.getDoneStatus()
        if self.isSameHood(doneStatus):
            self.fsm.request('quietZone', [doneStatus])
        else:
            self.doneStatus = doneStatus
            messenger.send(self.doneEvent)
