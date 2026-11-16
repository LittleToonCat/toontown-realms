from panda3d.core import Vec4, TextNode
from direct.showbase import DirectObject
from otp.otpbase import OTPLocalizer
from toontown.toonbase import ToontownGlobals, TTLocalizer
from . import TTQTGraph
from . import TTQTNode
from direct.fsm import ClassicFSM, State
from direct.gui.DirectGui import *


class TTChatInputQuickTalker(DirectObject.DirectObject):
    
    def __init__(self, chatMgr):
        DirectObject.DirectObject.__init__(self)
        self.chatMgr = chatMgr
        self.sentenceList = []
        chatInputGui = loader.loadModel('phase_3.5/models/gui/chat_input_gui')
        self.frame = DirectFrame(parent=base.a2dTopLeft, image = chatInputGui.find('**/quick_talker'), relief = None, pos = (0.9, 0, -0.1), sortOrder = 10)
        self.frame.hide()
        self.backButton = DirectButton(parent = self.frame, image = (chatInputGui.find('**/ChtBx_BackBtn_UP'), chatInputGui.find('**/ChtBx_BackBtn_DN'), chatInputGui.find('**/ChtBx_BackBtn_Rllvr')), relief = None, pos = (0.7073, 0, 0.0125), text = ('', TTLocalizer.QuickTalkerBack, TTLocalizer.QuickTalkerBack), text_scale = 0.06, text_fg = Vec4(1, 1, 1, 1), text_shadow = Vec4(0, 0, 0, 1), text_pos = (0, -0.1), text_font = ToontownGlobals.getInterfaceFont(), clickSound = DGG.getDefaultClickSound(), rolloverSound = DGG.getDefaultRolloverSound(), command = self.__backButtonPressed)
        self.chatButton = DirectButton(parent = self.frame, image = (chatInputGui.find('**/ChtBx_ChtBtn_UP'), chatInputGui.find('**/ChtBx_ChtBtn_DN'), chatInputGui.find('**/ChtBx_ChtBtn_RLVR')), relief = None, pos = (0.8, 0, 0.0125), text = ('', OTPLocalizer.ChatInputNormalSayIt, OTPLocalizer.ChatInputNormalSayIt), text_scale = 0.06, text_fg = Vec4(1, 1, 1, 1), text_shadow = Vec4(0, 0, 0, 1), text_pos = (0, -0.1), text_font = ToontownGlobals.getInterfaceFont(), clickSound = DGG.getDefaultClickSound(), rolloverSound = DGG.getDefaultRolloverSound(), command = self.__chatButtonPressed)
        self.cancelButton = DirectButton(parent = self.frame, image = (chatInputGui.find('**/CloseBtn_UP'), chatInputGui.find('**/CloseBtn_DN'), chatInputGui.find('**/CloseBtn_Rllvr')), relief = None, pos = (-0.783, 0, 0.0125), text = ('', OTPLocalizer.lCancel, OTPLocalizer.lCancel), text_scale = 0.06, text_fg = Vec4(1, 1, 1, 1), text_shadow = Vec4(0, 0, 0, 1), text_pos = (0, -0.1), text_font = ToontownGlobals.getInterfaceFont(), clickSound = DGG.getDefaultClickSound(), rolloverSound = DGG.getDefaultRolloverSound(), command = self.__cancelButtonPressed)
        self.displayText = DirectLabel(parent = self.frame, relief = None, text = '', text_font = ToontownGlobals.getToonFont(), text_fg = Vec4(0, 0, 0, 1), text_pos = (-0.675, -0.008), text_scale = 0.06, text_align=TextNode.ALeft)
        self.chatHead = self.frame.attachNewNode('chatHead')
        self.fsm = ClassicFSM.ClassicFSM('QuickTalker', [
            State.State('Hidden', self.__enterHidden, self.__exitHidden, [
                'Constructing']),
            State.State('Constructing', self.__enterConstructing, self.__exitConstructing, [
                'ConstructingTransition',
                'SayIt',
                'Hidden']),
            State.State('ConstructingTransition', self.__enterConstructingTransition, self.__exitConstructingTransition,
                        ['Constructing', 'Hidden']),
            State.State('SayIt', self.__enterSayIt, self.__exitSayIt, ['Hidden'])], 'Hidden', 'Hidden')
        chatInputGui.removeNode()
        self.fsm.enterInitialState()
    
    def delete(self):
        self.frame.destroy()
        del self.chatMgr
        del self.frame
        del self.backButton
        del self.chatButton
        del self.cancelButton
        del self.displayText
        del self.fsm
        del self.sentenceList

    def show(self):
        self.curQTnode = TTQTGraph.QTGraph['start']
        self.fsm.request('Constructing')

    def hide(self):
        self.fsm.request('Hidden')

    def getSentenceCleartext(self):
        sentence = ''
        for entry in self.sentenceList:
            sentence = sentence + entry[0].getPhrase(entry[1])
        
        return sentence

    def getSentenceEncoded(self):
        sentence = []
        for entry in self.sentenceList:
            sentence.append(entry[1])
        
        return sentence

    def __cancelButtonPressed(self):
        self.chatMgr.fsm.request('mainMenu')

    def __backButtonPressed(self):
        if len(self.sentenceList) == 0:
            self.chatMgr.fsm.request('mainMenu')
        else:
            prevState = self.sentenceList.pop(len(self.sentenceList) - 1)
            self.newQTnode = prevState[0]
            self.fsm.request('ConstructingTransition')

    def __chatButtonPressed(self):
        self.fsm.request('SayIt')

    def __enterHidden(self):
        self.sentenceList = []
        self.frame.hide()

    def __exitHidden(self):
        pass

    def __enterConstructing(self):
        self.frame.show()
        self.displayText['text'] = self.getSentenceCleartext()
        textNode = self.displayText.component('text0').node()
        # Don't know why but the position doesn't reset
        # on its own when reopening the menu; it did in
        # 2001 but whatever this solves that
        if len(self.displayText['text']) == 0:
            width = 0
        else:
            width = textNode.getWidth() * 0.06
        self.chatHead.setPos(-0.65 + width, 0.0, -0.06)
        self.curQTnode.nodepath.reparentTo(self.chatHead)
        self.curQTnode.nodepath.setPos(0, 0, 0)
        self.curQTnode.setSelectionHandler(self.__selectionMade)
        base.playSfx(self.chatMgr.openScSfx)

    def __selectionMade(self, index):
        self.newQTnode = self.curQTnode[index]
        self.sentenceList.append([
            self.curQTnode,
            index])
        if self.newQTnode == TTQTNode.QTSend:
            self.fsm.request('SayIt')
        else:
            self.fsm.request('ConstructingTransition')

    def __exitConstructing(self):
        self.curQTnode.clearSelectionHandler()
        self.curQTnode.nodepath.reparentTo(hidden)
        del self.curQTnode

    def __enterConstructingTransition(self):
        self.curQTnode = self.newQTnode
        self.fsm.request('Constructing')

    def __exitConstructingTransition(self):
        pass

    def __enterSayIt(self):
        self.chatMgr.sendQTChatMessage(self.getSentenceEncoded())
        self.chatMgr.fsm.request('mainMenu')

    def __exitSayIt(self):
        pass


