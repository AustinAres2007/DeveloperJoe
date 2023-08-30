import tiktoken, typing, openai_async

from .chat import GPTConversationContext
from .common.developerconfig import GPT_REQUEST_TIMEOUT
from .exceptions import GPTReplyError

__all__ = [
    "GPTModel",
    "GPT3Turbo",
    "GPT4",
    "GPTModelType",
    "registered_models"
]

class AIReply:
    def __init__(self, _reply: str, _tokens: int, _error_code: int, _error: str) -> None:
        self._reply = _reply
        self._tokens = _tokens
        self._error_code = _error_code
        self._error = _error
    
class GPTModel:

    _model: str = ""
    _display_name: str = ""
    _description: str = ""
    
    @classmethod
    @property
    def model(cls) -> str:
        """Returns the actual model name that is used to send communication requests."""
        return cls._model
    
    @classmethod
    @property
    def tokeniser(cls) -> tiktoken.Encoding:
        """The encoding used to calculate the amount of tokens used."""
        return tiktoken.encoding_for_model(cls.model)
    
    @classmethod
    @property
    def description(cls) -> str:
        """The description for the model."""
        return cls._description
    
    @classmethod
    @property
    def display_name(cls) -> str:
        """User-readable display name for the model."""
        return cls._display_name
    
    @classmethod
    def __repr__(cls):
        return f"<{cls.__name__} display_name={cls.display_name}, model={cls.model}>"
    
    @classmethod
    def __str__(cls) -> str:
        return cls._model
    
    @classmethod
    async def __askmodel__(cls, query: str, context: GPTConversationContext, api_key: str, **kwargs) -> AIReply:
        raise NotImplementedError
    
        
class GPT3Turbo(GPTModel):
    """Generative Pre-Trained Transformer 3.5 Turbo (gpt-3.5-turbo)"""

    _model: str = "gpt-3.5-turbo"
    _display_name: str = "GPT 3.5 Turbo"
    _description: str = "Good for generating text and general usage. Cost-effective."

    @classmethod
    def __eq__(cls, __value: GPTModel) -> bool:
        return cls.model == __value.model
    
    @classmethod
    async def __askmodel__(cls, query: str, context: GPTConversationContext, api_key: str, role: str="user", **kwargs) -> AIReply:
        
        context.add_user_query(query, role)
        
        payload = {
            "model": cls.model,
            "messages": context.context
        }
        _reply = await openai_async.chat_complete(api_key=api_key, timeout=GPT_REQUEST_TIMEOUT, payload=payload)
            
        print(_reply.json())

        reply = _reply.json()["choices"][0]
        usage = _reply.json()["usage"]

        if isinstance(reply, dict):
            actual_reply = reply["message"]  
            replied_content = actual_reply["content"]

            self.chat_history.append(dict(actual_reply))
            r_history.extend([kwargs, dict(actual_reply)])
            self.readable_history.append(r_history)
 
            return AIReply(replied_content, usage["total_tokens"], 0, "No error")
        else:
            raise GPTReplyError(reply, type(reply))
            
        
class GPT4(GPTModel):
    """Generative Pre-Trained Transformer 4 (gpt-4)"""

    _model: str = "gpt-4"
    _display_name: str = "GPT 4"
    _description: str = "Better than GPT 3 Turbo at everything. Would stay with GPT 3 for most purposes-- Can get expensive."
    
    @classmethod
    def __eq__(cls, __value: GPTModel) -> bool:
        return cls.model == __value.model
    
GPTModelType = typing.Union[GPT3Turbo, GPT4]
registered_models = {
    "gpt-4": GPT4,
    "gpt-3.5-turbo": GPT3Turbo
}