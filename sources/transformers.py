from __future__ import annotations
from typing import TYPE_CHECKING, List
import discord
from discord.app_commands.models import Choice

from . import (
    usermodelhandler,
    models,
    history
)
from .common import (
    commands_utils
)

if TYPE_CHECKING:
    from ..joe import (
        DeveloperJoe
    )
    
class ModelChoiceTransformer(discord.app_commands.Transformer):
    async def autocomplete(self, interaction: discord.Interaction[DeveloperJoe], value: int | float | str) -> List[Choice[str | int | float]]:
        user_custom_models = usermodelhandler.get_user_models(interaction.user)
        models_copy = models.MODEL_CHOICES.copy()
        
        for model in user_custom_models:
            model_based = commands_utils.get_modeltype_from_name(model.based_model)
            models_copy.append(Choice(name=f"{model_based.display_name} ({model.model_name})", value=f"{model_based.model}|{model.model_name}"))
        
        return models_copy
    
    async def transform(self, _interaction: discord.Interaction[DeveloperJoe], value) -> tuple[str | None, str | None]:
        try:
            model, custom = str(value).split("|")
        except ValueError:
            return (value, None)

        if value is None:
            return (None, None)
        
        return (model, custom)

class CustomModelChoiceTransformer(discord.app_commands.Transformer):
    async def autocomplete(self, interaction: discord.Interaction[DeveloperJoe], value: int | float | str) -> List[Choice[str | int | float]]:
        user_custom_models = usermodelhandler.get_user_models(interaction.user)
        custom_models = []
        
        for model in user_custom_models:
            model_based = commands_utils.get_modeltype_from_name(model.based_model)
            custom_models.append(Choice(name=f"{model_based.display_name} ({model.model_name})", value=model.model_name))

        return custom_models
    
    async def transform(self, _interaction: discord.Interaction[DeveloperJoe], value: usermodelhandler.Any) -> usermodelhandler.Any:
        return value

class VanillaModelChoiceTransformer(discord.app_commands.Transformer):
    async def autocomplete(self, _interaction: discord.Interaction[DeveloperJoe], value: int | float | str) -> List[Choice[str | int | float]]:
        return models.MODEL_CHOICES
    
    async def transform(self, _interaction: discord.Interaction[DeveloperJoe], value: usermodelhandler.Any) -> usermodelhandler.Any:
        return value
    
class ChatChoiceTransformer(discord.app_commands.Transformer):
    
    async def autocomplete(self, interaction: discord.Interaction[DeveloperJoe], value: int | float | str) -> List[Choice[str | int | float]]:
        try:
            assert isinstance(member := interaction.user, discord.Member)
            return [Choice(name=c.display_name, value=c.display_name) for c in interaction.client.get_all_user_conversations(member).values()]
        except AssertionError:
            return []

    async def transform(self, _interaction: discord.Interaction[DeveloperJoe], value: usermodelhandler.Any) -> usermodelhandler.Any:
        return value

class HistoryChoiceTransformer(discord.app_commands.Transformer):
    async def autocomplete(self, interaction: discord.Interaction[DeveloperJoe], value: int | float | str) -> List[Choice[str | int | float]]:
        return [Choice(name=u_history.name, value=u_history.history_id) for u_history in history.get_user_histories(str(interaction.user.id))]

    async def transform(self, _interaction: discord.Interaction[DeveloperJoe], value: usermodelhandler.Any) -> usermodelhandler.Any:
        return value

class ReadableBooleanTransformer(discord.app_commands.Transformer):
    async def autocomplete(self, interaction: discord.Interaction[DeveloperJoe], value: int | float | str) -> List[Choice[str | int | float]]:
        return [Choice(name="Yes", value="1"), Choice(name="No", value="0")]

    async def transform(self, _interaction: discord.Interaction[DeveloperJoe], value: usermodelhandler.Any) -> usermodelhandler.Any:
        return bool(int(value))
    
ModelChoices = discord.app_commands.Transform[tuple[str | None, str | None], ModelChoiceTransformer]
CustomModelChoices = discord.app_commands.Transform[str, CustomModelChoiceTransformer]
VanillaModelChoices = discord.app_commands.Transform[str, VanillaModelChoiceTransformer]
ChatChoices = discord.app_commands.Transform[str, ChatChoiceTransformer]
HistoryChoices = discord.app_commands.Transform[str, HistoryChoiceTransformer]
BooleanChoices = discord.app_commands.Transform[bool, ReadableBooleanTransformer]