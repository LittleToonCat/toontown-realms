from panda3d.core import *
from direct.actor import Actor
from direct.directnotify import DirectNotifyGlobal

from toontown.sandbox import PropGlobals
from otp.otpbase import OTPGlobals
from toontown.toonbase import ToontownGlobals, ClientSettings
import random


class PropPool:
    notify = DirectNotifyGlobal.directNotify.newCategory('PropPool')

    def __init__(self):
        self.props = {}
        self.propCache = []
        self.propStrings = {}
        self.propTypes = {}
        self.propScales = {}
        self.maxPoolSize = base.config.GetInt('prop-pool-size', 8)
        for p in ToontownGlobals.Props:
            phase = p[0]
            propName = p[1].lower()
            modelName = p[2]
            if len(p) == 4:
                animName = p[3]
                propPath = self.getPath(phase, modelName)
                animPath = self.getPath(phase, animName)
                self.propTypes[propName] = 'actor'
                self.propStrings[propName] = (propPath, animPath)
                self.propScales[propName] = 1.0
            else:
                propPath = self.getPath(phase, modelName)
                self.propTypes[propName] = 'model'
                self.propStrings[propName] = (propPath,)
                self.propScales[propName] = 1.0

        for prop in ToontownGlobals.PropsBattle:
            name = prop[0].lower()
            type = prop[1]
            self.propTypes[name] = type
            self.propStrings[name] = prop[2]
            if len(prop) == 4 and isinstance(prop[3], float):
                self.propScales[name] = prop[3]
            elif len(prop) == 5 and isinstance(prop[4], float):
                self.propScales[name] = prop[4]
            else:
                self.propScales[name] = 1.0

        for prop in PropGlobals.PropList:
            type = prop[0]

    def getPath(self, phase, model):
        return 'phase_%s/models/props/%s' % (phase, model)

    def makeVariant(self, name):
        name = name.lower()
        if name == 'tart':
            self.props[name].setScale(0.5)
        elif name == 'fruitpie':
            self.props[name].setScale(0.75)
        elif name == 'double-windsor':
            self.props[name].setScale(1.5)
        elif name[:6] == 'splat-':
            prop = self.props[name]
            scale = prop.getScale() * ToontownGlobals.Splats[name[6:]][0]
            prop.setScale(scale)
            prop.setColor(ToontownGlobals.Splats[name[6:]][1])
        elif name == 'splash-from-splat':
            self.props[name].setColor(0.75, 0.75, 1.0, 1.0)
        elif name == 'clip-on-tie':
            tie = self.props[name]
            tie.getChild(0).setHpr(23.86, -16.03, 9.18)
        elif name == 'small-magnet':
            self.props[name].setScale(0.5)
        elif name == 'shredder-paper':
            paper = self.props[name]
            paper.setPosHpr(2.22, -0.95, 1.16, -48.61, 26.57, -111.51)
            paper.flattenMedium()
        elif name == 'lips':
            lips = self.props[name]
            lips.setPos(0, 0, -3.04)
            lips.flattenMedium()
        elif name == '5dollar':
            tex = loader.loadTexture('phase_5/maps/dollar_5.png')
            tex.setMinfilter(Texture.FTLinearMipmapLinear)
            tex.setMagfilter(Texture.FTLinear)
            self.props[name].setTexture(tex, 1)
        elif name == '10dollar':
            tex = loader.loadTexture('phase_5/maps/dollar_10.png')
            tex.setMinfilter(Texture.FTLinearMipmapLinear)
            tex.setMagfilter(Texture.FTLinear)
            self.props[name].setTexture(tex, 1)
        elif name == 'dust':
            bin = 110
            for cloudNum in range(1, 12):
                cloudName = '**/cloud' + str(cloudNum)
                cloud = self.props[name].find(cloudName)
                cloud.setBin('fixed', bin)
                bin -= 10
        elif name == 'kapow':
            l = self.props[name].find('**/letters')
            l.setBin('fixed', 20)
            e = self.props[name].find('**/explosion')
            e.setBin('fixed', 10)
        elif name == 'suit_explosion':
            joints = ['**/joint_scale_POW', '**/joint_scale_BLAM', '**/joint_scale_BOOM']
            joint = random.choice(joints)
            self.props[name].find(joint).hide()
            joints.remove(joint)
            joint = random.choice(joints)
            self.props[name].find(joint).hide()
        elif name == 'quicksand' or name == 'trapdoor':
            p = self.props[name]
            p.setBin('shadow', -5)
            p.setDepthWrite(0)
            p.getChild(0).setPos(0, 0, OTPGlobals.FloorOffset)
        elif name == 'traintrack' or name == 'traintrack2':
            prop = self.props[name]
            prop.find('**/tunnel3').hide()
            prop.find('**/tunnel2').hide()
            prop.find('**/tracksA').setPos(0, 0, OTPGlobals.FloorOffset)
        elif name == 'geyser':
            p = self.props[name]
            s = SequenceNode('geyser')
            p.findAllMatches('**/Splash*').reparentTo(NodePath(s))
            s.loop(0)
            s.setFrameRate(12)
            p.attachNewNode(s)
        elif name == 'ship':
            self.props[name] = self.props[name].find('**/ship_gag')
        elif name == 'streetlight':
            self.props[name] = self.props[name].find('**/prop_post_sign')
        elif name == 'globe':
            globe = self.props[name]
            collisionMesh = globe.find('**/collisionMesh')
            collisionMesh.hide()
        elif name == 'sellbot table':
            self.props[name] = self.props[name].find('**/table')
        elif name == 'sellbot monitor 1':
            self.props[name] = self.props[name].find('**/stocks_monitor')
        elif name == 'sellbot monitor 2':
            self.props[name] = self.props[name].find('**/value_monitor')
        elif name == 'sellbot lamp':
            self.props[name] = self.props[name].find('**/lamp')
        elif name == 'sellbot cabinet':
            self.props[name] = self.props[name].find('**/cabient')
        elif name == 'tree':
            self.props[name] = self.props[name].find('**/prop_leaves_large_ul_brickbox_6')
        elif name == 'transparent cube':
            cube = self.props[name]
            cube.setTransparency(1)
            cube.setColorScale(1.0, 1.0, 1.0, 0.5)
            cube.flattenLight()
        elif name == 'cashbot highrise 1':
            self.props[name] = self.props[name].find('**/BLD1')
        elif name == 'cashbot highrise 2':
            self.props[name] = self.props[name].find('**/BLD5')
        elif name == 'cashbot highrise 3':
            self.props[name] = self.props[name].find('**/BLD19')
        elif name == 'cashbot highrise 4':
            self.props[name] = self.props[name].find('**/BLD16')
        elif name == 'cashbot highrise 5':
            self.props[name] = self.props[name].find('**/BLD8')
        elif name == 'cashbot highrise 6':
            self.props[name] = self.props[name].find('**/BLD9')
        elif name == 'cashbot highrise 7':
            self.props[name] = self.props[name].find('**/BLD4')
        elif name == 'cashbot highrise 8':
            self.props[name] = self.props[name].find('**/BLD10')
        elif name == 'cashbot highrise 9':
            self.props[name] = self.props[name].find('**/BLD17')
        elif name == 'cashbot highrise 10':
            self.props[name] = self.props[name].find('**/BLD18')
        elif name == 'cashbot highrise 11':
            self.props[name] = self.props[name].find('**/BLD13')
        elif name == 'cashbot highrise 12':
            self.props[name] = self.props[name].find('**/BLD14')
        elif name == 'cashbot highrise 13':
            self.props[name] = self.props[name].find('**/BLD15')
        elif name == 'cashbot highrise 14':
            self.props[name] = self.props[name].find('**/BLD11')
        elif name == 'cashbot highrise 15':
            self.props[name] = self.props[name].find('**/BLD12')
        elif name == 'cashbot highrise 16':
            self.props[name] = self.props[name].find('**/BLD20')
        elif name == 'lawbot highrise 1':
            self.props[name] = self.props[name].find('**/LB_BLD1')
        elif name == 'lawbot highrise 2':
            self.props[name] = self.props[name].find('**/LB_BLD5')
        elif name == 'lawbot highrise 3':
            self.props[name] = self.props[name].find('**/LB_BLD19')
        elif name == 'lawbot highrise 4':
            self.props[name] = self.props[name].find('**/LB_BLD16')
        elif name == 'lawbot highrise 5':
            self.props[name] = self.props[name].find('**/LB_BLD8')
        elif name == 'lawbot highrise 6':
            self.props[name] = self.props[name].find('**/LB_BLD9')
        elif name == 'lawbot highrise 7':
            self.props[name] = self.props[name].find('**/LB_BLD4')
        elif name == 'lawbot highrise 8':
            self.props[name] = self.props[name].find('**/LB_BLD10')
        elif name == 'lawbot highrise 9':
            self.props[name] = self.props[name].find('**/LB_BLD17')
        elif name == 'lawbot highrise 10':
            self.props[name] = self.props[name].find('**/LB_BLD18')
        elif name == 'lawbot highrise 11':
            self.props[name] = self.props[name].find('**/LB_BLD13')
        elif name == 'lawbot highrise 12':
            self.props[name] = self.props[name].find('**/LB_BLD14')
        elif name == 'lawbot highrise 13':
            self.props[name] = self.props[name].find('**/LB_BLD15')
        elif name == 'lawbot highrise 14':
            self.props[name] = self.props[name].find('**/LB_BLD11')
        elif name == 'lawbot highrise 15':
            self.props[name] = self.props[name].find('**/LB_BLD12')
        elif name == 'lawbot highrise 16':
            self.props[name] = self.props[name].find('**/LB_BLD20')
        elif name == 'lawbot highrise 17':
            self.props[name] = self.props[name].find('**/LB_BLD21')
        elif name == 'lawbot highrise 18':
            self.props[name] = self.props[name].find('**/LB_BLD22')
        elif name == 'lawbot highrise 19':
            self.props[name] = self.props[name].find('**/LB_BLD23')
        elif name == 'umbrella':
            self.props[name] = self.props[name].find('**/open_umbrella')
        elif name == 'cactus 1':
            self.props[name] = self.props[name].find('**/cactus_a')
        elif name == 'cactus 2':
            self.props[name] = self.props[name].find('**/cactus_b')

    def unloadProps(self):
        for p in list(self.props.values()):
            if type(p) != type(()):
                self.__delProp(p)

        self.props = {}
        self.propCache = []

    def getProp(self, name):
        return self.__getPropCopy(name)

    def __getPropCopy(self, name):
        if self.propTypes[name] == 'actor':
            if name not in self.props:
                prop = Actor.Actor()
                prop.loadModel(self.propStrings[name][0])
                animDict = {}
                animDict[name] = self.propStrings[name][1]
                prop.loadAnims(animDict)
                prop.setScale(self.propScales[name])
                prop.flattenLight()
                prop.setName(name)
                prop.setBlend(frameBlend=ClientSettings.SmoothAnimations.get())
                self.storeProp(name, prop)
                if name in PropGlobals.Variants:
                    self.makeVariant(name)
            return Actor.Actor(other=self.props[name])
        else:
            if name not in self.props:
                prop = loader.loadModel(self.propStrings[name][0])
                prop.setScale(self.propScales[name])
                prop.flattenLight()
                prop.setName(name)
                self.storeProp(name, prop)
                if name in PropGlobals.Variants:
                    self.makeVariant(name)
            return self.props[name].copyTo(hidden)

    def storeProp(self, name, prop):
        self.props[name] = prop
        self.propCache.append(prop)
        if len(self.props) > self.maxPoolSize:
            oldest = self.propCache.pop(0)
            del self.props[oldest.getName()]
            self.__delProp(oldest)
        self.notify.debug(f'props = {self.props}')
        self.notify.debug(f'propCache = {self.propCache}')

    def getPropType(self, name):
        return self.propTypes[name]

    def __delProp(self, prop):
        if prop == None:
            self.notify.warning('tried to delete null prop!')
            return
        if isinstance(prop, Actor.Actor):
            prop.delete()
        else:
            prop.removeNode()
        return


globalPropPool = PropPool()
