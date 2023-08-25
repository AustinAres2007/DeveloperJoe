"""Types that DeveloperJoe uses."""

from __future__ import annotations
import discord, typing

from .. import (
    chat,
    models
)

__all__ = [
    "InteractableChannel",
    "DGChatType",
    "GPTModelType"
]

# Channels

InteractableChannel = discord.TextChannel | discord.Thread
AllChannels = discord.TextChannel | discord.Thread | discord.interactions.InteractionChannel
# Chats

DGChatType = chat.DGTextChat | chat.DGVoiceChat

# GPT Models

GPTModelType = typing.Type[models.GPT3Turbo | models.GPT4] 
