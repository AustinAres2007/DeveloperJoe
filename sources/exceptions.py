from __future__ import annotations
from .common.developerconfig import ALLOW_TRACEBACK

# Models

class DGException(Exception):
    reply = None
    def __init__(self, message: str, *args, log_error: bool | None=None, send_exceptions: bool=True, **kwargs):
        """Base exception for all DGE exceptions. (All DGE exceptions inherit from DGException, and must do if they want to be recognised by error handler)"""

        self._message = message
        self._log_error = log_error if isinstance(log_error, bool) else ALLOW_TRACEBACK
        self._send_exception = send_exceptions
        
        super().__init__(*args, **kwargs)
    
    @property
    def message(self) -> str:
        return self._message

    @property
    def log_error(self) -> bool:
        return self._log_error

    @property
    def send_exception(self) -> bool:
        return self._send_exception

# TODO: Change errors to more specific instead of just DGException (To HistoryError, or ConversationError, etc)

class HistoryError(DGException):
    ...

class ConversationError(DGException):
    ...

class ModelError(DGException):
    ...

class VoiceError(DGException):
    ...