import asyncio
import discord, random

from discord.ext import commands, tasks
from typing import Union

from joe import DeveloperJoe

from sources import (
    chat,
    exceptions,
    database,
    voice,
    confighandler,
    models
)
from sources.common import (
    commands_utils,
    developerconfig,
    common
)

class Listeners(commands.Cog):
    """Contains discord.py listener methods.

    Args:
        commands (_type_): _description_
    """
    def __init__(self, _client: DeveloperJoe):
        self.client = _client
        self.change_status.start() if confighandler.get_config("enable_status_scrolling") else None
        
        print(f"{self.__cog_name__} Loaded")
        
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):   
        """This listener does what the function name suggests.
            In the context of DeveloperJoe, it listens for Thread messages and replies to them if the user is in a private thread alone.
            or, if the user @ed the bot.

        Args:
            message (discord.Message): The message the user sent

        Raises:
            exceptions.DGException: Generic
            exceptions.ModelIsLockedError: If the model the user wants to user is locked.
            exceptions.ChatChannelDoesntExist: Raised if the bot doesn't have access to a thread channel

        Returns:
            _type_: None
        """
        convo = None
        try:
            
            
            async def respond_to_mention(member: discord.Member):
                model: models.AIModelType = commands_utils.get_modeltype_from_name(confighandler.get_guild_config_attribute(member.guild, "default-ai-model"))
                
                async with model(member) as ai_model:
                    async with message.channel.typing():
                        ai_reply = await ai_model.ask_model(message.clean_content)
                    
                        if len(reply := ai_reply.response + "\n\n*Notice: When you @ me, I do not remember anything you've said in the past*") >= 2000:
                            return await message.channel.send(file=commands_utils.to_file(reply, "reply.txt"))
                        return await message.channel.send(reply)
                
            # TODO: Fix > 2000 characters bug non-streaming
            if self.client.application and message.author.id != self.client.application.id and message.content != developerconfig.QUERY_CONFIRMATION:
                
                member: discord.Member = commands_utils.assure_class_is_value(message.author, discord.Member)
                
                if isinstance(convo := self.client.get_default_conversation(member), chat.DGChatType) and message.guild:
                    if isinstance(channel := message.channel, discord.Thread):

                        thread: Union[discord.Thread, None] = discord.utils.get(message.guild.threads, id=message.channel.id) 
                        content: str = message.content
                        has_private_thread = thread and thread.is_private()
                        
                        if has_private_thread and convo.is_processing != True:
                            if convo.stream == True:
                                await convo.ask_stream(content, channel)
                            else:
                                await convo.ask(content, channel)
                            
                        elif has_private_thread and convo.is_processing == True:
                            raise exceptions.DGException(f"{confighandler.get_config('bot_name')} is still processing your last request.")
                        
                    elif self.client.user and message.mentions and message.mentions[0].id == self.client.user.id:
                        await respond_to_mention(member)
                        
                elif self.client.user and message.mentions and message.mentions[0].id == self.client.user.id:
                    await respond_to_mention(member)

        except (exceptions.DGException, exceptions.ChatIsDisabledError, exceptions.GPTContentFilter) as error:
            await message.channel.send(error.message)
        except discord.Forbidden:
            raise exceptions.ChatChannelDoesntExist(message, str(convo)) 

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        """When the bot joins a guild, a welcome message will be sent to general users and the server owner.

        Args:
            guild (discord.Guild): The guild the bot joined.
        """
        if system := guild.system_channel:
            #[await system.send(self.client.WELCOME_TEXT[.CHARACTER_LIMIT * (t - 1) : .CHARACTER_LIMIT * t]) for t in range(1, ceil(len(self.client.WELCOME_TEXT) / .CHARACTER_LIMIT) + 1)]
            await system.send(file=commands_utils.to_file(self.client.WELCOME_TEXT, "welcome.md"))
        if owner := guild.owner:
            #[await owner.send(self.client.ADMIN_TEXT[.CHARACTER_LIMIT * t:]) for t in range(ceil(len(self.client.ADMIN_TEXT) / .CHARACTER_LIMIT))]
            await owner.send(file=commands_utils.to_file(self.client.ADMIN_TEXT, "admin-introduction.md"))

        with database.DGDatabaseManager() as _guild_handler:
            _guild_handler.add_guild_to_database(guild.id)
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """This function listens to if a user has joined a voice channel. This is done to update a VoiceChat instance if the user has one. Read the given comments for more.

        Args:
            member (discord.Member): Which member invoked this listener
            before (discord.VoiceState): The users old voice state
            after (discord.VoiceState): The users new voice state
        """
        
        bot_voice: voice.VoiceRecvClient = discord.utils.get(self.client.voice_clients, guild=member.guild) # type: ignore because all single instances are `discord.VoiceClient`
        
        b_channel = getattr(before, "channel", None)
        a_channel = getattr(after, "channel", None)
        
        if member.id != self.client.user.id: # type: ignore will always be True
            if convos := self.client.get_all_user_conversations(member):
                
                async def _manage_bot_disconnect(convo: chat.DGVoiceChat):
                    if bot_voice:
                        try:
                            await convo.stop_listening()
                            convo.voice_tss_queue.clear() 
                        except exceptions.DGNotListening:
                            pass
                        finally:
                            await bot_voice.disconnect()
                            bot_voice.cleanup()
                            
                for convo in convos.values(): 
                    if isinstance(convo, chat.DGVoiceChat):
                        if a_channel:
                            convo.voice = a_channel
                        
                        if b_channel == None and isinstance(a_channel, discord.VoiceChannel): # User joined VC
                            pass
                        
                        elif isinstance(b_channel, discord.VoiceChannel) and a_channel == None: # User left VC
                            await _manage_bot_disconnect(convo)
                            
                        elif isinstance(b_channel, discord.VoiceChannel) and isinstance(a_channel, discord.VoiceChannel): # User done something with VC or moved
                            if b_channel == a_channel: # User has muted or deafened. Etc...
                                pass
                            elif b_channel != a_channel: # User has moved channel
                                await _manage_bot_disconnect(convo)
                                
                        else: # No fucking clue what happened. Panic disconnect!
                            await _manage_bot_disconnect(convo)

    @tasks.loop(seconds=confighandler.get_config("status_scrolling_change_interval"))
    async def change_status(self):
        """This task loop changes the bots status every set amount of seconds. If enabled in config YAML file.
        """
        try:
            status_to_use = random.choice(list(self.client.statuses))
            status_type = int(self.client.statuses[status_to_use])
            
            if status_type < -1 or status_type > 5: # type: ignore because it is a type alias 
                common.warn_for_error(f'A status has been incorrectly configured in {developerconfig.CONFIG_FILE}. Wrong status is "{status_to_use}". The value is {status_type} when it should only be more more than -2 and less than 6!')
            await self.client.change_presence(activity=discord.Activity(type=status_type, name=status_to_use))
        except AttributeError:
            pass # Still loading!
        
async def setup(client: DeveloperJoe):
    await client.add_cog(Listeners(client))
