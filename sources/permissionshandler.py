import json
from discord import Guild

from .common import (
    developerconfig
)
from . import (
    database
)

class DGGuildDatabasePermissionHandler(database.DGDatabaseSession):
    def __init__(self, guild: Guild, database: str = developerconfig.DATABASE_FILE, reset_if_failed_check: bool = True):
        super().__init__(database, reset_if_failed_check)
        self.guild = guild
    
    def get_all_permissions(self) -> dict[str, list[int]]:
        try:
            json_string = self._exec_db_command("SELECT permission_json FROM permissions WHERE gid=?", (self.guild.id,))[0][0]
            data: dict[str, list[int]] = json.loads(json_string)
            
            return data
        except KeyError:
            raise KeyError(f"{self.guild} does not exist within permission database.")
            
    def get_permission_list(self, _object: str) -> list[int]:
        try:
            json_data_string = self._exec_db_command("SELECT permission_json FROM permissions WHERE gid=?", (self.guild.id,))[0][0]
            return json.loads(json_data_string)[_object]
        except KeyError:
            raise KeyError(f"No rules for {_object}.")
    
    def add_to_permission_list(self, _object: str, roles: list[int]) -> None:
        new_entry = self.get_all_permissions().copy()
        try:
            new_entry[_object].extend(roles)
        except KeyError:
            new_entry[_object] = roles
        
        permission_data = json.dumps(new_entry)
        self._exec_db_command("UPDATE permissions SET permission_json=? WHERE gid=?", (permission_data, self.guild.id,))
    
    def remove_from_permission_list(self, _object: str) -> None:
        new_entry = self.get_all_permissions().copy()
        try:
            del new_entry[_object]
        except KeyError:
            raise KeyError(f"No rules for {_object}.")
        
        permission_data = json.dumps(new_entry)
        self._exec_db_command("UPDATE permissions SET permission_json=? WHERE gid=?", (permission_data, self.guild.id,))
        
def get_guild_object_permissions(guild: Guild, permission_object: str) -> list[int]: 
    with DGGuildDatabasePermissionHandler(guild) as permission_handler:
        try:
            roles = permission_handler.get_permission_list(permission_object)
            return roles
        except KeyError:
            return []

def add_guild_permission(guild: Guild, permission_object: str, roles: list[int]) -> None:
    with DGGuildDatabasePermissionHandler(guild) as permission_handler:
        permission_handler.add_to_permission_list(permission_object, roles)

def remove_guild_permission(guild: Guild, permission_object: str) -> None:
    with DGGuildDatabasePermissionHandler(guild) as permission_handler:
        permission_handler.remove_from_permission_list(permission_object)
        
        
            