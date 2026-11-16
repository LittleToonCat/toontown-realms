##################################################
# The Toontown Realms Magic Word Manager
##################################################
# Co-Authors: John Cote, William Lord, Frank, Nick, Little Cat, Ooowoo, Drew, Leo
# Copyright: Copyright 2022, Toontown Realms
# License: MIT
# Version: 1.0.0
##################################################
from json import JSONDecodeError
from typing import Any, Dict

from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObjectAI

from otp.avatar.DistributedPlayerAI import DistributedPlayerAI

from toontown.spellbook.MagicWordConfig import *
from toontown.spellbook.MagicWordIndex import *

import json
import os
from datetime import datetime

# All of the data regarding our Magic Words
from toontown.toon.DistributedToonAI import DistributedToonAI
from toontown.toonbase import ServerSettings

MagicWordIndex = magicWordIndex.copy()

# We allow server hosters to change a few things about the Magic Words on their server
# These are the default values generated with spellbook.json to help get them started
spellbookJsonDefaultValues = CUSTOM_SPELLBOOK_DEFAULT

# If we don't have a config directory, make it
if not os.path.exists('config/'):
    os.mkdir('config/')

# If spellbook.json doesn't exist, make it
if not os.path.isfile('config/spellbook.json'):
    with open('config/spellbook.json', 'w') as data:
        data.write(spellbookJsonDefaultValues)
        data.close()

# Now load the data from spellbook.json
with open('config/spellbook.json') as data:
    spellbook = json.load(data)


# Make changes to all the Magic Words based on the data in spellbook.json
words = spellbook.get('words')
wordData = []
for word in words:
    name = word.get('name')
    accessLevel = word.get('access')
    cooldown = word.get('cooldown')
    anyTarget = word.get('anyTarget')
    # Pack these up to ship them off to clients
    wordData.append((name if name is not None else '', accessLevel if accessLevel is not None else 'USER',
                     cooldown if cooldown is not None else 0, anyTarget if anyTarget is not None else False))

    if accessLevel not in list(OTPGlobals.AccessLevelName2Int.keys()):
        break

    if cooldown:
        cooldown = max(0, min(cooldown, 300))

    try:
        wordInfo = MagicWordIndex[str(name.lower())]
        for alias in wordInfo['aliases']:
            if accessLevel is not None:
                MagicWordIndex[alias]['access'] = accessLevel
            if cooldown is not None:
                MagicWordIndex[alias]['cooldown'] = cooldown
            if anyTarget is not None:
                MagicWordIndex[alias]['anyTarget'] = anyTarget
    except:
        pass

# If we don't have a logs/moderation/spellbook directory, generate one
if not os.path.exists('logs/'):
    os.mkdir('logs/')

if not os.path.exists('logs/moderation/'):
    os.mkdir('logs/moderation/')

if not os.path.exists('logs/moderation/spellbook'):
    os.mkdir('logs/moderation/spellbook')

# Get the file name for this spellbook log
ltime = 1 and time.localtime()
logSuffix = '%02d%02d%02d_%02d%02d%02d' % (ltime[0] - 2000, ltime[1], ltime[2], ltime[3], ltime[4], ltime[5])
fileName = 'spellbook-%s' % logSuffix


def getFullFileName():
    return 'logs/moderation/spellbook/' + fileName + '.json'


class ToontownRealmsMagicWordManagerAI(DistributedObjectAI.DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownRealmsMagicWordManagerAI')

    def __init__(self, air):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)

        self.cooldown = []
        self.loggedWords = -1
        self.botCommands = True

        if ServerSettings.LogMagicWords.get():
            self.generateLogFile()

    def announceGenerate(self):
        DistributedObjectAI.DistributedObjectAI.announceGenerate(self)

        # If bot.json doesn't exist, make it
        if not os.path.isfile('config/bot.json'):
            with open('config/bot.json', 'w') as data:
                data.write(BOT_COMMANDS_DEFAULT)
                data.close()
        if not os.path.isfile('config/web_commands.json'):
            with open('config/web_commands.json', 'w') as data:
                data.write('[]')
                data.close()

        if self.botCommands:
            self.doMethodLater(1.0, self.detectBotCommands, 'detectBotCommands')
            self.doMethodLater(1.0, self.detectWebCommands, 'detectWebCommands')

        self.sendChanges()

    def delete(self):
        DistributedObjectAI.DistributedObjectAI.delete(self)

        if self.botCommands:
            self.removeTask('detectBotCommands')
            self.removeTask('detectWebCommands')

    def sendChanges(self):
        # Send changes from the magic word json file down to the client so the client can use them
        if wordData:
            self.sendUpdate('sendWordData', [wordData])
        self.sendUpdate('sendCooldownBypass', [ServerSettings.MagicWordCooldownBypassMinimumAccess.get()])

    def requestExecuteMagicWord(self, affectRange, affectType, affectExtra, lastClickedAvId, magicWord):
        avId = self.air.getAvatarIdFromSender()

        # It's not good if we can't get the avId for whatever reason
        if not avId:
            self.notify.warning('requestExecuteMagicWord: Magic Word use requested but invoker avId is non-existent!')
            return

        # We also need the Toon as well, or else this Magic Word isn't going to do much good
        toon: DistributedToonAI = self.air.doId2do.get(avId)
        if not toon:
            self.notify.warning('requestExecuteMagicWord: Magic Word use requested but invoker avatar is non-existent!')
            return

        # If the avId of the invoker is in the Episode Manager, don't allow the use of the Magic Word
        # Instead, let's just tell the user they can't use it because they're in an Episode
        if avId in list(self.air.episodeManager.avId2fsm.keys()):
            self.generateResponse(avId=avId, responseType="Episode")
            return

        # Same thing with the Toontorial. Magic Words are strictly forbidden here
        # Tell the user they can't use it because they're in the Toontorial
        if self.air.tutorialManager.playerDict.get(avId):
            self.generateResponse(avId=avId, responseType="Tutorial")
            return

        self.air.logEvent(3, avId, toon.getName(), toon.DISLid, magicWord, target = lastClickedAvId)

        if ServerSettings.LogMagicWords.get():
            # Log Magic Word usage for moderation purposes
            log = {'invokerId': avId,
                   'invokerName': toon.getName(),
                   'timestamp': datetime.now().strftime("%d-%b-%Y (%H:%M:%S.%f)"),
                   'magicWord': magicWord,
                   'lastClickedAvId': lastClickedAvId,
                   'affectRange': affectRange,
                   'affectType': affectType,
                   'affectExtra': affectExtra}
            self.logMagicWord(log)

        # Our Magic Word affectRange is either SELF (the invoker) or BOTH (invoker and a target)
        # Because of this, we should add the invoker to the target list
        targetIds = []
        if affectRange in (AFFECT_SELF, AFFECT_BOTH):
            targetIds.append(avId)

        # This Magic Word's affectRange is either OTHER (a target) or BOTH (invoker and a target)
        # However, it's also a NORMAL affectType, so it's not as if we're targeting a zone or the whole server
        # In that case, let's try to grab the single target by the lastClickedAvId provided by the invoker
        lastClickedToon = None
        if (affectRange in (AFFECT_OTHER, AFFECT_BOTH)) and affectType == AFFECT_NORMAL:
            if lastClickedAvId:
                lastClickedToon = self.air.doId2do.get(lastClickedAvId)
                if lastClickedToon:
                    targetIds.append(lastClickedAvId)
            else:
                self.generateResponse(avId=avId, responseType="NoTarget")
                return

        # The affectType is ZONE (zone the invoker is in), SERVER (the entire server), or RANK (specified access level)
        # Gather all of the Toons using whichever method this Magic Word requests
        if affectType in (AFFECT_ZONE, AFFECT_SERVER, AFFECT_RANK):
            toonIds = []
            # Iterate over a copy of every single doId on the server
            for doId in list(self.air.doId2do.keys())[:]:
                do = self.air.doId2do.get(doId)
                # We only care if our DistributedObject is a player that is NOT our invoker (we dealt with that earlier)
                if isinstance(do, DistributedPlayerAI) and do.isPlayerControlled() and do != toon:
                    # Only add the Toons that are in the same zone as the invoker
                    if affectType == AFFECT_ZONE and do.zoneId == toon.zoneId:
                        toonIds.append(doId)
                    # Add every Toon regardless of zone
                    elif affectType == AFFECT_SERVER:
                        toonIds.append(doId)
                    # Only add the Toons that have the Access Level specified when the Magic Word was used
                    elif affectType == AFFECT_RANK and do.getAccessLevel() == affectExtra:
                        toonIds.append(doId)

            # There were no Toons we could perform this Magic Word on, so let the invoker know that
            if not toonIds and not targetIds:
                self.generateResponse(avId=avId, responseType="NoTarget")
                return

            # Add the found Toons to the targetId list
            targetIds += toonIds

        # If, at this point, we still don't have any targets somehow, then let the invoker know that
        if not targetIds:
            self.generateResponse(avId=avId, responseType="NoTarget")
            return

        # Figure out some info related to the Magic Word early
        # We need to know this earlier than we did before because of the new anyTarget field
        magicWord, args = (magicWord.split(' ', 1) + [''])[:2]

        # Get the name of the word in lowercase
        magicWord = magicWord.lower()

        # Lookup the info for this word
        magicWordInfo = MagicWordIndex[magicWord]

        # Okay, back to dealing with targets now
        # Access level of the invoker
        invokerAccess = int(round(toon.getAccessLevel(), -2))

        # Access level of the selected target, if we have one
        targetAccess = 0
        if lastClickedAvId and lastClickedToon:
            targetAccess = lastClickedToon.getAccessLevel()

        # Now that we have all the avIds of who we want to target with this Magic Word, let's run some sanity checks
        # First things first, let's make sure the invoker is allowed to target who they want to target
        for targetId in targetIds[:]:
            # Of course the invoker has access to target themselves
            if targetId == avId:
                continue
            # If our target DistributedObject doesn't exist anymore for whatever reason, just ignore them
            targetToon = self.air.doId2do.get(targetId)
            if not targetToon:
                continue
            # Get the Access Level of the target and round it to the nearest 100th
            # This kind of thing is useful for roles like BUILDER, that are technically higher than USER
            # They should have more perms than USERS, but shouldn't be allowed to target them
            targetAccess = int(round(targetToon.getAccessLevel(), -2))
            # If the Access Level of the target is greater than or equal to than that of the invoker, remove them
            # However, make an exemption if the Magic Word has anyTarget set to true
            if targetAccess >= invokerAccess and not magicWordInfo['anyTarget']:
                targetIds.remove(targetId)
                continue
            # However, we need to make an exception here for the two Access Levels below USER
            # Users shouldn't really be able to target others no matter what, so lets turn them away
            if invokerAccess <= ToontownGlobals.AccessLevelName2Int.get('NO_ACCESS'):
                targetIds.remove(targetId)
                continue

        # If, after the previous check, we don't have any more targets, let's inform the invoker about it
        if len(targetIds) == 0:
            # If affectType is NORMAL, let the invoker know what their Access Level is compared to their target
            if (affectRange in (AFFECT_OTHER, AFFECT_BOTH)) and affectType == AFFECT_NORMAL:
                # Create a nice little message to tell the invoker the difference between the Access Levels
                returnValue = MAGIC_WORD_RESPONSES.get("NoAccessSingleTarget")
                returnValue = returnValue.format(lastClickedToon.getName(), targetAccess, invokerAccess)
                self.generateResponse(avId=avId, responseType="Success", returnValue=returnValue)
            # Otherwise, just let the invoker know that everyone who was targeted was not allowed to be
            else:
                self.generateResponse(avId=avId, responseType="NoAccessToTarget")
            return

        # We're finally done determining everything related to the targets. Finally, let's get into the word itself
        # Make sure the invoker has a high enough Access Level to use this Magic Word in the first place
        # If they don't, them let them know about it
        if toon.getAccessLevel() < OTPGlobals.AccessLevelName2Int.get(magicWordInfo['access']):
            self.generateResponse(avId=avId, responseType="NoAccess")
            return

        # If the server is in legit mode, only allow the use of Administrative Commands
        # Let the invoker know if the Magic Word they're trying to use isn't administrative
        if self.air.legitMode:
            if not magicWordInfo['administrative']:
                self.generateResponse(avId=avId, responseType="LegitServer")
                return

        # If the affectRange circumstance made by the invoker is not allowed, let them know about it
        # This kind of thing is good to make sure that words that shouldn't really have a particular target don't end
        # up getting used in mass. For example, you don't want to use a word intended to kill a Cog Boss on other Toons
        if affectRange not in magicWordInfo['affectRange']:
            self.generateResponse(avId=avId, responseType="RestrictionOther")
            return

        # Get the arguments the Magic Word will accept
        commandArgs = magicWordInfo['args']

        # Determine the max and min amount of arguments the word will accept
        maxArgs = len(commandArgs)
        minArgs = 0
        argList = args.split(None, maxArgs-1)
        for argSet in commandArgs:
            isRequired = argSet[ARGUMENT_REQUIRED]
            if isRequired:
                minArgs += 1

        # If we have less arguments provided than are required, let the invoker know that
        messageData = "{} argument{}"
        if len(argList) < minArgs:
            messageData = messageData.format(minArgs, "s" if minArgs != 1 else '')
            self.generateResponse(avId=avId, responseType="NotEnoughArgs", extraMessageData=messageData)
            return
        # On the other hand, if we have more than what we need, tell them that instead
        elif len(argList) > maxArgs:
            messageData = messageData.format(maxArgs, "s" if maxArgs != 1 else '')
            self.generateResponse(avId=avId, responseType="TooManyArgs", extraMessageData=messageData)
            return

        # If we have less arguments provided than the max, use the defaults of the ones not provided
        if len(argList) < maxArgs:
            for x in range(minArgs, maxArgs):
                if commandArgs[x][ARGUMENT_REQUIRED] or len(argList) >= x + 1:
                    continue
                argList.append(commandArgs[x][ARGUMENT_DEFAULT])

        # Parse through all the args we had provided
        parsedArgList = []
        for x in range(len(argList)):
            arg = argList[x]
            if isinstance(arg, str):
                arg = arg.strip() # Strip trailing white space (happens if theres a space at the end of a cmd input)
            argType = commandArgs[x][ARGUMENT_TYPE]
            try:
                if argType == bool and isinstance(arg, str):
                    if arg.lower() in ['true', 'false']:
                        arg = arg.lower() == 'true'
                    else:
                        arg = int(arg)
                parsedArg = argType(arg)
            except:
                self.generateResponse(avId=avId, responseType="BadArgs")
                return

            parsedArgList.append(parsedArg)

        # If this Magic Word has a cooldown, let's handle that
        cooldown = magicWordInfo['cooldown']
        if cooldown and toon.getAccessLevel() < OTPGlobals.AccessLevelName2Int.get(ServerSettings.MagicWordCooldownBypassMinimumAccess.get()):
            cooldownName = magicWordInfo['classname'] + str(avId)

            # If this word is still on cooldown, let the invoker know
            if cooldownName in self.cooldown:
                self.generateResponse(avId=avId, responseType="Cooldown")
                return

            def cooldownMagicWord(name):
                if name in self.cooldown:
                    self.cooldown.remove(name)

            # Otherwise we're free to use it, just make sure to add it to the cooldown list
            self.cooldown.append(cooldownName)
            taskMgr.doMethodLater(cooldown, cooldownMagicWord, self.uniqueName(cooldownName), extraArgs=[cooldownName])

        # If this is a client-sided Magic Word, execute it on the client
        if magicWordInfo['execLocation'] == EXEC_LOC_CLIENT:
            # We are only allowed to target ourselves with client-sided Magic Words
            if len(targetIds) == 1 and avId in targetIds:
                self.sendClientCommand(avId, magicWord, magicWordInfo['classname'], targetIds=targetIds,
                                       parsedArgList=parsedArgList, affectRange=affectRange, affectType=affectType,
                                       affectExtra=affectExtra, lastClickedAvId=lastClickedAvId)
            else:
                self.generateResponse(avId=avId, responseType="CannotTarget")
                return
        # But if it's a server-sided one, execute it on the server
        else:
            # Find the class associated with our Magic Word and load it
            command = magicWordInfo['class']
            command.loadWord(self.air, None, avId, targetIds, parsedArgList)
            # Execute the Magic Word and grab a return value
            returnValue = command.executeWord()
            # If we have a return value, pass it over to the invoker
            # Otherwise, we give no response.
            if returnValue:
                self.generateResponse(avId=avId, responseType="Success", returnValue=returnValue)

    def generateResponse(self, avId, responseType="BadWord", magicWord='', parsedArgList=(), returnValue='',
                         affectRange=0, affectType=0, affectExtra=0, lastClickedAvId=0, extraMessageData=''):
        # Pack up the arg list so it's ready to ship to the client
        parsedArgList = json.dumps(parsedArgList)
        # Send the invoker a response to their use of the word
        self.sendUpdateToAvatarId(avId, 'generateResponse',
                                  [responseType, magicWord, parsedArgList, returnValue, affectRange, affectType,
                                   affectExtra, lastClickedAvId, extraMessageData])

    def sendClientCommand(self, avId, word, commandName, targetIds=(), parsedArgList=(), affectRange=0, affectType=0,
                          affectExtra=0, lastClickedAvId=0):
        # Pack up the arg list so it's ready to ship to the client
        parsedArgList = json.dumps(parsedArgList)
        # Execute the Magic Word on the client, because it's a client-sided Magic Word
        self.sendUpdateToAvatarId(avId, "executeMagicWord", [word, commandName, targetIds, parsedArgList, affectRange,
                                                             affectType, affectExtra, lastClickedAvId])

    def generateLogFile(self):
        # Generate a log file if Magic Word logging is enabled
        if not os.path.isfile(getFullFileName()):
            with open(getFullFileName(), 'w+') as file:
                logData = {}
                json.dump(logData, file, indent=4, default=str)
                file.close()

    def logMagicWord(self, log):
        # Increase the amount of words by 1
        self.loggedWords += 1

        # Open the file for write
        with open(getFullFileName(), 'r') as file:
            logData = json.load(file)
            file.close()

        # Add our logged Magic Word to the dictonary
        logData[self.loggedWords] = log

        # Write to the file
        with open(getFullFileName(), 'w') as file:
            data = json.dumps(logData, indent=4, default=str)
            file.write(data)

    def getLoggedWords(self):
        return self.loggedWords

    def detectBotCommands(self, task):
        with open('config/bot.json') as data:
            queuedCommands = json.load(data)

        if queuedCommands:
            commands = (queuedCommands.keys())
            for command in commands:
                arg = queuedCommands.get(command)
                self.runBotCommand(command, arg)

            queuedCommands = {}

            with open('config/bot.json', 'w') as data:
                json.dump(queuedCommands, data, indent=4)

            del queuedCommands
        else:
            del queuedCommands

        return task.again

    def detectWebCommands(self, task):
        with open('config/online_players.json', 'w') as data:
            players: List[Dict[str, Union[int, str]]] = []
            for doId, do in list(self.air.doId2do.items()):
                if isinstance(do, DistributedPlayerAI) and do.isPlayerControlled() and not do.isTemporaryToon():
                    players.append(
                            {
                                "DoId": do.getDoId(),
                                "ToonName": do.getName(),
                                "AccountId": do.DISLid,
                                "AccessLevel": do.getAccessLevel(),
                                "ZoneId": do.zoneId,

                            }
                    )
            json.dump(players, data)
        rewriteWeb = False
        with open('config/web_commands.json', 'r') as web_data:
            try:
                commands = json.load(web_data)

                if commands:
                    command: Dict[str, Union[str, Dict[Union[str, int]]]]
                    for command in commands:
                        commandName = command['Command']
                        args = command['Args']
                        self.notify.info(f'COMMAND {commandName} REQUESTED WITH {args}')
                        self.runWebCommand(commandName, args)

                        rewriteWeb = True
            except JSONDecodeError:
                rewriteWeb = True
                return task.again
        if rewriteWeb:
            with open('config/web_commands.json', 'w') as web_2:
                web_2.write('[]')

        return task.again

    def runWebCommand(self, command: str, args: []):
        if command not in ('Announce', 'System'):
            toon: DistributedToonAI = self.air.doId2do.get(args['DoId'])
            if not toon:
                return
        if command == 'Kick':
            toon.sendSetKick(reason=args['Reason'], target=toon, silent=3)
            self.air.logEvent(3, 9999, 'WEBPANELUSER', 0, f'kick {args["Reason"]}', target = args["DoId"])
        elif command == 'Ban':
            toon.sendSetBan(reason = args['Reason'], target = toon, invoker = None, minutes = args['Minutes'])
            self.air.logEvent(3, 9999, 'WEBPANELUSER', 0, f'ban {args["Minutes"]} {args["Reason"]}', target = args["DoId"])
        elif command == 'Whisper':
            toon.d_setSystemMessage(0, args['Message'], WhisperPopup.WTSystem)
            self.air.logEvent(2, 9999, 'WEBPANELUSER', 0, args['Message'], target = args["DoId"])
        elif command == 'Announce':
            self.air.logEvent(3, 9999, 'WEBPANELUSER', 0, f"announce {args['Message']}")
            for doId, do in list(self.air.doId2do.items()):
                if isinstance(do, DistributedPlayerAI):
                    if str(doId)[0] != str(self.air.districtId)[0]:
                        do.d_setSystemMessage(
                            0,
                            TTLocalizer.SystemMessagePrefix.format(args['Message']),
                            WhisperPopup.WTAnnouncement)
        elif command == 'System':
            self.air.logEvent(3, 9999, 'WEBPANELUSER', 0, f"system {args['Message']}")
            for doId, do in list(self.air.doId2do.items()):
                if isinstance(do, DistributedPlayerAI):
                    if str(doId)[0] != str(self.air.districtId)[0]:
                        do.d_setSystemMessage(
                            0,
                            TTLocalizer.ToonHQMessagePrefix + args['Message'],
                            WhisperPopup.WTSystem)

    def runBotCommand(self, command, arg):
        command = command.lower()

        self.air.logEvent(3, 8888, 'BOTCOMMAND', 0, f"{command} {arg}")

        # Announce and system commands
        if command in ('announce', 'broadcast', 'system'):
            for doId, do in list(self.air.doId2do.items()):
                if isinstance(do, DistributedPlayerAI):
                    if str(doId)[0] != str(self.air.districtId)[0]:
                        if command in ('announce', 'broadcast'):
                            announcementType = WhisperPopup.WTAnnouncement
                        else:
                            announcementType = WhisperPopup.WTSystem
                        do.d_setSystemMessage(0, TTLocalizer.SystemMessagePrefix.format(arg), announcementType)

        elif command in ('setholiday', 'startholiday', 'holiday', 'endholiday'):
            try:
                holidayId = int(arg)
            except:
                return

            if not hasattr(self.air, 'holidayManager'):
                return
            if self.air.holidayManager.isHolidayRunning(holidayId):
                return

            if command == 'endholiday':
                self.air.holidayManager.endHoliday(holidayId)
            else:
                self.air.holidayManager.startHoliday(holidayId)

        elif command == 'snap':
            for do in list(self.air.doId2do.values()):
                if isinstance(do, DistributedPlayerAI) and do.isPlayerControlled():
                    if random.random() < 0.5:
                        do.d_generateSnapEffect()

        elif command in ('banid', 'kickid'):
            try:
                toonId = int(arg)
            except:
                return

            toon = self.air.doId2do.get(toonId)
            if not toon:
                return

            if command == 'banid':
                toon.sendSetBan(reason='', target=toon, invoker=None, minutes=0)
            else:
                toon.sendSetKick(reason='', target=toon, silent=3)

        elif command in ('update', 'maintenance'):
            try:
                duration = int(arg)
            except:
                return

            if command == 'update':
                reasonType = TTLocalizer.ServerShutdownUpdate
            else:
                reasonType = TTLocalizer.ServerShutdownMaintenance

            reason = TTLocalizer.ServerShutdownMessage % reasonType
            self.air.announceMaintenance(reason, reasonType, duration)
