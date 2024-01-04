from enum import StrEnum


class MessageTypeEnum(StrEnum):
    DISCONNECT = "DISCONNECT"
    CONNECT = "CONNECT"
    CURSOR = "CURSOR"
    ACKNOWLEDGE = "ACKNOWLEDGE"
    EXT_CHANGE = "EXT_CHANGE"
