""" Data Pack Manager. """
import glob
import json
import tomllib as toml
import os
import random
from pathlib import Path
from typing import Any, List, Dict, Tuple, Union

from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from direct.stdpy.file import exists, listdir, open
from panda3d.core import Multifile, Filename, VirtualFileSystem

from toontown.toonbase.ToontownTypes import TCogAppearance, TCogHead, TCogQuote, TColor
from toontown.toonbase.ToontownTypes import TStatusEffectClient, TStatusEffect_D_Server
from toontown.toonbase.ToontownTypes import TCogAttackClient, TCogAttack_D_Server

class DataPackManagerAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DataPackManagerAI')
    notify.setDebug(True)
    PropHuntMaps = {}

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)

        self.propHuntMaps = {}
        self.suitZoneSpawns = {}

        self.cogAppearances: List[TCogAppearance] = []
        self.cogQuotes: List[TCogQuote] = []

        self.cogAttackQuotes: Dict[str, List[str]] = {}
        self.cogAttacks: List[TCogAttackClient] = []
        self.cogAttacksDict: Dict[str, TCogAttack_D_Server] = {}
        self.statusEffects: List[TStatusEffectClient] = []
        self.statusEffectsDict: Dict[str, TStatusEffect_D_Server] = {}
        self.cogBattleAttributes: Dict[str, dict] = {}

        self.datapackMultifiles: Dict[str, Multifile] = {}
        self.activePacks: List[Tuple[str, str, int, str]] = []

    def loadDatapacks(self):
        vfs = VirtualFileSystem.getGlobalPtr()
        packList = [('Toontown Realms Default Datapack', 'Toontown Realms Team', 100, 'ttrealms:default')]  # Todo: load actual file
        for name in glob.glob('resources/datapacks/*.rmdp'):
            packIdentifier = None
            mf = Multifile()
            mf.openReadWrite(Filename(name))

            infoFile = mf.findSubfile('pack.json')
            if infoFile != -1:
                info = json.loads(mf.readSubfile(infoFile))
                packIdentifier = info.get('pack_identifier', None)
                if not packIdentifier:
                    raise Exception(f'Unable to mount datapack {mf} - No pack_identifier')
                if packIdentifier in self.datapackMultifiles:
                    raise Exception(f'Unable to mount datapack {mf} - Pack with identifier "{packIdentifier}" already exists!')

                ver = info.get('datapacks_version', None)
                if ver != 101:
                    raise Exception(f'Unable to mount datapack {mf} - Unsupported Datapack Version ({ver})')
                packList.insert(0, (info.get('pack_name', name), info.get('pack_author', 'Unknown'), ver, packIdentifier))
                self.notify.info(f'Mounted datapack {info.get("pack_name", "")}')
            else:
                self.notify.warning(f'pack.json not found in {name}! Not loading...')
                continue

            names = mf.getSubfileNames()

            for fname in names:
                ext = os.path.splitext(fname)[1]
                if ext not in ('.json', '.toml'):
                    mf.removeSubfile(fname)
                    self.notify.warning(f'{fname} found in datapack {name} is not a supported file type (.json or .toml), removing...')

            successfulMount = vfs.mount(mf, Filename('/'), 0)
            if not successfulMount:
                raise Exception(f"Unable to mount datapack {mf}")
            self.datapackMultifiles[packIdentifier] = mf

        self.b_setActivePacks(packList)

    def b_setActivePacks(self, packs: List[Tuple[str, str, int, str]]):
        self.setActivePacks(packs)
        self.d_setActivePacks(packs)

    def setActivePacks(self, packs: List[Tuple[str, str, int, str]]):
        self.activePacks = packs

    def d_setActivePacks(self, packs: List[Tuple[str, str, int, str]]):
        self.sendUpdate('setActivePacks', [packs])

    def getActivePacks(self) -> List[Tuple[str, str, int, str]]:
        return self.activePacks

    def loadPropHuntMaps(self):
        """
        Searches the {DATAPACK}/minigames/prophunt/maps folder for .json files, then parses them
        """
        # Remove any currently loaded filters
        for _map in self.propHuntMaps:
            del _map
        self.propHuntMaps = {}

        vfs = VirtualFileSystem.getGlobalPtr()

        filedata = self.readFilesInFolderWithIncluded('minigames/prophunt/maps')

        for jsonData in filedata:
            # Make sure this unique identifier hasnt been registered already
            if jsonData['map_info']['identifier'] in self.propHuntMaps:
                # If it has, don't register it
                DataPackManagerAI.notify.warning(
                    f"Found duplicate identifier ({jsonData['map_info']['identifier']})! Not registering!")
            else:
                DataPackManagerAI.notify.info(f"Registering Prop Hunt Map {jsonData['map_info']['identifier']}")
                self.propHuntMaps[jsonData['map_info']['identifier']] = jsonData

    def loadSuitZoneSpawns(self):
        """

        """
        self.suitZoneSpawns = {}
        filedata = self.readFilesInFolderWithIncluded('cogs/zone_spawns', True)

        for zoneId, jsonData in filedata:
            DataPackManagerAI.notify.debug(f"Registering suit spawns for zone {zoneId}")
            self.suitZoneSpawns[int(zoneId)] = jsonData

    def readFilesInFolderWithIncluded(self, folder: str, returnFilename: bool = False) -> List[Union[Dict, Tuple[str, Dict]]]:
        _fileData = []

        for file in self.getDefaultFiles(folder):
            self.notify.debug(f'Loading {file}')
            with open(file, 'r') as _file:
                if file.endswith('.json'):
                    parser = json
                else:
                    parser = toml
                if returnFilename:
                    _fileData.append((
                        Path(file).stem,
                        parser.loads(_file.read())
                    ))

                else:
                    _fileData.append(parser.loads(_file.read()))

        for pack in self.datapackMultifiles.values():
            for file in self.getFilesInPack(pack, folder):
                self.notify.debug(f'Loading {file} from {pack}')
                if file.endswith('.json'):
                    parser = json
                else:
                    parser = toml
                if returnFilename:
                    _fileData.append((
                        Path(file).stem,
                        parser.loads(pack.readSubfile(pack.findSubfile(file)))
                    ))
                else:
                    _fileData.append(parser.loads(pack.readSubfile(pack.findSubfile(file))))

        return _fileData

    def loadCogAppearances(self):
        _cogs: List[TCogAppearance] = []
        for name, cog in self.readFilesInFolderWithIncluded('cogs/appearance', True):
            _heads: List[TCogHead] = []
            for head in cog.get('head_models', [{'path': 'phase_4/models/char/suitB-heads', 'node': 'beancounter', 'texture': 'phase_4/maps/suit-heads_palette_3cmla_4.png'}]):
                _heads.append(
                    (head.get('path', 'phase_3.5/models/props/cube'),
                     head.get('node', ''),
                     head.get('texture', ''),
                     head.get('position', (0, 0, 0)),
                     head.get('rotation', (0, 0, 0)),
                     head.get('scale', (1, 1, 1)),
                     head.get('color_scale', (1, 1, 1, 1)),
                     head.get('remove_nodes', [])
                     )
                )

            if isinstance(cog.get('color_scale', (1.0, 1.0, 1.0, 1.0)), dict):
                colDict = cog.get('color_scale', {"normal": (1.0, 1.0, 1.0, 1.0)})
                normalCol = colDict.get('normal', (1.0, 1.0, 1.0, 1.0))
                skeletonCol = colDict.get('skeleton', normalCol)
                virtualCol = colDict.get('virtual', (-1, -1, -1, -1))
            else:
                normalCol = cog.get('color_scale', (1.0, 1.0, 1.0, 1.0))
                skeletonCol = normalCol
                virtualCol = (-1, -1, -1, -1)

            soundPaths = cog.get('sound_paths', {})

            _cogs.append((name,
                          _heads,
                          cog.get('body_type', 0),
                          cog.get('scale', 1),
                          cog.get('height', 7),
                          cog.get('torso_texture', 'phase_14.5/maps/suit_blazer.png'),
                          cog.get('leg_texture', 'phase_14.5/maps/suit_leg.png'),
                          cog.get('arm_texture', 'phase_14.5/maps/suit_sleeve.png'),
                          cog.get('wrist_texture', ''),
                          cog.get('shoe_texture', ''),
                          cog.get('name', f'[no name {name}.json]'),
                          cog.get('name_singular', 'a COG'),
                          cog.get('name_plural', 'COGS'),
                          cog.get('hand_texture', ''),
                          cog.get('hand_color', (1.0, 1.0, 1.0, 1.0)),
                          normalCol,
                          skeletonCol,
                          virtualCol,
                          cog.get('medallion_color', (-1, -1, -1, -1)),
                          cog.get('is_skeleton', False),
                          cog.get('is_virtual', False),
                          soundPaths.get('normal_voice_grunt', ''),
                          soundPaths.get('normal_voice_murmur', ''),
                          soundPaths.get('normal_voice_statement', ''),
                          soundPaths.get('normal_voice_question', ''),
                          soundPaths.get('skelecog_voice_grunt', ''),
                          soundPaths.get('skelecog_voice_murmur', ''),
                          soundPaths.get('skelecog_voice_statement', ''),
                          soundPaths.get('skelecog_voice_question', ''),
                          cog.get('quote_sets', []),
                          )
                         )
        self.b_setCogAppearances(_cogs)

    def b_setCogAppearances(self, cogs: List[TCogAppearance]):
        self.setCogAppearances(cogs)
        self.d_setCogAppearances(cogs)

    def setCogAppearances(self, cogs: List[TCogAppearance]):
        self.cogAppearances = cogs

    def d_setCogAppearances(self, cogs: List[TCogAppearance]):
        self.sendUpdate('setCogAppearances', [cogs])

    def getCogAppearances(self) -> List[TCogAppearance]:
        return self.cogAppearances

    def loadCogQuotes(self):
        _cogQuotes: List[TCogQuote] = []
        for name, set in self.readFilesInFolderWithIncluded('cogs/quotes', True):
            _cogQuotes.append((name,
                               set.get('brush_offs', []),
                               set.get('faceoff_taunts', []),
                               set.get('cog_building_boss_taunts', []),
                               set.get('facility_boss_taunts', []),
                               set.get('facility_boss_minion_taunts', []),
                               set.get('action_prop_explode', []),
                               set.get('fire', []),
                               set.get('battle_explode', [])
                               )
                              )
        self.b_setCogQuotes(_cogQuotes)

    def b_setCogQuotes(self, cogQuotes: List[TCogQuote]):
        self.setCogQuotes(cogQuotes)
        self.d_setCogQuotes(cogQuotes)

    def setCogQuotes(self, cogQuotes: List[TCogQuote]):
        self.cogQuotes = cogQuotes

    def d_setCogQuotes(self, cogQuotes: List[TCogQuote]):
        self.sendUpdate('setCogQuotes', [cogQuotes])

    def getCogQuotes(self) -> List[TCogQuote]:
        return self.cogQuotes

    def loadCogAttackQuotes(self):
        for filename, cogAttackQuote in self.readFilesInFolderWithIncluded('cogs/attack_quotes', True):
            identifier = cogAttackQuote.get('identifier', 'null')
            attackQuotes = cogAttackQuote.get('quotes', [])
            if identifier in self.cogAttackQuotes:
                DataPackManagerAI.notify.warning(
                    f"Found duplicate identifier ({identifier})! Not registering!")
                continue
            self.cogAttackQuotes[identifier] = attackQuotes

    def getCogAttackQuoteList(self, identifier: str) -> List[str]:
        _cogAttackQuoteList = self.cogAttackQuotes.get(identifier, [])
        return _cogAttackQuoteList

    def loadCogAttacks(self):
        _cogAttacks: List[TCogAttackClient] = []
        for filename, cogAttack in self.readFilesInFolderWithIncluded('cogs/attacks', True):
            identifier = cogAttack.get('identifier', 'null')
            if self.getCogAttack(identifier) is not None:
                DataPackManagerAI.notify.warning(
                    f"Found duplicate identifier ({identifier})! Not registering!")
                continue
            targetType = cogAttack.get('target_type', 'single').lower()
            attackQuoteSets = cogAttack.get('attack_quote_sets', [])
            if targetType not in ('single', 'group'):
                targetType = 'single'
            self.cogAttacksDict[identifier] = (targetType, attackQuoteSets)
            _cogAttacks.append((identifier,
                                cogAttack.get('display_name', f'[no identifier {identifier}.json]'),
                                cogAttack.get('description', ''),
                                cogAttack.get('animation', 'finger-wag').lower(),
                                targetType
                               )
                              )
        self.b_setCogAttacks(_cogAttacks)

    def b_setCogAttacks(self, cogAttacks: List[TCogAttackClient]):
        self.setCogAttacks(cogAttacks)
        self.d_setCogAttacks(cogAttacks)

    def setCogAttacks(self, cogAttacks: List[TCogAttackClient]):
        self.cogAttacks = cogAttacks

    def d_setCogAttacks(self, cogAttacks: List[TCogAttackClient]):
        self.sendUpdate('setCogAttacks', [cogAttacks])

    def getCogAttacks(self) -> List[TCogAttackClient]:
        return self.cogAttacks

    def getCogAttack(self, identifier: str) -> TCogAttack_D_Server:
        return self.cogAttacksDict.get(identifier, None)

    def getCogAttackQuote(self, attackIdentifier: str) -> str:
        cogAttack: TCogAttack_D_Server = self.getCogAttack(attackIdentifier)
        if not cogAttack:
            return ""
        _quoteSets = cogAttack[1]
        _quotes = []
        for quoteSet in _quoteSets:
            _attackQuotes = self.getCogAttackQuoteList(quoteSet)
            if _attackQuotes:
                _quotes.extend(_attackQuotes)
        if not _quotes:
            return ""
        return random.choice(_quotes)

    def getCogAttackTargetType(self, identifier: str) -> str:
        attack = self.getCogAttack(identifier)
        if attack is None:
            return 'single'
        return attack[0]

    def loadStatusEffects(self):
        _statusEffects: List[TStatusEffectClient] = []
        for filename, statusEffect in self.readFilesInFolderWithIncluded('cogs/status_effects', True):
            identifier = statusEffect.get('identifier', 'null')
            if identifier in self.getStatusEffects():
                DataPackManagerAI.notify.warning(
                    f"Found duplicate identifier ({identifier})! Not registering!")
                continue
            rounds = statusEffect.get('rounds', -1)
            self.statusEffectsDict[identifier] = (rounds)
            _statusEffects.append((identifier,
                                   statusEffect.get('display_name', f'[no identifier {identifier}.json]'),
                                   statusEffect.get('display_color', (1.0, 0.0, 0.0, 1.0)),
                                   rounds
                                  )
                                 )
        self.b_setStatusEffects(_statusEffects)

    def b_setStatusEffects(self, statusEffects: List[TStatusEffectClient]):
        self.setStatusEffects(statusEffects)
        self.d_setStatusEffects(statusEffects)

    def setStatusEffects(self, statusEffects: List[TStatusEffectClient]):
        self.statusEffects = statusEffects

    def d_setStatusEffects(self, statusEffects: List[TStatusEffectClient]):
        self.sendUpdate('setStatusEffects', [statusEffects])

    def getStatusEffects(self) -> List[TStatusEffectClient]:
        return self.statusEffects

    def getStatusEffect(self, identifier: str) -> TStatusEffect_D_Server:
        return self.statusEffectsDict.get(identifier, None)

    def loadCogBattleAttributes(self):
        self.cogBattleAttributes = {}

        filedata = self.readFilesInFolderWithIncluded('cogs/battle_attributes', True)
        for identifier, battleAttributes in filedata:
            self.cogBattleAttributes[identifier] = {
                'level': battleAttributes.get('level', 0),
                'hp_by_level': battleAttributes.get('hp_by_level', {}),
                'gag_accuracy_decrement_by_level': battleAttributes.get('gag_accuracy_decrement_by_level', {}),
                'level_range': battleAttributes.get('level_range', [1, 5]),
                'flags': battleAttributes.get('flags', {}),
                'status_effects': battleAttributes.get('status_effects', {}),
                'attacks': battleAttributes.get('attacks', {})
            }

    def getCogBattleAttributes(self) -> Dict[str, dict]:
        return self.cogBattleAttributes

    def getCogHP(self, identifier: str, level: int) -> int:
        return self.cogBattleAttributes[identifier]['hp_by_level'].get(str(level), (level + 1) * (level + 2))

    def getFlag(self, identifier: str, flag: str) -> Any:
        # TODO: support validation of flag values
        # TODO: allow multiple attributes within a flag

        return self.cogBattleAttributes[identifier]['flags'].get(flag)

    def getStatusEffectsList(self, identifier: str) -> List[Tuple[str, Dict[str, Any]]]:
        return list(self.cogBattleAttributes[identifier]['status_effects'].items())

    def getCogGagAccuracyDecrement(self, identifier: str, level: int) -> int:
        def getDefaultValue():
            accuracyDecrement = (level * 5) - 5
            if accuracyDecrement < 2:
                accuracyDecrement = 2
            elif accuracyDecrement >= 55:
                accuracyDecrement = 55
            return accuracyDecrement

        return -self.cogBattleAttributes[identifier]['gag_accuracy_decrement_by_level'].get(str(level), getDefaultValue())

    def getCogCappedLevel(self, identifier: str, level: int) -> int:
        levelRange = self.cogBattleAttributes[identifier]['level_range']
        try:
            if level < levelRange[0]:
                level = levelRange[0]
            elif level > levelRange[1]:
                level = levelRange[1]
        except:
            level = 1
        return level

    @staticmethod
    def getFilesInPack(pack: Multifile, folder: str) -> List[str]:
        fn: str
        return [fn for fn in pack.getSubfileNames() if fn.startswith((folder, f'/{folder}'))]

    @staticmethod
    def getDefaultFiles(folder: str) -> List[str]:
        files = []
        # The listdir() func from direct.stdpy works nicely with VFS
        # Search the phase_3/filters folder
        if __debug__:
            # This works differently on DEV
            for file in listdir(f"resources/phase_3/data/{folder}/"):
                if file.endswith(('.json', '.toml')):
                    files.append(f'resources/phase_3/data/{folder}/{file}')
        else:
            for file in listdir(f"/phase_3/data/{folder}/"):
                if file.endswith(('.json', '.toml')):
                    files.append(f'/phase_3/data/{folder}/{file}')
        return files
