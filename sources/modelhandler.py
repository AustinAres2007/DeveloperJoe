from __future__ import annotations
import json, discord

from typing import ( 
    Any as _Any,
    TYPE_CHECKING
)

from . import (
    database, 
    exceptions
)
from .common import (
    commands_utils,
)

__all__ = [
    "DGGuildDatabaseModelHandler"
]

if TYPE_CHECKING:
    from . import (
        models
    )
class DGGuildDatabaseModelHandler(database.DGDatabaseSession):
    # Old: DGRules
    """Database connection that manages model permissions (Model Lock List, or MLL, etc..) maybe more in the future."""

    def __enter__(self):
        
        self.in_database = self.has_guild()
        
        if self.in_database == False:
            self.in_database = bool(self.add_guild())
            
        return super().__enter__()

    def __exit__(self, type_, value_, traceback_):
        super().__exit__(type_, value_, traceback_)

    def __init__(self, guild: discord.Guild):
        """Class that manages model permissions (Model Lock List, etc..) maybe more in the future."""
        
        self._guild: discord.Guild = guild
        self.in_database = False

        super().__init__()
    

    def _get_raw_models_database(self) -> list[tuple[str, ...]]:
        """Retrieves all models in the lock list of the specified guild.

        Raises:
            exceptions.GuildNotExist: If the guild does not exist in the lock list.

        Returns:
            list[tuple[str, ...]]: The models.
        """
        raw_models = self._exec_db_command("SELECT jsontables FROM model_rules WHERE gid=?", (self.guild.id,))
        if raw_models:
            return raw_models
        raise exceptions.GuildNotExist(self.guild)
    
    def _dump_into_database(self, __object: _Any) -> list[_Any]:
        """Dumps raw dictionary data into the guilds lock list

        Args:
            __object (_Any): Data.

        Returns:
            list[_Any]: SQLite3 Response.
        """
        json_string = json.dumps(__object)
        return self._exec_db_command("UPDATE model_rules SET jsontables=? WHERE gid=?", (json_string, self.guild.id))

    @property
    def in_database(self) -> bool:
        return self._in_database
    
    @in_database.setter
    def in_database(self, value: bool):
        self._in_database = value

    @property
    def guild(self):
        return self._guild
    
    def get_guild_model(self, model: models.AIModelType) -> list[int]:
        """Retrieves a specified model from the lock list.

        Args:
            model (models.AIModelType): The model to be fetched.

        Raises:
            exceptions.ModelNotExist: If the specified model does not exist within the lock list.

        Returns:
            list[int]: A list of user role IDs attached to the model.
        """
        models = self.get_guild_models()
        if models:
            if model.model in models: 
                return models[model.model]
            raise exceptions.ModelNotExist(self.guild, model.model)
        return []
    
    def get_guild_models(self) -> dict[models.AIModelType, list[int]]:
        """Fetches all guild models from the lock list.

        Returns:
            dict[models.AIModelType, list[int]]: _description_
        """
        models = self._get_guild_models_raw()
        return {model: data for model, data in models.items()}

    def _get_guild_models_raw(self) -> dict[str, list[int]]:
        """Fetches raw database data regarding the guilds models

        Returns:
            dict[str, list[int]]: Returned database data.
        """
        _guild_pointer = self._get_raw_models_database()

        if _guild_pointer:
            guild_models = json.loads(_guild_pointer[0][0])
            return guild_models 
        return {}
    
    def has_guild(self) -> bool:
        """If the guild is in the database.

        Returns:
            bool: If the guild is, or is not present.
        """
        return bool(self._exec_db_command("SELECT jsontables FROM model_rules WHERE gid=?", (self.guild.id,)))
    
    def upload_guild_model(self, model: models.AIModelType, role: discord.Role) -> bool:
        """Adds a specified role to the lock list.

        Args:
            model (models.AIModelType): The model to be locked
            role (discord.Role): What role to be locked.

        Returns:
            bool: If the operation was successful or not.
        """
        guild_rules = self._get_guild_models_raw() 

        if model.model in list(guild_rules) and isinstance(guild_rules, dict) and role.id not in guild_rules[model.model]:
            guild_rules[model.model].append(role.id)
    
        elif isinstance(guild_rules, dict) and model not in list(guild_rules):
            guild_rules[model.model] = [role.id]

        else:
            return False
        
        self._dump_into_database(guild_rules)
        
        return True

    def remove_guild_model(self, model: models.AIModelType, role: discord.Role):
        """Performs the opposite of `upload_guild_model` (Removes a role from the lock list)

        Args:
            model (models.AIModelType): The role to be unlocked
            role (discord.Role): The role to be freed.

        Raises:
            exceptions.ModelNotExist: If the model is not present in the lock list.

        Returns:
            None
        """
        models_allowed_roles = self._get_guild_models_raw()

        if model.model in list(models_allowed_roles) and isinstance(models_allowed_roles, dict) and role.id in list(models_allowed_roles[model.model]):
            models_allowed_roles[model.model].remove(role.id)
        elif model not in list(models_allowed_roles):
            raise exceptions.ModelNotExist(self.guild, model.display_name)
        else:
            return
        
        self._dump_into_database(models_allowed_roles)

    def add_guild(self) -> bool:  
        """Adds a guild to the lock list database.

        Raises:
            exceptions.GuildExistsError: If the guild is already present in the database.

        Returns:
            bool: Always True if `GuildExistsError` is not raised.
        """
        if self.in_database == False:
            self._exec_db_command("INSERT INTO model_rules VALUES(?, ?)", (self.guild.id, json.dumps({})))
            return self.has_guild()
        raise exceptions.GuildExistsError(self.guild)
    
    def del_guild(self) -> bool:
        """Removes a guild from the lock list database.

        Raises:
            exceptions.GuildNotExist: If the guild is already not present in the database.

        Returns:
            bool: _description_
        """
        if self.in_database == True:
            self._exec_db_command("DELETE FROM model_rules WHERE gid=?", (self.guild.id,))
            return not self.has_guild()
        raise exceptions.GuildNotExist(self.guild)
    
    def user_has_model_permissions(self, user_role: discord.Role, model: models.AIModelType) -> bool:
        """Checks if the specified role has permission to used a specified model.

        Args:
            user_role (discord.Role): The role to be checked.
            model (models.AIModelType): The model to be checked.

        Returns:
            bool: True if usable, False if otherwise.
        """
        try:
            model_roles = self.get_guild_model(model)
            def _does_have_senior_role():
                return [True for r_id in model_roles if user_role >= user_role.guild.get_role(int(r_id))]

            return (bool(model_roles) == False) \
            or (user_role.id in model_roles if isinstance(model_roles, list) else False) \
            or (not model_roles or bool(_does_have_senior_role())) # Check if the model has no restrictions. The user has a role contained within any possible restrictions, or if the user has a role that is higher that of any lower role.
        except exceptions.ModelNotExist:
            return True

def user_has_model_permissions(member: discord.Member, model: models.AIModelType):
    if isinstance(member, discord.Member):
        with DGGuildDatabaseModelHandler(member.guild) as check_rules:
            return bool(check_rules.user_has_model_permissions(member.roles[-1], model))
    else:
        raise TypeError("member must be discord.Member, not {}".format(member.__class__))