import sqlite3, json
from typing import Union
from objects import GPTErrors

database_file = "dependencies/histories.db"

class GPTHistory:

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
            return True
        except sqlite3.OperationalError:
            return False

    def _exec_db_command(self, query: str, args: tuple=()) -> sqlite3.Cursor:
        v = self.cursor.execute(query, args)
        self.database.commit()
        return v
    
    def retrieve_chat_history(self, history_id: str) -> list:
        return self._exec_db_command("SELECT * FROM history WHERE uid=?", (history_id,)).fetchall()
    
    def delete_chat_history(self, history_id: str) -> Union[str, bool]:
        if self.retrieve_chat_history(history_id):
            self._exec_db_command("DELETE FROM history WHERE uid=?", (history_id,)).fetchall()
            return f"Deleted chat history with ID: {history_id}"
        return GPTErrors.HistoryErrors.HISTORY_DOESNT_EXIST
    
    def upload_chat_history(self, chat) -> list:
        json_dump = json.dumps(chat.readable_history)
        return self._exec_db_command("INSERT INTO history VALUES(?, ?, ?, ?)", (chat.id, chat.user.id, chat.name, json_dump,)).fetchall()

    def init_history(self):
        return self._exec_db_command("CREATE TABLE history(uid TEXT NOT NULL, author_id INTEGER NOT NULL, chat_name VARCHAR(40) NOT NULL, chat_json TEXT NOT NULL)")
    

    def __repr__(self) -> str:
        return f"<GPTHistory(database_file={self.database_file})>"