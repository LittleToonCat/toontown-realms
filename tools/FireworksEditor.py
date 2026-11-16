""" Fireworks Editor/Control Panel module """
from panda3d.core import Point3, Filename, Vec3, CSDefault, VirtualFileSystem, loadPrcFile, ConfigVariableList, WindowProperties
from panda3d.toontown import loadDNAFile, DNAStorage

from tkinter import CURRENT, IntVar, Frame, TOP, X, BOTH, LEFT, W, Button, Radiobutton, Label, CENTER, S, N, GROOVE, VERTICAL
from tkinter.filedialog import asksaveasfilename, askopenfilename
from tkinter.messagebox import askyesno

import Pmw

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.interval.IntervalGlobal import Sequence, Func, Wait, LerpFunctionInterval, Parallel
from direct.showbase.ShowBase import ShowBase
from direct.tkwidgets.AppShell import AppShell
from direct.tkwidgets import Slider
from direct.tkwidgets import VectorWidgets

from otp.otpbase.PythonUtil import cmp_to_key

from toontown.effects import Fireworks
from toontown.effects.FireworkGlobals import *

NUM_RB_COLS = 8
MAX_AMP = 100

loadPrcFile('fireworkseditor.prc')

vfs = VirtualFileSystem.getGlobalPtr()

ttmodelsDirectory = vfs.getCwd()

# The VirtualFileSystem, which has already initialized, doesn't see the mount
# directives in the config(s) yet. We have to force it to load those manually:
mounts = ConfigVariableList('vfs-mount')
for mount in mounts:
    mountFile, mountPoint = (mount.split(' ', 2) + [None, None, None])[:2]
    vfs.mount(Filename(mountFile), Filename(mountPoint), 0)

notify = directNotify.newCategory('FireworksEditor')


def fwTuple2Str(tuple):
    styleStr = styleNames[tuple[FW_STYLE]]
    color1Str = ColorNames[tuple[FW_COLOR1]].upper()
    color2Str = ColorNames[tuple[FW_COLOR2]].upper()
    return '(%0.2f, %s, %s, %s, %0.2f, %0.2f, %0.2f, %0.2f)' % (
        tuple[FW_T], styleStr, color1Str, color2Str, tuple[FW_AMP],
        tuple[FW_POS_X], tuple[FW_POS_Y], tuple[FW_POS_Z])


class FireworkParams:
    def __init__(self, ID, style=CIRCLE, startTime=0, pos=Point3(0),
                 color1=0, color2=0, amp=10.0):
        self.ID = ID
        self.style = style
        self.startTime = startTime
        self.pos = pos
        self.color1 = color1
        self.color2 = color2
        self.amp = amp

    def setID(self, ID):
        self.ID = ID

    def getID(self):
        return self.ID

    def setStyle(self, style):
        self.style = style

    def getStyle(self):
        return self.style

    def setStartTime(self, startTime):
        self.startTime = startTime

    def getStartTime(self):
        return self.startTime

    def setPos(self, x, y, z):
        self.pos.set(x, y, z)

    def getPos(self):
        return self.pos

    def setColor1(self, color1):
        self.color1 = color1

    def getColor1(self):
        return self.color1

    def setColor2(self, color2):
        self.color2 = color2

    def getColor2(self):
        return self.color2

    def setAmp(self, amp):
        self.amp = amp

    def getAmp(self):
        return self.amp

    def asTuple(self):
        return (self.startTime, self.style, self.color1, self.color2,
                self.amp, self.pos[0], self.pos[1], self.pos[2])

    def __repr__(self):
        styleStr = styleNames[self.style]
        color1Str = ColorNames[self.color1].upper()
        color2Str = ColorNames[self.color2].upper()
        return '( %0.2f, %s, %s, %s, %0.2f, %0.2f, %0.2f, %0.2f )' % (
            self.startTime, styleStr, color1Str, color2Str, self.amp,
            self.pos[0], self.pos[1], self.pos[2])


class FireworksShow:
    fireworkID = 0

    def __init__(self, editor):
        self.editor = editor
        self.fwDict = {}
        self.fwIval = None
        self.fPlayingIval = 0
        self.musicFilename = None
        self.showMusic = None
        self.minDuration = 60.0

    def createFirework(self, startTime, style, pos, color1, color2, amp):
        # Generate unique ID
        ID = FireworksShow.fireworkID
        FireworksShow.fireworkID += 1
        fw = FireworkParams(ID, startTime=startTime,
                            style=style,
                            pos=pos,
                            color1=color1,
                            color2=color2,
                            amp=amp)
        self.fwDict[ID] = fw
        notify.debug('Created firework.')
        return fw

    def getFirework(self, ID):
        return self.fwDict.get(ID, None)

    def removeFirework(self, ID):
        if ID in self.fwDict:
            del self.fwDict[ID]

    def getSortedList(self):
        def sortFW(a, b):
            startA = a.asTuple()[0]
            startB = b.asTuple()[0]
            if startA < startB:
                return -1
            elif startA > startB:
                return 1
            else:
                return 0

        # Sort the firework show by start time
        fwList = list(self.fwDict.values())
        fwList.sort(key=cmp_to_key(sortFW))
        return fwList

    def getNextFirework(self, currFw):
        fwList = self.getSortedList()
        if currFw:
            currT = currFw.getStartTime()
            currID = currFw.getID()
            for fw in fwList:
                if fw.getID() == currID:
                    continue
                if fw.getStartTime() >= currT:
                    return fw
        elif fwList:
            return fwList[0]
        else:
            return None

    def getPrevFirework(self, currFw):
        fwList = self.getSortedList()
        if currFw:
            fwList.reverse()
            currT = currFw.getStartTime()
            currID = currFw.getID()
            for fw in fwList:
                if fw.getID() == currID:
                    continue
                if fw.getStartTime() <= currT:
                    return fw
        elif fwList:
            return fwList[-1]
        else:
            return None

    def getShow(self):
        fwList = self.getSortedList()
        fwShowList = []
        startT = 0.0
        for fw in fwList:
            fwTuple = fw.asTuple()
            deltaT = fwTuple[FW_T] - startT
            startT = fwTuple[FW_T]
            fwShowList.append((deltaT,) + fwTuple[1:])
        return fwShowList

    def setMinDuration(self, duration):
        self.minDuration = duration

    def getDuration(self):
        musicDuration = 0.0
        fwDuration = 0.0
        if self.showMusic:
            musicDuration = self.showMusic.length()
        fwList = self.getSortedList()
        if fwList:
            fwDuration = fwList[-1].getStartTime()
        return max(self.minDuration, musicDuration, fwDuration)

    def printShow(self):
        printOut = '('
        for fw in self.getShow():
            printOut += '%s,' % (fwTuple2Str(fw))
        printOut += ')'
        notify.info(printOut)

    def saveShow(self, fireworksFilename):
        fname = Filename(fireworksFilename)
        f = open(fname.toOsSpecific(), 'wb')
        if self.musicFilename:
            f.write(bytes('MUSICFILE: %s\n' % self.musicFilename.toOsSpecific(), encoding='utf-8'))
        for fw in self.getShow():
            f.write(bytes('FIREWORKS: %s\n' % fwTuple2Str(fw), encoding='utf-8'))
        f.close()

    def loadShow(self, fireworksFilename):
        self.clearShow()
        fname = Filename(fireworksFilename)
        f = open(fname.toOsSpecific(), 'r')
        rawData = f.readlines()
        f.close()
        currentT = 0.0
        notify.info('Loading %s...' % fname.getBasename())
        for line in rawData:
            # First strip whitespace from both ends of line
            lineStipped = line.strip()
            if lineStipped and (len(lineStipped) > 11):
                if lineStipped[:11] == 'MUSICFILE: ':
                    self.editor.setMusicFile(lineStipped[11:].strip())
                elif lineStipped[:11] == 'FIREWORKS: ':
                    fwStr = lineStipped[11:].strip()
                    notify.info(fwStr)
                    fw = self.fireworkFromString(fwStr, currentT)
                    if not fw:
                        notify.warning('Failed to load show!')
                        self.clearShow()
                        break
                    currentT = fw.getStartTime()
        notify.info('Loaded.')

    def fireworkFromString(self, fwStr, currentT=0):
        # Remove parentheses
        lParen = fwStr.find('(')
        rParen = fwStr.find(')')
        if lParen < 0 or rParen < 0 or lParen >= rParen:
            return
        fwStr = fwStr[lParen + 1: rParen]
        # If its a valid line, split on separator and
        # strip leading/trailing whitespace from each element
        fwStrSplit = fwStr.split(', ')
        data = []
        for fStr in fwStrSplit:
            data.append(fStr)
        # Try to convert string to firework data
        try:
            startT = currentT + eval(data[FW_T])
            style = styleNames.index(data[FW_STYLE])
            color1 = ColorNames.index(data[FW_COLOR1].capitalize())
            color2 = ColorNames.index(data[FW_COLOR2].capitalize())
            amp = eval(data[FW_AMP])
            x = eval(data[FW_POS_X])
            y = eval(data[FW_POS_Y])
            z = eval(data[FW_POS_Z])
        except (ValueError, IndexError) as e:
            return
        return self.createFirework(startT, style, Point3(x, y, z),
                                   color1, color2, amp)

    def loadShowFromList(self, fireworksList):
        self.clearShow()
        currentT = 0.0
        for effect in fireworksList:
            waitTime, style, color1, color2, amp, x, y, z = effect
            currentT += waitTime
            self.createFirework(currentT, style, Point3(x, y, z),
                                color1, color2, amp)

    def clearShow(self):
        self.fwDict = {}

    def setMusicFile(self, filename):
        if filename:
            self.musicFilename = Filename.fromOsSpecific(filename)
            fullFilename = self.musicFilename.getFullpath()
            self.showMusic = loader.loadMusic(fullFilename)
        else:
            self.musicFilename = None
            self.showMusic = None

    def setMusicVolume(self, volume):
        if self.showMusic:
            self.showMusic.setVolume(volume)

    def getShowIval(self, startT=0.0, volume=1):
        showIval = Parallel()
        duration = 0.0

        # Start our music
        if self.showMusic:
            duration = self.showMusic.length()
            if duration > startT:
                duration = duration - startT
                musicTrack = Sequence(
                    Func(base.musicManager.stopAllSounds),
                    Func(base.playMusic, self.showMusic, 0, 1, volume, startT),
                    Wait(duration),
                    Func(base.musicManager.stopAllSounds)
                )
                showIval.append(musicTrack)

        # Add in fireworks track
        fwTrack = self.getFireworksTrack(startT)
        showIval.append(fwTrack)

        # Set duration to longest
        duration = max(duration, startT + fwTrack.getDuration())

        indicatorIval = LerpFunctionInterval(self.broadcastPlaybackT,
                                             fromData=startT,
                                             toData=startT + duration,
                                             duration=duration)
        showIval.append(indicatorIval)
        return showIval

    def getFireworksTrack(self, startT=0.0):
        fwTrack = Sequence()

        currentT = 0.0
        fStarted = 0
        for effect in self.getShow():
            waitTime, style, colorIndex1, colorIndex2, amp, x, y, z = effect
            if waitTime > 0:
                currentT += waitTime
                if fStarted:
                    fwTrack.append(Wait(waitTime))
            if currentT >= startT:
                if not fStarted:
                    fwTrack.append(Wait(currentT - startT))
                    fStarted = 1
                fwTrack.append(Func(Fireworks.shootFirework, style, x, y, z,
                                    colorIndex1, colorIndex2, amp))
        return fwTrack

    def broadcastPlaybackT(self, t):
        messenger.send('fireworksPlaybackT', [t])

    def playPauseShow(self, startT=0.0):
        # Pause current ival
        if self.fwIval:
            self.fwIval.pause()
        # Stop music
        base.musicManager.stopAllSounds()
        # Toggle flags
        if self.fPlayingIval:
            self.fPlayingIval = 0
        else:
            # Regenerate ival incase any changes were made
            self.fwIval = self.getShowIval(startT=startT)
            if self.fwIval:
                self.fwIval.start()
            self.fPlayingIval = 1

    def stopShow(self, event=None):
        self.fPlayingIval = 0
        if self.fwIval:
            self.fwIval.pause()
            if self.showMusic:
                base.musicManager.stopAllSounds()
        messenger.send('fireworksPlaybackT', [0])

    def offsetPos(self, dx=0, dy=0, dz=0, startT=0.0, endT='END', excludeList=None):
        if not excludeList:
            excludeList = []
        fwList = self.getSortedList()
        for fw in fwList:
            if fw.getStyle() in excludeList:
                notify.info('Excluding', styleNames[fw.getStyle()])
                continue
            currT = fw.getStartTime()
            if currT < startT:
                continue
            if endT is not 'END' and currT > endT:
                break
            pos = fw.getPos()
            pos.set(pos[0] + dx, pos[1] + dy, pos[2] + dz)

    def offsetT(self, dt=0, startT=0.0, endT='END'):
        fwList = self.getSortedList()
        for fw in fwList:
            currT = fw.getStartTime()
            if currT < startT:
                continue
            if endT is not 'END' and currT > endT:
                break
            fw.setStartTime(currT + dt)


class FireworksEditor(AppShell):
    # Override class variables
    appname = 'Fireworks Editor'
    frameWidth = 800
    frameHeight = 450
    usecommandarea = 0
    usestatusarea = 0
    contactname = 'Mark Mine'
    contactphone = '(818) 623-3915'
    contactemail = "mark.mine@disney.com"

    def appInit(self):
        # Initialize any instance variables you use here
        base.enableParticles()

        self.fwShow = FireworksShow(self)
        self.selectedFirework = None

        self.axis = loader.loadModel('phase_3/models/misc/xyzAxis')
        self.axis.reparentTo(render)
        self.axis.setTag('Fireworks', 'axis')
        s = loader.loadModel('phase_3/models/misc/sphere')
        s.reparentTo(self.axis)
        s.setPos(3, 3, 3)
        s.setScale(6)
        s.setTransparency(1)
        s.setColor(1, 1, 1, 0)

        self.target = loader.loadModel('phase_3/models/misc/xyzAxis')
        self.target.reparentTo(render)
        self.target.setTextureOff(1)
        self.target.setColor(1, 0, 0)
        self.target.setTag('Fireworks', 'target')
        s = loader.loadModel('phase_3/models/misc/sphere')
        s.reparentTo(self.target)
        s.setPos(3, 3, 3)
        s.setScale(6)
        s.setTransparency(1)
        s.setColor(1, 1, 1, 0)

        # Current firework style parameters
        self.fwStyle = IntVar()
        self.fwStyle.set(CIRCLE)
        self.fwColor1 = IntVar()
        self.fwColor1.set(WHITE)
        self.fwColor2 = IntVar()
        self.fwColor2.set(WHITE)
        self.fwPos = Vec3(0)
        self.fwAmp = 10.0
        self.fwStartTime = 0.0

        self.DNASTORE = None
        self.npToplevel = None
        self.hoods = []

        self.accept('f2', self.fwShow.stopShow)
        self.accept('f9', self.playPauseShow)
        self.accept('f10', self.shootFirework)
        self.accept('arrow_left', self.selectPrevFirework)
        self.accept('arrow_right', self.selectNextFirework)
        self.accept('arrow_up', lambda: self.setDeltaAmp(1.0))
        self.accept('arrow_down', lambda: self.setDeltaAmp(-1.0))
        self.accept('fireworksPlaybackT', self.moveToTime)

    def createMenuBar(self):
        menuBar = self.menuBar
        # FILE
        # add file entries before calling down, since we can't control order
        menuBar.addmenuitem('File', 'command',
                            'Load a fireworks show',
                            label='Load show',
                            command=self.loadFireworksShow)
        menuBar.addmenuitem('File', 'command',
                            'Save the fireworks show',
                            label='Save show',
                            command=self.saveFireworksShow)
        menuBar.addmenuitem('File', 'command',
                            'Clear fireworks show',
                            label='Clear show',
                            command=self.clearShow)
        menuBar.addmenuitem('File', 'separator')
        menuBar.addmenuitem('File', 'command',
                            'Load a fireworks show music',
                            label='Load music',
                            command=self.loadMusicFile)
        menuBar.addmenuitem('File', 'command',
                            'Clear fireworks show music',
                            label='Clear music',
                            command=lambda: self.setMusicFile(None))

        menuBar.addmenu('DNA', 'DNA Operations')
        for hood in ['TT', 'DD', 'MM', 'BR', 'DG', 'DL']:
            menuBar.addmenuitem(
                'DNA', 'command', 'Load %s DNA' % hood,
                label='Load %s DNA' % hood,
                command=lambda h=hood: self.loadSafeZone(h))

        menuBar.addmenuitem(
            'DNA', 'command', 'Clear SZ DNA', label='Clear DNA',
            command=self.clearSafeZone)

        # Create App Shell common menu bar items
        AppShell.createMenuBar(self)

    def createInterface(self):
        # Create the tk components
        interior = self.interior()

        # Paned widget for dividing two halves
        self.framePane = Pmw.PanedWidget(interior, orient=VERTICAL)
        self.controlFrame = self.framePane.add('control', min=200)

        # Radio buttons to select FW Style
        self.createStyleSelector(self.controlFrame)

        # Radio buttons to select color index
        self.createColorSelector(self.controlFrame, self.fwColor1, 1)
        self.createColorSelector(self.controlFrame, self.fwColor2, 2)

        # Vector widget to control FW origin
        sliderFrame = Frame(self.controlFrame)
        self.createPosSliders(sliderFrame)
        self.createAmpSlider(sliderFrame)
        self.createTimeSlider(sliderFrame)
        sliderFrame.pack(side=TOP, expand=1, fill=X)

        # Create edit buttons
        self.createEditButtons(self.controlFrame)

        self.controlFrame.pack(fill=BOTH, expand=1)

        # Frame for editing time of events
        self.timelineFrame = self.framePane.add('timeline', min=100)
        self.createTimelineEditor(self.timelineFrame)
        self.timelineFrame.pack(fill=BOTH, expand=1)
        self.framePane.pack(fill=BOTH, expand=1)

    def createStyleSelector(self, parent):
        # Tkinter value to hold current choice
        mainFrame = Frame(parent, relief=GROOVE, borderwidth=2)
        # Create label
        label = Label(mainFrame, text='Style:', width=10,
                      anchor=W, justify=LEFT)
        label.pack(side=LEFT, expand=0)
        buttonFrame = Frame(mainFrame)
        buttonFrame.pack(side=LEFT, expand=1, fill=X)
        rowFrame = Frame(buttonFrame)
        rowFrame.pack(side=TOP, expand=1, fill=X)
        # Add radio buttons
        count = 0
        for styleIndex in range(len(Names)):
            choiceStr = Names[styleIndex]
            choiceButton = Radiobutton(
                rowFrame,
                text=choiceStr,
                width=6,
                justify=LEFT,
                anchor=W,
                takefocus=0,
                value=styleIndex,
                variable=self.fwStyle,
                command=self.updateSelectedStyle)
            choiceButton.pack(side=LEFT, expand=0)
            if count == NUM_RB_COLS:
                rowFrame = Frame(buttonFrame)
                rowFrame.pack(side=TOP, expand=1, fill=X)
                count = 0
            count += 1
        mainFrame.pack(side=TOP, fill=X, expand=1)

    def createColorSelector(self, parent, variable, colorNum):
        # Tkinter value to hold current choice
        mainFrame = Frame(parent, relief=GROOVE, borderwidth=2)
        # Create label
        labelText = 'Color %d' % colorNum
        label = Label(mainFrame, text=labelText, width=10,
                      anchor=W, justify=LEFT)
        label.pack(side=LEFT, expand=0)
        buttonFrame = Frame(mainFrame)
        buttonFrame.pack(side=LEFT, expand=1, fill=X)
        rowFrame = Frame(buttonFrame)
        rowFrame.pack(side=TOP, expand=1, fill=X)
        # Add radio buttons
        count = 0
        for colorIndex in range(len(ColorNames)):
            choiceStr = ColorNames[colorIndex]
            choiceButton = Radiobutton(
                rowFrame,
                text=choiceStr,
                width=6,
                justify=LEFT,
                anchor=W,
                takefocus=0,
                value=colorIndex,
                variable=variable,
                command=lambda i=colorNum: self.updateSelectedColor(i)
            )
            choiceButton.pack(side=LEFT, expand=0)
            if count == NUM_RB_COLS:
                rowFrame = Frame(buttonFrame)
                rowFrame.pack(side=TOP, expand=1, fill=X)
                count = 0
            count += 1
        mainFrame.pack(side=TOP, fill=X, expand=1)

    def createPosSliders(self, parent):
        def fwPosCommand(poslist):
            self.axis.setPos(*poslist)
            self.fwPos.set(*poslist)
            if self.getSelectedFirework():
                self.getSelectedFirework().setPos(*poslist)
            self._canvas.focus_set()

        # Compute some defaults for the widgets
        value = (self.fwPos[0], self.fwPos[1], self.fwPos[2])
        floaterLabels = ['x', 'y', 'z']
        floaterType = 'floater'

        # Create the vector entry widgets with appropriate popups
        self.posWidget = VectorWidgets.VectorEntry(
            parent,
            text="Pos:", value=value,
            type=floaterType, bd=0, relief=None,
            label_justify=LEFT, label_anchor=W, label_width=14,
            label_bd=0, labelIpadx=0, floaterGroup_labels=floaterLabels)

        self.posWidget['command'] = fwPosCommand
        self.posWidget.pack(side=LEFT, fill=X, expand=1)

    def createAmpSlider(self, parent):
        def fwAmpCommand(amp):
            self.fwAmp = amp
            if self.getSelectedFirework():
                self.getSelectedFirework().setAmp(amp)
            self._canvas.focus_set()

        self.ampSlider = Slider.Slider(parent, text='Amp:',
                                       value=self.fwAmp,
                                       max=MAX_AMP,
                                       command=fwAmpCommand)
        self.ampSlider.pack(side=LEFT, fill=X, expand=1)

    def createTimeSlider(self, parent):
        def timeCommand(startTime):
            self.updateSelectedStartTime(startTime)
            if self.getSelectedFirework():
                self.timeline.moveFireworkTabToTime(
                    self.getSelectedFirework(), startTime, fReselect=1)
            self._canvas.focus_set()

        self.timeSlider = Slider.Slider(
            parent, text='Time:',
            value=self.fwStartTime,
            command=timeCommand)
        self.timeSlider.pack(side=LEFT, fill=X, expand=1)

    def createEditButtons(self, parent):
        buttonFrame = Frame(parent)
        self.testButton = Button(buttonFrame, text='Fire', takefocus=0,
                                 command=self.shootFirework)
        self.testButton.pack(side=LEFT, expand=1, fill=X)

        self.insertButton = Button(buttonFrame, text='Insert', takefocus=0,
                                   command=self.insertFirework)
        self.insertButton.pack(side=LEFT, expand=1, fill=X)

        self.printButton = Button(buttonFrame, takefocus=0, text='Print Show',
                                  command=self.fwShow.printShow)
        self.printButton.pack(side=LEFT, expand=1, fill=X)

        self.playButton = Button(buttonFrame, text='Play/Pause', takefocus=0,
                                 command=self.playPauseShow)
        self.playButton.pack(side=LEFT, expand=1, fill=X)

        self.stopButton = Button(buttonFrame, text='Stop', takefocus=0,
                                 command=self.fwShow.stopShow)
        self.stopButton.pack(side=LEFT, expand=1, fill=X)

        buttonFrame.pack(side=TOP, expand=1, fill=X)

    def createTimelineEditor(self, parent):
        # The Scrolled Canvas
        sc = self._scrolledCanvas = self.createcomponent(
            'scrolledCanvas',
            (), None,
            Pmw.ScrolledCanvas, (parent,),
            hull_width=600, hull_height=200,
            vscrollmode='none', canvas_background='White',
            usehullsize=1)
        self._canvas = sc.component('canvas')
        self._canvas['scrollregion'] = (0, '-1c', '4c', '1c')
        # Augment the scoll command to update the gui position
        sc.component('horizscrollbar')['command'] = self.horizScroll
        sc.component('vertscrollbar')['command'] = self.vertScroll
        sc.pack(padx=5, pady=5, expand=1, fill=BOTH)
        # Update lines
        self._canvas.bind('<Configure>', self.resizeScrollregion)
        self.timeline = Timeline(self._canvas, self)
        # Try to show left edge of canvas
        sc.xview('moveto', .0)
        self._canvas.focus_set()

    def resizeScrollregion(self, event):
        self.timeline.repositionGui()

    def horizScroll(self, x, y, w=None):
        self._canvas.xview(x, y, w)
        self.timeline.repositionGui()

    def vertScroll(self, x, y, w=None):
        self._canvas.yview(x, y, w)
        self.timeline.repositionGui()

    def saveFireworksShow(self):
        fireworksFilename = asksaveasfilename(
            defaultextension='.fws',
            filetypes=(('Fireworks Files', '*.fws'), ('All files', '*')),
            initialdir=ttmodelsDirectory,
            title='Save Fireworks Show as',
            parent=self.parent)
        if fireworksFilename:
            self.fwShow.saveShow(fireworksFilename)

    def loadFireworksShow(self):
        fireworksFilename = askopenfilename(
            defaultextension='.fws',
            filetypes=(('Fireworks Files', '*.fws'), ('All files', '*')),
            initialdir=ttmodelsDirectory,
            title='Save Fireworks Show as',
            parent=self.parent)
        if fireworksFilename:
            self.fwShow.loadShow(fireworksFilename)
            self.timeline.updateCanvas()

    def loadFireworkShowFromList(self, fwList):
        self.fwShow.loadShowFromList(fwList)
        self.timeline.updateCanvas()

    def loadMusicFile(self):
        # Load music
        # Set duration of show based on fireworks
        musicFilename = askopenfilename(
            defaultextension='.ogg',
            filetypes=(('OGG Files', '*.ogg'), ('MIDI Files', '*.mid'), ('MP3 Files', '*.mp3'),
                       ('WAV Files', '*.wav'), ('All files', '*')),
            initialdir=ttmodelsDirectory,
            title='Load Music File',
            parent=self.parent)
        if musicFilename:
            self.setMusicFile(musicFilename)

    def setMusicFile(self, filename):
        self.fwShow.setMusicFile(filename)
        self.timeline.updateCanvas()
        wp = WindowProperties(base.win.getProperties())
        if self.fwShow.musicFilename:
            basename = self.fwShow.musicFilename.getBasename()
            title = 'Fireworks Editor - %s' % basename
            notify.info('Loaded music %s.' % basename)
        else:
            title = 'Fireworks Editor'
        wp.setTitle(title)
        self.parent.title(title)
        base.win.requestProperties(wp)

    def clearShow(self):
        resp = askyesno('Fireworks Editor',
                        'Delete current fireworks show?',
                        parent=self.parent)
        if resp == 1:
            self.setMusicFile(None)
            self.fwShow.clearShow()
            self.timeline.updateCanvas()
            notify.debug('Cleared show.')

    def playPauseShow(self, event=None):
        self.fwShow.playPauseShow(self.timeline.currentTime)

    def moveToTime(self, time):
        self.timeline.moveTimeTabToTime(time)

    def loadDNAFile(self, filename, fStorage=0):
        node = loadDNAFile(self.DNASTORE, filename, CSDefault, 1)
        if fStorage:
            return
        self.npToplevel = render.attachNewNode(node)

    def loadStorageDNAFile(self, filename):
        self.loadDNAFile(filename, fStorage=1)

    def loadSafeZone(self, SZ):
        self.clearSafeZone()
        if not self.DNASTORE:
            self.DNASTORE = DNAStorage()
            # Load the generic storage files
            self.loadStorageDNAFile('phase_4/dna/ttrm_d_strg.dna')
            self.loadStorageDNAFile('phase_5/dna/ttrm_d_strg_town.dna')
            self.loadStorageDNAFile('phase_5.5/dna/ttrm_d_strg_est.dna')
            self.loadStorageDNAFile('phase_5.5/dna/ttrm_d_strg_house_int.dna')
        dnaPhases = {'ttc': 4, 'dod': 6, 'mml': 6, 'tbr': 8, 'dga': 8, 'ddl': 8}
        if SZ not in self.hoods:
            prefix = 'phase_%d/dna/ttrm_d_ara_%s' % (dnaPhases[SZ], SZ)
            self.loadStorageDNAFile(prefix + '.dna')
            self.loadStorageDNAFile(prefix + '_sz.dna')
            self.loadStorageDNAFile(prefix + '_town.dna')
            self.hoods.append(SZ)
        if SZ == 'ttc':
            filename = 'phase_4/dna/ttrm_d_ara_ttc_sz.dna'
        elif SZ == 'dod':
            filename = 'phase_6/dna/ttrm_d_ara_dod_sz.dna'
        elif SZ == 'MM':
            filename = 'phase_6/dna/ttrm_d_ara_mml_sz.dna'
        elif SZ == 'tbr':
            filename = 'phase_8/dna/ttrm_d_ara_tbr_sz.dna'
        elif SZ == 'dga':
            filename = 'phase_8/dna/ttrm_d_ara_dga_sz.dna'
        elif SZ == 'ddl':
            filename = 'phase_8/dna/ttrm_d_ara_ddl_sz.dna'
        else:
            notify.error('Invalid SZ %s' % SZ)
        notify.info('Loaded SZ %s.' % SZ)
        self.loadDNAFile(filename)

    def clearSafeZone(self):
        if self.npToplevel:
            self.npToplevel.removeNode()
            self.npToplevel = None

    def createFirework(self, startTime=None, style=None, pos=None,
                       color1=None, color2=None, amp=None):
        # If values not set, use current panel values
        if startTime is None:
            startTime = self.fwStartTime
        if style is None:
            style = self.fwStyle.get()
        if pos is None:
            pos = self.axis.getPos()
        if color1 is None:
            color1 = self.fwColor1.get()
        if color2 is None:
            color2 = self.fwColor2.get()
        if amp is None:
            amp = self.fwAmp
        return self.fwShow.createFirework(startTime, style, pos,
                                          color1, color2, amp)

    def shootFirework(self):
        fwColor2 = self.fwColor2.get()
        fwStyle = self.fwStyle.get()
        if fwStyle == Fireworks.CIRCLESPRITE and fwColor2 > list(Fireworks.textures.keys())[-1]:
            notify.warning('Invalid treasure type!')
        else:
            Fireworks.shootFirework(fwStyle,
                                    self.fwPos[0], self.fwPos[1], self.fwPos[2],
                                    self.fwColor1.get(), fwColor2,
                                    self.fwAmp)

    def insertFirework(self):
        self.timeline.insertFirework(self.fwStyle.get())

    def selectFirework(self, ID):
        fw = self.selectedFirework = self.fwShow.getFirework(ID)
        if fw:
            self.fwStyle.set(fw.getStyle())
            self.fwColor1.set(fw.getColor1())
            self.fwColor2.set(fw.getColor2())
            self.posWidget.set(fw.getPos())
            self.axis.setPos(fw.getPos())
            self.ampSlider.set(fw.getAmp())
            self.updateSelectedStartTime(fw.getStartTime(), updateSlider=1)

    def getSelectedFirework(self):
        return self.selectedFirework

    def selectPrevFirework(self):
        prev = self.fwShow.getPrevFirework(self.getSelectedFirework())
        if prev:
            self.timeline.selectFireworkWithID(prev.getID())

    def selectNextFirework(self):
        next = self.fwShow.getNextFirework(self.getSelectedFirework())
        if next:
            self.timeline.selectFireworkWithID(next.getID())

    def setDeltaAmp(self, deltaAmp):
        self.ampSlider.set(max(0, min(self.fwAmp + deltaAmp, MAX_AMP)))

    def updateSelectedStartTime(self, startTime, updateSlider=0):
        self.fwStart = startTime
        if self.getSelectedFirework():
            self.getSelectedFirework().setStartTime(startTime)
        if updateSlider:
            self.timeSlider.set(self.fwStart, fCommand=0)

    def updateSelectedStyle(self):
        if self.getSelectedFirework():
            self.getSelectedFirework().setStyle(self.fwStyle.get())
            self.timeline.updateSelectedStyle(self.getSelectedFirework())

    def updateSelectedColor(self, index):
        if self.getSelectedFirework():
            if index == 1:
                self.getSelectedFirework().setColor1(self.fwColor1.get())
            elif index == 2:
                self.getSelectedFirework().setColor2(self.fwColor2.get())

    def toggleBalloon(self):
        # 'balloon' shows balloon help
        # 'status' shows status bar
        # 'both' shows in both places
        # 'none' shows nothing
        if self.toggleBalloonVar.get():
            self.balloon().configure(state='both')
        else:
            self.balloon().configure(state='none')

    def onDestroy(self, event):
        """ Called on Factory Panel shutdown """
        self.axis.removeNode()
        self.target.removeNode()
        self.clearSafeZone()
        self.ignore('f2')
        self.ignore('f9')
        self.ignore('f10')
        self.ignore('arrow_left')
        self.ignore('arrow_right')
        self.ignore('arrow_up')
        self.ignore('arrow_down')
        self.ignore('fireworksPlaybackT')


class Timeline:
    def __init__(self, canvas, editor):

        c = self.canvas = canvas
        self.editor = editor

        # Style parameters
        self.normalStyle = 'black'
        self.activeStyle = 'green'
        self.activeStipple = ''
        self.deleteStyle = 'red'
        self.deleteStipple = 'gray25'

        self.pad = 2.0
        self.grid = '0.25c'
        # These bounds don't change
        self.left = 0.0
        self.top = c.winfo_fpixels('1c')
        self.bottom = c.winfo_fpixels('1.5c')
        self.size = c.winfo_fpixels('.2c')
        # The right side of the timeline depends on the duration
        self.mag = 1.0
        self.x = 0
        self.y = 0
        self.currentTime = 0.0

        self.createGui()
        self.updateCanvas()

        # Some general bindings
        # To select any firework tab
        c.tag_bind('tab', '<ButtonPress-1>',
                   lambda e: self.selectTab(e.x))
        # For the time tag
        c.tag_bind('timeTab', '<ButtonPress-1>',
                   lambda e: self.selectTimeTab(e.x))
        # To select/deselect current tag
        c.bind('<ButtonPress-3>', self.deselectFirework)
        # To move any firework tab
        c.bind('<B1-Motion>', lambda e: self.moveTab(e.x, e.y))
        c.bind('<Any-ButtonRelease-1>', self.releaseTab)
        c.bind('<Left>', lambda e: self.editor.selectPrevFirework())
        c.bind('<Right>', lambda e: self.editor.selectNextFirework())
        c.bind('<Up>', lambda e: self.editor.setDeltaAmp(1))
        c.bind('<Down>', lambda e: self.editor.setDeltaAmp(-1))
        c.bind('<F1>', self.moveTimeTabToCursor)
        c.bind('<F2>', self.editor.fwShow.stopShow)
        c.bind('<F9>', self.editor.playPauseShow)

    def createGui(self):
        xOffset = 0.0
        for index in range(len(Names)):
            self.makeWell(index, xOffset)
            xOffset += 1.25
        self.makeZoomButtons()
        self.makeTimeTab()

    def makeTab(self, x, y, tags):
        self.canvas.create_polygon(
            x, y, x + self.size, y + self.size, x - self.size, y + self.size,
            tags=tags)

    def makeWell(self, index, x=0.0, y=2):
        fwName = Names[index]
        tags = ('gui', fwName + '_well')
        self.canvas.create_rectangle(
            '%fc' % x, '%fc' % y,
            '%fc' % (x + 0.6), '%fc' % (y + 0.5),
            outline='black', fill=self.canvas['background'],
            tags=tags)
        self.makeTab(
            self.canvas.winfo_pixels('%fc' % (x + 0.3)),
            self.canvas.winfo_pixels('%fc' % (y + 0.15)),
            tags)
        self.canvas.create_text(
            '%fc' % (x + 0.3), '%fc' % (y + 0.6),
            text=fwName, anchor=N, tags=tags)
        if fwName:
            self.canvas.tag_bind(fwName + '_well', '<ButtonPress-1>',
                                 lambda e: self.newFirework(e.x, e.y, index))

    def makeZoomButtons(self):
        self.makeZoomButton('zoomIn', self.zoomIn, 0.0)
        self.makeZoomButton('zoomOut', self.zoomOut, 1.25)

    def makeZoomButton(self, tag, cmd, x=2.0, y=3.5):
        tags = ('gui', tag)
        self.canvas.create_rectangle(
            '%fc' % x, '%fc' % y,
            '%fc' % (x + 0.6), '%fc' % (y + 0.5),
            outline='black', fill=self.canvas['background'],
            tags=tags)
        self.canvas.create_oval(
            self.canvas.winfo_pixels('%fc' % (x + 0.1)),
            self.canvas.winfo_pixels('%fc' % (y + 0.05)),
            self.canvas.winfo_pixels('%fc' % (x + 0.5)),
            self.canvas.winfo_pixels('%fc' % (y + 0.45)),
            tags=tags)
        self.canvas.create_line(
            self.canvas.winfo_pixels('%fc' % (x + 0.15)),
            self.canvas.winfo_pixels('%fc' % (y + 0.25)),
            self.canvas.winfo_pixels('%fc' % (x + 0.45)),
            self.canvas.winfo_pixels('%fc' % (y + 0.25)),
            tags=tags)
        if tag == 'zoomIn':
            self.canvas.create_line(
                self.canvas.winfo_pixels('%fc' % (x + 0.3)),
                self.canvas.winfo_pixels('%fc' % (y + 0.1)),
                self.canvas.winfo_pixels('%fc' % (x + 0.3)),
                self.canvas.winfo_pixels('%fc' % (y + 0.4)),
                tags=tags)
        self.canvas.create_text(
            '%fc' % (x + 0.3), '%fc' % (y + 0.6),
            text=tag, anchor=N, tags=tags)
        self.canvas.tag_bind(tag, '<ButtonPress-1>', lambda e: cmd())

    def makeTimeTab(self, x=0):
        y = self.top
        self.canvas.create_polygon(
            x, y,
            x + self.size, y - self.size,
            x - self.size, y - self.size,
            tags=('timeTab',))

    def repositionGui(self):
        deltaX = self.canvas.canvasx(50) - self.canvas.coords('Pow_well')[0]
        self.canvas.move('gui', deltaX, 0)

    def zoomIn(self):
        # Deselect currently selected tab as a precaution
        self.deselectFirework()
        self.mag *= 2.0
        self.x *= 2.0
        self.updateCanvas()
        notify.debug('Zoomed in timeline.')

    def zoomOut(self):
        # Deselect currently selected tab as a precaution
        self.deselectFirework()
        self.mag *= 0.5
        self.x *= 0.5
        self.updateCanvas()
        notify.debug('Zoomed out timeline.')

    def updateCanvas(self):
        self.numTicks = int(round(self.editor.fwShow.getDuration()))
        self.length = self.numTicks * self.mag
        # Change slider length to match actual timeline length
        self.editor.timeSlider['max'] = self.length
        self.editor.timeSlider.setMax()
        self.right = self.canvas.winfo_fpixels('%dc' % self.length)
        leftEdge = self.canvas.winfo_fpixels('%dc' % -self.pad)
        rightEdge = self.canvas.winfo_fpixels('%dc' % (self.length + self.pad))
        self.canvas['scrollregion'] = (leftEdge, 0, rightEdge, '2c')
        self.updateTimeline()
        self.redrawTabs()

    def updateTimeline(self):
        c = self.canvas
        c.delete('timeline')
        c.create_line(self.left, '0.5c', self.left, '1c',
                      self.right, '1c', self.right, '0.5c',
                      width=1, tags=('timeline',))
        i = 0
        while i in range(self.numTicks):
            x = '%fc' % (i * self.mag)
            c.create_line(x, '1c', x, '0.6c', width=1, tags=('timeline',))
            c.create_text(x, '.5c', text=i, anchor=S,
                          justify=CENTER, tags=('timeline',))
            x = '%fc' % ((i + 0.25) * self.mag)
            c.create_line(x, '1c', x, '0.8c', width=1, tags=('timeline',))
            x = '%fc' % ((i + 0.5) * self.mag)
            c.create_line(x, '1c', x, '0.7c', width=1, tags=('timeline',))
            x = '%fc' % ((i + 0.75) * self.mag)
            c.create_line(x, '1c', x, '0.8c', width=1, tags=('timeline',))
            i += 1
        # Create last text label
        x = '%fc' % ((i + 1) * self.mag)
        c.create_text(x, '.5c', text=i + 1, anchor=S,
                      justify=CENTER, tags=('timeline',))

    def makeFireworkTab(self, x, y, fw, fActive=0):
        style = fw.getStyle()
        fwName = Names[style]
        tags = ('tab', fwName, 'fwID_%d' % fw.getID())
        # active tag is used for tab that is being interactively dragged
        # selected tag is used for tab that is being controlled by panel
        if fActive:
            tags = tags + ('active', 'selected')
        self.makeTab(x, y, tags)
        self.canvas.create_text(x, y + self.canvas.winfo_fpixels('0.3c'),
                                text=styleNamesShort[style], anchor=N,
                                tags=tags + ('styleText',))

    def redrawTabs(self):
        c = self.canvas
        c.delete('tab')
        fwList = self.editor.fwShow.getSortedList()
        for fw in fwList:
            startT = fw.getStartTime()
            x = self.canvas.winfo_fpixels('%fc' % (startT * self.mag))
            self.makeFireworkTab(x, self.top + 2, fw, fActive=0)
        # Redraw time marker
        c.delete('timeTab')
        x = self.canvas.winfo_fpixels('%fc' % (self.currentTime * self.mag))
        self.makeTimeTab(x)

    def selectTab(self, x):
        # Deselect currently selected tab
        self.deselectFirework()
        self.x = self.canvas.canvasx(x, self.grid)
        self.y = self.top + 2
        self.canvas.addtag_withtag('active', CURRENT)
        # Figure out ID specific tag so you can also select the
        # corresponding marker or label
        ID = None
        for tag in self.canvas.gettags(CURRENT):
            if tag.find('fwID') == 0:
                ID = int(tag[5:])
                self.canvas.addtag_withtag('active', tag)
                self.canvas.addtag_withtag('selected', tag)
                break
        self.selectFirework(ID)

    def selectTimeTab(self, x):
        # Deselect currently selected tab
        self.deselectFirework()
        self.x = self.canvas.canvasx(x, self.grid)
        self.y = self.top + 2
        self.canvas.addtag_withtag('active', CURRENT)
        self.canvas.itemconfig('active', fill=self.activeStyle,
                               stipple=self.activeStipple)
        self.canvas.lift('active')

    def selectFireworkWithID(self, ID):
        # Deselect currently selected tab
        self.deselectFirework()
        self.canvas.addtag_withtag('active', 'fwID_%d' % ID)
        self.canvas.addtag_withtag('selected', 'fwID_%d' % ID)
        self.selectFirework(ID)
        self.canvas.dtag('active')

    def updateSelectedStyle(self, fw):
        c = self.canvas
        fwTags = c.find_withtag('fwID_%d' % fw.getID())
        for tag in fwTags:
            tagList = c.gettags(tag)
            if 'styleText' in tagList:
                x, y = c.coords(tag)
                c.delete(tag)
                newText = self.canvas.create_text(
                    x, y, text=styleNamesShort[fw.getStyle()],
                    anchor=N, tags=tagList)
                # Color active things green
                self.canvas.itemconfig(newText, fill=self.activeStyle,
                                       stipple=self.activeStipple)
                self.canvas.lift(newText)

    def releaseTab(self, event):
        tags = self.canvas.find_withtag('active')
        if not tags:
            return
        fwTags = self.canvas.gettags('active')

        if 'timeTab' in fwTags:
            self.canvas.itemconfig('active', fill=self.normalStyle,
                                   stipple=self.activeStipple)
            pixelsPerCM = self.canvas.winfo_fpixels('1c')
            self.currentTime = (self.x / pixelsPerCM) / self.mag
            self.canvas.dtag('active')
        else:
            ID = None
            for tag in fwTags:
                if tag.find('fwID') == 0:
                    ID = int(tag[5:])
            if ID is not None:
                if self.y != self.top + 2:
                    self.editor.fwShow.removeFirework(ID)
                    self.canvas.delete('active')
                    notify.debug('Deleted firework.')
                else:
                    pixelsPerCM = self.canvas.winfo_fpixels('1c')
                    startTime = (self.x / pixelsPerCM) / self.mag
                    self.editor.updateSelectedStartTime(
                        startTime, updateSlider=1)
            # Clear the active flag but leave item selected and highlighted
            self.canvas.dtag('active')
        # Force a redraw of the canvas to avoid text trails
        leftEdge = self.canvas.winfo_fpixels('%dc' % -self.pad)
        rightEdge = self.canvas.winfo_fpixels('%dc' % (self.length + self.pad))
        self.canvas['scrollregion'] = (leftEdge, 0, rightEdge, '2c')

    def moveTab(self, x, y):
        tags = self.canvas.find_withtag('active')
        if not tags:
            return
        cx = self.canvas.canvasx(x, self.grid)
        # This seems to give an incorrect y position
        # cy = self.canvas.canvasx(y)
        cy = y

        # Clamp position of tag
        if cx < self.left:
            cx = self.left
        if cx > self.right:
            cx = self.right

        if 'timeTab' in self.canvas.gettags('active'):
            self.canvas.move('active', cx - self.x, 0)
        else:
            # See if tag is within the "sweet spot"
            if self.top <= cy <= self.bottom:
                cy = self.top + 2
                self.canvas.itemconfig('active', fill=self.activeStyle,
                                       stipple=self.activeStipple)
            else:
                cy = cy - self.size - 2
                self.canvas.itemconfig('active', fill=self.deleteStyle,
                                       stipple=self.deleteStipple)
            self.canvas.move('active', cx - self.x, cy - self.y)
        self.x = cx
        self.y = cy

    def moveTimeTabToTime(self, time):
        if self.length >= time >= 0.0:
            c = self.canvas
            c.delete('timeTab')
            self.currentTime = time
            x = self.canvas.winfo_fpixels('%fc' % (self.currentTime * self.mag))
            self.makeTimeTab(x)

    def moveTimeTabToCursor(self, event):
        if self.editor.fwShow.fPlayingIval:
            self.editor.playPauseShow()
        pixelsPerCM = self.canvas.winfo_fpixels('1c')
        currentTime = (self.canvas.canvasx(event.x) / pixelsPerCM) / self.mag
        self.moveTimeTabToTime(currentTime)

    def moveFireworkTabToTime(self, fw, time, fReselect=0):
        c = self.canvas
        c.delete('fwID_%d' % fw.getID())
        startT = fw.getStartTime()
        x = self.canvas.winfo_fpixels('%fc' % (startT * self.mag))
        self.makeFireworkTab(x, self.top + 2, fw, fActive=fReselect)
        if fReselect:
            self.selectFirework(fw.getID())
            self.canvas.dtag('active')

    def newFirework(self, x, y, style):
        # Deselect currently selected tab
        self.deselectFirework()
        # Create new one
        fw = self.editor.createFirework(style=style)
        self.makeFireworkTab(x, y, fw, fActive=1)
        self.selectFirework(fw.getID())
        self.x = x
        self.y = y
        self.moveTab(x, y)

    def insertFirework(self, style):
        # Deselect currently selected tab
        self.deselectFirework()
        # Create new one
        fw = self.editor.createFirework(style=style, startTime=self.currentTime)
        x = self.canvas.winfo_fpixels('%fc' % (self.currentTime * self.mag))
        self.makeFireworkTab(x, self.top + 2, fw, fActive=1)
        self.selectFirework(fw.getID())
        self.canvas.dtag('active')

    def selectFirework(self, ID):
        self.editor.selectFirework(ID)
        # Color active things green
        self.canvas.itemconfig('active', fill=self.activeStyle,
                               stipple=self.activeStipple)
        self.canvas.lift('active')

    def deselectFirework(self, event=None):
        self.canvas.itemconfig('selected', fill=self.normalStyle,
                               stipple=self.activeStipple)
        self.canvas.dtag('selected')
        self.editor.selectFirework(None)


base = ShowBase()
# The original Disney code used direct but direct just makes this annoying to use so I removed the functionality
base.startTk()
FireworksEditor(base.tkRoot)
base.useTrackball()
base.run()
