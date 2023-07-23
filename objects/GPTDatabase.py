import sqlite3
from objects import GPTConfig as _GptConfig

database_file = _GptConfig.DATABASE_FILE

class GPTDatabase:

    def __enter__(self):
        return self

    def __exit__(self, type_, value_, traceback_):
        self.database.close()

    def __init__(self):
        
        """
            Handles connection between the server and discord client.

            -> db_name | Name of the database file.
            -> table | Name of the table where your data is.
        """

        # Add error handlers on every command
        self.database_file = database_file
        self.database: sqlite3.Connection = sqlite3.connect(database_file)
        self.cursor: sqlite3.Cursor = self.database.cursor()

    def __check__(self) -> bool:
        try:
            self._exec_db_command("SELECT * FROM history")
            self._exec_db_command("SELECT * FROM model_rules")
            return True
        except sqlite3.OperationalError:
            return False

    def _exec_db_command(self, query: str, args: tuple=()) -> sqlite3.Cursor:
        v = self.cursor.execute(query, args)
        self.database.commit()
        return v