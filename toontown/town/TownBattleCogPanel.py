from typing import List, Optional
from panda3d.core import Vec3, Vec4, NodePath, PointerData
from direct.gui.DirectGui import *
from direct.interval.IntervalGlobal import Sequence, Func, Wait
from otp.otpgui import OTPGUIUtils
from toontown.battle import BattleProps
from toontown.suit import Suit, SuitDNA
from toontown.suit.DistributedSuit import DistributedSuit
from toontown.toonbase import TTLocalizer, ToontownGlobals
from toontown.toonbase.ToonBaseGlobal import base
from toontown.toonbase.ToontownTypes import CogAppearanceIndex


class TownBattleCogPanel(DirectFrame):
    gui = base.loader.loadModel('phase_3.5/models/gui/ttrm_m_gui_btl_cogPanel')

    def __init__(self, index: int):
        DirectFrame.__init__(self,
                             relief = None,
                             image = self.gui.find('**/ttrm_t_gui_btl_cogPanelBg'),
                             image_scale = OTPGUIUtils.getImageScale(453, 295, 0.25),
                             image_color = Vec4(1, 1, 1, 0.7),
                             state = DGG.NORMAL
                             )
        self.setBin('fixed', 0)
        self.setScale(0.8)
        self.initialiseoptions(TownBattleCogPanel)
        self.index = index
        self.lured: bool = False
        self.cog: Optional[DistributedSuit] = None
        self.body: Optional[NodePath] = None
        self.model: Optional[Suit.Suit] = None
        self.healthMeter: Optional[NodePath] = None
        self.healthMeterGlow: Optional[NodePath] = None
        self.cogHealthCondition: Optional[int] = None
        self.blinkIval: Optional[Sequence] = None
        self.levelText: DirectLabel = DirectLabel(
            parent = self,
            text = '',
            pos = (0.01, 0, -0.075),
            text_font = ToontownGlobals.getSuitFont(),
            text_fg = Vec4(1, 1, 1, 1),
            text_scale = 0.055
        )
        self.levelText.setBin('fixed', 1)
        self.hoverTooltip: Optional[DirectLabel] = None
        self.bind(DGG.ENTER, lambda e: self.showTooltip())
        self.bind(DGG.EXIT, lambda e: self.hideTooltip())
        self.hide()

    def cleanup(self):
        self.ignoreAll()
        self.cleanupHealthMeter()
        DirectFrame.destroy(self)

    def show(self):
        DirectFrame.show(self)
        if self.healthMeter is not None:
            self.updateCogMeter()

    def setLevelText(self, level: int):
        self.levelText['text'] = TTLocalizer.TownBattleLevelText % level

    def setLured(self, lured: bool):
        self.lured = lured

    def setCogMeter(self, cog: DistributedSuit, level: int = -1, lured: bool = False):
        if self.body:
            self.cleanupHealthMeter()
        self.cog = cog

        self.body = self.attachNewNode('body')
        self.model = Suit.Suit()
        dna = SuitDNA.SuitDNA()
        dna.newSuit(cog.style.name)
        self.model.setDNA(dna)
        self.model.update()
        self.model.reparentTo(self.body)
        self.model.getGeomNode().setScale(0.055)
        self.model.setZ((-.38, -0.35, -0.3)[self.model.appearance[CogAppearanceIndex.BODY_TYPE]])
        self.model.setH(15)
        self.model.setDepthTest(True)
        self.model.setDepthWrite(True)
        self.model.setBlend(frameBlend = False)
        size = .1895
        bodyX = -0.05 if self.model.appearance[CogAppearanceIndex.BODY_TYPE] == 2 else -0.06
        self.body.setPosHprScale(bodyX, 0, 0.08, 180, 0, 0, 1, 1, 1)
        self.model.setScissor(self.body, Vec3(-size), Vec3(.1245, 0, size))
        self.model.loop('neutral')

        model = base.loader.loadModel('phase_3.5/models/gui/matching_game_gui')
        self.healthMeter = model.find('**/minnieCircle')
        self.healthMeter.setScale(0.55)
        if self.cog.currHP > self.cog.maxHP:
            condition = 5
        else:
            condition = 0
        self.healthMeter.setColor(Suit.Suit.healthColors[condition])
        self.healthMeter.reparentTo(self)
        self.healthMeterGlow = BattleProps.globalPropPool.getProp('glow')
        self.healthMeterGlow.reparentTo(self.healthMeter)
        self.healthMeterGlow.setScale(0.28)
        self.healthMeterGlow.setPos(-0.005, 0.01, 0.015)
        self.healthMeterGlow.setColor(Suit.Suit.healthGlowColors[condition])
        self.healthMeter.flattenLight()
        self.healthMeter.setPos(0.08, 0, 0.05)
        if hasattr(cog, 'getSkeleRevives') and cog.getSkeleRevives():
            level = str(level) + TTLocalizer.SkeleRevivePostFix
        self.setLevelText(level)
        self.setLured(lured)

    def startBlinkIval(self, pauseTime: float):
        self.blinkIval = Sequence(
            Func(self.__blinkRed),
            Wait(pauseTime),
            Func(self.__blinkGray),
            Wait(0.1)
        )
        self.blinkIval.loop()

    def stopBlinkIval(self):
        if self.blinkIval is not None:
            self.blinkIval.finish()
            self.blinkIval = None

    def updateCogMeter(self):
        condition = self.cog.healthCondition

        if self.cogHealthCondition is None:
            self.cogHealthCondition = condition

        if condition == 4:
            self.stopBlinkIval()
            self.startBlinkIval(pauseTime = 0.75)
        elif condition == 6:
            if self.cogHealthCondition == 4:
                self.stopBlinkIval()
            self.startBlinkIval(pauseTime = 0.25)
        else:
            self.healthMeter.setColor(Suit.Suit.healthColors[condition], 1)
            self.healthMeterGlow.setColor(Suit.Suit.healthGlowColors[condition], 1)
            self.stopBlinkIval()
            self.cogHealthCondition = condition
        self.model.loop('lured' if self.lured else 'neutral')

    def __blinkRed(self):
        self.healthMeter.setColor(Suit.Suit.healthColors[3], 1)
        self.healthMeterGlow.setColor(Suit.Suit.healthGlowColors[3], 1)
        if self.cogHealthCondition == 6:
            self.healthMeter.setScale(1.17)

    def __blinkGray(self):
        if not self.healthMeter:
            return
        self.healthMeter.setColor(Suit.Suit.healthColors[4], 1)
        self.healthMeterGlow.setColor(Suit.Suit.healthGlowColors[4], 1)
        if self.cogHealthCondition == 6:
            self.healthMeter.setScale(1.0)

    def cleanupHealthMeter(self):
        self.stopBlinkIval()
        self.setLured(False)
        if self.body is not None:
            self.body.removeNode()
            del self.body
            del self.model
        if self.healthMeter is not None:
            self.healthMeter.removeNode()
            del self.healthMeter
        if self.healthMeterGlow is not None:
            self.healthMeterGlow.removeNode()
            del self.healthMeterGlow

    def showTooltip(self):
        if self.hoverTooltip:
            self.hoverTooltip.destroy()
            self.hoverTooltip = None
        self.hoverTooltip: DirectLabel = DirectLabel(
            relief = DGG.RAISED,
            text_style = 3,
            borderWidth = (0.01, 0.01),
            parent = base.aspect2d,
            text_font = ToontownGlobals.getSuitFont(),
            text_fg = (1, 1, 1, 1),
            text_scale = 0.06,
            frameColor = (.2, .2, .2, .7),
            text = TTLocalizer.TownBattleCogHealthText % {'hitPoints': self.cog.currHP, 'maxHit': self.cog.maxHP}
        )
        self.hoverTooltip.reparentTo(base.aspect2d)
        self.addTask(self.doTooltipTask, 'cog-tooltip')

    def hideTooltip(self):
        self.removeTask('cog-tooltip')
        if self.hoverTooltip:
            self.hoverTooltip.destroy()
            self.hoverTooltip = None

    def doTooltipTask(self, task):
        if base.mouseWatcherNode.hasMouse():
            width: float = self.hoverTooltip.getWidth()

            mouse: PointerData = base.mouseWatcherNode.getMouse()
            x: float = mouse.getX()
            y: float = mouse.getY()
            y += 0.05
            self.hoverTooltip.setPos(base.render2d, Vec3(x, 0, y))

            __pos = base.a2dBottomLeft.getRelativePoint(self.hoverTooltip, Vec3(-width / 2, 0, 0))
            if __pos.getX() < 0.025:
                self.hoverTooltip.setX(base.a2dBottomLeft, width / 2 + 0.025)

        return task.cont
