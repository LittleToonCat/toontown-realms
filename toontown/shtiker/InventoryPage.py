from . import ShtikerPage
from toontown.toonbase import ToontownBattleGlobals
from direct.gui.DirectGui import *
from panda3d.core import *
from toontown.toonbase import ToontownGlobals, HotkeySettings
from toontown.toonbase import TTLocalizer
from toontown.shtiker.DisguisePage import DeptColors
from toontown.coghq.CogDisguiseGlobals import getTotalMerits, isSuitComplete
from toontown.suit.SuitDNA import suitDepts

class InventoryPage(ShtikerPage.ShtikerPage):

    def __init__(self):
        ShtikerPage.ShtikerPage.__init__(self)
        self.currentTrackInfo = None
        self.onscreen = 0
        self.lastInventoryTime = globalClock.getRealTime()
        self.meritBars = []

    def load(self):
        ShtikerPage.ShtikerPage.load(self)
        self.title = DirectLabel(parent=self, relief=None, text=TTLocalizer.InventoryPageTitle, text_scale=0.12, textMayChange=1, pos=(0, 0, 0.62))
        self.gagFrame = DirectFrame(parent=self, relief=None, pos=(0.1, 0, -0.47), scale=(0.35, 0.35, 0.35), geom=DGG.getDefaultDialogGeom(), geom_color=ToontownGlobals.GlobalDialogColor)
        self.trackInfo = DirectFrame(parent=self, relief=None, pos=(-0.4, 0, -0.47), scale=(0.35, 0.35, 0.35), geom=DGG.getDefaultDialogGeom(), geom_scale=(1.4, 1, 1), geom_color=ToontownGlobals.GlobalDialogColor, text='', text_wordwrap=11, text_align=TextNode.ALeft, text_scale=0.12, text_pos=(-0.65, 0.3), text_fg=(0.05, 0.14, 0.4, 1))
        self.trackProgress = DirectWaitBar(parent=self.trackInfo, pos=(0, 0, -0.2), relief=DGG.SUNKEN, frameSize=(-0.6,
         0.6,
         -0.1,
         0.1), borderWidth=(0.025, 0.025), scale=1.1, frameColor=(0.4, 0.6, 0.4, 1), barColor=(0.9, 1, 0.7, 1), text='0/0', text_scale=0.15, text_fg=(0.05, 0.14, 0.4, 1), text_align=TextNode.ACenter, text_pos=(0, -0.22))
        self.trackProgress.hide()
        jarGui = loader.loadModel('phase_3.5/models/gui/jar_gui')
        self.moneyDisplay = DirectLabel(parent=self, relief=None, pos=(0.55, 0, -0.5), scale=0.8, text=str(base.localAvatar.getMoney()), text_scale=0.18, text_fg=(0.95, 0.95, 0, 1), text_shadow=(0, 0, 0, 1), text_pos=(0, -0.1, 0), image=jarGui.find('**/Jar'), text_font=ToontownGlobals.getSignFont())
        jarGui.removeNode()
        for i in range(len(suitDepts)):
            self.meritBars.append(DirectWaitBar(parent=self.trackInfo, relief=DGG.SUNKEN, frameSize=(-0.6, 0.6, -0.09, 0.09), borderWidth=(0.02, 0.02), scale=1.1, frameColor=(DeptColors[i][0] * 0.7,
             DeptColors[i][1] * 0.7, DeptColors[i][2] * 0.7, 1), barColor=(DeptColors[i][0], DeptColors[i][1], DeptColors[i][2], 1),
            text='0/0 ' + TTLocalizer.RewardPanelMeritBarLabels[i], text_scale=0.106, text_fg=(0, 0, 0, 1), text_align=TextNode.ALeft, text_pos=(-0.55, -0.04), pos=(0, 0, -0.23 * i + 0.34)))
            self.meritBars[i].hide()
        return

    def unload(self):
        del self.title
        for meritBar in self.meritBars:
            meritBar.destroy()
            del meritBar
        ShtikerPage.ShtikerPage.unload(self)

    def __moneyChange(self, money):
        self.moneyDisplay['text'] = str(money)

    def enter(self):
        ShtikerPage.ShtikerPage.enter(self)
        base.localAvatar.inventory.setActivateMode('book')
        base.localAvatar.inventory.show()
        base.localAvatar.inventory.reparentTo(self)
        self.moneyDisplay['text'] = str(base.localAvatar.getMoney())
        self.accept('enterBookDelete', self.enterDeleteMode)
        self.accept('exitBookDelete', self.exitDeleteMode)
        self.accept('enterTrackFrame', self.updateTrackInfo)
        self.accept('exitTrackFrame', self.clearTrackInfo)
        self.accept(localAvatar.uniqueName('moneyChange'), self.__moneyChange)
        self.updateMeritData()

    def exit(self):
        ShtikerPage.ShtikerPage.exit(self)
        self.clearTrackInfo(self.currentTrackInfo)
        self.ignore('enterBookDelete')
        self.ignore('exitBookDelete')
        self.ignore('enterTrackFrame')
        self.ignore('exitTrackFrame')
        self.ignore(localAvatar.uniqueName('moneyChange'))
        self.makePageWhite(None)
        base.localAvatar.inventory.hide()
        base.localAvatar.inventory.reparentTo(hidden)
        self.exitDeleteMode()
        return

    def enterDeleteMode(self):
        self.title['text'] = TTLocalizer.InventoryPageDeleteTitle
        self.title['text_fg'] = (0, 0, 0, 1)
        self.book['image_color'] = Vec4(1, 1, 0, 1)

    def exitDeleteMode(self):
        self.title['text'] = TTLocalizer.InventoryPageTitle
        self.title['text_fg'] = (0, 0, 0, 1)
        self.book['image_color'] = Vec4(1, 1, 1, 1)

    def updateTrackInfo(self, trackIndex):
        self.currentTrackInfo = trackIndex
        trackName = ToontownBattleGlobals.Tracks[trackIndex].upper()
        if base.localAvatar.hasTrackAccess(trackIndex):
            curExp, nextExp = base.localAvatar.inventory.getCurAndNextExpValues(trackIndex)
            trackText = '%s / %s' % (curExp, nextExp)
            self.trackProgress['range'] = nextExp
            self.trackProgress['value'] = curExp
            if curExp >= ToontownBattleGlobals.regMaxSkill:
                str = TTLocalizer.InventoryPageTrackFull % trackName
                trackText = TTLocalizer.InventoryUberTrackExp % {'nextExp': ToontownBattleGlobals.MaxSkill - curExp}
                self.trackProgress['range'] = ToontownBattleGlobals.UberSkill
                uberCurrExp = curExp - ToontownBattleGlobals.regMaxSkill
                self.trackProgress['value'] = uberCurrExp
            else:
                morePoints = nextExp - curExp
                if morePoints == 1:
                    str = TTLocalizer.InventoryPageSinglePoint % {'trackName': trackName,
                     'numPoints': morePoints}
                else:
                    str = TTLocalizer.InventoryPagePluralPoints % {'trackName': trackName,
                     'numPoints': morePoints}
            self.trackInfo['text'] = str
            self.trackProgress['text'] = trackText
            self.trackProgress['frameColor'] = (ToontownBattleGlobals.TrackColors[trackIndex][0] * 0.6,
             ToontownBattleGlobals.TrackColors[trackIndex][1] * 0.6,
             ToontownBattleGlobals.TrackColors[trackIndex][2] * 0.6,
             1)
            self.trackProgress['barColor'] = (ToontownBattleGlobals.TrackColors[trackIndex][0],
             ToontownBattleGlobals.TrackColors[trackIndex][1],
             ToontownBattleGlobals.TrackColors[trackIndex][2],
             1)
            self.trackProgress.show()
        else:
            str = TTLocalizer.InventoryPageNoAccess % trackName
            self.trackInfo['text'] = str
            self.trackProgress.hide()
        for i in range(len(suitDepts)):
            self.meritBars[i].hide()

    def clearTrackInfo(self, trackIndex):
        if self.currentTrackInfo == trackIndex:
            self.trackInfo['text'] = ''
            self.trackProgress.hide()
            self.currentTrackInfo = None
            self.updateMeritData()

    def acceptOnscreenHooks(self):
        self.accept(HotkeySettings.PeekInventory.getPressed(), self.showInventoryOnscreen)
        self.accept(HotkeySettings.PeekInventory.getReleased(), self.hideInventoryOnscreen)

    def ignoreOnscreenHooks(self):
        self.ignore(HotkeySettings.PeekInventory.getPressed())
        self.ignore(HotkeySettings.PeekInventory.getReleased())

    def showInventoryOnscreen(self):
        messenger.send('wakeup')
        timedif = globalClock.getRealTime() - self.lastInventoryTime
        if timedif < 0.7:
            return
        self.lastInventoryTime = globalClock.getRealTime()
        if self.onscreen or base.localAvatar.questPage.onscreen:
            return
        self.onscreen = 1
        base.localAvatar.inventory.setActivateMode('book')
        base.localAvatar.inventory.show()
        base.localAvatar.inventory.reparentTo(self)
        self.moneyDisplay['text'] = str(base.localAvatar.getMoney())
        self.accept('enterTrackFrame', self.updateTrackInfo)
        self.accept('exitTrackFrame', self.clearTrackInfo)
        self.accept(localAvatar.uniqueName('moneyChange'), self.__moneyChange)
        self.reparentTo(aspect2d)
        if not self.currentTrackInfo:
            self.updateMeritData()
        self.title.hide()
        self.show()

    def hideInventoryOnscreen(self):
        if not self.onscreen:
            return
        self.onscreen = 0
        self.ignore('enterTrackFrame')
        self.ignore('exitTrackFrame')
        self.ignore(localAvatar.uniqueName('moneyChange'))
        base.localAvatar.inventory.hide()
        base.localAvatar.inventory.reparentTo(hidden)
        self.reparentTo(self.book)
        self.title.show()
        self.hide()

    def updateMeritData(self):
        for i in range(len(suitDepts)):
            meritBar = self.meritBars[i]
            totalMerits = getTotalMerits(base.localAvatar, i)
            merits = base.localAvatar.cogMerits[i]
            if isSuitComplete(base.localAvatar.cogParts, i):
                meritBar.show()
                if totalMerits:
                    meritBar['range'] = totalMerits
                    meritBar['value'] = merits
                    if merits == totalMerits:
                        meritBar['text'] = TTLocalizer.RewardPanelMeritAlert
                    else:
                        meritBar['text'] = '%s/%s %s' % (merits, totalMerits, TTLocalizer.RewardPanelMeritBarLabels[i])
                else:
                    meritBar['range'] = 1
                    meritBar['value'] = 1
                    meritBar['text'] = TTLocalizer.RewardPanelMeritsMaxed
            else:
                meritBar.hide()