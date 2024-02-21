from __future__ import annotations
from textwrap import indent

import discord, json, yaml
from typing import Any, TYPE_CHECKING, Self, Type

from . import (
    database, 
    exceptions
)
from .common import (
    decorators,
    developerconfig,
    common,
    commands_utils,
    types
)

if TYPE_CHECKING:
    from . import (
        models
    )
# XXX: Must make DGGuildModelSession (For init())

__all__ = [
    "GuildData",
    "DGGuildDatabaseConfigHandler",
    "get_guild_config",
    "edit_guild_config",
    "get_guild_config_attribute",
    "reset_guild_config"
]

def generate_config_key():
    return {
        "timezone": get_config("timezone"),
        "voice-enabled": True,
        "voice-speed": get_config("voice_speedup_multiplier"),
        "voice-volume": get_config("voice_volume"),
        "default-ai-model": get_config("default_ai_model")
    }

class GuildData:    
    
    def __init__(self, data: list):
        try:
            if not isinstance(data, list):
                raise TypeError("Got type {}, expect List.".format(type(data)))
            
            self._raw_data = data
        except IndexError: 
            raise ValueError("Incorrect database response.")
    
    def _get_data_from_raw(self, index: int) -> Any:
        try:
            if isinstance(index, int):
                return self.raw[0][index]
            raise TypeError("index must be an Integer. Got {}".format(type(index)))
        except IndexError:
            raise ValueError("Incorrect / Corrupt database response.")
        
    @property
    def guild_id(self) -> int:
        return self._get_data_from_raw(0) # 0 = Guild ID
    
    @property
    def author_id(self) -> int:
        return self._get_data_from_raw(1) # 1 = Author ID
    
    def get_local_guild_config_key(self, key: str) -> types.Empty | Any:
        if isinstance(key, str) == True:
            return self.raw_config_data.get(key, types.Empty)
        raise TypeError("key must be a String. Not {}".format(type(key)))
    
    @property
    def raw_config_data(self) -> dict:
        return json.loads(self._get_data_from_raw(2)) # 2 = Raw JSON Model rule text.
    
    @property
    def raw(self) -> list:
        return self._raw_data
            
class DGGuildDatabaseConfigHandler(database.DGDatabaseSession):
    # Old: DGGuildConfigSession
    def __enter__(self):
        return self

    def __exit__(self, type_, value_, traceback_):
        self.database.commit()
        self.database.close()
    
    def __init__(self, guild: discord.Guild):
        super().__init__()
        self._guild = guild

    @property
    def guild(self) -> discord.Guild:
        return self._guild
    
    @decorators.has_config
    def edit_guild(self, **keys):
        
        if keys and set(keys.keys()).issubset(set(generate_config_key().keys())):
            data: GuildData = self.get_guild()
            
            _raw = data.raw_config_data.copy()
            _raw.update(keys)
            self._exec_db_command("UPDATE guild_configs SET json=? WHERE gid=?", (json.dumps(_raw), self.guild.id))
        elif not keys:
            raise exceptions.DGException(f"Empty keys would make no change.")
        else:
            raise exceptions.DGException(f"Unknown configuration key(s): {list(keys)}")

    def _get_raw_guild(self, gid: int):
        return self._exec_db_command("SELECT * FROM guild_configs WHERE gid=?", (gid,))
    
    @decorators.has_config
    def get_guild(self, gid: int | None=None) -> GuildData:
        # BUG: Guild may not exist within `guild_configs` and recursion error here
        return GuildData(self._get_raw_guild(gid if isinstance(gid, int) else self.guild.id))
    
    def has_guild(self, gid: int | None=None) -> bool:
        return bool(self._get_raw_guild(gid if isinstance(gid, int) else self.guild.id))
    
    def add_guild(self):
        self._exec_db_command("INSERT INTO guild_configs VALUES(?, ?, ?)", (self.guild.id, self.guild.owner_id, json.dumps(generate_config_key()),))

class GuildConfigAttributes:

    @staticmethod
    def get_guild_model(guild: discord.Guild) -> Type[models.AIModel]:
        return commands_utils.get_modeltype_from_name(get_guild_config_attribute(guild, "default-ai-model"))
    
    @staticmethod
    def get_voice_status(guild: discord.Guild) -> bool:
        return bool(get_guild_config_attribute(guild, "voice-enabled"))
    
    @staticmethod
    def get_voice_volume(guild: discord.Guild) -> float:
        return float(get_guild_config_attribute(guild, "voice-volume"))
    
    @staticmethod
    def get_voice_speed(guild: discord.Guild) -> float:
        return float(get_guild_config_attribute(guild, "voice-speed"))
    
def get_guild_config(guild: discord.Guild) -> GuildData:
    """Returns a guilds full developerconfig.

    Args:
        guild (discord.Guild): The guild.

    Returns:
        GuildData: _description_
    """
    with DGGuildDatabaseConfigHandler(guild) as cs:
        return cs.get_guild()

def edit_guild_config(guild: discord.Guild, key: str | None=None, value: Any | None=None, **kwargs) -> None:
    with DGGuildDatabaseConfigHandler(guild) as cs:
        actual_data = {key: value} if key != None and value != None else kwargs
        return cs.edit_guild(**actual_data)

def reset_guild_config(guild: discord.Guild) -> None:
    return edit_guild_config(guild, **generate_config_key())
        
    
def get_guild_config_attribute(guild: discord.Guild, attribute: str) -> Any:
    """Will return the localised guild config value of the specified guild. Will return the global default if the guild has an outdated config.

    Args:
        guild (discord.Guild): The guild in question
        attribute (str): The attribute of the guild config you want.

    Returns:
        _Union[_Any, None]: The value, or None.
    """
    with DGGuildDatabaseConfigHandler(guild) as cs:
        val = cs.get_guild().get_local_guild_config_key(attribute)
        if val != types.Empty:
            return val
        raise KeyError('No config key named "{}"'.format(attribute))

def get_config(key: str) -> Any:
    return database.get_config(key)

def get_api_key(api_key: str) -> str:
    api_config = database.check_and_get_yaml(developerconfig.TOKEN_FILE, developerconfig.default_api_keys)
    k = api_config.get(api_key, None)
    if k == None:
        raise exceptions.DGException(f'API Key "{api_key}" not found within YAML file.')
    return k

def has_api_key(api_key: str) -> bool:
    try:
        k = get_api_key(api_key)
        return True if k else False
    except exceptions.DGException:
        return False
    
def fix_config(file: str, fix_with: dict[str, Any]) -> dict[str, Any]:
    """Resets the bot-config.yaml file to the programmed default. This function also returns the default.

    Args:
        error_message (str): The warning about the failed configuration.

    Returns:
        dict[str, Any]: _description_ The default config.
    """
    common.warn_for_error("Invalid YAML File Type. Default configuration will be used. Repairing...")
    with open(file, 'w+') as yaml_file_repair:
        yaml.safe_dump(fix_with, yaml_file_repair)
        return fix_with

# TODO: Refactor check_and_get and fix_config
        

def write_keys(keys: dict[str, str]) -> dict[str, str]:
    new_keys = database.check_and_get_yaml(developerconfig.TOKEN_FILE, developerconfig.default_api_keys)
    new_keys.update(keys)
    
    with open(developerconfig.TOKEN_FILE, "w+") as key_yaml:
        yaml.safe_dump(new_keys, key_yaml)
    
    return new_keys