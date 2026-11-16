# = Distributed DataPackManager - Client Side =
# Created by drewc on 4/26/2023 11:08 PM
from typing import List, Dict, Optional, Tuple

from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObject import DistributedObject
from panda3d.core import VBase4, NodePath, Texture

from toontown.datapack.DataPackGlobals import DefaultCogAppearance, DefaultCogQuotes
from toontown.toonbase import TTLocalizer
from toontown.toonbase.ToontownTypes import TCogAppearance, TCogQuote
from toontown.toonbase.ToontownTypes import TCogAppearance_D, TCogQuote_D
from toontown.toonbase.ToontownTypes import CogAppearanceIndex, CogQuoteIndex
from toontown.toonbase.ToontownTypes import TStatusEffectClient, TStatusEffect_D_Client
from toontown.toonbase.ToontownTypes import TCogAttackClient, TCogAttack_D_Client
from toontown.toonbase.ToontownTypes import TColor

import random


class DataPackManager(DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('DataPackManager')
    notify.setDebug(True)

    def __init__(self, cr):
        DistributedObject.__init__(self, cr)
        cr.dataPackMgr = self
        self.activePacks: List[Tuple[str, str, int, str]] = []
        self.cogAppearances: Dict[str, TCogAppearance_D] = {}
        self.cogQuotes: Dict[str, TCogQuote_D] = {}
        self.cogAttacks: Dict[str, TCogAttack_D_Client] = {}
        self.statusEffects: Dict[str, TStatusEffect_D_Client] = {}

    def setActivePacks(self, packs: List[Tuple[str, str, int, str]]):
        self.activePacks = packs

    def getActivePacks(self) -> List[Tuple[str, str, int, str]]:
        return self.activePacks

    def setCogAppearances(self, cogs: List[TCogAppearance]):
        for cog in cogs:
            self.cogAppearances[cog[0]] = (*cog[1:],)

    def getCogAppearances(self) -> Dict[str, TCogAppearance_D]:
        return self.cogAppearances

    def getCogAppearance(self, cogType: str) -> TCogAppearance_D:
        _cogAppearance = self.cogAppearances.get(cogType, DefaultCogAppearance)
        self.notify.debug(_cogAppearance)
        return _cogAppearance

    def setCogQuotes(self, cogQuotes: List[TCogQuote]):
        for quotes in cogQuotes:
            self.cogQuotes[quotes[0]] = (*quotes[1:],)

    def getCogQuotes(self) -> Dict[str, TCogQuote_D]:
        return self.cogQuotes

    def getCogQuotesByType(self, cogType: str, quoteTypeIndex: int) -> List[str]:
        _sets = self.getCogAppearance(cogType)[CogAppearanceIndex.QUOTE_SETS]
        _allQuotes = []
        for _set in _sets:
            _quotes = self.cogQuotes.get(_set, None)
            if _quotes and _quotes[quoteTypeIndex]:
                _allQuotes.extend(_quotes[quoteTypeIndex])
        if not _allQuotes:
            _allQuotes.append(DefaultCogQuotes[quoteTypeIndex])
        return _allQuotes

    def getCogQuoteByDoId(self, cogType: str, quoteTypeIndex: int, doId: int) -> str:
        quotes = self.getCogQuotesByType(cogType, quoteTypeIndex)
        return self.getLocalizedText(quotes[doId % len(quotes)])

    def getBrushOffText(self, cogType: str, seed: int) -> str:
        S = random.getstate()
        random.seed(seed)
        quotes = self.getCogQuotesByType(cogType, CogQuoteIndex.BRUSH_OFFS)
        quote = random.choice(quotes)
        random.setstate(S)
        return self.getLocalizedText(quote)

    def setCogAttacks(self, cogAttacks: List[TCogAttackClient]):
        for cogAttack in cogAttacks:
            self.cogAttacks[cogAttack[0]] = (*cogAttack[1:],)

    def getCogAttacks(self) -> Dict[str, TCogAttack_D_Client]:
        return self.cogAttacks

    def getCogAttack(self, identifier: str) -> TCogAttack_D_Client:
        _cogAttack = self.cogAttacks.get(identifier, None)
        return _cogAttack

    def getCogAttackAnimName(self, identifier: str) -> str:
        if identifier not in self.getCogAttacks():
            return 'finger-wag'
        return self.getCogAttacks()[identifier][2]

    def getCogAttackTargetType(self, identifier: str) -> str:
        if identifier not in self.getCogAttacks():
            return 'single'
        return self.getCogAttacks()[identifier][3]

    def setStatusEffects(self, statusEffects: List[TStatusEffectClient]):
        for statusEffect in statusEffects:
            self.statusEffects[statusEffect[0]] = (*statusEffect[1:],)

    def getStatusEffects(self) -> Dict[str, TStatusEffect_D_Client]:
        return self.statusEffects

    def getStatusEffect(self, identifier: str) -> TStatusEffect_D_Client:
        _statusEffect = self.statusEffects.get(identifier, None)
        return _statusEffect

    def getStatusEffectDisplayName(self, identifier: str) -> str:
        if identifier not in self.getStatusEffects():
            return 'UNKNOWN STATUS EFFECT.'
        return self.getLocalizedText(self.getStatusEffects()[identifier][0])

    def getStatusEffectDisplayColor(self, identifier: str) -> TColor:
        if identifier not in self.getStatusEffects():
            return (1.0, 0.0, 0.0, 1.0)
        return self.getStatusEffects()[identifier][1]

    @staticmethod
    def getLocalizedText(string: str, mustExist: bool = False) -> Optional[str]:
        """
        Checks if we should are trying to use localized text (starts with #)
        then gets the string from the localizer, otherwise just return the string
        :param string: Raw String
        :param mustExist: If true, returns None if the string isn't in localizer, otherwise will just return the raw string
        :return: Localized String
        """
        if string.startswith('#'):
            _attrName = string[1:]
            if hasattr(TTLocalizer, _attrName):
                _attr = getattr(TTLocalizer, _attrName)
                if isinstance(_attr, str):
                    return _attr
        return None if mustExist else string

    @staticmethod
    def getModelNode(modelPath: str, nodePath: Optional[str] = None) -> NodePath:
        _model = loader.loadModel(modelPath, okMissing = True)
        if not _model:
            DataPackManager.notify.warning(f'Unable to find model {modelPath}')
            _model = loader.loadModel('phase_3.5/models/props/cube')
        if nodePath is not None:
            if _model.find(f'**/{nodePath}').isEmpty():
                DataPackManager.notify.warning(f'Unable to find node {nodePath} from {_model}')
                return _model
            _np: NodePath = _model.find(f'**/{nodePath}')
            _newNode = NodePath(_np)
            _model.removeNode()
            return _newNode
        return _model

    @staticmethod
    def getTexture(texturePath: str) -> Texture:
        _texture = loader.loadTexture(texturePath, okMissing = True)
        if not _texture:
            DataPackManager.notify.warning(f'Unable to find texture {texturePath}')
            _texture = loader.loadTexture('phase_3/maps/ttrm_t_gen_textureNotFound.png')
            _texture.setMagfilter(Texture.FTNearest)
        return _texture