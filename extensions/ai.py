from email.mime import image
import discord, datetime

from discord.ext import commands
from typing import Union

# Local dependencies

from joe import DeveloperJoe

from sources import (
    exceptions, 
    chat,
    errors,
    confighandler
)
from sources.common import (
    commands_utils,
    developerconfig,
    types
)

class Communication(commands.Cog):

    def __init__(self, _client: DeveloperJoe):
        self.client = _client
        print(f"{self.__cog_name__} Loaded") 

    chat_group = discord.app_commands.Group(name="chat", description="Chat command group. All subcommands relate to starting or managing chats.")
    @chat_group.command(name="start", description=f"Start a {confighandler.get_config('bot_name')} Session")
    @discord.app_commands.describe(chat_name="The name of the chat you will start. If none is provided, your name and the amount of chats you have so far will be the name.", 
                                   stream_conversation="Weather the user wants the chat to appear gradually. (Like ChatGPT)",
                                   ai_model="The model being used for the AI.",
                                   in_thread=f"If you want a dedicated private thread to talk with {confighandler.get_config('bot_name')} in.",
                                   speak_reply=f"Weather you want voice mode on. If so, join a voice channel, and {confighandler.get_config('bot_name')} will join and speak your replies.",
                                   is_private="Weather you want other users to access the chats transcript if and when it is stopped and saved. It is public by default."
                                   
    )
    @discord.app_commands.choices(ai_model=developerconfig.MODEL_CHOICES)
    async def start(self, interaction: discord.Interaction, chat_name: Union[str, None]=None, stream_conversation: bool=False, ai_model: str | None=None, in_thread: bool=False, speak_reply: bool=False, is_private: bool=False):
        
        member: discord.Member = commands_utils.assure_class_is_value(interaction.user, discord.Member)
        channel: developerconfig.InteractableChannel = commands_utils.is_correct_channel(interaction.channel)
    
        actual_name = chat_name if chat_name else f"{datetime.datetime.now()}-{member.display_name}"
        chats = self.client.get_all_user_conversations(member)
        name = chat_name if chat_name else f"{member.name}-{len(chats) if isinstance(chats, dict) else '0'}"
        chat_thread: discord.Thread | None = None
        ai_model = ai_model if isinstance(ai_model, str) else confighandler.GuildConfigAttributes.get_guild_model(member.guild)
        
        # Error Checking

        if len(actual_name) > 39:
            raise exceptions.ConversationError("The name of your chat must be less than 40 characters.", len(actual_name))
        elif isinstance(chats, dict) and name in list(chats):
            raise exceptions.ConversationError(errors.ConversationErrors.HAS_CONVO)
        elif isinstance(chats, dict) and len(chats) > developerconfig.CHATS_LIMIT:
            raise exceptions.ConversationError(errors.ConversationErrors.CONVO_LIMIT)
        
        # Actual Code
        
        if in_thread and type(channel) == discord.TextChannel:
            chat_thread = await channel.create_thread(name=name, message=None, auto_archive_duration=1440, type=discord.ChannelType.private_thread, reason=f"{member.id} created a private DeveloperJoe Thread.", invitable=True, slowmode_delay=None)
            await chat_thread.add_user(member)
            await chat_thread.send(f"{member.mention} Here I am! Feel free to chat privately with me here.")
                
        chat_args = (member, self.client, actual_name, stream_conversation, name, ai_model, chat_thread, is_private)
        
        if speak_reply == False:
            convo = chat.DGTextChat(*chat_args)
        elif speak_reply and self.client.is_voice_compatible == False:
            raise exceptions.VoiceError(errors.VoiceConversationErrors.NO_VOICE)
        elif speak_reply and interaction.guild and confighandler.get_guild_config_attribute(interaction.guild, "voice-enabled") == False:
            raise exceptions.VoiceError(errors.VoiceConversationErrors.VOICE_IS_LOCKED)
        elif speak_reply and self.client.is_voice_compatible:
            convo = chat.DGVoiceChat(*chat_args, voice=member.voice.channel if member.voice else None)
        else:
            convo = chat.DGTextChat(*chat_args)
        
        await interaction.response.defer(ephemeral=is_private, thinking=True)
        await convo.start()
            
        welcome = f"*Conversation Name — {name} | Model — {convo.model.display_name} | Thread — {chat_thread.name if chat_thread else 'No thread made either because the user denied it, or this chat was started in a thread.'} | Voice — {'Yes' if speak_reply == True else 'No'} | Private - {'Yes' if is_private == True else 'No'}*"
        await interaction.followup.send(welcome, ephemeral=is_private)
        
    @chat_group.command(name="ask", description=f"Ask {confighandler.get_config('bot_name')} a question.")
    @discord.app_commands.describe(message=f"The query you want to send {confighandler.get_config('bot_name')}", name="The name of the chat you want to interact with. If no name is provided, it will use the default first chat name (Literal number 0)", stream="Weather or not you want the chat to appear overtime.")
    async def ask_query(self, interaction: discord.Interaction, message: str, name: str="", stream: bool | None=None):

            member: discord.Member = commands_utils.assure_class_is_value(interaction.user, discord.Member)
            channel = commands_utils.get_correct_channel(interaction.channel) # Check if in right channel
            conversation = self.client.manage_defaults(member, name)
            status = f'/help and "{message}"'

            await interaction.response.send_message("Thinking..", ephemeral=conversation.private)
            
            self.client.add_status(status, 2) if not conversation.private else None
            if stream == True or (conversation.stream == True and stream != False):
                await conversation.ask_stream(message, channel)
            else:
                await conversation.ask(message, channel)
            
            self.client.remove_status(status)
            return await interaction.delete_original_response()
            
    @chat_group.command(name="stop", description=f"Stop a {confighandler.get_config('bot_name')} session.")
    @discord.app_commands.describe(save_chat="If you want to save your transcript.", name="The name of the chat you want to end. This is NOT optional as this is a destructive command.")
    async def stop(self, interaction: discord.Interaction, name: str, save_chat: bool=False):
        member: discord.Member = commands_utils.assure_class_is_value(interaction.user, discord.Member)
        
        # checks because app_commands cannot use normal ones.
        if convo := self.client.get_user_conversation(member, name):
            reply = await self.client.get_input(interaction, f'Are you sure you want to end {name}? (Send reply within {developerconfig.QUERY_TIMEOUT} seconds, and "{developerconfig.QUERY_CONFIRMATION}" to confirm, anything else to cancel.')
            if not reply or reply.content != developerconfig.QUERY_CONFIRMATION:
                return await interaction.followup.send("Cancelled action.", ephemeral=False)
            
            farewell = await convo.stop(interaction, save_chat)
            await interaction.followup.send(farewell, ephemeral=False)
            
        else:
            raise exceptions.ConversationError(errors.ConversationErrors.NO_CONVO)

    @chat_group.command(name="end-all", description=f"Stop all conversations you hold with {confighandler.get_config('bot_name')}. No conversation threads will be deleted.")
    async def stop_all(self, interaction: discord.Interaction):
        member: discord.Member = commands_utils.assure_class_is_value(interaction.user, discord.Member)
        
        if convos := self.client.get_all_user_conversations(member):
            reply = await self.client.get_input(interaction, f'Are you sure you want to end all of your chats? Type "{developerconfig.QUERY_CONFIRMATION}" to confirm or anything else to cancel. Timeout is {developerconfig.QUERY_TIMEOUT} seconds.')
            if not reply or reply.content != developerconfig.QUERY_CONFIRMATION:
                return await interaction.followup.send("Cencelled action.", ephemeral=False)
            
            chat_len = len(convos)
            await self.client.delete_all_conversations(member)
            
            await interaction.followup.send(f"Deleted {chat_len} chat{'s.' if chat_len > 1 else '.'}")
        else:
            raise exceptions.ConversationError(errors.ConversationErrors.NO_CONVOS)
        
    @chat_group.command(name="image", description="Create an image with specified parameters.")
    @discord.app_commands.describe(prompt=f"The keyword you want {confighandler.get_config('bot_name')} to describe.", save_to="What chat you want to save the image history too. (For exporting)") 
    async def image_generate(self, interaction: discord.Interaction, prompt: str, save_to: str=""):
        member: discord.Member = commands_utils.assure_class_is_value(interaction.user, discord.Member)
        convo = self.client.manage_defaults(member, save_to)

        await interaction.response.defer(ephemeral=True, thinking=True)

        image = await convo.generate_image(prompt)
        result = f"Created Image at {datetime.datetime.fromtimestamp(image.timestamp)}\nImage Link: {image.image_url}"
        return await interaction.followup.send(result, ephemeral=False)

    @chat_group.command(name="info", description=f"Displays information about your current {confighandler.get_config('bot_name')} Chat.")
    @discord.app_commands.describe(name="Name of the chat you want information on.")
    async def get_info(self, interaction: discord.Interaction, name: str=""):
        member: discord.Member = commands_utils.assure_class_is_value(interaction.user, discord.Member)
        convo = self.client.manage_defaults(member, name)

        uptime_delta = self.client.get_uptime()
        returned_embed = discord.Embed(title=f'"{convo.display_name}" Information')

        embeds = (
            {"name": "Started At", "value": str(convo.time), "inline": False},
            {"name": "Chat Length", "value": str(len(convo.context.context)), "inline": False},
            {"name": "Chat History ID", "value": str(convo.hid), "inline": False},
            {"name": "Chat ID", "value": str(convo.display_name), "inline": False},
            {"name": "Is Active", "value": str(convo.is_active), "inline": False},
            {"name": "AI Model", "value": str(convo.model.display_name), "inline": False},
            {"name": "Is Voice", "value": f"Yes" if isinstance(convo, chat.DGVoiceChat) else "No", "inline": False},
            {"name": f"{self.client.application.name} Version", "value": developerconfig.VERSION, "inline": False}, # type: ignore Client will be logged in by the time this is executed.
            {"name": f"{self.client.application.name} Uptime", "value": f"{uptime_delta.days} Days ({uptime_delta})", "inline": False} # type: ignore Client will be logged in by the time this is executed. 
        )
        for embed in embeds:
            returned_embed.add_field(**embed)
        returned_embed.color = discord.Colour.purple()

        return await interaction.response.send_message(embed=returned_embed, ephemeral=False)
    
    @chat_group.command(name="switch", description="Changes your default chat. This is a convenience command.")
    @discord.app_commands.describe(name="Name of the chat you want to switch to.")
    async def switch_default(self, interaction: discord.Interaction, name: str):
        member: discord.Member = commands_utils.assure_class_is_value(interaction.user, discord.Member)
        convo = self.client.manage_defaults(member, name)
        await interaction.response.send_message(f"Switched default chat to: {convo} (The name will not change or be set to default if the chat does not exist)" if convo else f"You do not have any {confighandler.get_config('bot_name')} conversations.")

    @chat_group.command(name="list", description="List all chats you currently have.")
    async def list_user_chats(self, interaction: discord.Interaction):
        member = commands_utils.assure_class_is_value(interaction.user, discord.Member)
        embed = self.client.get_embed(f"{member} Conversations")
        for chat in self.client.get_all_user_conversations(member).values():
            embed.add_field(name=chat.display_name, value=f"Model — {chat.model.display_name} | Is Private — {chat.private} | Voice - {True if chat.type == types.DGChatTypesEnum.VOICE else False}", inline=False)
             
        await interaction.response.send_message(embed=embed)
            
    @chat_group.command(name="inquire", description="Ask a one-off question. This does not require a chat. Context will not be saved.")
    @discord.app_commands.describe(query="The question you wish to pose.")
    @discord.app_commands.choices(ai_model=developerconfig.MODEL_CHOICES)
    async def inquire_once(self, interaction: discord.Interaction, query: str, ai_model: str | None):
        member = commands_utils.assure_class_is_value(interaction.user, discord.Member)
        model_string = ai_model if isinstance(ai_model, str) else confighandler.get_guild_config_attribute(member.guild, "default-ai-model")
        actual_model = commands_utils.get_modeltype_from_name(model_string)
        
        async with actual_model(member) as model:
            asked = await model.ask_model(query)
            reply = asked.response
        
            if reply and len(reply) >= 2000:
                return await interaction.response.send_message(file=commands_utils.to_file(reply, "reply.txt"))
            return await interaction.response.send_message(reply)
    
async def setup(client):
    await client.add_cog(Communication(client))
