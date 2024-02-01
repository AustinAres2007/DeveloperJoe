import discord, datetime, io, asyncio

from typing import Any
from discord.ext import commands
from joe import DeveloperJoe

from sources import (
    history, 
    exceptions, 
    errors,
    confighandler
)
from sources.common import (
    commands_utils,
    developerconfig
)

class History(commands.Cog):
    def __init__(self, _client: DeveloperJoe):
        self.client = _client
        print(f"{self.__cog_name__} Loaded")

    def format(self, data: list, username: str, model: str) -> str:
        final = ""
        
        for entry in data:
            final += f"{username}: {entry[0]['content']}\n{model}: {entry[1]['content']}\n\n{'~' * 15}\n\n" \
                if 'content' in entry[0] else f"{entry[0]['image']}\n{entry[1]['image_return']}\n\n{'~' * 15}\n\n"
        
        return final

    @discord.app_commands.command(name="delete", description="Delete a past saved conversation.")
    async def delete_chat_history(self, interaction: discord.Interaction, history_id: str):
        try:
            await interaction.response.defer(thinking=False, ephemeral=True)
            with history.DGHistorySession() as history_session:
                reply = await self.client.get_input(interaction, f'Are you sure? \n(Send reply within {developerconfig.QUERY_TIMEOUT} seconds, \nand "{developerconfig.QUERY_CONFIRMATION}" to confirm, anything else to cancel.)')
                if reply and reply.content == developerconfig.QUERY_CONFIRMATION:
                    return await interaction.followup.send(history_session.delete_chat_history(history_id))
                return await interaction.followup.send("Cancelled action.")

        except ValueError:
            raise exceptions.HistoryError(errors.HistoryErrors.INVALID_HISTORY_ID)
        except asyncio.TimeoutError:
            return

    @discord.app_commands.command(name="export", description="Export current chat history.")
    async def export_chat_history(self, interaction: discord.Interaction, name: str=""):

        member: discord.Member = commands_utils.assure_class_is_value(interaction.user, discord.Member)
        convo = self.client.manage_defaults(member, name)
        formatted_history_string = self.format(convo.context._display_context, convo.member.display_name, convo.model.display_name) if convo.context._display_context else errors.HistoryErrors.HISTORY_EMPTY
        
        file_like = io.BytesIO(formatted_history_string.encode())
        file_like.name = f"{convo.display_name}-{datetime.datetime.now()}-transcript.txt"

        await interaction.user.send(f"{convo.member.name}'s {confighandler.get_config('bot_name')} Transcript ({convo.display_name})", file=discord.File(file_like))
        await interaction.response.send_message("I have sent the conversation transcript to our direct messages.")
    
        
            
    @discord.app_commands.command(name="history", description="Get a past saved conversation.")
    async def get_chat_history(self, interaction: discord.Interaction, history_id: str):
        try:
            with history.DGHistorySession() as history_session:
                if history_chat := history_session.retrieve_chat_history(history_id):
                    if history_chat.private == False or interaction.user.id == history_chat.user:
                        list_history: Any = history_chat.data
                        history_user = self.client.get_user(history_chat.user)
                        formatted = self.format(data=list_history, username=history_user.display_name if history_user else "Deleted User", model="AI") if list_history else errors.HistoryErrors.HISTORY_EMPTY

                        history_file = io.BytesIO(formatted.encode())
                        history_file.name = f"{history_chat.name}-transcript.txt"

                        await interaction.user.send(file=discord.File(history_file))
                        return await interaction.response.send_message("I have sent the history transcript to our direct messages.")
                raise exceptions.HistoryError(errors.HistoryErrors.HISTORY_DOESNT_EXIST)
        except ValueError:
            raise exceptions.HistoryError(errors.HistoryErrors.INVALID_HISTORY_ID)
        
async def setup(client):
    await client.add_cog(History(client))
