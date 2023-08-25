import discord, json, datetime, io, asyncio

from typing import Union, Any
from discord.ext import commands
from joe import DeveloperJoe

from sources import (
    history, 
    config, 
    exceptions, 
    errors
)
from sources.common import (
    commands_utils,
    dgtypes
)

class History(commands.Cog):
    def __init__(self, client):
        self.client: DeveloperJoe = client
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
            with history.DGHistorySession() as history_session:
                reply: discord.Message = await self.client.get_input(interaction, f'Are you sure? \n(Send reply within {config.QUERY_TIMEOUT} seconds, \nand "{config.QUERY_CONFIRMATION}" to confirm, anything else to cancel.)')
                if reply.content == config.QUERY_CONFIRMATION:
                    return await interaction.followup.send(history_session.delete_chat_history(history_id))
                return await interaction.followup.send("Cancelled action.")

        except ValueError:
            raise exceptions.InvalidHistoryID(history_id)
        except asyncio.TimeoutError:
            return

    @discord.app_commands.command(name="export", description="Export current chat history.")
    async def export_chat_history(self, interaction: discord.Interaction, name: Union[None, str]):

        member: discord.Member = commands_utils.assure_class_is_value(interaction.user, discord.Member)
        convo = self.client.manage_defaults(member, name)
    
        formatted_history_string = self.format(convo.readable_history, convo.user.display_name) if convo.readable_history else errors.HistoryErrors.HISTORY_EMPTY
        file_like = io.BytesIO(formatted_history_string.encode())
        file_like.name = f"{convo.display_name}-{datetime.datetime.now()}-transcript.txt"

        await interaction.user.send(f"{convo.user.name}'s {config.BOT_NAME} Transcript ({convo.display_name})", file=discord.File(file_like))
        await interaction.response.send_message("I have sent the conversation transcript to our direct messages.")
    
        
            
    @discord.app_commands.command(name="history", description="Get a past saved conversation.")
    async def get_chat_history(self, interaction: discord.Interaction, history_id: str):
        try:
            with history.DGHistorySession() as history_session:
                if history_chat := history_session.retrieve_chat_history(history_id):
                    if history_chat.private == False or interaction.user.id == history_chat.user:
                        list_history: Any = history_chat.data
                        history_user = self.client.get_user(history_chat.user)
                        formatted = self.format(data=list_history, username=history_user.display_name if history_user else "Deleted User") if list_history else errors.HistoryErrors.HISTORY_EMPTY

                        history_file = io.BytesIO(formatted.encode())
                        history_file.name = f"{history_chat.name}-transcript.txt"

                        await interaction.user.send(file=discord.File(history_file))
                        return await interaction.response.send_message("I have sent the history transcript to our direct messages.")
                    raise exceptions.InvalidHistoryOwner(history_id)
                raise exceptions.HistoryNotExist(history_id)
        except ValueError:
            raise exceptions.InvalidHistoryID(history_id)
        
async def setup(client):
    await client.add_cog(History(client))
