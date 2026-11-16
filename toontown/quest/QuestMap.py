import math

from direct.gui import DirectGuiGlobals
from panda3d.core import CardMaker, Vec2
from direct.gui.DirectGui import DirectFrame, DirectLabel, DirectButton
from toontown.toon import NPCToons
from toontown.hood import ZoneUtil
from toontown.toonbase import ToontownGlobals, ClientSettings, HotkeySettings
from toontown.quest import Quests
from . import QuestMapGlobals
from .QuestMapGlobals import getIconNodeName, LandmarkPosTable, isZoneIcon
from ..toon.DistributedToon import DistributedToon
from ..toontowngui.AnimatedButton import AnimatedButton


class QuestMap(DirectFrame):
    laffMeterGui = loader.loadModel('phase_3/models/gui/laff_o_meter', allowInstance = True)

    def __init__(self, av):
        DirectFrame.__init__(self, relief = None, sortOrder = 50)
        self.initialiseoptions(QuestMap)
        self.container = DirectFrame(parent = self, relief = None)
        self.marker = DirectFrame(parent = self.container, relief = None)
        self.cogInfoFrame = DirectFrame(parent = self.container, relief = None)
        cm = CardMaker('bg')
        cm.setFrame(-0.5, 0.5, -0.5, 0.5)
        bg = self.cogInfoFrame.attachNewNode(cm.generate())
        bg.setTransparency(1)
        bg.setColor(0.5, 0.5, 0.5, 0.5)
        bg.setBin('fixed', 0)
        self.cogInfoFrame['geom'] = bg
        self.cogInfoFrame['geom_pos'] = (0, 0, 0)
        self.cogInfoFrame['geom_scale'] = (6, 1, 2)
        self.cogInfoFrame.setScale(0.05)
        self.cogInfoFrame.setPos(0, 0, 0.6)
        self.avMarkers = {}
        self.buildingMarkers = []
        self.landmarkMarkers = []
        self.av = av
        self.wantToggle = False
        if base.config.GetBool('want-toggle-quest-map', True):
            self.wantToggle = True
        self.updateMarker = True
        self.cornerPosInfo = None
        self.hqPosInfo = None
        self.gyroPosInfo = None
        self.fishingSpotInfo = None
        self.load()
        self.setScale(1.5)
        bg.removeNode()
        self.hoodId = None
        self.zoneId = None

    def load(self):
        gui = loader.loadModel('phase_4/models/questmap/questmap_gui')
        icon = gui.find('**/tt_t_gui_qst_arrow')
        iconNP = aspect2d.attachNewNode('iconNP')
        icon.reparentTo(iconNP)
        icon.setR(90)
        self.marker['geom'] = iconNP
        self.marker['image'] = iconNP
        self.marker.setScale(0.05)
        iconNP.removeNode()
        gui.removeNode()
        icons = loader.loadModel('phase_3/models/gui/cog_icons')
        cIcon = icons.find('**/CorpIcon')
        lIcon = icons.find('**/LegalIcon')
        mIcon = icons.find('**/MoneyIcon')
        sIcon = icons.find('**/SalesIcon')
        cogInfoTextColor = (0.2, 0.2, 0.2, 1)
        textPos = (1.2, -0.2)
        textScale = 0.8
        self.cInfo = DirectLabel(parent = self.cogInfoFrame, text = '', text_fg = cogInfoTextColor, text_pos = textPos,
                                 text_scale = textScale, geom = cIcon, geom_pos = (-0.2, 0, 0), geom_scale = 0.8,
                                 relief = None)
        self.cInfo.setPos(-2.2, 0, 0.5)
        self.lInfo = DirectLabel(parent = self.cogInfoFrame, text_fg = cogInfoTextColor, text = '', text_pos = textPos,
                                 text_scale = textScale, geom = lIcon, geom_pos = (-0.2, 0, 0), geom_scale = 0.8,
                                 relief = None)
        self.lInfo.setPos(-2.2, 0, -0.5)
        self.mInfo = DirectLabel(parent = self.cogInfoFrame, text_fg = cogInfoTextColor, text = '', text_pos = textPos,
                                 text_scale = textScale, geom = mIcon, geom_pos = (-0.2, 0, 0), geom_scale = 0.8,
                                 relief = None)
        self.mInfo.setPos(0.8, 0, 0.5)
        self.sInfo = DirectLabel(parent = self.cogInfoFrame, text_fg = cogInfoTextColor, text = '', text_pos = textPos,
                                 text_scale = textScale, geom = sIcon, geom_pos = (-0.2, 0, 0), geom_scale = 0.8,
                                 relief = None)
        self.sInfo.setPos(0.8, 0, -0.5)
        icons.removeNode()

    def updateCogInfo(self):
        if hasattr(base.cr, 'currSuitPlanner') and base.cr.currSuitPlanner:
            percentages = base.cr.currSuitPlanner.getCogPercentages()
            self.cInfo['text'] = f'{percentages[0]}%'
            self.lInfo['text'] = f'{percentages[1]}%'
            self.mInfo['text'] = f'{percentages[2]}%'
            self.sInfo['text'] = f'{percentages[3]}%'

    def destroy(self):
        self.ignore('questPageUpdated')
        DirectFrame.destroy(self)

    def putBuildingMarker(self, pos, mapIndex = None):
        for marker in self.buildingMarkers:
            # Prevent duplicates
            if pos == marker.getPos():
                return
        marker = DirectLabel(parent = self.container, text = '', text_pos = (-0.05, -0.15), text_fg = (1, 1, 1, 1),
                             relief = None)
        gui = loader.loadModel('phase_4/models/parties/schtickerbookHostingGUI')
        icon = gui.find('**/startPartyButton_inactive')
        iconNP = aspect2d.attachNewNode('iconNP')
        icon.reparentTo(iconNP)
        icon.setX(-12.0792 / 30.48)
        icon.setZ(-9.7404 / 30.48)
        marker['text'] = '%s' % mapIndex if not None else ''
        marker['text_scale'] = 0.7
        marker['image'] = iconNP
        marker['image_color'] = (1, 0, 0, 1)
        marker['image_scale'] = 6
        marker.setScale(0.05)
        relX, relY = self.transformAvPos(pos)
        marker.setPos(relX, 0, relY)
        self.buildingMarkers.append(marker)
        iconNP.removeNode()
        gui.removeNode()

    def putLandmarkMarker(self, label, markerType, pos):
        landmarkIconModel = loader.loadModel('phase_3.5/models/gui/ttoff_m_gui_hud_questMap', allowInstance = True)

        # todo: this doesnt need to be a button (unless we wanna add a popup with info which might be a good idea)
        # this new icon will just have the tooltip follow the cursor
        marker = AnimatedButton(parent = self.container,
                                text = ('', label), text_pos = (0, 0.05), text_fg = (1.0, 1.0, 1.0, 1.0),
                                text_shadow = (0, 0, 0, 0.8),
                                text_bg = (0, 1, 0, .6), text_scale = 0.024, relief = None,
                                image = landmarkIconModel.find(getIconNodeName(markerType)),
                                image_scale = 0.15 if isZoneIcon(markerType) else 0.08)
        relX, relY = self.transformAvPos(pos)
        marker.setPos(relX, 0, relY)
        self.landmarkMarkers.append(marker)
        landmarkIconModel.removeNode()

    def updateQuestInfo(self):
        for marker in self.buildingMarkers:
            marker.destroy()

        for marker in self.landmarkMarkers:
            marker.destroy()

        self.buildingMarkers = []
        self.landmarkMarkers = []
        dnaStore = base.cr.playGame.dnaStore
        for questIndex in list(self.av.questPage.quests.keys()):
            questDesc = self.av.questPage.quests.get(questIndex)
            if questDesc is None:
                continue
            mapIndex = questIndex + 1
            questId, fromNpcId, toNpcId, rewardId, toonProgress = questDesc
            quest = Quests.getQuest(questId)
            fComplete = quest.getCompletionStatus(self.av, questDesc) in (Quests.COMPLETE, Quests.COMPLETE_NERFS)
            if not fComplete:
                if quest.getType() == Quests.RecoverItemQuest:
                    if quest.getHolder() == Quests.AnyFish:
                        self.putBuildingMarker(self.fishingSpotInfo, mapIndex)
                    continue
                elif quest.getType() not in (
                        Quests.DeliverGagQuest, Quests.DeliverItemQuest, Quests.VisitQuest, Quests.TrackChoiceQuest):
                    continue
            if toNpcId == Quests.ToonHQ:
                self.putBuildingMarker(self.hqPosInfo, mapIndex)
            # Hackfix to make sure that Gyro's Lighthouse shows up on the map
            elif toNpcId == 1333 and self.zoneId == ToontownGlobals.LighthouseLane:
                self.putBuildingMarker(self.gyroPosInfo, mapIndex)
            else:
                npcZone = NPCToons.getNPCZone(toNpcId)
                hoodId = ZoneUtil.getCanonicalHoodId(npcZone)
                branchId = ZoneUtil.getCanonicalBranchZone(npcZone)
                if self.hoodId == hoodId and self.zoneId == branchId:
                    for blockIndex in range(dnaStore.getNumBlockNumbers()):
                        blockNumber = dnaStore.getBlockNumberAt(blockIndex)
                        zone = dnaStore.getZoneFromBlockNumber(blockNumber)
                        branchZone = zone - zone % 100
                        finalZone = branchZone + 500 + blockNumber
                        if npcZone == finalZone:
                            self.putBuildingMarker(dnaStore.getDoorPosHprFromBlockNumber(blockNumber).getPos(),
                                                   mapIndex)

    def transformAvPos(self, pos):
        if self.cornerPosInfo is None:
            return 0, 0
        topRight = self.cornerPosInfo[0]
        bottomLeft = self.cornerPosInfo[1]
        relativeX = (pos.getX() - bottomLeft.getX()) / (topRight.getX() - bottomLeft.getX()) - 0.5
        relativeY = (pos.getY() - bottomLeft.getY()) / (topRight.getY() - bottomLeft.getY()) - 0.5
        return relativeX, relativeY

    def update(self, task):
        if self.av:
            for objId, obj in list(base.cr.doId2do.items()):
                if objId == base.localAvatar.getDoId():
                    continue
                if isinstance(obj, DistributedToon) and obj.isPlayerControlled():
                    # Ghost mode 1 is for estate decoration, we don't care about that
                    if base.cr.getAvatarVisibility(objId):
                        self.updateAvatarMarker(obj)
                    else:
                        self.removeAvatarMarker(objId)

            for id in list(self.avMarkers.keys()):
                if id not in base.cr.doId2do.keys():
                    self.removeAvatarMarker(id)
            if self.updateMarker:
                relX, relY = self.transformAvPos(self.av.getPos(render))
                self.marker.setPos(relX, 0, relY)
                self.marker.setHpr(0, 0, -180 - self.av.getH())
        i = 0
        for buildingMarker in self.buildingMarkers:
            if not buildingMarker.isEmpty():
                buildingMarker.setScale((math.sin(task.time * 16.0 + i * math.pi / 3.0) + 1) * 0.005 + 0.04)
                i = i + 1

        return task.cont

    def makeAvatarMarkerImage(self, hType):
        if hType == 'dog':
            headModel = self.laffMeterGui.find('**/doghead')
        elif hType == 'cat':
            headModel = self.laffMeterGui.find('**/cathead')
        elif hType == 'mouse':
            headModel = self.laffMeterGui.find('**/mousehead')
        elif hType == 'horse':
            headModel = self.laffMeterGui.find('**/horsehead')
        elif hType == 'rabbit':
            headModel = self.laffMeterGui.find('**/bunnyhead')
        elif hType in ('duck', 'gyro', 'scrooge'):
            headModel = self.laffMeterGui.find('**/duckhead')
        elif hType == 'monkey':
            headModel = self.laffMeterGui.find('**/monkeyhead')
        elif hType == 'bear':
            headModel = self.laffMeterGui.find('**/bearhead')
        elif hType == 'pig':
            headModel = self.laffMeterGui.find('**/pighead')
        else:
            headModel = self.laffMeterGui.find('**/doghead')

        return headModel

    def updateAvatarMarker(self, avData: DistributedToon):
        if self.container.isHidden():
            return
        avId = avData.getDoId()
        if avId == base.localAvatar.doId:
            return
        relX, relY = self.transformAvPos(
            Vec2(avData.getPos(render)[0], avData.getPos(render)[1])
        )
        if avId in self.avMarkers:
            marker = self.avMarkers[avId]
            # TODO POST LAUNCH: REIMPLEMENT THIS BUT NOT TERRIBLE
            # ITS MAKING THE AVATAR IMAGE EVRY FRAME THATS NOT GOOD
            #marker['image'] = self.makeAvatarMarkerImage(avData.style.getType())
            #marker['image_color'] = avData.getStyle().headColor
            #marker['text'] = ('', avData.getName())
            marker.setPos(relX, 0, relY)
        else:
            marker = AnimatedButton(parent = self.container,
                                    text = ('', avData.getName()), text_pos = (0, 0.05), text_fg = (1.0, 1.0, 1.0, 1.0),
                                    text_shadow = (0, 0, 0, 0.8),
                                    text_bg = (0, 1, 0, .6), text_scale = 0.024,
                                    text_wordwrap = 12,
                                    relief = None,
                                    pos = (relX, 0, relY),
                                    image = self.makeAvatarMarkerImage(avData.style.getType()),
                                    image_scale = 0.015,
                                    image_color = avData.style.headColor,
                                    command = self.openProfilePanel, extraArgs = [avId])
            self.avMarkers[avId] = marker

    def removeAvatarMarker(self, avId):
        if avId in self.avMarkers:
            self.avMarkers[avId].destroy()
            del self.avMarkers[avId]

    def openProfilePanel(self, avId):
        handle = base.cr.identifyAvatar(avId)
        if handle:
            messenger.send('clickedNametag', [handle])

    def updateMap(self):
        zoneId = base.localAvatar.zoneId
        if self.av:

            try:
                hoodId = ZoneUtil.getCanonicalHoodId(self.av.getLocation()[1])
                zoneId = ZoneUtil.getCanonicalBranchZone(self.av.getLocation()[1])
                hood = ToontownGlobals.dnaMap[hoodId]
                mapsGeom = loader.loadModel(f'phase_4/models/questmap/ttrm_m_maps_{hood}')
                mapImage = mapsGeom.find(f'**/ttrm_t_map_{hood}_{zoneId}')
                if not mapImage.isEmpty():
                    mapName = f'ttrm_t_map_{hood}_{zoneId}'
                    self.container['image'] = mapImage
                    self.resetFrameSize()
                    self.cornerPosInfo = QuestMapGlobals.CornerPosTable.get(mapName)
                    self.hqPosInfo = QuestMapGlobals.HQPosTable.get(mapName)
                    self.gyroPosInfo = QuestMapGlobals.GyroPosTable.get(mapName)
                    self.fishingSpotInfo = QuestMapGlobals.FishingSpotPosTable.get(mapName)
                    self.cogInfoPos = QuestMapGlobals.CogInfoPosTable.get(mapName)
                    self.cogInfoFrame.setPos(self.cogInfoPos)
                    self.hide()
                    self.hoodId = hoodId
                    self.zoneId = zoneId
                    self.updateQuestInfo()
                    self.updateCogInfo()
                    if mapName in LandmarkPosTable:
                        for label, iconType, pos in LandmarkPosTable[mapName]:
                            self.putLandmarkMarker(label, iconType, pos)

                    self.handleMarker()
                    self.doMethodLater(0.05, self.update, 'questMapUpdate')
                else:
                    self.stop()
                mapsGeom.removeNode()
            except:
                self.stop()

    def start(self):
        self.container.show()
        self.accept('questPageUpdated', self.updateMap)
        self.updateMap()

        base.localAvatar.mapButton['state'] = DirectGuiGlobals.NORMAL

    def initMarker(self, task):
        if self.av:
            if not hasattr(base.cr.playGame.getPlace(), 'isInterior') or not base.cr.playGame.getPlace().isInterior:
                relX, relY = self.transformAvPos(self.av.getPos())
                self.marker.setPos(relX, 0, relY)
                self.marker.setHpr(0, 0, -180 - self.av.getH())
            self.marker['geom_scale'] = 1.4 * task.time % 0.5 * 10 + 1
            self.marker['geom_color'] = (1, 1, 1, 0.8 - 1.4 * task.time % 0.5 * 2 / 0.8 + 0.2)
        if task.time < 1:
            return task.cont
        else:
            self.marker['geom_color'] = (1, 1, 1, 0)
            return task.done

    def show(self):
        self.addTask(self.initMarker, 'questMapInit')
        DirectFrame.show(self)
        # self.mapOpenButton.hide()
        self.container.setAlphaScale(ClientSettings.StreetMapOpacity.get())
        if self.container['image']:
            base.localAvatar.mapButton['command'] = self.hide

    def hide(self):
        self.removeTask('questMapInit')
        DirectFrame.hide(self)
        if self.container['image']:
            base.localAvatar.mapButton['command'] = self.show

        for avId, marker in list(self.avMarkers.items()):
            self.avMarkers[avId].destroy()
            del self.avMarkers[avId]
        self.avMarkers = {}

    def toggle(self):
        if self.isHidden():
            self.show()
        else:
            self.hide()

    def obscureButton(self):
        if base.localAvatar.actionBar:
            base.localAvatar.mapButton['state'] = DirectGuiGlobals.DISABLED

    def stop(self):
        self.container['image'] = None
        for marker in self.buildingMarkers:
            marker.destroy()
        for avId, marker in list(self.avMarkers.items()):
            self.avMarkers[avId].destroy()

        self.buildingMarkers = []
        self.avMarkers = {}
        self.container.hide()
        self.hide()
        self.obscureButton()
        self.ignore('questPageUpdated')
        self.removeTask('questMapUpdate')

    def handleMarker(self):
        if hasattr(base.cr.playGame.getPlace(), 'isInterior') and base.cr.playGame.getPlace().isInterior:
            self.updateMarker = False
        else:
            self.updateMarker = True

    def acceptOnscreenHooks(self):
        if self.wantToggle:
            self.accept(HotkeySettings.ToggleMiniMap.getPressed(), self.toggle)
        else:
            self.accept(HotkeySettings.ToggleMiniMap.getPressed(), self.show)
            self.accept(HotkeySettings.ToggleMiniMap.getReleased(), self.hide)
        self.updateMap()

        if self.container['image']:
            base.localAvatar.mapButton['state'] = DirectGuiGlobals.NORMAL
            base.localAvatar.mapButton['command'] = self.show

    def ignoreOnscreenHooks(self):
        self.ignore(HotkeySettings.ToggleMiniMap.getPressed())
        self.ignore(HotkeySettings.ToggleMiniMap.getReleased())
        self.obscureButton()