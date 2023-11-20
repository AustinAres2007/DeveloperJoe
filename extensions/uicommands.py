import discord
from discord.ext.commands import Cog
from joe import DeveloperJoe
from .ui import modals

class UICommands(Cog):
    def __init__(self, client: DeveloperJoe) -> None:
        super().__init__()
        
        self.client = client 
        print(f"{self.__cog_name__} Loaded")
        
async def setup(client: DeveloperJoe):
    await client.add_cog(UICommands(client))
