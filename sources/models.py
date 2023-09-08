import tiktoken, typing, openai_async, json, tiktoken

from sources.chat import GPTConversationContext

from .chat import GPTConversationContext
from .common.developerconfig import GPT_REQUEST_TIMEOUT
from .exceptions import GPTReplyError, GPTContentFilter, GPTReachedLimit, DGException

__all__ = [
    "GPTModel",
    "GPT3Turbo",
    "GPT4",
    "GPTModelType",
    "registered_models"
]

async def _gpt_ask_base(query: str, context: GPTConversationContext | None, api_key: str, role: str="user", save_message: bool=True, __model: str | None=None):
    temp_context = context.get_temporary_context(query, role) if context else [{"role": role, "content": query}]
        
    payload = {
        "model": __model,
        "messages": temp_context
    }
    _reply = await openai_async.chat_complete(api_key=api_key, timeout=GPT_REQUEST_TIMEOUT, payload=payload)
    try:
        reply = _reply.json()["choices"][0]
        usage = _reply.json()["usage"]

        if isinstance(reply, dict):
            actual_reply = reply["message"]  
            replied_content = actual_reply["content"]

            if save_message and context:
                context.add_conversation_entry(query, actual_reply["content"], "user")
            
            return AIReply(replied_content, usage["total_tokens"], 0, "No error")
        else:
            raise GPTReplyError(reply, type(reply))
    except KeyError:
        raise DGException(f"Got incomplete reply: {_reply.json()}", log_error=True, send_exceptions=True)
    
async def _gpt_ask_stream_base(query: str, context: GPTConversationContext, api_key: str, role: str, tokenizer: tiktoken.Encoding, model: str, **kwargs):
    async def __get_stream_parsed_data__(_history, **kwargs) -> typing.AsyncGenerator:
        payload = {"model": model, "messages": _history, "stream": True} | kwargs
        reply = await openai_async.chat_complete(api_key=api_key, timeout=GPT_REQUEST_TIMEOUT, payload=payload)

        # Setup the list of responses
        responses: list[str] = [""]
        last_char = 0

        # For every character byte in byte stream
        for char in reply.read():
            # Check if current character and last char are line feed characters (Represents new chunk)
            if char == 10 and last_char == 10:
                
                # Check if chunk is the right format, or doesn't equal anything
                if responses[-1].strip("\n") in ["data: [DONE]", ""]:
                    responses.pop()
                else:
                    responses[-1] = json.loads(responses[-1][6:]) # Filter out the "data: " part, and translate to a dictionary

                    yield responses[-1] # Yield finished chunk
                    responses.append("") # Append start of a new chunk
            else:
                # Append part of new chunk to string
                responses[-1] += chr(char)

            last_char = char
    
    total_tokens = len(tokenizer.encode(query))
    replied_content = ""

    add_history = True
    
    history = context.get_temporary_context(query, role)
    generator_reply = __get_stream_parsed_data__(history)
    
    async for chunk in generator_reply:
        stop_reason = chunk["choices"][0]["finish_reason"]
        if stop_reason == None:
            c_token = chunk["choices"][0]["delta"]["content"].encode("latin-1").decode()
            replied_content += c_token
            total_tokens += len(tokenizer.encode(c_token))

            yield (c_token, total_tokens)
        elif stop_reason == "length":
            add_history = False
            raise GPTReachedLimit()

        elif stop_reason == "content_filter":
            add_history = False
            raise GPTContentFilter(kwargs["content"])

    if add_history == True:
        context.add_conversation_entry(query, replied_content, role)
        
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
    async def __askmodel__(cls, query: str, context: GPTConversationContext | None, api_key: str, role: str="user", save_message: bool=True, __model: str | None=None, **kwargs) -> AIReply:
        raise NotImplementedError
    
    @classmethod
    def __askmodelstream__(cls, query: str, context: GPTConversationContext, api_key: str, role: str="user", **kwargs) -> typing.AsyncGenerator:
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
    async def __askmodel__(cls, query: str, context: GPTConversationContext | None, api_key: str, role: str="user", save_message: bool=True, __model: str | None=None, **kwargs) -> AIReply:
        return await _gpt_ask_base(query, context, api_key, role, save_message, cls.model)
    
    @classmethod
    def __askmodelstream__(cls, query: str, context: GPTConversationContext, api_key: str, role: str="user", **kwargs) -> typing.AsyncGenerator:
        return _gpt_ask_stream_base(query, context, api_key, role, cls.tokeniser, cls.model, **kwargs)
            
        
class GPT4(GPTModel):
    """Generative Pre-Trained Transformer 4 (gpt-4)"""

    _model: str = "gpt-4"
    _display_name: str = "GPT 4"
    _description: str = "Better than GPT 3 Turbo at everything. Would stay with GPT 3 for most purposes-- Can get expensive."
    
    @classmethod 
    def __eq__(cls, __value: GPTModel) -> bool:
        return cls.model == __value.model

    @classmethod
    async def __askmodel__(cls, query: str, context: GPTConversationContext | None, api_key: str, role: str = "user", save_message: bool = True, **kwargs) -> AIReply:
        return await _gpt_ask_base(query, context, api_key, role, save_message, cls.model)
    
    @classmethod
    def __askmodelstream__(cls, query: str, context: GPTConversationContext, api_key: str, role: str = "user", **kwargs) -> typing.AsyncGenerator:
        return _gpt_ask_stream_base(query, context, api_key, role, cls.tokeniser, cls.model, **kwargs)
    
GPTModelType = typing.Union[GPT3Turbo, GPT4]
registered_models = {
    "gpt-4": GPT4,
    "gpt-3.5-turbo": GPT3Turbo
}