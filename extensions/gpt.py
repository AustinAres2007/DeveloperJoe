import discord, openai, asyncio
from discord.ext import commands

class gpt(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client
        
        openai.organization = "org-v6VcB3sShPterTqRqUnEB0um"
        openai.api_key = client.gpt_token

        print("General Loaded")

    def send(self, context, message: str):
        asyncio.run_coroutine_threadsafe(context.channel.send(message), self.client.loop)

    @discord.app_commands.command(name="status", description=f"Check if bot is online.", extras={'error': "Wait some moments please."})
    async def online(self, ctx: discord.Interaction):
        print("Test command working")
        await ctx.response.send_message("Online")

    @discord.app_commands.command(name="shutdown", description="Shuts down bot client")
    async def halt(self, ctx: discord.Interaction):
        await ctx.response.send_message("Shutting down.")
        await self.client.close()
    
    @discord.app_commands.command(name="start", description="Start a GPT-3 Session")
    async def start(self, ctx: discord.Interaction):
        await ctx.response.defer(ephemeral=True, thinking=True)
        completion = openai.ChatCompletion.create(model = "gpt-3.5-turbo",
            messages = [
                {"role": "user", "content": "Hello GPT. Please give us a short paragraph of what you can do."}
            ])
        
        self.send(ctx, completion.choices[0].message.content)
    
    @discord.app_commands.command(name="stop", description="Start a GPT-3 Session")
    async def start(self, ctx: discord.Interaction):
        await ctx.response.defer(ephemeral=True, thinking=True)
        completion = openai.ChatCompletion.create(model = "gpt-3.5-turbo",
            messages = [
                {"role": "user", "content": "Hello GPT. Please give us a short paragraph of what you can do."}
            ])
        
        self.send(ctx, completion.choices[0].message.content)

        
        


async def setup(client):
    await client.add_cog(gpt(client))
