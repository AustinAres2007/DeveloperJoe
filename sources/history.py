import json as _json

from .database import *
from .exceptions import *

class DGHistorySession(DGDatabaseSession):

    """
            Handles history between the end-user and the database.
    """

    def __enter__(self):
        return self

    def __exit__(self, type_, value_, traceback_):
        self.database.commit()
        self.database.close()

    def __init__(self):
        """
            Handles history between the end-user and the database.
        """
        super().__init__()
    
    def retrieve_chat_history(self, history_id: str) -> list:
        return self._exec_db_command("SELECT * FROM history WHERE uid=?", (history_id,))
    
    def delete_chat_history(self, history_id: str) -> str:
        if self.retrieve_chat_history(history_id):
            self._exec_db_command("DELETE FROM history WHERE uid=?", (history_id,))
            return f"Deleted chat history with ID: {history_id}"
        raise HistoryNotExist(history_id)
    
    def upload_chat_history(self, chat) -> list:
        json_dump = _json.dumps(chat.readable_history)
        return self._exec_db_command("INSERT INTO history VALUES(?, ?, ?, ?)", (chat.hid, chat.user.id, chat.name, json_dump,))

    def init_history(self) -> None:
        self._exec_db_command("CREATE TABLE history (uid TEXT NOT NULL, author_id INTEGER NOT NULL, chat_name VARCHAR(40) NOT NULL, chat_json TEXT NOT NULL)")
        self._exec_db_command("CREATE TABLE model_rules (gid INTEGER NOT NULL UNIQUE, jsontables TEXT NOT NULL)")