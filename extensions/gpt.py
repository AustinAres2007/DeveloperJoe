import discord, openai
from discord.ext import commands

class gpt(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client
        openai.api_key = client.gpt_token

        print("General Loaded")

    @discord.app_commands.command(name="status", description=f"Check if bot is online.", extras={'error': "Wait some moments please."})
    async def online(self, ctx: discord.Interaction):
        print("Test command working")
        await ctx.response.send_message("Online")

    @discord.app_commands.command(name="stop", description="Shuts down bot client")
    async def halt(self, ctx: discord.Interaction):
        await ctx.response.send_message("Shutting down.")
        await self.client.close()

async def setup(client):
    await client.add_cog(gpt(client))
