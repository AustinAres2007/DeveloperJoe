import discord, datetime, io
from discord.ext import commands
from typing import Optional

from joe import DevJoe
from objects import GPTChat, GPTHistory

"""
Rant:
    This API / kit is so shit it makes me not want to code for discord anymore. It has become complex since the update and discords
    TOS change. It has a very "linear" structure now. Not flexible at all.
"""
# Errors

GPT_HISTORY_ARGS = {
    "user": "root",
    "password": "\\15NavidRohim16/",
    "database": "chats",
    "host": "austinares.synology.me",
    "port": 3306
}

NO_CONVO = "You do not have a conversation with DeveloperJoe. Do /start to do such."
HAS_CONVO = 'You already have an ongoing conversation with DeveloperJoe. To reset, do "/stop."'
GENERIC_ERROR = "Unknown error, contact administrator."

DATABASE_FILE = "histories.db"

class gpt(commands.Cog):

    def __init__(self, client):
        self.client: DevJoe = client

        print(f"{self.__cog_name__} Loaded") 
    
    @discord.app_commands.command(name="start", description="Start a DeveloperJoe Session")
    @discord.app_commands.describe(name="The name of the chat you will start (Will be used when saving the transcript)")
    async def start(self, interaction: discord.Interaction, name: str=""):
        
        await interaction.response.defer(ephemeral=True, thinking=True)
        actual_name = name if name else f"{datetime.datetime.now()}-{interaction.user.display_name}"

        if len(actual_name) > 39:
            return await interaction.followup.send("The name of your chat must be less than 40 characters.")
        
        async def func():

            convo = GPTChat.GPTChat(interaction.user, actual_name)
            self.client.chats[interaction.user.id] = convo
            await interaction.followup.send(convo.start())

        if not self.client.get_user_conversation(interaction.user.id):
            return await func()

        await interaction.response.send_message(HAS_CONVO)

    @discord.app_commands.command(name="ask", description="Ask DeveloperJoe a question.")
    @discord.app_commands.describe(message="The query you want to send DeveloperJoe")
    async def ask(self, interaction: discord.Interaction, message: str):

        if convo := self.client.get_user_conversation(interaction.user.id):
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await interaction.followup.send(convo.ask(message))
        await interaction.response.send_message(NO_CONVO)

    @discord.app_commands.command(name="stop", description="Stop a DeveloperJoe session.")
    @discord.app_commands.describe(save="If you want to save your transcript.")
    @discord.app_commands.choices(save=[
        discord.app_commands.Choice(name="No, do not save my transcript save.", value="n"),
        discord.app_commands.Choice(name="Yes, please save my transcript.", value="y")
    ])
    async def stop(self, interaction: discord.Interaction, save: discord.app_commands.Choice[str]):
        
        # Actual command
        if save.value not in ["n", "y"]:
            return await interaction.response.send_message("You did not pick a save setting. Please pick one from the pre-selected options.")
            
        async def func(gpt: GPTChat.GPTChat):
            with GPTHistory.GPTHistory(DATABASE_FILE) as history:
                farewell, error = gpt.stop(history, save.value)
                await interaction.response.send_message(farewell)
                if error == 0:
                    del self.client.chats[interaction.user.id]
        
        # checks because app_commands cannot use normal ones.
        if convo := self.client.get_user_conversation(interaction.user.id):
            return await func(convo)
        await interaction.response.send_message(NO_CONVO)

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
                    r = NO_CONVO
            else:
                r = "Incorrect resolution setting. (Must be: 256x256, 512x512, 1024x1024)"
        except Exception as e:
            r = f"Uncaught Exception: {e}"

        finally:
            return await interaction.followup.send(r)
        
    @discord.app_commands.command(name="export", description="Export current chat history.")
    async def export_chat_history(self, interaction: discord.Interaction):
        if (convo := self.client.get_user_conversation(interaction.user.id)):

            def format(data: list) -> str:
                final = ""
                
                for entry in data:
                    final += f"{convo.user.name}: {entry[0]['content']}\nGPT 3.5: {entry[1]['content']}\n\n{'~' * 15}\n\n" \
                        if 'content' in entry[0] else f"{entry[0]['image']}\n{entry[1]['image_return']}\n\n{'~' * 15}\n\n"
                
                return final
            
            formatted_history_string = format(convo.readable_history)
            file_like = io.BytesIO(formatted_history_string.encode())
            file_like.name = f"{datetime.datetime.now()}-transcript.txt"

            await interaction.user.send(f"{convo.user.name}'s DeveloperJoe Transcript", file=discord.File(file_like))
            return await interaction.response.send_message("I have sent your conversation transcript to our direct messages.")
        
        await interaction.response.send_message(NO_CONVO)

    @discord.app_commands.command(name="info", description="Displays information about your current DeveloperJoe Chat.")
    async def get_info(self, interaction: discord.Interaction):
        if convo := self.client.get_user_conversation(interaction.user.id):
            
            returned_embed = discord.Embed(title="Chat Information")

            returned_embed.add_field(name="Started At", value=str(convo.time), inline=False)
            returned_embed.add_field(name="Used Tokens", value=f"{str(convo.tokens)} / 4096", inline=False)
            returned_embed.add_field(name="Chat Length", value=str(len(convo.chat_history)), inline=False)
            returned_embed.add_field(name="Chat ID", value=str(convo.id), inline=False)
            
            returned_embed.color = discord.Colour.purple()

            return await interaction.response.send_message(embed=returned_embed)
        
        await interaction.response.send_message(NO_CONVO) 

    @discord.app_commands.command(name="history", description="Get a past saved conversation.")
    async def get_history(self, interaction: discord.Interaction, history_id: int):
        with GPTHistory.GPTHistory(DATABASE_FILE) as history:
            if h_file := history.retrieve_chat_history(history_id):
                return await interaction.response.send_message(str(h_file))
            return await interaction.response.send_message(f"No history with the ID: {history_id}")

async def setup(client):
    await client.add_cog(gpt(client))
