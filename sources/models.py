import tiktoken, typing, openai_async, json, tiktoken

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
    async def __askmodel__(cls, query: str, context: GPTConversationContext, api_key: str, role: str="user", save_message: bool=True, **kwargs) -> AIReply:
        raise NotImplementedError
    
    @classmethod
    async def __askmodelstream__(cls):
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
    async def __askmodel__(cls, query: str, context: GPTConversationContext, api_key: str, role: str="user", save_message: bool=True, **kwargs) -> AIReply:
        
        # TODO: Add error handling (Check for error key and add it to AIReply)
        
        temp_context = context.get_temporary_context(query, role)
        
        payload = {
            "model": cls.model,
            "messages": temp_context
        }
        _reply = await openai_async.chat_complete(api_key=api_key, timeout=GPT_REQUEST_TIMEOUT, payload=payload)
            
        print(_reply.json())

        reply = _reply.json()["choices"][0]
        usage = _reply.json()["usage"]

        if isinstance(reply, dict):
            actual_reply = reply["message"]  
            replied_content = actual_reply["content"]
            """
            self.chat_history.append(dict(actual_reply))
            r_history.extend([kwargs, dict(actual_reply)])
            self.readable_history.append(r_history)
            """
            print(save_message)
            if save_message:
                context.add_conversation_entry(query, actual_reply["content"], "user")
            
            return AIReply(replied_content, usage["total_tokens"], 0, "No error")
        else:
            raise GPTReplyError(reply, type(reply))
    
    @classmethod
    async def __askmodelstream__(cls):
        async def __get_stream_parsed_data__(self, **kwargs) -> typing.AsyncGenerator:
            payload = {"model": self.model.model, "messages": self.chat_history, "stream": True} | kwargs
            reply = await openai_async.chat_complete(api_key=self.oapi, timeout=GPT_REQUEST_TIMEOUT, payload=payload)

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
        
        total_tokens = len(self.model.tokeniser.encode(kwargs["content"]))
        r_history = []
        replied_content = ""

        add_history, self.is_processing = True, True
        self.chat_history.append(kwargs)
        generator_reply = self.__get_stream_parsed_data__()

        async for chunk in generator_reply:
            stop_reason = chunk["choices"][0]["finish_reason"]
            if stop_reason == None:
                c_token = chunk["choices"][0]["delta"]["content"].encode("latin-1").decode()
                replied_content += c_token
                total_tokens += len(self.model.tokeniser.encode(c_token))

                yield c_token
            elif stop_reason == "length":
                add_history = self.is_active = False
                raise exceptions.GPTReachedLimit()

            elif stop_reason == "content_filter":
                add_history = False
                raise exceptions.GPTContentFilter(kwargs["content"])

        if add_history == True:
            replicate_reply = {"role": "assistant", "content": replied_content}
            self.chat_history.append(replicate_reply)
            r_history.extend([kwargs, replicate_reply])

            self.readable_history.append(r_history)

            self.__manage_history__(generator_reply, "query", save_message, total_tokens)
        
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