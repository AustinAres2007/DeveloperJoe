"""Main DeveloperJoe file."""

import sys
v_info = sys.version_info

def print_and_exit(text, sys):
    ...
if not (v_info.major >= 3 and v_info.minor > 8):
    print(f'You must run this bot with Python 3.9 and above.\nYou are using Python {v_info.major}.{v_info.minor}\nYou may install python at "https://www.python.org/downloads/" and download the latest version.')
    exit(1)

try:
    # Not required here, just importing for integrity check.
    import json, openai, openai_async, tiktoken, sqlite3, math, traceback, aiohttp

    import discord, logging, asyncio, os, datetime
    from discord.ext import commands
    from typing import Union

except ImportError as e:
    print(f"Missing Imports, please execute `pip install -r dependencies/requirements.txt` to install required dependencies. (Actual Error: {e})")
    exit(1)

from sources import *

# Configuration

try:
    with open(config.TOKEN_FILE, 'r') as tk_file:
        DISCORD_TOKEN, OPENAI_TOKEN = tk_file.readlines()[0:2]
        DISCORD_TOKEN = DISCORD_TOKEN.strip()
        OPENAI_TOKEN = OPENAI_TOKEN.strip()
    
except (FileNotFoundError, ValueError, IndexError):
    print("Missing token file / Missing tokens within token file"); exit(1)

try:
    with open(WELCOME_FILE) as welcome_file, open(ADMIN_FILE) as admin_file:
        WELCOME_TEXT = welcome_file.read()
        ADMIN_TEXT = admin_file.read()

except FileNotFoundError:
    print(f"Missing server join files. ({WELCOME_FILE} and {ADMIN_FILE})")

# Main Bot Class

class DeveloperJoe(commands.Bot):

    """Main DeveloperJoe Bot Instance"""

    INTENTS = discord.Intents.all()

    def __init__(self, *args, **kwargs):
        self._DISCORD_TOKEN = DISCORD_TOKEN
        self._OPENAI_TOKEN = OPENAI_TOKEN

        self.WELCOME_TEXT = WELCOME_TEXT.format(BOT_NAME)
        self.ADMIN_TEXT = ADMIN_TEXT.format(BOT_NAME)
        
        super().__init__(*args, **kwargs)

    def get_uptime(self) -> datetime.timedelta:
        return (datetime.datetime.now(tz=TIMEZONE) - self.start_time)
    
    def get_user_conversation(self, member: discord.Member, chat_name: Union[str, None]=None) -> Union[Union[DGTextChat, DGVoiceChat], None]:
        """ Get the specified members current chat.

        Args:
            member (discord.Member): The member of whoms chat will be returned.
            chat_name (Union[str, None], optional): The name of the chat. Defaults to None.

        Raises:
            UserDoesNotHaveChat: If the specified chat does not exist.

        Returns:
            Union[Union[DGTextChat, DGVoiceChat], None]: The chat, or None if chat_name is not specified.
        """
        
        if int(member.id) in list(self.chats):
            if not chat_name:
                return
            elif chat_name and chat_name in self.chats[member.id]:
                return self.chats[member.id][chat_name]
        
        raise UserDoesNotHaveChat(chat_name, member)
    
    def get_all_user_conversations(self, member: discord.Member) -> Union[dict[str, DGChatType], None]:
        """Get all of a specified members conversation(s)

        Args:
            member (discord.Member): The member of whoms chats will be returned.

        Returns:
            Union[dict[str, DGChatType], None]: A dictionary containing the name of the chat as the key, and the chat instance as the value.
        """
        if member.id in list(self.chats) and self.chats[member.id]:
            return self.chats[member.id]
    
    def get_user_has_permission(self, member: Union[discord.Member, None], model: GPTModelType) -> bool:
        """Return if the user has permission to user a model

        Args:
            member (Union[discord.Member, None]): The member to be checked
            model (GPTModelType): The model to try the user agaisnt.

        Returns:
            bool: True if the user has correct permissions, False if not.
        """
        if isinstance(member, discord.Member):
            with DGRules(member.guild) as check_rules:
                return bool(check_rules.user_has_model_permissions(member.roles[-1], model))
        return False
    
    def get_default_conversation(self, member: discord.Member) -> Union[DGChatType, None]:
        """Get a users default conversation

        Args:
            member (discord.Member): Which member to get default chat

        Returns:
            Union[DGChatType, None]: The default chat, or None if the user doesn't have one.
        """
        return self.default_chats[f"{member.id}-latest"]
    
    def get_user_voice_conversation(self, member: discord.Member, chat_name) -> Union[DGVoiceChat, None]:
        # TODO: Add funcion that aquires all voice chats only
        """Get a users chat, only if it supports voice.

        Args:
            member (discord.Member): The member that the chat will belong to.
            chat_name (_type_): The name of the chat.

        Returns:
            Union[DGVoiceChat, None]: The chat, or None if the chat doesn't exist, or does not support voice.
        """
        chat = self.get_user_conversation(member, chat_name=chat_name)
        return chat if isinstance(chat, DGVoiceChat) else None
    
    def delete_conversation(self, member: discord.Member, conversation_name: str) -> None:
        """Deletes a members chat.

        Args:
            member (discord.Member): The member that the chat belongs to.
            conversation_name (str): The name of the chat to be deleted.
        """
        del self.chats[member.id][conversation_name]

    def add_conversation(self, member: discord.Member, name: str, conversation: DGChatType) -> None:
        """Adds a conversation to a users chat database.

        Args:
            member (discord.Member): The member who owns the chat.
            name (str): Name of the chat
            conversation (DGChatType): Instance of the conversation.
        """
        self.chats[member.id][name] = conversation

    def set_default_conversation(self, member: discord.Member, name: Union[None, str]) -> None:
        """Sets a users default chat.

        Args:
            member (discord.Member): The member who's default chat will change.
            name (Union[None, str]): Name of the new chat.
        """
        self.default_chats[f"{member.id}-latest"] = self.get_user_conversation(member, name)
    
    def manage_defaults(self, member: discord.Member, name: Union[None, str], set_to_none: bool=False) -> Union[str, None]:
        """Manages a users default chat depending on parameters given.

        Args:
            member (discord.Member): The member to modify default.
            name (Union[None, str]): Name of different chat.
            set_to_none (bool, optional): Weather the chat will be reset to None. Defaults to False.

        Returns:
            Union[str, None]: The name of the new chat, or None if the chat does not exist.
        """
        current_default = self.get_default_conversation(member)
        names_convo = self.get_user_conversation(member, name)
        name_is_chat = isinstance(names_convo, DGChatType)

        if name_is_chat:
            self.set_default_conversation(member, name)
            return name
        elif not name and set_to_none == True:
            self.set_default_conversation(member, None)
        elif current_default:
            return current_default.display_name

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
        async def send(text: str):
            if interaction.response.is_done():
                return await interaction.followup.send(text)
            return await interaction.response.send_message(text)
        
        async def send_with_file(text: str, file: discord.File):
            if interaction.response.is_done():
                return await interaction.followup.send(text, file=file)
            return await interaction.response.send_message(text, file=file)
        
        exception: str = traceback.format_exc()
        # If it is a DGException
        if message := getattr(error, "message", None):
            if (log := getattr(error, "log_error", None)) != None:
                if log == True:
                    logging.error(exception) 
                return await send(message) if getattr(error, "send_exception", False) == True else None
        
        logging.error(exception)

        error_text = f"From error handler: {str(error)}"
        error_traceback = utils.to_file(traceback.format_exc(), "traceback.txt")

        return await send_with_file(error_text, error_traceback)

    async def get_confirmation(self, interaction: discord.Interaction, msg: str) -> discord.Message:
        """Get confirmation for an action that a user can perform (For example; /stop)

        Args:
            interaction (discord.Interaction): Interaction of the command instance
            msg (str): Confirmation text

        Returns:
            discord.Message: New message that was generated by the confirmation.
        """
        def _check_if_user(message: discord.Message) -> bool:
            return message.author.id == interaction.user.id and message.channel == interaction.channel
        
        await interaction.response.send_message(msg) if not interaction.response.is_done() else await interaction.followup.send(msg)
        message: discord.Message = await self.wait_for('message', check=_check_if_user, timeout=QUERY_TIMEOUT)
        return message
    
    async def send_debug_message(self, interaction: discord.Interaction, error: BaseException, cog: str) -> None:
        """For internal use. Sends a debug message.

        Args:
            interaction (discord.Interaction): The interaction of the message.
            error (BaseException): The error to send.
            cog (str): Where the error came from.

        Raises:
            error: the error given.
        """
        if DEBUG == True:
            exception_text = f"From main class error handler \n\nError Class: {str(Exception)}\nError Arguments: {str(Exception.args)}\nFrom cog: {cog} "
            await interaction.followup.send(exception_text) if interaction.response.is_done() else await interaction.response.send_message(exception_text) 
            raise error
            
    async def on_ready(self):
        if self.application:
            print(f"\n{self.application.name} Online (V: {VERSION})")

            self.chats: dict[int, Union[dict[str, DGChatType], dict]] = {}
            self.default_chats: dict[str, Union[None, DGChatType]] = {}

            self.start_time = datetime.datetime.now(tz=TIMEZONE)
            
            await self.change_presence(activity=discord.Activity(type=STATUS_TYPE, name=STATUS_TEXT))
            with (DGHistorySession() as _history, DGRulesManager() as _guild_handler):
                
                
                def check_servers():
                    print("Checking guild rule status..")
                    g_ids = _guild_handler.get_guilds()
                    for guild in self.guilds:
                        if guild.id not in g_ids:
                            _guild_handler._add_raw_guild(guild.id)
                            print(f"Added new guild: {guild.id}")
                    print()

                async def _check_integrity(i: int):
                    print("Performing database check..")
                    if not i > 1:
                        if not _history.__check__():
                            print("Database file has been modified / deleted, rebuilding..")
                            _history.init_history()
                            return await _check_integrity(i+1)
                            
                        return print("Database all set.")
                    print("Database could not be rebuilt. Aborting. Check database files.")
                    return await self.close()
            
                await _check_integrity(0)
                check_servers()

                print("Done! Running.")
            self.chats = {user.id: {} for user in self.users}
            self.chats = self.chats
            self.default_chats = {f"{user.id}-latest": None for user in self.users if not user.bot}

            self.tree.on_error = self.handle_error

    async def setup_hook(self):
        for file in os.listdir(f"extensions"):
            if file.endswith(".py"):
                await self.load_extension(f"extensions.{file[:-3]}")

        await self.tree.sync()
        return await super().setup_hook()
    

# Driver Code

async def run_bot():
    """Runs the bot."""
    client = None
    try:
        print(f"Tokens\n\nDiscord: {DISCORD_TOKEN}\nOpenAI: {OPENAI_TOKEN}\n")
        
        with open("misc/bot_log.log", "w+"):
            ...
            
        logging_handler = logging.FileHandler("misc/bot_log.log", mode="w+")

        discord.utils.setup_logging(level=logging.ERROR, handler=logging_handler)
        
        async with DeveloperJoe(command_prefix=commands.when_mentioned_or("?"), intents=DeveloperJoe.INTENTS) as client:
            await client.start(DISCORD_TOKEN)
            
    except KeyboardInterrupt:
        if client:
            await client.close()
            exit(0)
            
    except discord.errors.LoginFailure:
        print(f"Improper Discord API Token given in {TOKEN_FILE}, please make sure the API token is still valid.")
        exit(1)
        
    except aiohttp.ClientConnectionError:
        print("You are not connected to WiFi.")
        exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        pass