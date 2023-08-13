import discord as _discord, json as _json

from . import database as _database, config as _config, utils as _utils
from typing import Union as _Union, Any as _Any

class GuildData:
    def __init__(self, data: list):
        try:
            print(data)
            self.guild_id = data[0][0]
            self.author_id = data[0][1]
            self.config_data: dict = _json.loads(data[0][2])
        except IndexError: 
            self.author_id = self.guild_id = 0
            self.config_data = {}
            
class DGGuildConfigSession:
    def __enter__(self):
        return self

    def __exit__(self, type_, value_, traceback_):
        self._manager.database.commit()
        self._manager.database.close()
    
    def __init__(self, guild: _discord.Guild):
        super().__init__()
        self._guild = guild
        self._manager = DGGuildConfigSessionManager(self)

    @property
    def guild(self) -> _discord.Guild:
        return self._guild
    
    @_utils.has_config
    def edit_guild(self, **keys):
        
        if set(keys.keys()).issubset(set(_config.GUILD_CONFIG_KEYS.keys())):
            data: GuildData = self._manager.get_guild()
            data.config_data.update(keys)
            self._manager.edit_guild(data.config_data)
    
    @_utils.has_config
    def get_guild(self) -> GuildData:
        return self._manager.get_guild()
    
    def get_config(self, attribute: str):
        config = self.get_guild().config_data
        if attribute in config:
            return config[attribute]
        
class DGGuildConfigSessionManager(_database.DGDatabaseSession):
    def __init__(self, session) -> None:
        super().__init__()
        self._session = session
    
    def get_guild(self, gid: _Union[int, None]=None) -> GuildData:
        return GuildData(self._exec_db_command("SELECT * FROM guild_configs WHERE gid=?", (gid if isinstance(gid, int) else self._session.guild.id,)))
    
    def has_guild(self, gid: _Union[int, None]=None) -> bool:
        return bool(self.get_guild(gid if isinstance(gid, int) else self._session.guild.id).guild_id)
    
    def add_guild(self):
        self._exec_db_command("INSERT INTO guild_configs VALUES(?, ?, ?)", (self._session.guild.id, self._session.guild.owner_id, _json.dumps(_config.GUILD_CONFIG_KEYS),))
    
    def edit_guild(self, data: dict):
        self._exec_db_command("UPDATE guild_configs SET json=? WHERE gid=?", (_json.dumps(data), self._session.guild.id))

def get_guild_config(guild: _discord.Guild) -> GuildData:
    with DGGuildConfigSession(guild) as cs:
        return cs.get_guild()

def edit_guild_config(guild: _discord.Guild, key: str, value: _Any) -> None:
    with DGGuildConfigSession(guild) as cs:
        return cs.edit_guild(**{key: value})
        