import discord
from typing import Union
from discord.ext import commands
from joe import DevJoe

class admin(commands.Cog):
    def __init__(self, client):
        self.client: DevJoe = client
        print(f"{self.__cog_name__} Loaded")

    @discord.app_commands.command(name="shutdown", description="Shuts down bot client")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def halt(self, interaction: discord.Interaction):
        await interaction.response.send_message("Shutting Down")
        await self.client.close()

        exit(0)

    @discord.app_commands.command(name="lock", description="Locks a select GPT Model behind a role or permission.")
    @discord.app_commands.checks.has_permissions(manage_channels=True)
    async def lock_user(self, interaction: discord.Interaction, user: Union[discord.Member, discord.User]):
        ...

async def setup(client):
    await client.add_cog(admin(client))
