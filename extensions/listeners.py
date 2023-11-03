import discord

from discord.ext import commands
from typing import Union

from joe import DeveloperJoe

from sources import (
    chat,
    exceptions,
    modelhandler,
    voice,
    confighandler
)
from sources.common import (
    commands_utils,
    developerconfig
)

class Listeners(commands.Cog):
    def __init__(self, _client: DeveloperJoe):
        self.client = _client
        print(f"{self.__cog_name__} Loaded")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):   
        convo = None
        try:
            # TODO: Fix > 2000 characters bug non-streaming
            if self.client.application and message.author.id != self.client.application.id and message.content != developerconfig.QUERY_CONFIRMATION:
                member: discord.Member = commands_utils.assure_class_is_value(message.author, discord.Member)
    
                if isinstance(convo := self.client.get_default_conversation(member), chat.DGChatType) and message.guild:
                    if isinstance(channel := message.channel, discord.Thread):
                        if self.client.get_user_has_permission(member, convo.model):

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
                        else:
                            raise exceptions.ModelIsLockedError(convo.model.model)

        except (exceptions.DGException, exceptions.ChatIsDisabledError, exceptions.GPTContentFilter) as error:
            await message.channel.send(error.message)
        except discord.Forbidden:
            raise exceptions.ChatChannelDoesntExist(message, str(convo)) 

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        if system := guild.system_channel:
            #[await system.send(self.client.WELCOME_TEXT[.CHARACTER_LIMIT * (t - 1) : .CHARACTER_LIMIT * t]) for t in range(1, ceil(len(self.client.WELCOME_TEXT) / .CHARACTER_LIMIT) + 1)]
            await system.send(file=commands_utils.to_file(self.client.WELCOME_TEXT, "welcome.md"))
        if owner := guild.owner:
            #[await owner.send(self.client.ADMIN_TEXT[.CHARACTER_LIMIT * t:]) for t in range(ceil(len(self.client.ADMIN_TEXT) / .CHARACTER_LIMIT))]
            await owner.send(file=commands_utils.to_file(self.client.ADMIN_TEXT, "admin-introduction.md"))

        with modelhandler.DGRules(guild):
            pass # Make sure guild in rule database, if not, make it.
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
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
            
async def setup(client: DeveloperJoe):
    await client.add_cog(Listeners(client))
