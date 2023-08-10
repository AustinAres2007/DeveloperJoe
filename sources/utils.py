"""General Utilities that DG Uses."""

import io as _io
from discord import File as _File
from . import config as _config, models as _models, exceptions as _exceptions

def to_file(content: str, name: str) -> _File:
        """From `str` to `discord.File`"""
        f = _io.BytesIO(content.encode())
        f.name = name
        return _File(f)

def get_modeltype_from_name(name: str) -> _models.GPTModelType:
        """Get GPT Model from actual model name. (Get `models.GPT4` from entering `gpt-4`)"""
        if name in list(_config.REGISTERED_MODELS):
            return _config.REGISTERED_MODELS[name]
        raise _exceptions.ModelNotExist(None, name)

def assure_class_is_value(object, __type: type):
    """For internal use. Exact same as `isinstance` but raises `IncorrectInteractionSetting` if the result is `False`."""
    if type(object) == __type:
        return object
    raise _exceptions.IncorrectInteractionSetting(object, type)

def check_enabled(func):
    """Decorator for checking if a conversation is enabled. If not, an `ChatIsDiabledError` will be raised.

    Args:
        func (_type_): The function.
    """
    def _inner(self, *args, **kwargs):
        if self.is_active:
            print("CHAT CHECK")
            return func(self, *args, **kwargs)
        raise _exceptions.ChatIsDisabledError(self)
    return _inner

def dg_in_voice_channel(func):
    """Decorator for checking if the bot is in a voice channel with you."""
    
    def _inner(self, *args, **kwargs):
        print(self.client_voice)
        if self.client_voice:
            print("INVC CHECK")
            return func(self, *args, **kwargs)
        raise _exceptions.DGNotInVoiceChat(self.voice)
    
    return _inner

def has_voice(func):
    """Decorator for checking if a user is connect to voice. Only to be used within `sources.chat.DGVoiceChat` instances.

    Args:
        func (_type_): The function.
    """
    def _inner(self, *args, **kwargs):
        if self.voice:
            print("VC CHECK")
            return func(self, *args, **kwargs)
    return _inner

def has_voice_with_error(func):
    """Decorator for checking if a user is connect to voice. Will raise `ERROR` if the check fails. Only to be used within `sources.chat.DGVoiceChat` instances.

    Args:
        func (_type_): The function.
    """
    def _inner(self, *args, **kwargs):
        if self.voice:
            print("HVC CHECK")
            return func(self, *args, **kwargs)
        raise _exceptions.UserNotInVoiceChannel(self.voice)
    return _inner

def dg_is_speaking(func):
    """Decorator for checking if the bot instance is talking in the users channel.

    Args:
        func (_type_): The function.
    """
    def _inner(self, *args, **kwargs):
        if self.is_speaking:
            print("SPEAKING CHECK")
            return func(self, *args, **kwargs)
        raise _exceptions.DGNotTalking(self.voice)
    
    return _inner

def dg_isnt_speaking(func):
    """Decorator for checking if the bot instance is in the users channel, but not speaking.

    Args:
        func (_type_): The function.
    """
    def _inner(self, *args, **kwargs):
        print(self.client_voice, self.client_voice.is_paused())
        if self.client_voice and self.client_voice.is_paused():
            return func(self, *args, **kwargs)
        raise _exceptions.DGIsTalking(self.voice)

    return _inner

def dg_isnt_processing(func):
    """Decorator for checking if a conversation is processing a request.

    Args:
        func (_type_): The function.
    """
    def _inner(self, *args, **kwargs):
        print(self.is_processing)
        if not self.is_processing:
            return func(self, *args, **kwargs)
        raise _exceptions.IsProcessingVoice(self)

    return _inner