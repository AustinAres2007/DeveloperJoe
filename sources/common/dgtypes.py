"""Types that DeveloperJoe uses."""

from __future__ import annotations
from typing import Any, overload
import discord, typing

from .. import (
    chat,
    models
)

if typing.TYPE_CHECKING:
    from joe import DeveloperJoe
    
__all__ = [
    "InteractableChannel",
    "DGChatType",
    "GPTModelType"
]

# Channels

InteractableChannel = discord.TextChannel | discord.Thread

# Chats

DGChatType = chat.DGTextChat | chat.DGVoiceChat

# GPT Models

GPTModelType = typing.Type[models.GPT3Turbo | models.GPT4]