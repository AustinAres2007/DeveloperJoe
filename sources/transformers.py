from typing import List
import discord
from discord.app_commands.models import Choice

from . import (
    usermodelhandler,
    models
)
from .common import (
    commands_utils
)

class ModelChoiceTransformer(discord.app_commands.Transformer):
    async def autocomplete(self, interaction: discord.Interaction[discord.Client], value: int | float | str) -> List[Choice[str | int | float]]:
        user_custom_models = usermodelhandler.get_user_models(interaction.user)
        models_copy = models.MODEL_CHOICES.copy()
        
        for model in user_custom_models:
            models_copy.append(Choice(name=f"{commands_utils.get_modeltype_from_name(model.based_model)} ({model.model_name})", value="d"))
    async def transform(self, interaction: discord.Interaction[discord.Client], value: usermodelhandler.Any) -> usermodelhandler.Any:
        return await super().transform(interaction, value)
        
class ChatChoiceTransformer(discord.app_commands.Transformer):
    async def autocomplete(self, interaction: discord.Interaction[discord.Client], value: int | float | str) -> List[Choice[str | int | float]]:
        ...

