from httpx import ReadTimeout
from numpy import isin
import tiktoken, json, tiktoken, openai
from sources import confighandler

from typing import (
    Any,
    AsyncGenerator
)

from .chat import GPTConversationContext

from .common import (
    developerconfig,
    types
)

from .exceptions import GPTContentFilter, GPTReachedLimit, DGException, GPTTimeoutError

__all__ = [
    "AIModel",
    "GPT3Turbo",
    "GPT4",
    "GPTModelType",
    "registered_models"
]        

class AIResponse:
    
    def __init__(self, data: str | dict[Any, Any]={}) -> None:
        if not isinstance(data, str | dict):
            raise TypeError("data should be of type dict or str, not {}".format(type(data)))
        
        self._data: dict = self._to_dict(data)
    
    def _to_dict(self, json_string: str | dict) -> dict:
        if isinstance(json_string, str):
            return json.loads(json_string)
        return json_string
    
    @property
    def raw(self) -> dict:
        return self._data
    
    @raw.setter
    def raw(self, new_data: dict) -> None:
        self._data = self._to_dict(new_data)
    
    @property
    def is_empty(self) -> bool:
        return True
        
class AIQueryResponse(AIResponse):
    
    def __init__(self, data: str | dict[Any, Any] = {}) -> None:
        super().__init__(data)
        
        if not self.raw.get("id", None):
            raise ValueError("Incorrect data response.")
    
    def __str__(self) -> str:
        return self.response
        
    @property
    def response_id(self) -> str | None:
        return self._data.get("id", None)
    
    @property
    def timestamp(self) -> int:
        return self._data.get("created", 0)
    
    @property
    def completion_tokens(self) -> int:
        return dict(self._data.get("usage", {})).get("completion_tokens", 0)
    
    @property
    def prompt_tokens(self) -> int:
        return dict(self._data.get("usage", {})).get("prompt_tokens", 0)
    
    @property
    def total_tokens(self) -> int:
        return self.completion_tokens + self.prompt_tokens
    
    @property
    def response(self) -> str:
        return self.raw["choices"][0]["message"]["content"]
        
    @property
    def finish_reason(self) -> str:
        return self.raw["choices"][0]["finish_reason"]

            

class AIErrorResponse(AIResponse):
    def __init__(self, data: str | dict[Any, Any] = {}) -> None:
        super().__init__(data)
        
        if not self.raw.get("error", None):
            raise ValueError("Incorrect data response.")
    
    @property
    def error_message(self) -> str:
        return self.raw["error"]["message"]
    
    @property
    def error_type(self) -> str:
        return self.raw["error"]["type"]
    
    @property
    def error_param(self) -> str:
        
        return self.raw["error"]["param"]
    
    @property
    def error_code(self) -> str:
        return self.raw["error"]["code"]
    
class AIImageResponse(AIResponse):
    
    def __init__(self, data: str | dict[Any, Any] = {}) -> None:
        super().__init__(data)
        
        if not self.raw.get("data", None):
            raise ValueError("Incorrect data response.")
    
    @property
    def timestamp(self) -> int:
        return self._data.get("created", 0)
    
    @property
    def is_image(self) -> bool:
        return bool(self.raw.get("data", False))
    
    @property
    def image_url(self) -> str | None:
        if self.is_image:
            return self.raw["data"][0]["url"]

class AIQueryResponseChunk(AIResponse):
    
    def __init__(self, data: str | dict[Any, Any] = {}) -> None:
        super().__init__(data)
        
        if self.raw.get("object", None) != "chat.completion.chunk":
            raise ValueError("Incorrect chunk data response.")
        
    @property
    def response_id(self) -> str | None:
        return self._data.get("id", None)
    
    @property
    def timestamp(self) -> int:
        return self._data.get("created", 0)
    
    @property
    def response(self) -> str:
        return self.raw["choices"][0]["delta"]["content"]
        
    @property
    def finish_reason(self) -> str:
        return self.raw["choices"][0]["finish_reason"]

class ReadableContext:
    ...
    
Response = AIResponse | AIQueryResponse | AIErrorResponse | AIImageResponse

def _response_factory(data: str | dict[Any, Any] = {}) -> Response:
    actual_data: dict = data if isinstance(data, dict) else json.loads(data)
    
    if actual_data.get("error", False): # If the response is an error
        return AIErrorResponse(data)
    elif actual_data.get("data", False): # If the response is an image
        return AIImageResponse(data)
    elif actual_data.get("object", False) == "chat.completion.chunk":
        return AIQueryResponseChunk(data)
    elif actual_data.get("id", False): # If the response is a query
        return AIQueryResponse(data)
    else:
        return AIResponse(data)

def _handle_error(response: AIErrorResponse) -> None:
    raise DGException(response.error_message, response.error_code)
       
async def _gpt_ask_base(query: str, context: GPTConversationContext | None, api_key: str, role: str="user", save_message: bool=True, model: types.AIModels="gpt-3.5-turbo-16k") -> AIQueryResponse:
    temp_context: list = context.get_temporary_context(query, role) if context else [{"role": role, "content": query}]
    
    if not isinstance(context, GPTConversationContext | None):
        raise TypeError("context should be of type GPTConversationContext or None, not {}".format(type(context)))
    
    try:
        async with openai.AsyncOpenAI(api_key=api_key, timeout=developerconfig.GPT_REQUEST_TIMEOUT) as async_openai_client:
            _reply = await async_openai_client.chat.completions.create(model=model, messages=temp_context)
            response = _response_factory(_reply.model_dump_json())
            
            if isinstance(response, AIErrorResponse):
                _handle_error(response)
            elif isinstance(response, AIQueryResponse):
                if save_message and context:
                    context.add_conversation_entry(query, str(response.response), "user")
                    
                return response
                
    except (TimeoutError, ReadTimeout):
        raise GPTTimeoutError()
    
    raise TypeError("Expected AIErrorResponse or AIQueryResponse, got {}".format(type(response)))
    
async def _gpt_ask_stream_base(query: str, context: GPTConversationContext, api_key: str, role: str, tokenizer: tiktoken.Encoding, model: str, **kwargs) -> AsyncGenerator[tuple[str, int], None]:
    total_tokens = len(tokenizer.encode(query))
    replied_content = ""

    add_history = True
    
    history: list = context.get_temporary_context(query, role)
    
    def _is_valid_chunk(chunk_data: str) -> bool:
        try:
            # NOTE: json.loads can take byte array
            if chunk_data not in ['', '[DONE]'] and bool(json.loads(chunk_data)):
                return True
            else:
                return False
        except:
            return False
    
    async def _get_streamed_response() -> AsyncGenerator[AIQueryResponseChunk | AIErrorResponse, None]:
        async with openai.AsyncOpenAI(api_key=api_key) as async_openai_client:
            _reply = await async_openai_client.chat.completions.create(messages=history, model=model, stream=True)
        
            async for raw_chunk in _reply.response.aiter_text():
                readable_chunks = filter(_is_valid_chunk, raw_chunk.replace("data: ", "").split("\n\n"))
                for chunk_text in readable_chunks:
                    chunk = _response_factory(chunk_text)
                    
                    if isinstance(chunk, AIQueryResponseChunk | AIErrorResponse):
                        yield chunk
                    else:
                        raise TypeError("Expected AIErrorResponse or AIQueryResponseChunk, got {}".format(type(chunk)))
                
    readable_chunks = _get_streamed_response()
    
    async for chunk in readable_chunks:
        if isinstance(chunk, AIErrorResponse):
            _handle_error(chunk)
        else:
            stop_reason = chunk.finish_reason
            
            if stop_reason == None:
                c_token = chunk.response 
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

async def _gpt_image_base(prompt: str, resolution: types.Resolution, image_engine: types.ImageEngine, api_key: str) -> AIImageResponse:
    async with openai.AsyncOpenAI(api_key=api_key) as async_openai_client:
        _image_reply = await async_openai_client.images.generate(prompt=prompt, size=resolution, model=image_engine)
        response = _response_factory(_image_reply.model_dump_json())
        
        if isinstance(response, AIErrorResponse):
            _handle_error(response)
        elif isinstance(response, AIImageResponse):
            return response
    
    raise TypeError("Expected AIImageResponse or AIErrorResponse, got {}".format(type(response)))
    
class AIModel:
    """Generic base class for all AIModels and blueprints for how they should be defined. Use a subclass of this."""
    
    def __init__(self) -> None:
        self._context: ReadableContext = ReadableContext()
    
    @property
    def model(self) -> str:
        return "AIModel"
    
    @property
    def display_name(self):
        return "AI Model"
    
    @property
    def context(self) -> ReadableContext:
        return self._context
    
    async def start_chat(self) -> None:
        raise NotImplemented(f"Use a subclass of {self.__class__.__name__}.")
    
    async def ask_model(self, query: str) -> AIResponse:
        raise NotImplemented(f"Use a subclass of {self.__class__.__name__}.")
    
    async def ask_model_stream(self, query: str) -> AsyncGenerator[AIQueryResponseChunk, None]:
        raise NotImplemented(f"Use a subclass of {self.__class__.__name__}.")
    
    async def generate_image(self, *args, **kwargs) -> AIImageResponse:
        raise NotImplemented(f"Use a subclass of {self.__class__.__name__}.")
    
    def __repr__(self):
        return f"<{self.__name__} display_name={self.display_name}, model={self.model}>"
    
    def __str__(self) -> str:
        return self.model

# GPT AI Code

class GPTConversationContext:
    """Class that contains a users conversation history / context with a GPT Model."""
    def __init__(self) -> None:
        """Class that contains a users conversation history / context with a GPT Model."""
        self._display_context, self._context = [], []
        
    @property
    def context(self) -> list:
        return self._context   
    
    def add_conversation_entry(self, query: str, answer: str, user_type: str) -> list:
        
        data_query = {"role": user_type, "content": query}
        data_reply = {"role": "assistant", "content": answer}
        
        self._context.extend([data_query, data_reply])
        self._display_context.append([data_query, data_reply]) # Add as whole
        
        return self._context
    
    def add_image_entry(self, prompt: str, image_url: str) -> list:
        interaction_data = [{'image': f'User asked GPT to compose the following image: "{prompt}"'}, {'image_return': image_url}]
        self._display_context.append(interaction_data)
        return self._display_context
    
    def get_temporary_context(self, query: str, user_type: str="user"):

        data = {"content": query, "role": user_type}
        _temp_context = self._context.copy()
        _temp_context.append(data)
        
        return _temp_context
    
class GPTModel(AIModel):
    
    def __init__(self) -> None:
        super().__init__()
        self._tokeniser = tiktoken.encoding_for_model(self.model)
        self._gpt_context: GPTConversationContext | None = None
    
    def _check_internal_context(self) -> bool:
        return isinstance(self._gpt_context, GPTConversationContext) == True
    
    @property
    def tokeniser(self) -> tiktoken.Encoding:
        return self._tokeniser
    
    async def start_chat(self) -> None:
        self._gpt_context = GPTConversationContext()
    
    async def ask_model(self, query: str) -> AIResponse:
        if self._check_internal_context:
            raise NotImplemented("Use a subclass of GPTModel.")
        raise TypeError("Internal chat context undefined. Did you call `start_chat` before calling this method?")
    
    async def ask_model_stream(self, query: str) -> AsyncGenerator[AIQueryResponseChunk, None]:
        if self._check_internal_context:
            raise NotImplemented("Use a subclass of GPTModel.")
        raise TypeError("Internal chat context undefined. Did you call `start_chat` before calling this method?")
    
    async def generate_image(self, *args, **kwargs) -> AIImageResponse:
        if self._check_internal_context:
            raise NotImplemented("Use a subclass of GPTModel.")
        raise TypeError("Internal chat context undefined. Did you call `start_chat` before calling this method?")
    
class GPT3Turbo(GPTModel):
    
    @property
    def model(self) -> str:
        return "gpt-3.5-turbo"
    
    @property
    def display_name(self) -> str:
        return "GPT 3.5 Turbo"

    # TODO: Use _gpt_image_base and other respective functions for all methods below
    async def ask_model(self, query: str) -> AIResponse:
        await super().ask_model(query)
        ...
    
    async def ask_model_stream(self, query: str) -> AsyncGenerator[AIQueryResponseChunk, None]:
        await super().ask_model_stream(query)
        ...
    
    async def generate_image(self, *args, **kwargs) -> AIImageResponse:
        await super().generate_image(*args, **kwargs)
        ...
    
class GPT4(AIModel):
    # TODO: Basically copy and paste GPT 3 code but change model param to gpt-4 instead of gpt-3.5-turbo (in xxx_base functions at top of files)
    ...
    
GPTModelType = GPT3Turbo | GPT4
registered_models = {
    "gpt-4": GPT4,
    "gpt-3.5-turbo": GPT3Turbo
}