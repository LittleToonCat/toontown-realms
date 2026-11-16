from . import ShtikerPage
from toontown.toonbase import ToontownGlobals, ClientSettings
from otp.otpbase import PythonUtil
from toontown.hood import ZoneUtil
from direct.gui.DirectGui import *
from panda3d.core import *
from toontown.toonbase import TTLocalizer
from toontown.toontowngui import TTDialog
from ..toontowngui.AnimatedButton import AnimatedButton


class MapPage(ShtikerPage.ShtikerPage):

    def __init__(self):
        ShtikerPage.ShtikerPage.__init__(self)

    def load(self):
        ShtikerPage.ShtikerPage.load(self)

        # Config option for Retro Mode
        updatedMap = ClientSettings.UpdatedMap.get()

        if updatedMap:
            mapModel = loader.loadModel('phase_3.5/models/gui/toontown_map')
            imageScale = (1.8 * 1.1, 1.1, 1.35 * 1.1)
        else:
            mapModel = loader.loadModel('phase_3.5/models/gui/toontown_map_retro')
            imageScale = (1.8, 1.1, 1.35)

        self.map = DirectFrame(parent=self, relief=None, image=mapModel.find('**/toontown_map'), image_scale=imageScale, scale=0.97, pos=(0, 0, 0.0775))
        mapModel.removeNode()

        self.allZones = []

        hoods = list(ToontownGlobals.Hoods)

        # Add these two zones just to get them working on the map
        # When SOS comes out, they will turn into normally functioning zones on the map
        # For now, they're just for show
        # But when SOS comes out we will have to find a way to integrate these locations into the Retro Mode Map
        if updatedMap:
            hoods.append(ToontownGlobals.Duckburg)
            hoods.append(ToontownGlobals.Scrapyards)

        excludedHoods = [ToontownGlobals.GolfZone, ToontownGlobals.FunnyFarm, ToontownGlobals.ToontownOutskirts,
                         ToontownGlobals.ToontownCentralBeta, ToontownGlobals.DaisyGardensBeta,
                         ToontownGlobals.MinniesMelodylandBeta, ToontownGlobals.DonaldsDreamlandBeta,
                         ToontownGlobals.TheBrrrghBeta, ToontownGlobals.DonaldsDockBeta, ToontownGlobals.ToontownSkies,ToontownGlobals.ToonLandFunnyFarm]

        # Append all hoods except for these
        for hood in hoods:
            if hood not in excludedHoods:
                self.allZones.append(hood)

        if updatedMap:
            self.cloudScaleList = (((-0.275, 0, 0.25), (0.325, 0, 0.3), (-0.4, 0, 0.35), (-0.35, 0, 0.375), (0.325, 0, 0.25), (-0.25, 0, 0.225)),
                                   (),
                                   ((-0.4, 0.0, 0.275), (0.375, 0.0, 0.35), (-0.4, 0.0, 0.275), (0.4, 0.0, 0.4), (0.275, 0, 0.25)),
                                   ((0.375, 0.0, 0.35), (0.45, 0.0, 0.4), (0.325, 0.0, 0.225), (-0.4, 0.0, 0.375), (-0.35, 0.0, 0.275)),
                                   ((0.35, 0.0, 0.3), (-0.45, 0.0, 0.3), (0.25, 0.0, 0.2)),
                                   ((0.4, 0.0, 0.25), (0.4, 0.0, 0.35), (-0.375, 0.0, 0.325), (0.375, 0.0, 0.325), (0.375, 0.0, 0.325)),
                                   ((0.25, 0.0, 0.225), (0.25, 0.0, 0.265), (0.275, 0.0, 0.25)),
                                   ((-0.4, 0.0, 0.275), (0.4, 0.0, 0.375), (-0.35, 0.0, 0.3), (0.425, 0.0, 0.275)),
                                   ((0.325, 0, 0.3), (0.375, 0, 0.4), (-0.35, 0, 0.4), (-0.3, 0, 0.25)),
                                   ((0.3, 0.0, 0.25), (0.35, 0.0, 0.3), (-0.35, 0.0, 0.3)),
                                   ((0.4, 0, 0.325), (0.375, 0, 0.425), (0.4, 0, 0.325), (0.535, 0, 0.325)),
                                   ((-0.35, 0, 0.4), (0.475, 0, 0.375), (-0.35, 0, 0.325)),
                                   ((0.35, 0.0, 0.35), (-0.35, 0.0, 0.325), (0.3, 0.0, 0.225), (0.2, 0.0, 0.15)),
                                   ((0.35, 0.0, 0.3), (-0.275, 0.0, 0.225), (-0.3, 0.0, 0.225)))
            self.cloudPosList = (((-0.7, 0.0, 0.15), (-0.695, 0.0, 0.33), (-0.425, 0.0, 0.075), (-0.55, 0.0, 0.1), (-0.425, 0.0, 0.14), (-0.315, 0.0, 0.16)),
                                 (),
                                 ((-0.34, 0.0, -0.17), (-0.69, 0.0, -0.15), (-0.68, 0.0, 0.0), (-0.5, 0.0, -0.2), (-0.25, 0.0, -0.1)),
                                 ((0.3, 0.0, -0.4), (0.0, 0.0, -0.425), (0.15, 0.0, -0.35), (-0.225, 0.0, -0.375), (-0.05, 0.0, -0.28)),
                                 ((0.38, 0.0, 0.14), (0.35, 0.0, 0.3), (0.475, 0.0, 0.2)),
                                 ((-0.5, 0.0, 0.575), (-0.45, 0.0, 0.4), (-0.635, 0.0, 0.5), (-0.325, 0.0, 0.5), (-0.2, 0.0, 0.325)),
                                 ((-0.2, 0.0, 0.2), (0.1, 0.0, 0.24), (-0.05, 0.0, 0.235)),
                                 ((0.635, 0.0, -0.1), (0.45, 0.0, -0.135), (0.225, 0.0, -0.155), (0.3, 0.0, -0.1)),
                                 ((-0.1, 0.0, 0.535), (0.0, 0.0, 0.475), (0.15, 0.0, 0.5), (-0.145, 0.0, 0.56)),
                                 ((0.615, 0.0, 0.375), (0.73, 0.0, 0.425), (0.685, 0.0, 0.315)),
                                 ((0.725, 0.0, -0.275), (0.735, 0.0, -0.39), (0.5, 0.0, -0.425), (0.65, 0.0, -0.3)),
                                 ((-0.7, 0.0, -0.485), (-0.56, 0.0, -0.475), (-0.7, 0.0, -0.335)),
                                 ((0.475, 0.0, 0.5), (0.325, 0.0, 0.525), (0.585, 0.0, 0.55), (0.68, 0.0, 0.59)),
                                 ((0.725, 0.0, 0.075), (0.775, 0.0, -0.075), (0.65, 0.0, 0.1)))
            self.labelPosList = ((-0.525, 0.0, 0.145),
                                 (-0.025, 0.0, 0.0),
                                 (-0.47, 0.0, -0.175),
                                 (-0.025, 0.0, -0.38),
                                 (0.375, 0.0, 0.2),
                                 (-0.4, 0.0, 0.42),
                                 (0.0, 0.0, 0.2),
                                 (0.45, 0.0, -0.1),
                                 (0.05, 0.0, 0.5),
                                 (0.68, 0.0, 0.38),
                                 (0.685, 0.0, -0.4),
                                 (-0.675, 0.0, -0.5),
                                 (0.475, 0.0, 0.5),
                                 (0.73, 0.0, 0.075))
        else:
            self.cloudScaleList = (((0.55, 0, 0.4), (0.35, 0, 0.25)),
                                   (),
                                   ((0.45, 0, 0.45), (0.5, 0, 0.4),),
                                   ((0.7, 0, 0.45),),
                                   ((0.55, 0, 0.4),),
                                   ((0.6, 0, 0.4), (0.5332, 0, 0.32)),
                                   ((0.7, 0, 0.45), (0.7, 0, 0.45),),
                                   ((0.7998, 0, 0.39),),
                                   ((0.5, 0, 0.4),),  # boss
                                   ((-0.45, 0, 0.4),),  # sell
                                   ((-0.45, 0, 0.35),),  # cash
                                   ((0.5, 0, 0.35),),  # law
                                   ((0.5, 0, 0.35),),  # golf
                                   )
            self.cloudPosList = (((0.575, 0., -0.04), (0.45, 0., -0.25)),
                                 (),
                                 ((0.375, 0., 0.4), (0.5625, 0., 0.2)),
                                 ((-0.02, 0., 0.23),),
                                 ((-0.3, 0., -0.4),),
                                 ((0.25, 0., -0.425), (0.125, 0., -0.36)),
                                 ((-0.5625, 0., -0.07), (-0.45, 0., 0.2125),),
                                 ((-0.125, 0., 0.5),),
                                 ((0.66, 0., -0.4),),  # boss
                                 ((-0.68, 0., -0.444),),  # sell
                                 ((-0.6, 0., 0.45),),  # cash
                                 ((0.66, 0., 0.5),),  # law
                                 ((0.40, 0., -0.35),),  # golf
                                 )
            self.labelPosList = ((0.594, 0., -0.075),
                                 (0., 0., -0.1),
                                 (0.475, 0., 0.25),
                                 (0.1, 0., 0.15),
                                 (-0.3, 0., -0.375),
                                 (0.2, 0., -0.45),
                                 (-0.55, 0., 0.0),
                                 (-0.088, 0., 0.47),
                                 (0.7, 0., -0.5),  # Bossbot HQ
                                 (-0.7, 0., -0.5),  # Sellbot HQ
                                 (-0.7, 0., 0.5),  # Cashbot HQ
                                 (0.7, 0., 0.5),  # Lawbot HQ
                                 (0.45, 0., -0.45),  # golf zone
                                 )

        self.labels = []
        self.clouds = []

        guiButton = loader.loadModel('phase_3/models/gui/quit_button')

        buttonLoc = (0.45, 0, - 0.74)
        if base.housingEnabled:
            buttonLoc = (0.55, 0, -0.74)

        self.safeZoneButton = DirectButton(
            parent=self.map,
            relief=None,
            image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')),
            image_scale=(1.3, 1.1, 1.1),
            pos=buttonLoc,
            text=TTLocalizer.MapPageBackToPlayground,
            text_scale=TTLocalizer.MPsafeZoneButton,
            text_pos=(0, -0.02),
            textMayChange=0,
            command=self.backToSafeZone)

        self.goHomeButton = DirectButton(
            parent=self.map,
            relief=None,
            image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')),
            image_scale=(0.66, 1.1, 1.1),
            pos=(0.15, 0, -.74),
            text=TTLocalizer.MapPageGoHome,
            text_scale=TTLocalizer.MPgoHomeButton,
            text_pos=(0, -0.02),
            textMayChange=0,
            command=self.goHome)
        self.goHomeButton.hide()

        guiButton.removeNode()

        textScale = TTLocalizer.MPhoodLabel
        if not updatedMap:
            textScale = TTLocalizer.MPhoodLabelRetro
        self.hoodLabel = DirectLabel(parent=self.map, relief=None, pos=(-0.43, 0, -0.726), text='',
                                     text_scale=textScale, text_pos=(0, 0), text_wordwrap=TTLocalizer.MPhoodLabelWordwrap)
        self.hoodLabel.hide()

        cloudModel = loader.loadModel('phase_3.5/models/gui/cloud')
        cloudImage = cloudModel.find('**/cloud')

        for hood in self.allZones:
            abbrev = base.cr.hoodMgr.getNameFromId(hood)
            fullname = base.cr.hoodMgr.getFullnameFromId(hood)
            hoodIndex = self.allZones.index(hood)
            label = AnimatedButton(
                parent=self.map,
                relief=None,
                pos=self.labelPosList[hoodIndex],
                pad=(0.2, 0.16),
                text=('', fullname, fullname),
                text_bg=Vec4(1, 1, 1, 0.4),
                text_scale=0.055,
                text_wordwrap=8,
                rolloverSound=None,
                clickSound=None,
                pressEffect=0,
                command=self.__buttonCallback,
                extraArgs=[hood],
                sortOrder=1)
            label.bind(DGG.WITHIN, self.__hoverCallback, extraArgs=[1, hoodIndex])
            label.bind(DGG.WITHOUT, self.__hoverCallback, extraArgs=[0, hoodIndex])
            label.resetFrameSize()
            self.labels.append(label)
            hoodClouds = []
            for cloudScale, cloudPos in zip(self.cloudScaleList[hoodIndex], self.cloudPosList[hoodIndex]):
                cloud = DirectFrame(
                    parent=self.map,
                    relief=None,
                    state=DGG.DISABLED,
                    image=cloudImage,
                    scale=(cloudScale[0], cloudScale[1], cloudScale[2]),
                    pos=(cloudPos[0], cloudPos[1], cloudPos[2]))
                cloud.hide()
                hoodClouds.append(cloud)

            self.clouds.append(hoodClouds)

        cloudModel.removeNode()
        self.resetFrameSize()
        return

    def unload(self):
        for labelButton in self.labels:
            labelButton.destroy()

        del self.labels
        del self.clouds
        self.safeZoneButton.destroy()
        self.goHomeButton.destroy()
        ShtikerPage.ShtikerPage.unload(self)

    def enter(self):
        ShtikerPage.ShtikerPage.enter(self)
        try:
            zone = base.cr.playGame.getPlace().getZoneId()
        except:
            zone = 0

        if base.localAvatar.lastHood >= ToontownGlobals.BossbotHQ:
            self.safeZoneButton['text'] = TTLocalizer.MapPageBackToCogHQ
        else:
            self.safeZoneButton['text'] = TTLocalizer.MapPageBackToPlayground
        if zone and ZoneUtil.isPlayground(zone) or self.book.safeMode:
            self.safeZoneButton.hide()
        else:
            self.safeZoneButton.show()
        if base.cr.playGame.getPlaceId() == ToontownGlobals.MyEstate and base.cr.playGame.hood.loader.atMyEstate() or self.book.safeMode:
            self.goHomeButton.hide()
        elif base.housingEnabled:
            self.goHomeButton.show()
        if base.cr.playGame.getPlaceId() == ToontownGlobals.MyEstate:
            if base.cr.playGame.hood.loader.atMyEstate():
                self.hoodLabel['text'] = TTLocalizer.MapPageYouAreAtHome
                self.hoodLabel.show()
            else:
                avatar = base.cr.identifyAvatar(base.cr.playGame.hood.loader.estateOwnerId)
                if avatar:
                    avName = avatar.getName()
                    self.hoodLabel['text'] = TTLocalizer.MapPageYouAreAtSomeonesHome % TTLocalizer.GetPossesive(avName)
                    self.hoodLabel.show()
        elif zone:
            hoodName = ToontownGlobals.hoodNameMap.get(ZoneUtil.getCanonicalHoodId(zone), ('',))[-1]
            streetName = ToontownGlobals.StreetNames.get(ZoneUtil.getCanonicalBranchZone(zone), ('',))[-1]
            if hoodName:
                self.hoodLabel['text'] = TTLocalizer.MapPageYouAreHere % (hoodName, streetName)
                self.hoodLabel.show()
            elif base.cr.playGame.getPlaceId() == ToontownGlobals.PartyHood:
                if base.cr.playGame.hood.loader.atMyParty():
                    self.hoodLabel['text'] = TTLocalizer.MapPageYouAreAtYourParty
                    self.hoodLabel.show()
                else:
                    if hasattr(base, 'distributedParty') and base.distributedParty:
                        hostName = base.distributedParty.hostName
                        self.hoodLabel['text'] = TTLocalizer.MapPageYouAreAtSomeonesParty % TTLocalizer.GetPossesive(hostName)
                        self.hoodLabel.show()
        else:
            self.hoodLabel.hide()
        safeZonesVisited = base.localAvatar.hoodsVisited
        hoodsAvailable = base.cr.hoodMgr.getAvailableZones()
        hoodVisibleList = PythonUtil.intersection(safeZonesVisited, hoodsAvailable)
        hoodTeleportList = base.localAvatar.getTeleportAccess()
        for hood in self.allZones:
            label = self.labels[self.allZones.index(hood)]
            clouds = self.clouds[self.allZones.index(hood)]
            if not self.book.safeMode and (hood in hoodVisibleList or (hood == ToontownGlobals.Duckburg and base.localAvatar.isEpisodeComplete('prologue'))):
                label['text_fg'] = (0, 0, 0, 1)
                label.show()
                for cloud in clouds:
                    cloud.hide()

                fullname = base.cr.hoodMgr.getFullnameFromId(hood)
                if hood in hoodTeleportList:
                    text = TTLocalizer.MapPageGoTo % fullname
                    label['text'] = ('', text, text)
                else:
                    label['text'] = ('', fullname, fullname)
            else:
                label['text_fg'] = (0, 0, 0, 0.65)
                label.show()
                for cloud in clouds:
                    cloud.show()

    def exit(self):
        ShtikerPage.ShtikerPage.exit(self)

    def backToSafeZone(self):
        self.doneStatus = {'mode': 'teleport',
         'hood': base.localAvatar.lastHood}
        messenger.send(self.doneEvent)

    def goHome(self):
        if base.config.GetBool('want-qa-regression', 0):
            self.notify.info('QA-REGRESSION: VISITESTATE: Visit estate')
        self.doneStatus = {'mode': 'gohome',
         'hood': base.localAvatar.lastHood}
        messenger.send(self.doneEvent)

    def __buttonCallback(self, hood):
        if hood in base.localAvatar.getTeleportAccess() and hood in base.cr.hoodMgr.getAvailableZones():
            base.localAvatar.sendUpdate('checkTeleportAccess', [hood])
            self.doneStatus = {'mode': 'teleport',
             'hood': hood}
            messenger.send(self.doneEvent)
        elif hood == ToontownGlobals.Duckburg:
            self.__handleNoticeShow(TTLocalizer.MapPageNoticeDuckburg)
        elif hood == ToontownGlobals.Scrapyards:
            self.__handleNoticeShow(TTLocalizer.MapPageNoticeScrapyards)

    def __handleNoticeShow(self, message):
        doneEvent = 'noticeAcknowledge'
        self.notice = TTDialog.TTGlobalDialog(doneEvent=doneEvent, message=message, style=TTDialog.Acknowledge)
        self.notice.show()
        self.accept(doneEvent, self.__handleAcknowledge)

    def __handleAcknowledge(self):
        self.ignore('noticeAcknowledge')
        self.notice.cleanup()
        del self.notice

    def __hoverCallback(self, inside, hoodIndex, pos):
        alpha = PythonUtil.choice(inside, 0.25, 1.0)
        try:
            clouds = self.clouds[hoodIndex]
        except ValueError:
            clouds = []

        for cloud in clouds:
            cloud.setColor((1,
             1,
             1,
             alpha))
