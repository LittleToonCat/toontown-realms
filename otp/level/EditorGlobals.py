from panda3d.core import ConfigVariableList

EditTargetPostName = 'inGameEditTarget'
EntIdRange = 10000

# If multiple people want to edit a level at once, they should all put some alias if they don't want others
# touching their stuff
username2entIdBase = {}
# This allows all usernames to be defined from config rather than defined here
editUsernames = ConfigVariableList('level-edit-username')
for i in range(len(editUsernames)):
    username2entIdBase[editUsernames.getStringValue(i)] = (i + 1) * EntIdRange
usernameConfigVar = 'local-level-edit-username'
undefinedUsername = 'UNDEFINED_USERNAME'
editUsername = config.GetString(usernameConfigVar, undefinedUsername)


def checkNotReadyToEdit():
    if editUsername == undefinedUsername:
        return "you must config '%s'; see %s.py" % (usernameConfigVar, __name__)
    if editUsername not in username2entIdBase:
        return "unknown editor username '%s'; see %s.py" % (editUsername, __name__)
    return None


def assertReadyToEdit():
    msg = checkNotReadyToEdit()
    if msg is not None:
        pass
    return


def getEditUsername():
    return editUsername


def getEntIdAllocRange():
    baseId = username2entIdBase[editUsername]
    return [baseId, baseId + EntIdRange]
