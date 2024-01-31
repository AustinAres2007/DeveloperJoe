"""Module for anything ralating to conversation storage"""

import json
from . import (
    database, 
    exceptions,
    errors
)    
    
__all__ = [
    "DGHistoryChat",
    "DGHistorySession"
]

class DGHistoryChat:
    
    def __init__(self, data: list):
        self._id: str = data[0][0]
        self._user: int = data[0][1]
        self._name: str = data[0][2]
        self._data: dict = json.loads(data[0][3])
        self._private: bool = data[0][4]
        
    @property
    def history_id(self) -> str:
        return self._id

    @property
    def user(self) -> int:
        return self._user

    @property
    def name(self) -> str:
        return self._name

    @property
    def data(self) -> dict:
        return self._data

    @property
    def private(self) -> bool:
        return self._private
 
class DGHistorySession(database.DGDatabaseSession):

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
    
    def retrieve_chat_history(self, history_id: str) -> DGHistoryChat | None:
        data = self._exec_db_command("SELECT * FROM history WHERE uid=?", (history_id,))
        if data:
            return DGHistoryChat(data)
        
    def delete_chat_history(self, history_id: str) -> str:
        if self.retrieve_chat_history(history_id):
            self._exec_db_command("DELETE FROM history WHERE uid=?", (history_id,))
            return f"Deleted chat history with ID: {history_id}"
        raise exceptions.DGException(errors.HistoryErrors.HISTORY_DOESNT_EXIST)
    
    def upload_chat_history(self, chat) -> list:
        json_dump = json.dumps(chat.context._display_context)
        return self._exec_db_command("INSERT INTO history VALUES(?, ?, ?, ?, ?)", (chat.hid, chat.member.id, chat.name, json_dump, int(chat.private)))