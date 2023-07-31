import sys
v_info = sys.version_info

if not (v_info.major >= 3 and v_info.minor > 8):
    print(f'You must run this bot with Python 3.9 and above.\nYou are using Python {v_info.major}.{v_info.minor}\nYou may install python at "https://www.python.org/downloads/" and download the latest version.')
    exit(1)

try:
    # Not required here, just importing for integrity check.
    import json, openai, openai_async, tiktoken, sqlite3, math, traceback

    import discord, logging, asyncio, os, io, datetime
    from discord.ext import commands
    from typing import Coroutine, Any, Union

except ImportError as e:
    print(f"Missing Imports, please execute `pip install -r dependencies/requirements.txt` to install required dependencies. (Actual Error: {e})")
    exit(1)

try:
    from objects import GPTChat, GPTHistory, GPTErrors, GPTModelRules, GPTDatabase, GPTConfig, GPTExceptions
except (ImportError, ImportWarning) as e:
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

try:
    with open(GPTConfig.WELCOME_FILE) as welcome_file, open(GPTConfig.ADMIN_FILE) as admin_file:
        WELCOME_TEXT = welcome_file.read()
        ADMIN_TEXT = admin_file.read()

except FileNotFoundError:
    print(f"Missing server join files. ({GPTConfig.WELCOME_FILE} and {GPTConfig.ADMIN_FILE})")

# Main Bot Class

class DevJoe(commands.Bot):

    INTENTS = discord.Intents.all()

    def __init__(self, *args, **kwargs):
        self._DISCORD_TOKEN = DISCORD_TOKEN
        self._OPENAI_TOKEN = OPENAI_TOKEN

        self.WELCOME_TEXT = WELCOME_TEXT.format(GPTConfig.BOT_NAME)
        self.ADMIN_TEXT = ADMIN_TEXT.format(GPTConfig.BOT_NAME)

        super().__init__(*args, **kwargs)

    def get_uptime(self) -> datetime.timedelta:
        return (datetime.datetime.now(tz=GPTConfig.TIMEZONE) - self.start_time)
    
    def get_user_conversation(self, member: discord.Member, chat_name: Union[str, None]=None) -> Union[Union[GPTChat.GPTChat, GPTChat.GPTVoiceChat], None]:
        if int(member.id) in list(self.chats) and self.chats[member.id]:
            if not chat_name:
                return None
            elif chat_name and chat_name in self.chats[member.id]:
                return self.chats[member.id][chat_name]
        return None
    
    def get_all_user_conversations(self, member: discord.Member) -> Union[dict[str, Union[GPTChat.GPTChat, GPTChat.GPTVoiceChat]], None]:
        if member.id in list(self.chats) and self.chats[member.id]:
            return self.chats[member.id]
    
    
    def assure_class_is_value(self, object, type):
        if isinstance(object, type):
            return object
        raise Exception("Wrong env")
        
    def get_user_has_permission(self, member: Union[discord.Member, None], model: str) -> bool:
        if isinstance(member, discord.Member):
            with GPTModelRules.GPTModelRules(member.guild) as check_rules:
                return bool(check_rules.user_has_model_permissions(member.roles[-1], model))
        return False
    
    def get_default_conversation(self, member: discord.Member) -> Union[GPTChat.GPTChat, GPTChat.GPTVoiceChat, None]:
        return self.default_chats[f"{member.id}-latest"]
    
    def get_user_voice_conversation(self, member: discord.Member, chat_name) -> Union[GPTChat.GPTVoiceChat, None]:
        # TODO: Add funcion that aquires all voice chats only
        chat = self.get_user_conversation(member, chat_name=chat_name)
        return chat if isinstance(chat, GPTChat.GPTVoiceChat) else None
    
    def delete_conversation(self, member: discord.Member, conversation_name: str) -> None:
        del self.chats[member.id][conversation_name]

    def add_conversation(self, member: discord.Member, name: str, conversation: GPTChat.GPTChat) -> None:
        self.chats[member.id][name] = conversation

    def set_default_conversation(self, member: discord.Member, name: Union[None, str]) -> None:
        self.default_chats[f"{member.id}-latest"] = self.get_user_conversation(member, name)
    
    def manage_defaults(self, member: discord.Member, name: Union[None, str], set_to_none: bool=False) -> Union[str, None]:
        current_default = self.get_default_conversation(member)
        names_convo = self.get_user_conversation(member, name)
        name_is_chat = isinstance(names_convo, GPTChat.GPTChat)

        if name_is_chat:
            self.set_default_conversation(member, name)
            return name
        elif not name and set_to_none == True:
            self.set_default_conversation(member, None)
        elif current_default:
            return current_default.display_name

    async def handle_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        print("Error")
        
        error_text = f"From error handler: {str(error)}"
        error_traceback = self.to_file(traceback.format_exc(), "traceback.txt")
        
        if interaction.response.is_done():
            await interaction.followup.send(error_text, file=error_traceback)
        else:
            await interaction.response.send_message(error_text, file=error_traceback)
        
        
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

            self.chats: dict[int, Union[dict[str, Union[GPTChat.GPTChat, GPTChat.GPTVoiceChat]], dict]] = {}
            self.default_chats: dict[str, Union[None, GPTChat.GPTChat, GPTChat.GPTVoiceChat]] = {}

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
            self.chats = self.chats
            self.default_chats = {f"{user.id}-latest": None for user in self.users}

            self.tree.on_error = self.handle_error

    async def setup_hook(self):
        for file in os.listdir(f"extensions"):
            if file.endswith(".py"):
                await self.load_extension(f"extensions.{file[:-3]}")

        await self.tree.sync()
        return await super().setup_hook()
    
    
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