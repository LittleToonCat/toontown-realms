from enum import IntEnum

class VisibilityTypes(IntEnum):
    INVISIBLE = 0
    ONLINE = 1
    # TODO: below need to implemented
    # SLEEPING implies that the avatar is asleep. This does not activate if the avatar is invisible. 
    SLEEPING = 2
    # IDLE is basically SLEEPING but forced by the user.
    IDLE = 3
    # DO_NOT_DISTURB indicates that you should not whisper or teleport to this user.
    DO_NOT_DISTURB = 4

class ELoginPopupTypes(IntEnum):
    EVERYONE = 0
    FRIENDS = 1
    NO_ONE = 2

class ETeleportRequestTypes(IntEnum):
    EVERYONE = 0
    FRIENDS = 1
    NO_ONE = 2
    # TODO: maybe in the future, allow requests to be accepted/denyed
    #UPON_REQUEST = 3

class FriendRequestResponses(IntEnum):
    FAILURE = 0
    SUCCESS = 1
    SUCCESS_RECEIVER = 2
    REJECT = 3
    LOGGED_OUT = 4
    FAILURE_TUTORIAL = 5
    FAILURE_IGNORE = 6
    FAILURE_NOT_ACCEPTING = 7
    FAILURE_FRIENDS = 8

class CooldownReasons(IntEnum):
    NONE = 0
    REQUEST_PENDING = 1
    REQUEST_REJECTED = 2