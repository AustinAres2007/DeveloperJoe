import discord, datetime

from discord.ext import commands
from typing import Optional
from joe import DevJoe
from objects import GPTChat, GPTHistory, GPTErrors, GPTConfig

class gpt(commands.Cog):

    def __init__(self, client):
        self.client: DevJoe = client
        print(f"{self.__cog_name__} Loaded") 
    
    @discord.app_commands.command(name="start", description="Start a DeveloperJoe Session")
    @discord.app_commands.describe(name="The name of the chat you will start (Will be used when saving the transcript)")
    async def start(self, interaction: discord.Interaction, name: str=""):
        
        actual_name = name if name else f"{datetime.datetime.now()}-{interaction.user.display_name}"

        if len(actual_name) > 39:
            return await interaction.followup.send("The name of your chat must be less than 40 characters.")
    
        async def func():
            convo = GPTChat.GPTChat(interaction.user, actual_name)

            await interaction.response.defer(ephemeral=True, thinking=True)
            await interaction.followup.send(convo.start())
            self.client.chats[interaction.user.id] = convo

        if not self.client.get_user_conversation(interaction.user.id):
            return await func()

        await interaction.response.send_message(GPTErrors.ConversationErrors.HAS_CONVO)

    @discord.app_commands.command(name="ask", description="Ask DeveloperJoe a question.")
    @discord.app_commands.describe(message="The query you want to send DeveloperJoe")
    async def ask(self, interaction: discord.Interaction, message: str):
        try:
            if convo := self.client.get_user_conversation(interaction.user.id):
                    
                await interaction.response.defer(ephemeral=True, thinking=True)
                reply = convo.ask(message)

                if len(reply) > 2000:
                    file_reply: discord.File = self.client.to_file(reply, "reply.txt")
                    return await interaction.followup.send(file=file_reply)
                return await interaction.followup.send(reply)
            await interaction.response.send_message(GPTErrors.ConversationErrors.NO_CONVO)
        except Exception as e:
            await self.client.send_debug_message(interaction, e)   

    @discord.app_commands.command(name="stop", description="Stop a DeveloperJoe session.")
    @discord.app_commands.describe(save="If you want to save your transcript.")
    @discord.app_commands.choices(save=[
        discord.app_commands.Choice(name="No, do not save my transcript save.", value="n"),
        discord.app_commands.Choice(name="Yes, please save my transcript.", value="y")
    ])
    async def stop(self, interaction: discord.Interaction, save: discord.app_commands.Choice[str]):
        
        if save.value not in ["n", "y"]:
            return await interaction.response.send_message("You did not pick a save setting. Please pick one from the pre-selected options.")
        
        reply = await self.client.get_confirmation(interaction, f'Are you sure you want to end this chat? (Send reply within {GPTConfig.QUERY_TIMEOUT} seconds, and "{GPTConfig.QUERY_CONFIRMATION}" to confirm, anything else to cancel.')
        if reply.content != GPTConfig.QUERY_CONFIRMATION:
            return await interaction.followup.send("Cancelled action.")
        
        async def func(gpt: GPTChat.GPTChat):
            with GPTHistory.GPTHistory() as history:
                farewell, error = gpt.stop(history, save.value)
                await interaction.followup.send(farewell)
                if error == 0:
                    del self.client.chats[interaction.user.id]
        
        # checks because app_commands cannot use normal ones.
        if convo := self.client.get_user_conversation(interaction.user.id):
            return await func(convo)
        await interaction.followup.send(GPTErrors.ConversationErrors.NO_CONVO)

    @discord.app_commands.command(name="generate", description="Create an image with specified parameters.")
    @discord.app_commands.describe(prompt="The keyword you want DeveloperJoe to describe.", resolution="Resolution of the final image.")
    @discord.app_commands.choices(resolution=[
        discord.app_commands.Choice(name="256x256", value="256x256"),
        discord.app_commands.Choice(name="512x512", value="512x512"),
        discord.app_commands.Choice(name="1024x1024", value="1024x1024")
    ]) 
    async def image_generate(self, interaction: discord.Interaction, prompt: discord.app_commands.Choice[str], resolution: Optional[discord.app_commands.Choice[str]]):
        r = "Error"
        try:
            await interaction.response.defer(ephemeral=True, thinking=True)
            if resolution in ["256x256", "512x512", "1024x1024"]:
                if convo := self.client.get_user_conversation(interaction.user.id):
                    r = str(convo.__send_query__(query_type="image", prompt=prompt, size=resolution, n=1))
                else:
                    r = GPTErrors.ConversationErrors.NO_CONVO
            else:
                r = "Incorrect resolution setting. (Must be: 256x256, 512x512, 1024x1024)"
        except Exception as e:
            r = f"Uncaught Exception: {e}"

        finally:
            return await interaction.followup.send(r)

    @discord.app_commands.command(name="info", description="Displays information about your current DeveloperJoe Chat.")
    async def get_info(self, interaction: discord.Interaction):
        if convo := self.client.get_user_conversation(interaction.user.id):
            
            returned_embed = discord.Embed(title="Chat Information")

            returned_embed.add_field(name="Started At", value=str(convo.time), inline=False)
            returned_embed.add_field(name="Used Tokens", value=f"{str(convo.tokens)}", inline=False)
            returned_embed.add_field(name="Chat Length", value=str(len(convo.chat_history)), inline=False)
            returned_embed.add_field(name="Chat ID", value=str(convo.id), inline=False)
            
            returned_embed.color = discord.Colour.purple()

            return await interaction.response.send_message(embed=returned_embed)
        
        await interaction.response.send_message(GPTErrors.ConversationErrors.NO_CONVO)  

async def setup(client):
    await client.add_cog(gpt(client))
