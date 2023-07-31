import discord, httpx
from typing import Any, Union

# Models

class DGException(Exception):
    def __init__(self, message: str, *args, **kwargs):
        self.message = message
        super().__init__(*args, **kwargs)
    
class ModelNotExist(DGException):
    def __init__(self, guild: discord.Guild, model: str):
        """Will be raised if a model does not exist within a lock list."""
        super().__init__(f"{model} model lock list does not exist within {guild.name} database.", guild, model)

class GuildNotExist(DGException):
    def __init__(self, guild: discord.Guild):
        """Will be raised if a guild does not exist within the model lock list database"""
        super().__init__(f"{guild.name} does not exist within database.", guild)
        
class GuildExistsError(DGException):
    def __init__(self, guild: discord.Guild):
        super().__init__("Guild with specified ID has already been registered.", guild)

class UserNotAMember(DGException):
    def __init__(self, user: discord.User, guild: discord.Guild):
        """Will be raised if a user was once part of a guild, but no longer."""
        super().__init__(f"{user} is not a member of {guild.name}.", user, guild)

class CannotDeleteThread(DGException):
    def __init__(self, thread: discord.Thread):
        """Will be raised if the user tries to stop a chat in the thread that was created by said chat."""
        super().__init__(f"You cannot do /stop in the thread created by your conversation ({thread.name})", thread)

class IncorrectInteractionSetting(DGException):
    def __init__(self, incorrect_object: Any, correct_object: Any):
        """Will be raised if a user tries to send a command in wrong conditions"""
        super().__init__(f"We cannot interact here. You must be in a discord server channel to make commands. (No stages, private direct messages)", incorrect_object, correct_object)

class GPTReplyError(DGException):
    def __init__(self, reply: Union[httpx.Response, Any]):
        super().__init__(f"Invalid command from OpenAI Gateway server.", reply)
