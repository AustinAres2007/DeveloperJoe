import discord as _discord, json as _json, yaml, os
from typing import Union as _Union, Any

from . import (
    database, 
    exceptions
)
from .common import (
    decorators,
    developerconfig,
    commands_utils,
    common_functions
)

__all__ = [
    "GuildData",
    "DGGuildConfigSession",
    "DGGuildConfigSessionManager",
    "get_guild_config",
    "edit_guild_config",
    "get_guild_config_attribute",
    "reset_guild_config"
]

def generate_config_key():
    return {
        "speed": get_config("voice_speedup_multiplier"),
        "timezone": get_config("timezone"),
        "voice": True,
        "voice-keyword": 
            get_config("listening_keyword")
    }

class GuildData:
    def __init__(self, data: list):
        try:
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
    
    @decorators.has_config
    def edit_guild(self, **keys):
        
        if keys and set(keys.keys()).issubset(set(generate_config_key().keys())):
            data: GuildData = self._manager.get_guild()
            data.config_data.update(keys)
            self._manager.edit_guild(data.config_data)
        elif not keys:
            raise exceptions.DGException(f"Empty keys would make no change.")
        else:
            raise exceptions.DGException(f"Unknown configuration key(s): {list(keys)}")
        
    @decorators.has_config
    def get_guild(self) -> GuildData:
        return self._manager.get_guild()
    
    async def get_config(self, attribute: str):
        config: dict = self.get_guild().config_data
        if attribute in config:
            return config[attribute]
        return config
        
class DGGuildConfigSessionManager(database.DGDatabaseSession):
    def __init__(self, session) -> None:
        super().__init__()
        self._session = session
    
    def get_guild(self, gid: _Union[int, None]=None) -> GuildData:
        return GuildData(self._exec_db_command("SELECT * FROM guild_configs WHERE gid=?", (gid if isinstance(gid, int) else self._session.guild.id,)))
    
    def has_guild(self, gid: _Union[int, None]=None) -> bool:
        return bool(self.get_guild(gid if isinstance(gid, int) else self._session.guild.id).guild_id)
    
    def add_guild(self):
        self._exec_db_command("INSERT INTO guild_configs VALUES(?, ?, ?)", (self._session.guild.id, self._session.guild.owner_id, _json.dumps(generate_config_key()),))
    
    def edit_guild(self, data: dict):
        self._exec_db_command("UPDATE guild_configs SET json=? WHERE gid=?", (_json.dumps(data), self._session.guild.id))
        
def get_guild_config(guild: _discord.Guild) -> GuildData:
    """Returns a guilds full developerconfig.

    Args:
        guild (_discord.Guild): The guild.

    Returns:
        GuildData: _description_
    """
    with DGGuildConfigSession(guild) as cs:
        return cs.get_guild()

def edit_guild_config(guild: _discord.Guild, key: str | None=None, value: Any | None=None, **kwargs) -> None:
    with DGGuildConfigSession(guild) as cs:
        actual_data = {key: value} if key != None and value != None else kwargs
        return cs.edit_guild(**actual_data)

def reset_guild_config(guild: _discord.Guild) -> None:
    return edit_guild_config(guild, **generate_config_key())
        
    
def get_guild_config_attribute(bot, guild: _discord.Guild, attribute: str) -> Any:
    """Will return the localised guild config value of the specified guild. Will return the global default if the guild has an outdated config.

    Args:
        guild (_discord.Guild): The guild in question
        attribute (str): The attribute of the guild config you want.

    Returns:
        _Union[_Any, None]: The value, or None.
    """
    with DGGuildConfigSession(guild) as cs:
        cf = cs.get_guild().config_data
        if attribute in cf:
            return cf[attribute]
        elif attribute in list(bot.config):
            return bot.config.get(attribute)
        else:
            raise exceptions.DGException(f"No such key in guild defaults or guild: {attribute}")

def get_config(key: str) -> Any:
    local_config = check_and_get_yaml()
    if key in local_config:
        return local_config.get(key)
    elif hasattr(developerconfig, key):
        return getattr(developerconfig, key)
    raise exceptions.ConfigKeyError(key)       

def get_api_key(api_key: str) -> str:
    api_config = check_and_get_yaml(developerconfig.TOKEN_FILE, developerconfig.default_api_keys)
    return api_config.get(api_key, None)

def fix_config(file: str, fix_with: dict[str, Any]) -> dict[str, Any]:
    """Resets the bot-config.yaml file to the programmed default. This function also returns the default.

    Args:
        error_message (str): The warning about the failed configuration.

    Returns:
        dict[str, Any]: _description_ The default config.
    """
    common_functions.warn_for_error("Invalid YAML File Type. Default configuration will be used. Repairing...")
    with open(file, 'w+') as yaml_file_repair:
        yaml.safe_dump(fix_with, yaml_file_repair)
        return fix_with
                    
def check_and_get_yaml(yaml_file: str=developerconfig.CONFIG_FILE, check_against: dict=developerconfig.default_config_keys) -> dict[str, Any]:
    """Return the bot-config.yaml file as a dictionary.

    Returns:
        dict[str, Any]: The configuration. (Updated when this function is called)
    """

    if os.path.isfile(yaml_file):
        with open(yaml_file, 'r') as yaml_file_obj:
            try:
                config = yaml.safe_load(yaml_file_obj)
                
                if config:
                    for i1 in enumerate(dict(config).items()):
                        if (i1[1][0] not in list(check_against) or type(i1[1][1]) != type(check_against[i1[1][0]])):
                            return fix_config(yaml_file, check_against)
                    else:
                        return config
                else:
                    return fix_config(yaml_file, check_against)
            except (KeyError, IndexError):
                return fix_config(yaml_file, check_against)
    else:        
        return fix_config(yaml_file, check_against)

def write_keys(keys: dict[str, str]) -> dict[str, str]:
    new_keys = check_and_get_yaml(developerconfig.TOKEN_FILE, developerconfig.default_api_keys)
    new_keys.update(keys)
    
    with open(developerconfig.TOKEN_FILE, "w+") as key_yaml:
        yaml.safe_dump(new_keys, key_yaml)
    
    return new_keys