from __future__ import annotations
import os
import discord as _discord, httpx as _httpx
from typing import Any as _Any, Union as _Union

from . import errors
from .common.developerconfig import ALLOW_TRACEBACK

# Models

class DGException(Exception):
    reply = None
    def __init__(self, message: str, *args, log_error: _Union[bool, None]=None, send_exceptions: bool=True, **kwargs):
        """Base exception for all DGE exceptions. (All DGE exceptions inherit from DGException, and must do if they want to be recognised by error handler)"""

        self._message = message
        self._log_error = log_error if isinstance(log_error, bool) else ALLOW_TRACEBACK
        self._send_exception = send_exceptions
        
        super().__init__(*args, **kwargs)
    
    @property
    def message(self) -> str:
        return self._message

    @property
    def log_error(self) -> bool:
        return self._log_error

    @property
    def send_exception(self) -> bool:
        return self._send_exception

class ModelNotExist(DGException):
    reply = errors.ModelErrors.MODEL_NOT_IN_DATABASE
    def __init__(self, guild: _Union[_discord.Guild, None], model: str, *args):
        """Will be raised if a model does not exist within a lock list."""
        super().__init__(self.reply.format(model, guild), guild, model, *args)

class GuildNotExist(DGException):
    reply = errors.ModelErrors.GUILD_NOT_IN_DATABASE
    def __init__(self, guild: _Union[_discord.Guild, int], *args):
        """Will be raised if a guild does not exist within the model lock list or configuration database."""
        super().__init__(self.reply.format(guild), guild, log_error=True, *args)
        
class GuildExistsError(DGException):
    reply = errors.ModelErrors.GUILD_IN_MODEL_DATABASE
    def __init__(self, guild: _discord.Guild, *args):
        super().__init__(self.reply, guild, *args)

class UserNotAMember(DGException):
    reply = errors.UserErrors.INCORRECT_USER_TYPE
    def __init__(self, user: _discord.User, guild: _discord.Guild, *args):
        """Will be raised if a user was once part of a guild, but no longer."""
        super().__init__(self.reply.format(user, guild.name), user, guild, *args)

class UserDoesNotHaveChat(DGException):
    reply = errors.ConversationErrors.NO_CONVO
    def __init__(self, name: _Union[str, None], *args):
        """Will be raised if the user specifies a chat that doesn't exist."""
        super().__init__(self.reply, name, *args)

class UserDoesNotHaveVoiceChat(DGException):
    reply = errors.VoiceConversationErrors.NO_VOICE_CONVO
    def __init__(self, name: str | None):
        super().__init__(self.reply, name)
        
class UserDoesNotHaveAnyChats(DGException):
    reply = errors.ConversationErrors.NO_CONVOS
    def __init__(self):
        super().__init__(self.reply)
        
class CannotDeleteThread(DGException):
    reply = errors.ConversationErrors.CANNOT_STOP_IN_CHANNEL
    def __init__(self, thread: _discord.Thread, *args):
        """Will be raised if the user tries to stop a chat in the thread that was created by said chat."""
        super().__init__(self.reply.format(thread), thread, *args)

class IncorrectInteractionSetting(DGException):
    reply = errors.ConversationErrors.CONVO_CANNOT_TALK
    def __init__(self, incorrect_object: _Any, correct_object: _Any, *args):
        """Will be raised if a user tries to send a command in wrong conditions"""
        super().__init__(self.reply, incorrect_object, correct_object, *args)

class GPTReplyError(DGException):
    reply = errors.GptErrors.GPT_PORTAL_ERROR
    def __init__(self, server_reply: _Union[_httpx.Response, _Any], *args):
        """Will be raised if an OpenAI error occurs."""
        super().__init__(self.reply, server_reply, log_error=True, *args)

class GPTContentFilter(DGException):
    reply = errors.GptErrors.GPT_CONTENT_FILTER
    def __init__(self, query: str, *args):
        """Raised when the user asks illegal questions. (Retaining to pornography or anything of the sort)"""
        super().__init__(self.reply, query, *args)

class ChatIsDisabledError(DGException):
    reply = errors.ConversationErrors.CONVO_CLOSED
    def __init__(self, chat, *args):
        """Will be raised if the users chat has been disabled for any reason."""
        super().__init__(self.reply, chat, *args)

class ModelIsLockedError(DGException):
    reply = errors.ModelErrors.MODEL_LOCKED
    def __init__(self, model: str, *args):
        """Will be raised if a user does not have access to a model they want to use."""
        super().__init__(self.reply, model, log_error=True, send_exceptions=True, *args)

class VoiceIsLockedError(DGException):
    reply = errors.VoiceConversationErrors.VOICE_IS_LOCKED
    def __init__(self):
        super().__init__(self.reply)
        
class GPTReachedLimit(DGException):
    reply = errors.ConversationErrors.CONVO_TOKEN_LIMIT
    def __init__(self, *args):
        """Will be raised when a chat has reached its token limit."""
        super().__init__(self.reply, *args)

class InvalidHistoryID(DGException):
    reply = errors.HistoryErrors.INVALID_HISTORY_ID
    def __init__(self, _id: str, *args):
        "Will be raised when a given history ID does not follow the history ID format (?)"
        super().__init__(self.reply, _id, log_error=True, *args)

class HistoryNotExist(DGException):
    reply = errors.HistoryErrors.HISTORY_DOESNT_EXIST
    def __init__(self, _id: str, *args):
        """Will be raised when a given history ID does not exist within the database."""
        super().__init__(self.reply, _id, *args)

class InvalidHistoryOwner(DGException):
    reply = errors.HistoryErrors.HISTORY_NOT_USERS
    def __init__(self, _id: str):
        """Will be raised when a user other than the owner of a private chat requests the transcript."""
        super().__init__(self.reply, _id)
        
class ChatChannelDoesntExist(DGException):
    reply = errors.ConversationErrors.CHANNEL_DOESNT_EXIST
    def __init__(self, message: _discord.Message, conversation: str | None):
        """Will be raised when a channel from a discord guild no longer exists (reletive to the bot, this could mean the bot was kicked / banned)"""
        super().__init__(self.reply.format(message, message.guild, conversation, conversation), message, conversation, log_error=True, send_exceptions=False)

class DGNotTalking(DGException):
    reply = errors.VoiceConversationErrors.NOT_SPEAKING
    def __init__(self, voice_channel: _discord.VoiceChannel):
        """Will be raised when the bot is supposed to be talking, but isn't."""
        super().__init__(self.reply, voice_channel)

class DGIsListening(DGException):
    reply = errors.VoiceConversationErrors.IS_LISTENING
    def __init__(self):
        super().__init__(self.reply)

class DGNotListening(DGException):
    reply = errors.VoiceConversationErrors.NOT_LISTENING
    def __init__(self):
        super().__init__(self.reply)
        
class DGNotInVoiceChat(DGException):
    reply = errors.VoiceConversationErrors.NOT_IN_CHANNEL
    def __init__(self, voice_channel: _discord.VoiceChannel):
        """Will be raised when the bot is not in a voice chat."""
        super().__init__(self.reply, voice_channel)

class UserNotInVoiceChannel(DGException):
    reply = errors.VoiceConversationErrors.USER_NOT_IN_CHANNEL
    def __init__(self, supposed_voice_channel: _discord.VoiceChannel | _Any):
        """Will be raised when a user is not in a voice chat."""
        super().__init__(self.reply, supposed_voice_channel)
    
class DGIsTalking(DGException):
    reply = errors.VoiceConversationErrors.IS_SPEAKING
    def __init__(self, conversation: str | None):
        """Will be raised when the bot not supposed talking, but is."""
        super().__init__(self.reply, conversation)

class ChatIsTextOnly(DGException):
    reply = errors.VoiceConversationErrors.TEXT_ONLY_CHAT
    def __init__(self, conversation: str | None):
        """Will be raised when a chat is text only."""
        super().__init__(self.reply, conversation)

class VoiceNotEnabled(DGException):
    reply = errors.VoiceConversationErrors.NO_VOICE
    def __init__(self, ffmpeg_status):
        """Will be raised when a user tries to use a voice feature when it is not installed."""
        super().__init__(self.reply, ffmpeg_status)

class CannotTalkInChannel(DGException):
    reply = errors.ConversationErrors.CANNOT_CONVO
    def __init__(self, channel_type: _Any):
        """Will be raised when a user is trying to talk in an enviroment where the bot cannot talk."""
        super().__init__(self.reply, channel_type)
    
class ConfigKeyError(DGException):
    reply = errors.GenericErrors.CONFIG_NO_ENTRY
    def __init__(self, missing_key: str):
        """Will be raised when a config key has been specified, but does not exist."""
        super().__init__(self.reply, missing_key)

class GPTTimeoutError(DGException):
    reply = errors.GptErrors.GPT_TIMEOUT_ERROR
    def __init__(self):
        """Will be raised when a query was given to DG, but the request timed out."""
        super().__init__(self.reply)

class MissingPermissions(DGException):
    reply = errors.GenericErrors.USER_MISSING_PERMISSIONS
    def __init__(self, user: _discord.User | _discord.Member):
        super().__init__(self.reply, user)