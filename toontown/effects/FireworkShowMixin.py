from direct.directnotify import DirectNotifyGlobal
from direct.distributed.ClockDelta import *
from direct.interval.IntervalGlobal import *
from toontown.toonbase.ToontownGlobals import *
from . import Fireworks
from . import FireworkShows
from .FireworkGlobals import skyTransitionDuration, preShowPauseDuration, postShowPauseDuration, preNormalMusicPauseDuration
from toontown.effects.FireworkShow import FireworkShow, fireworkShowMessages, fireworkShowMusic


class FireworkShowMixin:
    notify = DirectNotifyGlobal.directNotify.newCategory('FireworkShowMixin')

    def __init__(self, restorePlaygroundMusic = True, startDelay = 0.0):
        self.currentShow = None
        self.restorePlaygroundMusic = restorePlaygroundMusic
        self.startDelay = startDelay
        self.timestamp = None
        self.fireworkShow = None
        self.eventId = JULY4_FIREWORKS
        # Continue music if audioManager is re-enabled
        self.accept('MusicEnabled', self.startMusic)
        # or if restored from minimize
        self.accept('PandaRestarted', self.startMusic)
        return

    def disable(self):
        if self.currentShow:
            self.currentShow.pause()
            self.currentShow = None
            if base.cr.config.GetBool('want-old-fireworks', 0):
                ivalMgr.finishIntervalsMatching('shootFirework*')
            else:
                self.destroyFireworkShow()
        from toontown.hood import DDHood
        if isinstance(self.getHood(), DDHood.DDHood):
            self.getHood().whiteFogColor = Vec4(0.8, 0.8, 0.8, 1)
        self.restoreCameraLens()
        if hasattr(self.getHood(), 'loader'):
            holidayIds = base.cr.newsManager.getDecorationHolidayId()
            if not (HALLOWEEN_COSTUMES in holidayIds or SPOOKY_COSTUMES in holidayIds) and not base.cr.playGame.hood.spookySkyFile:
                sky = None
                type = None
                if hasattr(base.cr.playGame.hood, 'sky'):
                    sky = base.cr.playGame.hood.sky
                if not sky:
                    try:
                        sky = render.find('**/party_skybox')
                        type = sky.getTag('sky')
                    except:
                        pass
                if type not in ('mml', 'ddl', 'hw', 'sbhq', 'sbhq2003', 'bbhq'):
                    self.getGeom().clearColorScale()
        if hasattr(self.getHood(), 'sky'):
            self.getSky().show()
            self.getSky().clearColorScale()
        if hasattr(base, 'localAvatar') and base.localAvatar:
            base.localAvatar.clearColorScale()
        base.setBackgroundColor(DefaultBackgroundColor)
        self.ignoreAll()
        return

    def startMusic(self):
        if self.timestamp:
            self.getLoader().music.stop()
            t = globalClockDelta.localElapsedTime(self.timestamp) - self.startDelay
            base.playMusic(self.showMusic, 0, 1, 0.8, max(0, t))

    def shootFirework(self, x, y, z, style, color1, color2):
        amp = 5
        Fireworks.shootFirework(style, x, y, z, color1, color2, amp)

    def runShow(self, eventId, style, timestamp, root = render):
        t = globalClockDelta.localElapsedTime(timestamp) - self.startDelay
        self.timestamp = timestamp
        self.showMusic = None
        self.eventId = eventId
        if base.config.GetBool('want-old-fireworks', 0):
            self.currentShow = self.getFireworkShowIval(eventId, style, t)
            if self.currentShow:
                self.currentShow.start(t)
        else:
            self.createFireworkShow()
            if t > self.fireworkShow.getShowDuration():
                return
            preShow = self.preShow(eventId, t)
            postShow = self.postShow(eventId)
            beginFireworkShow = Func(self.beginFireworkShow, max(0, t), root)
            self.currentShow = Sequence(preShow, beginFireworkShow, Wait(max(0, self.fireworkShow.getShowDuration() - max(0, t))), postShow)
            self.currentShow.start()
        return

    def preShow(self, eventId, startT):
        showMessages = fireworkShowMessages.get(eventId)
        if not showMessages:
            FireworkShowMixin.notify.error('Invalid fireworks event ID: %d' % eventId)
        instructionMessage = showMessages['instructions']
        startMessage = showMessages['start']
        musicFile = fireworkShowMusic[eventId]
        self.showMusic = loader.loadMusic(musicFile)
        self.showMusic.setVolume(1)

        def __lightDecorationOn__():
            place = base.cr.playGame.getPlace()
            if place is None:
                return
            if hasattr(place, 'halloweenLights'):
                if not self.__checkStreetValidity():
                    return
                else:
                    place.halloweenLights = list(base.cr.playGame.getPlace().loader.geom.findAllMatches('**/*light*'))
                    place.halloweenLights.extend(list(base.cr.playGame.getPlace().loader.geom.findAllMatches('**/*lamp*')))
                    for light in place.halloweenLights:
                        light.setColorScaleOff(0)
            elif not self.__checkHoodValidity():
                return
            else:
                if hasattr(place, 'halloweenLights'):
                    place.loader.hood.halloweenLights = base.cr.playGame.hood.loader.geom.findAllMatches('**/*light*').asList()
                    place.loader.hood.halloweenLights.extend(base.cr.playGame.hood.loader.geom.findAllMatches('**/*lamp*').asList())
                    for light in base.cr.playGame.hood.halloweenLights:
                        light.setColorScaleOff(0)

            if self.fireworkShow and not self.fireworkShow.isEmpty():
                self.fireworkShow.setColorScaleOff(0)
            return

        sky = None
        if hasattr(base.cr.playGame.hood, 'sky'):
            sky = base.cr.playGame.hood.sky
        if not sky:
            try:
                sky = render.find('**/party_skybox')
            except:
                pass

        if self.__checkHoodValidity() and hasattr(base.cr.playGame, 'hood') and base.cr.playGame.hood and sky:
            preShow = Sequence(Func(base.localAvatar.setSystemMessage, 0, startMessage),
                               Parallel(LerpColorScaleInterval(sky, 2.5, Vec4(0.0, 0.0, 0.0, 1.0)),
                                        LerpColorScaleInterval(base.cr.playGame.hood.loader.geom, 2.5,
                                                               Vec4(0.25, 0.25, 0.35, 1)),
                                        LerpColorScaleInterval(base.localAvatar, 2.5, Vec4(0.85, 0.85, 0.85, 1)),
                                        Func(__lightDecorationOn__)),
                               Func(base.setBackgroundColor, Vec4(0, 0, 0, 1)), Func(self.__checkDDFog),
                               Func(base.camLens.setFar, 1000.0), Func(sky.hide),
                               Func(base.localAvatar.setSystemMessage, 0, instructionMessage),
                               Func(self.getLoader().music.stop), Wait(2.0),
                               Func(base.playMusic, self.showMusic, 0, 1, 0.8, max(0, startT)))
            return preShow
        elif self.__checkHoodValidity() and hasattr(base.cr.playGame, 'hood') and base.cr.playGame.hood:
            preShow = Sequence(Func(base.localAvatar.setSystemMessage, 0, startMessage),
                               Parallel(LerpColorScaleInterval(base.cr.playGame.hood.loader.geom, 2.5,
                                                               Vec4(0.25, 0.25, 0.35, 1)),
                                        LerpColorScaleInterval(base.localAvatar, 2.5, Vec4(0.85, 0.85, 0.85, 1)),
                                        Func(__lightDecorationOn__)),
                               Func(base.setBackgroundColor, Vec4(0, 0, 0, 1)), Func(self.__checkDDFog),
                               Func(base.camLens.setFar, 1000.0),
                               Func(base.localAvatar.setSystemMessage, 0, instructionMessage),
                               Func(self.getLoader().music.stop), Wait(2.0),
                               Func(base.playMusic, self.showMusic, 0, 1, 0.8, max(0, startT)))
            return preShow
        return None

    def restoreCameraLens(self):
        hood = self.getHood()
        from toontown.hood import GSHood, OZHood, PartyHood
        if isinstance(hood, OZHood.OZHood):
            base.camLens.setFar(SpeedwayCameraFar)
        elif isinstance(hood, GSHood.GSHood):
            base.camLens.setFar(SpeedwayCameraFar)
        elif isinstance(hood, PartyHood.PartyHood):
            base.camLens.setFar(PartyCameraFar)
        else:
            base.camLens.setFar(DefaultCameraFar)

    def postShow(self, eventId):
        showMessages = fireworkShowMessages.get(eventId)
        if not showMessages:
            FireworkShowMixin.notify.error('Invalid fireworks event ID: %d' % eventId)
        endMessage = showMessages['end']

        sky = None
        type = None
        if hasattr(base.cr.playGame.hood, 'sky'):
            sky = base.cr.playGame.hood.sky
        if not sky:
            try:
                sky = render.find('**/party_skybox')
                type = sky.getTag('sky')
            except:
                pass

        colors = Vec4(1, 1, 1, 1)
        holidayIds = base.cr.newsManager.getDecorationHolidayId()
        if type == 'mml':
            colors = Vec4(1.0, 0.95, 0.85, 1.0)
        elif type in ('ddl', 'sbhq', 'sbhq2003', 'bbhq'):
            colors = Vec4(0.7, 0.7, 0.7, 1.0)
        elif type == 'hw':
            colors = Vec4(0.55, 0.55, 0.65, 1.0)
        elif (HALLOWEEN_COSTUMES in holidayIds or SPOOKY_COSTUMES in holidayIds) and base.cr.playGame.hood.spookySkyFile:
            colors = Vec4(0.55, 0.55, 0.65, 1.0)
        if self.__checkHoodValidity() and sky:
            postShow = Sequence(Func(sky.show), Parallel(LerpColorScaleInterval(sky, 2.5, Vec4(1, 1, 1, 1)),
                                                         LerpColorScaleInterval(base.cr.playGame.hood.loader.geom, 2.5,
                                                                                colors),
                                                         LerpColorScaleInterval(base.localAvatar, 2.5,
                                                                                Vec4(1, 1, 1, 1))),
                                Func(self.__restoreDDFog), Func(self.restoreCameraLens),
                                Func(base.setBackgroundColor, DefaultBackgroundColor), Func(self.showMusic.stop),
                                Func(base.localAvatar.setSystemMessage, 0, endMessage))
        elif self.__checkHoodValidity():
            postShow = Sequence(Parallel(LerpColorScaleInterval(base.cr.playGame.hood.loader.geom, 2.5, colors),
                                         LerpColorScaleInterval(base.localAvatar, 2.5, Vec4(1, 1, 1, 1))),
                                Func(self.__restoreDDFog), Func(self.restoreCameraLens),
                                Func(base.setBackgroundColor, DefaultBackgroundColor), Func(self.showMusic.stop),
                                Func(base.localAvatar.setSystemMessage, 0, endMessage))
        if self.restorePlaygroundMusic:
            postShow.append(Wait(2.0))
            postShow.append(Func(base.playMusic, self.getLoader().music, 1, 1, 0.8))
        return postShow

    def createFireworkShow(self):
        if not self.fireworkShow:
            self.fireworkShow = FireworkShow(self.eventId)

    def destroyFireworkShow(self):
        if self.fireworkShow:
            self.fireworkShow.cleanupShow()
            self.fireworkShow = None
        return

    def beginFireworkShow(self, timeStamp, root):
        if self.fireworkShow and not self.fireworkShow.isPlaying():
            self.fireworkShow.begin(timeStamp)
            self.fireworkShow.reparentTo(root)
            from toontown.hood import TTHood, BRHood, MMHood, DGHood, DLHood, GSHood, DDHood, OZHood, PartyHood
            hood = self.getHood()

            from toontown.hood import TTHood, DDHood, BRHood, MMHood, DGHood, DLHood, GSHood, OZHood

            if isinstance(hood, TTHood.TTHood):
                self.fireworkShow.setPos(150, 0, 80)
                self.fireworkShow.setHpr(90, 0, 0)
            elif isinstance(hood, BRHood.BRHood):
                self.fireworkShow.setPos(-200, -60, 50)
                self.fireworkShow.setHpr(270, 0, 0)
            elif isinstance(hood, MMHood.MMHood):
                self.fireworkShow.setPos(150, -25, 40)
                self.fireworkShow.setHpr(90, 0, 0)
            elif isinstance(hood, DGHood.DGHood):
                self.fireworkShow.setPos(-80, -50, 60)
                self.fireworkShow.setHpr(0, 0, 0)
            elif isinstance(hood, DLHood.DLHood):
                self.fireworkShow.setPos(-160, 0, 80)
                self.fireworkShow.setHpr(270, 0, 0)
            elif isinstance(hood, GSHood.GSHood):
                self.fireworkShow.setPos(60, -350, 80)
                self.fireworkShow.setHpr(20, 0, 0)
            elif isinstance(hood, DDHood.DDHood):
                self.fireworkShow.setPos(150, 0, 50)
                self.fireworkShow.setHpr(90, 0, 0)
            elif isinstance(hood, OZHood.OZHood):
                self.fireworkShow.setPos(-450, -80, 140)
                self.fireworkShow.setHpr(300, 0, 0)
            elif isinstance(hood, PartyHood.PartyHood):
                self.fireworkShow.setPos(0, -400, 120)
                self.fireworkShow.lookAt(0, 0, 0)
                self.fireworkShow.setScale(1.8)

    def getFireworkShowIval(self, eventId, index, startT):
        show = FireworkShows.getShow(eventId, index)
        if show is None:
            FireworkShowMixin.notify.warning('could not find firework show: index: %s' % index)
            return
        preShow = self.preShow(eventId, startT)
        mainShow = Sequence()
        currentT = skyTransitionDuration + preShowPauseDuration
        for effect in show:
            waitTime, style, colorIndex1, colorIndex2, amp, x, y, z = effect
            if waitTime > 0:
                currentT += waitTime
                mainShow.append(Wait(waitTime))
            if currentT >= startT:
                mainShow.append(Func(Fireworks.shootFirework, style, x, y, z, colorIndex1, colorIndex2, amp))

        postShow = self.postShow(eventId)
        return Sequence(preShow, mainShow, postShow)

    def clearMyColorScales(self):
        if self.getGeom() and not self.getGeom().isEmpty():
            self.getGeom().clearColorScale()
        if self.getSky() and not self.getSky().isEmpty():
            self.getSky().clearColorScale()

    def getLoader(self):
        if base.cr.playGame.hood != None:
            return base.cr.playGame.hood.loader
        return

    def getHood(self):
        if base.cr.playGame.hood != None:
            return base.cr.playGame.hood
        return

    def getGeom(self):
        loader = self.getLoader()
        if loader:
            return loader.geom
        return None

    def getSky(self):
        hood = self.getHood()
        if hood:
            return hood.sky
        return None

    def __checkDDFog(self):
        from toontown.hood import DDHood
        if isinstance(self.getHood(), DDHood.DDHood):
            self.getHood().whiteFogColor = Vec4(0.2, 0.2, 0.2, 1)
            if hasattr(base.cr.playGame.getPlace(), 'cameraSubmerged'):
                if not base.cr.playGame.getPlace().cameraSubmerged:
                    self.getHood().setDDFog()

    def __restoreDDFog(self):
        from toontown.hood import DDHood
        if isinstance(self.getHood(), DDHood.DDHood):
            self.getHood().whiteFogColor = Vec4(0.8, 0.8, 0.8, 1)
            if hasattr(base.cr.playGame.getPlace(), 'cameraSubmerged'):
                if not base.cr.playGame.getPlace().cameraSubmerged:
                    self.getHood().setDDFog()

    def __checkStreetValidity(self):
        if hasattr(base.cr.playGame, 'getPlace') and base.cr.playGame.getPlace() and hasattr(base.cr.playGame.getPlace(), 'loader') and base.cr.playGame.getPlace().loader and hasattr(base.cr.playGame.getPlace().loader, 'geom') and base.cr.playGame.getPlace().loader.geom:
            return True
        else:
            return False

    def __checkHoodValidity(self):
        if hasattr(base.cr.playGame, 'hood') and base.cr.playGame.hood and hasattr(base.cr.playGame.hood, 'loader') and base.cr.playGame.hood.loader and hasattr(base.cr.playGame.hood.loader, 'geom') and base.cr.playGame.hood.loader.geom:
            return True
        else:
            return False
