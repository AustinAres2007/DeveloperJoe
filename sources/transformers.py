from __future__ import annotations
from typing import TYPE_CHECKING, List
import discord
from discord.app_commands.models import Choice

from . import (
    usermodelhandler,
    models
)
from .common import (
    commands_utils
)

if TYPE_CHECKING:
    from ..joe import (
        DeveloperJoe
    )
    
class ModelChoiceTransformer(discord.app_commands.Transformer):
    async def autocomplete(self, interaction: discord.Interaction[discord.Client], value: int | float | str) -> List[Choice[str | int | float]]:
        user_custom_models = usermodelhandler.get_user_models(interaction.user)
        models_copy = models.MODEL_CHOICES.copy()
        
        for model in user_custom_models:
            model_based = commands_utils.get_modeltype_from_name(model.based_model)
            models_copy.append(Choice(name=f"{model_based.display_name} ({model.model_name})", value=f"{model_based.model}|{model.model_name}"))
        
        return models_copy
    
    async def transform(self, interaction: discord.Interaction[discord.Client], value) -> tuple[str | None, str | None]:
        try:
            model, custom = str(value).split("|")
        except ValueError:
            return (value, None)

        if value is None:
            return (None, None)
        
        return (model, custom)
        
    
class ChatChoiceTransformer(discord.app_commands.Transformer):
    
    async def autocomplete(self, interaction: discord.Interaction[DeveloperJoe], value: int | float | str) -> List[Choice[str | int | float]]:
        try:
            assert isinstance(member := interaction.user, discord.Member)
            return [Choice(name=c.display_name, value=c.display_name) for c in interaction.client.get_all_user_conversations(member).values()]
        except AssertionError:
            return []

    async def transform(self, interaction: discord.Interaction[discord.Client], value: usermodelhandler.Any) -> usermodelhandler.Any:
        return value
