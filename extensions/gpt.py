import discord, openai, asyncio, requests
from discord.ext import commands
from typing import Callable, Union

BASE_ENDPOINT = "https://api.openai.com/v1"

# TODO: Handle GPT errors

"""
Rant:
    This API / kit is so shit it makes me not want to code for discord anymore. It has become complex since the update and discords
    TOS change. It has a very "linear" structure now. Not flexible at all.
"""
# Errors

NO_CONVO = "You do not have a conversation with DeveloperJoe. Do /start to do such."
HAS_CONVO = 'You already have an ongoing conversation with DeveloperJoe. To reset, do "/stop."'

class gpt(commands.Cog):
    
    def has_conversation(self, id_: int) -> bool:
        return int(id_) in list(self.conversations) 
    def is_owner(interaction: discord.Interaction) -> bool:
        return interaction.user.id == 400089431933059072
    
    async def ask_gpt(self, ctx: discord.Interaction, message: str, role: str="user", save_to_context: bool=True):
        try:
            self.conversations[ctx.user.id].append({"role": role, "content": message})
            body = {"model": "gpt-3.5-turbo", "messages": self.conversations[ctx.user.id]}
            gpt_request = requests.post(f"{BASE_ENDPOINT}/chat/completions", headers=self.header, json=body)
            
            if gpt_request.status_code == 200:

                response = gpt_request.json()
                message_response = response["choices"][0]["message"]
                
                await ctx.followup.send(message_response["content"].strip())
                self.conversations[ctx.user.id].append(message_response) if save_to_context else None
                self.conversations[ctx.user.id].pop() if not save_to_context else None
            else:
                print(gpt_request.json())

        except requests.ConnectionError:
            await ctx.followup.send("General Error, please try again.")
        except requests.Timeout:
            await ctx.followup.send("Timeout. Please try again.")
        except KeyError:
            await ctx.followup.send(NO_CONVO)

    def __init__(self, client):
        self.client: commands.Bot = client
        
        openai.organization = "org-v6VcB3sShPterTqRqUnEB0um"
        openai.api_key = client.gpt_token

        self.header = {"Content-Type": "application/json", "Authorization": f"Bearer {openai.api_key}"}
        self.conversations = {}

        print("GPT Loaded")

    @discord.app_commands.command(name="halt", description="Shuts down bot client")
    @discord.app_commands.check(is_owner)
    async def halt(self, ctx: discord.Interaction):
        await ctx.response.send_message("Shutting down.")
        await self.client.close()
    
    @discord.app_commands.command(name="start", description="Start a DeveloperJoe Session")
    async def start(self, interaction: discord.Interaction):
        
        async def func():
            self.conversations[interaction.user.id] = []
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await self.ask_gpt(interaction, "Introduce yourself. Give a short formal description, something to understand easily.", "system", False)
            
        
        if not self.has_conversation(interaction.user.id):
            return await func()
        await interaction.response.send_message(HAS_CONVO)

    @discord.app_commands.command(name="ask", description="Ask DeveloperJoe a question.")
    async def ask(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer(ephemeral=True, thinking=True)
        await self.ask_gpt(interaction, message)

    @discord.app_commands.command(name="stop", description="Stop a DeveloperJoe session.")
    async def stop(self, interaction: discord.Interaction):

        # Actual command
        async def func():
            del self.conversations[interaction.user.id]
            await interaction.response.send_message("Deleted conversation history.")
        
        # checks because app_commands cannot use normal ones.
        if self.has_conversation(interaction.user.id):
            return await func()
        await interaction.response.send_message(NO_CONVO)
            

async def setup(client):
    await client.add_cog(gpt(client))
