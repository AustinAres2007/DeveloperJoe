from __future__ import annotations

from abc import ABC, abstractmethod
import logging
import json, openai, discord, typing, requests
import httpx

from typing import (
    Any,
    AsyncGenerator,
    Awaitable,
    Callable,
    Dict,
)
from .common import (
    developerconfig,
    types
)
from . import (
    confighandler,
    modelhandler,
    errors,
    exceptions,
    responses
)
from discord.app_commands import Choice
import google.generativeai as google_ai

__all__ = [
    "AIModel",
    "GPT3Turbo",
    "GPT4",
    "GPT4Vision",
    "GoogleAI",
    "registered_models"
]       
missing_perms = errors.ModelErrors.MODEL_LOCKED
unknown_internal_context = "Undefined internal image context. Was `start_chat` called?"
logger = logging.getLogger(__name__)
    
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

class ReaderContext:
    
    def __init__(self) -> None:
        self._reader_context = []
        self._images = []
        self._image_urls = []
        
    def __len__(self):
        return len(self.image_urls)
    
    @property
    def image_urls(self) -> list[str]:
        return self._image_urls
    
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

class GPTReaderContext(ReaderContext):
    @property
    def images(self) -> list[dict]:
        return self._images
    
    @property
    def context(self) -> list:
        return self._reader_context
    
    @staticmethod
    def _url_to_gpt_readable(url: str) -> dict:
        return {"type": "image_url", "image_url": url}
    
    async def add_images(self, image_urls: list[str], check_if_valid: bool=True) -> None:
        def _is_image(url: str) -> bool:
            if check_if_valid == False:
                return True
            
            image_formats = ("image/png", "image/jpeg", "image/jpg")
            req_header = requests.head(url).headers
            
            return True if req_header["content-type"] in image_formats else False
        
        for url in image_urls:
            if _is_image(url):
                self._images.extend([self._url_to_gpt_readable(url)])
                self._image_urls.append(url)
            else:
                raise exceptions.DGException(f"Image url `{url}` is invalid. Please make sure the image URL is accessible without logging into anything or things of the sort.")
            
    def clear(self) -> None:
        self._images.clear()
        self._reader_context.clear()
                
    def add_reader_context(self, query: str, reply: str) -> None:
        
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
        
        user_reply["content"].extend(self.images)
        return user_reply
    
    def get_temporary_context(self, query: str) -> list:
        user_query = self.generate_empty_context(query)
        _temp_context = self._reader_context.copy()
        _temp_context.append(user_query)
        
        return _temp_context
    
def _handle_error(response: responses.BaseAIErrorResponse) -> None:
    raise exceptions.DGException(response.error_message, response.error_code)
    
async def _gpt_ask_base(query: str, context: GPTConversationContext | None,  model: str, api_key: str, **kwargs) -> responses.OpenAIQueryResponse:
    temp_context: list = context.get_temporary_context(query) if context else GPTConversationContext.generate_empty_context(query)
    
    if not isinstance(context, GPTConversationContext | None):
        raise TypeError("context should be of type GPTConversationContext or None, not {}".format(type(context)))
    
    try:
        async with openai.AsyncOpenAI(api_key=api_key, timeout=developerconfig.GPT_REQUEST_TIMEOUT) as async_openai_client:
            _reply = await async_openai_client.chat.completions.create(model=model, messages=temp_context, **kwargs)
            response = responses._gpt_response_factory(_reply.model_dump_json())
            
            if isinstance(response, responses.BaseAIErrorResponse):
                _handle_error(response)
            elif isinstance(response, responses.OpenAIQueryResponse):
                if isinstance(context, GPTConversationContext):
                    context.add_conversation_entry(query, str(response.response))
                    
                return response
                
    except (TimeoutError, httpx.ReadTimeout):
        raise exceptions.DGException(errors.AIErrors.AI_TIMEOUT_ERROR)
    
    raise TypeError("Expected AIErrorResponse or AIQueryResponse, got {}".format(type(response)))
    
async def _gpt_ask_stream_base(
    query: str, 
    context: GPTConversationContext | None, 
    model: str, 
    api_key: str, 
    **kwargs) -> AsyncGenerator[responses.OpenAIQueryResponseChunk | responses.OpenAIErrorResponse | responses.AIEmptyResponseChunk, None]:
    
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
                    chunk = responses._gpt_response_factory(chunk_text)

                    if isinstance(chunk, responses.OpenAIQueryResponseChunk | responses.OpenAIErrorResponse):
                        yield chunk
                    else:
                        raise TypeError(
                            "Expected AIErrorResponse or AIQueryResponseChunk, got {}".format(type(chunk)))
                        
    except openai.AuthenticationError:
        raise exceptions.DGException("**OpenAI API Key is invalid.** Please contact bot owner to resolve this issue.")

async def _gpt_image_base(prompt: str, image_engine: types.ImageEngine, api_key: str) -> responses.OpenAIImageResponse:
    async with openai.AsyncOpenAI(api_key=api_key) as async_openai_client:
        _image_reply = await async_openai_client.images.generate(prompt=prompt, model=image_engine)
        response = responses._gpt_response_factory(_image_reply.model_dump_json())
        
        if isinstance(response, responses.OpenAIErrorResponse):
            _handle_error(response)
        elif isinstance(response, responses.OpenAIImageResponse):
            return response
    
    raise TypeError("Expected AIImageResponse or AIErrorResponse, got {}".format(type(response)))

def check_is_enabled(func: Callable[..., Awaitable[Any]]):
    async def _inner(self, *args, **kwargs):
        if self.enabled == True:
            return await func(self, *args, **kwargs)
        raise exceptions.ModelError(f"{self.display_name} is not enabled.")
    return _inner

def check_can_talk(func: Callable[..., Awaitable[Any]]):
    
    @check_is_enabled
    async def _inner(self, *args, **kwargs):
        if self.can_talk:
            return await func(self, *args, **kwargs)
        raise exceptions.ModelError(f"{self.display_name} does not support text generation.")
    return _inner

def check_can_stream(func: Callable[..., Awaitable[Any]]):
    
    @check_is_enabled
    async def _inner(self, *args, **kwargs):
        if self.can_stream:
            return await func(self, *args, **kwargs)
        raise exceptions.ModelError(f"{self.display_name} does not support streaming text.")
    return _inner

def check_can_generate_images(func: Callable[..., Awaitable[Any]]):
    
    @check_is_enabled
    async def _inner(self, *args, **kwargs):
        if self.can_generate_images:
            return await func(self, *args, **kwargs)
        raise exceptions.ModelError(f"{self.display_name} does not support image generation.")
    return _inner

def check_can_read(func: Callable[..., Awaitable[Any]]):
    
    @check_is_enabled
    async def _inner(self, *args, **kwargs):
        if self.can_read_images:
            return await func(self, *args, **kwargs)
        raise exceptions.ModelError(f"{self.display_name} does not support image reading.")
    return _inner

class AIModel(ABC):
    """Generic base class for all AIModels and blueprints for how they should be defined. Use a subclass of this."""
    
    @staticmethod
    def is_enabled() -> bool:
        return False
    
    model: str = "AIModel"
    display_name: str = "AI Model"
    description: str | None = None

    can_talk: bool = False
    can_stream: bool = False
    can_generate_images: bool = False
    can_read_images: bool = False
    enabled: bool = is_enabled()
    
    async def __aenter__(self):
        await self.start_chat()
        return self
    
    async def __aexit__(self, blah, _blah, __blah) -> None:
        await self.end()
    
    def _check_user_permissions(self):
        return modelhandler.user_has_model_permissions(self.member, type(self))
    
    def __init__(self, member: discord.Member) -> None:
        self._context: ReadableContext = ReadableContext()
        self._image_reader_context: ReaderContext | None = None
        self.member = member
        
        if not self._check_user_permissions():
            raise exceptions.ModelError(missing_perms)
    
    def is_init(self):
        return isinstance(self._context, ReadableContext)
    
    def get_lock_list(self) -> list[discord.Role | None]:
        try:
            return [self.member.guild.get_role(r_id) for r_id in modelhandler.get_permitted_roles_for_model(self.member.guild, type(self))]
        except exceptions.ModelError:
            return []
        
    @property
    def context(self) -> ReadableContext:
        return self._context
    
    @abstractmethod
    def fetch_raw(self) -> dict:
        # Returns raw chat context
        pass
    
    @abstractmethod
    async def clear_context(self) -> None:
        pass
    
    @abstractmethod
    async def clear_chat_context(self) -> None:
        pass
    
    @abstractmethod
    async def clear_image_context(self) -> None:
        pass
    
    async def start_chat(self) -> None:
        pass
    
    async def ask_model(self, query: str) -> responses.BaseAIQueryResponse:
        raise exceptions.ModelError(f"{self.display_name} does not support text generation.")
    
    async def ask_model_stream(self, query: str) -> AsyncGenerator[responses.BaseAIQueryResponseChunk | responses.BaseAIErrorResponse | responses.AIEmptyResponseChunk, None]:
        pass
    
    async def generate_image(self, image_prompt: str, *args, **kwargs) -> responses.BaseAIImageResponse:
        pass
    
    async def ask_image(self, query: str) -> responses.BaseAIQueryResponse: # TODO regarding type errors: Make AIModelABC class?
        pass
    
    async def add_images(self, image_urls: list[str], check_if_valid: bool=True) -> None:
        pass
    
    @abstractmethod
    async def end(self) -> None:
        pass
        
    def __repr__(self):
        return f"<{self.__name__} display_name={self.display_name}, model={self.model}>"
    
    def __str__(self) -> str:
        return self.display_name

# GPT AI Code
    
class GPTModel(AIModel):
    
    @staticmethod
    def is_enabled() -> bool:
        return confighandler.has_api_key("openai_api_key")
    
    def __init__(self, member: discord.Member) -> None:
        super().__init__(member)
        self._gpt_context: GPTConversationContext | None = None
    
    def is_init(self):
        return isinstance(self._gpt_context, GPTConversationContext) and super().is_init()
    
    async def clear_context(self) -> None:
        if self.is_init():
            self._gpt_context.clear() # type: ignore shutup, that is what the check is for.
            self.context.clear()

    def fetch_raw(self) -> Any:
        return json.dumps(self._gpt_context._context, indent=3) if self._gpt_context else {}
    
    async def start_chat(self) -> None:
        self._gpt_context = GPTConversationContext()
    
    @abstractmethod
    async def ask_model(self, query: str) -> responses.BaseAIQueryResponse:
        pass
    
    @abstractmethod
    async def ask_model_stream(self, query: str) -> AsyncGenerator[responses.OpenAIQueryResponseChunk | responses.OpenAIErrorResponse | responses.AIEmptyResponseChunk, None]:
        pass
    
    @abstractmethod
    async def generate_image(self, image_prompt: str, *args, **kwargs) -> responses.OpenAIImageResponse:
        pass
    
    async def end(self) -> None:
        pass
    
    async def clear_chat_context(self) -> None:
        pass
    
    async def clear_image_context(self) -> None:
        pass
    
class GPT3Turbo(GPTModel):
    
    model: types.AIModels = "gpt-3.5-turbo-16k"
    description = "Cost effective, smart, image generation. Everything normal users need."
    display_name = "GPT 3.5 Turbo"

    can_talk = True
    can_stream = True
    can_generate_images = True
    can_read_images = False
    enabled = GPTModel.is_enabled()
    
    @check_can_talk
    async def ask_model(self, query: str) -> responses.OpenAIQueryResponse:
        if self._check_user_permissions():
            return await _gpt_ask_base(query, self._gpt_context, self.model, confighandler.get_api_key("openai_api_key"))
        raise exceptions.DGException(missing_perms)
    
    @check_can_stream
    async def ask_model_stream(self, query: str) -> AsyncGenerator[responses.OpenAIQueryResponseChunk | responses.OpenAIErrorResponse | responses.AIEmptyResponseChunk, None]:
        if self._check_user_permissions():
            return _gpt_ask_stream_base(query, self._gpt_context, self.model, confighandler.get_api_key("openai_api_key"))
        raise exceptions.DGException(missing_perms)
    
    @check_can_generate_images
    async def generate_image(self, image_prompt: str) -> responses.OpenAIImageResponse:
        if self._check_user_permissions():
            return await _gpt_image_base(image_prompt, "dall-e-2", confighandler.get_api_key("openai_api_key"))
        raise exceptions.DGException(missing_perms)
    
class GPT4(GPTModel):
    
    model = "gpt-4"
    description = "Slightly better at everything that GPT-3 does, costs more. For normal use, use GPT-3."
    display_name = "GPT 4"
    
    can_talk = True
    can_stream = True
    can_generate_images = True
    can_read_images = False
    enabled = GPTModel.is_enabled()
    
    # XXX: Bot cannot see image after it is sent. Perhaps keep the image URL in local memory and send it everytime so it can be refered too?
    # XXX: If the image is overwritten, it will not be remembered and the bot can only be recall it via the text it has said regarding the old image.
    
    @check_can_talk
    async def ask_model(self, query: str) -> responses.OpenAIQueryResponse:
        if self._check_user_permissions():
            return await _gpt_ask_base(query, self._gpt_context, self.model, confighandler.get_api_key("openai_api_key"))
        raise exceptions.DGException(missing_perms)
    
    @check_can_stream
    async def ask_model_stream(self, query: str) -> AsyncGenerator[responses.OpenAIQueryResponseChunk | responses.OpenAIErrorResponse | responses.AIEmptyResponseChunk, None]:
        if self._check_user_permissions():
            return _gpt_ask_stream_base(query, self._gpt_context, self.model, confighandler.get_api_key("openai_api_key"))
        raise exceptions.DGException(missing_perms)
    
    @check_can_generate_images
    async def generate_image(self, image_prompt: str) -> responses.OpenAIImageResponse:
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
    enabled = GPTModel.is_enabled()
    
    def __init__(self, member: discord.Member) -> None:
        super().__init__(member)
        self._image_reader_context: GPTReaderContext | None = None
    
    async def clear_context(self) -> None:
        await super().clear_context()
        await self.clear_image_context()
    
    async def clear_image_context(self) -> None:
        if self.is_init():
            self._image_reader_context.clear() # type: ignore :|
            
    async def start_chat(self) -> None:
        await super().start_chat()
        self._image_reader_context = GPTReaderContext()
    
    async def _gpt4_read_image_base(self, query: str, _api_key: str) -> responses.OpenAIQueryResponse:

        if not self._image_reader_context:
            raise exceptions.DGException(unknown_internal_context)
        
        if self._image_reader_context._images:
            reader_context = self._image_reader_context.get_temporary_context(query)
        else:
            raise exceptions.DGException("No images avalible to analyse.")
        
        if not isinstance(self._gpt_context, GPTConversationContext | None):
            raise TypeError("context should be of type GPTConversationContext or None, not {}".format(type(self._gpt_context)))
        
        try:
            async with openai.AsyncOpenAI(api_key=_api_key, timeout=developerconfig.GPT_REQUEST_TIMEOUT) as async_openai_client:
                logger.debug(f"Image read raw request: {reader_context}")
                _reply = await async_openai_client.chat.completions.create(model="gpt-4-vision-preview", messages=reader_context, max_tokens=4096)
                response = responses._gpt_response_factory(_reply.model_dump_json())
                
                if isinstance(response, responses.OpenAIErrorResponse):
                    _handle_error(response)
                elif isinstance(response, responses.OpenAIQueryResponse):
                    if isinstance(self._image_reader_context, GPTReaderContext):
                        self._image_reader_context.add_reader_context(query, str(response.response)) # Note to self; this updates INTERNAL CONTEXT.. Not Readable
                    return response
                    
        except (TimeoutError, httpx.ReadTimeout):
            raise exceptions.ModelError(errors.AIErrors.AI_TIMEOUT_ERROR)
        except openai.RateLimitError:
            raise exceptions.ModelError("You must wait before analysing again. This is a limitation of GPT 4 Vision and fault of OpenAI. Once again, this model is in preview.")
        except openai.BadRequestError:
            raise exceptions.ModelError("An image was flagged as inappropriate. Please retry. If this persists, please start chat to continue using image features.")
        
        raise TypeError("Expected AIErrorResponse or AIQueryResponse, got {}".format(type(response)))
    
    # TODO: (Make commands for reading images. /chat analyze to register an image, /chat followup to ask questions about the image registered (or just use /chat analyze again) and use /chat clear
    
    @check_can_read
    async def add_images(self, image_urls: list[str], check_if_valid: bool=True) -> None:
        if isinstance(self._image_reader_context, GPTReaderContext):
            if len(image_urls) + len(self._image_reader_context.images) > 10: # This is arbituary. I have heard it is up to 48 but some say that is wrong. 10 to be safe and should all one person needs.
                raise exceptions.ModelError(f"{self.display_name} cannot have more than 10 images registered.")
            return await self._image_reader_context.add_images(image_urls, check_if_valid)
        raise exceptions.ModelError(unknown_internal_context)
    
    @check_can_read
    async def ask_image(self, query: str) -> responses.OpenAIQueryResponse:
        if self._check_user_permissions() and self._image_reader_context:
            if isinstance(query, str):
                return await self._gpt4_read_image_base(query, confighandler.get_api_key("openai_api_key"))    
            raise TypeError(f"`query` must be of type `str` not {query.__class__.__name__}")
            
        raise exceptions.DGException(missing_perms)

class GoogleAI(AIModel):
    
    @staticmethod
    def is_enabled() -> bool:
        return False
    
    model = "gemini-pro"
    description = "Google Bard"
    display_name = "Google PaLM"

    can_talk = True
    can_stream = False
    can_generate_images = False
    can_read_images = False
    enabled = is_enabled()
    
    def __init__(self, member: discord.Member) -> None:
        super().__init__(member)
        self._ai_model_obj: google_ai.GenerativeModel | None = None
        self._chat: google_ai.ChatSession | None = None
        
    async def start_chat(self) -> None:
        await super().start_chat()
        self._ai_model_obj = google_ai.GenerativeModel(self.model)
        self._chat = self._ai_model_obj.start_chat(history=[])
        
    @check_can_talk
    async def ask_model(self, query: str) -> responses.GoogleAIQueryResponse: # Note: GoogleAIResponse classes not finished.
        if isinstance(self._ai_model_obj, google_ai.GenerativeModel) == True and isinstance(self._chat, google_ai.ChatSession):
            query_response = await self._chat.send_message_async(query)
            print(query_response._result) # NOTE: Cannot continue because I am based in the UK. I cannot get an API key due to European laws.
            
        raise exceptions.ModelError(unknown_internal_context)
    
registered_models: Dict[str, typing.Type[AIModel]] = {
    "gpt-4": GPT4,
    "gpt-4v": GPT4Vision,
    "gpt-3.5-turbo": GPT3Turbo,
    "google-wip": GoogleAI
}
MODEL_CHOICES: list[Choice] = [
    Choice(name="GPT 3.5 - Turbo", value="gpt-3.5-turbo"),
    Choice(name="GPT 4", value="gpt-4"),
    Choice(name="GPT 4 with Vision", value="gpt-4v"),
    Choice(name="Google Bard / Gemini", value="google-wip")
] # What models of GPT are avalible to use, you can chose any that exist, but keep in mind that have to follow the return format of GPT 3 / 4. If not, the bot will crash immediately after a query is sent.
