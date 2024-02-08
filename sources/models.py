import logging
from httpx import ReadTimeout
import json, openai, discord

from typing import (
    Any,
    AsyncGenerator
)
from .common import (
    developerconfig,
    types
)
from . import (
    confighandler,
    modelhandler,
    errors,
    exceptions
)
from discord.app_commands import Choice

__all__ = [
    "AIModel",
    "GPT3Turbo",
    "GPT4",
    "AIModelType",
    "registered_models"
]       
missing_perms = errors.ModelErrors.MODEL_LOCKED
unknown_internal_context = "Undefined internal image context. Was `start_chat` called?"
logger = logging.getLogger(__name__)

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
        interaction_data = [{'image': f'User asked AI to compose the following image: "{prompt}"'}, {'image_return': image_url}]
        self._display_context.append(interaction_data)
        return interaction_data

    def add_reader_entry(self, query: str, image_urls: list[str], answer: str) -> list:
        reader_data = [{'reader_content': query, "image_urls": image_urls}, {"reply": answer}]
        self._display_context.append(reader_data)
        return reader_data
    
# GPT Contexts

class GPTConversationContext:
    def __init__(self) -> None:
        super().__init__()
        self._context = []
    
    def add_conversation_entry(self, query: str, answer: str) -> list:
        
        data_query = {"role": "user", "content": query}    
        data_reply = {"role": "assistant", "content": answer}
        context_entry = [data_query, data_reply]
        
        self._context.extend(context_entry)
        return context_entry

    def clear(self) -> None:
        self._context.clear()
    
    def get_temporary_context(self, query: str) -> list:

        data = {"content": query, "role": "user"}    
        _temp_context = self._context.copy()
        _temp_context.append(data)
        
        return _temp_context
    
    @staticmethod
    def get_empty_image_context(query: str, image_url: str) -> list:
        data_query = [{"role": "user", "content": [
            {"type": "text", "text": query},
            {
                "type": "image_url",
                "image_url": image_url
            }
        ]}]
        return data_query
        
    @staticmethod
    def generate_empty_context(query: str) -> list:
        return [{"role": "user", "content": query}]

class GPTReaderContext:
    def __init__(self) -> None:
        self._reader_context = []
        self._images = []
    
    @property
    def images(self) -> list[str]:
        return self._images
    
    @staticmethod
    def _url_to_gpt_readable(url: str) -> dict:
        return {"type": "image_url", "image_url": url}
    
    async def add_images(self, image_urls: list[str]) -> None:
        for url in image_urls:
            self._images.append(self._url_to_gpt_readable(url)) 
    
    def clear(self) -> None:
        self._images.clear()
                
    def add_reader_context(self, query: str, reply: str) -> None:
        
        # TODO: Fixed fucked up context system. (Use add_images to add images to context possibly)
        user_query = self.generate_empty_context(query)
        ai_reply = {"role": "assistant", "content": reply}
        interaction = [user_query, ai_reply]
        
        return self._reader_context.extend(interaction)
    
    def generate_empty_context(self, query: str) -> dict:
        user_reply = {"role": "user", "content": [
            {
                "type": "text",
                "text": query
            }
        ]}
        
        user_reply["content"].extend(self._images)
        return user_reply
    
    def get_temporary_context(self, query: str, image_urls: list[str] | None=None) -> list:
        user_query = self.generate_empty_context(query)
        _temp_context = self._reader_context.copy()
        _temp_context.append(user_query)
        
        print(_temp_context)
        
        return _temp_context
    
Response = AIResponse | AIQueryResponse | AIErrorResponse | AIImageResponse

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
    raise exceptions.DGException(response.error_message, response.error_code)
    
async def _gpt_ask_base(query: str, context: GPTConversationContext | None,  model: types.AIModels, api_key: str, **kwargs) -> AIQueryResponse:
    temp_context: list = context.get_temporary_context(query) if context else GPTConversationContext.generate_empty_context(query)
    
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
                    context.add_conversation_entry(query, str(response.response))
                    
                return response
                
    except (TimeoutError, ReadTimeout):
        raise exceptions.DGException(errors.AIErrors.AI_TIMEOUT_ERROR)
    
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
        exceptions.exceptions.DGException: If the API key is invalid.
        GPTReachedLimit: If the response has reached the token limit.
        GPTContentFilter: If the response has been filtered by the content filter for explicit terms. 

    Returns:
        _type_: None

    Yields:
        _type_: FIXME: Add new description
    """
    history: list = context.get_temporary_context(query) if context else GPTConversationContext.generate_empty_context(query)

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
                readable_chunks = filter(_is_valid_chunk, raw_chunk.replace("data: ", "").split("\n\n"))
                
                for chunk_text in readable_chunks:
                    chunk = _response_factory(chunk_text)

                    if isinstance(chunk, AIQueryResponseChunk | AIErrorResponse):
                        yield chunk
                    else:
                        raise TypeError(
                            "Expected AIErrorResponse or AIQueryResponseChunk, got {}".format(type(chunk)))
                        
    except openai.AuthenticationError:
        raise exceptions.DGException("**OpenAI API Key is invalid.** Please contact bot owner to resolve this issue.")

async def _gpt_image_base(prompt: str, image_engine: types.ImageEngine, api_key: str) -> AIImageResponse:
    async with openai.AsyncOpenAI(api_key=api_key) as async_openai_client:
        _image_reply = await async_openai_client.images.generate(prompt=prompt, model=image_engine)
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

    can_talk = False
    can_stream = False
    can_generate_images = False
    can_read_images = False
    
    async def __aenter__(self):
        await self.start_chat()
        return self
    
    async def __aexit__(self, blah, _blah, __blah) -> None:
        await self.end()
    
    def _check_user_permissions(self):
        return modelhandler.user_has_model_permissions(self.member, self)
    
    def __init__(self, member: discord.Member) -> None:
        self._context: ReadableContext = ReadableContext()
        self.member = member
    
    def is_init(self):
        return isinstance(self._context, ReadableContext)
    
    def get_lock_list(self) -> list[discord.Role | None]:
        try:
            return [self.member.guild.get_role(r_id) for r_id in modelhandler.get_permitted_roles_for_model(self.member.guild, self)]
        except exceptions.ModelError:
            return []
        
    @property
    def context(self) -> ReadableContext:
        return self._context
    
    async def clear_context(self) -> None:
        raise NotImplemented(f"Use a subclass of {self.__class__.__name__}.")
    
    async def clear_chat_context(self) -> None:
        raise NotImplemented(f"Use a subclass of {self.__class__.__name__}.")
    
    async def clear_image_context(self) -> None:
        raise NotImplemented(f"Use a subclass of {self.__class__.__name__}.")
    
    async def start_chat(self) -> None:
        raise NotImplemented(f"Use a subclass of {self.__class__.__name__}.")
    
    async def ask_model(self, query: str) -> AIQueryResponse:
        raise NotImplemented(f"Use a subclass of {self.__class__.__name__}.")
    
    async def ask_model_stream(self, query: str) -> AsyncGenerator[AIQueryResponseChunk | AIErrorResponse | AIEmptyResponseChunk, None]:
        raise NotImplemented(f"Use a subclass of {self.__class__.__name__}.")
    
    async def generate_image(self, image_prompt: str, *args, **kwargs) -> AIImageResponse:
        raise NotImplemented(f"Use a subclass of {self.__class__.__name__}.")
    
    async def ask_image(self, query: str) -> AIQueryResponse:
        raise NotImplemented(f"Use a subclass of {self.__class__.__name__}.")
    
    async def add_images(self, image_urls: list[str]) -> None:
        raise NotImplemented(f"Use a subclass of {self.__class__.__name__}.")
    
    async def end(self) -> None:
        pass
        
    def __repr__(self):
        return f"<{self.__name__} display_name={self.display_name}, model={self.model}>"
    
    def __str__(self) -> str:
        return self.display_name

# GPT AI Code
    
class GPTModel(AIModel):
    
    def __init__(self, member: discord.Member) -> None:
        super().__init__(member)
        self._gpt_context: GPTConversationContext | None = None
    
    def is_init(self):
        return isinstance(self._gpt_context, GPTConversationContext) and super().is_init()
    
    async def clear_context(self) -> None:
        if self.is_init():
            self._gpt_context.clear() # type: ignore shutup, that is what the check is for.
            self.context.clear()

    async def start_chat(self) -> None:
        self._gpt_context = GPTConversationContext()
    
    async def ask_model(self, query: str) -> AIQueryResponse:
        raise NotImplemented("Use a subclass of GPTModel.")
    
    async def ask_model_stream(self, query: str) -> AsyncGenerator[AIQueryResponseChunk | AIErrorResponse | AIEmptyResponseChunk, None]:
        raise NotImplemented("Use a subclass of GPTModel.")
    
    async def generate_image(self, image_prompt: str, *args, **kwargs) -> AIImageResponse:
        raise NotImplemented("Use a subclass of GPTModel.")
    
class GPT3Turbo(GPTModel):
    
    model: types.AIModels = "gpt-3.5-turbo-16k"
    description = "Cost effective, smart, image generation. Everything normal users need."
    display_name = "GPT 3.5 Turbo"

    can_talk = True
    can_stream = True
    can_generate_images = True
    can_read_images = False
    
    async def ask_model(self, query: str) -> AIQueryResponse:
        if self._check_user_permissions():
            return await _gpt_ask_base(query, self._gpt_context, self.model, confighandler.get_api_key("openai_api_key"))
        raise exceptions.DGException(missing_perms)
    
    async def ask_model_stream(self, query: str) -> AsyncGenerator[AIQueryResponseChunk | AIErrorResponse | AIEmptyResponseChunk, None]:
        if self._check_user_permissions():
            return _gpt_ask_stream_base(query, self._gpt_context, self.model, confighandler.get_api_key("openai_api_key"))
        raise exceptions.DGException(missing_perms)
    
    async def generate_image(self, image_prompt: str) -> AIImageResponse:
        if self._check_user_permissions():
            return await _gpt_image_base(image_prompt, "dall-e-2", confighandler.get_api_key("openai_api_key"))
        raise exceptions.DGException(missing_perms)
    
    async def read_image(self, query: str, image_url: str) -> AIQueryResponse:
        raise exceptions.ModelError("This model does not support image reading.")
    
class GPT4(GPTModel):
    
    model = "gpt-4"
    description = "Slightly better at everything that GPT-3 does, costs more. For normal use, use GPT-3."
    display_name = "GPT 4"
    
    can_talk = True
    can_stream = True
    can_generate_images = True
    can_read_images = False
    
    # XXX: Bot cannot see image after it is sent. Perhaps keep the image URL in local memory and send it everytime so it can be refered too?
    # XXX: If the image is overwritten, it will not be remembered and the bot can only be recall it via the text it has said regarding the old image.
        
    async def ask_model(self, query: str) -> AIQueryResponse:
        if self._check_user_permissions():
            return await _gpt_ask_base(query, self._gpt_context, self.model, confighandler.get_api_key("openai_api_key"))
        raise exceptions.DGException(missing_perms)
    
    async def ask_model_stream(self, query: str) -> AsyncGenerator[AIQueryResponseChunk | AIErrorResponse | AIEmptyResponseChunk, None]:
        if self._check_user_permissions():
            return _gpt_ask_stream_base(query, self._gpt_context, self.model, confighandler.get_api_key("openai_api_key"))
        raise exceptions.DGException(missing_perms)
    
    async def generate_image(self, image_prompt: str) -> AIImageResponse:
        if self._check_user_permissions():
            return await _gpt_image_base(image_prompt, "dall-e-3", confighandler.get_api_key("openai_api_key"))
        raise exceptions.DGException(missing_perms)

class GPT4Vision(GPT4):
    
    model = "gpt-4"
    description = "GPT 4 Engine with added image reading support. Good for describing photos and translating latin-derived languages. Do keep note that this AI model is in preview, and may have usage limits."
    display_name = "GPT 4 with Vision (Preview)"
    
    can_talk = True
    can_stream = True
    can_generate_images = True
    can_read_images = True
    
    def __init__(self, member: discord.Member) -> None:
        super().__init__(member)
        self._image_reader_context: GPTReaderContext | None = None
    
    async def clear_context(self) -> None:
        await super().clear_context()
        self._image_reader_context.clear() # type: ignore :|
    
    async def clear_image_context(self) -> None:
        if self.is_init():
            self._image_reader_context.clear() # type: ignore :|
            
    async def start_chat(self) -> None:
        await super().start_chat()
        self._image_reader_context = GPTReaderContext()
    
    async def _gpt4_read_image_base(self, query: str, _api_key: str) -> AIQueryResponse:

        if not self._image_reader_context:
            raise exceptions.DGException(unknown_internal_context)
        
        elif self._image_reader_context._images:
            reader_context = self._image_reader_context.get_temporary_context(query)
        else:
            raise exceptions.DGException("No images avalible to analyse.")
        
        if not isinstance(self._gpt_context, GPTConversationContext | None):
            raise TypeError("context should be of type GPTConversationContext or None, not {}".format(type(self._gpt_context)))
        
        try:
            print("BEFORE: ",self._image_reader_context._reader_context)
            async with openai.AsyncOpenAI(api_key=_api_key, timeout=developerconfig.GPT_REQUEST_TIMEOUT) as async_openai_client:
                logger.debug(f"Image read raw request: {reader_context}")
                _reply = await async_openai_client.chat.completions.create(model="gpt-4-vision-preview", messages=reader_context, max_tokens=4096)
                response = _response_factory(_reply.model_dump_json())
                
                if isinstance(response, AIErrorResponse):
                    _handle_error(response)
                elif isinstance(response, AIQueryResponse):
                    if isinstance(self._image_reader_context, GPTReaderContext):
                        self._image_reader_context.add_reader_context(query, str(response.response)) # Note to self; this updates INTERNAL CONTEXT.. Not Readable
                        print("AFTER: ",self._image_reader_context._reader_context)
                    return response
                    
        except (TimeoutError, ReadTimeout):
            raise exceptions.ModelError(errors.AIErrors.AI_TIMEOUT_ERROR)
        except openai.RateLimitError as e:
            logger.debug(e.response.read())
            raise exceptions.ModelError("You must wait before analysing again. This is a limitation of GPT 4 Vision and fault of OpenAI. Once again, this model is in preview.")
        
        raise TypeError("Expected AIErrorResponse or AIQueryResponse, got {}".format(type(response)))
    
    # TODO: (Make commands for reading images. /chat analyze to register an image, /chat followup to ask questions about the image registered (or just use /chat analyze again) and use /chat clear
    async def add_images(self, image_urls: list[str]) -> None:
        if isinstance(self._image_reader_context, GPTReaderContext):
            for url in image_urls:
                return self._image_reader_context._images.append(self._image_reader_context._url_to_gpt_readable(url))
        raise exceptions.DGException(unknown_internal_context)
    
    async def ask_image(self, query: str) -> AIQueryResponse:
        if self._check_user_permissions() and self._image_reader_context:
            if isinstance(query, str):
                return await self._gpt4_read_image_base(query, confighandler.get_api_key("openai_api_key"))    
            raise TypeError(f"`query` must be of type `str` not {query.__class__.__name__}")
            
        raise exceptions.DGException(missing_perms)

AIModelType = type(GPT3Turbo) | type(GPT4) | type(GPT4Vision)
GenericAIModel = GPT3Turbo | GPT4 | GPT4Vision

registered_models: dict[str, AIModelType] = {
    "gpt-4": GPT4,
    "gpt-4v": GPT4Vision,
    "gpt-3.5-turbo": GPT3Turbo
}
MODEL_CHOICES: list[Choice] = [
    Choice(name="GPT 3.5 - Turbo", value="gpt-3.5-turbo"),
    Choice(name="GPT 4", value="gpt-4"),
    Choice(name="GPT 4 with Vision", value="gpt-4v")
] # What models of GPT are avalible to use, you can chose any that exist, but keep in mind that have to follow the return fo    rmat of GPT 3 / 4. If not, the bot will crash immediately after a query is sent.
