import discord

from discord.ext import commands
from typing import Union, AsyncGenerator
from joe import DeveloperJoe
from sources import (
    utils,
    config,
    chat,
    exceptions,
    modelhandler,
    voice
)

class Listeners(commands.Cog):
    def __init__(self, client: DeveloperJoe):
        self.client: DeveloperJoe = client
        print(f"{self.__cog_name__} Loaded")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):   
        convo = None
        try:
            # TODO: Fix > 2000 characters bug non-streaming
            if self.client.application and message.author.id != self.client.application.id and message.content != config.QUERY_CONFIRMATION:
                member: discord.Member = utils.assure_class_is_value(message.author, discord.Member)
                if isinstance(convo := self.client.get_default_conversation(member), chat.DGChatType) and message.guild:
                    if self.client.get_user_has_permission(message.guild.get_member(member.id), convo.model):

                        thread: Union[discord.Thread, None] = discord.utils.get(message.guild.threads, id=message.channel.id) 
                        content: str = message.content
                        has_private_thread = thread and thread.is_private()
                        
                        if has_private_thread and convo.is_processing != True:
                            
                            info = f'{convo.display_name} | {convo.model.display_name}'
                            header_and_message = f"## {info}\n\n"
                            
                            final_message_reply = ""
        
                            # If streamed reply
                            if convo.stream == True:
                                
                                msg: list[discord.Message] = [await message.channel.send("Asking...")]
                                streamed_reply: AsyncGenerator = convo.ask_stream(content)

                                sendable_portion = "<>"
                                ind, start_message_at = 0, 0
                                
                                # enumerate is not compatible with async syntax. There are some external modules that can do just that. But I do not want to rely on those.
                                async for token in streamed_reply:
                                    ind += 1
                                    header_and_message += token
                                    final_message_reply += token
                                    sendable_portion = header_and_message[start_message_at * config.CHARACTER_LIMIT:((start_message_at + 1) * config.CHARACTER_LIMIT)]

                                    if len(header_and_message) and len(header_and_message) >= (start_message_at + 1) * config.CHARACTER_LIMIT:
                                        await msg[-1].edit(content=sendable_portion)
                                        msg.append(await msg[-1].channel.send(":)"))

                                    start_message_at = len(header_and_message) // config.CHARACTER_LIMIT

                                    if ind and ind % config.STREAM_UPDATE_MESSAGE_FREQUENCY == 0:
                                        await msg[-1].edit(content=sendable_portion)
                                else:
                                    await msg[-1].edit(content=sendable_portion)

                            # If normal reply
                            else:
                                final_message_reply = reply = await convo.ask(content)
                                final_reply = header_and_message + reply
                                await message.channel.send(final_reply)

                            if isinstance(convo, chat.DGVoiceChat) and message.channel.type in config.ALLOWED_INTERACTIONS:
                                await convo.speak(final_message_reply, message.channel)
                            return
                        
                        elif has_private_thread and convo.is_processing == True:
                            raise exceptions.DGException(f"{config.BOT_NAME} is still processing your last request.")
                    else:
                        raise exceptions.ModelIsLockedError(convo.model)

        except (exceptions.ChatIsDisabledError, exceptions.GPTContentFilter) as error:
            await message.channel.send(error.reply)
        except discord.Forbidden:
            raise exceptions.ChatChannelDoesntExist(message, convo) 

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        if system := guild.system_channel:
            #[await system.send(self.client.WELCOME_TEXT[.CHARACTER_LIMIT * (t - 1) : .CHARACTER_LIMIT * t]) for t in range(1, ceil(len(self.client.WELCOME_TEXT) / .CHARACTER_LIMIT) + 1)]
            await system.send(file=utils.to_file(self.client.WELCOME_TEXT, "welcome.md"))
        if owner := guild.owner:
            #[await owner.send(self.client.ADMIN_TEXT[.CHARACTER_LIMIT * t:]) for t in range(ceil(len(self.client.ADMIN_TEXT) / .CHARACTER_LIMIT))]
            await owner.send(file=utils.to_file(self.client.ADMIN_TEXT, "admin-introduction.md"))

        with modelhandler.DGRules(guild) as _:
            ...
    
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
                            convo.stop_listening()
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
