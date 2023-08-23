"""Decorator Utilities that DG Uses."""

from .. import (
    exceptions,
    voice
)

def check_enabled(func):
    """Decorator for checking if a conversation is enabled. If not, an `ChatIsDiabledError` will be raised. If making a custom method, this decorator MUST come first.

    Args:
        func (_type_): The function.
    """
    def _inner(self, *args, **kwargs):
        if self.is_active:
            return func(self, *args, **kwargs)
        raise exceptions.ChatIsDisabledError(self)
    return _inner

def dg_in_voice_channel(func):
    """Decorator for checking if the bot is in a voice channel with you."""
    
    def _inner(self, *args, **kwargs):
        if isinstance(self.client_voice, voice.VoiceRecvClient) and self.client_voice.is_connected():
            return func(self, *args, **kwargs)
        raise exceptions.DGNotInVoiceChat(self.voice)
    
    return _inner

def has_voice(func):
    """Decorator for checking if a user is connect to voice. Only to be used within `sources.chat.DGVoiceChat` instances.

    Args:
        func (_type_): The function.
    """
    def _inner(self, *args, **kwargs):
        if self.voice:
            return func(self, *args, **kwargs)
    return _inner

def has_voice_with_error(func):
    """Decorator for checking if a user is connect to voice. Will raise `ERROR` if the check fails. Only to be used within `sources.chat.DGVoiceChat` instances.

    Args:
        func (_type_): The function.
    """
    def _inner(self, *args, **kwargs):
        if self.voice:
            return func(self, *args, **kwargs)
        raise exceptions.UserNotInVoiceChannel(self.voice)
    return _inner

def dg_is_speaking(func):
    """Decorator for checking if the bot instance is talking in the users channel.

    Args:
        func (_type_): The function.
    """
    def _inner(self, *args, **kwargs):
        if self.is_speaking:
            return func(self, *args, **kwargs)
        raise exceptions.DGNotTalking(self.voice)
    
    return _inner

def dg_isnt_speaking(func):
    """Decorator for checking if the bot instance is in the users channel, but not speaking.

    Args:
        func (_type_): The function.
    """
    def _inner(self, *args, **kwargs):
        if self.client_voice and (self.client_voice.is_paused() or not self.client_voice.is_playing()):
            return func(self, *args, **kwargs)
        raise exceptions.DGIsTalking(self.voice)

    return _inner

def dg_is_listening(func):
    """Decorator for checking if the bot instance is listening to voice chat.

    Args:
        func (_type_): The function.
    """
    def _inner(self, *args, **kwargs):
        if self.client_voice.is_listening():
            return func(self, *args, **kwargs)
        raise exceptions.DGNotListening()
    return _inner

def dg_isnt_listening(func):
    """Decorator for checking if the bot instance is not listening to voice chat.

    Args:
        func (_type_): The function.
    """
    def _inner(self, *args, **kwargs):
        if not self.client_voice.is_listening():
            return func(self, *args, **kwargs)
        raise exceptions.DGIsListening()
    return _inner

def has_config(func):
    """Decorator for checking if a conversation is processing a request. (Not used currently)

    Args:
        func (_type_): The function.
    """
    def _inner(self, *args, **kwargs):
        if not self._manager.has_guild():
            self._manager.add_guild()
        return func(self, *args, **kwargs)

    return _inner

