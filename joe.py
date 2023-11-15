"""Main DeveloperJoe file.

Thank you to:
    - Fabian Kuzbiel (Tester, Support, Survey)
    - Bradley King (Tester)
    - Emie (Testing in early stages, Survey)
    
    - The Developers of Opus.
    - The Developers of FFmpeg.
"""

from __future__ import annotations
from asyncio import CancelledError
import sys, os

v_info = sys.version_info

if not (v_info.major >= 3 and v_info.minor >= 11):
    print(f'You must run this bot with Python 3.11 and above.\nYou are using Python {v_info.major}.{v_info.minor}\nYou may install python at "https://www.python.org/downloads/" and download the latest version.')
    exit(1)

try:
    # Not required here, just importing for integrity check.
    import json, openai, openai_async, tiktoken, sqlite3, math, wave, array, pytz, yaml, colorama

    import discord, logging, asyncio, datetime, traceback, aiohttp
    from discord.ext import commands
    from typing import Union
    
    from distutils.spawn import find_executable
    
except ImportError as e:
    print(f"Missing Imports, please execute `pip install -r dependencies/requirements.txt` to install required dependencies. (Actual Error: {e})")
    exit(1)

try:
    from sources.common import (
        commands_utils,
        decorators,
        developerconfig,
        common_functions,
        voice_checks
    )
    
    from sources import (
        chat,  
        database, 
        errors, 
        exceptions, 
        confighandler, 
        history, 
        modelhandler, 
        models, 
        ttsmodels, 
    )
    
    from sources.voice import pydub # type: ignore It does exist mate.
    
except IndexError as err:
    print(f"Missing critical files. Please redownload DeveloperJoe and try again. (Actual Error: {err})")
    exit(1)
    
# Configuration

try:
    with open(developerconfig.WELCOME_FILE, encoding="utf8") as welcome_file, open(developerconfig.ADMIN_FILE, encoding="utf8") as admin_file:
        WELCOME_TEXT = welcome_file.read()
        ADMIN_TEXT = admin_file.read()

except FileNotFoundError:
    common_functions.send_fatal_error_warning(f"Missing server join files. ({developerconfig.WELCOME_FILE} and {developerconfig.ADMIN_FILE})")

# Main Bot Class    

class OpusWarning(Warning):
    ...
    
class DeveloperJoe(commands.Bot):

    """Main DeveloperJoe Bot Instance"""

    INTENTS = discord.Intents.all()
    
    def __init__(self, *args, **kwargs):
        self.__keys__ = {}

        self.WELCOME_TEXT = WELCOME_TEXT.format(confighandler.get_config("bot_name"))
        self.ADMIN_TEXT = ADMIN_TEXT.format(confighandler.get_config("bot_name"))
        self.__tzs__ = pytz.all_timezones
        self.__tz__ = pytz.timezone(confighandler.get_config("timezone"))
        self.config = None
        
        super().__init__(*args, **kwargs)
    
    def get_uptime(self) -> datetime.timedelta:
        return (datetime.datetime.now(tz=self.__tz__) - self.start_time)
    
    @decorators.user_has_chat
    def get_user_conversation(self, member: discord.Member | discord.User, chat_name: str) -> chat.DGChatType | None:
        """ Get the specified members current chat.

        Args:
            member (discord.Member): The member of whoms chat will be returned.
            chat_name (Union[str, None], optional): The name of the chat. Defaults to None.

        Raises:
            UserDoesNotHaveChat: If the specified chat does not exist.

        Returns:
            Union[Union[DGTextChat, DGVoiceChat], None]: The chat, or None if chat_name is not specified.
        """
        return self.chats[member.id][chat_name]
    
    @decorators.user_exists
    def get_all_user_conversations(self, member: discord.Member) -> dict[str, chat.DGChatType]:
        """Get all of a specified members conversation(s)

        Args:
            member (discord.Member): The member of whoms chats will be returned.

        Returns:
            Union[dict[str, DGChatType], None]: A dictionary containing the name of the chat as the key, and the chat instance as the value.
        """
        return self.chats[member.id]
    
    def get_user_has_permission(self, member: discord.Member, model: models.GPTModelType) -> bool:
        """Return if the user has permission to user a model

        Args:
            member (Union[discord.Member, None]): The member to be checked
            model (GPTModelType): The model to try the user agaisnt.

        Returns:
            bool: True if the user has correct permissions, False if not.
        """
        if isinstance(member, discord.Member):
            with modelhandler.DGRules(member.guild) as check_rules:
                return bool(check_rules.user_has_model_permissions(member.roles[-1], model))
        else:
            raise TypeError("member must be discord.Member, not {}".format(member.__class__))
    
    @decorators.user_exists
    def get_default_conversation(self, member: discord.Member | discord.User) -> Union[chat.DGChatType, None]:
        """Get a users default conversation

        Args:
            member (discord.Member): Which member's default chat to obtain

        Returns:
            Union[DGChatType, None]: The default chat, or None if the user doesn't have one.
        """
        return self.default_chats[f"{member.id}-latest"]
    
    @decorators.user_exists
    def get_default_voice_conversation(self, member: discord.Member) -> chat.DGVoiceChat | None:
        """Returns a users default conversation only if it supports voice.

        Args:
            member (discord.Member): Which member's default chat to obtain

        Returns:
            Union[DGChatType, None]: The default voice chat, or None if the user doesn't have one or it is a text chat.
        """
        _chat = self.get_default_conversation(member)
        return _chat if isinstance(_chat, chat.DGVoiceChat) else None
    
    @decorators.user_has_chat
    def get_user_voice_conversation(self, member: discord.Member, chat_name: str) -> Union[chat.DGVoiceChat, None]:
        # TODO: Add funcion that aquires all voice chats only
        """Get a users chat, only if it supports voice.

        Args:
            member (discord.Member): The member that the chat will belong to.
            chat_name (_type_): The name of the chat.

        Returns:
            Union[DGVoiceChat, None]: The chat, or None if the chat doesn't exist, or does not support voice.
        """
        __chat__ = self.get_user_conversation(member, chat_name=chat_name)
        return __chat__ if isinstance(__chat__, chat.DGVoiceChat) else None
    
    @decorators.user_has_chat
    def delete_conversation(self, member: discord.Member, conversation_name: str) -> None:
        """Deletes a members chat.

        Args:
            member (discord.Member): The member that the chat belongs to.
            conversation_name (str): The name of the chat to be deleted.
        """
        del self.chats[member.id][conversation_name]

    @decorators.chat_not_exist
    def add_conversation(self, member: discord.Member | discord.User, name: str, conversation: chat.DGChatType) -> None:
        """Adds a conversation to a users chat database.

        Args:
            member (discord.Member): The member who owns the chat.
            name (str): Name of the chat
            conversation (DGChatType): Instance of the conversation.
        """
        self.chats[member.id][name] = conversation

    @decorators.user_has_chat
    def set_default_conversation(self, member: discord.Member | discord.User, name: str) -> None:
        """Sets a users default chat.

        Args:
            member (discord.Member): The member who's default chat will change.
            name (Union[None, str]): Name of the new chat.
        """
        self.default_chats[f"{member.id}-latest"] = self.get_user_conversation(member, name)
    
    def reset_default_conversation(self, member: discord.Member):
        """Sets a users default chat no `None`.

        Args:
            member (discord.Member): The member who's default chat will be set.
        """
        self.default_chats[f"{member.id}-lastest"] = None
        
    @decorators.user_has_chat
    def manage_defaults(self, member: discord.Member, name: str | None=None) -> chat.DGChatType:
        """Manages a users default chat depending on parameters given.

        Args:
            member (discord.Member): The member to modify default.
            name (Union[None, str]): Name of different chat.
            set_to_none (bool, optional): Weather the chat will be reset to None. Defaults to False.

        Returns:
            Union[str, None]: The name of the new chat, or None if the chat does not exist.
        """
        current_default = self.get_default_conversation(member)
        if isinstance(name, str) and name:
            names_convo = self.get_user_conversation(member, name)
            name_is_chat = isinstance(names_convo, chat.DGChatType)

            if name_is_chat:
                self.set_default_conversation(member, name)
                return names_convo
            elif current_default:
                return current_default
            else:
                raise exceptions.UserDoesNotHaveChat(member.name)
        else:
            if current_default:
                return current_default
            raise exceptions.UserDoesNotHaveChat(member.name)
        
    def get_member_conversation_bot_voice_instance(self, voice_channel: discord.VoiceChannel):
        return discord.utils.get(self.voice_clients, guild=voice_channel.guild)
    
    async def handle_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        """For internal use. Error handler for DG.

        Args:
            interaction (discord.Interaction): Interaction that caused the error.
            error (discord.app_commands.AppCommandError): The error.

        Returns:
            _type_: Any
        """
        error = getattr(error, "original", error)
        async def send_to_debug_channel(**kwargs):
            if confighandler.get_config("bug_report_channel") == None:
                return
            elif str(confighandler.get_config("bug_report_channel")).isdecimal():
                channel = self.get_channel(int(confighandler.get_config("bug_report_channel")))
                if channel:
                    return await channel.send(**kwargs) # type: ignore
                common_functions.warn_for_error("Bug report channel ID is invalid or it does not exist. (Error 1)")
            else:
                common_functions.warn_for_error("Bug report channel ID is invalid or it does not exist. (Error 0)")
                
        async def send(text: str):
            if interaction.response.is_done():
                return await interaction.followup.send(text)
            return await interaction.response.send_message(text)
        
        async def send_with_file(text: str, file: discord.File):
            if interaction.response.is_done():
                return await interaction.followup.send(text, file=file)
            return await interaction.response.send_message(text, file=file)
        
        exception: str = traceback.format_exc()
        
        # If it is a DGException or derives from it
        if message := getattr(error, "message", None):
            if (log := getattr(error, "log_error", None)) != None:
                if log == True:
                    logging.error(exception) 
                return await send(message) if getattr(error, "send_exception", False) == True else None
                
        
        if isinstance(error, discord.app_commands.CheckFailure):
            return await send("An error occured whilst trying to execute your command. This is likely because you are trying to execute a discord-server only command in direct messages.")
        
        logging.error(exception)
        error_text = f"From error handler: {str(error)}"
        error_traceback = commands_utils.to_file(exception, "traceback.txt")
        
        await send_with_file(error_text, error_traceback)
        
        nef = commands_utils.to_file(exception, f"{interaction.guild}-error.txt")
        return await send_to_debug_channel(content=error_text, file=nef)
    
    def get_embed(self, title: str) -> discord.Embed:
        
        uptime = self.get_uptime()
        embed = discord.Embed(title=title)
        embed.color = discord.Colour.lighter_grey()
        embed.set_footer(text=f"Uptime — {uptime.days} Days ({uptime}) | Version — {developerconfig.VERSION}")
        
        return embed
    
    async def get_input(self, interaction: discord.Interaction, msg: str) -> discord.Message | None:
        """Get confirmation for an action that a user can perform (For example; /stop)

        Args:
            interaction (discord.Interaction): Interaction of the command instance
            msg (str): Confirmation text

        Returns:
            discord.Message: New message that was generated by the confirmation.
        """
        def _check_if_user(message: discord.Message) -> bool:
            return message.author.id == interaction.user.id and message.channel == interaction.channel
        
        try:
            await interaction.response.send_message(msg) if not interaction.response.is_done() else await interaction.followup.send(msg)
            message: discord.Message = await self.wait_for('message', check=_check_if_user, timeout=developerconfig.QUERY_TIMEOUT)
            return message
        except (TimeoutError, CancelledError):
            return None
        
    @property
    def is_voice_compatible(self) -> bool:
        try:
            self.__ffmpeg__ = find_executable(developerconfig.FFMPEG)
            self.__ffprobe__ = find_executable(developerconfig.FFPROBE)
            discord.opus.load_opus(developerconfig.LIBOPUS)
        except OSError:
            common_functions.warn_for_error(f"Opus library not found. Voice will NOT work. \n(Library specified: {developerconfig.LIBOPUS}\nHas FFMpeg: {'No' if not self.__ffmpeg__ else f'Yes (At: {self.__ffmpeg__})'}\nHas FFProbe: {'No' if not self.__ffprobe__ else f'Yes (At: {self.__ffprobe__})'})")
        return bool(self.__ffmpeg__ and self.__ffprobe__ and discord.opus.is_loaded())
        
    async def on_ready(self):
        if self.application:
            with database.DGDatabaseSession(reset_if_failed_check=True) as database_session:
                with modelhandler.DGRulesManager() as _guild_handler:
                    
                    
                    def check_servers():
                        common_functions.send_info_text("Checking guild rule status..")
                        g_ids = _guild_handler.get_guilds()
                        for guild in self.guilds:
                            if guild.id not in g_ids:
                                _guild_handler._add_raw_guild(guild.id)
                                common_functions.send_info_text(f"Added new guild: {guild.id}")
                        common_functions.send_info_text("Guilds all added\n")

                    async def _check_integrity(i: int):
                        try:
                            
                            common_functions.send_info_text("Performing database check..")
                            if not i > 1:
                                if not database_session.check():
                                    common_functions.warn_for_error("Database file has been modified / deleted, rebuilding..")
                                    database_session.init()
                                    return await _check_integrity(i+1)
                                
                                return common_functions.send_info_text("Database all set.\n")
                            common_functions.send_fatal_error_warning("Database could not be rebuilt. Aborting. Check database files.")
                            return await self.close()
                        
                        except sqlite3.OperationalError:
                            common_functions.warn_for_error("Database error. Purging and resetting..")
                            database_session.reset()
                        
                        except sqlite3.DatabaseError:
                            common_functions.warn_for_error("Incorrect database version.")
                            database_session.reset()
                            
                    await _check_integrity(0)
                    check_servers()
                    confighandler.check_and_get_yaml()
                    
                    if confighandler.get_config("backup_upon_start") == True:
                        location = database_session.backup_database()
                        common_functions.send_info_text(f'Backed up database to "{location}"')
                    
                    has_voice = self.is_voice_compatible
                    database_age = database_session.get_seconds_since_creation()
                    
                    print(f"""
                    Version = {developerconfig.VERSION}
                    Database Version = {database_session.get_version()}
                    Database Age = {database_age // 86400} Days, {database_age // 3600} Hours, {database_age // 60} Minutes, {database_age} Seconds.
                    Report Channel = {self.get_channel(confighandler.get_config("bug_report_channel")) if confighandler.get_config("bug_report_channel") and str(confighandler.get_config("bug_report_channel")).isdecimal() == True else None}
                    Voice Installed = {has_voice}
                    Voice Enabled = {confighandler.get_config("allow_voice")}
                    Users Can Use Voice = {has_voice and confighandler.get_config("allow_voice")}
                    """)

                    self.chats: dict[int, dict[str, chat.DGChatType] | dict] = {}
                    self.default_chats: dict[str, None | chat.DGChatType] = {}

                    self.start_time = datetime.datetime.now(tz=self.__tz__)
                    
                    await self.change_presence(activity=discord.Activity(type=confighandler.get_config("status_type"), name=confighandler.get_config("status_text")))
                
                    common_functions.send_affirmative_text(f"{self.application.name} / {confighandler.get_config('bot_name')} Online.")
                    
                
                self.chats = {user.id: {} for user in self.users}
                self.default_chats = {f"{user.id}-latest": None for user in self.users if not user.bot}

                self.tree.on_error = self.handle_error # type: ignore

    async def setup_hook(self):
        print("Cogs\n")
        for file in os.listdir(f"extensions"):
            if file.endswith(".py"):
                await self.load_extension(f"extensions.{file[:-3]}")
        
        print("\nConnecting to discord..")
        await self.tree.sync()
        print("Synced.")
        return await super().setup_hook()

# Driver Code

async def _run_bot():
    """Runs the bot."""
    client = None
    try:
        DISCORD_TOKEN, OPENAI_TOKEN = confighandler.get_api_key("discord_api_key"), confighandler.get_api_key("openai_api_key")
        print(f"\nTokens\n\nDiscord: {DISCORD_TOKEN[:6]}...{DISCORD_TOKEN[-3:]}\nOpenAI: {OPENAI_TOKEN[:6]}...{OPENAI_TOKEN[-3:]}\n")
            
        logging_handler = logging.FileHandler(developerconfig.LOG_FILE, mode="w+")
        discord.utils.setup_logging(level=logging.ERROR, handler=logging_handler)
        
        async with DeveloperJoe(command_prefix="whatever", intents=DeveloperJoe.INTENTS) as client:
            await client.start(DISCORD_TOKEN)
            
    except KeyboardInterrupt:
        if client:
            await client.close()
            exit(0)
            
    except discord.errors.LoginFailure:
        common_functions.send_fatal_error_warning(f"Improper Discord API Token given in {developerconfig.TOKEN_FILE}, please make sure the API token is still valid.")
        exit(1)
        
    except aiohttp.ClientConnectionError:
        common_functions.send_fatal_error_warning("You are not connected to WiFi.")
        exit(1)
    
    except discord.app_commands.errors.CommandSyncFailure:
        common_functions.send_fatal_error_warning(f'There was an error with a command. This may occur because your bots name is too long within the "{developerconfig.CONFIG_FILE}" config file.')
        exit(1)
        
def main(keys: dict[str, str]):
    try:
        confighandler.write_keys(keys)
        asyncio.run(_run_bot())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    common_functions.send_fatal_error_warning(f"Please use main.py to run {confighandler.get_config('bot_name')} or call the main() function.")
    