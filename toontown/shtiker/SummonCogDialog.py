from direct.directnotify import DirectNotifyGlobal
from direct.fsm import StateData
from direct.gui.DirectGui import *
from direct.interval.IntervalGlobal import *
from panda3d.core import *

from toontown.datapack.DataPackManager import DataPackManager
from toontown.suit import Suit
from toontown.suit import SuitDNA
from toontown.toon import NPCToons
from toontown.toonbase import TTLocalizer, ClientSettings
from toontown.toonbase import ToontownGlobals
from toontown.toonbase.ToontownTypes import CogAppearanceIndex
from toontown.toontowngui import TTDialog, ToontownGUIUtils

TTL = TTLocalizer


class SummonCogDialog(DirectFrame, StateData.StateData):
    notify = DirectNotifyGlobal.directNotify.newCategory('SummonCogDialog')
    notify.setInfo(True)

    def __init__(self, suitIndex):
        suitGui = loader.loadModel('phase_3.5/models/gui/ttoff_m_gui_sbk_cogGallery')
        DirectFrame.__init__(self, parent = aspect2dp, pos = (0, 0, 0.3), relief = None,
                             image = suitGui.find('**/CSP_BACKGROUND'),
                             image_scale = (1.94, 1, 1),
                             image_pos = (0, 0, 0),
                             image_hpr = (0, 0, 0),
                             borderWidth = (0.01, 0.01), sortOrder = DGG.NO_FADE_SORT_INDEX)
        StateData.StateData.__init__(self, 'summon-cog-done')
        suitGui.removeNode()
        self.initialiseoptions(SummonCogDialog)
        self.suitIndex = suitIndex
        base.summonDialog = self
        self.popup = None
        self.suitName = SuitDNA.suitHeadTypes[self.suitIndex]
        self.suitFullName = DataPackManager.getLocalizedText(base.cr.dataPackMgr.getCogAppearance(self.suitName)[CogAppearanceIndex.NAME])
        self.ival = None

    def unload(self):
        if self.isLoaded == 0:
            return None
        self.isLoaded = 0
        self.exit()
        DirectFrame.destroy(self)

    def load(self):
        if self.isLoaded == 1:
            return None
        self.isLoaded = 1
        gui = loader.loadModel('phase_3.5/models/gui/ttoff_m_gui_sbk_cogGallery')

        self.body = self.attachNewNode('body')
        self.model = Suit.Suit()
        dna = SuitDNA.SuitDNA()
        dna.newSuit(self.suitName)
        self.model.setDNA(dna)
        self.model.update()
        self.model.reparentTo(self.body)
        self.model.setH(0)
        self.model.getGeomNode().setScale(0.08)
        self.model.setZ((-.5, -0.5, -0.35)[self.model.appearance[CogAppearanceIndex.BODY_TYPE]])
        self.model.setDepthTest(1)
        self.model.setDepthWrite(1)
        size = .3
        self.body.setPosHprScale(-0.453, -0.1, 0.05, 180, 0, 0, 1, 1, 1)
        self.model.setScissor(self.body, Vec3(-size), Vec3(size))
        self.model.loop('neutral')

        self.suitLabel = DirectLabel(parent = self, relief = None, text = self.suitFullName,
                                     text_fg = (1.0, 1.0, 1.0, 1.0), text_style = 3,
                                     text_font = ToontownGlobals.getSuitFont(), pos = (-0.453, 0, -0.20), scale = 0.05)
        closeButtonImage = (gui.find('**/CSP_CLOSE_OFF'), gui.find('**/CSP_CLOSE_ON'))
        buttonImage = (
            (gui.find('**/CSP_COG_OFF'), gui.find('**/CSP_COG_ON')),
            (gui.find('**/CSP_BLDG_OFF'), gui.find('**/CSP_BLDG_ON')),
            (gui.find('**/CSP_INVASION_OFF'), gui.find('**/CSP_INVASION_ON'))
        )
        disabledColor = Vec4(0.5, 0.5, 0.5, 0.5)
        self.summonSingleButton = DirectButton(parent = self, relief = None,
                                               image = buttonImage[0], image_scale = (0.541, 1, .1),
                                               image3_color = disabledColor,
                                               pos = (0.3, 0, .065), command = self.issueSummons,
                                               extraArgs = ['single'])
        self.summonBuildingButton = DirectButton(parent = self, relief = None,
                                                 image = buttonImage[1], image_scale = (0.541, 1, .1),
                                                 image3_color = disabledColor,
                                                 pos = (0.3, 0, -0.065), command = self.issueSummons,
                                                 extraArgs = ['building'])
        self.summonInvasionButton = DirectButton(parent = self, relief = None,
                                                 image = buttonImage[2], image_scale = (0.541, 1, .1),
                                                 image3_color = disabledColor,
                                                 pos = (0.3, 0, -0.195), command = self.issueSummons,
                                                 extraArgs = ['invasion'])
        self.statusLabel = DirectLabel(parent = self, 
                                       relief = None, 
                                       text = '', 
                                       text_fg = (1.0, 1.0, 1.0, 1.0),
                                       text_font = ToontownGlobals.getSuitFont(),
                                       text_wordwrap = 12,
                                       pos = (0.41, 0, 0), 
                                       scale = 0.065)
        self.cancel = DirectButton(parent = self, relief = None, image = closeButtonImage, pos = (0.75, 0, -0.35),
                                   scale = 0.1,
                                   command = self.__cancel)
        self.invasionAmount = 1000
        self.invasionAmountEntry = DirectEntry(parent = self, relief = DGG.RIDGE, scale = 0.0512,
                                               pos = (-0.555, 0.0, -0.375),
                                               numLines = 1, command = self.__verifyAmount, width = 4,
                                               text_font = ToontownGlobals.getSuitFont(),
                                               initialText = str(self.invasionAmount), frameColor = (0.8, 0.8, 0.8, 1))
        gui.removeNode()
        self.hide()

    def enter(self):
        if self.isEntered == 1:
            return
        self.isEntered = 1
        if self.isLoaded == 0:
            self.load()
        if not base.cr.legitMode:
            base.localAvatar.chatMgr.fsm.request('otherDialog')
        else:
            self.invasionAmountEntry.hide()
        self.disableButtons()
        self.enableButtons()
        self.popup = None
        base.transitions.fadeScreen(0.5)
        self.show()
        if ClientSettings.GUIAnimations.get():
            ToontownGUIUtils.Animations.popup(self, self.getScale()).start()

    def exit(self):
        if self.isEntered == 0:
            return
        self.isEntered = 0
        self.cleanupDialogs()
        base.transitions.noTransitions()
        self.ignoreAll()
        self.hide()
        # Clear focus when exiting
        self.invasionAmountEntry.setFocus()
        base.localAvatar.chatMgr.fsm.request('mainMenu')
        messenger.send(self.doneEvent, [])

    def cleanupDialogs(self):
        self.body = None
        self.model = None
        if self.popup != None:
            self.popup.cleanup()
            self.popup = None

    def cogSummonsDone(self, returnCode, suitIndex, buildingId):
        self.cancel['state'] = DGG.NORMAL
        if self.summonsType == 'single':
            if returnCode == 'success':
                self.statusLabel['text'] = TTL.SummonDlgSingleSuccess
            elif returnCode == 'badlocation':
                self.statusLabel['text'] = TTL.SummonDlgSingleBadLoc
            elif returnCode == 'fail':
                self.statusLabel['text'] = TTL.SummonDglSingleFail
        elif self.summonsType == 'building':
            if returnCode == 'success':
                building = base.cr.doId2do.get(buildingId)
                dnaStore = base.cr.playGame.dnaStore
                buildingTitle = dnaStore.getTitleFromBlockNumber(building.block)
                buildingInteriorZone = building.zoneId + 500 + building.block
                npcName = TTLocalizer.SummonDlgShopkeeper
                npcId = NPCToons.zone2NpcDict.get(buildingInteriorZone)
                if npcId:
                    npcName = NPCToons.getNPCName(npcId[0])
                if buildingTitle:
                    self.statusLabel['text'] = TTL.SummonDlgBldgSuccess % (npcName, buildingTitle)
                else:
                    self.statusLabel['text'] = TTL.SummonDlgBldgSuccess2
            elif returnCode == 'badlocation':
                self.statusLabel['text'] = TTL.SummonDlgBldgBadLoc
            elif returnCode == 'fail':
                self.statusLabel['text'] = TTL.SummonDglBldgFail
        elif self.summonsType == 'invasion':
            if returnCode == 'success':
                self.statusLabel['text'] = TTL.SummonDlgInvasionSuccess
            elif returnCode == 'busy':
                self.statusLabel['text'] = TTL.SummonDlgInvasionBusy % self.suitFullName
            elif returnCode == 'fail':
                self.statusLabel['text'] = TTL.SummonDlgInvasionFail
            elif returnCode == 'tooManyCogs':
                self.statusLabel['text'] = TTL.SummonDlgInvasionAmtOutOfRange.format(self.invasionAmount)

    def showSummonButtons(self):
        # Just in case
        if hasattr(self, 'summonSingleButton') and self.summonSingleButton:
            self.summonSingleButton.show()
        if hasattr(self, 'summonBuildingButton') and self.summonBuildingButton:
            self.summonBuildingButton.show()
        if hasattr(self, 'summonInvasionButton') and self.summonInvasionButton:
            self.summonInvasionButton.show()

    def hideSummonButtons(self):
        # Just in case
        if hasattr(self, 'summonSingleButton') and self.summonSingleButton:
            self.summonSingleButton.hide()
        if hasattr(self, 'summonBuildingButton') and self.summonBuildingButton:
            self.summonBuildingButton.hide()
        if hasattr(self, 'summonInvasionButton') and self.summonInvasionButton:
            self.summonInvasionButton.hide()

    def issueSummons(self, summonsType):
        if summonsType == 'single':
            text = TTL.SummonDlgSingleConf
        elif summonsType == 'building':
            text = TTL.SummonDlgBuildingConf
        elif summonsType == 'invasion':
            # Below we validate the input if the user presses the invasion button
            # and they're still typing in the DirectEntry

            # Convert current text for comparison
            # because we don't need to validate it
            # if it's the same as the current amount
            amtEntry = self.invasionAmountEntry.get()
            try:
                amtEntry = int(amtEntry)
            except ValueError:
                pass
            amtEqual = self.invasionAmount == amtEntry

            if self.invasionAmountEntry.guiItem.getState() == PGEntry.SFocus and not amtEqual:
                if self.__verifyAmount(amtEntry):
                    # Toggle focus out of the DirectEntry
                    # if text is valid value
                    self.invasionAmountEntry.setFocus()
                return

            # Toggle focus out of the DirectEntry
            # if text is equal to the current value
            if amtEqual:
                self.invasionAmountEntry.setFocus()

            text = TTL.SummonDlgInvasionConf
        else:
            self.notify.error('Invalid summonsType %s' % summonsType)
        text = text % self.suitFullName

        def handleResponse(resp):
            self.popup.cleanup()
            self.popup = None
            self.reparentTo(self.getParent(), DGG.NO_FADE_SORT_INDEX)
            base.transitions.fadeScreen(0.5)
            if resp == DGG.DIALOG_OK:
                self.notify.info('issuing %s summons for %s' % (summonsType, self.suitIndex))
                self.accept('cog-summons-response', self.cogSummonsDone)
                if self.ival and self.ival.isPlaying():
                    self.ival.finish()
                self.summonsType = summonsType
                self.doIssueSummonsText()
                base.localAvatar.d_reqCogSummons(self.summonsType, self.suitIndex, self.invasionAmount)
                self.hideSummonButtons()
                self.cancel['state'] = DGG.DISABLED
            else:
                self.enableButtons()
            return

        self.disableButtons()
        self.reparentTo(self.getParent(), 0)
        self.popup = TTDialog.TTDialog(parent = aspect2dp, style = TTDialog.YesNo, text = text, fadeScreen = 1,
                                       command = handleResponse)

    def __verifyAmount(self, amount):
        verified = False
        self.hideSummonButtons()
        try:
            amount = int(amount)
            if not 1000 <= amount <= 25000:
                self.statusLabel['text'] = TTL.SummonDlgInvasionAmtOutOfRange.format(amount)
            else:
                self.invasionAmount = amount
                self.statusLabel['text'] = TTL.SummonDlgInvasionAmtSuccess.format(amount)
                verified = True
        except ValueError:
            self.statusLabel['text'] = TTL.SummonDlgInvasionAmtNaN
        self.ival = Sequence(Wait(1.5), Parallel(Func(self.showSummonButtons), Func(self.clearStatusLabel)))
        self.ival.start()
        return verified

    def clearStatusLabel(self):
        self.statusLabel['text'] = ''

    def doIssueSummonsText(self):
        self.disableButtons()
        self.statusLabel['text'] = TTL.SummonDlgDelivering

    def disableButtons(self):
        self.summonSingleButton['state'] = DGG.DISABLED
        self.summonBuildingButton['state'] = DGG.DISABLED
        self.summonInvasionButton['state'] = DGG.DISABLED

    def enableButtons(self):
        if base.localAvatar.hasCogSummons(self.suitIndex, 'single'):
            self.summonSingleButton['state'] = DGG.NORMAL
        if base.localAvatar.hasCogSummons(self.suitIndex, 'building'):
            self.summonBuildingButton['state'] = DGG.NORMAL
        if base.localAvatar.hasCogSummons(self.suitIndex, 'invasion'):
            self.summonInvasionButton['state'] = DGG.NORMAL

    def __cancel(self):
        if self.ival and self.ival.isPlaying():
            self.ival.finish()
        self.exit()
