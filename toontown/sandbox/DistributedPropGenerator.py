import re
import string
import uuid
from datetime import datetime

from otp.otpbase.PythonUtil import bound
from toontown.sandbox import PropGlobals
from toontown.sandbox.Prop import Prop
from toontown.sandbox.PropAnimated import PropAnimated
from toontown.sandbox.PropCollisionGenerator import PropCollisionGenerator
from toontown.sandbox.PropDistributed import PropDistributed
from toontown.sandbox.PropGlobals import PropPool
from toontown.sandbox.PropGrid import PropGrid
from toontown.sandbox.PropOccluderGenerator import PropOccluderGenerator
from toontown.sandbox.PropSpecialCurbPile import PropSpecialCurbPile
from toontown.sandbox.PropSpecialInterior import PropSpecialInterior
from toontown.sandbox.PropSpecialSidewalk import PropSpecialSidewalk
from toontown.sandbox.PropSpecialSign import PropSpecialSign
from toontown.sandbox.PropSpecialSpawnPad import PropSpecialSpawnPad
from toontown.sandbox.PropSpecialStreet import PropSpecialStreet
from toontown.sandbox.PropSpecialTexturePlane import PropSpecialTexturePlane
from toontown.sandbox.PropSpecialToon import PropSpecialToon
from toontown.sandbox.PropStatic import PropStatic
from toontown.toonbase.ToonBaseGlobal import base

if __debug__:
    import traceback

from panda3d.core import *
from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObject
from direct.gui.DirectGui import *
from direct.interval.IntervalGlobal import *

from panda3d.toontown import WhisperPopup

from otp.otpbase import OTPGlobals

from panda3d.core import PNMImage

from toontown.battle import BattleProps
from toontown.toonbase import TTLocalizer, ToontownGlobals, HotkeySettings
from toontown.toontowngui import FileBrowser, TTDialog

from collections import OrderedDict

import json
import os
import time

from toontown.sandbox.PropSpawnerGUI import PropSpawnerGUI

from typing import Dict, Optional, Any


class DistributedPropGenerator(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPropGenerator')
    gridSnap = [
        2.5,  # POS
        22.5,  # ANGLE
        0.5  # HEIGHT
    ]
    gridSnapState = [
        False,  # POS
        False,  # ANGLE
        False  # SHOW GRID
    ]

    # if specified, this will always be the height insetead of the
    # height of the geometry. especially useful for street building
    lockHeight: bool = False

    propPlaceHeightOffset = 0.0
    propPlaceMode = True

    editorOpen = False
    removeTool = False

    placeSound: AudioSound = base.loader.loadSfx('phase_3/audio/sfx/GUI_create_toon_back.ogg')
    placeSound.setVolume(0.6)

    rotationWidget: NodePath = base.loader.loadModel('phase_3.5/models/misc/ttrm_m_propgen_widget_rotate')
    rotationWidget.reparentTo(base.hidden)
    rotationWidget.setH(180)
    rotationWidget.setDepthTest(True)
    rotationWidget.setDepthWrite(False)
    rotationWidget.setCollideMask(0)

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        self.propTag = 'spawnPropTag'
        self.previewPropTag = 'previewPropTag'
        self.propNode: Optional[NodePath] = None

        self.propListNew: Dict[str, Prop] = {}
        self.selectedProp = None
        self.currentPage = 0
        self.currentProp = -1
        self.pages = []
        self.pageTabs = []
        self.editorGUI = None
        self.ival = None
        self.generatorGUI = None
        self.propInfoPanels = []
        self.propInfoLabels = []
        self.previewProp = None
        self.previewPropPanel = None
        self.sampleProp = None
        self.fileBrowser = None
        self.windowOpen = 0
        self.colorPageToggle = False
        self.availablePropPreviews = list(range(0, len(PropGlobals.PropList.keys())))
        self.availablePropNames = list(PropGlobals.PropList.keys())
        self.hiddenPropPreviews = []
        self.savedValues = {}
        self.totalPropCount = None
        self.serverPropList = []
        self.involved = False
        self.dialog = None
        self.maxPropCount = PropGlobals.MaxPropCount
        self.propListGui: Optional[PropSpawnerGUI] = None

        self.duplicatingPropData: Optional[Dict[str, Any]] = None

        self.movingPropUUID: Optional[str] = None

        self.rotateWidgetVisible: bool = False

        # Tells the client if we're in a build lot or estate zone
        # this is primarily used to allow collisions
        self.isBuildLotOrEstate: bool = False

    def announceGenerate(self):
        DistributedObject.DistributedObject.announceGenerate(self)
        self.load()

    def disable(self):
        DistributedObject.DistributedObject.disable(self)
        self.unload()

    def setIsBuildLotOrEstate(self, state: bool):
        self.isBuildLotOrEstate = state

    def load(self):
        base.cr.propGenerator = self
        if base.experimentalPropRendering:
            self.rbc = RigidBodyCombiner('propNode')
            self.propNode = base.render.attachNewNode(self.rbc)
        else:
            self.propNode = base.render.attachNewNode('propNode')

        self.fileBrowser = FileBrowser.FileBrowser()

        self.grid = PropGrid()
        self.grid.reparentTo(base.hidden)

        self.ccPropTrav = CollisionTraverser('PropGenerator.ccTrav')
        self.ccPropQueue = CollisionHandlerQueue()

        pickerNode = CollisionNode('mouseRay')
        self.pickerNode = pickerNode
        pickerNP = base.camera.attachNewNode(self.pickerNode)
        self.pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask() | ToontownGlobals.PropGenSnapPointBitMask)
        self.pickerNode.setIntoCollideMask(0)
        self.pickerRay = CollisionRay()
        self.pickerNode.addSolid(self.pickerRay)
        self.ccPropTrav.addCollider(pickerNP, self.ccPropQueue)

        self.accept('mouse1', self.checkClick)
        self.accept('alt-mouse1', self.checkClick)
        self.accept('mouse2', self.checkClick, extraArgs = [True])
        self.accept('toon-caged', self.closePropEditor)

        self.sendUpdate('requestProps')

    def __rightClickStart(self, startTime: float):
        self.__rightClickStartTime = startTime

    def collectRBC(self, task):
        self.rbc.collect()
        return task.done

    def savePropsCallback(self, state, propData):
        # Remove the dialogue box
        if self.dialog:
            self.dialog.hide()
            self.dialog.cleanup()
            self.dialog = None

        base.transitions.noTransitions()
        base.localAvatar.setLocked(False)

        if state == DGG.DIALOG_OK:
            if not os.path.exists('props/'):
                os.mkdir('props/')

            fileName = 'backup-' + base.cr.serverName + '-' + str(base.localAvatar.zoneId) + '-' + time.strftime(
                "%Y%m%d-%H%M%S")

            with open('props/' + fileName + '.json', 'w') as data:
                json.dump(propData, data, indent = 4)
                data.close()

    def savePropsToJson(self, callback = False):
        propData = OrderedDict({'propgen_version': PropGlobals.PropGenVersion})
        for propID in self.propListNew:
            prop = self.propListNew[propID]
            propInfo = OrderedDict()
            propInfo['PropType'] = prop.propName
            propInfo['Position'] = (
                prop.getX(),
                prop.getY(),
                prop.getZ()
            )
            propInfo['Rotation'] = (
                prop.getH(),
                prop.getP(),
                prop.getR()
            )
            propInfo['Scale'] = (
                prop.getSx(),
                prop.getSy(),
                prop.getSz()
            )
            propInfo['Data'] = prop.data

            propData[propID] = propInfo
        # print(propData)

        # We only want the prop data, so return that
        if callback:
            return propData

        if not os.path.exists('props/'):
            os.mkdir('props/')

        # TODO: POPUP TO NAME THE FILE
        fileName = None
        if not fileName:
            fileName = base.cr.serverName + '-' + str(base.localAvatar.zoneId) + '-' + time.strftime("%Y%m%d-%H%M%S")
        with open('props/' + fileName + '.json', 'w') as data:
            json.dump(propData, data, indent = 4)
            data.close()

        base.localAvatar.setSystemMessage(0, TTLocalizer.PropGeneratorDumpSuccessFilename.format(fileName))

    def loadPropsFromJson(self):
        base.messenger.send('wakeup')

        self.fileBrowser.openFileBrowser()
        self.fileBrowser.accept('selectionMade', self.loadPropFile)

    def loadPropFile(self, filePath = None):
        if not filePath:
            return

        if not filePath.endswith('.json'):
            return

        try:
            with open(filePath) as fileData:
                props = json.load(fileData)
                if 'propgen_version' not in props:
                    self.propMessage(ToontownGlobals.PROPS_FUTURE_SAVE)
                    return
                fileVersion = None
                for propId in props:
                    # this will still get recognized
                    if propId == 'propgen_version':
                        fileVersion = props[propId]
                        continue
                    prop = props[propId]

                    if fileVersion < PropGlobals.PropGenVersion:
                        # Convert props that have had their names changed
                        if prop['PropType'].lower() in PropGlobals.Conversions:
                            prop['PropType'] = PropGlobals.Conversions[prop['PropType'].lower()]
                    elif fileVersion > PropGlobals.PropGenVersion:
                        # If the save is a newer propgen version, don't load it
                        self.propMessage(ToontownGlobals.PROPS_FUTURE_SAVE)
                        return

                    self.d_loadPropsFromFile(propId,
                                             prop['PropType'],
                                             prop['Position'],
                                             prop['Rotation'],
                                             prop['Scale'],
                                             json.dumps(prop['Data']))

        except:
            pass

    def d_loadPropsFromFile(self, propUUID: str, propName: str, pos: Vec3F, hpr: Vec3F, scale: Vec3F, data: str):
        self.sendUpdate('loadPropsFromFile', [propUUID, propName, pos, hpr, scale, data])

    def d_requestPropSave(self):
        self.sendUpdate('requestPropSave', [])

    def unload(self):
        base.cr.propGenerator = None
        DistributedPropGenerator.editorOpen = False

        for prop in self.propListNew:
            self.propListNew[prop].removeNode()

        if self.propNode:
            self.propNode.removeNode()
            self.propNode = None

        if self.editorGUI:
            self.editorGUI.destroy()
            self.editorGUI = None

        if self.generatorGUI:
            self.generatorGUI.destroy()
            self.generatorGUI = None

        if self.previewProp:
            self.previewProp.removeNode()
            self.previewProp = None

        if self.previewPropPanel:
            self.previewPropPanel.destroy()
            self.previewPropPanel = None

        self.setRotateWidgetVisible(False)

        if self.sampleProp:
            self.sampleProp.removeNode()
            self.sampleProp = None

        if self.fileBrowser:
            self.fileBrowser.cleanup()
            self.fileBrowser = None

        if self.dialog:
            self.dialog.hide()
            self.dialog.cleanup()
            self.dialog = None

        if self.grid:
            self.grid.removeNode()
            self.grid = None

        if self.propListGui:
            self.propListGui.exit()
            self.propListGui = None

        self.involved = False
        self.removeAllTasks()

        self.ignoreAll()

    def refreshInvolvement(self):
        self.involved = True

        name = self.uniqueName('clearInvolvement')
        self.removeTask(name)
        self.doMethodLater(600, self.clearInvolvement, name, extraArgs = [])

    def clearInvolvement(self):
        self.involved = False

    def checkClick(self, rightClick = False):
        if not base.mouseWatcherNode.hasMouse():
            return

        if PropSpawnerGUI.open and not rightClick and PropSpawnerGUI.PlacingProp:
            self.d_spawnProp()
            return

        self.pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())

        mpos = base.mouseWatcherNode.getMouse()
        self.pickerRay.setFromLens(base.camNode, mpos.getX(), mpos.getY())

        self.ccPropTrav.traverse(render)
        if self.ccPropQueue.getNumEntries() > 0:
            self.ccPropQueue.sortEntries()
            pickedObj = self.ccPropQueue.getEntry(0).getIntoNodePath()  # type: NodePath
            propObj = pickedObj.findNetTag(self.propTag)

            if not propObj.isEmpty():
                if self.removeTool:
                    messenger.send('deleteProp', [propObj])
                else:
                    messenger.send('selectedProp', [propObj])
            else:
                return

    def d_spawnProp(self):
        if not self.previewProp and not self.sampleProp:
            return

        self.refreshInvolvement()

        x, y, z = self.sampleProp.getPos(render)
        h, p, r = self.sampleProp.getHpr(render)
        scale = self.sampleProp.getScale()
        propName = self.availablePropNames[self.currentProp]

        DistributedPropGenerator.placeSound.play()

        if self.movingPropUUID:
            _pr = self.propListNew.get(self.movingPropUUID, None)
            if not _pr:
                return
            _pr.newPropPos = Vec3(x, y, z)
            _pr.newPropHpr = Vec3(h, p, r)
            _pr.newPropScale = scale
            self.requestUpdateProp(self.movingPropUUID)

            self.movingPropUUID = None
            self.propListGui.stopPlacing()
            self.propListGui.selectedPropText['text'] = TTLocalizer.PropGeneratorCurrentlyPlacing
            return

        self.sendUpdate('requestSpawnProp',
                        [propName, (x, y, z), (h, p, r), (scale.getX(), scale.getY(), scale.getZ())])

        if self.duplicatingPropData:
            self.propListGui.selectedPropText['text'] = TTLocalizer.PropGeneratorCurrentlyPlacing

    def finishedSpawnProp(self, propUUID: str):
        prop: Prop = self.propListNew.get(propUUID)

        self.notify.debug(f'Got response for prop spawn {propUUID}. Type is {type(propUUID)}')

        if self.duplicatingPropData:
            for key in ('spawned_by_name', 'spawned_by_avid', 'spawned_on', 'edited_by_name', 'edited_by_avid', 'edited_on'):
                if key in self.duplicatingPropData:
                    del self.duplicatingPropData[key]

            prop.data.update(self.duplicatingPropData)

        else:
            if isinstance(prop, PropSpecialStreet):
                prop.selectStreetStyle(self.propListGui.defaultStreetTexture['selectedItem'])
                prop.selectCurbStyle(self.propListGui.defaultCurbTexture['selectedItem'])
                prop.selectSidewalkStyle(self.propListGui.defaultSidewalkTexture['selectedItem'])

            elif isinstance(prop, PropSpecialSidewalk):
                prop.selectSidewalkStyle(self.propListGui.defaultSidewalkTexture['selectedItem'])

    # TODO: REMOVE NEW SUFFIX
    def spawnPropNew(self, propUUID: str, propName: str, pos: Vec3F, hpr: Vec3F, scale: Vec3F, data: bytes):
        """
        === Sent from server ===
        Spawns the prop
        """
        if propUUID in self.propListNew:
            return

        # Convert the bytes into a dict
        data = json.loads(data.decode('utf-8'))
        propInfo = PropGlobals.PropList.get(propName, 'error?')
        if propInfo == 'error?':
            DistributedPropGenerator.notify.error(f'Prop type {propName} does not exist! Make sure you are running'
                                                  f'the same version of the game as the server!')

        # Spawn the prop
        prop = self.getPropClass(propInfo[PropGlobals.LIST_TYPE])(self, propName, propUUID, pos, hpr, scale, data)
        prop.reparentTo(self.propNode)
        self.propListNew[propUUID] = prop
        self.updatePropCount()

    @staticmethod
    def getPropClass(propType: str):
        # Get the prop class we want to spawn
        typeToClass = {
            PropGlobals.PropStatic: PropStatic,
            PropGlobals.PropAnimated: PropAnimated,
            PropGlobals.PropSpecialSign: PropSpecialSign,
            PropGlobals.PropSpecialStreet: PropSpecialStreet,
            PropGlobals.PropCollisionGen: PropCollisionGenerator,
            PropGlobals.PropSpecialSidewalk: PropSpecialSidewalk,
            PropGlobals.PropSpecialCurbPile: PropSpecialCurbPile,
            PropGlobals.PropSpecialTexturePlane: PropSpecialTexturePlane,
            PropGlobals.PropSpecialSpawnPad: PropSpecialSpawnPad,
            PropGlobals.PropSpecialToon: PropSpecialToon,
            PropGlobals.PropOccluderGen: PropOccluderGenerator,
            PropGlobals.PropDistributed: PropDistributed,
            PropGlobals.PropSpecialTInterior: PropSpecialInterior
        }
        if propType not in typeToClass:
            DistributedPropGenerator.notify.error(f'Prop type {propType} does not have a class defined')

        return typeToClass.get(propType)

    def updatePropNode(self):
        if not base.experimentalPropRendering:
            return
        self.removeTask('collectRBC')
        self.addTask(self.collectRBC, 'collectRBC')

    def toggleSnap(self, snapType: int):
        """
        Toggle snap to grid
        :param snapType: 0 for pos, 1 for rotation
        """
        DistributedPropGenerator.gridSnapState[snapType] = not DistributedPropGenerator.gridSnapState[snapType]

        if self.gridSnapState[2]:
            self.grid.reparentTo(render)
            self.grid.updateGridSize()
        else:
            self.grid.reparentTo(hidden)

    def toggleHeightLock(self):
        DistributedPropGenerator.lockHeight = not DistributedPropGenerator.lockHeight

    def setSnapSize(self, size: float, _type: int):
        DistributedPropGenerator.gridSnap[_type] = size
        self.grid.setGridSize(DistributedPropGenerator.gridSnap[0])

    def openPropEditor(self, prop):
        messenger.send('wakeup')
        self.selectedProp = prop

        propIndex = int(self.selectedProp.getTag(self.propTag))
        propInfo = self.propList[propIndex]
        if (propInfo[7] in (2, 3) and not base.localAvatar.getAccessLevel() >= OTPGlobals.AccessLevelName2Int.get(
                'BUILDER') and base.localAvatar.getDoId() != propInfo[
                3]) or base.localAvatar.getAccessLevel() == OTPGlobals.AccessLevelName2Int.get('NO_ACCESS'):
            self.selectedProp = None
            return

        if self.windowOpen == 2:
            self.closeNewPropWindow()

        localAvatar.chatMgr.setBackgroundFocus(False, True)

        self.updatePropInfo()

        if self.editorGUI:
            self.editorGUI.show()

        self.windowOpen = 1

    def closePropEditor(self):
        messenger.send('wakeup')
        self.selectedProp = None

        localAvatar.chatMgr.setBackgroundFocus(base.controlManager.getChatDisabled(), True)

        self.ignore('selectSecondaryProp')

        if self.editorGUI:
            self.editorGUI.hide()

        if self.previewProp:
            self.previewProp.removeNode()
            self.previewProp = None

        self.grid.reparentTo(hidden)

        self.windowOpen = 0

    def openNewPropWindow(self):
        base.messenger.send('wakeup')
        base.messenger.send('openPropGenUI')
        self.duplicatingPropData = None
        self.movingPropUUID = None

        if base.localAvatar.getAccessLevel() == OTPGlobals.AccessLevelName2Int.get('NO_ACCESS'):
            return

        if self.windowOpen == 2:
            return

        self.propListGui = PropSpawnerGUI(self)

        self.closePropEditor()
        self.grid.setGridSize(DistributedPropGenerator.gridSnap[0])

        base.localAvatar.chatMgr.setBackgroundFocus(base.controlManager.getChatDisabled(), True)

        if self.currentProp == -1:
            self.changeProp(1)
        else:
            self.createProp(self.currentProp)

        self.windowOpen = 2
        DistributedPropGenerator.editorOpen = True

        if self.gridSnapState[2]:
            self.grid.reparentTo(base.render)
            self.grid.updateGridSize()
        else:
            self.grid.reparentTo(base.hidden)

        if Prop.selectedProp:
            Prop.selectedProp.deselect()

        self.accept(HotkeySettings.Action.getPressed(), self.__keySpawnProp)
        self.accept(HotkeySettings.PropGeneratorPreviousProp.getReleased(), self.changeProp, extraArgs = [-1])
        self.accept(HotkeySettings.PropGeneratorNextProp.getReleased(), self.changeProp, extraArgs = [1])

    def __keySpawnProp(self):
        if not PropSpawnerGUI.SearchHasFocus and PropSpawnerGUI.PlacingProp:
            self.d_spawnProp()

    def closeNewPropWindow(self, wantTransition: bool = True):
        messenger.send('wakeup')
        messenger.send('closePropGenUI')
        self.removeTask('PROPGENmovePropSample')

        localAvatar.chatMgr.setBackgroundFocus(base.controlManager.getChatDisabled(), True)

        self.ignore(HotkeySettings.PropGeneratorPreviousProp.getReleased())
        self.ignore(HotkeySettings.PropGeneratorNextProp.getReleased())
        self.ignore(HotkeySettings.Action.getPressed())

        if self.generatorGUI:
            self.generatorGUI.hide()
            self.toggleEntryFocus(False)

        self.grid.reparentTo(hidden)
        if self.propListGui:
            self.propListGui.exit(wantTransition)
            self.propListGui = None

        if self.previewProp and self.sampleProp:
            propName = self.availablePropNames[self.currentProp]
            propType = BattleProps.globalPropPool.propTypes.get(propName.lower())
            self.ignore('alt-wheel_down')
            self.ignore('alt-wheel_up')
            self.ignore('shift-wheel_down')
            self.ignore('shift-wheel_up')

            self.setRotateWidgetVisible(False)
            if propType == 'actor':
                try:
                    self.previewProp.cleanup()

                    self.sampleProp.cleanup()
                except:
                    self.previewProp.removeNode()
                    self.sampleProp.removeNode()
            else:
                self.previewProp.removeNode()
                self.sampleProp.removeNode()
            self.previewProp = None
            self.sampleProp = None
            if self.previewPropPanel:
                self.previewPropPanel.destroy()
                self.previewPropPanel = None

        if self.ival:
            self.ival.finish()
            self.ival = None

        if self.fileBrowser.browser:
            self.fileBrowser.closeFileBrowser()

        self.windowOpen = 0

        DistributedPropGenerator.editorOpen = False

    def changeProp(self, direction: int):
        self.cleanupLastPropPreview()
        nextProp = self.currentProp + (1 * direction)
        maxProps = len(self.availablePropPreviews)
        if maxProps == 0:
            self.currentProp = -1
            return
        while nextProp in self.hiddenPropPreviews:
            nextProp += (1 * direction)
            if nextProp > max(self.availablePropPreviews):
                nextProp = min(self.availablePropPreviews)
            elif nextProp < min(self.availablePropPreviews):
                nextProp = max(self.availablePropPreviews)
        if nextProp > max(self.availablePropPreviews):
            nextProp = min(self.availablePropPreviews)
        elif nextProp < min(self.availablePropPreviews):
            nextProp = max(self.availablePropPreviews)
        self.currentProp = nextProp
        self.createProp(nextProp)

    def openPropList(self):
        self.propListGui = PropSpawnerGUI(self)

    def cleanupLastPropPreview(self):
        self.setRotateWidgetVisible(False)
        if self.previewProp and self.sampleProp:
            self.previewProp.removeNode()
            self.sampleProp.removeNode()
            self.previewProp = None
            self.sampleProp = None
            if self.previewPropPanel:
                self.previewPropPanel.destroy()
                self.previewPropPanel = None

    def selectProp(self, propIndex):
        self.duplicatingPropData = None
        if Prop.selectedProp:
            Prop.selectedProp.deselect()
        self.movingPropUUID = None
        self.cleanupLastPropPreview()
        self.currentProp = propIndex
        self.createProp(propIndex)

    def createProp(self, propIndex: int):
        self.removeTask('PROPGENmovePropSample')
        if self.ival:
            self.ival.finish()
        propName = self.availablePropNames[propIndex]
        self.previewProp = PropPool.getProp(propName)
        self.previewProp.setBin('unsorted', 0, 1)
        self.previewPropPanel, self.ival = self.makeFrameModel(self.previewProp)
        self.previewPropPanel.reparentTo(self.propListGui.selectedPropHolder, -1)
        self.previewPropPanel.setX(1.95)
        self.previewPropPanel.setScale(0.21)
        self.ival.loop()
        self.propListGui.selectedPropName.setText(propName)
        self.propListGui.selectedPropText['text'] = TTLocalizer.PropGeneratorCurrentlyPlacing

        # If the prop name is too long, we need to move it up so the second line is acutally
        # where the first line is otherwise (panda doesnt have any option for this for some reason).
        if self.propListGui.selectedPropName.textNode.getWidth() >= 13:
            self.propListGui.selectedPropName.setTextY(-0.03)
        else:
            self.propListGui.selectedPropName.setTextY(-0.13)

        self.sampleProp = NodePath('preview')
        prop = PropPool.getProp(propName)
        prop.reparentTo(self.sampleProp)
        self.sampleProp.clearTransform()
        self.sampleProp.reparentTo(render)
        self.sampleProp.setColorScale(1, 1, 1, 0.6)  # increasing this from 0.3 seems to fix the tree issue
        self.sampleProp.setTransparency(TransparencyAttrib.MAlpha)
        self.sampleProp.setTag(self.previewPropTag, propName.lower())
        self.sampleProp.setCollideMask(BitMask32(0))

        self.setRotateWidgetVisible(True)

        # TODO: Add an overridable static function to the Prop class makePreview() -> NodePath

        propType = PropGlobals.PropList.get(propName)[PropGlobals.LIST_TYPE]
        if propType == PropGlobals.PropSpecialStreet:
            self.sampleProp.find('**/*_street').setTexture(
                loader.loadTexture(
                    PropSpecialStreet.streetTextures[
                        bound(self.propListGui.defaultStreetTexture['selectedItem'], 0,len(PropSpecialStreet.streetTextures) - 1)
                    ]), 1
            )

            self.sampleProp.find('**/*_curb').setTexture(
                loader.loadTexture(
                    PropSpecialStreet.curbTextures[
                        bound(self.propListGui.defaultCurbTexture['selectedItem'], 0, len(PropSpecialStreet.curbTextures) - 1)
                    ]), 1
            )

            self.sampleProp.find('**/*_sidewalk').setTexture(
                loader.loadTexture(
                    PropSpecialStreet.sidewalkTextures[
                        bound(self.propListGui.defaultSidewalkTexture['selectedItem'], 0, len(PropSpecialStreet.sidewalkTextures) - 1)
                    ]), 1
            )
        elif propType == PropGlobals.PropSpecialSidewalk:
            self.sampleProp.find('**/*_sidewalk').setTexture(
                loader.loadTexture(
                    PropSpecialStreet.sidewalkTextures[
                        bound(self.propListGui.defaultSidewalkTexture['selectedItem'], 0, len(PropSpecialStreet.sidewalkTextures) - 1)
                    ]), 1
            )

        self.addTask(self.moveSamplePropTask, 'PROPGENmovePropSample')
        collisions = self.sampleProp.findAllMatches('**/+CollisionNode')
        if collisions:
            for coll in collisions:
                coll.stash()

        self.accept('shift-wheel_down', self.scaleSample, [-1])
        self.accept('shift-wheel_up', self.scaleSample, [1])

        self.accept('alt-wheel_down', self.moveSample, extraArgs = [False])
        self.accept('alt-wheel_up', self.moveSample, extraArgs = [True])

    def moveSamplePropTask(self, task):
        """
        Reposition the sample prop task, this is a separate method instead of just
        parenting to LocalAvatar so we can allow grid snapping
        :param task:
        :return:
        """

        if not PropSpawnerGUI.PlacingProp:
            self.sampleProp.hide()
            return task.cont
        if not base.mouseWatcherNode.hasMouse():
            return task.cont

        self.sampleProp.show()
        mouse: PointerData = base.mouseWatcherNode.getMouse()

        if base.mouseWatcherNode.isButtonDown(KeyboardButton.alt()):
            self.pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
        else:
            self.pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask() | ToontownGlobals.PropGenSnapPointBitMask)


        self.pickerRay.setFromLens(base.camNode, mouse.getX(), mouse.getY())
        self.ccPropTrav.traverse(base.render)
        if self.ccPropQueue.getNumEntries() > 0 and DistributedPropGenerator.propPlaceMode:
            self.ccPropQueue.sortEntries()
            entry: CollisionEntry = self.ccPropQueue.getEntry(0)
            solid: CollisionNode = entry.getIntoNode()
            mask = solid.getIntoCollideMask()
            if mask == ToontownGlobals.PropGenSnapPointBitMask:
                np: NodePath = entry.getIntoNodePath()
                pos = np.getPos(base.render)
                rot = np.getHpr(base.render)
                self.sampleProp.setPos(pos)
                self.sampleProp.setHpr(rot)
                return task.cont

            elif entry.hasSurfacePoint():
                pos = entry.getSurfacePoint(base.render)
                if DistributedPropGenerator.lockHeight:
                    pos.setZ(self.propPlaceHeightOffset)
                else:
                    pos.addZ(self.propPlaceHeightOffset)
        else:
            pos = base.render.getRelativePoint(base.localAvatar, (0, 6, 0))  # type: VBase3F
            if DistributedPropGenerator.lockHeight:
                pos.setZ(self.propPlaceHeightOffset)
            else:
                pos.addZ(self.propPlaceHeightOffset)

        rot = base.localAvatar.getHpr(base.render)
        if self.gridSnapState[1]:
            rot.setX(self.roundTo(rot.getX(), self.gridSnap[1]))
            rot.setY(self.roundTo(rot.getY(), self.gridSnap[1]))
            rot.setZ(self.roundTo(rot.getZ(), 0.5))

        if base.mouseWatcherNode.isButtonDown(KeyboardButton.asciiKey('z')) and DistributedPropGenerator.propPlaceMode:
            self.sampleProp.lookAt(pos[0], pos[1], pos[2])
            self.sampleProp.setH(self.sampleProp, 180)
            self.sampleProp.setP(0)
            self.sampleProp.setR(0)
            if self.gridSnapState[1]:
                self.sampleProp.setH(self.roundTo(self.sampleProp.getH(), self.gridSnap[1]))

        else:
            if self.gridSnapState[0]:
                pos.setX(self.roundTo(pos.getX(), self.gridSnap[0]))
                pos.setY(self.roundTo(pos.getY(), self.gridSnap[0]))
                pos.setZ(self.roundTo(pos.getZ(), 0.5))

            self.sampleProp.setPos(pos)
            self.grid.setPos(
                self.roundTo(pos.getX(), self.gridSnap[0]) if not self.gridSnapState[0] else pos.getX(),
                self.roundTo(pos.getY(), self.gridSnap[0]) if not self.gridSnapState[0] else pos.getY(),
                pos.getZ()
            )

        if not DistributedPropGenerator.propPlaceMode:
            self.sampleProp.setHpr(rot)

        return task.cont

    @staticmethod
    def roundTo(value: float, divisor: float) -> float:
        return round(value / divisor) * divisor

    def moveSample(self, state):
        if not self.sampleProp:
            return

        off = self.gridSnap[2] if self.gridSnapState[0] else 0.1

        if self.gridSnapState[0]:
            DistributedPropGenerator.propPlaceHeightOffset = (self.gridSnap[2] *
                                                              round(self.propPlaceHeightOffset / self.gridSnap[2]))

        if state:
            DistributedPropGenerator.propPlaceHeightOffset = self.propPlaceHeightOffset + off
        else:
            DistributedPropGenerator.propPlaceHeightOffset = self.propPlaceHeightOffset - off

    def scaleThroughSample(self, state, rightClick = False):
        if state:
            self.doMethodLater(0.1, self.scaleSample, self.uniqueName('scaleThroughSample'), extraArgs = [rightClick],
                               appendTask = True)
        else:
            self.removeTask(self.uniqueName('scaleThroughSample'))

    def scaleSample(self, direction):
        if not self.sampleProp:
            return

        value = 0.1 * direction
        scale = self.sampleProp.getScale() + value
        if scale > PropGlobals.PropMaxScale:
            scale = 0.1
        elif scale < 0.1:
            scale = PropGlobals.PropMaxScale
        self.sampleProp.setScale(scale)

    def makeFrame(self):
        # from direct.gui.DirectGui import DirectFrame
        frame = DirectFrame(parent = hidden, frameSize = (-1.0, 1.0, -1.0, 1.0), relief = None)
        return frame

    def makeFrameModel(self, model):
        frame = self.makeFrame()
        ival = None
        if model:
            model.setDepthTest(1)
            model.setDepthWrite(1)
            # Small hack to fix billboards on the UI
            for np in model.findAllMatches('**/*'):
                if isinstance(np, NodePath):
                    if np.hasBillboard():
                        np.setBillboardPointEye()
            pitch = frame.attachNewNode('pitch')
            rotate = pitch.attachNewNode('rotate')
            scale = rotate.attachNewNode('scale')
            model.reparentTo(scale)
            bMin, bMax = model.getTightBounds()
            center = (bMin + bMax) / 2.0
            model.setPos(-center[0], -center[1], -center[2])
            pitch.setP(20)
            bMin, bMax = pitch.getTightBounds()
            center = (bMin + bMax) / 2.0
            corner = Vec3(bMax - center)
            scale.setScale(1.0 / max(corner[0], corner[1], corner[2]))
            pitch.setY(2)
            ival = LerpHprInterval(rotate, 10, VBase3(-270, 0, 0), startHpr = VBase3(90, 0, 0), name = 'pg-preview-rot')
        return (frame, ival)

    def changePage(self, direction, force = -1):
        messenger.send('wakeup')
        self.pages[self.currentPage].hide()
        nextPage = self.currentPage + (1 * direction)
        if direction == 0 and force != -1:
            nextPage = force
        if nextPage == 7:
            nextPage = 0
        elif nextPage == -1:
            nextPage = 6
        self.pageTabs[self.currentPage]['text_fg'] = (0.5, 0.5, 0.5, 1.0)
        self.currentPage = nextPage
        self.pageTabs[nextPage]['text_fg'] = (0.0, 0.0, 0.0, 1.0)
        self.pages[nextPage].show()

    def updatePropPreview(self, extraArgs = None):
        if not self.selectedProp:
            return

        info = []

        for infoPanel in self.propInfoPanels:
            try:
                # If the user is just starting to type a negative or decimal number,
                # dont do the regex, since entering just '-' will clear it before you can put a number
                if not infoPanel.get() in ('.', '-'):
                    reg = re.findall(r'[-+]?\d*\.\d+|[-+]?\d+\.?', infoPanel.get())
                    if len(reg) == 0:
                        infoPanel.set('')  # Just clear the field if theres nothing valid in it
                        return
                    validatedValue = reg[0]
                    input = float(validatedValue)
                    infoPanel.set(validatedValue)
                    info.append(input)
                else:
                    info.append(float(infoPanel.get()))
            except:
                if __debug__:
                    traceback.print_exc()
                return

        for x in range(len(info)):
            value = info[x]
            if 0 <= x <= 2:
                # Position
                if value > 10000:
                    info[x] = 9999.0
                elif value < -10000:
                    info[x] = -9999.0
            elif 3 <= x <= 5:
                # Rotation
                if (value > 360) or (value < -360):
                    info[x] = 0.0
            elif 6 <= x <= 8:
                # Scale
                if value > 5:
                    info[x] = 5.0
                elif value < 0.1:
                    info[x] = 0.1
            elif 9 <= x <= 11:
                # Color Scale
                if value > 255:
                    info[x] = 255.00
                elif value < 0:
                    info[x] = 0.00

        if self.previewProp:
            self.previewProp.removeNode()
            self.previewProp = None

        self.previewProp = self.selectedProp.copyTo(render)
        self.previewProp.setPosHprScale(self.selectedProp.getParent(),
                                        info[0], info[1], info[2], info[3], info[4], info[5], info[6], info[7], info[8])
        self.previewProp.setColorScale(info[9] / 255, info[10] / 255, info[11] / 255, 0.3)
        self.previewProp.setAttrib(RenderModeAttrib.make(RenderModeAttrib.MWireframe, 5), 1)
        self.previewProp.setAttrib(StencilAttrib.make(1, StencilAttrib.SCFGreaterThan, StencilAttrib.SOKeep,
                                                      StencilAttrib.SOKeep, StencilAttrib.SOKeep, 8, 255, 255), 1)
        self.previewProp.setDepthTest(False)
        self.previewProp.setDepthWrite(False)
        self.previewProp.setTransparency(1)

    def confirmDeleteProp(self):
        messenger.send('wakeup')
        if not self.selectedProp:
            return

        propIndex = int(self.selectedProp.getTag(self.propTag))
        self.closePropEditor()
        self.sendUpdate('confirmDeleteProp', [propIndex])

    def requestDeleteProp(self, propID: str):
        """
        Ask the server if we can delete the prop
        TODO: Confirmation menu & dont let this if not allowed to
        :param propID:
        """
        if propID in self.propListNew:
            self.sendUpdate('confirmDeleteProp', [propID])

    def deleteProp(self, propId):
        self.propListNew[propId].removeNode()
        del self.propListNew[propId]
        # del self.propData[propId]

        self.updatePropCount()

    def toggleEntryFocus(self, state):
        if state:
            localAvatar.chatMgr.setBackgroundFocus(False, True)
            base.localAvatar.disableAvatarControls()
        else:
            localAvatar.chatMgr.setBackgroundFocus(base.controlManager.getChatDisabled(), True)
            base.localAvatar.enableAvatarControls()

    def propMessage(self, index):
        base.localAvatar.setSystemMessage(0, TTLocalizer.PropMessages[index], WhisperPopup.WTSystem)

    def __checkZoneValue(self, zoneId):
        for char in zoneId:
            # Check if the value is actually an integer
            if char not in string.digits:
                return False

        return True

    def confirmDeletePropsInZone(self):
        zoneId = self.zoneId
        base.transitions.fadeScreen(0.5)
        base.localAvatar.setLocked(True)
        self.dialog = TTDialog.TTDialog(style = TTDialog.TwoChoice,
                                        text = TTLocalizer.PropGeneratorDeleteZonePropsConfirm,
                                        command = self.confirmDeletePropsInZoneCallback,
                                        extraArgs = [zoneId])

    def confirmDeletePropsInZoneCallback(self, state, zoneId):
        # Cleanup the dialog box
        if self.dialog:
            self.dialog.cleanup()
            self.dialog = None

        base.transitions.noTransitions()
        base.localAvatar.setLocked(False)

        if state == DGG.DIALOG_OK:
            self.sendUpdate('confirmDeleteAllProps', [False, zoneId])

    def confirmDeleteAllProps(self):
        base.transitions.fadeScreen(0.5)
        base.localAvatar.setLocked(True)
        self.dialog = TTDialog.TTDialog(style = TTDialog.TwoChoice, text = TTLocalizer.PropGeneratorDeleteAllPropsConfirm,
                                        command = self.confirmDeleteAllPropsCallback)

    def confirmDeleteAllPropsCallback(self, state):
        # Cleanup the dialog box
        if self.dialog:
            self.dialog.cleanup()
            self.dialog = None

        base.transitions.noTransitions()
        base.localAvatar.setLocked(False)

        if state == DGG.DIALOG_OK:
            self.sendUpdate('confirmDeleteAllProps', [True, 0])

    def deleteAllProps(self):
        # Before we delete the props, we need to keep in mind users who were currently working with them
        # First, we save the current props to memory
        propData = self.savePropsToJson(callback = True)

        # Next, we see if the player has recently edited a prop in this zone
        # If they have, give them a prompt with the option to save the propData to a file
        if self.involved:
            self.closeNewPropWindow()
            # We might have a confirmation dialog open
            # Clean that up just in-case
            if self.dialog:
                self.dialog.cleanup()
                self.dialog = None

            base.transitions.fadeScreen(0.5)
            base.localAvatar.setLocked(True)
            self.dialog = TTDialog.TTDialog(style = TTDialog.TwoChoice, text = TTLocalizer.PropDeletionNotice,
                                            command = self.savePropsCallback, extraArgs = [propData])

        for propId in list(self.propListNew.keys()):
            self.deleteProp(propId)

        self.propListNew = {}

        self.updatePropCount()

    def confirmLockPropsInZone(self):
        zoneId = self.zoneId
        self.sendUpdate('confirmLockProps', [False, zoneId])

    def confirmLockProps(self, state = True):
        self.sendUpdate('confirmLockProps', [state, 0])

    def updatePropCount(self):
        # todo: this
        # also probably want to store this in this file, this is only updated when it needs to be
        if self.propListGui:
            self.propListGui.setPropCount(len(self.propListNew), self.getMaxPropCount())

    def getButton(self, type):
        if not type:
            return self.editorGUI
        else:
            return self.generatorGUI

    def generatePixelArt(self, filePath):
        # If we're about to go over the prop count with this image, let the player know
        if len(list(self.propListNew.keys())) + (64 * 64) >= PropGlobals.MaxPropCountHard and not __debug__:
            self.propMessage(ToontownGlobals.PIXEL_ART_OVERFLOW)
            return

        # Load the image from filepath
        image = PNMImage()

        # If we're unsuccessful, display an error message
        if not image.read(filePath):
            self.propMessage(ToontownGlobals.PIXEL_ART_ERROR)
            return

        # Convert our image to 64 x 64
        image = self.resizeImage(image, 64, 64)

        # Get the width, height, and alpha
        width, height = image.get_size()
        has_alpha = image.has_alpha()

        # Get our avatar's position to place the pixel art relative to them
        xPos, yPos, zPos = base.localAvatar.getPos()

        # A flag used for determining the fist pixel generated by this function
        # This is useful if we ever want to have everything else reparent to it
        # Right now though, reparenting is messy, so we wont do that
        # primary = None

        # Iterate over each pixel and spawn a prop that represents it
        for x in range(width):
            # Move the pixel over by 1 for each time we shift on the x-ais
            xPos += 1

            # Reset the z-axis each time we shift over on the x-axis
            z = zPos + height + 1

            # Iterate over the pixels on the y-axis
            for y in range(height):
                # Move the pixel down by 1
                z -= 1

                if has_alpha:
                    # Grab the RGB or palette index of the pixel
                    r, g, b, a = image.get_xel_a(x, y)  # already in 0..1 range

                    # We have an alpha value and it's 0, so this pixel is completely transparent
                    if a == 0:
                        continue
                else:
                    r, g, b = image.get_xel(x, y)  # already in 0..1 range
                    # No alpha channel in the image; just set it to 1
                    a = 1

                # Generate prop info for the pixel
                propName = 'Cube'
                # Set the primary pixel if it hasn't been set yet
                # if not primary:
                #    primary = len(self.propList)

                # Load the prop
                self.d_loadPropsFromFile(str(uuid.uuid4()), propName, (xPos, yPos, z), (0, 0, 0), (1.0, 1.0, 1.0),
                                         json.dumps({
                                             'color_scale': (r, g, b, a),
                                             'spawned_by_name': base.localAvatar.getName(),
                                             'spawned_by_avid': base.localAvatar.getDoId(),
                                             'spawned_on': datetime.now().timestamp()
                                         }))

        # Save all of the props in the zone
        # self.d_requestPropSave()

    def resizeImage(self, image, x_size, y_size):
        if image.get_x_size() <= x_size and image.get_y_size() <= y_size:
            # This image does not need to be resized!
            return image

        x_size = min(image.get_x_size(), x_size)
        y_size = min(image.get_y_size(), y_size)
        new_image = PNMImage(x_size, y_size, image.get_num_channels(), image.get_maxval(), image.get_type())
        new_image.quick_filter_from(image)
        return new_image

    def requestUpdateProp(self, propUUID: str):
        """
        === Send to Server ===
        Tell the server that we want to update a prop
        :param propUUID:
        """
        if propUUID in self.propListNew:
            prop = self.propListNew[propUUID]
            pos = prop.newPropPos if prop.newPropPos else prop.getPos()
            hpr = prop.newPropHpr if prop.newPropHpr else prop.getHpr()
            scale = prop.newPropScale if prop.newPropScale else prop.getScale()
            prop.data['color_scale'] = prop.newPropColor if prop.newPropColor else [prop.getColorScale()[0], prop.getColorScale()[1],
                                                                                    prop.getColorScale()[2], prop.getColorScale()[3]]
            prop.data['edited_on'] = datetime.now().timestamp()
            prop.data['edited_by_avid'] = base.localAvatar.getDoId()
            prop.data['edited_by_name'] = base.localAvatar.getName()
            data = json.dumps(prop.data)
            self.sendUpdate('requestUpdateProp', [propUUID, pos, hpr, scale, data])

    def updatePropNew(self, propUUID: str, pos: Vec3F, hpr: Vec3F, scale: Vec3F, data: bytes):
        """
        === Sent from Server ===
        Server told us that a prop has been updated
        """
        data = json.loads(data)
        if propUUID in self.propListNew:
            self.propListNew[propUUID].update(pos, hpr, scale, data)

        self.updatePropCount()

    def requestDuplicateProp(self, propUUID: str, newPos: Vec3F, newHpr: Vec3F, newScale: Vec3F, newColorScale: Vec3F):
        if propUUID in self.propListNew:
            self.sendUpdate('requestDuplicateProp', [propUUID, newPos, newHpr, newScale, newColorScale])

    def exportToBam(self):
        filenameStr = 'props/' + datetime.now().strftime(f'PROPGEN_EXPORT_{PropGlobals.PropGenVersion}'
                                                         f'%a-%b-%d-%H-%M-%S-%Y-{globalClock.getFrameCount()}.bam')
        result = self.propNode.writeBamFile(Filename.fromOsSpecific(filenameStr))
        if result:
            base.localAvatar.setSystemMessage(0, f'$EXPORTED BAM AS {filenameStr}')
        else:
            base.localAvatar.setSystemMessage(0, '$UNABLE TO EXPORT: REASON UNKNOWN')

    def setMaxPropCount(self, maxPropCount):
        self.maxPropCount = maxPropCount

    def getMaxPropCount(self):
        return self.maxPropCount

    def setRotateWidgetVisible(self, state: bool):
        if self.rotateWidgetVisible != state:
            self.rotateWidgetVisible = state
            if state:
                DistributedPropGenerator.rotationWidget.reparentTo(self.sampleProp)
            else:
                DistributedPropGenerator.rotationWidget.reparentTo(base.hidden)