import discord, requests
from discord.ext import commands

BASE_ENDPOINT = "https://api.openai.com/v1"

# TODO: Handle GPT errors

"""
Rant:
    This API / kit is so shit it makes me not want to code for discord anymore. It has become complex since the update and discords
    TOS change. It has a very "linear" structure now. Not flexible at all.
"""
# Errors

NO_CONVO = "You do not have a conversation with DeveloperJoe. Do /start to do such."
HAS_CONVO = 'You already have an ongoing conversation with DeveloperJoe. To reset, do "/stop."'

api_key = "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"
url = "https://api.openai.com/v1/chat/completions"
headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

class gpt_instance:
    def __init__(self, id: int, *args):
        self.id = id
        self.args = args
        self.chat_history = []

    def __send_query__(self, query, role) -> str:
        self.chat_history.append({"role": role, "content": query, "name": f"{self.id}"})
        json_body = {"model": "gpt-3.5-turbo", "messages": self.chat_history}

        reply = requests.post(url, headers=headers, json=json_body)
        reply_json = reply.json()
        reply_code = reply.status_code

        if reply_code == 200:
            return reply_json["choices"][0]["message"]["content"]
        else:
            ...

    def ask(self, query: str) -> str:
        return self.__send_query__(query, "user")
    
    def start(self, uid: int) -> str:
        self.id = uid
        return self.__send_query__("Please give a short and formal introduction to yourself, what you can do, and limitations.", "system")

class gpt(commands.Cog):
    
    def has_conversation(self, id_: int) -> bool:
        return int(id_) in list(self.conversations) 
    
    def is_owner(interaction: discord.Interaction) -> bool:
        return interaction.user.id == 400089431933059072

    def __init__(self, client):
        self.client: commands.Bot = client
        self.conversations: dict[int, gpt_instance] = {}

        print("GPT Loaded")

    @discord.app_commands.command(name="halt", description="Shuts down bot client")
    @discord.app_commands.check(is_owner)
    async def halt(self, ctx: discord.Interaction):
        await ctx.response.send_message("Shutting down.")
        await self.client.close()
    
    @discord.app_commands.command(name="start", description="Start a DeveloperJoe Session")
    async def start(self, interaction: discord.Interaction):
        
        async def func():
            await interaction.response.defer(ephemeral=True, thinking=True)

            convo = gpt_instance(interaction.user.id)
            self.conversations[interaction.user.id] = convo
            await interaction.followup.send(convo.start(interaction.user.id))

        if not self.has_conversation(interaction.user.id):
            return await func()
        await interaction.response.send_message(HAS_CONVO)

    @discord.app_commands.command(name="ask", description="Ask DeveloperJoe a question.")
    async def ask(self, interaction: discord.Interaction, message: str):
        if self.has_conversation(interaction.user.id):
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await interaction.followup.send(self.conversations[interaction.user.id].ask(message))

    @discord.app_commands.command(name="stop", description="Stop a DeveloperJoe session.")
    async def stop(self, interaction: discord.Interaction):

        # Actual command
        async def func():
            await interaction.response.send_message(self.conversations[interaction.user.id].__send_query__("Please give a short and formal farewell.", "system"))
            del self.conversations[interaction.user.id]
        
        # checks because app_commands cannot use normal ones.
        if self.has_conversation(interaction.user.id):
            return await func()
        await interaction.response.send_message(NO_CONVO)
            
    @discord.app_commands.command(name="engine", description="Create a custom OpenAI Chat AI Model")
    async def custom_engine(self, interaction: discord.Interaction):
        ...

async def setup(client):
    await client.add_cog(gpt(client))
