
import sys
from typing import Any
v_info = sys.version_info

if not (v_info.major >= 3 and v_info.minor > 8):
    print(f'You must run this bot with Python 3.9 and above.\nYou are using Python {v_info.major}.{v_info.minor}\nYou may install python at "https://www.python.org/downloads/" and download the latest version.')
    exit(1)

try:
    # Not required here, just importing for integrity check.
    import json, openai, openai_async, tiktoken, sqlite3

    import discord, logging, asyncio, os, io, datetime
    from discord.ext import commands
    from typing import Coroutine, Any, Union

except ImportError as e:
    print(f"Missing Imports, please execute `pip install -r dependencies/requirements.txt` to install required dependencies. (Actual Error: {e})")
    exit(1)

try:
    from objects import GPTChat, GPTHistory, GPTErrors, GPTModelRules, GPTDatabase, GPTConfig
except (IndexError) as e:
    print(f"Missing internal dependencies, please collect a new install of DeveloperJoe. (Actual Error: {e})")
    exit(1)

# Configuration

try:
    with open(GPTConfig.TOKEN_FILE, 'r') as tk_file:
        DISCORD_TOKEN, OPENAI_TOKEN = tk_file.readlines()[0:2]
        DISCORD_TOKEN = DISCORD_TOKEN.strip()
        OPENAI_TOKEN = OPENAI_TOKEN.strip()
except (FileNotFoundError, ValueError, IndexError):
    print("Missing token file / Missing tokens within token file"); exit(1)

"""Changelog:
    Fixed streaming message size error
    Secured DeveloperJoe chat requirements (What channels it may speak in)
"""

# Main Bot Class

class DevJoe(commands.Bot):

    INTENTS = discord.Intents.all()
    full_user_chat_return_type = Union[dict[str, GPTChat.GPTChat], dict]

    def __init__(self, *args, **kwargs):
        self._DISCORD_TOKEN = DISCORD_TOKEN
        self._OPENAI_TOKEN = OPENAI_TOKEN
        super().__init__(*args, **kwargs)

    def get_uptime(self) -> datetime.timedelta:
        return (datetime.datetime.now(tz=GPTConfig.TIMEZONE) - self.start_time)
    
    def get_user_conversation(self, id_: int, chat_name: Union[str, None]=None, all: bool=False) -> Union[Union[GPTChat.GPTChat, int], full_user_chat_return_type]:
        if int(id_) in list(self.chats) and self.chats[id_]: # type: ignore
            if all == True: 
                return self.chats[id_] # type: ignore
            if not chat_name:
                return None # type: ignore
            elif chat_name and chat_name in self.chats[id_]: # type: ignore
                return self.chats[id_][chat_name] # type: ignore
        return 0
    
    def delete_conversation(self, user: Union[discord.Member, discord.User], conversation_name: str) -> None:
        del self.chats[user.id][conversation_name] # type: ignore

    def add_conversation(self, user: Union[discord.Member, discord.User], name: str, conversation: GPTChat.GPTChat) -> None:
        self.chats[user.id][name] = conversation # type: ignore

    def set_default_conversation(self, user: Union[discord.Member, discord.User], name: Union[None, str], absolute: bool=False) -> None:
        self.chats[f"{user.id}-latest"] = self.get_user_conversation(user.id, name) if not absolute else name# type: ignore
    
    def get_default_conversation(self, user: Union[discord.User, discord.Member]) -> Union[None, GPTChat.GPTChat]:
        return self.chats[f"{user.id}-latest"] # type: ignore
    
    def manage_defaults(self, user: Union[discord.User, discord.Member], name: Union[None, str], set_to_none: bool=False) -> Union[str, None]:
        current_default = self.get_default_conversation(user)
        names_convo = self.get_user_conversation(user.id, name)
        name_is_chat = isinstance(names_convo, GPTChat.GPTChat)

        if name_is_chat:
            self.set_default_conversation(user, name)
            return name
        elif not name and set_to_none == True:
            self.set_default_conversation(user, None)
        elif current_default:
            return current_default.display_name

    async def handle_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        if interaction.response.is_done():
            await interaction.followup.send(str(error))
        else:
            await interaction.response.send_message(str(error))

    def to_file(self, content: str, name: str) -> discord.File:
        f = io.BytesIO(content.encode())
        f.name = name
        return discord.File(f)
    
    async def get_confirmation(self, interaction: discord.Interaction, msg: str) -> discord.Message:
        def _check_if_user(message: discord.Message) -> bool:
            return message.author.id == interaction.user.id and message.channel == interaction.channel
        
        await interaction.response.send_message(msg) if not interaction.response.is_done() else await interaction.followup.send(msg)
        message: discord.Message = await self.wait_for('message', check=_check_if_user, timeout=GPTConfig.QUERY_TIMEOUT)
        return message
    
    async def send_debug_message(self, interaction: discord.Interaction, error: BaseException, cog: str) -> None:
        if GPTConfig.DEBUG == True:
            exception_text = f"From main class error handler \n\nError Class: {str(Exception)}\nError Arguments: {str(Exception.args)}\nFrom cog: {cog} "
            await interaction.followup.send(exception_text) if interaction.response.is_done() else await interaction.response.send_message(exception_text) 
            raise error
            
    async def on_ready(self):
        if self.application:
            print(f"\n{self.application.name} Online (V: {GPTConfig.VERSION})")

            self.chats: Union[dict[int, Union[dict[str, GPTChat.GPTChat], dict]], dict[str, Union[None, GPTChat.GPTChat]]] = {}
            self.start_time = datetime.datetime.now(tz=GPTConfig.TIMEZONE)
            
            await self.change_presence(activity=discord.Activity(type=GPTConfig.STATUS_TYPE, name=GPTConfig.STATUS_TEXT))

            _history = GPTHistory.GPTHistory()
            async def _check_integrity(i: int):
                if not i > 1:
                    if not _history.__check__():
                        print("Database file has been modified / deleted, rebuilding..")
                        _history.init_history()
                        return await _check_integrity(i+1)
                    return print("Database all set.")
                print("Database could not be rebuilt. Aborting. Check database files.")
                return await self.close()
            
            await _check_integrity(0)

            self.chats = {user.id: {} for user in self.users}
            self.chats = self.chats | {f"{user.id}-latest": None for user in self.users} # type: ignore
            self.tree.on_error = self.handle_error

    async def setup_hook(self) -> Coroutine[Any, Any, None]:
        for file in os.listdir(f"extensions"):
            if file.endswith(".py"):
                await self.load_extension(f"extensions.{file[:-3]}")

        await self.tree.sync()
        return await super().setup_hook() # type: ignore
    
    
# Driver Code

async def run_bot():
    client = None
    try:
        print(f"Tokens\n\nDiscord: {DISCORD_TOKEN}\nOpenAI: {OPENAI_TOKEN}\n")
        
        with open("misc/bot_log.log", "w+"):
            ...
            
        logging_handler = logging.FileHandler("misc/bot_log.log", mode="w+")
        discord.utils.setup_logging(level=logging.ERROR, handler=logging_handler)
        
        async with DevJoe(command_prefix="?", intents=DevJoe.INTENTS) as client:
            await client.start(DISCORD_TOKEN)
    except KeyboardInterrupt:
        if client:
            await client.close()
            exit(0)
    except discord.errors.LoginFailure:
        print(f"Improper Discord API Token given in {GPTConfig.TOKEN_FILE}, please make sure the API token is still valid.")
        exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        pass