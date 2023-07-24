import json, discord
from objects import GPTDatabase, GPTExceptions

from typing import Union, TypedDict, Any, Iterable

GuildModels = TypedDict('GuildModels', {"model": list[int]})

class GPTModelRules(GPTDatabase.GPTDatabase):
    def __enter__(self):

        print(self.in_database)

        if self.in_database == False:
            self.add_guild()
            self.in_database = bool(self.get_models_for_guild())

        return self

    def __exit__(self, type_, value_, traceback_):
        self.database.commit()
        self.database.close()

    def __init__(self, guild: discord.Guild):
        """
        Handles user GPT Model permissions based on roles they possess.
        """
        super().__init__()
        self.guild: discord.Guild = guild
        self._in_database = bool(self.get_models_for_guild())
    

    @property
    def in_database(self) -> bool:
        return self._in_database
    
    @in_database.setter
    def in_database(self, value: bool):
        self._in_database = value

    def retrieve_guild_models(self, model: str) -> Union[GuildModels, Iterable]:
        _guild_pointer = self._exec_db_command("SELECT jsontables FROM model_rules WHERE gid=?", (self.guild.id,)).fetchall()
        
        if _guild_pointer:
            guild_models = json.loads(_guild_pointer[0][0]) 

            if model in guild_models:
                return guild_models[model] 
            raise GPTExceptions.GuildNotExist(self.guild)
            
        raise GPTExceptions.ModelNotExist(self.guild, model)
        
    def get_models_for_guild(self) -> dict[str, list[int]]:
        models = self._get_raw_models_database()
        print(models)
        return json.loads(models[0][0])
    
    def _get_raw_models_database(self) -> list[tuple[str, ...]]:
        raw_models = self._exec_db_command("SELECT jsontables FROM model_rules WHERE gid=?", (self.guild.id,)).fetchall()
        if raw_models:
            return raw_models
        raise GPTExceptions.GuildNotExist(self.guild)
    
    def upload_guild_model(self, model: str, role: discord.Role) -> Union[list[GuildModels], GuildModels, None, dict]:
        guild_rules = self.retrieve_guild_models(model) 

        if model in list(guild_rules) and isinstance(guild_rules, dict) and role.id not in guild_rules[model]: # type: ignore
            guild_rules[model].append(role.id)
    
        elif isinstance(guild_rules, dict) and model not in list(guild_rules):
            guild_rules[model] = [role.id]

        else:
            return None
        
        json_string = json.dumps(guild_rules)
        self._exec_db_command("UPDATE model_rules SET jsontables=? WHERE gid=?", (json_string, self.guild.id))

        return guild_rules

    def remove_guild_model(self, model: str, role: discord.Role):
        models_allowed_roles = self.retrieve_guild_models(model)

        if isinstance(models_allowed_roles, dict):
            if model in list(models_allowed_roles) and role.id in list(models_allowed_roles[model]): # type: ignore
                models_allowed_roles[model].remove(role.id)
            elif model not in list(models_allowed_roles):
                raise GPTExceptions.ModelNotExist(self.guild, model)
            else:
                return None
        
        json_string = json.dumps(models_allowed_roles)
        self._exec_db_command("UPDATE model_rules SET jsontables=? WHERE gid=?", (json_string, self.guild.id))

        return models_allowed_roles

    def add_guild(self) -> Union[None, Any]:
        if self.in_database == False:
            self._exec_db_command("INSERT INTO model_rules VALUES(?, ?)", (self.guild.id, json.dumps({})))
            return bool(self.get_models_for_guild())
        raise GPTExceptions.ModelGuildError("Guild with specified ID has already been registered.")
    
    def del_guild(self) -> Union[None, Any]:
        if self.in_database == True:
            return self._exec_db_command("DELETE FROM model_rules WHERE gid=?", (self.guild.id,))
        raise GPTExceptions.GuildNotExist(self.guild)
    
    def user_has_model_permissions(self, user_role: discord.Role, model: str):
        model_roles = self.retrieve_guild_models(model)
        def _does_have_senior_role():
            return [True for r_id in model_roles if user_role >= user_role.guild.get_role(int(r_id))]

        return (bool(model_roles) == False) \
        or (user_role.id in model_roles if isinstance(model_roles, list) else False) \
        or (not model_roles or bool(_does_have_senior_role())) # Check if the model has no restrictions. The user has a role contained within any possible restrictions, or if the user has a role that is higher that of any lower role.
            
            

