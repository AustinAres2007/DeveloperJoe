
from enum import Enum

class ChatFunctions(Enum):
    TEXT = 1
    VOICE = 2
    LISTEN = 3
    
    def __int__(self) -> int:
        return self.value

class DGChatTypesEnum(Enum):
    """Enums for chat types (text or voice)"""
    TEXT = 1
    VOICE = 2
    
    def __int__(self) -> int:
        return self.value
    
