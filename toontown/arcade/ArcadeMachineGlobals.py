from enum import IntEnum


class RequestPlayResponses(IntEnum):
    SOMEONE_ELSE_PLAYING = 0
    START_PLAYING = 1
    STOP_PLAYING = 2
