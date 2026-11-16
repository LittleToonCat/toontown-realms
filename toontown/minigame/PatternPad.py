from direct.gui.DirectGui import *


class PatternPad(DirectFrame):
    ButtonNames = ('upButton', 'rightButton', 'downButton', 'leftButton')
    DI = 0.5
    LI = 1.0
    RI = 0.6
    ButtonDarkColors = ((DI, 0, 0, 1), (0, 0, DI, 1), (DI, DI, 0, 1), (0, DI, 0, 1))
    ButtonLightColors = ((LI, 0, 0, 1), (0, 0, LI, 1), (LI, LI, 0, 1), (0, LI, 0, 1))
    ButtonRolloverColors = ((RI, 0, 0, 1), (0, 0, RI, 1), (RI, RI, 0, 1), (0, RI, 0, 1))
    
    def __init__(self, parent = aspect2d, **kw):
        self.__pressHandlers = ((lambda db, self = self: self.__pressButton(0)), (lambda db, self = self: self.__pressButton(1)), (lambda db, self = self: self.__pressButton(2)), (lambda db, self = self: self.__pressButton(3)))
        self.__releaseHandlers = ((lambda db, self = self: self.__releaseButton(0)), (lambda db, self = self: self.__releaseButton(1)), (lambda db, self = self: self.__releaseButton(2)), (lambda db, self = self: self.__releaseButton(3)))
        self.__enterHandlers = ((lambda db, self = self: self.__enterButton(0)), (lambda db, self = self: self.__enterButton(1)), (lambda db, self = self: self.__enterButton(2)), (lambda db, self = self: self.__enterButton(3)))
        self.__exitHandlers = ((lambda db, self = self: self.__exitButton(0)), (lambda db, self = self: self.__exitButton(1)), (lambda db, self = self: self.__exitButton(2)), (lambda db, self = self: self.__exitButton(3)))
        BP = 0.25
        BBW = 0.02
        BFS = 0.12
        FS = 0.4
        FCI = 0.1
        optiondefs = (('callbacks', None, self.setCallbacks),
                      ('pressHandlers', self.__pressHandlers, self.setPressHandlers),
                      ('releaseHandlers', self.__releaseHandlers, self.setReleaseHandlers),
                      ('enterHandlers', self.__enterHandlers, self.setEnterHandlers),
                      ('exitHandlers', self.__exitHandlers, self.setExitHandlers),
                      ('frameSize', (-FS, FS, -FS, FS), None),
                      ('frameColor', (FCI, FCI, FCI, 1), None),
                      ('buttons_frameSize', (-BFS, BFS, -BFS, BFS), None),
                      ('buttons_borderWidth', (BBW, BBW), None),
                      ('buttons_relief', DGG.RAISED, None),
                      ('buttons_clickSound', None, None),
                      ('buttons_rolloverSound', None, None),
                      ('upButton_pos', (0, 0, BP), None),
                      ('downButton_pos', (0, 0, -BP), None),
                      ('leftButton_pos', (-BP, 0, 0), None),
                      ('rightButton_pos', (BP, 0, 0), None))
        self.defineoptions(kw, optiondefs, dynamicGroups = ('buttons',))
        DirectFrame.__init__(self, parent)
        for i in range(0, len(self.ButtonNames)):
            self.createcomponent(self.ButtonNames[i], (), 'buttons', DirectButton, (), parent = self, frameColor = self.ButtonDarkColors[i])
        
        self.initialiseoptions(PatternPad)
        self.setPressCallback(None)
        self.setReleaseCallback(None)
        self.setEnterCallback(None)
        self.setExitCallback(None)

    def destroy(self):
        for name in self.ButtonNames:
            self.destroycomponent(name)
        
        DirectFrame.destroy(self)

    def __getButtons(self):
        buttons = []
        for name in self.ButtonNames:
            buttons.append(self.component(name))
        
        return buttons

    def disable(self):
        buttons = self.__getButtons()
        for button in buttons:
            button['state'] = DGG.DISABLED

    def enable(self):
        buttons = self.__getButtons()
        for button in buttons:
            button['state'] = DGG.NORMAL

    def setPressCallback(self, callback):
        self.__clientPressCallback = callback

    def setReleaseCallback(self, callback):
        self.__clientReleaseCallback = callback

    def setEnterCallback(self, callback):
        self.__clientEnterCallback = callback

    def setExitCallback(self, callback):
        self.__clientExitCallback = callback

    def setCallbacks(self):
        buttons = self.__getButtons()
        if self['callbacks'] is None:
            for button in buttons:
                button['command'] = None
            
        else:
            for i in range(0, len(buttons)):
                buttons[i]['command'] = self['callbacks'][i]

    def __bindButtonHandlers(self, event, handlerTypeName):
        buttons = self.__getButtons()
        if self[handlerTypeName] is None:
            for button in buttons:
                button.unbind(event)
            
        else:
            for i in range(0, len(buttons)):
                buttons[i].bind(event, self[handlerTypeName][i])

    def setPressHandlers(self):
        self.__bindButtonHandlers(DGG.B1PRESS, 'pressHandlers')

    def setReleaseHandlers(self):
        self.__bindButtonHandlers(DGG.B1RELEASE, 'releaseHandlers')

    def setEnterHandlers(self):
        self.__bindButtonHandlers(DGG.ENTER, 'enterHandlers')

    def setExitHandlers(self):
        self.__bindButtonHandlers(DGG.EXIT, 'exitHandlers')

    def __pressButton(self, index):
        self.__lightenButton(index)
        if self.__clientPressCallback is not None:
            self.__clientPressCallback(index)

    def __releaseButton(self, index):
        self.__darkenButton(index)
        if self.__clientReleaseCallback is not None:
            self.__clientReleaseCallback(index)

    def __enterButton(self, index):
        if self.__clientEnterCallback is not None:
            self.__clientEnterCallback(index)

    def __exitButton(self, index):
        if self.__clientExitCallback is not None:
            self.__clientExitCallback(index)

    def __lightenButton(self, index):
        buttons = self.__getButtons()
        buttons[index]['frameColor'] = self.ButtonLightColors[index]

    def __darkenButton(self, index):
        buttons = self.__getButtons()
        buttons[index]['frameColor'] = self.ButtonDarkColors[index]

    def simButtonPress(self, index):
        self.__lightenButton(index)

    def simButtonRelease(self, index):
        self.__darkenButton(index)


