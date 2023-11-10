"""Decorator Utilities that DG Uses."""
from __future__ import annotations
import discord, typing

from .. import (
    exceptions,
    voice,
    errors
)

if typing.TYPE_CHECKING:
    from joe import DeveloperJoe
    
def check_enabled(func):
    """Decorator for checking if a conversation is enabled. If not, an `ChatIsDiabledError` will be raised. If making a custom method, this decorator MUST come first.

    Args:
        func (_type_): The function.
    """
    async def _inner(self, *args, **kwargs):
        if self.is_active:
            return await func(self, *args, **kwargs)
        raise exceptions.ChatIsDisabledError(self)
    return _inner

def has_voice(func):
    """Decorator for checking if a user is connect to voice. Only to be used within `sources.chat.DGVoiceChat` instances.

    Args:
        func (_type_): The function.
    """
    async def _inner(self, *args, **kwargs):
        if self.voice:
            return await func(self, *args, **kwargs)
    return _inner

def dg_in_voice_channel(func):
    """Decorator for checking if the bot is in a voice channel with you."""
    
    async def _inner(self, *args, **kwargs):
        if isinstance(self.client_voice, voice.VoiceRecvClient) and self.client_voice.is_connected():
            return await func(self, *args, **kwargs)
        raise exceptions.DGNotInVoiceChat(self.voice)
    
    return _inner

def has_voice_with_error(func):
    """Decorator for checking if a user is connect to voice. Will raise `ERROR` if the check fails. Only to be used within `sources.chat.DGVoiceChat` instances.

    Args:
        func (_type_): The function.
    """
    async def _inner(self, *args, **kwargs):
        if self.voice:
            return await func(self, *args, **kwargs)
        raise exceptions.UserNotInVoiceChannel(self.voice)
    return _inner

def dg_is_speaking(func):
    """Decorator for checking if the bot instance is talking in the users channel.

    Args:
        func (_type_): The function.
    """
    async def _inner(self, *args, **kwargs):
        if self.is_speaking:
            return await func(self, *args, **kwargs)
        raise exceptions.DGNotTalking(self.voice)
    
    return _inner

def dg_isnt_speaking(func):
    """Decorator for checking if the bot instance is in the users channel, but not speaking.

    Args:
        func (_type_): The function.
    """
    async def _inner(self, *args, **kwargs):
        if self.client_voice and (self.client_voice.is_paused() or not self.client_voice.is_playing()):
            return await func(self, *args, **kwargs)
        raise exceptions.DGIsTalking(self.voice)

    return _inner

def dg_is_listening(func):
    """Decorator for checking if the bot instance is listening to voice chat.

    Args:
        func (_type_): The function.
    """
    async def _inner(self, *args, **kwargs):
        if self.client_voice.is_listening():
            return await func(self, *args, **kwargs)
        raise exceptions.DGNotListening()
    return _inner

def dg_isnt_listening(func):
    """Decorator for checking if the bot instance is not listening to voice chat.

    Args:
        func (_type_): The function.
    """
    async def _inner(self, *args, **kwargs):
        if not self.client_voice.is_listening():
            return await func(self, *args, **kwargs)
        raise exceptions.DGIsListening()
    return _inner

# Config Decorators

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

# DeveloperJoe Class Decorators

def _is_joe_class(func: typing.Callable):
    def _self_wrapper(self: DeveloperJoe, *args, **kwargs):
        from joe import DeveloperJoe
        if isinstance(self, DeveloperJoe):
            return func(self, *args, **kwargs)
        raise TypeError(f"self should be DeveloperJoe bot type, not {self.__class__.__name__}")
    
    return _self_wrapper

def user_exists(func):
    """Decorator for checking if a member exists withint the global chat index.

    Args:
        func (_type_): The non-awaitable function with self and member parameter.
    """
    
    @_is_joe_class
    def _member_wrapper(self, member: discord.Member, *args, **kwargs):
        if member.id in list(self.chats):
            return func(self, member, *args, **kwargs)
        
        self.chats[member.id] = {}
        return func(self, member)
    
    return _member_wrapper

def user_has_chat(func):
    
    @user_exists
    def _member_wrapper(self: DeveloperJoe, member: discord.Member, chat_name: str, *args, **kwargs):
        chat_name = str(chat_name or self.get_default_conversation(member))
        if chat_name in list(self.chats[member.id]):
            return func(self, member, chat_name, *args, **kwargs)
        raise exceptions.UserDoesNotHaveChat(chat_name, member)
    
    return _member_wrapper

def chat_not_exist(func):
    
    @user_exists
    def _member_wrapper(self, member: discord.Member, name: str, *args, **kwargs):
        if name not in list(self.chats[member.id]):
            return func(self, member, name, *args, **kwargs)
        raise exceptions.DGException(errors.ConversationErrors.HAS_CONVO)
    
    return _member_wrapper
