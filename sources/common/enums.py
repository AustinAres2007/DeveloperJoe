
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..chat import *

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
    
type NoKey = None