import discord as _discord, httpx as _httpx
from typing import Any as _Any, Union as _Union
from .errors import *
from .models import *
from sources import chat
from .config import *

# Models

class DGException(Exception):
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
    reply = ModelErrors.MODEL_NOT_IN_DATABASE
    def __init__(self, guild: _Union[_discord.Guild, None], model: _Union[GPTModelType, str], *args):
        """Will be raised if a model does not exist within a lock list."""
        super().__init__(self.reply.format(model, guild), guild, model, *args)

class GuildNotExist(DGException):
    reply = ModelErrors.GUILD_NOT_IN_DATABASE
    def __init__(self, guild: _discord.Guild, *args):
        """Will be raised if a guild does not exist within the model lock list database"""
        super().__init__(self.reply.format(guild.name), guild, log_error=True, *args)
        
class GuildExistsError(DGException):
    reply = ModelErrors.GUILD_IN_MODEL_DATABASE
    def __init__(self, guild: _discord.Guild, *args):
        super().__init__(self.reply, guild, *args)

class UserNotAMember(DGException):
    reply = UserErrors.INCORRECT_USER_TYPE
    def __init__(self, user: _discord.User, guild: _discord.Guild, *args):
        """Will be raised if a user was once part of a guild, but no longer."""
        super().__init__(self.reply.format(user, guild.name), user, guild, *args)

class UserDoesNotHaveChat(DGException):
    reply = ConversationErrors.NO_CONVO
    def __init__(self, name: _Union[str, None], *args):
        """Will be raised if the user specifies a chat that doesn't exist."""
        super().__init__(self.reply, name, *args)

class CannotDeleteThread(DGException):
    reply = ConversationErrors.CANNOT_STOP_IN_CHANNEL
    def __init__(self, thread: _discord.Thread, *args):
        """Will be raised if the user tries to stop a chat in the thread that was created by said chat."""
        super().__init__(self.reply.format(thread), thread, *args)

class IncorrectInteractionSetting(DGException):
    reply = ConversationErrors.CONVO_CANNOT_TALK
    def __init__(self, incorrect_object: _Any, correct_object: _Any, *args):
        """Will be raised if a user tries to send a command in wrong conditions"""
        super().__init__(self.reply, incorrect_object, correct_object, *args)

class GPTReplyError(DGException):
    reply = GptErrors.GPT_PORTAL_ERROR
    def __init__(self, server_reply: _Union[_httpx.Response, _Any], *args):
        """Will be raised if an OpenAI error occurs."""
        super().__init__(self.reply, server_reply, log_error=True, *args)

class GPTContentFilter(DGException):
    reply = GptErrors.GPT_CONTENT_FILTER
    def __init__(self, query: str, *args):
        """Raised when the user asks illegal questions. (Retaining to pornography or anything of the sort)"""
        super().__init__(self.reply, query, *args)

class ChatIsDisabledError(DGException):
    reply = ConversationErrors.CONVO_CLOSED
    def __init__(self, chat, *args):
        """Will be raised if the users chat has been disabled for any reason."""
        super().__init__(self.reply, chat, *args)

class ModelIsLockedError(DGException):
    reply = ModelErrors.MODEL_LOCKED
    def __init__(self, model: GPTModelType, *args):
        """Will be raised if a user does not have access to a model they want to use."""
        super().__init__(self.reply, model, *args)

class GPTReachedLimit(DGException):
    reply = ConversationErrors.CONVO_TOKEN_LIMIT
    def __init__(self, *args):
        """Will be raised when a chat has reached its token limit."""
        super().__init__(self.reply, *args)

class InvalidHistoryID(DGException):
    reply = HistoryErrors.INVALID_HISTORY_ID
    def __init__(self, _id: str, *args):
        "Will be raised when a given history ID does not follow the history ID format (?)"
        super().__init__(self.reply, _id, log_error=True, *args)

class HistoryNotExist(DGException):
    reply = HistoryErrors.HISTORY_DOESNT_EXIST
    def __init__(self, _id: str, *args):
        """Will be raised when a given history ID does not exist within the database."""
        super().__init__(self.reply, _id, *args)

class ChatChannelDoesntExist(DGException):
    reply = ConversationErrors.CHANNEL_DOESNT_EXIST
    def __init__(self, message: _discord.Message, conversation: _Union[chat.DGChatType, None]):
        """Will be raised when a channel from a discord guild no longer exists (reletive to the bot, this could mean the bot was kicked / banned)"""
        super().__init__(self.reply.format(message, message.guild, conversation, conversation), message, conversation, log_error=True, send_exceptions=False)

class DGNotTalking(DGException):
    reply = VoiceConversationErrors.NOT_SPEAKING
    def __init__(self, voice_channel: _discord.VoiceChannel):
        super().__init__(self.reply, voice_channel)

class DGNotInVoiceChat(DGException):
    reply = VoiceConversationErrors.NOT_IN_CHANNEL
    def __init__(self, voice_channel: _discord.VoiceChannel):
        super().__init__(self.reply, voice_channel)

class UserNotInVoiceChannel(DGException):
    reply = VoiceConversationErrors.USER_NOT_IN_CHANNEL
    def __init__(self, supposed_voice_channel: _discord.VoiceChannel | _Any):
        super().__init__(self.reply, supposed_voice_channel)
    
class DGIsTalking(DGException):
    reply = VoiceConversationErrors.IS_SPEAKING
    def __init__(self, conversation: chat.DGChatType):
        super().__init__(self.reply, conversation)

class ChatIsTextOnly(DGException):
    reply = VoiceConversationErrors.TEXT_ONLY_CHAT
    def __init__(self, conversation: chat.DGChatType):
        super().__init__(self.reply, conversation)

class FFMPEGNotInstalled(DGException):
    reply = VoiceConversationErrors.NO_FFMPEG
    def __init__(self, ffmpeg_status):
        super().__init__(self.reply, ffmpeg_status)
        
class CoquiNotInstalled(DGException):
    reply = VoiceConversationErrors.NO_COQUI
    def __init__(self):
        super().__init__(self.reply)

class IsProcessingVoice(DGException):
    reply = VoiceConversationErrors.IS_PROCESSING_VOICE
    def __init__(self, conversation: chat.DGChatType):
        super().__init__(self.reply, conversation)