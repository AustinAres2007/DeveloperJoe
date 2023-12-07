import json
from discord import Guild

from sources.common import developerconfig
from . import (
    database
)

class DGGuildDatabasePermissionHandler(database.DGDatabaseSession):
    def __init__(self, guild: Guild, database: str = developerconfig.DATABASE_FILE, reset_if_failed_check: bool = True):
        super().__init__(database, reset_if_failed_check)
        self.guild = guild
        
    def get_permission_list(self, _object: str) -> list[int]:
        try:
            json_data_string = self._exec_db_command("SELECT permission_json FROM permissions WHERE gid=?", (self.guild.id,))[0][0]
            return json.loads(json_data_string)[_object]
        except KeyError:
            raise KeyError(f"No rules for {_object}.")
        
def get_guild_object_permissions(guild: Guild, permission_object: str) -> list[int]:
    with DGGuildDatabasePermissionHandler(guild) as permission_handler:
        return permission_handler.get_permission_list(permission_object)