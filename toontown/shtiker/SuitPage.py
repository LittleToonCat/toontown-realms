from direct.gui import DirectGuiGlobals
from direct.gui.DirectGui import *
from direct.task.Task import Task
from panda3d.core import *

from toontown.suit import Suit
from toontown.suit import SuitDNA
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals
from . import ShtikerPage
from . import SummonCogDialog
from .CogPageGlobals import *
from toontown.toontowngui.AnimatedButton import AnimatedButton
from ..datapack.DataPackManager import DataPackManager
from ..toonbase.ToontownTypes import CogAppearanceIndex

TOOLTIP_NORMAL = 0
TOOLTIP_SHORTHAND = 1
SCALE_FACTOR = 1.5
RADAR_DELAY = 0.2
BUILDING_RADAR_POS = (0.375,
 0.065,
 -0.225,
 -0.5)
PANEL_COLORS = (Vec4(0.8, 0.78, 0.77, 1),
 Vec4(0.75, 0.78, 0.8, 1),
 Vec4(0.75, 0.82, 0.79, 1),
 Vec4(0.825, 0.76, 0.77, 1))
PANEL_COLORS_COMPLETE1 = (Vec4(0.7, 0.725, 0.545, 1),
 Vec4(0.625, 0.725, 0.65, 1),
 Vec4(0.6, 0.75, 0.525, 1),
 Vec4(0.675, 0.675, 0.55, 1))
PANEL_COLORS_COMPLETE2 = (Vec4(0.9, 0.725, 0.32, 1),
 Vec4(0.825, 0.725, 0.45, 1),
 Vec4(0.8, 0.75, 0.325, 1),
 Vec4(0.875, 0.675, 0.35, 1))


class SuitPage(ShtikerPage.ShtikerPage):

    def __init__(self):
        ShtikerPage.ShtikerPage.__init__(self)

    def load(self):
        ShtikerPage.ShtikerPage.load(self)
        frameModel = loader.loadModel('phase_3.5/models/gui/suitpage_frame')
        frameModel.setScale(0.03375, 1, 0.045)
        frameModel.setPos(0, 10, -0.575)
        self.guiTop = NodePath('guiTop')
        self.guiTop.reparentTo(self)
        self.frameNode = NodePath('frameNode')
        self.frameNode.reparentTo(self.guiTop)
        self.panelNode = NodePath('panelNode')
        self.panelNode.reparentTo(self.guiTop)
        self.iconNode = NodePath('iconNode')
        self.iconNode.reparentTo(self.guiTop)
        self.enlargedPanelNode = NodePath('enlargedPanelNode')
        self.enlargedPanelNode.reparentTo(self.guiTop)
        frame = frameModel.find('**/frame')
        frame.wrtReparentTo(self.frameNode)
        frame.setScale(0.0449888, 1, 0.045)
        screws = frameModel.find('**/screws')
        screws.wrtReparentTo(self.iconNode)
        screws.setScale(0.0449888, 1, 0.045)
        icons = frameModel.find('**/icons')
        del frameModel
        self.title = DirectLabel(parent = self.iconNode,
                                 text_font = ToontownGlobals.getSuitFont(),
                                 relief = None,
                                 text = TTLocalizer.SuitPageTitle,
                                 text_scale = 0.1,
                                 text_pos = (0.04, 0),
                                 textMayChange = 0)

        self.radarButtons = []
        icon = icons.find('**/corp_icon')
        self.corpRadarButton = DirectButton(parent=self.iconNode,
                                            relief=None,
                                            state=DGG.DISABLED,
                                            image=icon,
                                            image_scale=(0.03375, 1, 0.045),
                                            image2_color=Vec4(1.0, 1.0, 1.0, 0.75),
                                            pos=(-0.2, 10, -0.575),
                                            command=self.toggleRadar,
                                            extraArgs=[0])
        self.radarButtons.append(self.corpRadarButton)
        icon = icons.find('**/legal_icon')
        self.legalRadarButton = DirectButton(parent=self.iconNode,
                                             relief=None,
                                             state=DGG.DISABLED,
                                             image=icon,
                                             image_scale=(0.03375, 1, 0.045),
                                             image2_color=Vec4(1.0, 1.0, 1.0, 0.75),
                                             pos=(-0.2, 10, -0.575), command=self.toggleRadar, extraArgs=[1])
        self.radarButtons.append(self.legalRadarButton)
        icon = icons.find('**/money_icon')
        self.moneyRadarButton = DirectButton(parent=self.iconNode, relief=None,
                                             state=DGG.DISABLED, image=(icon, icon, icon),
                                             image_scale=(0.03375, 1, 0.045),
                                             image2_color=Vec4(1.0, 1.0, 1.0, 0.75),
                                             pos=(-0.2, 10, -0.575), command=self.toggleRadar, extraArgs=[2])
        self.radarButtons.append(self.moneyRadarButton)
        icon = icons.find('**/sales_icon')
        self.salesRadarButton = DirectButton(parent=self.iconNode, relief=None, state=DGG.DISABLED, image=(icon, icon, icon), image_scale=(0.03375, 1, 0.045), image2_color=Vec4(1.0, 1.0, 1.0, 0.75), pos=(-0.2, 10, -0.575), command=self.toggleRadar, extraArgs=[3])
        self.radarButtons.append(self.salesRadarButton)

        self.corpRadarButton.bind(DirectGuiGlobals.WITHIN, self.__showTooltip,
                                  extraArgs = [TOOLTIP_NORMAL, TTLocalizer.SuitPageBossbotRadar])
        self.corpRadarButton.bind(DirectGuiGlobals.WITHOUT, self.__hideTooltip)

        self.legalRadarButton.bind(DirectGuiGlobals.WITHIN, self.__showTooltip,
                                   extraArgs = [TOOLTIP_NORMAL, TTLocalizer.SuitPageLawbotRadar])
        self.legalRadarButton.bind(DirectGuiGlobals.WITHOUT, self.__hideTooltip)

        self.moneyRadarButton.bind(DirectGuiGlobals.WITHIN, self.__showTooltip,
                                   extraArgs = [TOOLTIP_NORMAL, TTLocalizer.SuitPageCashbotRadar])
        self.moneyRadarButton.bind(DirectGuiGlobals.WITHOUT, self.__hideTooltip)

        self.salesRadarButton.bind(DirectGuiGlobals.WITHIN, self.__showTooltip,
                                   extraArgs = [TOOLTIP_NORMAL, TTLocalizer.SuitPageSellbotRadar])
        self.salesRadarButton.bind(DirectGuiGlobals.WITHOUT, self.__hideTooltip)

        for radarButton in self.radarButtons:
            radarButton.building = 0
            radarButton.buildingRadarLabel = None

        gui = loader.loadModel('phase_3.5/models/gui/suitpage_gui')
        self.panelModel = gui.find('**/card')

        del gui
        self.makePanels()
        self.radarOn = [0,
         0,
         0,
         0]
        priceScale = 0.1
        emblemIcon = loader.loadModel('phase_3.5/models/gui/tt_m_gui_gen_emblemIcons')
        silverModel = emblemIcon.find('**/tt_t_gui_gen_emblemSilver')
        goldModel = emblemIcon.find('**/tt_t_gui_gen_emblemGold')
        self.silverLabel = DirectLabel(parent=self, relief=None, pos=(-0.25, 0, -0.69), scale=priceScale, image=silverModel, image_pos=(-0.4, 0, 0.4), text=str(localAvatar.emblems[ToontownGlobals.EmblemTypes.Silver]), text_fg=(0.95, 0.95, 0, 1), text_shadow=(0, 0, 0, 1), text_font=ToontownGlobals.getSignFont(), text_align=TextNode.ALeft)
        self.goldLabel = DirectLabel(parent=self, relief=None, pos=(0.25, 0, -0.69), scale=priceScale, image=goldModel, image_pos=(-0.4, 0, 0.4), text=str(localAvatar.emblems[ToontownGlobals.EmblemTypes.Gold]), text_fg=(0.95, 0.95, 0, 1), text_shadow=(0, 0, 0, 1), text_font=ToontownGlobals.getSignFont(), text_align=TextNode.ALeft)
        if not base.cr.wantEmblems:
            self.silverLabel.hide()
            self.goldLabel.hide()
        self.accept(localAvatar.uniqueName('emblemsChange'), self.__emblemChange)
        self.guiTop.setZ(0.625)

        suitGui = loader.loadModel('phase_3.5/models/gui/suit_detail_panel')

        self.tooltip = DirectLabel(parent=self,
                                   relief=None,
                                   text='$TOOLTIP',
                                   image = suitGui.find('**/avatar_panel'),
                                   image_scale = (0.1, 1, 0.2),
                                   image_hpr = (0, 0, 90),
                                   text_font = ToontownGlobals.getSuitFont(),
                                   text_scale=0.1,
                                   text_fg = Vec4(0.0, 0.0, 0.0, 1.0),
                                   text_pos = (-0.005, -0.025),
                                   scale = 0.7,
                                   pos=(0.04, 0, -.7), textMayChange=1)
        self.tooltipExtra = DirectLabel(parent = self.tooltip,
                                        relief = None,
                                        text = '',
                                        text_font = ToontownGlobals.getSuitFont(),
                                        text_scale=0.1,
                                        text_fg = Vec4(0.2, 0.2, 0.2, 1.0),
                                        text_pos = (-0.005, -0.08),
                                        scale = 0.5,
                                        textMayChange = 1)
        self.tooltip.hide()
        suitGui.removeNode()
        return

    def unload(self):
        self.ignoreAll()
        self.title.destroy()
        self.corpRadarButton.destroy()
        self.legalRadarButton.destroy()
        self.moneyRadarButton.destroy()
        self.salesRadarButton.destroy()
        for panel in self.panels:
            panel.destroy()

        del self.panels

        self.panelModel.removeNode()
        ShtikerPage.ShtikerPage.unload(self)

    def enter(self):
        self.updatePage()
        self.bigPanel = None
        self.nextPanel = None
        ShtikerPage.ShtikerPage.enter(self)
        return

    def exit(self):
        taskMgr.remove('buildingListResponseTimeout-later')
        taskMgr.remove('suitListResponseTimeout-later')
        taskMgr.remove('showCogRadarLater')
        taskMgr.remove('showBuildingRadarLater')
        for index in range(0, len(self.radarOn)):
            if self.radarOn[index]:
                self.toggleRadar(index)
                self.radarButtons[index]['state'] = DGG.NORMAL

        if hasattr(self, 'summonDialog') and self.summonDialog:
            self.summonDialog.unload()
            self.summonDialog = None

        ShtikerPage.ShtikerPage.exit(self)

    def __emblemChange(self, newEmblems):
        self.silverLabel['text'] = str(newEmblems[0])
        self.goldLabel['text'] = str(newEmblems[1])

    def grow(self, panel, pos):
        if self.bigPanel:
            print('setting next panel - ' + str(panel))
            self.nextPanel = panel
            self.nextPanelPos = pos
            return
        print('big panel - ' + str(panel))
        self.bigPanel = panel
        panel.reparentTo(self.enlargedPanelNode)
        panel.setScale(panel.getScale() * SCALE_FACTOR)
        if panel.summonButton:
            panel.summonButton.show()
            panel.summonButton['state'] = DGG.NORMAL

    def shrink(self, panel, pos):
        print('trying to shrink - ' + str(panel))
        if panel != self.bigPanel:
            self.nextPanel = None
            return
        print('shrink panel - ' + str(panel))
        self.bigPanel = None
        panel.setScale(panel.scale)
        panel.reparentTo(self.panelNode)
        if panel.summonButton:
            panel.summonButton.hide()
            panel.summonButton['state'] = DGG.DISABLED
        if self.nextPanel:
            self.grow(self.nextPanel, self.nextPanelPos)
        return

    def toggleRadar(self, deptNum):
        messenger.send('wakeup')
        if self.radarOn[deptNum]:
            self.radarOn[deptNum] = 0
        else:
            self.radarOn[deptNum] = 1
        deptSize = SuitDNA.suitsPerDept
        panels = self.panels[deptSize * deptNum:SuitDNA.suitsPerDept * (deptNum + 1)]
        if self.radarOn[deptNum]:
            if hasattr(base.cr, 'currSuitPlanner'):
                if base.cr.currSuitPlanner != None:
                    base.cr.currSuitPlanner.d_suitListQuery()
                    self.acceptOnce('suitListResponse', self.updateCogRadar, extraArgs=[deptNum, panels])
                    taskMgr.doMethodLater(1.0, self.suitListResponseTimeout, 'suitListResponseTimeout-later', extraArgs=(deptNum, panels))
                    if self.radarButtons[deptNum].building:
                        base.cr.currSuitPlanner.d_buildingListQuery()
                        self.acceptOnce('buildingListResponse', self.updateBuildingRadar, extraArgs=[deptNum])
                        taskMgr.doMethodLater(1.0, self.buildingListResponseTimeout, 'buildingListResponseTimeout-later', extraArgs=(deptNum,))
                else:
                    self.updateCogRadar(deptNum, panels)
                    self.updateBuildingRadar(deptNum)
            else:
                self.updateCogRadar(deptNum, panels)
                self.updateBuildingRadar(deptNum)
            self.radarButtons[deptNum]['state'] = DGG.DISABLED
        else:
            self.updateCogRadar(deptNum, panels)
            self.updateBuildingRadar(deptNum)
        return

    def suitListResponseTimeout(self, deptNum, panels):
        self.updateCogRadar(deptNum, panels, 1)

    def buildingListResponseTimeout(self, deptNum):
        self.updateBuildingRadar(deptNum, 1)

    def makePanels(self):
        self.panels = []
        base.panels = []
        xStart = -0.66
        yStart = -0.18
        xOffset = 0.199
        yOffset = 0.284
        for dept in range(0, len(SuitDNA.suitDepts)):
            row = []
            color = PANEL_COLORS[dept]
            for type in range(0, SuitDNA.suitsPerDept):
                panel = DirectLabel(parent=self.panelNode, pos=(xStart + type * xOffset, 0.0, yStart - dept * yOffset), relief=None, state=DGG.NORMAL, image=self.panelModel, image_scale=(1, 1, 1), image_color=color)
                panel.scale = 0.6
                panel.setScale(panel.scale)
                panel.quotaLabel = None
                panel.body = None
                panel.count = 0
                panel.summonButton = None
                self.addNameLabel(panel)
                self.addCogRadarLabel(panel)
                self.panels.append(panel)
                base.panels.append(panel)

    def addQuotaLabel(self, panel):
        index = self.panels.index(panel)
        count = str(base.localAvatar.cogCounts[index])
        if base.localAvatar.cogs[index] < COG_COMPLETE1:
            quota = str(COG_QUOTAS[0][index % SuitDNA.suitsPerDept])
        else:
            quota = str(COG_QUOTAS[1][index % SuitDNA.suitsPerDept])
        quotaLabel = DirectLabel(parent=panel, pos=(0.0, 0.0, -0.215),
                                 text_style = 3,
                                 relief=None, state=DGG.DISABLED, text=TTLocalizer.SuitPageQuota % (count, quota), text_scale=0.045, text_fg=(1, 1, 1, 1), text_font=ToontownGlobals.getSuitFont())
        quotaLabel.setBin('gui-popup', 100)
        panel.quotaLabel = quotaLabel

    def addSuitBody(self, panel, suitName):
        panelIndex = self.panels.index(panel)
        body = panel.attachNewNode('body')
        panel.body = Suit.Suit()
        dna = SuitDNA.SuitDNA()
        dna.newSuit(suitName)
        panel.body.setDNA(dna)
        panel.body.update()
        panel.body.reparentTo(body)
        panel.body.setH(-20)
        panel.body.getGeomNode().setScale((0.08, 0.1, 0.09)[panel.body.appearance[CogAppearanceIndex.BODY_TYPE]])
        panel.body.setZ((-.55, -0.62, -0.45)[panel.body.appearance[CogAppearanceIndex.BODY_TYPE]])
        panel.body.setDepthTest(1)
        panel.body.setDepthWrite(1)
        width = .165
        height = .235
        body.setPosHprScale(0, 0, 0, 180, 0, 0, 1, 1, 1)
        panel.body.setScissor(body, Vec3(-width, 0, -height), Vec3(width, 0, height))
        panel.body.pose('neutral', 30)

    def addNameLabel(self, panel):
        nameLabel = DirectButton(parent = panel,
                                 relief = None,
                                 pos = (0, 0, 0.185),
                                 text = TTLocalizer.SuitPageMystery,
                                 text_scale = 0.045,
                                 text_fg = (0, 0, 0, 1),
                                 text_font = ToontownGlobals.getSuitFont(),
                                 text_wordwrap = 7,
                                 frameSize = (-.125, .125, -.045, .045),
                                 clickSound = None,
                                 pressEffect = 0)
        nameLabel.setBin('gui-popup', 100)
        panel.nameLabel = nameLabel

    def addCogRadarLabel(self, panel):
        cogRadarLabel = DirectLabel(parent=panel, pos=(0.0, 0.0, -0.215),
                                    text_style = 3,
                                    relief=None, state=DGG.DISABLED, text='', text_scale=0.05, text_fg=(1, 1, 1, 1), text_font=ToontownGlobals.getSuitFont())
        cogRadarLabel.setBin('gui-popup', 100)
        panel.cogRadarLabel = cogRadarLabel

    def addSummonButton(self, panel):
        buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        okButtonList = (buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr'))
        gui = loader.loadModel('phase_3.5/models/gui/stickerbook_gui')
        iconGeom = gui.find('**/summons')
        summonButton = AnimatedButton(
                parent=panel,
                pos=(0.1, -10, -0.13),
                scale=0.1,
                relief=None,
                state=DGG.NORMAL,
                image=okButtonList,
                image_scale=13.0,
                geom=iconGeom,
                geom_scale=0.7,
                command=self.summonButtonPressed,
                extraArgs=[panel])
        summonButton.bind(DirectGuiGlobals.WITHIN, self.__showTooltip, extraArgs = [TOOLTIP_NORMAL, TTLocalizer.IssueSummons])
        summonButton.bind(DirectGuiGlobals.WITHOUT, self.__hideTooltip)
        panel.summonButton = summonButton

    def __showTooltip(self, code, text, e):
        if code == TOOLTIP_NORMAL:
            self.tooltip['image_scale'] = (0.1, 1, 0.2)
            self.tooltip['text_scale'] = 0.1
            self.tooltip['text_pos'] = (-0.005, -0.025)
            self.tooltipExtra['text'] = ''
            self.tooltipExtra.hide()
        else:
            self.tooltip['image_scale'] = (0.1, 1, 0.275)
            self.tooltip['text_scale'] = 0.075
            self.tooltip['text_pos'] = (-0.005, 0.0125)
            self.tooltipExtra['text'] = TTLocalizer.SuitPageShorthandTip
            self.tooltipExtra.show()

        self.tooltip['text'] = text
        self.tooltip.show()

    def __hideTooltip(self, e):
        self.tooltip.hide()

    def summonButtonPressed(self, panel):
        panelIndex = self.panels.index(panel)
        self.summonDialog = SummonCogDialog.SummonCogDialog(panelIndex)
        self.summonDialog.load()
        self.accept(self.summonDialog.doneEvent, self.summonDone, extraArgs=[panel])
        self.summonDialog.enter()

    def summonDone(self, panel):
        if self.summonDialog:
            self.summonDialog.unload()
            self.summonDialog = None
        index = self.panels.index(panel)
        if not base.localAvatar.hasCogSummons(index):
            panel.summonButton.hide()
        return

    def addBuildingRadarLabel(self, button):
        gui = loader.loadModel('phase_3.5/models/gui/suit_detail_panel')
        zPos = BUILDING_RADAR_POS[self.radarButtons.index(button)]
        buildingRadarLabel = DirectLabel(parent=button, relief=None, pos=(0.225, 0.0, zPos), state=DGG.DISABLED, image=gui.find('**/avatar_panel'), image_hpr=(0, 0, 90), image_scale=(0.05, 1, 0.1), image_pos=(0, 0, 0.015), text=TTLocalizer.SuitPageBuildingRadarP % '0', text_scale=0.05, text_fg=(1, 0, 0, 1), text_font=ToontownGlobals.getSuitFont())
        gui.removeNode()
        button.buildingRadarLabel = buildingRadarLabel
        return

    def resetPanel(self, dept, type):
        panel = self.panels[dept * SuitDNA.suitsPerDept + type]
        panel.nameLabel['text'] = TTLocalizer.SuitPageMystery
        panel.nameLabel.unbind(DGG.WITHIN)
        panel.nameLabel.unbind(DGG.WITHOUT)
        if panel.cogRadarLabel:
            panel.cogRadarLabel.hide()
        if panel.quotaLabel:
            panel.quotaLabel.hide()
        if panel.body:
            panel.body.hide()
        if panel.summonButton:
            panel.summonButton.hide()
        color = PANEL_COLORS[dept]
        panel['image_color'] = color
        for button in self.radarButtons:
            if button.buildingRadarLabel:
                button.buildingRadarLabel.hide()

    def setPanelStatus(self, panel, status):
        index = self.panels.index(panel)
        if status == COG_UNSEEN:
            panel.nameLabel['text'] = TTLocalizer.SuitPageMystery
        elif status == COG_BATTLED:
            suitName = SuitDNA.suitHeadTypes[index]
            suitFullName = DataPackManager.getLocalizedText(base.cr.dataPackMgr.getCogAppearance(suitName)[CogAppearanceIndex.NAME])
            panel.nameLabel['text'] = suitFullName
            if panel.quotaLabel:
                panel.quotaLabel.show()
            else:
                self.addQuotaLabel(panel)
            self.addSuitBody(panel, suitName)
            if base.localAvatar.hasCogSummons(index):
                if panel.summonButton:
                    panel.summonButton.show()
                    # small hack to fix it appearing behind
                    panel.summonButton.reparentTo(hidden)
                    panel.summonButton.reparentTo(panel)
                else:
                    self.addSummonButton(panel)
        elif status == COG_DEFEATED:
            count = str(base.localAvatar.cogCounts[index])
            if base.localAvatar.cogs[index] < COG_COMPLETE1:
                quota = str(COG_QUOTAS[0][index % SuitDNA.suitsPerDept])
            else:
                quota = str(COG_QUOTAS[1][index % SuitDNA.suitsPerDept])
            panel.quotaLabel['text'] = TTLocalizer.SuitPageQuota % (count, quota)
        elif status == COG_COMPLETE1:
            panel['image_color'] = PANEL_COLORS_COMPLETE1[int(index / SuitDNA.suitsPerDept)]
        elif status == COG_COMPLETE2:
            panel['image_color'] = PANEL_COLORS_COMPLETE2[int(index / SuitDNA.suitsPerDept)]

        if not base.cr.legitMode and status != COG_UNSEEN:
            panel.nameLabel.bind(DirectGuiGlobals.WITHIN, self.__showTooltip, extraArgs = [TOOLTIP_SHORTHAND, 
                                 TTLocalizer.SuitPageShorthand % SuitDNA.suitHeadTypes[index]])
            panel.nameLabel.bind(DirectGuiGlobals.WITHOUT, self.__hideTooltip)

    def updateAllCogs(self, status):
        for index in range(0, len(base.localAvatar.cogs)):
            base.localAvatar.cogs[index] = status

        self.updatePage()

    def updatePage(self):
        index = 0
        cogs = base.localAvatar.cogs
        badFlag = None
        for dept in range(0, len(SuitDNA.suitDepts)):
            for type in range(0, SuitDNA.suitsPerDept):
                # Don't overwrite badFlag if it's not None
                if not badFlag:
                    badFlag = self.updateCogStatus(dept, type, cogs[index])
                else:
                    self.updateCogStatus(dept, type, cogs[index])
                index += 1

        # Don't enable the buttons if the values are somehow invalid
        if not badFlag:
            self.updateCogRadarButtons(base.localAvatar.cogRadar)
            self.updateBuildingRadarButtons(base.localAvatar.buildingRadar)

    def updateCogStatus(self, dept, type, status):
        if dept < 0 or dept > len(SuitDNA.suitDepts):
            print('updateCogStatus: bad cog dept: ', dept)
            return dept
        elif type < 0 or type > SuitDNA.suitsPerDept:
            print('updateCogStatus: bad cog type: ', type)
            return type
        elif status < COG_UNSEEN or status > COG_COMPLETE2:
            print('updateCogStatus: bad status: ', status)
            return status
        else:
            self.resetPanel(dept, type)
            panel = self.panels[dept * SuitDNA.suitsPerDept + type]
            if status == COG_UNSEEN:
                self.setPanelStatus(panel, COG_UNSEEN)
            elif status == COG_BATTLED:
                self.setPanelStatus(panel, COG_BATTLED)
            elif status == COG_DEFEATED:
                self.setPanelStatus(panel, COG_BATTLED)
                self.setPanelStatus(panel, COG_DEFEATED)
            elif status == COG_COMPLETE1:
                self.setPanelStatus(panel, COG_BATTLED)
                self.setPanelStatus(panel, COG_DEFEATED)
                self.setPanelStatus(panel, COG_COMPLETE1)
            elif status == COG_COMPLETE2:
                self.setPanelStatus(panel, COG_BATTLED)
                self.setPanelStatus(panel, COG_DEFEATED)
                self.setPanelStatus(panel, COG_COMPLETE2)
            return None

    def updateCogRadarButtons(self, radars):
        for index in range(0, len(radars)):
            if radars[index] == 1:
                self.radarButtons[index]['state'] = DGG.NORMAL

    def updateCogRadar(self, deptNum, panels, timeout = 0):
        taskMgr.remove('suitListResponseTimeout-later')
        if not timeout and hasattr(base.cr, 'currSuitPlanner') and base.cr.currSuitPlanner != None:
            cogList = base.cr.currSuitPlanner.suitList
        else:
            cogList = []
        for panel in panels:
            panel.count = 0

        for cog in cogList:
            # Exception for custom cogs, as they don't appear in the Cog Gallery
            if (cog - 1) <= len(self.panels):
                self.panels[cog].count += 1

        for panel in panels:
            panel.cogRadarLabel['text'] = TTLocalizer.SuitPageCogRadar % panel.count
            if self.radarOn[deptNum]:
                panel.quotaLabel.hide()

                def showLabel(label):
                    label.show()

                taskMgr.doMethodLater(RADAR_DELAY * panels.index(panel), showLabel, 'showCogRadarLater', extraArgs=(panel.cogRadarLabel,))

                def activateButton(s = self, index = deptNum):
                    self.radarButtons[index]['state'] = DGG.NORMAL
                    return Task.done

                if not self.radarButtons[deptNum].building:
                    taskMgr.doMethodLater(RADAR_DELAY * len(panels), activateButton, 'activateButtonLater')
            else:
                panel.cogRadarLabel.hide()
                panel.quotaLabel.show()

        return

    def updateBuildingRadarButtons(self, radars):
        for index in range(0, len(radars)):
            if radars[index] == 1:
                self.radarButtons[index].building = 1

    def updateBuildingRadar(self, deptNum, timeout = 0):
        taskMgr.remove('buildingListResponseTimeout-later')
        if not timeout and hasattr(base.cr, 'currSuitPlanner') and base.cr.currSuitPlanner != None:
            buildingList = base.cr.currSuitPlanner.buildingList
        else:
            buildingList = [0,
             0,
             0,
             0]
        button = self.radarButtons[deptNum]
        if button.building:
            if not button.buildingRadarLabel:
                self.addBuildingRadarLabel(button)
            if self.radarOn[deptNum]:
                num = buildingList[deptNum]
                if num == 1:
                    button.buildingRadarLabel['text'] = TTLocalizer.SuitPageBuildingRadarS % num
                else:
                    button.buildingRadarLabel['text'] = TTLocalizer.SuitPageBuildingRadarP % num

                def showLabel(button):
                    button.buildingRadarLabel.show()
                    button['state'] = DGG.NORMAL

                taskMgr.doMethodLater(RADAR_DELAY * SuitDNA.suitsPerDept, showLabel, 'showBuildingRadarLater', extraArgs=(button,))
            else:
                button.buildingRadarLabel.hide()
        return
