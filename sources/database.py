import sqlite3, shutil, os
from typing import Any

from .common.developerconfig import DATABASE_FILE, DATABASE_VERSION
from .common import common_functions
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
    
    def __init__(self, database: str=DATABASE_FILE, reset_if_failed_check: bool=True):
        """Handles connections between the database and the client.

        Args:
            database (str, optional): The database that will be used. Defaults to DATABASE_FILE.
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
            if version != DATABASE_VERSION and warn_if_incompatible_versions == True:
                common_functions.warn_for_error(f"Database version is different than specified. (Needs: {DATABASE_VERSION} Has: {version})")
                
            for tb in self._required_tables:
                if not self.table_exists(tb) and fix_if_broken:
                    common_functions.warn_for_error(f'Table "{tb}" in database file "{self.database_file}" missing. Repairing..') if warn_if_fixable_corruption == True else None
                    self.init()
                    return self.check()
                elif not self.table_exists(tb) and fix_if_broken == False and warn_if_fixable_corruption == True:
                    common_functions.warn_for_error(f'Table "{tb}" in database file "{self.database_file}" missing. Not repaired.')
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
        # uid = User / Member ID (Integer)
        # *_json = Json-formatted data
        
        """model_rules `jsontables` format
        
        
            {
                "<model-code-name>: List[role_id]",
                ...
            }
            
            Where `role_id` is the role that can use the model specified in model-code-name
            
            For example: 
            {
                "gpt-4": [1132623433230975076]
            }
            
            permissions `permission_json` format
            
            {
                
            } 
        """
        
        self._exec_db_command(f"CREATE TABLE {'IF NOT EXISTS' if override == False else ''} history (uid TEXT NOT NULL, author_id INTEGER NOT NULL, chat_name VARCHAR(40) NOT NULL, chat_json TEXT NOT NULL, is_private INTEGER CHECK (is_private IN (0,1)))")
        self._exec_db_command(f"CREATE TABLE {'IF NOT EXISTS' if override == False else ''} model_rules (gid INTEGER NOT NULL UNIQUE, jsontables TEXT NOT NULL)")
        self._exec_db_command(f"CREATE TABLE {'IF NOT EXISTS' if override == False else ''} guild_configs (gid INTEGER NOT NULL UNIQUE, oid INTEGER NOT NULL, json TEXT NOT NULL)")
        self._exec_db_command(f"CREATE TABLE {'IF NOT EXISTS' if override == False else ''} database_file (version TEXT NOT NULL, creation_date INTEGER NOT NULL)")
        self._exec_db_command(f"CREATE TABLE {'IF NOT EXISTS' if override == False else ''} permissions (gid INTEGER NOT NULL UNIQUE, permission_json TEXT NOT NULL)")
        
        self._exec_db_command("INSERT INTO database_file VALUES(?, ?)", (
            DATABASE_VERSION, 
            common_functions.get_posix()
            )
        )
        
    def delete(self) -> None:
        """Deletes tables that are needed. This should only be used if there is an error with the database. DGDatabaseSession.init() should be called right after this."""
        
        self._exec_db_command("DROP TABLE IF EXISTS history")
        self._exec_db_command("DROP TABLE IF EXISTS model_rules")
        self._exec_db_command("DROP TABLE IF EXISTS guild_configs")
        self._exec_db_command("DROP TABLE IF EXISTS database_file")
    
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
        return common_functions.get_posix() - self.get_creation_date() 
    
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

    def get_rules(self):
        ...