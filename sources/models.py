from httpx import ReadTimeout
import tiktoken, json, tiktoken, openai

from typing import (
    Any,
    AsyncGenerator
)
from .common import (
    developerconfig,
    types
)
from . import (
    confighandler
)

from .exceptions import DGException, GPTTimeoutError

__all__ = [
    "AIModel",
    "GPT3Turbo",
    "GPT4",
    "AIModelType",
    "registered_models"
]       
missing_context = "Internal chat context undefined. Did you call `start_chat` before calling this method?"

class AIResponse:
    """Generic base class for an AI response"""
    
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

class AIEmptyResponseChunk(AIQueryResponseChunk):
    
    @property
    def response(self) -> str:
        return ""
    
    def __bool__(self):
        return False
    
    def __len__(self):
        return 0
    
# Contexts

class ReadableContext:
    """Class that contains a users conversation history / context with a GPT Model."""
    def __init__(self) -> None:
        """Class that contains a users conversation history / context with a GPT Model."""
        self._display_context = []
        
    @property
    def context(self) -> list:
        return self._display_context   
    
    def clear(self) -> None:
        self._display_context.clear()
        
    def add_conversation_entry(self, query: str, answer: str) -> list:
        
        data_query = {"role": "user", "content": query}
        data_reply = {"role": "ai", "content": answer}
        context_entry = [data_query, data_reply]
        
        self._display_context.append(context_entry) # Add as whole
        
        return context_entry
    
    def add_image_entry(self, prompt: str, image_url: str) -> list:
        interaction_data = [{'image': f'User asked GPT to compose the following image: "{prompt}"'}, {'image_return': image_url}]
        self._display_context.append(interaction_data)
        return interaction_data
    
# GPT Contexts

class GPTConversationContext:
    def __init__(self) -> None:
        super().__init__()
        self._context = []
    
    def add_conversation_entry(self, query: str, answer: str, user_type: str) -> list:
        data_query = {"role": "user", "content": query}
        data_reply = {"role": "assistant", "content": answer}
        context_entry = [data_query, data_reply]
        
        self._context.extend(context_entry)
        return context_entry

    def clear(self) -> None:
        self._context.clear()
    
    def get_temporary_context(self, query: str, user_type: str="user") -> list:

        data = {"content": query, "role": user_type}
        _temp_context = self._context.copy()
        _temp_context.append(data)
        
        return _temp_context
    
Response = AIResponse | AIQueryResponse | AIErrorResponse | AIImageResponse

def generate_empty_context(query: str) -> list:
    return [{"role": "user", "content": query}]

def _response_factory(data: str | dict[Any, Any] = {}) -> Response:
    actual_data: dict = data if isinstance(data, dict) else json.loads(data)
    
    if actual_data.get("error", False): # If the response is an error
        return AIErrorResponse(data)
    elif actual_data.get("data", False): # If the response is an image
        return AIImageResponse(data)
    elif actual_data.get("object", False) == "chat.completion.chunk":
        if actual_data["choices"][0]["delta"] != {}:
            return AIQueryResponseChunk(data)
        return AIEmptyResponseChunk(data)
    
    elif actual_data.get("id", False): # If the response is a query
        return AIQueryResponse(data)
    else:
        return AIResponse(data)

def _handle_error(response: AIErrorResponse) -> None:
    raise DGException(response.error_message, response.error_code)
    
async def _gpt_ask_base(query: str, context: GPTConversationContext | None,  model: types.AIModels, api_key: str, **kwargs) -> AIQueryResponse:
    temp_context: list = context.get_temporary_context(query, "user") if context else generate_empty_context(query)
    
    if not isinstance(context, GPTConversationContext | None):
        raise TypeError("context should be of type GPTConversationContext or None, not {}".format(type(context)))
    
    try:
        async with openai.AsyncOpenAI(api_key=api_key, timeout=developerconfig.GPT_REQUEST_TIMEOUT) as async_openai_client:
            _reply = await async_openai_client.chat.completions.create(model=model, messages=temp_context, **kwargs)
            response = _response_factory(_reply.model_dump_json())
            
            if isinstance(response, AIErrorResponse):
                _handle_error(response)
            elif isinstance(response, AIQueryResponse):
                if isinstance(context, GPTConversationContext):
                    context.add_conversation_entry(query, str(response.response), "user")
                    
                return response
                
    except (TimeoutError, ReadTimeout):
        raise GPTTimeoutError()
    
    raise TypeError("Expected AIErrorResponse or AIQueryResponse, got {}".format(type(response)))
    
async def _gpt_ask_stream_base(
    query: str, 
    context: GPTConversationContext | None, 
    model: str, 
    api_key: str, 
    **kwargs) -> AsyncGenerator[AIQueryResponseChunk | AIErrorResponse | AIEmptyResponseChunk, None]:
    
    """Streams a response from the AI. This is not meant to be used directly.

    Raises:
        TypeError: If a chunk of a response is not of type AIErrorResponse or AIQueryResponse.
        DGException: If the API key is invalid.
        GPTReachedLimit: If the response has reached the token limit.
        GPTContentFilter: If the response has been filtered by the content filter for explicit terms. 

    Returns:
        _type_: None

    Yields:
        _type_: A tuple containing the response and the amount of tokens used.
    """
    history: list = context.get_temporary_context(query, "user") if context else generate_empty_context(query)

    def _is_valid_chunk(chunk_data: str) -> bool:
        try:
            # NOTE: json.loads can take byte array
            if chunk_data not in ['', '[DONE]'] and bool(json.loads(chunk_data)):
                return True
            else:
                return False
        except:
            return False


    try:
        async with openai.AsyncOpenAI(api_key=api_key) as async_openai_client:
            _reply = await async_openai_client.chat.completions.create(messages=history, model=model, stream=True, **kwargs)

            async for raw_chunk in _reply.response.aiter_text():
                readable_chunks = filter(
                    _is_valid_chunk, raw_chunk.replace("data: ", "").split("\n\n"))
                for chunk_text in readable_chunks:
                    chunk = _response_factory(chunk_text)

                    if isinstance(chunk, AIQueryResponseChunk | AIErrorResponse):
                        yield chunk
                    else:
                        raise TypeError(
                            "Expected AIErrorResponse or AIQueryResponseChunk, got {}".format(type(chunk)))
                        
    except openai.AuthenticationError:
        raise DGException("**OpenAI API Key is invalid.** Please contact bot owner to resolve this issue.")

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
    
    model: types.AIModels = "AIModel"
    display_name: str = "AI Model"
    description: str | None = None

    def __init__(self) -> None:
        self._context: ReadableContext = ReadableContext()
    
    @property
    def context(self) -> ReadableContext:
        return self._context
    
    @property
    def can_talk(self) -> bool:
        return False
    @property
    def can_stream(self) -> bool:
        return False
    @property
    def can_generate_images(self) -> bool:
        return False
    
    def clear_context(self) -> None:
        raise NotImplemented(f"Use a subclass of {self.__class__.__name__}.")
    
    def start_chat(self) -> None:
        raise NotImplemented(f"Use a subclass of {self.__class__.__name__}.")
    
    async def ask_model(self, query: str) -> AIQueryResponse:
        raise NotImplemented(f"Use a subclass of {self.__class__.__name__}.")
    
    def ask_model_stream(self, query: str) -> AsyncGenerator[AIQueryResponseChunk | AIErrorResponse | AIEmptyResponseChunk, None]:
        raise NotImplemented(f"Use a subclass of {self.__class__.__name__}.")
    
    async def generate_image(self, image_prompt: str, *args, **kwargs) -> AIImageResponse:
        raise NotImplemented(f"Use a subclass of {self.__class__.__name__}.")
    
    def __repr__(self):
        return f"<{self.__name__} display_name={self.display_name}, model={self.model}>"
    
    def __str__(self) -> str:
        return self.display_name

# GPT AI Code
    
class GPTModel(AIModel):
    
    def __init__(self) -> None:
        super().__init__()
        self._tokeniser = tiktoken.encoding_for_model(self.model)
        self._gpt_context: GPTConversationContext | None = None
    
    def _check_internal_context(self) -> bool:
        print(self._gpt_context)
        return isinstance(self._gpt_context, GPTConversationContext) == True
    
    @property
    def tokeniser(self) -> tiktoken.Encoding:
        return self._tokeniser
    
    @property
    def can_talk(self) -> bool:
        return True
    @property
    def can_stream(self) -> bool:
        return True
    @property
    def can_generate_images(self) -> bool:
        return True
    
    def clear_context(self) -> None:
        if self._check_internal_context():
            self._gpt_context.clear() # type: ignore shutup, that is what the check is for.
            self.context.clear()
            
        raise TypeError(missing_context)
    
    def start_chat(self) -> None:
        self._gpt_context = GPTConversationContext()
    
    async def ask_model(self, query: str) -> AIQueryResponse:
        raise NotImplemented("Use a subclass of GPTModel.")
    
    def ask_model_stream(self, query: str) -> AsyncGenerator[AIQueryResponseChunk | AIErrorResponse | AIEmptyResponseChunk, None]:
        raise NotImplemented("Use a subclass of GPTModel.")
    
    async def generate_image(self, image_prompt: str, *args, **kwargs) -> AIImageResponse:
        raise NotImplemented("Use a subclass of GPTModel.")
    
class GPT3Turbo(GPTModel):
    
    model: types.AIModels = "gpt-3.5-turbo"
    description = "Cost effective, smart, image generation. Everything normal users need."
    display_name = "GPT 3.5 Turbo"

    # TODO: Use _gpt_image_base and other respective functions for all methods below
    async def ask_model(self, query: str) -> AIQueryResponse:
        if self._check_internal_context():
            return await _gpt_ask_base(query, self._gpt_context, self.model, confighandler.get_api_key("openai_api_key"))
        raise TypeError(missing_context)
    
    def ask_model_stream(self, query: str) -> AsyncGenerator[AIQueryResponseChunk | AIErrorResponse | AIEmptyResponseChunk, None]:
        if self._check_internal_context():
            return _gpt_ask_stream_base(query, self._gpt_context, self.model, confighandler.get_api_key("openai_api_key"))
        raise TypeError(missing_context)
    
    async def generate_image(self, image_prompt: str, *args, **kwargs) -> AIImageResponse:
        if self._check_internal_context():
            return await _gpt_image_base(image_prompt, kwargs.get("resolution", "512x512"), "dall-e-2", confighandler.get_api_key("openai_api_key"))
        raise TypeError(missing_context)
    
class GPT4(GPTModel):
    
    model = "gpt-4"
    description = "Slightly better at everything that GPT-3 does, costs more. For normal use, use GPT-3."
    display_name = "GPT 4"
    
    async def ask_model(self, query: str) -> AIQueryResponse:
        if self._check_internal_context():
            return await _gpt_ask_base(query, self._gpt_context, self.model, confighandler.get_api_key("openai_api_key"))
        raise TypeError(missing_context)
    
    def ask_model_stream(self, query: str) -> AsyncGenerator[AIQueryResponseChunk | AIErrorResponse | AIEmptyResponseChunk, None]:
        if self._check_internal_context():
            return _gpt_ask_stream_base(query, self._gpt_context, self.model, confighandler.get_api_key("openai_api_key"))
        raise TypeError(missing_context)   
    
    async def generate_image(self, image_prompt: str, *args, **kwargs) -> AIImageResponse:
        if self._check_internal_context():
            return await _gpt_image_base(image_prompt, kwargs.get("resolution", "512x512"), "dall-e-3", confighandler.get_api_key("openai_api_key"))
        raise TypeError(missing_context)
    
AIModelType = type(GPT3Turbo) | type(GPT4)
registered_models: dict[str, AIModelType] = {
    "gpt-4": GPT4,
    "gpt-3.5-turbo": GPT3Turbo
}