import discord, datetime

from discord.ext import commands
from typing import Union
from joe import DevJoe
from objects import GPTChat, GPTHistory, GPTErrors, GPTConfig, GPTExceptions

yes_no_choice: list[discord.app_commands.Choice] = [
        discord.app_commands.Choice(name="Yes", value="y"),
        discord.app_commands.Choice(name="No", value="n")
]

def in_correct_channel(interaction: discord.Interaction) -> bool:
    return bool(interaction.channel) == True and bool(interaction.channel.guild if interaction.channel else False) and interaction.channel.type in GPTConfig.ALLOWED_INTERACTIONS # type: ignore

def is_member(interaction: discord.Interaction) -> bool:
    return isinstance(interaction.user, discord.Member)

class gpt(commands.Cog):

    def __init__(self, client):
        self.client: DevJoe = client
        print(f"{self.__cog_name__} Loaded") 

    @discord.app_commands.command(name="start", description=f"Start a {GPTConfig.BOT_NAME} Session")
    @discord.app_commands.describe(chat_name="The name of the chat you will start. If none is provided, your name and the amount of chats you have so far will be the name.", 
                                   stream_conversation="Weather the user wants the chat to appear gradually. (Like ChatGPT)",
                                   gpt_model="The model being used for the AI (GPT 3 or GPT 4)"
    )
    @discord.app_commands.choices(stream_conversation=yes_no_choice, gpt_model=GPTConfig.MODEL_CHOICES, in_thread=yes_no_choice)
    @discord.app_commands.check(in_correct_channel)
    @discord.app_commands.check(is_member)
    async def start(self, interaction: discord.Interaction, chat_name: Union[str, None]=None, stream_conversation: Union[str, None]=None, gpt_model: Union[str, None]=None, in_thread: Union[str, None]=None):
        actual_model: str = str(gpt_model if isinstance(gpt_model, str) else GPTConfig.DEFAULT_GPT_MODEL)

        async def command():
            try:
                
                actual_choice = True if stream_conversation == "y" else False
                actual_name = chat_name if chat_name else f"{datetime.datetime.now()}-{interaction.user.display_name}"
                chats = self.client.get_user_conversation(interaction.user.id, None, True)
                name = chat_name if chat_name else f"{interaction.user.name}-{len(chats) if isinstance(chats, dict) else '0'}"
                chat_thread: Union[discord.Thread, None] = None

                # Error Checking

                if len(actual_name) > 39:
                    return await interaction.response.send_message("The name of your chat must be less than 40 characters.", ephemeral=False)
                elif isinstance(chats, dict) and name in list(chats):
                    return await interaction.response.send_message(GPTErrors.ConversationErrors.HAS_CONVO, ephemeral=False)
                elif isinstance(chats, dict) and len(chats) > GPTConfig.CHATS_LIMIT:
                    return await interaction.response.send_message(GPTErrors.ConversationErrors.CONVO_LIMIT, ephemeral=False)
                
                # Actual Code


                if interaction.channel and interaction.channel.type == discord.ChannelType.text and in_thread == "y":
                    chat_thread = await interaction.channel.create_thread(name=name, message=None, auto_archive_duration=1440, type=discord.ChannelType.private_thread, reason=f"{interaction.user.id} created a private DeveloperJoe Thread.", invitable=True, slowmode_delay=None) # type: ignore
                    await chat_thread.add_user(interaction.user)
                    await chat_thread.send(f"{interaction.user.mention} Here I am! Feel free to chat privately with me here. I am still processing your chat request. So please wait a few moments.")

                convo = GPTChat.GPTChat(self.client, interaction.user, actual_name, name, actual_model, chat_thread)
                convo.stream = actual_choice

                await interaction.response.defer(ephemeral=False, thinking=True)
                await interaction.followup.send(f"{await convo.start()}\n\n*Conversation Name — {name} | Model — {actual_model} | Thread — {chat_thread.name if chat_thread else 'No thread made.'}*", ephemeral=False)

                self.client.add_conversation(interaction.user, name, convo)
                self.client.set_default_conversation(interaction.user, name)

            except Exception as e:
                await self.client.send_debug_message(interaction, e, self.__cog_name__)
        
        if self.client.get_user_has_permission(interaction.user, actual_model) and interaction.channel: # type: ignore
            return await command()
        await interaction.response.send_message(GPTErrors.ModelErrors.MODEL_LOCKED)
        
    @discord.app_commands.command(name="ask", description=f"Ask {GPTConfig.BOT_NAME} a question.")
    @discord.app_commands.describe(message=f"The query you want to send {GPTConfig.BOT_NAME}", name="The name of the chat you want to interact with. If no name is provided, it will use the default first chat name (Literal number 0)", stream="Weather or not you want the chat to appear overtime.")
    @discord.app_commands.choices(stream=yes_no_choice)
    @discord.app_commands.check(in_correct_channel)
    @discord.app_commands.check(is_member)
    async def ask(self, interaction: discord.Interaction, message: str, name: Union[None, str]=None, stream: Union[str, None]=None):
            try:
                name = self.client.manage_defaults(interaction.user, name)
                if interaction.channel and interaction.channel.type in GPTConfig.ALLOWED_INTERACTIONS:
                    if isinstance(convo := self.client.get_user_conversation(interaction.user.id, name), GPTChat.GPTChat):
                        if self.client.get_user_has_permission(interaction.user, convo.model): # type: ignore

                            header_text = f'{name} | {convo.model}'

                            if stream == "y" or (convo.stream == True and stream != "n"):
                                await interaction.response.send_message("Asking...", ephemeral=False)
                                
                                msg: list[discord.Message] = []
                                reply = convo.ask_stream(message)
                                full_message = f"## {header_text}\n\n"
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
                                
                            await interaction.response.defer(ephemeral=False, thinking=True)
                            reply = await convo.ask(message)
                            final_user_reply = f"## {header_text}\n\n{reply}"

                            if len(final_user_reply) > GPTConfig.CHARACTER_LIMIT:
                                file_reply: discord.File = self.client.to_file(final_user_reply, "reply.txt")
                                return await interaction.followup.send(file=file_reply, ephemeral=False)
                            return await interaction.followup.send(final_user_reply, ephemeral=False)
                        
                        else:
                            await interaction.response.send_message(GPTErrors.ModelErrors.MODEL_LOCKED) 
                    else:
                        await interaction.response.send_message(GPTErrors.ConversationErrors.NO_CONVO, ephemeral=False)
                else:
                    await interaction.response.send_message(GPTErrors.ConversationErrors.CANNOT_CONVO, ephemeral=False)
            
            except Exception as e:
                await self.client.send_debug_message(interaction, e, self.__cog_name__) 
                  

    @discord.app_commands.command(name="stop", description=f"Stop a {GPTConfig.BOT_NAME} session.")
    @discord.app_commands.describe(save="If you want to save your transcript.", name="The name of the chat you want to end. This is NOT optional as this is a destructive command.")
    @discord.app_commands.choices(save=[
        discord.app_commands.Choice(name="No, do not save my transcript save.", value="n"),
        discord.app_commands.Choice(name="Yes, please save my transcript.", value="y")
    ])
    async def stop(self, interaction: discord.Interaction, save: discord.app_commands.Choice[str], name: str):
        
        # TODO: Fix broken chat name checking.
        
        if save.value not in ["n", "y"]:
            return await interaction.response.send_message("You did not pick a save setting. Please pick one from the pre-selected options.", ephemeral=False)
        
        async def func(gpt: GPTChat.GPTChat):
            try:
                with GPTHistory.GPTHistory() as history:
        
                    if self.client.get_user_conversation(interaction.user.id, name, True):
                        reply = await self.client.get_confirmation(interaction, f'Are you sure you want to end {name}? (Send reply within {GPTConfig.QUERY_TIMEOUT} seconds, and "{GPTConfig.QUERY_CONFIRMATION}" to confirm, anything else to cancel.')
                        if reply.content != GPTConfig.QUERY_CONFIRMATION:
                            return await interaction.followup.send("Cancelled action.", ephemeral=False)
                        
                        farewell = await gpt.stop(interaction, history, save.value)
                        
                        await interaction.followup.send(farewell, ephemeral=False)
                        self.client.delete_conversation(interaction.user, name)
                        self.client.set_default_conversation(interaction.user, None, True)
                    else:
                        await interaction.followup.send(GPTErrors.ConversationErrors.NO_CONVO_WITH_NAME, ephemeral=False)
            except GPTExceptions.CannotDeleteThread as e:
                return await interaction.response.send_message(e.args[0])
            
        # checks because app_commands cannot use normal ones.
        if isinstance(convo := self.client.get_user_conversation(interaction.user.id, name), GPTChat.GPTChat):
            return await func(convo)
        await interaction.response.send_message(GPTErrors.ConversationErrors.NO_CONVO, ephemeral=False)

    @discord.app_commands.command(name="generate", description="Create an image with specified parameters.")
    @discord.app_commands.describe(prompt=f"The keyword you want {GPTConfig.BOT_NAME} to describe.", resolution="Resolution of the final image.", save_to="What chat you want to save the image history too. (For exporting)")
    @discord.app_commands.choices(resolution=[
        discord.app_commands.Choice(name="256x256", value="256x256"),
        discord.app_commands.Choice(name="512x512", value="512x512"),
        discord.app_commands.Choice(name="1024x1024", value="1024x1024")
    ]) 
    async def image_generate(self, interaction: discord.Interaction, prompt: str, resolution: str, save_to: Union[None, str]=None):
        save_to = self.client.manage_defaults(interaction.user, save_to)
        r = GPTErrors.GENERIC_ERROR
        try:
            await interaction.response.defer(ephemeral=True, thinking=True)

            if resolution in ["256x256", "512x512", "1024x1024"]:
                if isinstance(convo := self.client.get_user_conversation(interaction.user.id, save_to), GPTChat.GPTChat):
                    r = str(await convo.__send_query__(query_type="image", prompt=prompt, size=resolution, n=1))
                else:
                    r = GPTErrors.ConversationErrors.NO_CONVO
            else:
                r = "Incorrect resolution setting. (Must be: 256x256, 512x512, 1024x1024)"
        except Exception as e:
            r = f"Uncaught Exception: {e}"

        finally:
            return await interaction.followup.send(r, ephemeral=False)

    @discord.app_commands.command(name="info", description=f"Displays information about your current {GPTConfig.BOT_NAME} Chat.")
    @discord.app_commands.describe(name="Name of the chat you want information on.")
    async def get_info(self, interaction: discord.Interaction, name: Union[None, str]=None):
        
        name = self.client.manage_defaults(interaction.user, name)
        if isinstance(convo := self.client.get_user_conversation(interaction.user.id, name), GPTChat.GPTChat) and self.client.application:

            uptime_delta = self.client.get_uptime()
            returned_embed = discord.Embed(title=f"{name if name != '0' else 'Conversation'} Information")

            returned_embed.add_field(name="Started At", value=str(convo.time), inline=False)
            returned_embed.add_field(name="Used Tokens", value=f"{str(convo.tokens)}", inline=False)
            returned_embed.add_field(name="Chat Length", value=str(len(convo.chat_history)), inline=False)
            returned_embed.add_field(name="Chat History ID", value=str(convo.hid), inline=False)
            returned_embed.add_field(name="Chat ID", value=str(convo.display_name), inline=False)
            returned_embed.add_field(name=f"{self.client.application.name} Uptime", value=f"{uptime_delta.days} Days ({uptime_delta})", inline=False)
            returned_embed.add_field(name=f"{self.client.application.name} Version", value=f"{GPTConfig.VERSION}", inline=False)
            
            returned_embed.color = discord.Colour.purple()

            return await interaction.response.send_message(embed=returned_embed, ephemeral=False)
        
        await interaction.response.send_message(GPTErrors.ConversationErrors.NO_CONVO, ephemeral=False)  

    @discord.app_commands.command(name="switch", description="Changes your default chat. This is a convenience command.")
    @discord.app_commands.describe(name="Name of the chat you want to switch to.")
    async def switch_default(self, interaction: discord.Interaction, name: Union[None, str]=None):
        name = self.client.manage_defaults(interaction.user, name)
        await interaction.response.send_message(f"Switched default chat to: {name} (The name will not change or be set to default if the chat does not exist)" if name else f"You do not have any {GPTConfig.BOT_NAME} conversations.")

async def setup(client):
    await client.add_cog(gpt(client))
