from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectGlobalAI import DistributedObjectGlobalAI

from datetime import datetime

import json
import os
import time

from toontown.toonbase import ServerSettings

REPORT_PLAYER = 'REPORT_PLAYER'


class CentralLoggerAI(DistributedObjectGlobalAI):
    notify = DirectNotifyGlobal.directNotify.newCategory("CentralLoggerAI")

    def __init__(self, air):
        DistributedObjectGlobalAI.__init__(self, air)

        # If we don't have a logs/moderation/reports directory, generate one
        if not os.path.exists('logs/'):
            os.mkdir('logs/')

        if not os.path.exists('logs/moderation/'):
            os.mkdir('logs/moderation/')

        if not os.path.exists('logs/moderation/reports/'):
            os.mkdir('logs/moderation/reports/')

    def sendMessage(self, category, reportType, description, targetAvId):
        # We've gotten a report! Let's verify some things to make sure it's valid

        # So... it turns out that this system isn't just used for normal reports. Yeah...
        # Well, WE only want to use it for normal reports. So ignore anything that isn't a report
        if reportType != REPORT_PLAYER:
            return

        # Check that the avId exists
        avId = self.air.getAvatarIdFromSender()
        if not avId:
            self.notify.warning(
                    'Toon with non-existent avId attempted to report Toon with avId of {}!'.format(targetAvId))
            return

        # Check that an avatar is associated with this avId
        av = self.air.doId2do.get(avId)
        if not av:
            self.notify.warning(
                    'Toon with avId of {} has no avatar associated with their avId, but attempted to report Toon with '
                    'avId of {}!'.format(
                            avId, targetAvId))
            return

        # Make sure there is a valid category and reportType
        if category == '' or reportType == '':
            self.notify.warning('Invalid category or reportType!')
            return

        # Make sure the target DISLId and avId are valid
        if not targetAvId:
            self.notify.warning('Invalid target avId!')
            return

        # Make sure the target Toon has an avatar associated with their avId
        targetAv = self.air.doId2do.get(targetAvId)
        if not targetAv:
            self.notify.warning('Target Toon with avId of {} does not exist!'.format(targetAvId))
            return

        # Looks like everything's good, so let's structure our report info
        targetName = targetAv.getName()

        # todo: implement!
        #
        report = {
            'reporterId': avId,
            'reporterName': av.getName(),
            'timestamp': datetime.utcnow().strftime("%d-%b-%Y (%H:%M:%S.%f)"),
            'category': category,
            'type': reportType,
            'reportDescription': description,
            'reportedId': targetAvId,
            'reportedName': targetName,
        }
        if ServerSettings.ReportsEndpoint.get() == 'local':
            timestamp = time.strftime("%Y-%m-%d-%H-%M-%S")
            fileName = 'report-{}-{}-{}'.format(targetName, targetAvId, timestamp)
            with open('logs/moderation/reports/' + fileName + '.json', 'w') as data:
                json.dump(report, data, indent = 4)
                data.close()
        else:
            self.sendPingToAPI(report)

    def sendPingToAPI(self, data):
        def __callback(resp):
            if 'status' not in resp:
                self.air.apinotify.info('Successfully sent report to the API')
                return  # ???
            status = resp['status']
            message = resp['message']

            if status != 200:
                self.air.apinotify.info('Could not send the report to the API! (Message: %s)' % message)
                return

            self.air.apinotify.info('Successfully sent report to API')
        self.air.httpRequest(ServerSettings.ReportsEndpoint.get(),
                             __callback, data = data,
                             authHeader = ServerSettings.ReportsEndpointAuthHeader.get())
