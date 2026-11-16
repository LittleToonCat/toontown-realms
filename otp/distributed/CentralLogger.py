from direct.distributed.DistributedObjectGlobal import DistributedObjectGlobal
REPORT_PLAYER = 'REPORT_PLAYER'
ReportFoulLanguage = 'MODERATION_FOUL_LANGUAGE'
ReportPersonalInfo = 'MODERATION_PERSONAL_INFO'
ReportRudeBehavior = 'MODERATION_RUDE_BEHAVIOR'
ReportBadName = 'MODERATION_BAD_NAME'
ReportHacking = 'MODERATION_HACKING'


class CentralLogger(DistributedObjectGlobal):
    PlayersReportedThisSession = {}

    def __init__(self, cr):
        DistributedObjectGlobal.__init__(self, cr)
        cr.centralLogger = self

    def hasReportedPlayer(self, targetDISLId, targetAvId):
        return (targetDISLId, targetAvId) in self.PlayersReportedThisSession

    def reportPlayer(self, category, targetDISLId, targetAvId, description = 'None'):
        # We can't report a player twice in one session
        if self.hasReportedPlayer(targetDISLId, targetAvId):
            return False

        # Add the target to our reported players lsit
        #self.PlayersReportedThisSession[targetDISLId, targetAvId] = 1

        # Send the report to the server
        self.sendUpdate('sendMessage', [category, REPORT_PLAYER, description, targetAvId])

        # Signal success
        return True

    def writeClientEvent(self, eventString):
        # We don't really care about writing client events to the server right now
        # Maybe we can add this back at some other point
        return
