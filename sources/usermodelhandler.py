import json
from . import (
    database
)
from .common import (
    developerconfig
)

import discord

# self._exec_db_command("INSERT INTO permissions VALUES(?, ?)", (guild_id, json.dumps(developerconfig.default_permission_keys),))

class DGUserModelCustomisationHandler(database.DGDatabaseSession):
    def __init__(self, database: str = developerconfig.DATABASE_FILE, reset_if_failed_check: bool = True):
        super().__init__(database, reset_if_failed_check)
    
    def fetch_user_models(self, user: discord.User | discord.Member) -> ...:
        _models = self._exec_db_command("SELECT model_json FROM custom_models WHERE uid=?", (user.id,))
        return _models
    
    def insert_user_model(self, user: discord.User | discord.Member, model_name: str, **kwargs) -> None: # TODO: Figure out params
        self._exec_db_command("INSERT INTO custom_models VALUES(?, ?, ?)", (user.id, model_name, json.dumps(kwargs)))