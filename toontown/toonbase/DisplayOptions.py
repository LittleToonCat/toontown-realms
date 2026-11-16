import copy
import string
import os
import sys
import datetime
from panda3d.core import loadPrcFileData, WindowProperties, ClockObject

from otp.otpbase.PythonUtil import bound
from otp.otpgui import OTPDialog
from otp.otpbase import OTPGlobals
from otp.otpbase import OTPRender
from direct.directnotify import DirectNotifyGlobal

from toontown.toonbase.ToontownSettings import ASPECT_RATIOS, FPS_CAPS, FONT_PPUS

try:
    import embedded
except:
    pass

from toontown.toonbase import ClientSettings

class DisplayOptions:
    notify = DirectNotifyGlobal.directNotify.newCategory('DisplayOptions')

    def __init__(self):
        self.restore_failed = False
        self.loadFromSettings()

    def loadFromSettings(self):
        displayMode = ClientSettings.DisplayMode.get()
        res = ClientSettings.Resolution.get()
        antialias = ClientSettings.AntiAliasing.get()
        syncVideo = ClientSettings.VerticalSync.get()
        maxFps = ClientSettings.FrameRateCap.get()
        aspectRatio = ClientSettings.AspectRatio.get()
        anisotropic = ClientSettings.AnisotropicFiltering.get()
        fontQuality = 2#ClientSettings.FontQuality.get()

        base.setAspectRatio(ASPECT_RATIOS[aspectRatio])

        loadPrcFileData('toonBase Settings Anisotropic Filtering',
                        'texture-anisotropic-degree %i' % bound(anisotropic**2, 1, 16))

        if maxFps:
            globalClock.setMode(ClockObject.MLimited)
            globalClock.setFrameRate(FPS_CAPS[maxFps])
        else:
            globalClock.setMode(ClockObject.MNormal)

        loadPrcFileData('toonBase Settings Text PPU', f'text-pixels-per-unit {FONT_PPUS[bound(fontQuality, 0, 2)]}')
        if antialias.value:
            loadPrcFileData('toonBase Settings Framebuffer MSAA', 'framebuffer-multisample 1')
            loadPrcFileData('toonBase Settings MSAA Level', 'multisamples %i' % min(antialias.value**2, 8))
        else:
            loadPrcFileData('toonBase Settings Framebuffer MSAA', 'framebuffer-multisample 0')
        self.notify.debug('before prc settings display mode mode=%s' % str(displayMode))
        fullscreen = displayMode == 1
        undecorated = displayMode == 2
        if not fullscreen and not self.isWindowedPossible():
            self.notify.warning('Windowed mode is not possible.')
            fullscreen = True
        loadPrcFileData('toonBase Settings Window Res', 'win-size %s %s' % (res[0], res[1]))
        self.notify.debug('settings resolution = %s' % str(res))
        loadPrcFileData('toonBase Settings Window FullScreen', 'fullscreen %s' % fullscreen)
        loadPrcFileData('toonBase Settings Window Undecorated', 'undecorated %s' % fullscreen)
        self.notify.debug('settings full screen mode=%s' % str(fullscreen))
        loadPrcFileData('toonBase Settings Antialiasing', 'antialiasing %s' % antialias)
        loadPrcFileData('toonBase settings v-sync', 'sync-video %s' % syncVideo)
        self.settingsDisplayMode = displayMode
        self.settingsWidth = res[0]
        self.settingsHeight = res[1]
        self.settingsAntialiasing = antialias
        self.notify.info('Display Mode = %s, width=%d height=%d' % (self.settingsDisplayMode,
         self.settingsWidth,
         self.settingsHeight))
        return

    def set(self, pipe, width, height, displayMode, embedded):
        self.notify.debugStateCall(self)
        state = False
        self.notify.info('SET')
        displayMode = displayMode
        fullscreen = displayMode == 1
        borderless = displayMode == 2
        self.current_pipe = base.pipe
        self.current_properties = WindowProperties(base.win.getProperties())
        properties = self.current_properties
        self.notify.debug('DISPLAY PREVIOUS:')
        self.notify.debug('  BORDERLESS: %s' % bool(properties.getUndecorated()))
        self.notify.debug('  FULLSCREEN: %s' % bool(properties.getFullscreen()))
        self.notify.debug('  X SIZE:     %s' % properties.getXSize())
        self.notify.debug('  Y SIZE:     %s' % properties.getYSize())
        self.notify.debug('DISPLAY REQUESTED:')
        self.notify.debug('  BORDERLESS: %s' % bool(borderless))
        self.notify.debug('  FULLSCREEN: %s' % bool(fullscreen))
        self.notify.debug('  X SIZE:     %s' % width)
        self.notify.debug('  Y SIZE:     %s' % height)
        if self.current_pipe == pipe \
                and bool(self.current_properties.getParentWindow()) == bool(embedded)\
                and self.current_properties.getFullscreen() == fullscreen\
                and self.current_properties.getUndecorated() == borderless\
                and self.current_properties.getXSize() == width\
                and self.current_properties.getYSize() == height:
            self.notify.info('DISPLAY NO CHANGE REQUIRED')
            state = True
        else:
            properties = WindowProperties()
            properties.setSize(width, height)
            properties.setFullscreen(fullscreen)
            properties.setUndecorated(borderless)
            properties.setParentWindow(0)
            original_sort = base.win.getSort()
            if self.resetWindowProperties(pipe, properties):
                self.notify.debug('DISPLAY CHANGE SET')
                properties = base.win.getProperties()
                self.notify.debug('DISPLAY ACHIEVED:')
                self.notify.debug('  EMBEDDED:   %s' % bool(properties.getParentWindow()))
                self.notify.debug('  FULLSCREEN: %s' % bool(properties.getFullscreen()))
                self.notify.debug('  X SIZE:     %s' % properties.getXSize())
                self.notify.debug('  Y SIZE:     %s' % properties.getYSize())
                if bool(properties.getParentWindow()) == bool(embedded) \
                        and properties.getFullscreen() == fullscreen \
                        and properties.getUndecorated() == borderless \
                        and properties.getXSize() == width \
                        and properties.getYSize() == height:
                    self.notify.info('DISPLAY CHANGE VERIFIED')
                    state = True
                else:
                    self.notify.warning('DISPLAY CHANGE FAILED, RESTORING PREVIOUS DISPLAY')
                    self.restoreWindowProperties()
            else:
                self.notify.warning('DISPLAY CHANGE FAILED')
                self.notify.warning('DISPLAY SET - BEFORE RESTORE')
                self.restoreWindowProperties()
                self.notify.warning('DISPLAY SET - AFTER RESTORE')
            base.win.setSort(original_sort)
            base.graphicsEngine.renderFrame()
            base.graphicsEngine.renderFrame()
        return state

    def resetWindowProperties(self, pipe, properties):
        if base.win:
            currentProperties = WindowProperties(base.win.getProperties())
            gsg = base.win.getGsg()
        else:
            currentProperties = WindowProperties.getDefault()
            gsg = None
        newProperties = WindowProperties(currentProperties)
        newProperties.addProperties(properties)
        if base.pipe != pipe:
            gsg = None
        if gsg == None or currentProperties.getFullscreen() != newProperties.getFullscreen() \
                or currentProperties.getUndecorated() != newProperties.getUndecorated() \
                or currentProperties.getParentWindow() != newProperties.getParentWindow():
            self.notify.debug('window properties: %s' % properties)
            self.notify.debug('gsg: %s' % gsg)
            base.pipe = pipe
            if not base.openMainWindow(props=properties, gsg=gsg, keepCamera=True):
                self.notify.warning('OPEN MAIN WINDOW FAILED')
                return 0
            self.notify.info('OPEN MAIN WINDOW PASSED')
            base.graphicsEngine.openWindows()
            if base.win.isClosed():
                self.notify.warning('Window did not open, removing.')
                base.closeWindow(base.win)
                return 0
            base.disableShowbaseMouse()
            if 'panda3d.toontown' in sys.modules:
                from panda3d.toontown import NametagGlobals
                NametagGlobals.setCamera(base.cam)
                NametagGlobals.setMouseWatcher(base.mouseWatcherNode)
        else:
            self.notify.debug('Adjusting properties')
            base.win.requestProperties(properties)
            base.graphicsEngine.renderFrame()
        return 1

    def restoreWindowProperties(self):
        if self.resetWindowProperties(self.current_pipe, self.current_properties):
            self.restore_failed = False
        else:
            self.notify.warning("Couldn't restore original display settings!")
            if self.current_properties.getFullscreen():
                fullscreen = 0
                embedded = 0
                tryProps = self.current_properties
                tryProps.setFullscreen(0)
                if self.resetWindowProperties(self.current_pipe, tryProps):
                    self.current_properties = copy.copy(tryProps)
                    self.restore_failed = False
                    return
            self.notify.error('Failed opening regular window!')
            base.panda3dRenderError()
            self.restore_failed = True

    @staticmethod
    def isDefaultEmbedded():
        result = False
        try:
            embedOption = int(base.launcher.getValue('GAME_DEFAULT_TO_EMBEDDED', None))
            if embedOption != None:
                result = bool(int(embedOption))
        except:
            pass

        return result

    @staticmethod
    def isEmbeddedPossible():
        result = False
        try:
            showOption = base.launcher.getValue('GAME_SHOW_EMBEDDED_OPTION', None)
            if showOption != None:
                result = bool(int(showOption))
        except:
            pass

        return result

    @staticmethod
    def isWindowedPossible():
        result = True
        try:
            showOption = base.launcher.getValue('GAME_SHOW_WINDOWED_OPTION', None)
            if showOption != None:
                result = bool(int(showOption))
        except:
            pass

        return result
