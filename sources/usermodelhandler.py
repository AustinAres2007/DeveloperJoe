import json
from typing import Type
from . import (
    database,
    models
)
from .common import (
    developerconfig,
)

import discord

class DGUserModelCustomisationHandler(database.DGDatabaseSession):
    def __init__(self, database: str = developerconfig.DATABASE_FILE, reset_if_failed_check: bool = True):
        super().__init__(database, reset_if_failed_check)
    
    def fetch_user_models(self, user: discord.User | discord.Member) -> ...:
        _models = self._exec_db_command("SELECT * FROM custom_models WHERE uid=?", (user.id,))
        return _models
    
    def insert_user_model(self, user: discord.User | discord.Member, based_model: models.AIModel | Type[models.AIModel], model_name: str, **kwargs) -> None: # TODO: Figure out params
        self._exec_db_command("INSERT INTO custom_models VALUES(?, ?, ?, ?)", (user.id, based_model.model, model_name, json.dumps(kwargs)))
        
def user_has_model(user: discord.User | discord.Member, model_name: str) -> bool:
    with DGUserModelCustomisationHandler() as DGUmch:
        return model_name in DGUmch.fetch_user_models(user) # XXX: Will always return False due to fetch_user_models is a list of tuples. Must compare model_name with fetch_user_models[0][2] which is the name.