import discord, threading, asyncio
from discord.ext import commands
from joe import DevJoe

class listeners(commands.Cog):
    def __init__(self, client: DevJoe):
        self.client: DevJoe = client
        print(f"{self.__cog_name__} Loaded")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        def _listener():

            def _send(msg: str):
                asyncio.run_coroutine_threadsafe(thread.send(msg), self.client.loop)

            try:
                if convo := self.client.get_user_conversation(message.author.id):
                    thread: discord.Thread = discord.utils.get(message.guild.threads, id=message.channel.id)
                    if (thread and thread.is_private() and thread.member_count == 2) and convo.is_processing != True:
                        _send(convo.ask(message.content))
                    elif not (thread and thread.is_private() and thread.member_count == 2):
                        return
                    else:
                        _send(f"{self.client.application.name} is still processing your last request.")

            except Exception as e:
                print(e)

        threading.Thread(target=_listener).start()

async def setup(client: commands.Bot):
    await client.add_cog(listeners(client))
