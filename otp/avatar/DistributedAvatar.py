from typing import List, Tuple, Optional, Dict

from direct.actor.DistributedActor import DistributedActor
from direct.interval.IntervalGlobal import *
from panda3d.core import NodePath, TextNode, Point3, Vec4
from panda3d.toontown import Nametag

from otp.otpbase import OTPGlobals
from toontown.battle.BattleProps import globalPropPool
from toontown.battle.StatusEffect import StatusEffect
from toontown.sandbox import PropGlobals
from toontown.sandbox.PropGlobals import PropPool
from toontown.toonbase import ToontownGlobals
from .Avatar import Avatar


class DistributedAvatar(DistributedActor, Avatar):
    HpTextGenerator = TextNode('HpTextGenerator')
    HpTextEnabled = 1
    ManagesNametagAmbientLightChanged = True

    def __init__(self, cr):
        try:
            self.DistributedAvatar_initialized
            return
        except:
            self.DistributedAvatar_initialized = 1

        Avatar.__init__(self)
        DistributedActor.__init__(self, cr)
        self.hpText = None
        self.hpTextSeq = None
        self.statusText: Optional[NodePath] = None
        self.statusTextSeq: Optional[Sequence] = None
        self.hp = None
        self.maxHp = None
        self.statusEffects: Dict[str, StatusEffect] = {}

    def disable(self):
        try:
            del self.DistributedAvatar_announced
        except:
            return

        self.reparentTo(hidden)
        self.removeActive()
        self.disableBodyCollisions()
        self.hideHpText()
        self.hp = None
        self.ignore('nameTagShowAvId')
        self.ignore('nameTagShowName')
        DistributedActor.disable(self)

    def delete(self):
        try:
            self.DistributedAvatar_deleted
        except:
            self.DistributedAvatar_deleted = 1
            Avatar.delete(self)
            DistributedActor.delete(self)

    def generate(self):
        DistributedActor.generate(self)
        if not self.isLocal():
            self.addActive()
            self.considerUnderstandable()
        self.setParent(OTPGlobals.SPHidden)
        self.setTag('avatarDoId', str(self.doId))
        self.accept('nameTagShowAvId', self.__nameTagShowAvId)
        self.accept('nameTagShowName', self.__nameTagShowName)

    def announceGenerate(self):
        try:
            self.DistributedAvatar_announced
            return
        except:
            self.DistributedAvatar_announced = 1

        if not self.isLocal():
            self.initializeBodyCollisions('distAvatarCollNode-' + str(self.doId))
        DistributedActor.announceGenerate(self)

    def __setTags(self, extra = None):
        if hasattr(base, 'idTags'):
            if base.idTags:
                self.__nameTagShowAvId()
            else:
                self.__nameTagShowName()

    def do_setParent(self, parentToken):
        if not self.isDisabled():
            if parentToken == OTPGlobals.SPHidden:
                self.nametag2dDist &= ~Nametag.CName
            else:
                self.nametag2dDist |= Nametag.CName
            self.nametag.getNametag2d().setContents(self.nametag2dContents & self.nametag2dDist)
            DistributedActor.do_setParent(self, parentToken)
            self.__setTags()

    def toonUp(self, hpGained):
        if self.hp == None or hpGained < 0:
            return
        oldHp = self.hp
        if self.hp + hpGained <= 0:
            self.hp += hpGained
        else:
            self.hp = min(max(self.hp, 0) + hpGained, self.maxHp)
        hpGained = self.hp - max(oldHp, 0)
        if hpGained > 0:
            self.showHpText(hpGained)
            self.hpChange(quietly=0)

    def takeDamage(self, hpLost, bonus = 0):
        if self.hp == None or hpLost < 0:
            return
        oldHp = self.hp
        self.hp = max(self.hp - hpLost, 0)
        hpLost = oldHp - self.hp
        if hpLost > 0:
            self.showHpText(-hpLost, bonus)
            self.hpChange(quietly=0)
            if self.hp <= 0 and oldHp > 0:
                self.died()

    def setHp(self, hitPoints):
        justRanOutOfHp = (hitPoints is not None and self.hp is not None and self.hp - hitPoints > 0) and (hitPoints <= 0)
        self.hp = hitPoints
        self.hpChange(quietly=1)
        if justRanOutOfHp:
            self.died()

    def hpChange(self, quietly = 0):
        if hasattr(self, 'doId'):
            if self.hp != None and self.maxHp != None:
                messenger.send(self.uniqueName('hpChange'), [self.hp, self.maxHp, quietly])
            if self.hp != None and self.hp > 0:
                messenger.send(self.uniqueName('positiveHP'))

    def showStatusText(self, identifier: str, scale: float = 0.75):
        if self.HpTextEnabled and not self.ghostMode:
            if self.statusText:
                self.hideStatusText()
            self.HpTextGenerator.setFont(OTPGlobals.getSignFont())
            displayName: str = base.cr.dataPackMgr.getStatusEffectDisplayName(identifier)
            r, g, b, a = base.cr.dataPackMgr.getStatusEffectDisplayColor(identifier)
            self.HpTextGenerator.setText(displayName)
            self.HpTextGenerator.clearShadow()
            self.HpTextGenerator.setAlign(TextNode.ACenter)
            self.HpTextGenerator.setTextColor(r, g, b, a)
            self.hpTextNode = self.HpTextGenerator.generate()
            self.statusText = self.attachNewNode(self.hpTextNode)
            self.statusText.setScale(scale)
            self.statusText.setBillboardPointEye()
            self.statusText.setBin('fixed', 100)
            self.statusText.setPos(0, 0, self.height / 2)
            self.statusTextSeq = Sequence(
                    self.statusText.posInterval(1.0, Point3(0, 0, self.height + 0.75), blendType='easeOut'),
                    Wait(0.85),
                    self.statusText.colorScaleInterval(0.1, Vec4(r, g, b, 0)),
                    Func(self.hideHpText))
            self.statusTextSeq.start()

    def hideStatusText(self):
        if self.statusText:
            self.statusText.removeNode()
            self.statusText = None
            if self.statusTextSeq:
                self.statusTextSeq.finish()
                self.statusTextSeq = None

    def died(self):
        pass

    def getHp(self):
        return self.hp

    def setMaxHp(self, hitPoints):
        self.maxHp = hitPoints
        self.hpChange()

    def getMaxHp(self):
        return self.maxHp

    def getName(self):
        if base.cr.getChatFilterMode() >= OTPGlobals.CHAT_FILTER_CENSOR:
            return base.profanityFilter.censor(Avatar.getName(self))
        return Avatar.getName(self)

    def setName(self, name):
        try:
            self.node().setName('%s-%d' % (name, self.doId))
            self.gotName = 1
        except:
            pass

        return Avatar.setName(self, name)

    def getStareAtNodeAndOffset(self):
        return (self, Point3(0, 0, self.height))

    def getAvIdName(self):
        return '%s\n%s' % (self.getName(), self.doId)

    def __nameTagShowAvId(self, extra = None):
        self.setDisplayName(self.getAvIdName())

    def __nameTagShowName(self, extra = None):
        self.setDisplayName(self.getName())

    def askAvOnShard(self, avId):
        if base.cr.doId2do.get(avId):
            messenger.send('AvOnShard%s' % avId, [True])
        else:
            self.sendUpdate('checkAvOnShard', [avId])

    def confirmAvOnShard(self, avId, onShard = True):
        messenger.send('AvOnShard%s' % avId, [onShard])

    def getDialogueArray(self):
        return None

    def setLoop(self, anim, start, end, part):
        start = start if start != -1 else None
        end = end if end != -1 else None
        part = part if part else None
        self.loop(anim, fromFrame = start, toFrame = end, partName = part)

    def setPingPong(self, anim, start, end, part):
        start = start if start != -1 else None
        end = end if end != -1 else None
        part = part if part else None
        self.pingpong(anim, fromFrame = start, toFrame = end, partName = part)

    def setPose(self, anim, frame, part):
        part = part if part else None
        self.pose(anim, frame, part)

    def setLeftHand(self, propName):
        transformationIndex = self.getActiveTransformationIndex()
        if transformationIndex == ToontownGlobals.TransformationCog:
            geom = self.getActiveTransformation()
            leftHand = geom.leftHand
        elif transformationIndex == ToontownGlobals.TransformationMisc and self.getTransformationsIndex(ToontownGlobals.TransformationMisc) - 1 == ToontownGlobals.TransformationMiscMickey:
            geom = self.getActiveTransformation()
            leftHand = geom.find('**/def_joint_left_hold')
        else:
            leftHand = self.find('**/leftHand')
        if propName == '':
            for child in leftHand.getChildren():
                child.removeNode()
        else:
            for child in leftHand.getChildren():
                child.removeNode()
            proptype = 0
            propName = PropGlobals.getPropNameCaseInsensitive(propName)
            if propName is not None:
                proptype = 1
            if proptype == 1:
                requestedProp = PropPool.getProp(propName)
            else:
                requestedProp = globalPropPool.getProp(propName.lower())
            collisions = requestedProp.findAllMatches('**/+CollisionNode')
            if collisions:
                for coll in collisions:
                    coll.stash()
            requestedProp.reparentTo(leftHand)

    def setRightHand(self, propName):
        transformationIndex = self.getActiveTransformationIndex()
        if transformationIndex == ToontownGlobals.TransformationCog:
            geom = self.getActiveTransformation()
            rightHand = geom.rightHand
        elif transformationIndex == ToontownGlobals.TransformationMisc and \
                self.getTransformationsIndex(ToontownGlobals.TransformationMisc) - 1 ==\
                ToontownGlobals.TransformationMiscMickey:
            geom = self.getActiveTransformation()
            rightHand = geom.find('**/def_joint_right_hold')
        else:
            rightHand = self.find('**/rightHand')
        if propName == '':
            for child in rightHand.getChildren():
                child.removeNode()
        else:
            for child in rightHand.getChildren():
                child.removeNode()
            propName = PropGlobals.getPropNameCaseInsensitive(propName)
            proptype = 0
            if propName is not None:
                proptype = 1
            if proptype == 1:
                requestedProp = PropPool.getProp(propName)
            else:
                requestedProp = globalPropPool.getProp(propName.lower())
            collisions = requestedProp.findAllMatches('**/+CollisionNode')
            if collisions:
                for coll in collisions:
                    coll.stash()
            requestedProp.reparentTo(rightHand)

    def setStatusEffects(self, statusEffects: List[Tuple[str, int, List[float]]]):
        self.statusEffects = {}
        for effect in statusEffects:
            identifier: str = effect[0]
            rounds: int = effect[1]
            extraArgs: List[float] = effect[2]
            self.statusEffects[identifier] = StatusEffect(identifier, rounds, extraArgs)

    def hasStatusEffect(self, identifier: str) -> bool:
        return identifier in self.statusEffects
