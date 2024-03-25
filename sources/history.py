"""Module for anything ralating to conversation storage"""
from __future__ import annotations
import json, typing
from . import (
    database, 
    exceptions,
    errors
)    
    
__all__ = [
    "DGHistoryChat",
    "DGHistorySession"
]

if typing.TYPE_CHECKING:
    from . import (
        chat
    )

class DGHistoryChat:
    
    def __init__(self, data: list):
        self._id: str = data[0]
        self._user: int = data[1]
        self._name: str = data[2]
        self._data: dict = json.loads(data[3])
        self._private: bool = data[4]
        
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
    
    def retrieve_chat_history(self, history_id: str | None=None, user_id: str | None=None) -> DGHistoryChat | None:
        if history_id == None and user_id == None:
            raise TypeError("At least either history_id or user_id must be a string, or stringlike.")
        
        data = self._exec_db_command("SELECT * FROM history WHERE uid=? OR author_id=?", (str(history_id),str(user_id),))
        if data:
            return DGHistoryChat(data[0])
    
    def retrieve_user_histories(self, user_id: str) -> list[DGHistoryChat]:
        if not isinstance(user_id, str):
            raise TypeError("user_id must be a string or stringlike")
        
        data = self._exec_db_command("SELECT * FROM history WHERE author_id=?", (str(user_id),))
        
        if data:
            return [DGHistoryChat(history_ent) for history_ent in data]
        return []
    
    def delete_chat_history(self, history_id: str) -> str:
        if self.retrieve_chat_history(history_id):
            self._exec_db_command("DELETE FROM history WHERE uid=?", (history_id,))
            return f"Deleted chat history with ID: {history_id}"
        raise exceptions.HistoryError(errors.HistoryErrors.HISTORY_DOESNT_EXIST)
    
    def upload_chat_history(self, chat: chat.DGChat) -> list:
        json_dump = json.dumps(chat.context._display_context)
        return self._exec_db_command("INSERT INTO history VALUES(?, ?, ?, ?, ?)", (chat.hid, chat.member.id, chat.name, json_dump, int(chat.private)))
    