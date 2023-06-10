import discord
from discord.ext import commands

class programming(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client
        print("Programming Loaded")

async def setup(client):
    await client.add_cog(programming(client))
