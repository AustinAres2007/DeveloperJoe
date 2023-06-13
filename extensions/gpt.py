import discord, datetime, openai, io
from discord.ext import commands
from typing import Union

# TODO: Handle GPT errors

"""
Rant:
    This API / kit is so shit it makes me not want to code for discord anymore. It has become complex since the update and discords
    TOS change. It has a very "linear" structure now. Not flexible at all.
"""
# Errors

NO_CONVO = "You do not have a conversation with DeveloperJoe. Do /start to do such."
HAS_CONVO = 'You already have an ongoing conversation with DeveloperJoe. To reset, do "/stop."'
GENERIC_ERROR = "Unknown error, contact administrator."

MODEL = "gpt-3.5-turbo"

API_KEY = "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"
GPT_HEADERS = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}

openai.api_key = API_KEY

class gpt_instance:
    def __init__(self, id: int, *args):
        self.id = id
        self.args = args
        self.chat_history = []
        self.readable_history = []

    def __send_query__(self, query_type: str, save_message: bool=True, **kwargs) -> str:
        
        replied_content = "Unknown error, contact administrator."
        error = False
        r_history = []
        
        try:
            if query_type == "query":
                

                self.chat_history.append(kwargs)
                r_history.append(kwargs)

                reply = openai.ChatCompletion.create(model=MODEL, messages=self.chat_history)
                actual_reply = reply.choices[0].message  # type: ignore

                replied_content = actual_reply["content"]

                self.chat_history.append(dict(actual_reply))
                r_history.append(dict(actual_reply))
                self.readable_history.append(r_history)
            
            
            elif query_type == "image":
                # Required Arguments: Prompt (String < 1000 chars), Size (String, 256x256, 512x512, 1024x1024)

                image_request = openai.Image.create(**kwargs)
                image_url = image_request['data'][0]['url'] # type: ignore
                replied_content = f"Created Image at {datetime.datetime.fromtimestamp(image_request['created'])}\nImage Link: {image_url}" # type: ignore

                r_history.append({'image': f'User asked GPT to compose the following image: "{kwargs["prompt"]}"'})
                r_history.append({'image_return': image_url})

                self.readable_history.append(r_history)
            else:
                error = f"Generic ({query_type})"
                replied_content = f"Unknown Error, contact administrator. (Error Code: {query_type})"
            
        except openai.InvalidRequestError as e:
            error = e
            replied_content = str(e)
        
        except (openai.APIError, openai.error.ServiceUnavalibleError) as e: # type: ignore
            error = e
            replied_content = "Generic GPT 3.5 Error, please try again later."
    
        except openai.error.RateLimitError as e: # type: ignore
            error = e
            replied_content = "Hit set rate limit for this month. Please contact administrator."

        except openai.error.APIConnectionError as e: # type: ignore
            error = e
            replied_content = "Could not connect to OpenAI API Endpoint, contact administrator."

        except Exception as e:
            error = e
            replied_content = f"Uncatched Error: {str(e)}. Please contact administrator"

        finally:
            if (not save_message or error) and query_type == "query":
                self.chat_history = self.chat_history[:len(self.chat_history)-2]
                self.readable_history.pop()

                if error:
                    self.readable_history.append(f"Error: {str(error)}")

            elif (not save_message or error) and query_type == "image":
                self.readable_history.pop()

                if error:
                    self.readable_history.append(f"Error: {str(error)}")

            return replied_content

    def ask(self, query: str) -> str:
        return self.__send_query__(query_type="query", role="user", content=query)
    
    def start(self, uid: int) -> str:
        self.id = uid
        return self.__send_query__(save_message=False, query_type="query", role="system", content="Please give a short and formal introduction to yourself, what you can do, and limitations.")

class gpt(commands.Cog):
    
    @staticmethod
    def is_owner(interaction: discord.Interaction) -> bool:
        return interaction.user.id == 400089431933059072
    
    def get_user_conversation(self, id_: int) -> Union[gpt_instance, None]:
        return self.conversations[id_] if int(id_) in list(self.conversations) else None

    def __init__(self, client):
        self.client: commands.Bot = client
        self.conversations: dict[int, gpt_instance] = {}

        print("GPT Loaded")

    @discord.app_commands.command(name="halt", description="Shuts down bot client")
    async def halt(self, ctx: discord.Interaction):

        await ctx.response.send_message("Shutting Down")
        await self.client.close()
    
    @discord.app_commands.command(name="start", description="Start a DeveloperJoe Session")
    async def start(self, interaction: discord.Interaction):
        
        await interaction.response.defer(ephemeral=True, thinking=True)

        async def func():

            convo = gpt_instance(interaction.user.id)
            self.conversations[interaction.user.id] = convo
            await interaction.followup.send(convo.start(interaction.user.id))

        if not self.get_user_conversation(interaction.user.id):
            return await func()

        await interaction.response.send_message(HAS_CONVO)

    @discord.app_commands.command(name="ask", description="Ask DeveloperJoe a question.")
    async def ask(self, interaction: discord.Interaction, message: str):

        if convo := self.get_user_conversation(interaction.user.id):
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await interaction.followup.send(convo.ask(message))
        await interaction.response.send_message(NO_CONVO)

    @discord.app_commands.command(name="stop", description="Stop a DeveloperJoe session.")
    async def stop(self, interaction: discord.Interaction):

        # Actual command
        async def func(gpt):
            await interaction.response.send_message(self.conversations[interaction.user.id].__send_query__(query_type="query", role="system", content="Please give a short and formal farewell."))
            del self.conversations[interaction.user.id]
        
        # checks because app_commands cannot use normal ones.
        if convo := self.get_user_conversation(interaction.user.id):
            return await func(convo)
        await interaction.response.send_message(NO_CONVO)

    @discord.app_commands.command(name="generate", description="Create an image with specified parameters.")
    async def image_generate(self, interaction: discord.Interaction, prompt: str, resolution: str="512x512"):
        r = ""
        try:
            await interaction.response.defer(ephemeral=True, thinking=True)
            if convo := self.get_user_conversation(interaction.user.id):
                return await interaction.followup.send(convo.__send_query__(query_type="image", prompt=prompt, size=resolution, n=1))
            await interaction.response.send_message(NO_CONVO)    
        except Exception as e:
            return f"Uncaught Exception: {e}"
    
    @discord.app_commands.command(name="export", description="Export current chat history.")
    async def export_chat_history(self, interaction: discord.Interaction, uid: int=0):
        if convo := self.get_user_conversation(uid if uid else interaction.user.id):

            def format(data: list) -> str:
                final = ""
                
                for entry in data:
                    final += f"{interaction.user.name}: {entry[0]['content']}\nGPT 3.5: {entry[1]['content']}\n\n{'~' * 15}\n\n" \
                        if 'content' in entry[0] else f"{entry[0]['image']}\n{entry[1]['image_return']}\n\n{'~' * 15}\n\n"
                
                return final
            
            formatted_history_string = format(convo.readable_history)
            file_like = io.BytesIO(formatted_history_string.encode())
            file_like.name = "transcript.txt"
            return await interaction.response.send_message(f"{interaction.user.display_name}'s DeveloperJoe Transcript", file=discord.File(file_like))
        
        await interaction.response.send_message(NO_CONVO)

async def setup(client):
    await client.add_cog(gpt(client))
