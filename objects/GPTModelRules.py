import json
from objects import GPTDatabase

from typing import Union, TypedDict, Any

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
    
    def retrieve_guild_models(self, guild_id: int, model: Union[str, None]=None) -> Union[list[GuildModels], GuildModels, None, dict]:
        _guild_pointer = self._exec_db_command("SELECT jsontables FROM model_rules WHERE gid=?", (guild_id,)).fetchall()
        guild_models = json.loads(_guild_pointer[0][0]) if _guild_pointer else None

        if isinstance(model, str) and isinstance(guild_models, GuildModels):
            return guild_models[model] if model in guild_models else None
        return guild_models

    def upload_guild_model(self, model: str, role_id: int, guild_id: int) -> Union[list[GuildModels], GuildModels, None, dict]:
        guild_rules = self.retrieve_guild_models(guild_id) 

        if model in list(guild_rules) and isinstance(guild_rules, dict) and role_id not in guild_rules[model]: # type: ignore
            guild_rules[model].append(role_id)
    
        elif isinstance(guild_rules, dict) and model not in list(guild_rules):
            guild_rules[model] = [role_id]

        else:
            return None
        
        json_string = json.dumps(guild_rules)
        self._exec_db_command("UPDATE model_rules SET jsontables=? WHERE gid=?", (json_string, guild_id))

        return guild_rules

    def add_guild(self, guild_id: int) -> Union[None, Any]:
        if self.retrieve_guild_models(guild_id) == None:
            self._exec_db_command("INSERT INTO model_rules VALUES(?, ?)", (guild_id, json.dumps({})))
            return self.retrieve_guild_models(guild_id)
    
    def del_guild(self, guild_id: int) -> Union[None, Any]:
        if self.retrieve_guild_models(guild_id) != None:
            return self._exec_db_command("DELETE FROM model_rules WHERE gid=?", (guild_id,))
            
            

