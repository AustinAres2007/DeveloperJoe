"""Utils that commands use."""

from __future__ import annotations
from warnings import warn
from typing import Any

import discord, io, typing, yaml, os

from .. import (
    chat,
    exceptions,
    models
)
from . import (
    developerconfig
)

__all__ = [
    "is_voice_conversation",
    "to_file",
    "to_file_fp",
    "assure_class_is_value",
    "get_modeltype_from_name",
    "in_correct_channel",
    "get_correct_channel"
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

def is_voice_conversation(conversation: chat.DGChatType | None) -> chat.DGVoiceChat:
    if isinstance(conversation, chat.DGVoiceChat):
        return conversation
    raise exceptions.UserDoesNotHaveChat(str(conversation))

def assure_class_is_value(object, __type: type):
    """For internal use. Exact same as `isinstance` but raises `IncorrectInteractionSetting` if the result is `False`."""
    if type(object) == __type:
        return object
    raise exceptions.IncorrectInteractionSetting(object, type)

def is_correct_channel(channel: typing.Any) -> developerconfig.InteractableChannel:
    if isinstance(channel, developerconfig.InteractableChannel):
        return channel
    raise exceptions.IncorrectInteractionSetting(channel, developerconfig.InteractableChannel)

def get_modeltype_from_name(name: str) -> models.GPTModelType:
    """Get GPT Model from actual model name. (Get `models.GPT4` from entering `gpt-4`)"""
    if name in list(models.registered_models):
        return models.registered_models[name]
    raise exceptions.DGException(f"Inconfigured GPT model setup. This is a fatal coding error and should be sorted as such. \n\n**Debug Information**\n\nFailed Model: {name}\nModel Map: {models.registered_models}\nName Parameter Type: {type(name)}")

def modeltype_is_in_models(name: str):
    return name in list(models.registered_models)

def in_correct_channel(interaction: discord.Interaction) -> bool:
    return bool(interaction.channel) == True and bool(interaction.channel.guild if interaction.channel else False)


def get_correct_channel(channel: typing.Any | None) -> developerconfig.InteractableChannel:
    if channel and isinstance(channel, developerconfig.InteractableChannel):
        return channel
    raise exceptions.CannotTalkInChannel(channel)

def fix_config(error_message: str):
    warn(error_message)
    with open(developerconfig.CONFIG_FILE, 'w+') as yaml_file_repair:
        yaml.safe_dump(developerconfig.default_config_keys, yaml_file_repair)
        return developerconfig.default_config_keys
                    
def check_config_yaml():
    if os.path.isfile(developerconfig.CONFIG_FILE):
        with open(developerconfig.CONFIG_FILE, 'r') as yaml_file:
            try:
                config = yaml.safe_load(yaml_file)
                for i1 in enumerate(dict(config).items()):
                    if (i1[1][0] not in list(developerconfig.default_config_keys) or type(i1[1][1]) != type(developerconfig.default_config_keys[i1[1][0]])):
                        return fix_config("Invalid Configuration Value Type. Default configuration will be used. Repairing...")
                else:
                    return config
            except (KeyError, IndexError):
                return fix_config(f"Invalid configuration key. Default configuration will be used. Repairing...")
    else:        
        return fix_config("Configuration file missing. Default configuration will be used. Repairing...")
                        
def get_config(key: str) -> Any:
    local_config = check_config_yaml()
    if key in local_config:
        return local_config.get(key)
    elif hasattr(developerconfig, key):
        return getattr(developerconfig, key)
    raise exceptions.ConfigKeyError(key)