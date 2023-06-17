import discord, threading, asyncio, io
from discord.ext import commands
from joe import DevJoe
from typing import Union

class listeners(commands.Cog):
    def __init__(self, client: DevJoe):
        self.client: DevJoe = client
        print(f"{self.__cog_name__} Loaded")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        def _listener():
            
            def _send(msg: str):
                if thread: 
                    if len(msg) > 2000:
                        msg_reply: discord.File = self.client.to_file(msg, "reply.txt")
                        return asyncio.run_coroutine_threadsafe(thread.send(file=msg_reply), self.client.loop)    
                    return asyncio.run_coroutine_threadsafe(thread.send(msg), self.client.loop)

            try:
                if convo := self.client.get_user_conversation(message.author.id):
                    thread: Union[discord.Thread, None] = discord.utils.get(message.guild.threads, id=message.channel.id) # type: ignore
                    content: str = message.content
                    if (thread and thread.is_private() and (thread.member_count == 2 or content.startswith(">"))) and convo.is_processing != True:
                        _send(convo.ask(content))
                    elif not (thread and thread.is_private() and thread.member_count == 2):
                        return
                    else:
                        _send(f"{self.client.application.name} is still processing your last request.") # type: ignore

            except Exception as e:
                _send(str(e))

        threading.Thread(target=_listener).start()

async def setup(client: DevJoe):
    await client.add_cog(listeners(client))
