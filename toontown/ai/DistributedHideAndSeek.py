from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.gui.OnscreenText import OnscreenText
from panda3d.toontown import NametagGlobals
from .DistributedMicroGame import DistributedMicroGame
from toontown.toonbase import TTLocalizer, ToontownGlobals


class DistributedHideAndSeek(DistributedMicroGame):
    notify = directNotify.newCategory('DistributedHideAndSeek')
    defaultTransitions = {'Off': ['Start'],
                          'Start': ['Seek', 'Done', 'Off'],
                          'Seek': ['Done', 'Off'],
                          'Done': ['Off']}

    def __init__(self, cr):
        DistributedMicroGame.__init__(self, cr)
        self._seekerText = OnscreenText(parent=aspect2d, mayChange=1, wordwrap=22, scale=0.1, fg=(1, 0, 0, 1),
                                        font=ToontownGlobals.getSignFont(), pos=(0.05, -0.75), text='')
        self._seekerText.setBin('gui-popup', 0)
        base.cr.hideAndSeekGame = self

    def delete(self):
        self._seekerText.destroy()
        del self._seekerText
        del base.cr.hideAndSeekGame
        self.ignoreAll()
        DistributedMicroGame.delete(self)

    def isActive(self):
        return self.getCurrentOrNextState() in ('Start', 'Seek')

    def setSeeker(self, name):
        if name == '':
            self._seekerText['text'] = ''
        else:
            self._seekerText['text'] = TTLocalizer.HideAndSeekCurrentSeeker % name

    def __cleanupHideEvents(self):
        for event in self.getAllAccepting():
            if 'enterdistAvatarCollNode-' in event:
                self.ignore(event)

    def setupRules(self, flag):
        DistributedMicroGame.setupRules(self, flag)
        if flag:
            base.disableToggleHotkeys()
            if NametagGlobals.getMasterNametagsVisible():
                base.toggleNametags()
            if hasattr(base, 'oobeMode') and base.oobeMode:
                base.oobe()
                if hasattr(base, 'oobeCullFrustum') and base.oobeCullFrustum:
                    base.oobeCull()
        else:
            if not NametagGlobals.getMasterNametagsVisible():
                base.toggleNametags()
            base.enableToggleHotkeys()

    def filterStart(self, request, args):
        self.notify.debug("filter%s( '%s', '%s' )" % (self.state, request, args))
        if request == self.state:
            return
        elif request == 'next':
            return 'Seek'
        else:
            return self.defaultFilter(request, args)

    def enterSeek(self):
        self.setupRules(True)

    def filterSeek(self, request, args):
        self.notify.debug("filter%s( '%s', '%s' )" % (self.state, request, args))
        if request == self.state:
            return
        elif request == 'next':
            return 'Done'
        else:
            return self.defaultFilter(request, args)

    def exitSeek(self):
        pass

    def setCollMaskWall(self, avId):
        # Change collide mask so players can be found
        if avId == 0:
            # Sending 0 changes all toons in the zone
            otherToons = base.cr.doFindAllOfType('DistributedToon')
            if otherToons:
                for toon in otherToons[0]:
                    if toon.isPlayerControlled():
                        distCNP = toon.find('**/distAvatarCollNode*')
                        distCNP.node().setIntoCollideMask(ToontownGlobals.WallBitmask)
        elif avId != base.localAvatar.getDoId():
            # Sending an avId only changes that toon
            toon = base.cr.doId2do.get(avId)
            if toon and toon.isPlayerControlled():
                distCNP = toon.find('**/distAvatarCollNode*')
                distCNP.node().setIntoCollideMask(ToontownGlobals.WallBitmask)

    def setCollMaskPie(self):
        # Game done - change collide masks back
        otherToons = base.cr.doFindAllOfType('DistributedToon')
        if otherToons:
            for toon in otherToons[0]:
                if toon.isPlayerControlled():
                    distCNP = toon.find('**/distAvatarCollNode*')
                    distCNP.node().setIntoCollideMask(ToontownGlobals.PieBitmask)

    def acceptFoundEvent(self, avId):
        self.accept('enterdistAvatarCollNode-' + str(avId), self.__sendFound, [avId])

    def __sendFound(self, avId, collisionEntry):
        self.sendUpdate('found', [avId])

    def sendClearHideEvents(self):
        self.__cleanupHideEvents()
