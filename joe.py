import discord, openai, asyncio, os
from discord.ext import commands
from typing import Coroutine, Any

# Configuration

try:
    with open('token', 'r') as tk_file:
        tk_file_data = tk_file.read().splitlines()
        TOKEN: str = tk_file_data[0]
        openai.api_key = tk_file_data[1]
except FileNotFoundError:
    print("Missing token file."); exit(1)
except IndexError:
    print("Missing tokens."); exit(1)

INTENTS = discord.Intents.default()

# Main Bot Class

class DevJoe(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gpt_token = openai.api_key

    async def on_ready(self):
        print(f"{self.application.name} Online.")

    async def setup_hook(self) -> Coroutine[Any, Any, None]:
        for file in os.listdir(f"extensions"):
            if file.endswith(".py"):
                await self.load_extension(f"extensions.{file[:-3]}")

        await self.tree.sync()
        self.command_errors = {str(command.name): dict(command.extras) for command in self.tree.walk_commands()}

        return await super().setup_hook()
    
# Driver Code

async def run_bot():
    ...
    async with DevJoe(command_prefix="?", intents=INTENTS) as client:
        await client.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        pass
