
from enum import Enum
from typing import TYPE_CHECKING, Dict, List, Protocol, Literal, TypedDict

from discord import Member

if TYPE_CHECKING:
    from ..chat import *

class DGChatTypesEnum(Enum):
    """Enums for chat types (text or voice)"""
    TEXT = 1
    VOICE = 2
    
    def __int__(self) -> int:
        return self.value

class ImageEngines(Enum):
    DALL_E_2 = "dall-e-2"
    DALL_E_3 = "dall-e-3"
    
    def __str__(self) -> str:
        return self.value

class HasMember(Protocol):
    member: Member

class AIInteraction(TypedDict):
    role: str
    content: str
    
type Empty = None

type ImageEngine = Literal["dall-e-2", "dall-e-3"]
type Resolution = Literal["256x256", "512x512", "1024x1024"]
type AIModels = Literal["gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-4", "chat-bison@002"]
