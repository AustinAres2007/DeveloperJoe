import discord, httpx
from typing import Any, Union
from objects import GPTErrors

# Models

class DGException(Exception):
    def __init__(self, message: str, *args, log_error: bool=False, **kwargs):
        """Base exception for all DGE exceptions. (All DGE exceptions inherit from DGException, and must do if they want to be recognised by error handler)"""

        self._message = message
        self._log_error = log_error
        super().__init__(*args, **kwargs)
    
    @property
    def message(self) -> str:
        return self._message

    @property
    def log_error(self) -> bool:
        return self._log_error

class ModelNotExist(DGException):
    reply = GPTErrors.ModelErrors.MODEL_NOT_IN_DATABASE
    def __init__(self, guild: discord.Guild, model: str, *args):
        """Will be raised if a model does not exist within a lock list."""
        super().__init__(self.reply.format(model, guild.name), guild, model, *args)

class GuildNotExist(DGException):
    reply = GPTErrors.ModelErrors.GUILD_NOT_IN_DATABASE
    def __init__(self, guild: discord.Guild, *args):
        """Will be raised if a guild does not exist within the model lock list database"""
        super().__init__(self.reply.format(guild.name), guild, *args)
        
class GuildExistsError(DGException):
    reply = GPTErrors.ModelErrors.GUILD_IN_MODEL_DATABASE
    def __init__(self, guild: discord.Guild, *args):
        super().__init__(self.reply, guild, *args)

class UserNotAMember(DGException):
    reply = GPTErrors.UserErrors.INCORRECT_USER_TYPE
    def __init__(self, user: discord.User, guild: discord.Guild, *args):
        """Will be raised if a user was once part of a guild, but no longer."""
        super().__init__(self.reply.format(user, guild.name), user, guild, *args)

class UserDoesNotHaveChat(DGException):
    reply = GPTErrors.ConversationErrors.NO_CONVO
    def __init__(self, name: Union[str, None], *args):
        super().__init__(self.reply, name, *args)

class CannotDeleteThread(DGException):
    reply = GPTErrors.ConversationErrors.CANNOT_STOP_IN_CHANNEL
    def __init__(self, thread: discord.Thread, *args):
        """Will be raised if the user tries to stop a chat in the thread that was created by said chat."""
        super().__init__(self.reply.format(thread), thread, *args)

class IncorrectInteractionSetting(DGException):
    reply = GPTErrors.ConversationErrors.CONVO_CANNOT_TALK
    def __init__(self, incorrect_object: Any, correct_object: Any, *args):
        """Will be raised if a user tries to send a command in wrong conditions"""
        super().__init__(self.reply, incorrect_object, correct_object, *args)

class GPTReplyError(DGException):
    reply = GPTErrors.GptErrors.GPT_PORTAL_ERROR
    def __init__(self, server_reply: Union[httpx.Response, Any], *args):
        """Will be raised if an OpenAI error occurs."""
        super().__init__(self.reply, server_reply, log_error=True, *args)

class GPTContentFilter(DGException):
    reply = GPTErrors.GptErrors.GPT_CONTENT_FILTER
    def __init__(self, query: str, *args):
        """Raised when the user asks illegal questions. (Retaining to pornography or anything of the sort)"""
        super().__init__(self.reply, query, *args)

class ChatIsDisabledError(DGException):
    reply = GPTErrors.ConversationErrors.CONVO_CLOSED
    def __init__(self, chat, *args):
        """Will be raised if the users chat has been disabled for any reason."""
        super().__init__(self.reply, chat, *args)

class ModelIsLockedError(DGException):
    reply = GPTErrors.ModelErrors.MODEL_LOCKED
    def __init__(self, model: str, *args):
        """Will be raised if a user does not have access to a model they want to use."""
        super().__init__(self.reply, model, *args)

class GPTReachedLimit(DGException):
    reply = GPTErrors.ConversationErrors.CONVO_TOKEN_LIMIT
    def __init__(self, *args):
        """Will be raised when a chat has reached its token limit."""
        super().__init__(self.reply, *args)

class InvalidHistoryID(DGException):
    reply = GPTErrors.HistoryErrors.INVALID_HISTORY_ID
    def __init__(self, _id: str, *args):
        "Will be raised when a given history ID does not follow the history ID format (?)"
        super().__init__(self.reply, _id, log_error=True, *args)

class HistoryNotExist(DGException):
    reply = GPTErrors.HistoryErrors.HISTORY_DOESNT_EXIST
    def __init__(self, _id: str, *args):
        """Will be raised when a given history ID does not exist within the database."""
        super().__init__(self.reply, _id, *args)