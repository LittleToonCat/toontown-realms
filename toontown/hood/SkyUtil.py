from panda3d.core import *
from toontown.toonbase.ToontownGlobals import *
from direct.task.Task import Task
from direct.directnotify import DirectNotifyGlobal
notify = DirectNotifyGlobal.directNotify.newCategory('SkyUtil')

def noCloudSkyTrack(task):
    task.h += globalClock.getDt() * 0.3
    if task.sky.isEmpty():
        notify.warning("Couldn't find sky!")
        return Task.done
    task.sky.setH(task.h)
    return Task.cont

def singleCloudSkyTrack(task):
    task.h += globalClock.getDt() * 0.25
    if task.clouds.isEmpty():
        notify.warning("Couldn't find clouds!")
        return Task.done
    task.clouds.setH(task.h)
    return Task.cont

def cloudSkyTrack(task):
    task.h += globalClock.getDt() * 0.25
    if task.cloud1.isEmpty() or task.cloud2.isEmpty():
        notify.warning("Couldn't find clouds!")
        return Task.done
    task.cloud1.setH(task.h)
    task.cloud2.setH(-task.h * 0.8)
    return Task.cont


def startCloudSky(hood, parent = camera, effects = CompassEffect.PRot | CompassEffect.PZ):
    hood.sky.reparentTo(parent)
    hood.sky.setDepthTest(0)
    hood.sky.setDepthWrite(0)
    hood.sky.setBin('background', 100)
    hood.sky.find('**/Sky').reparentTo(hood.sky, -1)
    hood.sky.reparentTo(parent)
    hood.sky.setZ(0.0)
    hood.sky.setHpr(0.0, 0.0, 0.0)
    ce = CompassEffect.make(NodePath(), effects)
    hood.sky.node().setEffect(ce)
    skyTrackTask = Task(hood.skyTrack)
    skyTrackTask.h = 0
    skyTrackTask.cloud1 = hood.sky.find('**/cloud1')
    skyTrackTask.cloud2 = hood.sky.find('**/cloud2')
    if not skyTrackTask.cloud1.isEmpty() and not skyTrackTask.cloud2.isEmpty():
        taskMgr.add(skyTrackTask, 'skyTrack')
    else:
        notify.warning("Couldn't find clouds!")

def startSingleCloudSky(hood, parent = camera, effects = CompassEffect.PRot | CompassEffect.PZ):
    hood.sky.reparentTo(parent)
    hood.sky.setDepthTest(0)
    hood.sky.setDepthWrite(0)
    hood.sky.setBin('background', 100)
    hood.sky.find('**/Sky').reparentTo(hood.sky, -1)
    hood.sky.reparentTo(parent)
    hood.sky.setZ(0.0)
    hood.sky.setHpr(0.0, 0.0, 0.0)
    ce = CompassEffect.make(NodePath(), effects)
    hood.sky.node().setEffect(ce)
    skyTrackTask = Task(hood.skyTrackSingle)
    skyTrackTask.h = 0
    skyTrackTask.clouds = hood.sky.find('**/clouds')
    skyTrackTask.clouds.setBin('background', 101)
    if not skyTrackTask.clouds.isEmpty():
        taskMgr.add(skyTrackTask, 'skyTrack')
    else:
        notify.warning("Couldn't find clouds!")

def startNoCloudSky(hood, parent = camera, effects = CompassEffect.PRot | CompassEffect.PZ):
    hood.sky.reparentTo(parent)
    hood.sky.setDepthTest(0)
    hood.sky.setDepthWrite(0)
    hood.sky.setBin('background', 100)
    hood.sky.find('**/Sky').reparentTo(hood.sky, -1)
    hood.sky.reparentTo(parent)
    hood.sky.setZ(0.0)
    hood.sky.setHpr(0.0, 0.0, 0.0)
    ce = CompassEffect.make(NodePath(), effects)
    hood.sky.node().setEffect(ce)
    skyTrackTask = Task(hood.skyTrackNoClouds)
    skyTrackTask.h = 0
    skyTrackTask.sky = hood.sky
    if not hood.sky.isEmpty():
        taskMgr.add(skyTrackTask, 'skyTrack')
    else:
        notify.warning("Couldn't find sky!")
