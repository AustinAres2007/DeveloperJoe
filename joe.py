import discord, openai, asyncio, os
from discord.ext import commands
from typing import Coroutine, Any, Union
from objects import GPTChat
# Configuration

try:
    with open('dependencies/token', 'r') as tk_file:
        TOKEN: str = tk_file.read()
except FileNotFoundError:
    print("Missing token file."); exit(1)

INTENTS = discord.Intents.all()

# Main Bot Class

class DevJoe(commands.Bot):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gpt_token = openai.api_key 

    def get_user_conversation(self, id_: int) -> Union[GPTChat.GPTChat, None]:
        return self.chats[id_] if int(id_) in list(self.chats) else None
    
    async def on_ready(self):
        if self.application:
            print(f"{self.application.name} Online")

            self.chats = {}
            await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="AND answering lifes biggest questions."))


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