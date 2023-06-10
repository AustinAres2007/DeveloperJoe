import discord
from discord.ext import commands

class programming(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client
        print("Programming Loaded")

    @discord.app_commands.command(name="interpret", description="Execute a line of code.")
    async def interpreter(self, interaction: discord.Interaction, code: str):
        returned = exec(code)
        return await interaction.response.send_message(returned if returned else "None")


async def setup(client):
    await client.add_cog(programming(client))
