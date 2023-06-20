import discord, json, datetime, io, asyncio

from discord.ext import commands
from joe import DevJoe
from objects import GPTHistory, GPTErrors, GPTConfig

class history(commands.Cog):
    def __init__(self, client):
        self.client: DevJoe = client
        print(f"{self.__cog_name__} Loaded")

    def format(self, data: list, username: str) -> str:
        final = ""
        
        for entry in data:
            final += f"{username}: {entry[0]['content']}\nGPT 3.5: {entry[1]['content']}\n\n{'~' * 15}\n\n" \
                if 'content' in entry[0] else f"{entry[0]['image']}\n{entry[1]['image_return']}\n\n{'~' * 15}\n\n"
        
        return final
    
    @discord.app_commands.command(name="delete", description="Delete a past saved conversation.")
    async def delete_chat_history(self, interaction: discord.Interaction, history_id: str):
        try:
            await interaction.response.defer(thinking=False, ephemeral=True)
            with GPTHistory.GPTHistory() as history:
                reply: discord.Message = await self.client.get_confirmation(interaction, f'Are you sure? \n(Send reply within {GPTConfig.QUERY_TIMEOUT} seconds, \nand "{GPTConfig.QUERY_CONFIRMATION}" to confirm, anything else to cancel.)') # type: ignore
                if reply.content == GPTConfig.QUERY_CONFIRMATION:
                    return await interaction.followup.send(history.delete_chat_history(history_id))
                return await interaction.followup.send("Cancelled action.")

        except ValueError:
            return await interaction.response.send_message(GPTErrors.HistoryErrors.INVALID_HISTORY_ID)
        except asyncio.TimeoutError:
            return
        except Exception as e:
            if GPTConfig.DEBUG:
                await interaction.followup.send(f"(Debug) Error > {e}")

    @discord.app_commands.command(name="export", description="Export current chat history.")
    async def export_chat_history(self, interaction: discord.Interaction):
        if (convo := self.client.get_user_conversation(interaction.user.id)):

            formatted_history_string = self.format(convo.readable_history, convo.user.display_name) if convo.readable_history else "No chat history."
            file_like = io.BytesIO(formatted_history_string.encode())
            file_like.name = f"{datetime.datetime.now()}-transcript.txt"

            await interaction.user.send(f"{convo.user.name}'s DeveloperJoe Transcript", file=discord.File(file_like))
            return await interaction.response.send_message("I have sent your conversation transcript to our direct messages.")
        
        await interaction.response.send_message(GPTErrors.ConversationErrors.NO_CONVO)
    
    @discord.app_commands.command(name="history", description="Get a past saved conversation.")
    async def get_chat_history(self, interaction: discord.Interaction, history_id: str):
        try:
            with GPTHistory.GPTHistory() as history:
                if h_file := history.retrieve_chat_history(history_id):
                    
                    list_history = json.loads(h_file[0][3])
                    history_user = self.client.get_user(h_file[0][1])
                    formatted = self.format(data=list_history, username=history_user.display_name if history_user else "Deleted User")

                    history_file = io.BytesIO(formatted.encode())
                    history_file.name = f"{h_file[0][0]}-transcript.txt"

                    await interaction.user.send(file=discord.File(history_file))
                    return await interaction.response.send_message("I have sent your history transcript to our direct messages.")
                return await interaction.response.send_message(GPTErrors.HistoryErrors.HISTORY_DOESNT_EXIST)
        except ValueError:
            return await interaction.response.send_message(GPTErrors.HistoryErrors.INVALID_HISTORY_ID)
    
    @discord.app_commands.command(name="context", description="Remove a part of your current conversation with DeveloperJoe.")
    async def remove_context(self, interaction: discord.Interaction, message_index: int):
        if convo := self.client.get_user_conversation(interaction.user.id):
            try:
                message_index -= 1
                del convo.chat_history[message_index:message_index + 2]
                del convo.readable_history[convo._readable_history_map_[message_index]]
                del convo._readable_history_map_[message_index]

                await interaction.response.send_message(f"Deleted Message & Response at position: {message_index + 1}")
            except IndexError:
                await interaction.response.send_message(f"No message at message index: {message_index}")
        await interaction.response.send_message(GPTErrors.ConversationErrors.NO_CONVO)
        
async def setup(client):
    await client.add_cog(history(client))
