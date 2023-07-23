import json, discord
from objects import GPTDatabase, GPTExceptions

from typing import Union, TypedDict, Any, Iterable

GuildModels = TypedDict('GuildModels', {"model": list[int]})

class GPTModelRules(GPTDatabase.GPTDatabase):
    def __enter__(self):
        return self

    def __exit__(self, type_, value_, traceback_):
        super().__exit__(type_, value_, traceback_)

    def __init__(self):
        """
        Handles user GPT Model permissions based on roles they possess.
        """
        super().__init__()
    
    def retrieve_guild_models(self, guild_id: int, model: Union[str, None]=None) -> Union[GuildModels, Iterable]:
        _guild_pointer = self._exec_db_command("SELECT jsontables FROM model_rules WHERE gid=?", (guild_id,)).fetchall()
        guild_models = json.loads(_guild_pointer[0][0]) if _guild_pointer else [None]

        if isinstance(model, str) and isinstance(guild_models, dict):
            return guild_models[model] if model in guild_models else [None]
        return guild_models

    def upload_guild_model(self, model: str, role: discord.Role, guild: discord.Guild) -> Union[list[GuildModels], GuildModels, None, dict]:
        guild_rules = self.retrieve_guild_models(guild.id) 

        if model in list(guild_rules) and isinstance(guild_rules, dict) and role.id not in guild_rules[model]: # type: ignore
            guild_rules[model].append(role.id)
    
        elif isinstance(guild_rules, dict) and model not in list(guild_rules):
            guild_rules[model] = [role.id]

        else:
            return None
        
        json_string = json.dumps(guild_rules)
        self._exec_db_command("UPDATE model_rules SET jsontables=? WHERE gid=?", (json_string, guild.id))

        return guild_rules

    def remove_guild_model(self, model: str, role: discord.Role, guild: discord.Guild):
        models_allowed_roles = self.retrieve_guild_models(guild.id)

        if isinstance(models_allowed_roles, dict):
            if model in list(models_allowed_roles) and role.id in list(models_allowed_roles[model]): # type: ignore
                models_allowed_roles[model].remove(role.id)
            elif model not in list(models_allowed_roles):
                raise GPTExceptions.ModelNotExist(f"{model} model lock list does not exist within {guild.name} database.")
            else:
                return None
        
        json_string = json.dumps(models_allowed_roles)
        self._exec_db_command("UPDATE model_rules SET jsontables=? WHERE gid=?", (json_string, guild.id))

        return models_allowed_roles

    def add_guild(self, guild_id: int) -> Union[None, Any]:
        if self.retrieve_guild_models(guild_id) == None:
            self._exec_db_command("INSERT INTO model_rules VALUES(?, ?)", (guild_id, json.dumps({})))
            return self.retrieve_guild_models(guild_id)
        raise GPTExceptions.ModelGuildError("Guild with specified ID has already been registered.")
    
    def del_guild(self, guild_id: int) -> Union[None, Any]:
        if self.retrieve_guild_models(guild_id) != None:
            return self._exec_db_command("DELETE FROM model_rules WHERE gid=?", (guild_id,))
    
    def user_has_model_permissions(self, user_role: discord.Role, model: str):
        model_roles = self.retrieve_guild_models(user_role.guild.id, model)
        def _does_have_senior_role():
            return [True for r_id in model_roles if user_role >= user_role.guild.get_role(int(r_id))]

        return (user_role.name == "@everyone" and bool(model_roles) == False) \
        or (user_role.id in model_roles if isinstance(model_roles, list) else False) \
        or (not model_roles or bool(_does_have_senior_role()))
            
            

