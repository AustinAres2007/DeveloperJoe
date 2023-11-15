import sqlite3 as _sqlite3, shutil, os
from typing import Union as _Union, Any as _Any

from .common.developerconfig import DATABASE_FILE, DATABASE_VERSION, TIMEZONE
from .common import common_functions
from . import exceptions, errors

__all__ = [
    "DGDatabaseSession"
]

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
        
        """
            Handles connection between the server and discord client.
        """

        self._context_manager_reset = reset_if_failed_check
        self.database_file = database
        self.database_file_backup = self.database_file + "backup"
        self.database: _sqlite3.Connection = _sqlite3.connect(self.database_file, timeout=60)
        self.cursor: _Union[_sqlite3.Cursor, None] = self.database.cursor()

    def check(self) -> bool:
        try:
            self._exec_db_command("SELECT * FROM history")
            self._exec_db_command("SELECT * FROM model_rules")
            self._exec_db_command("SELECT * FROM guild_configs")
            self._exec_db_command("SELECT * FROM database_file")
            
            current_version = self.get_version()
            
            return True and current_version == DATABASE_VERSION
        except _sqlite3.OperationalError:
            return False

    def _exec_db_command(self, query: str, args: tuple=()) -> list[_Any]:
        
        self.cursor = self.database.cursor()

        fetched = self.cursor.execute(query, args).fetchall()

        self.database.commit()
        self.cursor.close()
        self.cursor = None

        return fetched
    
    def init(self) -> None:
        """Creates tables required for normal bot operation."""
        
        self._exec_db_command("CREATE TABLE history (uid TEXT NOT NULL, author_id INTEGER NOT NULL, chat_name VARCHAR(40) NOT NULL, chat_json TEXT NOT NULL, is_private INTEGER CHECK (is_private IN (0,1)))")
        self._exec_db_command("CREATE TABLE model_rules (gid INTEGER NOT NULL UNIQUE, jsontables TEXT NOT NULL)")
        self._exec_db_command("CREATE TABLE guild_configs (gid INTEGER NOT NULL UNIQUE, oid INTEGER NOT NULL, json TEXT NOT NULL)")
        self._exec_db_command("CREATE TABLE database_file (version TEXT NOT NULL, creation_date INTEGER NOT NULL)")
        
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
        self.init()
    
    def get_version(self) -> str:
        """Gets database version."""
        return str(self._exec_db_command("SELECT version FROM database_file")[0][0])

    def get_creation_date(self) -> int:
        """Gets the POSIX timestamp when the database was created."""
        timestamp = str(self._exec_db_command("SELECT creation_date FROM database_file")[0][0])
        return int(timestamp if timestamp.isdecimal() else 0)

    def get_seconds_since_creation(self) -> int:
        """Gets the seconds since the database was created."""
        return common_functions.get_posix() - self.get_creation_date() 
    
    def backup_database(self) -> str:
        shutil.copy(self.database_file, self.database_file_backup)
        return self.database_file_backup
        
    def load_database_backup(self) -> str:    
        if self.check() == True:
            os.remove(self.database_file)
            shutil.copy(self.database_file_backup, self.database_file)
            
            return self.database_file_backup
        raise _sqlite3.DatabaseError(errors.DatabaseErrors.DATABASE_CORRUPTED, self.database_file_backup)
