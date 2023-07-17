import discord

from discord.ext import commands
from joe import DevJoe
from typing import Union, AsyncGenerator
from objects import GPTConfig, GPTChat

class listeners(commands.Cog):
    def __init__(self, client: DevJoe):
        self.client: DevJoe = client
        print(f"{self.__cog_name__} Loaded")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):   
        async def _send(msg: str):
            if thread: 
                if len(msg) > GPTConfig.CHARACTER_LIMIT:
                    msg_reply: discord.File = self.client.to_file(msg, "reply.txt")
                    return await thread.send(file=msg_reply)
                return await thread.send(msg)

        try:
            if isinstance(convo := self.client.get_default_conversation(message.author), GPTChat.GPTChat):
                thread: Union[discord.Thread, None] = discord.utils.get(message.guild.threads, id=message.channel.id) # type: ignore
                content: str = message.content
                if (thread and thread.is_private() and (thread.member_count == 2 or content.startswith(">"))) and convo.is_processing != True and not content.startswith(">"):

                    if convo.stream == True:
                        msg: list[discord.Message] = [await message.channel.send("Asking...")]
                        streamed_reply: AsyncGenerator = convo.ask_stream(content)
                        full_message = f"## {convo.display_name if convo.display_name != '0' else 'Conversation'}\n\n"
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

                    final_reply = f"## {convo.display_name if convo.display_name != '0' else 'Conversation'}\n\n{await convo.ask(content)}"
                    await message.channel.send(final_reply)
                elif not (thread and thread.is_private() and thread.member_count == 2) or content.startswith(">"):
                    return
                else:
                    await _send(f"{self.client.application.name} is still processing your last request.") # type: ignore

        except Exception as e:
            await _send(str(e))

        

async def setup(client: DevJoe):
    await client.add_cog(listeners(client))
