"""Utils that commands use."""

from __future__ import annotations
import discord, io, typing

from .. import (
    chat,
    exceptions,
    config
)
from .dgtypes import (
    DGChatType, 
    GPTModelType,
    AllChannels,
    InteractableChannel
)

if typing.TYPE_CHECKING:
   ...

__all__ = [
    "is_voice_conversation",
    "to_file",
    "to_file_fp",
    "assure_class_is_value",
    "get_modeltype_from_name",
    "in_correct_channel"
]

def to_file_fp(fp: str) -> discord.File:
    """Get `File` object from a filepath.

    Args:
        fp (str): Path of the file (aka a filepath lol)

    Returns:
        _File: The object made from the filepath.
    """
    return discord.File(fp)

def to_file(content: str, name: str) -> discord.File:
    """From `str` to `discord.File`"""
    f = io.BytesIO(content.encode())
    f.name = name
    return discord.File(f)

def is_voice_conversation(conversation: DGChatType | None) -> chat.DGVoiceChat:
    if isinstance(conversation, chat.DGVoiceChat):
        return conversation
    raise exceptions.UserDoesNotHaveChat(str(conversation))

def assure_class_is_value(object, __type: type):
    """For internal use. Exact same as `isinstance` but raises `IncorrectInteractionSetting` if the result is `False`."""
    if type(object) == __type:
        return object
    raise exceptions.IncorrectInteractionSetting(object, type)

def get_modeltype_from_name(name: str) -> GPTModelType:
        """Get GPT Model from actual model name. (Get `models.GPT4` from entering `gpt-4`)"""
        if name in list(config.REGISTERED_MODELS):
            return config.REGISTERED_MODELS[name]
        raise exceptions.ModelNotExist(None, name)

def in_correct_channel(interaction: discord.Interaction) -> bool:
    return bool(interaction.channel) == True and bool(interaction.channel.guild if interaction.channel else False)

def get_correct_channel(channel:  AllChannels | None) -> InteractableChannel:
    if channel and isinstance(channel, InteractableChannel):
        return channel
    raise exceptions.CannotTalkInChannel(channel)