from typing import List
import discord
from discord.app_commands.models import Choice

class ModelChoiceTransformer(discord.app_commands.Transformer):
    async def autocomplete(self, interaction: discord.Interaction[discord.Client], value: int | float | str) -> List[Choice[str | int | float]]:
        ...
        
class ChatChoiceTransformer(discord.app_commands.Transformer):
    async def autocomplete(self, interaction: discord.Interaction[discord.Client], value: int | float | str) -> List[Choice[str | int | float]]:
        ...

