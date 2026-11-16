from toontown.toonbase import TTLocalizer, ToontownGlobals
from toontown.hood import ZoneUtil

from . import TTStreet

visualizeZones = base.config.GetBool('visualize-zones', 0)


class TutorialStreet(TTStreet.TTStreet):

    def enter(self, requestStatus):
        TTStreet.TTStreet.enter(self, requestStatus, visibilityFlag=0, arrowsOn=0)
        base.cr.discordManager.setInfo(base.cr.discordManager.getState(),
                                       TTLocalizer.GlobalStreetNames.get(ToontownGlobals.TutorialHood)[2],
                                       ToontownGlobals.Zone2String.get(ToontownGlobals.ToontownCentral), None, None,
                                       None, ToontownGlobals.ToontownCentral)

    def exit(self):
        TTStreet.TTStreet.exit(self, visibilityFlag=0)

    def enterTeleportIn(self, requestStatus):
        TTStreet.TTStreet.enterTeleportIn(self, requestStatus)

    def enterTownBattle(self, event):
        self.loader.townBattle.enter(event, self.fsm.getStateNamed('battle'), tutorialFlag=1)

    def handleEnterTunnel(self, requestStatus, collEntry):
        messenger.send('stopTutorial')

        # Handle default zone
        cr = base.cr
        defaultZone = cr.moddingManager.getDefaultZone()
        if not cr.legitMode and defaultZone != ToontownGlobals.ToontownCentral:
            requestStatus['loader'] = ZoneUtil.getLoaderName(defaultZone)
            requestStatus['where'] = ZoneUtil.getToonWhereName(defaultZone)
            requestStatus['hoodId'] = ZoneUtil.getCanonicalHoodId(defaultZone)
            requestStatus['zoneId'] = ZoneUtil.getCanonicalZoneId(defaultZone)
            # This is necessary for the spawn points to be used
            base.queuedHood = ToontownGlobals.hood2Id[requestStatus['zoneId']][0]

        TTStreet.TTStreet.handleEnterTunnel(self, requestStatus, collEntry)

    def exitDoorIn(self):
        base.localAvatar.obscureMoveFurnitureButton(-1)

    def doEnterZone(self, newZoneId):
        if self.zoneId != None:
            for i in self.loader.nodeDict[self.zoneId]:
                if newZoneId:
                    if i not in self.loader.nodeDict[newZoneId]:
                        self.loader.fadeOutDict[i].start()
                        self.loader.exitAnimatedProps(i)
                else:
                    i.stash()
                    self.loader.exitAnimatedProps(i)

        if newZoneId != None:
            for i in self.loader.nodeDict[newZoneId]:
                if self.zoneId:
                    if i not in self.loader.nodeDict[self.zoneId]:
                        self.loader.fadeInDict[i].start()
                        self.loader.enterAnimatedProps(i)
                else:
                    if self.loader.fadeOutDict[i].isPlaying():
                        self.loader.fadeOutDict[i].finish()
                    if self.loader.fadeInDict[i].isPlaying():
                        self.loader.fadeInDict[i].finish()
                    self.loader.enterAnimatedProps(i)
                    i.unstash()

        if newZoneId != self.zoneId:
            if visualizeZones:
                if self.zoneId != None:
                    self.loader.zoneDict[self.zoneId].clearColor()
                if newZoneId != None:
                    self.loader.zoneDict[newZoneId].setColor(0, 0, 1, 1, 100)

            if newZoneId != None:
                self.notify.debug(f"doEnterZone(): hoodId={self.loader.hood.id}")
                self.notify.debug("doEnterZone(): Using Disney zone set logic for Tutorial.")
                base.cr.sendSetZoneMsg(newZoneId)
                self.notify.debug('Entering Zone %d' % newZoneId)

            self.zoneId = newZoneId

        geom = base.cr.playGame.getPlace().loader.geom
        self.halloweenLights = geom.findAllMatches('**/*light*')
        self.halloweenLights += geom.findAllMatches('**/*lamp*')
        self.halloweenLights += geom.findAllMatches('**/prop_snow_tree*')

        for light in self.halloweenLights:
            light.setColorScaleOff(1)
