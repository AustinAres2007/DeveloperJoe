"""Utils that commands use."""

from __future__ import annotations
from typing import Any

import discord, io, typing, yaml, os

from .. import (
    chat,
    exceptions,
    models
)
from . import (
    developerconfig,
    common_functions
)

__all__ = [
    "to_file",
    "to_file_fp",
    "is_voice_conversation",
    "is_correct_channel",
    "assure_class_is_value",
    "get_modeltype_from_name",
    "modeltype_is_in_models",
    "in_correct_channel",
    "get_correct_channel",
    "fix_config",
    "check_and_get_yaml"
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

def fix_config(error_message: str) -> dict[str, Any]:
    """Resets the bot-config.yaml file to the programmed default. This function also returns the default.

    Args:
        error_message (str): The warning about the failed configuration.

    Returns:
        dict[str, Any]: _description_ The default config.
    """
    common_functions.warn_for_error(error_message)
    with open(developerconfig.CONFIG_FILE, 'w+') as yaml_file_repair:
        yaml.safe_dump(developerconfig.default_config_keys, yaml_file_repair)
        return developerconfig.default_config_keys
                    
def check_and_get_yaml(yaml_file: str=developerconfig.CONFIG_FILE, check_against: dict=developerconfig.default_config_keys) -> dict[str, Any]:
    """Return the bot-config.yaml file as a dictionary.

    Returns:
        dict[str, Any]: The configuration. (Updated when this function is called)
    """
    if os.path.isfile(yaml_file):
        with open(yaml_file, 'r') as yaml_file_obj:
            try:
                config = yaml.safe_load(yaml_file_obj)

                for i1 in enumerate(dict(config).items()):
                    if (i1[1][0] not in list(check_against) or type(i1[1][1]) != type(check_against[i1[1][0]])):
                        return fix_config("Invalid Configuration Value Type. Default configuration will be used. Repairing...")
                else:
                    return config
            except (KeyError, IndexError):
                return fix_config(f"Invalid configuration key. Default configuration will be used. Repairing...")
    else:        
        return fix_config("Configuration file missing. Default configuration will be used. Repairing...")
    