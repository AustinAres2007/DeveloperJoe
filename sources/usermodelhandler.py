from __future__ import annotations
from dataclasses import dataclass
import json
from typing import TYPE_CHECKING, Any, Type

from regex import D
from . import (
    database,
    exceptions
)
from .common import (
    developerconfig,
)

import discord

__all__ = (
    "CustomModel",
    "DGUserModelCustomisationHandler",
    "user_has_model",
    "get_user_models",
    "get_user_model"
    
)

if TYPE_CHECKING:
    from . import (
        models
    )
    
@dataclass
class CustomModel:
    owner_id: int
    based_model: str
    model_name: str
    
    _model_json_raw: str
    
    def __post_init__(self):
        self._model_json_obj = json.loads(str(self._model_json_raw))
        for k, v in self._model_json_obj.items():
            setattr(self, k, v)
            
    def get_attribute(self, attribute: str) -> Any | None:
        return self._model_json_obj.get(attribute, None)
    
    def __str__(self) -> str:
        return self.model_name
    
    def __repr__(self) -> str:
        __repr = f"<CustomModel(owner_id={self.owner_id}, based_model={self.based_model}, model_name={self.model_name}, "
        model_attrs = (f"{k}={v}" for k, v in self._model_json_obj.items())
        __repr += ", ".join(model_attrs) + ")>"

        return __repr
    
class DatabaseSQLCommands:
    FETCH_ALL = "SELECT * FROM custom_models WHERE uid=?"
    FETCH_SPECIFIED = "SELECT * FROM custom_models WHERE uid=? AND model_name=?"
    ADD_MODEL = "INSERT INTO custom_models VALUES(?, ?, ?, ?)"
    UPDATE_MODEL = "UPDATE custom_models SET based_from=?, model_json=? WHERE uid=? AND model_name=?"
    DROP_MODEL = "DELETE FROM custom_models WHERE uid=? AND model_name=?"
    
class DGUserModelCustomisationHandler(database.DGDatabaseSession):
    def __init__(self, database: str = developerconfig.DATABASE_FILE, reset_if_failed_check: bool = True):
        super().__init__(database, reset_if_failed_check)
    
    def fetch_user_models(self, user: discord.User | discord.Member) -> list[tuple]:
        return self._exec_db_command(DatabaseSQLCommands.FETCH_ALL, (user.id,))
        
    def fetch_user_model(self, user: discord.User | discord.Member, model_name: str) -> tuple | None:
        try:
            return self._exec_db_command(DatabaseSQLCommands.FETCH_SPECIFIED, (user.id, model_name,))[0]
        except IndexError:
            return None
        
    def insert_user_model(self, user: discord.User | discord.Member, based_model: models.AIModel | Type[models.AIModel], model_name: str, **kwargs) -> None:
        self._exec_db_command(DatabaseSQLCommands.ADD_MODEL, (user.id, based_model.model, model_name, json.dumps(kwargs),))
    
    def destroy_custom_model(self, user: discord.User | discord.Member, model_name: str) -> None:
        self._exec_db_command(DatabaseSQLCommands.DROP_MODEL, (user.id, model_name,))
        
    def update_user_model(self, user: discord.User | discord.Member, based_model: models.AIModel | Type[models.AIModel], model_name: str, **new_kwargs) -> None:
        existsing_params = self.fetch_user_model(user, model_name)
        
        if existsing_params == None:
            raise exceptions.ModelError(f'{user} has no custom model matching "{model_name}"')
        elif existsing_params[3] == "null":
            self.destroy_custom_model(user, model_name)
            raise exceptions.ModelError(f"Corrupted Model: {model_name} belonging to {user.id} ({user})")
        
        existsing_kwargs = json.loads(existsing_params[3]) | new_kwargs
        self._exec_db_command(DatabaseSQLCommands.UPDATE_MODEL, (based_model.model, json.dumps(existsing_kwargs), user.id, model_name,))
    
def user_has_model(user: discord.User | discord.Member, model_name: str) -> bool:
    with DGUserModelCustomisationHandler() as DGUmch:
        return model_name in (model[2] for model in DGUmch.fetch_user_models(user))

def get_user_model(user: discord.User | discord.Member, model_name: str) -> CustomModel | None:
    with DGUserModelCustomisationHandler() as DGUmch:
        model_data = DGUmch.fetch_user_model(user, model_name)
        return CustomModel(*model_data) if model_data else None

def get_user_models(user: discord.User | discord.Member) -> list[CustomModel]:
    with DGUserModelCustomisationHandler() as DGUmch:
        return [CustomModel(*m) for m in DGUmch.fetch_user_models(user)]

def update_user_model(user: discord.User | discord.Member, based_model: models.AIModel | Type[models.AIModel], model_name: str, **new_kwargs) -> CustomModel | None:
    with DGUserModelCustomisationHandler() as DGUmch:
        DGUmch.update_user_model(user, based_model, model_name, **new_kwargs)
    return get_user_model(user, model_name)

def destroy_user_model(user: discord.User | discord.Member, model_name: str) -> CustomModel | None:
    model = get_user_model(user, model_name)
    
    with DGUserModelCustomisationHandler() as DGUmch:
        DGUmch.destroy_custom_model(user, model_name)
    
    return model