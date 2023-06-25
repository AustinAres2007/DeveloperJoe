import discord, logging, asyncio, os, io

from discord import abc
from discord.ext import commands
from typing import Coroutine, Any, Union
from objects import GPTChat, GPTHistory, GPTConfig

# Configuration

try:
    with open('dependencies/token', 'r') as tk_file:
        TOKEN: str = tk_file.read()
except FileNotFoundError:
    print("Missing token file."); exit(1)

INTENTS = discord.Intents.all()

"""Changelog:
    Fixed streaming message size error
    Secured DeveloperJoe chat requirements (What channels it may speak in)
"""

# Main Bot Class

class DevJoe(commands.Bot):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_user_conversation(self, id_: int) -> Union[GPTChat.GPTChat, None]:
        return self.chats[id_] if int(id_) in list(self.chats) else None
    
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
    
    async def send_debug_message(self, interaction: discord.Interaction, error: Exception) -> None:
        if GPTConfig.DEBUG == True:
            await interaction.followup.send(str(error)) if interaction.response.is_done() else await interaction.response.send_message(str(error)) 
            
    async def on_ready(self):
        if self.application:
            print(f"{self.application.name} Online")

            self.chats = {}
            await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="AND answering lifes biggest questions. (/help)"))

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
        logging_handler = logging.FileHandler("misc/bot_log.log", mode="w+")
        discord.utils.setup_logging(level=logging.DEBUG, handler=logging_handler)
        
        async with DevJoe(command_prefix="?", intents=INTENTS) as client:
            await client.start(TOKEN)
    except KeyboardInterrupt:
        if client:
            await client.close()
        
if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        pass