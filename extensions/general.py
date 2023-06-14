import discord
from discord.ext import commands

class general(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client
        print("Programming Loaded")

    @discord.app_commands.command(name="help", description="Lists avalible commands")
    async def help_command(self, interaction: discord.Interaction):
        for command in self.client.tree.walk_commands():
            print(command.name, command.description, str(command.parameters))

async def setup(client):
    await client.add_cog(general(client))
