import discord

from discord.ext import commands
from joe import DevJoe
from typing import Union, AsyncGenerator
from objects import GPTConfig, GPTChat, GPTModelRules, GPTExceptions

class listeners(commands.Cog):
    def __init__(self, client: DevJoe):
        self.client: DevJoe = client
        print(f"{self.__cog_name__} Loaded")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):   
        try:
            if self.client.application and message.author.id != self.client.application.id and message.content != GPTConfig.QUERY_CONFIRMATION:
                member: discord.Member = self.client.assure_class_is_value(message.author, discord.Member)
                if isinstance(convo := self.client.get_default_conversation(member), GPTChat.GPTChat) and message.guild:
                    if self.client.get_user_has_permission(message.guild.get_member(member.id), convo.model):

                        thread: Union[discord.Thread, None] = discord.utils.get(message.guild.threads, id=message.channel.id) 
                        content: str = message.content
                        has_private_thread = thread and thread.is_private()
                        
                        if has_private_thread and convo.is_processing != True:
                            
                            header_text = f'{convo.display_name} | {convo.model}'

                            if convo.stream == True:
                                msg: list[discord.Message] = [await message.channel.send("Asking...")]
                                streamed_reply: AsyncGenerator = convo.ask_stream(content)
                                full_message = f"## {header_text}\n\n"
                                sendable_portion = "<>"
                                ind, start_message_at = 0, 0
                                
                                # enumerate is not compatible with async syntax. There are some external modules that can do just that. But I do not want to rely on those.
                                async for token in streamed_reply:
                                    ind += 1
                                    full_message += token
                                    sendable_portion = full_message[start_message_at * GPTConfig.CHARACTER_LIMIT:((start_message_at + 1) * GPTConfig.CHARACTER_LIMIT)]

                                    if len(full_message) and len(full_message) >= (start_message_at + 1) * GPTConfig.CHARACTER_LIMIT:
                                        await msg[-1].edit(content=sendable_portion)
                                        msg.append(await msg[-1].channel.send(":)"))

                                    start_message_at = len(full_message) // GPTConfig.CHARACTER_LIMIT

                                    if ind and ind % GPTConfig.STREAM_UPDATE_MESSAGE_FREQUENCY == 0:
                                        await msg[-1].edit(content=sendable_portion)
                                else:
                                    return await msg[-1].edit(content=sendable_portion)

                            final_reply = f"## {header_text}\n\n{await convo.ask(content)}"
                            await message.channel.send(final_reply)
                        
                        elif has_private_thread and convo.is_processing == True:
                            raise GPTExceptions.DGException(f"{GPTConfig.BOT_NAME} is still processing your last request.")
                    else:
                        raise GPTExceptions.ModelIsLockedError(convo.model)

        except (GPTExceptions.ChatIsDisabledError, GPTExceptions.GPTContentFilter) as error:
            await message.channel.send(error.reply)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        if system := guild.system_channel:
            #[await system.send(self.client.WELCOME_TEXT[GPTConfig.CHARACTER_LIMIT * (t - 1) : GPTConfig.CHARACTER_LIMIT * t]) for t in range(1, ceil(len(self.client.WELCOME_TEXT) / GPTConfig.CHARACTER_LIMIT) + 1)]
            await system.send(file=self.client.to_file(self.client.WELCOME_TEXT, "welcome.md"))
        if owner := guild.owner:
            #[await owner.send(self.client.ADMIN_TEXT[GPTConfig.CHARACTER_LIMIT * t:]) for t in range(ceil(len(self.client.ADMIN_TEXT) / GPTConfig.CHARACTER_LIMIT))]
            await owner.send(file=self.client.to_file(self.client.ADMIN_TEXT, "admin-introduction.md"))

        with GPTModelRules.GPTModelRules(guild) as _:
            ...

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, _before: discord.VoiceState, after: discord.VoiceState):
        if convos := self.client.get_all_user_conversations(member):
            [setattr(convo, "voice", after.channel) for convo in convos.values() if convo.type == GPTChat.GPTTypes.voice]
        
        # DebugCode:
        # print(self.client.get_user_voice_conversation(member, "navidrohim-0"))

        

async def setup(client: DevJoe):
    await client.add_cog(listeners(client))
