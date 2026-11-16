from toontown.toonbase.ToonBase import *
from panda3d.toontown import *
from toontown.toonbase.ToontownGlobals import *
import random
from direct.task.Task import Task
from direct.actor.Actor import Actor
from direct.distributed import DistributedObject
from direct.gui.OnscreenImage import OnscreenImage
from . import ToonInteriorColors
from toontown.toonbase import TTLocalizer, ClientSettings


class DistributedHQInterior(DistributedObject.DistributedObject):
    starGui = loader.loadModel('phase_3.5/models/gui/ttrm_m_gui_nameStar', allowInstance = True)

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        self.dnaStore = cr.playGame.dnaStore
        self.leaderAvIds = []
        self.leaderNames = []
        self.leaderScores = []
        self.numLeaders = 10
        self.tutorial = 0

    def generate(self):
        DistributedObject.DistributedObject.generate(self)
        self.interior = loader.loadModel('phase_3.5/models/modules/HQ_interior')
        self.interior.reparentTo(render)
        self.interior.find('**/cream').hide()
        self.interior.find('**/crashed_piano').hide()
        self.buildLeaderBoard()
        self.pillar = loader.loadModel('phase_3.5/models/props/HQ_pillar')
        self.periscope = Actor('phase_3.5/models/props/HQ_periscope-base-mod',
                               {'anim': 'phase_3.5/models/props/HQ_periscope-base-chan'})
        self.periscope.setPos(-5.25, 30.2, 6.5)
        self.periscope.setScale(0.75)
        self.periscope.setBlend(frameBlend=ClientSettings.SmoothAnimations.get())

    def announceGenerate(self):
        DistributedObject.DistributedObject.announceGenerate(self)
        self.setupDoors()
        self.interior.flattenMedium()
        emptyBoard = self.interior.find('**/empty_board')
        self.leaderBoard.reparentTo(emptyBoard.getChild(0))
        # Maybe in the future we could make the Periscope NPCs an actual NPC type, instead of just client-sided
        # We could then add additional functions to them, such as having them speak dialogue about the current
        # Cog Invasion that is going on, and possibly even more
        if config.GetBool('want-periscope-npcs', True):
            self.interior.find('**/periscope').hide()
            self.pillar.reparentTo(render)
            self.periscope.reparentTo(render)
            self.periscope.loop('anim')

    def setTutorial(self, flag):
        if self.tutorial == flag:
            return
        else:
            self.tutorial = flag
        if self.tutorial:
            self.interior.find('**/periscope').hide()
            self.interior.find('**/speakers').hide()
            self.pillar.hide()
            self.periscope.hide()
        else:
            self.interior.find('**/periscope').show()
            self.interior.find('**/speakers').show()

    def getTutorial(self):
        return self.tutorial

    def setZoneIdAndBlock(self, zoneId, block):
        self.zoneId = zoneId
        self.block = block

    def buildLeaderBoard(self):
        self.leaderBoard = hidden.attachNewNode('leaderBoard')
        self.leaderBoard.setPosHprScale(0.1, 0, 4.5, 90, 0, 0, 0.9, 0.9, 0.9)
        z = 0
        row = self.buildTitleRow()
        row.reparentTo(self.leaderBoard)
        row.setPos(0, 0, z)
        z -= 1
        self.nameTextNodes = []
        self.scoreTextNodes = []
        self.trophyStars = []
        for i in range(self.numLeaders):
            row, nameText, scoreText, trophyStar = self.buildLeaderRow()
            self.nameTextNodes.append(nameText)
            self.scoreTextNodes.append(scoreText)
            self.trophyStars.append(trophyStar)
            row.reparentTo(self.leaderBoard)
            row.setPos(0, 0, z)
            z -= 1

    def updateLeaderBoard(self):
        taskMgr.remove(self.uniqueName('starSpinHQ'))
        numNames = len(self.leaderNames)
        if numNames > 10:
            numNames = 1
        for i in range(numNames):
            name = self.leaderNames[i]
            score = self.leaderScores[i]
            self.nameTextNodes[i].setText(name)
            self.scoreTextNodes[i].setText(str(score))
            self.updateTrophyStar(self.trophyStars[i], score)

        for i in range(len(self.leaderNames), self.numLeaders):
            self.nameTextNodes[i].setText('-')
            self.scoreTextNodes[i].setText('-')
            self.trophyStars[i].hide()

    def buildTitleRow(self):
        row = hidden.attachNewNode('leaderRow')
        nameText = TextNode('titleRow')
        nameText.setFont(ToontownGlobals.getSignFont())
        nameText.setAlign(TextNode.ACenter)
        nameText.setTextColor(0.5, 0.75, 0.7, 1)
        nameText.setText(TTLocalizer.LeaderboardTitle)
        namePath = row.attachNewNode(nameText)
        namePath.setPos(0, 0, 0)
        return row

    def buildLeaderRow(self):
        row = hidden.attachNewNode('leaderRow')
        nameText = TextNode('nameText')
        nameText.setFont(ToontownGlobals.getToonFont())
        nameText.setAlign(TextNode.ALeft)
        nameText.setTextColor(1, 1, 1, 0.7)
        nameText.setText('-')
        namePath = row.attachNewNode(nameText)
        namePath.setPos(*TTLocalizer.DHQInamePathPos)
        namePath.setScale(TTLocalizer.DHQInamePath)
        scoreText = TextNode('scoreText')
        scoreText.setFont(ToontownGlobals.getToonFont())
        scoreText.setAlign(TextNode.ARight)
        scoreText.setTextColor(1, 1, 0.1, 0.7)
        scoreText.setText('-')
        scorePath = row.attachNewNode(scoreText)
        scorePath.setPos(*TTLocalizer.DHQIscorePathPos)
        trophyStar = self.buildTrophyStar()
        trophyStar.reparentTo(row)
        return (row,
         nameText,
         scoreText,
         trophyStar)

    def setLeaderBoard(self, avIds, names, scores):
        self.notify.debug('setLeaderBoard: avIds: %s, names: %s, scores: %s' % (avIds, names, scores))
        self.leaderAvIds = avIds
        newNames = []
        for name in names:
            for emoji in base.emojis:
                name = name.replace(f':{emoji}:', f'\x01white\x01\5{emoji}\5\x02')
            if base.cr.getChatFilterMode() >= CHAT_FILTER_CENSOR:
                name = base.profanityFilter.censor(name)
            newNames.append(name)
        self.leaderNames = newNames
        self.leaderScores = scores
        self.updateLeaderBoard()

    def chooseDoor(self):
        doorModelName = 'door_double_round_ul'
        if doorModelName[-1:] == 'r':
            doorModelName = doorModelName[:-1] + 'l'
        else:
            doorModelName = doorModelName[:-1] + 'r'
        door = self.dnaStore.findNode(doorModelName)
        return door

    def setupDoors(self):
        self.randomGenerator = random.Random()
        self.randomGenerator.seed(self.zoneId)
        self.colors = ToonInteriorColors.colors[ToontownCentral]
        door = self.chooseDoor()
        doorOrigins = render.findAllMatches('**/door_origin*')
        numDoorOrigins = doorOrigins.getNumPaths()
        for npIndex in range(numDoorOrigins):
            doorOrigin = doorOrigins[npIndex]
            doorOriginNPName = doorOrigin.getName()
            doorOriginIndexStr = doorOriginNPName[len('door_origin_'):]
            newNode = ModelNode('door_' + doorOriginIndexStr)
            newNodePath = NodePath(newNode)
            newNodePath.reparentTo(self.interior)
            doorNP = door.copyTo(newNodePath)
            doorOrigin.setScale(0.8, 0.8, 0.8)
            doorOrigin.setPos(doorOrigin, 0, -0.025, 0)
            doorColor = self.randomGenerator.choice(self.colors['TI_door'])
            # Small hack to make doors work a little better with the interact key
            doorNP.find('door_*_trigger').setScale(2)
            triggerId = str(self.block) + '_' + doorOriginIndexStr
            DNADoor.setupDoor(doorNP, newNodePath, doorOrigin, self.dnaStore, triggerId, doorColor)
            doorFrame = doorNP.find('door_*_flat')
            doorFrame.setColor(doorColor)

        del self.dnaStore
        del self.randomGenerator

    def disable(self):
        self.leaderBoard.removeNode()
        del self.leaderBoard
        self.interior.removeNode()
        del self.interior
        del self.nameTextNodes
        del self.scoreTextNodes
        del self.trophyStars
        self.pillar.removeNode()
        del self.pillar
        self.periscope.delete()
        del self.periscope
        taskMgr.remove(self.uniqueName('starSpinHQ'))
        DistributedObject.DistributedObject.disable(self)

    def buildTrophyStar(self):
        trophyStar = OnscreenImage(image = self.starGui.find('**/star_normal'), pos = TTLocalizer.DHQItrophyStarPos)
        trophyStar.hide()
        return trophyStar

    def updateTrophyStar(self, trophyStar, score):
        scale = 0.8
        if score >= ToontownGlobals.TrophyStarLevels[6]:
            trophyStar['image'] = self.starGui.find('**/star_diamond')
            trophyStar.show()
            if score >= ToontownGlobals.TrophyStarLevels[7]:
                task = taskMgr.add(self.__starSpin, self.uniqueName('starSpinHQ'))
                task.trophyStarSpeed = 15
                task.trophyStar = trophyStar
        elif score >= ToontownGlobals.TrophyStarLevels[4]:
            trophyStar['image'] = self.starGui.find('**/star_normal')
            trophyStar.show()
            trophyStar.setScale(scale)
            trophyStar.setColor(ToontownGlobals.TrophyStarColors[4])
            if score >= ToontownGlobals.TrophyStarLevels[5]:
                task = taskMgr.add(self.__starSpin, self.uniqueName('starSpinHQ'))
                task.trophyStarSpeed = 15
                task.trophyStar = trophyStar
        elif score >= ToontownGlobals.TrophyStarLevels[2]:
            trophyStar['image'] = self.starGui.find('**/star_normal')
            trophyStar.show()
            trophyStar.setScale(0.75 * scale)
            if score >= ToontownGlobals.TrophyStarLevels[3]:
                task = taskMgr.add(self.__starSpin, self.uniqueName('starSpinHQ'))
                task.trophyStarSpeed = 10
                task.trophyStar = trophyStar
        elif score >= ToontownGlobals.TrophyStarLevels[0]:
            trophyStar.show()
            trophyStar.setScale(0.75 * scale)
            trophyStar.setColor(ToontownGlobals.TrophyStarColors[0])
            if score >= ToontownGlobals.TrophyStarLevels[1]:
                task = taskMgr.add(self.__starSpin, self.uniqueName('starSpinHQ'))
                task.trophyStarSpeed = 8
                task.trophyStar = trophyStar
        else:
            trophyStar.hide()

    def __starSpin(self, task):
        now = globalClock.getFrameTime()
        r = now * task.trophyStarSpeed % 360.0
        task.trophyStar.setR(r)
        return Task.cont
