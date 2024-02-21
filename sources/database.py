import json
import sqlite3, shutil, os
from typing import Any

import discord
import yaml

from .common import (
    common,
    developerconfig
)

from . import errors

__all__ = [
    "DGDatabaseSession"
]

# TODO: Data transfer to new database file (use .check() and detect if a table is missing and replace with parameters that will be specified in a dictionary)
class DGDatabaseSession:
    """
        Handles connection between the server and discord client.
    """

    def __enter__(self):
        if self.check() == False and self._context_manager_reset == True:
            self.reset()
        return self
    
    def __exit__(self, type_, value_, traceback_):
        self.database.commit()
        self.cursor.close() if self.cursor else None
        self.database.close()
    
    def __init__(self, database: str=developerconfig.DATABASE_FILE, reset_if_failed_check: bool=True):
        """Handles connections between the database and the client.

        Args:
            database (str, optional): The database that will be used. Defaults to developerconfig.DATABASE_FILE.
            reset_if_failed_check (bool, optional): Weather you want to reset the database if the check fails. Defaults to True.
        """

        self._context_manager_reset = reset_if_failed_check
        self._required_tables = ["history", "model_rules", "guild_configs", "database_file", "permissions"]
        
        self.database_file = database
        self.database_file_backup = self.database_file.replace(os.path.splitext(self.database_file)[-1], ".sqlite3")
        self.database: sqlite3.Connection = sqlite3.connect(self.database_file, timeout=60)
        self.cursor: sqlite3.Cursor | None = self.database.cursor()

    def table_exists(self, table: str) -> bool:
        try:
            __has_table = self._exec_db_command("SELECT * FROM {}".format(table))
            return True
        except sqlite3.OperationalError:
            return False
        
    def check(self, fix_if_broken: bool=True, warn_if_fixable_corruption: bool=True, warn_if_incompatible_versions: bool=False) -> bool:
        """Checks if all required tables exist and the version is correct for normal bot usage.

        Returns:
            bool: Weather the check succeeded or failed.
        """
        try:
            version = self.get_version()
            if version != developerconfig.DATABASE_VERSION and warn_if_incompatible_versions == True:
                common.warn_for_error(f"Database version is different than specified. (Needs: {developerconfig.DATABASE_VERSION} Has: {version})")
                
            for tb in self._required_tables:
                if not self.table_exists(tb) and fix_if_broken:
                    common.warn_for_error(f'Table "{tb}" in database file "{self.database_file}" missing. Repairing..') if warn_if_fixable_corruption == True else None
                    self.init()
                    return self.check()
                elif not self.table_exists(tb) and fix_if_broken == False and warn_if_fixable_corruption == True:
                    common.warn_for_error(f'Table "{tb}" in database file "{self.database_file}" missing. Not repaired.')
                    return False
            return True
        except sqlite3.OperationalError:
            return False

    def _exec_db_command(self, query: str, args: tuple=()) -> list[Any]:
        """Execute an SQLite3 database command.

        Args:
            query (str): The SQLite3 database command.
            args (tuple, optional): Any variable values. Defaults to ().

        Returns:
            list[Any]: The response from the database
        """
        
        self.cursor = self.database.cursor()

        fetched = self.cursor.execute(query, args).fetchall()

        self.database.commit()
        self.cursor.close()
        self.cursor = None

        return fetched
    
    def init(self, override: bool=False) -> None:
        """Creates tables required for normal bot operation."""
        
        # Common Terminology
        # gid = Guild ID (Integer)
        # uid / oid = Owning User / Member ID  of value
        # *_json = Json-formatted data
        
        """model_rules `jsontables` format
        
            For context, in my server "1132623433230975076" is a VIP role.
            {
                "<model-code-name>: List[role_id]",
                ...
            }
            
            Where `role_id` is the role that can use the model specified in model-code-name
            
            For example: 
            {
                "gpt-4": [1132623433230975076]
            }
        """
        ### ~~~
        """
            permissions `permission_json` format
            
            It uses integers to represent different functions. For a list, refer to `sources.common.enum.ChatFunctions (An Enum)`
            {
                0: [], # 0 = Text function. An empty list meaning everyone can use it
                1: [], # 1 = Bot Speaking Function. An empty list meaning everyone can use it.
                2: [1132623433230975076] # 2 = Bot-Listening-to-user-voice-queries function. Anyone who wants to use it must have the VIP role (1132623433230975076) or higher in the role hierarchy.
            } 
        """
        
        self._exec_db_command(f"CREATE TABLE {'IF NOT EXISTS' if override == False else ''} history (uid TEXT NOT NULL, author_id INTEGER NOT NULL, chat_name VARCHAR(40) NOT NULL, chat_json TEXT NOT NULL, is_private INTEGER CHECK (is_private IN (0,1)))")
        self._exec_db_command(f"CREATE TABLE {'IF NOT EXISTS' if override == False else ''} model_rules (gid INTEGER NOT NULL UNIQUE, jsontables TEXT NOT NULL)")
        self._exec_db_command(f"CREATE TABLE {'IF NOT EXISTS' if override == False else ''} guild_configs (gid INTEGER NOT NULL UNIQUE, oid INTEGER NOT NULL, json TEXT NOT NULL)")
        self._exec_db_command(f"CREATE TABLE {'IF NOT EXISTS' if override == False else ''} database_file (version TEXT NOT NULL, creation_date INTEGER NOT NULL)")
        self._exec_db_command(f"CREATE TABLE {'IF NOT EXISTS' if override == False else ''} permissions (gid INTEGER NOT NULL UNIQUE, permission_json TEXT NOT NULL)")
        
        self._exec_db_command("INSERT INTO database_file VALUES(?, ?)", (
            developerconfig.DATABASE_VERSION, 
            common.get_posix()
            )
        )
        
    def delete(self) -> None:
        """Deletes tables that are needed. This should only be used if there is an error with the database. DGDatabaseSession.init() should be called right after this."""
        
        for table in self._required_tables:
            self._exec_db_command(f"DROP TABLE IF EXISTS {table}") # I know. Do not say it.
            
        #self._exec_db_command("DROP TABLE IF EXISTS database_file")
        #self._exec_db_command("DROP TABLE IF EXISTS database_file")
        #self._exec_db_command("DROP TABLE IF EXISTS model_rules")
        #self._exec_db_command("DROP TABLE IF EXISTS guild_configs")
    
    def reset(self) -> None:
        """Resets the database contents to default (Zero items) This is shorthand for delete() then init()"""
        self.delete()
        self.init(override=True)
    
    def get_version(self) -> str:
        """Gets database version."""
        try:
            return str(self._exec_db_command("SELECT version FROM database_file")[0][0])
        except (sqlite3.OperationalError, IndexError):
            self.init()
            return self.get_version()
        
    def get_creation_date(self) -> int:
        """Gets the POSIX timestamp when the database was created."""
        try:
            timestamp = str(self._exec_db_command("SELECT creation_date FROM database_file")[0][0])
            return int(timestamp if timestamp.isdecimal() else 0)
        except sqlite3.OperationalError:
            self.init()
            return self.get_creation_date()
        
    def get_seconds_since_creation(self) -> int:
        """Gets the seconds since the database was created."""
        return common.get_posix() - self.get_creation_date() 
    
    def backup_database(self) -> str:
        """Backs up the database by simply copy and pasting the file.

        Returns:
            str: The path where the backup is.
        """
        shutil.copy(self.database_file, self.database_file_backup)
        return self.database_file_backup
    
    # TODO: Test saving and loading of backups.
    
    def load_database_backup(self) -> str:  
        """Loads the database backup. This includes doing the check() method on it (Version checking, table checking, etc)

        Raises:
            sqlite3.DatabaseError: If the database is corrupted at all (check() Fails)

        Returns:
            str: The path of the backup that was used.
        """
        with DGDatabaseSession(self.database_file_backup, False) as db_backup:
            if db_backup.check() == True:
                os.remove(self.database_file)
                shutil.copy(self.database_file_backup, self.database_file)
            
                return self.database_file_backup
            raise sqlite3.DatabaseError(errors.DatabaseErrors.DATABASE_CORRUPTED, self.database_file_backup)

_get_ids_as_list = lambda db_reply : [gid[0] for gid in db_reply]
class DGDatabaseManager(DGDatabaseSession):
    """Performs static operations on the database."""
    
    def __enter__(self):
        return super().__enter__()
    
    def __exit__(self, t_, v_, tr_):
        return super().__exit__(t_, v_, tr_)

    def __init__(self, database_path: str=developerconfig.DATABASE_FILE, reset_if_failed_check: bool=True):
        super().__init__(database_path, reset_if_failed_check)
    
    def get_guilds_in_models(self) -> list[int]:
        guilds_database_reply = self._exec_db_command("SELECT gid FROM model_rules")
        return _get_ids_as_list(guilds_database_reply)

    def get_guilds_in_config(self) -> list[int]:
        guilds_database_reply = self._exec_db_command("SELECT gid FROM guild_configs")
        return _get_ids_as_list(guilds_database_reply)
    
    def get_guilds_in_permissions(self) -> list[int]:
        guilds_database_reply = self._exec_db_command("SELECT gid FROM permissions")
        return _get_ids_as_list(guilds_database_reply)
        
    def check_if_guild_in_all(self, guild_id: discord.Guild | int):
        gid = guild_id.id if isinstance(guild_id, discord.Guild) else int(guild_id)
        gid_is_in_all_tables: bool = len([ids for ids in [self.get_guilds_in_models(), self.get_guilds_in_config(), self.get_guilds_in_config()] if gid in ids]) == 3
        
        return gid_is_in_all_tables
    
    # TODO: Make function that lists all guilds within `permissions` table in database. This is done for database integrity checking in joe.py
    
    def create_model_rules_schema(self, guild_id: int) -> None:
        try:
            self._exec_db_command("INSERT INTO model_rules VALUES(?, ?)", (guild_id, json.dumps({})))
        except sqlite3.IntegrityError: # This could be raised because a guild may already exist within the database but was added again. It isn't a problem to we just continue
            common.warn_for_error(f'Guild ID: "{guild_id}" is already in database. Not fatal but keep of note of this incase it happens more than once. (You should NOT get this error more than once consecutively)')
    
    def create_config_schema(self, guild_id: int) -> None:
        try:
            self._exec_db_command("INSERT INTO guild_configs VALUES(?, ?, ?)", (guild_id, 0, json.dumps(generate_config_key()),))
        except sqlite3.IntegrityError:
            common.warn_for_error(f'Guild ID: "{guild_id}" is already in database. Not fatal but keep of note of this incase it happens more than once. (You should NOT get this error more than once consecutively)')
    
    def create_permissions_schema(self, guild_id: int) -> None:
        try:
            self._exec_db_command("INSERT INTO permissions VALUES(?, ?)", (guild_id, json.dumps(developerconfig.default_permission_keys),))
        except sqlite3.IntegrityError:
            common.warn_for_error(f'Guild ID: "{guild_id}" is already in database. Not fatal but keep of note of this incase it happens more than once. (You should NOT get this error more than once consecutively)')
            
    def add_guild_to_database(self, guild: discord.Guild | int) -> None:
        actual_guild_id: int = guild.id if isinstance(guild, discord.Guild) else guild
        
        self.create_model_rules_schema(actual_guild_id)
        self.create_config_schema(actual_guild_id)
        self.create_permissions_schema(actual_guild_id)
        
        # XXX: Update database with all required tables (permissions and guild_configs)

def check_and_get_yaml(yaml_file: str=developerconfig.CONFIG_FILE, check_against: dict=developerconfig.default_config_keys) -> dict[str, Any]:
    """Return the bot-config.yaml file as a dictionary.

    Returns:
        dict[str, Any]: The configuration. (Updated when this function is called)
    """

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
        
    if os.path.isfile(yaml_file):
        with open(yaml_file, 'r') as yaml_file_obj:
            try:
                config = yaml.safe_load(yaml_file_obj)
                                        
                if config:
                    if set(check_against).difference(config):
                        return fix_config(yaml_file, check_against)
                    
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
    
def get_config(key: str) -> Any:
    
    local_config = check_and_get_yaml()
    if key in local_config:
        return local_config.get(key)
    elif hasattr(developerconfig, key.upper()):
        return getattr(developerconfig, key.upper())
    raise KeyError('Cannot find key: "{}" in developer configuration or YAML configuration.'.format(key))  

def generate_config_key():
    return {
        "timezone": get_config("timezone"),
        "voice-enabled": True,
        "voice-speed": get_config("voice_speedup_multiplier"),
        "voice-volume": get_config("voice_volume"),
        "default-ai-model": get_config("default_ai_model")
    }
    