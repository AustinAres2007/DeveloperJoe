import sqlite3, discord
from objects import GPTChat
from typing import Union

class GPTHistory:

    def __enter__(self):
        return self

    def __exit__(self, type_, value_, traceback_):
        self.database.close()

    def __init__(self, db_name: str):
        
        """
            Handles connection between the server and discord client.

            -> db_name | Name of the database file.
            -> table | Name of the table where your data is.
        """

        # Add error handlers on every command
        self.database_file = db_name
        self.database: sqlite3.Connection = sqlite3.connect(db_name)
        self.cursor: sqlite3.Cursor = self.database.cursor()

        if not self.__check__():
            self.init_history()

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
    
    def retrieve_chat_history(self, history_id) -> list:
        return self._exec_db_command("SELECT * FROM history WHERE uid=?", (history_id,)).fetchall()
    
    def upload_chat_history(self, chat) -> list:
        return self._exec_db_command("INSERT INTO history VALUES(?, ?, ?, ?)", (chat.id, chat.user.id, chat.name, str(chat.chat_history),)).fetchall()

    def init_history(self):
        return self._exec_db_command("CREATE TABLE history(uid INTEGER NOT NULL, author_id INTEGER NOT NULL, chat_name VARCHAR(40) NOT NULL, chat_json TEXT NOT NULL)")
    
    def __repr__(self) -> str:
        return f"GPTHistory(database_file={self.database_file})"