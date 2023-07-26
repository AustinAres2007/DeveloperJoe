import sqlite3
from objects import GPTConfig as _GptConfig
from typing import Union, Any

database_file = _GptConfig.DATABASE_FILE

class GPTDatabase:

    def __enter__(self):
        return self
    
    def __exit__(self, type_, value_, traceback_):
        self.database.commit()
        self.cursor.close() if self.cursor else None
        self.database.close()
    
    def __init__(self):
        
        """
            Handles connection between the server and discord client.
        """

        
        self.database_file = database_file
        self.database: sqlite3.Connection = sqlite3.connect(database_file, timeout=60)
        self.cursor: Union[sqlite3.Cursor, None] = self.database.cursor()

    def __check__(self) -> bool:
        try:
            self._exec_db_command("SELECT * FROM history")
            self._exec_db_command("SELECT * FROM model_rules")
            return True
        except sqlite3.OperationalError:
            return False

    def _exec_db_command(self, query: str, args: tuple=()) -> list[Any]:
        
        self.cursor = self.database.cursor()

        fetched = self.cursor.execute(query, args).fetchall()
        self.database.commit()
        self.cursor.close()
        self.cursor = None
        return fetched