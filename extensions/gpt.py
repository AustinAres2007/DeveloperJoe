import discord, datetime

from discord.ext import commands
from typing import Union

from joe import *
from sources import *
yes_no_choice: list[discord.app_commands.Choice] = [
        discord.app_commands.Choice(name="Yes", value="y"),
        discord.app_commands.Choice(name="No", value="n")
]

class gpt(commands.Cog):

    def __init__(self, client):
        self.client: DeveloperJoe = client
        print(f"{self.__cog_name__} Loaded") 

    @discord.app_commands.command(name="start", description=f"Start a {BOT_NAME} Session")
    @discord.app_commands.describe(chat_name="The name of the chat you will start. If none is provided, your name and the amount of chats you have so far will be the name.", 
                                   stream_conversation="Weather the user wants the chat to appear gradually. (Like ChatGPT)",
                                   gpt_model="The model being used for the AI (GPT 3 or GPT 4)"
    )
    @discord.app_commands.choices(stream_conversation=yes_no_choice, gpt_model=MODEL_CHOICES, in_thread=yes_no_choice, speak_reply=yes_no_choice)
    async def start(self, interaction: discord.Interaction, chat_name: Union[str, None]=None, stream_conversation: Union[str, None]=None, gpt_model: Union[str, None]=None, in_thread: Union[str, None]=None, speak_reply: Union[str, None]=None):
        
        member: discord.Member = utils.assure_class_is_value(interaction.user, discord.Member)
        channel: discord.TextChannel = utils.assure_class_is_value(interaction.channel, discord.TextChannel)
        actual_model = utils.get_modeltype_from_name(str(gpt_model if isinstance(gpt_model, str) else DEFAULT_GPT_MODEL.model))
        
        async def command():
            
            actual_choice = True if stream_conversation == "y" else False
            actual_name = chat_name if chat_name else f"{datetime.datetime.now()}-{member.display_name}"
            chats = self.client.get_all_user_conversations(member)
            name = chat_name if chat_name else f"{member.name}-{len(chats) if isinstance(chats, dict) else '0'}"
            chat_thread: Union[discord.Thread, None] = None

            # Error Checking

            if len(actual_name) > 39:
                raise DGException("The name of your chat must be less than 40 characters.", len(actual_name))
            elif isinstance(chats, dict) and name in list(chats):
                raise DGException(ConversationErrors.HAS_CONVO)
            elif isinstance(chats, dict) and len(chats) > CHATS_LIMIT:
                raise DGException(ConversationErrors.CONVO_LIMIT)
            
            # Actual Code
            
            if in_thread == "y":
                chat_thread = await channel.create_thread(name=name, message=None, auto_archive_duration=1440, type=discord.ChannelType.private_thread, reason=f"{member.id} created a private DeveloperJoe Thread.", invitable=True, slowmode_delay=None)
                await chat_thread.add_user(member)
                await chat_thread.send(f"{member.mention} Here I am! Feel free to chat privately with me here. I am still processing your chat request. So please wait a few moments.")

            chat_args = (self.client, self.client._OPENAI_TOKEN, member, actual_name, actual_choice, name, actual_model, chat_thread)
            
            if speak_reply != "y":
                convo = DGTextChat(*chat_args)
            elif speak_reply == "y" and self.client.has_ffmpeg:
                convo = DGVoiceChat(*chat_args, voice=member.voice.channel if member.voice else None)
            elif speak_reply == "y" and self.client.has_ffmpeg == False:
                raise FFMPEGNotInstalled(self.client.has_ffmpeg)
            else:
                convo = DGTextChat(*chat_args)
            
            await interaction.response.defer(ephemeral=False, thinking=True)
            await interaction.followup.send(f"{await convo.start()}\n\n*Conversation Name — {name} | Model — {actual_model.display_name} | Thread — {chat_thread.name if chat_thread else 'No thread made.'} | Voice — {'Yes' if speak_reply == 'y' else 'No'}*", ephemeral=False)

            self.client.add_conversation(member, name, convo)
            self.client.set_default_conversation(member, name)
    
        if self.client.get_user_has_permission(member, actual_model):
            return await command()
        raise ModelIsLockedError(actual_model)
        
    @discord.app_commands.command(name="ask", description=f"Ask {BOT_NAME} a question.")
    @discord.app_commands.describe(message=f"The query you want to send {BOT_NAME}", name="The name of the chat you want to interact with. If no name is provided, it will use the default first chat name (Literal number 0)", stream="Weather or not you want the chat to appear overtime.")
    @discord.app_commands.choices(stream=yes_no_choice)
    async def ask(self, interaction: discord.Interaction, message: str, name: Union[None, str]=None, stream: Union[str, None]=None):

            member: discord.Member = utils.assure_class_is_value(interaction.user, discord.Member)
            channel: discord.TextChannel = utils.assure_class_is_value(interaction.channel, discord.TextChannel)
            name = self.client.manage_defaults(member, name)
            
            if channel and channel.type in ALLOWED_INTERACTIONS: # Check if in right channel
                if convo := self.client.get_user_conversation(member, name): # Check if user has a conversation 
                    if self.client.get_user_has_permission(member, convo.model): # If user has model permission

                        header_text = f'{name} | {convo.model.display_name}'
                        final_message_reply = ""
                        
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
                                final_message_reply += t
                                
                                sendable_portion = full_message[start_message_at * CHARACTER_LIMIT:((start_message_at + 1) * CHARACTER_LIMIT)]
                        
                                if len(full_message) and len(full_message) >= (start_message_at + 1) * CHARACTER_LIMIT:
                                    if not msg:
                                        await interaction.edit_original_response(content=sendable_portion)
                                        msg.append(await channel.send(":)"))
                                    else:
                                        await msg[-1].edit(content=sendable_portion)
                                        msg.append(await msg[-1].channel.send(":)"))

                                start_message_at = len(full_message) // CHARACTER_LIMIT
                                if i and i % STREAM_UPDATE_MESSAGE_FREQUENCY == 0:
                                    if not msg:
                                        await interaction.edit_original_response(content=sendable_portion)
                                    else:
                                        await msg[-1].edit(content=sendable_portion)

                            else:
                                if not msg:
                                    await interaction.edit_original_response(content=sendable_portion)
                                else:
                                    await msg[-1].edit(content=sendable_portion)
                                
                        else:         
                            
                            await interaction.response.defer(ephemeral=False, thinking=True)
                            final_message_reply = reply = await convo.ask(message)
                            final_user_reply = f"## {header_text}\n\n{reply}"
                            
                            if len(final_user_reply) > CHARACTER_LIMIT:
                                file_reply: discord.File = utils.to_file(final_user_reply, "reply.txt")
                                await interaction.followup.send(file=file_reply, ephemeral=False)
                            else:
                                await interaction.followup.send(final_user_reply, ephemeral=False)

                    
                        if isinstance(convo, DGVoiceChat):
                            await convo.speak(final_message_reply)
                        return
                        
                    else:
                        await interaction.response.send_message(ModelErrors.MODEL_LOCKED) 
                else:
                    await interaction.response.send_message(ConversationErrors.NO_CONVO, ephemeral=False)
            else:
                await interaction.response.send_message(ConversationErrors.CANNOT_CONVO, ephemeral=False) 
                  

    @discord.app_commands.command(name="stop", description=f"Stop a {BOT_NAME} session.")
    @discord.app_commands.describe(save="If you want to save your transcript.", name="The name of the chat you want to end. This is NOT optional as this is a destructive command.")
    @discord.app_commands.choices(save=[
        discord.app_commands.Choice(name="No, do not save my transcript save.", value="n"),
        discord.app_commands.Choice(name="Yes, please save my transcript.", value="y")
    ])
    async def stop(self, interaction: discord.Interaction, save: discord.app_commands.Choice[str], name: str):
        member: discord.Member = utils.assure_class_is_value(interaction.user, discord.Member)
        
        async def func(gpt: DGTextChat):
            with DGHistorySession() as history:
    
                if self.client.get_all_user_conversations(member):
                    reply = await self.client.get_confirmation(interaction, f'Are you sure you want to end {name}? (Send reply within {QUERY_TIMEOUT} seconds, and "{QUERY_CONFIRMATION}" to confirm, anything else to cancel.')
                    if reply.content != QUERY_CONFIRMATION:
                        return await interaction.followup.send("Cancelled action.", ephemeral=False)
                    
                    farewell = await gpt.stop(interaction, history, save.value)
                    
                    self.client.delete_conversation(member, name)
                    self.client.set_default_conversation(member, None)
                    await interaction.followup.send(farewell, ephemeral=False)
                else:
                    await interaction.followup.send(ConversationErrors.NO_CONVO_WITH_NAME, ephemeral=False)
            
        # checks because app_commands cannot use normal ones.
        if convo := self.client.get_user_conversation(member, name):
            return await func(convo)
        else:
            raise UserDoesNotHaveChat(name)

    @discord.app_commands.command(name="generate", description="Create an image with specified parameters.")
    @discord.app_commands.describe(prompt=f"The keyword you want {BOT_NAME} to describe.", resolution="Resolution of the final image.", save_to="What chat you want to save the image history too. (For exporting)")
    @discord.app_commands.choices(resolution=[
        discord.app_commands.Choice(name="256x256", value="256x256"),
        discord.app_commands.Choice(name="512x512", value="512x512"),
        discord.app_commands.Choice(name="1024x1024", value="1024x1024")
    ]) 
    async def image_generate(self, interaction: discord.Interaction, prompt: str, resolution: str, save_to: Union[None, str]=None):
        member: discord.Member = utils.assure_class_is_value(interaction.user, discord.Member)
        save_to = self.client.manage_defaults(member, save_to)

        await interaction.response.defer(ephemeral=True, thinking=True)

        if resolution in ["256x256", "512x512", "1024x1024"]:
            if convo := self.client.get_user_conversation(member, save_to):
                result = str(await convo.__send_query__(query_type="image", prompt=prompt, size=resolution, n=1))
            else:
                result = ConversationErrors.NO_CONVO
        else:
            result = "Incorrect resolution setting. (Must be: 256x256, 512x512, 1024x1024)"

        return await interaction.followup.send(result, ephemeral=False)

    @discord.app_commands.command(name="info", description=f"Displays information about your current {BOT_NAME} Chat.")
    @discord.app_commands.describe(name="Name of the chat you want information on.")
    async def get_info(self, interaction: discord.Interaction, name: Union[None, str]=None):
        member: discord.Member = utils.assure_class_is_value(interaction.user, discord.Member)
        name = self.client.manage_defaults(member, name)

        if isinstance(convo := self.client.get_user_conversation(member, name), DGTextChat) and self.client.application:

            uptime_delta = self.client.get_uptime()
            returned_embed = discord.Embed(title=f'"{name}" Information')

            embeds = (
                {"name": "Started At", "value": str(convo.time), "inline": False},
                {"name": "Used Tokens", "value": str(convo.tokens), "inline": False},
                {"name": "Chat Length", "value": str(len(convo.chat_history)), "inline": False},
                {"name": "Chat History ID", "value": str(convo.hid), "inline": False},
                {"name": "Chat ID", "value": str(convo.display_name), "inline": False},
                {"name": "Is Active", "value": str(convo.is_active), "inline": False},
                {"name": "GPT Model", "value": str(convo.model.display_name), "inline": False},
                {"name": "Is Voice", "value": f"Yes" if isinstance(convo, DGVoiceChat) else "No", "inline": False},
                {"name": f"{self.client.application.name} Version", "value": VERSION, "inline": False},
                {"name": f"{self.client.application.name} Uptime", "value": f"{uptime_delta.days} Days ({uptime_delta})", "inline": False}
            )
            for embed in embeds:
                returned_embed.add_field(**embed)
            returned_embed.color = discord.Colour.purple()

            return await interaction.response.send_message(embed=returned_embed, ephemeral=False)
        
        raise UserDoesNotHaveChat(name)
    
    @discord.app_commands.command(name="switch", description="Changes your default chat. This is a convenience command.")
    @discord.app_commands.describe(name="Name of the chat you want to switch to.")
    async def switch_default(self, interaction: discord.Interaction, name: Union[None, str]=None):
        member: discord.Member = utils.assure_class_is_value(interaction.user, discord.Member)
        name = self.client.manage_defaults(member, name)
        await interaction.response.send_message(f"Switched default chat to: {name} (The name will not change or be set to default if the chat does not exist)" if name else f"You do not have any {BOT_NAME} conversations.")

    @discord.app_commands.command(name="shutup", description=f"If you have a {BOT_NAME} voice chat and you want it to stop talking a reply, execute this command.")
    async def shutup_reply(self, interaction: discord.Interaction):
        member: discord.Member = utils.assure_class_is_value(interaction.user, discord.Member)
        default_chat = self.client.get_default_conversation(member)
        if default_chat and isinstance(default_chat, DGVoiceChat):
            default_chat.stop_speaking()
            return await interaction.response.send_message(f"I have shut up.")
        elif default_chat:
            raise ChatIsTextOnly(default_chat)
        else:
            raise UserDoesNotHaveChat(str(default_chat))

    @discord.app_commands.command(name="pause", description="Paused the bots voice reply.")
    async def pause_reply(self, interaction: discord.Interaction):
        member: discord.Member = utils.assure_class_is_value(interaction.user, discord.Member)
        default_chat = self.client.get_default_conversation(member)
        
        if default_chat and isinstance(default_chat, DGVoiceChat):
            default_chat.pause_speaking()
            return await interaction.response.send_message(f"I have paused my reply.")
        elif default_chat:
            raise ChatIsTextOnly(default_chat)
        else:
            raise UserDoesNotHaveChat(str(default_chat))
    
    @discord.app_commands.command(name="resume", description="Resues the bots voice reply.")
    async def resume_reply(self, interaction: discord.Interaction):
        member: discord.Member = utils.assure_class_is_value(interaction.user, discord.Member)
        default_chat = self.client.get_default_conversation(member)
        
        if default_chat and isinstance(default_chat, DGVoiceChat):
            default_chat.resume_speaking()
            return await interaction.response.send_message(f"Speaking...")
        elif default_chat:
            raise ChatIsTextOnly(default_chat)
        else:
            raise UserDoesNotHaveChat(str(default_chat))
        
async def setup(client):
    await client.add_cog(gpt(client))
