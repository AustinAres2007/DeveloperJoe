import discord, datetime

from discord.ext import commands
from typing import Union
from joe import DevJoe
from objects import GPTChat, GPTHistory, GPTErrors, GPTConfig

stream_choices = [
        discord.app_commands.Choice(name="Yes", value="y"),
        discord.app_commands.Choice(name="No", value="n")
]

class gpt(commands.Cog):

    def __init__(self, client):
        self.client: DevJoe = client
        print(f"{self.__cog_name__} Loaded") 
    
    @discord.app_commands.command(name="start", description="Start a DeveloperJoe Session")
    @discord.app_commands.describe(name="The name of the chat you will start (Will be used when saving the transcript)")
    @discord.app_commands.choices(stream_conversation=stream_choices)
    async def start(self, interaction: discord.Interaction, name: str="", stream_conversation: Union[str, None]=None):
        actual_choice = True if stream_conversation == "y" else False
        try:
            actual_name = name if name else f"{datetime.datetime.now()}-{interaction.user.display_name}"

            if len(actual_name) > 39:
                return await interaction.followup.send("The name of your chat must be less than 40 characters.", ephemeral=False)
    
            async def func():
                convo = GPTChat.GPTChat(interaction.user, actual_name)
                convo.stream = actual_choice

                await interaction.response.defer(ephemeral=True, thinking=True)
                await interaction.followup.send(await convo.start(), ephemeral=False)
                self.client.chats[interaction.user.id] = convo

            if not self.client.get_user_conversation(interaction.user.id):
                return await func()

            await interaction.response.send_message(GPTErrors.ConversationErrors.HAS_CONVO, ephemeral=False)
        except Exception as e:
            await self.client.send_debug_message(interaction, e)

    @discord.app_commands.command(name="ask", description="Ask DeveloperJoe a question.")
    @discord.app_commands.describe(message="The query you want to send DeveloperJoe")
    @discord.app_commands.choices(stream=stream_choices)
    async def ask(self, interaction: discord.Interaction, message: str, stream: Union[str, None]=None):
        try:
            if interaction.channel and interaction.channel.type in [discord.ChannelType.private_thread, discord.ChannelType.text, discord.ChannelType.private, discord.TextChannel]:
                if convo := self.client.get_user_conversation(interaction.user.id):
                    if stream == "y" or (convo.stream == True and stream != "n"):
                        await interaction.response.send_message("Asking...", ephemeral=False)
                        
                        msg: list[discord.Message] = []
                        reply = convo.ask_stream(message)
                        full_message = ""
                        i, start_message_at = 0, 0
                        sendable_portion = "<>"

                        async for t in reply:
                            i += 1
                            full_message += t
                            sendable_portion = full_message[start_message_at * GPTConfig.CHARACTER_LIMIT:((start_message_at + 1) * GPTConfig.CHARACTER_LIMIT)]

                            if len(full_message) and len(full_message) >= (start_message_at + 1) * GPTConfig.CHARACTER_LIMIT:
                                if not msg:
                                    await interaction.edit_original_response(content=sendable_portion)
                                    msg.append(await interaction.channel.send(":)")) # type: ignore
                                else:
                                    await msg[-1].edit(content=sendable_portion)
                                    msg.append(await msg[-1].channel.send(":)"))

                            start_message_at = len(full_message) // GPTConfig.CHARACTER_LIMIT
                            if i and i % GPTConfig.STREAM_UPDATE_MESSAGE_FREQUENCY == 0:
                                if not msg:
                                    await interaction.edit_original_response(content=sendable_portion)
                                else:
                                    await msg[-1].edit(content=sendable_portion)

                        else:
                            if not msg:
                                return await interaction.edit_original_response(content=sendable_portion)
                            return await msg[-1].edit(content=sendable_portion)
                    await interaction.response.defer(ephemeral=True, thinking=True)
                    reply = await convo.ask(message)

                    if len(reply) > GPTConfig.CHARACTER_LIMIT:
                        file_reply: discord.File = self.client.to_file(reply, "reply.txt")
                        return await interaction.followup.send(file=file_reply, ephemeral=False)
                    return await interaction.followup.send(reply, ephemeral=False)
                await interaction.response.send_message(GPTErrors.ConversationErrors.NO_CONVO, ephemeral=False)
            else:
                await interaction.response.send_message(GPTErrors.ConversationErrors.CANNOT_CONVO, ephemeral=False)
        
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
            return await interaction.response.send_message("You did not pick a save setting. Please pick one from the pre-selected options.", ephemeral=False)
        
        reply = await self.client.get_confirmation(interaction, f'Are you sure you want to end this chat? (Send reply within {GPTConfig.QUERY_TIMEOUT} seconds, and "{GPTConfig.QUERY_CONFIRMATION}" to confirm, anything else to cancel.')
        if reply.content != GPTConfig.QUERY_CONFIRMATION:
            return await interaction.followup.send("Cancelled action.", ephemeral=False)
        
        async def func(gpt: GPTChat.GPTChat):
            with GPTHistory.GPTHistory() as history:
                farewell = gpt.stop(history, save.value)
                await interaction.followup.send(farewell, ephemeral=False)
                if not farewell.startswith("Critical Error:"):
                    del self.client.chats[interaction.user.id]
        
        # checks because app_commands cannot use normal ones.
        if convo := self.client.get_user_conversation(interaction.user.id):
            return await func(convo)
        await interaction.followup.send(GPTErrors.ConversationErrors.NO_CONVO, ephemeral=False)

    @discord.app_commands.command(name="generate", description="Create an image with specified parameters.")
    @discord.app_commands.describe(prompt="The keyword you want DeveloperJoe to describe.", resolution="Resolution of the final image.")
    @discord.app_commands.choices(resolution=[
        discord.app_commands.Choice(name="256x256", value="256x256"),
        discord.app_commands.Choice(name="512x512", value="512x512"),
        discord.app_commands.Choice(name="1024x1024", value="1024x1024")
    ]) 
    async def image_generate(self, interaction: discord.Interaction, prompt: str, resolution: str):
        r = GPTErrors.GENERIC_ERROR
        try:
            await interaction.response.defer(ephemeral=True, thinking=True)

            if resolution in ["256x256", "512x512", "1024x1024"]:
                if convo := self.client.get_user_conversation(interaction.user.id):
                    r = str(await convo.__send_query__(query_type="image", prompt=prompt, size=resolution, n=1))
                else:
                    r = GPTErrors.ConversationErrors.NO_CONVO
            else:
                r = "Incorrect resolution setting. (Must be: 256x256, 512x512, 1024x1024)"
        except Exception as e:
            r = f"Uncaught Exception: {e}"

        finally:
            return await interaction.followup.send(r, ephemeral=False)

    @discord.app_commands.command(name="info", description="Displays information about your current DeveloperJoe Chat.")
    async def get_info(self, interaction: discord.Interaction):
        if convo := self.client.get_user_conversation(interaction.user.id):
            
            uptime_delta = self.client.get_uptime()
            returned_embed = discord.Embed(title="Chat Information")

            returned_embed.add_field(name="Started At", value=str(convo.time), inline=False)
            returned_embed.add_field(name="Used Tokens", value=f"{str(convo.tokens)}", inline=False)
            returned_embed.add_field(name="Chat Length", value=str(len(convo.chat_history)), inline=False)
            returned_embed.add_field(name="Chat ID", value=str(convo.id), inline=False)
            returned_embed.add_field(name=f"{self.client.application.name} Uptime", value=f"{uptime_delta.days} Days ({uptime_delta})", inline=False)
            returned_embed.add_field(name=f"{self.client.application.name} Version", value=f"{GPTConfig.VERSION}", inline=False)
            
            returned_embed.color = discord.Colour.purple()

            return await interaction.response.send_message(embed=returned_embed, ephemeral=False)
        
        await interaction.response.send_message(GPTErrors.ConversationErrors.NO_CONVO, ephemeral=False)  

async def setup(client):
    await client.add_cog(gpt(client))
