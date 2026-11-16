from panda3d.core import *
from . import ShtikerPage
from direct.gui.DirectGui import *
from toontown.toonbase import TTLocalizer
import os, string, sys
from toontown.toonbase import ToontownGlobals, ClientSettings
from toontown.toontowngui import TTDialog
if sys.platform == 'win32':
    from winreg import ConnectRegistry, OpenKey, HKEY_CURRENT_USER, QueryValueEx


class PhotoAlbumPage(ShtikerPage.ShtikerPage):
    screenshotDir = './screenshots'

    screenshotNames = []
    for prefix in ConfigVariableList('screenshot-prefix'):
        screenshotNames.append(prefix)

    def __init__(self):
        ShtikerPage.ShtikerPage.__init__(self)
        self.textRolloverColor = Vec4(1, 1, 0, 1)
        self.textDownColor = Vec4(0.5, 0.9, 1, 1)
        self.textDisabledColor = Vec4(0.4, 0.8, 0.4, 1)
        self.photos = {}
        self.selectedFileName = None
        self.photoIndex = 0

    def load(self):
        self.title = DirectLabel(parent=self, relief=None, text=TTLocalizer.PhotoPageTitle, text_scale=0.1, pos=(0, 0, 0.6))
        self.pictureImage = loader.loadModel('phase_3.5/models/gui/photo_frame')
        self.pictureImage.setScale(0.2)
        self.pictureImage.setPos(0.44, 0, 0.25)
        self.pictureImage.reparentTo(self)
        self.pictureFg = self.pictureImage.find('**/fg')
        self.pictureFg.setColor(1, 1, 1, 0.1)
        guiButton = loader.loadModel('phase_3/models/gui/quit_button')
        self.pictureCaption = DirectLabel(parent=self, relief=None, text=TTLocalizer.PhotoPageCaption, text_scale=0.05,
                                          text_wordwrap=10, text_align=TextNode.ACenter, pos=(0.45, 0, -0.22))
        self.renameButton = DirectButton(parent=self, relief=None, image=(guiButton.find('**/QuitBtn_UP'),
                                                                          guiButton.find('**/QuitBtn_DN'),
                                                                          guiButton.find('**/QuitBtn_RLVR')),
                                         image_scale=(1, 1, 1), pos=(0.45, 0, -0.35),
                                         text=TTLocalizer.PhotoPageCaptionButton, text_scale=0.06, text_pos=(0, -0.02),
                                         command=self.renameImage, state=DGG.DISABLED)
        trashcanGui = loader.loadModel('phase_3/models/gui/trashcan_gui')
        self.deleteButton = DirectButton(parent=self, image=(trashcanGui.find('**/TrashCan_CLSD'),
                                                             trashcanGui.find('**/TrashCan_OPEN_default'),
                                                             trashcanGui.find('**/TrashCan_RLVR_default')),
                                         text=('', TTLocalizer.PhotoPageDelete, TTLocalizer.PhotoPageDelete),
                                         text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1), text_scale=0.1,
                                         text_pos=(0, -0.1), text_font=ToontownGlobals.getInterfaceFont(),
                                         textMayChange=0, relief=None, pos=(0.73, 0, -0.33), scale=0.4,
                                         state=DGG.DISABLED, command=self.deleteImage)
        self.directoryButton = DirectButton(parent=self, relief=None, image=(guiButton.find('**/QuitBtn_UP'),
                                                                             guiButton.find('**/QuitBtn_DN'),
                                                                             guiButton.find('**/QuitBtn_RLVR')),
                                            image_scale=(1.3, 1, 1), pos=(0.46, 0, -0.50),
                                            text=TTLocalizer.PhotoPageDirectory, text_scale=0.06, text_pos=(0, -0.02),
                                            command=self.openPhotoDirectory)
        guiButton.removeNode()
        trashcanGui.removeNode()
        gui = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
        self.scrollList = DirectScrolledList(parent=self, relief=None, forceHeight=0.07, pos=(-0.5, 0, 0),
                                             incButton_image=(gui.find('**/FndsLst_ScrollUp'),
                                                              gui.find('**/FndsLst_ScrollDN'),
                                                              gui.find('**/FndsLst_ScrollUp_Rllvr'),
                                                              gui.find('**/FndsLst_ScrollUp')),
                                             incButton_relief=None, incButton_scale=(1.3, 1.3, -1.3),
                                             incButton_pos=(0, 0, -0.51), incButton_image3_color=Vec4(1, 1, 1, 0.2),
                                             decButton_image=(gui.find('**/FndsLst_ScrollUp'),
                                                              gui.find('**/FndsLst_ScrollDN'),
                                                              gui.find('**/FndsLst_ScrollUp_Rllvr'),
                                                              gui.find('**/FndsLst_ScrollUp')), decButton_relief=None,
                                             decButton_scale=(1.3, 1.3, 1.3), decButton_pos=(0, 0, 0.51),
                                             decButton_image3_color=Vec4(1, 1, 1, 0.2), itemFrame_pos=(-0.237, 0, 0.41),
                                             itemFrame_scale=1.0, itemFrame_relief=DGG.SUNKEN,
                                             itemFrame_frameSize=(-0.05, 0.66, -0.88, 0.06),
                                             itemFrame_frameColor=(0.85, 0.95, 1, 1),
                                             itemFrame_borderWidth=(0.01, 0.01), numItemsVisible=13, items=[])
        self.renamePanel = DirectFrame(parent=self, relief=None, pos=(0.45, 0, -0.45), image=DGG.getDefaultDialogGeom(),
                                       image_color=ToontownGlobals.GlobalDialogColor, image_scale=(1.0, 1.0, 0.6),
                                       text=TTLocalizer.PhotoPageCaptionPhoto, text_scale=0.06, text_pos=(0.0, 0.13),
                                       sortOrder=DGG.NO_FADE_SORT_INDEX)
        self.renameEntry = DirectEntry(parent=self.renamePanel, relief=DGG.SUNKEN, scale=0.06, pos=(-0.3, 0, 0),
                                       borderWidth=(0.1, 0.1), numLines=1, cursorKeys=1, frameColor=(0.8, 0.8, 0.5, 1),
                                       frameSize=(-0.2, 10, -0.4, 1.1), command=self.renameDialog)
        buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        self.cancelButton = DirectButton(parent=self.renamePanel, image=(buttons.find('**/CloseBtn_UP'),
                                                                         buttons.find('**/CloseBtn_DN'),
                                                                         buttons.find('**/CloseBtn_Rllvr')),
                                         relief=None, text=TTLocalizer.OL.DialogCancel, text_scale=0.05,
                                         text_pos=(0.0, -0.1), pos=(0.0, 0.0, -0.1), command=self.renameCancel)
        self.renamePanel.hide()
        self.deletePanel = None
        self.errorPanel = None
        self.leftArrow = DirectButton(parent=self, relief=None, image=(gui.find('**/Horiz_Arrow_UP'),
                                                                       gui.find('**/Horiz_Arrow_DN'),
                                                                       gui.find('**/Horiz_Arrow_Rllvr'),
                                                                       gui.find('**/Horiz_Arrow_UP')),
                                      image3_color=Vec4(1, 1, 1, 0.5), scale=(-1.0, 1.0, 1.0), pos=(0.15, 0, -0.21),
                                      command=self.prevPhoto, state=DGG.DISABLED)
        self.rightArrow = DirectButton(parent=self, relief=None, image=(gui.find('**/Horiz_Arrow_UP'),
                                                                        gui.find('**/Horiz_Arrow_DN'),
                                                                        gui.find('**/Horiz_Arrow_Rllvr'),
                                                                        gui.find('**/Horiz_Arrow_UP')),
                                       image3_color=Vec4(1, 1, 1, 0.5), pos=(0.75, 0, -0.21), command=self.nextPhoto,
                                       state=DGG.DISABLED)
        gui.removeNode()
        buttons.removeNode()

    def unload(self):
        del self.title
        del self.scrollList
        self.pictureImage.removeNode()
        self.pictureFg.removeNode()
        del self.pictureCaption
        del self.deleteButton
        del self.renameButton
        del self.renamePanel
        del self.renameEntry
        del self.cancelButton
        if self.deletePanel:
            self.deletePanel.cleanup()
        del self.deletePanel
        if self.errorPanel:
            self.errorPanel.cleanup()
        del self.errorPanel
        del self.leftArrow
        del self.rightArrow
        del self.directoryButton
        ShtikerPage.ShtikerPage.unload(self)

    def __makeErrorPanel(self, text=TTLocalizer.PhotoPageGenericError):
        self.errorPanel = TTDialog.TTDialog(parent=self, text=text, style=TTDialog.Acknowledge,
                                            command=self.handleErrorAck, fadeScreen=False)

    def __makeDeletePanel(self, text=TTLocalizer.PhotoPageDeletePrompt):
        self.deletePanel = TTDialog.TTDialog(parent=self, text=text, style=TTDialog.YesNo, command=self.handleDelete,
                                             fadeScreen=False)

    def renameDialog(self, str):
        messenger.send('wakeup')
        separator = '_'
        validChars = string.ascii_letters + string.digits + ' -\''
        str = [s for s in str if s in validChars]
        if not str:
            self.renameCleanup()
            return 0
        newStr = ''
        for s in str:
            newStr += s
        oldName = self.selectedFileName
        numUnders = oldName.count(separator)
        if numUnders == 0:
            prevName = ''
            endPart = ''
            for name in self.screenshotNames:
                if name == oldName[0:len(name)]:
                    prevName = oldName[0:len(name) + 1]
                    endPart = oldName[len(name):]
                    break
            if not prevName:
                prevName = self.screenshotNames[0][0:11]
            if not endPart:
                endPart = self.screenshotNames[0][10:]
            newName = prevName + separator + newStr + separator + endPart
        elif numUnders == 2:
            sp = oldName.split(separator)
            newName = sp[0] + separator + newStr + separator + sp[2]
        else:
            self.renameCleanup()
            return 0
        oldFile = self.__joinFilePath(oldName)
        if os.path.isfile(oldFile):
            os.rename(oldFile, self.__joinFilePath(newName))
        else:
            self.__makeErrorPanel(TTLocalizer.PhotoPageRenameFailed)
        self.renameCleanup()
        self.updateScrollList()
        self.chosePhoto(newName)
        return 1

    def __joinFilePath(self, fileName):
        return os.path.join(self.getScreenshotDirectory(), fileName)

    def renameCancel(self):
        messenger.send('wakeup')
        self.renameCleanup()

    def renameCleanup(self):
        self.renamePanel.hide()
        chatEntry = base.localAvatar.chatMgr.chatInputNormal.chatEntry
        chatEntry['backgroundFocus'] = self.oldFocus
        base.controlManager.removeDisabledHotkey(ToontownGlobals.HotkeyMovement, ToontownGlobals.HotkeyLeft)
        base.controlManager.removeDisabledHotkey(ToontownGlobals.HotkeyMovement, ToontownGlobals.HotkeyRight)

    def renameImage(self):
        self.deleteCleanup()
        self.renameEntry.set(self.getPhotoName(self.selectedFileName))
        self.renamePanel.show()
        chatEntry = base.localAvatar.chatMgr.chatInputNormal.chatEntry
        chatEntry['backgroundFocus'] = 0
        self.renameEntry['focus'] = 1
        base.controlManager.addDisabledHotkey(ToontownGlobals.HotkeyMovement, ToontownGlobals.HotkeyLeft)
        base.controlManager.addDisabledHotkey(ToontownGlobals.HotkeyMovement, ToontownGlobals.HotkeyRight)
        messenger.send('wakeup')

    def handleDelete(self, value):
        messenger.send('wakeup')
        if value == DGG.DIALOG_YES:
            self.deleteConfirm()
        else:
            self.deleteCancel()

    def deleteConfirm(self):
        file = self.__joinFilePath(self.selectedFileName)
        if os.path.isfile(file):
            os.remove(file)
        else:
            self.__makeErrorPanel(TTLocalizer.PhotoPageDeleteFailed)
        self.selectedFileName = None
        self.deleteCleanup()
        self.updateScrollList()
        if len(self.photos) == 0:
            self.rightArrow['state'] = DGG.DISABLED
            self.leftArrow['state'] = DGG.DISABLED

    def deleteCancel(self):
        self.deleteCleanup()

    def deleteCleanup(self):
        self.__enableImageButtons()
        if self.deletePanel:
            self.deletePanel.cleanup()

    def deleteImage(self):
        self.renameCleanup()
        self.deletePanel = TTDialog.TTDialog(parent=self, text=TTLocalizer.PhotoPageDeletePromptPhotoName % self.getPhotoName(self.selectedFileName),
                                             style=TTDialog.YesNo, command=self.handleDelete, fadeScreen=False)
        self.__disableImageButtons()
        messenger.send('wakeup')

    def __disableImageButtons(self):
        for imageBtn in self.scrollList['items']:
            imageBtn['state'] = DGG.DISABLED

        self.rightArrow['state'] = DGG.DISABLED
        self.leftArrow['state'] = DGG.DISABLED

    def __enableImageButtons(self):
        for imageBtn in self.scrollList['items']:
            imageBtn['state'] = DGG.NORMAL

        self.checkArrowStatus()

    def handleErrorAck(self, value):
        if self.errorPanel:
            self.errorPanel.cleanup()

    def makePhotoButton(self, fileName):
        return DirectButton(relief=None, text=self.getPhotoName(fileName), text_scale=0.06, text_align=TextNode.ALeft,
                            text1_bg=self.textDownColor, text2_bg=self.textRolloverColor,
                            text3_fg=self.textDisabledColor, command=self.chosePhoto, extraArgs=[fileName])

    def getPhotoName(self, fileName):
        separator = '_'
        numUnders = fileName.count(separator)
        if numUnders == 0:
            return TTLocalizer.PhotoPageUnnamed
        elif numUnders == 2:
            return fileName.split(separator)[1]
        else:
            return TTLocalizer.PhotoPageUnnamed

    def chosePhoto(self, fileName):
        if fileName and os.path.isfile(self.__joinFilePath(fileName)):
            self.selectedFileName = fileName
            photoTexture = loader.loadTexture(Filename.fromOsSpecific(self.__joinFilePath(fileName)))
            photoName = self.getPhotoName(fileName)
            self.pictureFg.setTexture(photoTexture, 1)
            self.pictureFg.setColor(1, 1, 1, 1)
            self.pictureCaption['text'] = photoName
            self.renameButton['state'] = DGG.NORMAL
            self.deleteButton['state'] = DGG.NORMAL
            self.renameEntry.set(photoName)
            self.photoIndex = self.getPhotos().index(fileName)
            self.checkArrowStatus()
        else:
            self.selectedFileName = None
            self.pictureFg.clearTexture()
            self.pictureFg.setColor(1, 1, 1, 0.1)
            self.pictureCaption['text'] = ''
            self.renameButton['state'] = DGG.DISABLED
            self.deleteButton['state'] = DGG.DISABLED
            self.renameEntry.set('')

    def getPhotos(self):
        if os.path.exists(self.getScreenshotDirectory()):
            files = os.listdir(self.getScreenshotDirectory())
            photos = []
            for fileName in files:
                for name in self.screenshotNames:
                    if fileName[0:len(name)] == name and fileName[-3:] in ToontownGlobals.ScreenshotFormats:
                        photos.append(fileName)

            return photos
        return

    def getScreenshotDirectory(self):
        folder = os.path.join(os.getcwd(), 'screenshots')
        if sys.platform == 'win32':
            directoryIndex = ClientSettings.ScreenshotDirectory.get()
            if directoryIndex == 1:
                # Retrieve the Windows Pictures Library location
                reg = ConnectRegistry(None, HKEY_CURRENT_USER)
                akey = OpenKey(reg, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")

                location = QueryValueEx(akey, "My Pictures")[0]
                folder = os.path.join(location, 'Toontown Realms')
                reg.Close()

        if not os.path.exists(folder):
            os.mkdir(folder)
        return folder

    def openPhotoDirectory(self):
        messenger.send('wakeup')
        try:
            path = self.getScreenshotDirectory()
            if sys.platform == 'win32':
                os.startfile(path)
            elif sys.platform == 'darwin':
                os.system('open "%s"' % path)
            else:
                os.system('xdg-open "%s"' % path)
        except (FileNotFoundError, OSError, IOError):
            self.__makeErrorPanel(TTLocalizer.PhotoPageDirectoryFailed)

    def newScreenshot(self, filename):
        self.updateScrollList()

    def updateScrollList(self):
        newPhotos = self.getPhotos()
        for photo in list(self.photos.keys()):
            if photo not in newPhotos:
                photoButton = self.photos[photo]
                self.scrollList.removeItem(photoButton)
                photoButton.destroy()
                del self.photos[photo]

        if newPhotos:
            for photo in newPhotos:
                if photo not in self.photos:
                    photoButton = self.makePhotoButton(photo)
                    self.scrollList.addItem(photoButton)
                    self.photos[photo] = photoButton

        if list(self.photos.keys()):
            self.chosePhoto(list(self.photos.keys())[0])
        else:
            self.chosePhoto(None)

    def enter(self):
        self.accept('screenshot', self.newScreenshot)
        self.updateScrollList()
        chatEntry = base.localAvatar.chatMgr.chatInputNormal.chatEntry
        self.oldFocus = chatEntry['backgroundFocus']
        ShtikerPage.ShtikerPage.enter(self)

    def exit(self):
        self.ignore('screenshot')
        self.renameCleanup()
        self.deleteCleanup()
        ShtikerPage.ShtikerPage.exit(self)

    def checkArrowStatus(self):
        if len(self.photos) == 0:
            self.rightArrow['state'] = DGG.DISABLED
            self.leftArrow['state'] = DGG.DISABLED
            return

        self.leftArrow['state'] = DGG.NORMAL
        self.rightArrow['state'] = DGG.NORMAL

        if len(self.getPhotos()) - 1 == self.photoIndex:
            self.rightArrow['state'] = DGG.DISABLED
        if self.photoIndex - 1 < 0:
            self.leftArrow['state'] = DGG.DISABLED

    def prevPhoto(self):
        messenger.send('wakeup')
        try:
            self.photoIndex -= 1
            self.chosePhoto(self.getPhotos()[self.photoIndex])
        except:
            self.photoIndex = 0

    def nextPhoto(self):
        messenger.send('wakeup')
        try:
            self.photoIndex += 1
            self.chosePhoto(self.getPhotos()[self.photoIndex])
        except:
            self.photoIndex = 0
