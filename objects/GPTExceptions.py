import discord

# Models

class ModelNotExist(Exception):
    def __init__(self, guild: discord.Guild, model: str):
        super().__init__(f"{model} model lock list does not exist within {guild.name} database.", guild, model)

class GuildNotExist(Exception):
    def __init__(self, guild: discord.Guild):
        super().__init__(f"{guild.name} does not exist within database.", guild)
        
class ModelGuildError(Exception):
    ...

class NotAMember(Exception):
    def __init__(self, user: discord.User, guild: discord.Guild):
        super().__init__(f"{user} is not a member of {guild.name}.", user, guild)

class CannotDeleteThread(Exception):
    def __init__(self, thread: discord.Thread):
        super().__init__(f"You cannot do /stop in the thread created by your conversation ({thread.name})", thread)