import tiktoken
import json
import tiktoken
import openai
import vertexai

from vertexai.language_models import ChatModel, ChatMessage
from httpx import ReadTimeout

from google.api_core.exceptions import PermissionDenied
from google.auth.exceptions import DefaultCredentialsError

from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Type
)

from .common import (
    developerconfig,
    types
)
from .exceptions import GPTContentFilter, GPTReachedLimit, DGException, GPTTimeoutError
from sources import confighandler

__all__ = [
    "ConversationContext",
    "AIModel",
    "GPT3Turbo",
    "GPT4",
    "PaLM2",
    "AIModelType",
    "registered_models"
]
# TODO (Not important): add __repr__ and __str__ to Response classes
                
class ConversationContext:
    """Class that should contain a users conversation history / context with a GPT Model."""
    def __init__(self) -> None:
        """Class that should contain a users conversation history / context with a GPT Model."""
        self._display_context = []
        self._context: list[types.AIInteraction] = []
        
    @property
    def context(self) -> list:
        """The technical context of that chat. Images are not stored here due to the way they are handled if sent to the AI. Image context is stored in `readable_context`.

        Returns:
            list: The context.
        """
        return self._context   
    
    @property
    def readable_context(self) -> list:
        """This has the same contents as `context`, but is formatted in a way that is readable by humans. Images are stored here.

        Returns:
            list: A list of dictionaries that contain the context.
        """
        return self._display_context
    
    def get_context_translated(self, translate_function: Callable[["ConversationContext"], Any]) -> Any:
        """This is a convenience function that passes the context to a function. This function must have one argument that is of type `ConversationContext`. You are free to write any code in the function and give it Any return type.

        Args:
            translate_function (Callable[[ConversationContext], Any]): The callable method

        Raises:
            TypeError: If `translate_function` is not of type Callable

        Returns:
            Any: Anything. The return type is up to you.
        """
        if not isinstance(translate_function, Callable):
            raise TypeError("translate_function should be of type Callable and have one argument that denotes a ConversationContext type, got type {}".format(type(translate_function)))
        return translate_function(self)
        
    def add_conversation_entry(self, query: str, answer: str, user_type: str="user") -> list[types.AIInteraction]:
        """Adds a question and an answer to said question to the context.

        Args:
            query (str): What the user said.
            answer (str): What the AI replied with.
            user_type (str, optional): Who asked the question. Defaults to "user".

        Returns:
            list[types.AIInteraction]: Returns the new context object.
        """
        
        data_query: types.AIInteraction = {"role": user_type, "content": query}
        data_reply: types.AIInteraction = {"role": "assistant", "content": answer}
        
        new: list[types.AIInteraction] = [data_query, data_reply]
        
        self._context.extend(new)
        self._display_context.append(new) # Add as whole
        
        return self._context
    
    def add_image_entry(self, prompt: str, image_url: str) -> list:
        """Adds an image query and URL to the context.

        Args:
            prompt (str): The image prompt.
            image_url (str): The URL of the image.

        Returns:
            list: Returns the new display context. This is the same as `readable_context`.
        """
        interaction_data = [{'image': f'User asked AI to compose the following image: "{prompt}"'}, {'image_return': image_url}]
        self._display_context.append(interaction_data)
        return self._display_context
    
    def get_temporary_context(self, query: str, user_type: str="user") -> list[types.AIInteraction]:
        """        
        This function is used for GPT Models. It returns a temporary context that is used to generate a response. This is not saved to the context.

        Args:
            query (str): What the user said.
            user_type (str, optional): Who has asked the query. Defaults to "user".

        Returns:
            list[types.AIInteraction]: The temporary context.
        """

        data: types.AIInteraction = {"content": query, "role": user_type}
        _temp_context = self._context.copy()
        _temp_context.append(data)
        
        return _temp_context
    
class AIResponse:

    def __init__(self, data: str | dict[Any, Any] = {}) -> None:
        """Represents a response from the AI. This is a base class and should not be used directly. Use one of the provided subclasses instead.

        Args:
            data (str | dict[Any, Any], optional): _description_. Defaults to {}.

        Raises:
            TypeError: If `data` is not of type str or dict.
        """
        if not isinstance(data, str | dict):
            raise TypeError("data should be of type dict or str, not {}".format(type(data)))

        self._data: dict = self._to_dict(data)

    def _to_dict(self, json_string: str | dict) -> dict:
        if isinstance(json_string, str):
            return json.loads(json_string)
        return json_string

    @property
    def raw(self) -> dict:
        """Raw JSON response from the AI.

        Returns:
            dict: The raw JSON response.
        """
        return self._data

    @raw.setter
    def raw(self, new_data: dict) -> None:
        """Changes the raw JSON response from the AI.

        Args:
            new_data (dict): The new raw JSON response.
        """
        self._data = self._to_dict(new_data)

    @property
    def is_empty(self) -> bool:
        """Checks if the response is empty."""
        return True


class AIQueryResponse(AIResponse):

    def __init__(self, data: str | dict[Any, Any] = {}) -> None:
        """Represents a successful response from the AI.

        Args:
            data (str | dict[Any, Any], optional): _description_. Defaults to {}.

        Raises:
            ValueError: If `data` is not a valid JSON response.
        """
        super().__init__(data)

        if not self.raw.get("id", None):
            raise ValueError("Incorrect data response.")

    def __str__(self) -> str:
        return self.response

    @property
    def response_id(self) -> str | None:
        """The model ID of the response. (e.g. gpt-3.5-turbo-16k, or chat-bison@002 if using PaLM 2)

        Returns:
            str | None: The ID.
        """
        return self._data.get("id", None)

    @property
    def timestamp(self) -> int:
        """The timestamp of the response. This is the time the response was generated.

        Returns:
            int: The Posix timestamp.
        """
        return self._data.get("created", 0)

    @property
    def completion_tokens(self) -> int:
        """The amount of tokens the completion took.

        Returns:
            int: The amount of tokens.
        """
        return dict(self._data.get("usage", {})).get("completion_tokens", 0)

    @property
    def prompt_tokens(self) -> int:
        """The amount of tokens the prompt took.

        Returns:
            int: The amount of tokens.
        """
        return dict(self._data.get("usage", {})).get("prompt_tokens", 0)

    @property
    def total_tokens(self) -> int:
        """The amount of tokens for the total response.

        Returns:
            int: The amount of tokens.
        """
        return self.completion_tokens + self.prompt_tokens

    @property
    def response(self) -> str:
        """The text response from the AI.

        Returns:
            str: The response.
        """
        return self.raw["choices"][0]["message"]["content"]

    @property
    def finish_reason(self) -> str:
        """Why the response finished. (Not necessarily an error)

        Returns:
            str: The reason.
        """
        return self.raw["choices"][0]["finish_reason"]


class AIErrorResponse(AIResponse):
    def __init__(self, data: str | dict[Any, Any] = {}) -> None:
        """Represents an error response from the AI.

        Args:
            data (str | dict[Any, Any], optional): _description_. Defaults to {}.

        Raises:
            ValueError: If `data` is not a valid JSON response.
        """
        super().__init__(data)

        if not self.raw.get("error", None):
            raise ValueError("Incorrect data response.")

    @property
    def error_message(self) -> str:
        """The error message.

        Returns:
            str: A human-readable error message.
        """
        return self.raw["error"]["message"]

    @property
    def error_type(self) -> str:
        """The type of error given by the AI.

        Returns:
            str: The error type.
        """
        return self.raw["error"]["type"]

    @property
    def error_param(self) -> str:
        """Parameters of the error."""
        return self.raw["error"]["param"]

    @property
    def error_code(self) -> str:
        """The error code.

        Returns:
            str: The error code.
        """
        return self.raw["error"]["code"]


class AIImageResponse(AIResponse):

    def __init__(self, data: str | dict[Any, Any] = {}) -> None:
        """Represents an image response from the AI.

        Args:
            data (str | dict[Any, Any], optional): _description_. Defaults to {}.

        Raises:
            ValueError: If `data` is not a valid JSON response.
        """
        super().__init__(data)

        if not self.raw.get("data", None):
            raise ValueError("Incorrect data response.")

    @property
    def timestamp(self) -> int:
        """The timestamp of the response. This is the time the response was generated.

        Returns:
            int: The Posix timestamp.
        
        Raises:
            KeyError: If `data` is not a valid JSON response.
        """
        return self._data.get("created", 0)

    @property
    def image_url(self) -> str:
        """The URL of the image made.

        Returns:
            str | None: The URL.
        
        Raises:
            KeyError: If `data` is not a valid JSON response.
        """
        return self.raw["data"][0]["url"]


class AIQueryResponseChunk(AIResponse):

    def __init__(self, data: str | dict[Any, Any] = {}) -> None:
        """This is a response from the AI that is a chunk of a response. This is used for streaming text generation and is not meant to be used directly.

        Args:
            data (str | dict[Any, Any], optional): _description_. Defaults to {}.

        Raises:
            ValueError: If `data` is not a valid JSON response.
        """
        super().__init__(data)

        if self.raw.get("object", None) != "chat.completion.chunk":
            raise ValueError("Incorrect chunk data response.")

    @property
    def response_id(self) -> str | None:
        """The model ID of the response. (e.g. gpt-3.5-turbo-16k, or chat-bison@002 if using PaLM 2)

        Returns:
            str | None: The ID.
        
        Raises:
            KeyError: If `data` is not a valid JSON response.
        """
        return self._data.get("id", None)

    @property
    def timestamp(self) -> int:
        """The timestamp of the response. This is the time the response was generated.

        Returns:
            int: The Posix timestamp.
        
        Raises:
            KeyError: If `data` is not a valid JSON response.
        """
        return self._data.get("created", 0)

    @property
    def response(self) -> str:
        """The text response from the AI.

        Returns:
            str: The response.
        
        Raises:
            KeyError: If `data` is not a valid JSON response.
        """
        return self.raw["choices"][0]["delta"]["content"]

    @property
    def finish_reason(self) -> str:
        """The finish reason of the response. (Not necessarily an error, may indicate that the response has finished)

        Returns:
            str: The reason.
        
        Raises:
            KeyError: If `data` is not a valid JSON response.
        """
        return self.raw["choices"][0]["finish_reason"]


Response = AIResponse | AIQueryResponse | AIErrorResponse | AIImageResponse
_error_text = "AI model is not enabled due to a technical issue on the server's end. If this persists, please contact the bot owner."

def _response_factory(data: str | dict[Any, Any] = {}) -> Response:
    actual_data: dict = data if isinstance(data, dict) else json.loads(data)

    if actual_data.get("error", False):  #  If the response is an error
        return AIErrorResponse(data)
    elif actual_data.get("data", False):  #  If the response is an image
        return AIImageResponse(data)
    elif actual_data.get("object", False) == "chat.completion.chunk":
        return AIQueryResponseChunk(data)
    elif actual_data.get("id", False):  #  If the response is a query
        return AIQueryResponse(data)
    else:
        return AIResponse(data)


def _handle_error(response: AIErrorResponse) -> None:
    """An internal function that handles errors from the AI.

    Args:
        response (AIErrorResponse): _description_

    Raises:
        DGException: _description_
    """
    raise DGException(response.error_message, response.error_code)


async def _gpt_ask_base(
    query: str, 
    context: ConversationContext | None, 
    api_key: str, 
    save_message: bool = True, 
    model: types.AIModels = "gpt-3.5-turbo-16k", 
    async_openai_kwargs: dict[str, Any]={}, 
    chat_completions_create_kwargs: dict[str, Any]={}) -> AIQueryResponse:
    
    """This is a base function for asking a GPT model a question. This is not meant to be used directly.

    Raises:
        TypeError: If the given context is not of type ConversationContext or None. Or if the response is not of type AIErrorResponse or AIQueryResponse.
        GPTTimeoutError: If the request to the GPT API times out.
        DGException: If the API key is invalid.

    Returns:
        _type_: The response from the AI.
    """
    print(api_key)
    temp_context: list = context.get_temporary_context(query, "user") if context else [{"role": "user", "content": query}]

    if not isinstance(context, ConversationContext | None):
        raise TypeError(
            "context should be of type ConversationContext or None, not {}".format(type(context)))

    try:
        async with openai.AsyncOpenAI(api_key=api_key, timeout=developerconfig.GPT_REQUEST_TIMEOUT, **async_openai_kwargs) as async_openai_client:
            _reply = await async_openai_client.chat.completions.create(model=model, messages=temp_context, **chat_completions_create_kwargs)
            response = _response_factory(_reply.model_dump_json())

            if isinstance(response, AIErrorResponse):
                _handle_error(response)
            elif isinstance(response, AIQueryResponse):
                if save_message and context:
                    context.add_conversation_entry(query, str(response.response), "user")

                return response

    except (TimeoutError, ReadTimeout):
        raise GPTTimeoutError()
    
    except openai.AuthenticationError:
        raise DGException("**OpenAI API Key is invalid.** Please contact bot owner to resolve this issue.")
    
    raise TypeError(
        "Expected AIErrorResponse or AIQueryResponse, got {}".format(type(response)))

    

async def _gpt_ask_stream_base(
    query: str, 
    context: ConversationContext, 
    api_key: str, 
    tokenizer: tiktoken.Encoding, 
    model: str, 
    **kwargs) -> AsyncGenerator[tuple[str, int], None]:
    
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
    
    total_tokens = len(tokenizer.encode(query))
    replied_content = ""

    add_history = True
    history: list = context.get_temporary_context(query, "user")

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
        try:
            async with openai.AsyncOpenAI(api_key=api_key) as async_openai_client:
                _reply = await async_openai_client.chat.completions.create(messages=history, model=model, stream=True)

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
        context.add_conversation_entry(query, replied_content, "user")


async def _gpt_image_base(context: ConversationContext | None, prompt: str, resolution: types.Resolution, image_engine: types.ImageEngine, api_key: str, save_message: bool) -> AIImageResponse:
    """Generates an image from the AI. This is not meant to be used directly.
    # TODO: Add support for image context.
    
    Args:
        prompt (str): The prompt for the image.
        resolution (types.Resolution): The resolution of the image.
        image_engine (types.ImageEngine): The image engine to use.
        api_key (str): The image engines API key (Same as OpenAI key in this case).

    Raises:
        TypeError: If the response is not of type AIErrorResponse or AIImageResponse.

    Returns:
        AIImageResponse: The response from the AI.
    """

    try:
        async with openai.AsyncOpenAI(api_key=api_key) as async_openai_client:
            _image_reply = await async_openai_client.images.generate(prompt=prompt, size=resolution, model=image_engine)
            response = _response_factory(_image_reply.model_dump_json())

            if isinstance(response, AIErrorResponse):
                raise DGException(response.error_message, response.error_code)
                
            elif isinstance(response, AIImageResponse):
                if context and save_message:
                    context.add_image_entry(prompt, response.image_url)
                return response

            else:
                raise TypeError("Expected AIImageResponse or AIErrorResponse, got {}".format(type(response)))
            
    except openai.BadRequestError as error:
        response = _response_factory(error.response.json())
        if isinstance(response, AIErrorResponse):
            raise DGException(response.error_message, response.error_code)
        raise error
        
class AIModel:

    """Base class for AI Models. This is not meant to be used directly."""
    
    model: types.AIModels = 'gpt-3.5-turbo'
    display_name: str = ""
    description: str = ""
    enabled: bool = True
    
    _api_key: str = "openai_api_key"
    enabled = confighandler.has_api_key(_api_key)
    
    @classmethod
    def get_tokeniser(cls) -> tiktoken.Encoding:
        """The encoding used to calculate the amount of tokens used."""
        return tiktoken.encoding_for_model(cls.model)

    @classmethod
    def __repr__(cls):
        return f"<{cls.__name__} display_name={cls.display_name}, model={cls.model}>"

    @classmethod
    def __str__(cls) -> str:
        return cls.model

    @classmethod
    async def __askmodel__(cls, 
        query: str, 
        context: ConversationContext | None, 
        save_message: bool = True) -> AIQueryResponse:
        
        """Ask the AI a question.

        Args:
            query (str): The question to ask.
            context (ConversationContext | None): The context of the conversation so far. It can be None if there is no context.
            save_message (bool, optional): If the AI's reply will be saved to `context`. Defaults to True.

        Raises:
            DGException: If the model is not enabled.

        Returns:
            AIQueryResponse: The response from the AI.
        """
        raise DGException("This model does not support text generation.")

    @classmethod
    def __askmodelstream__(cls, 
        query: str, 
        context: ConversationContext) -> AsyncGenerator[tuple[str, int], None]:
        
        """Ask the AI a question and stream the response.

        Args:
            query (str): The question to ask.
            context (ConversationContext): The context of the conversation so far.

        Raises:
            DGException: If the model is not enabled.

        Returns:
            AsyncGenerator[tuple[str, int], None]: The streamed response from the AI.
        """
        raise DGException("This model does not support streaming text generation.")

    @classmethod
    async def __imagegenerate__(cls, 
        prompt: str, 
        context: ConversationContext | None = None,
        resolution: types.Resolution = "256x256", 
        image_engine: types.ImageEngine = "dall-e-2",
        save_message: bool = True) -> AIImageResponse:

        """Generate an image from the AI. The AI must support image generation.

        Raises:
            DGException: If the model is not enabled.

        Returns:
            AIImageResponse: The response from the AI containing an image.
        """
        raise DGException("This model does not support image generation.")


class GPT3Turbo(AIModel):
    """Generative Pre-Trained Transformer 3.5 Turbo (gpt-3.5-turbo)"""

    model: types.AIModels = "gpt-3.5-turbo-16k"
    display_name: str = "GPT 3.5 Turbo"
    description: str = "Good for generating text and general usage. Cost-effective."
    
    _api_key: str = "openai_api_key"
    enabled = confighandler.has_api_key(_api_key)

    @classmethod
    async def __askmodel__(cls, 
        query: str, 
        context: ConversationContext | None, 
        save_message: bool = True) -> AIQueryResponse:
        
        if not cls.enabled:
            raise DGException(f"{cls.display_name} {_error_text}")
        
        return await _gpt_ask_base(query, context, confighandler.get_api_key(cls._api_key), save_message, cls.model)

    @classmethod
    def __askmodelstream__(cls, 
        query: str, 
        context: ConversationContext) -> AsyncGenerator[tuple[str, int], None]:

        if not cls.enabled:
            raise DGException(f"{cls.display_name} {_error_text}")
        
        return _gpt_ask_stream_base(query, context, confighandler.get_api_key(cls._api_key), cls.get_tokeniser(), cls.model)

    @classmethod
    async def __imagegenerate__(cls, 
        prompt: str, 
        context: ConversationContext | None = None,
        resolution: types.Resolution = "256x256", 
        image_engine: types.ImageEngine = "dall-e-2",
        save_message: bool = True) -> AIImageResponse:
        
        if not cls.enabled:
            raise DGException(f"{cls.display_name} {_error_text}")
        
        if not isinstance(context, ConversationContext) and save_message == True:
            raise DGException("context cannot be type {} if save_message is True.".format(type(context)))
        
        
        return await _gpt_image_base(context, prompt, resolution, image_engine, confighandler.get_api_key(cls._api_key), save_message)


class GPT4(AIModel):
    """Generative Pre-Trained Transformer 4 (gpt-4)"""

    model: types.AIModels = "gpt-4"
    display_name: str = "GPT 4"
    description: str = "Better than GPT 3 Turbo at everything. Would stay with GPT 3 for most purposes-- Can get expensive."
       
    _api_key = "openai_api_key"
    enabled = confighandler.has_api_key(_api_key)

    @classmethod
    async def __askmodel__(cls, 
        query: str, 
        context: ConversationContext | None, 
        save_message: bool = True) -> AIQueryResponse:
        
        if not cls.enabled:
            raise DGException(f"{cls.display_name} {_error_text}")
        
        return await _gpt_ask_base(query, context, confighandler.get_api_key(cls._api_key), save_message, cls.model)

    @classmethod
    def __askmodelstream__(cls, 
        query: str, 
        context: ConversationContext) -> AsyncGenerator[tuple[str, int], None]:
        
        if not cls.enabled:
            raise DGException(f"{cls.display_name} {_error_text}")
        
        return _gpt_ask_stream_base(query, context, confighandler.get_api_key(cls._api_key), cls.get_tokeniser(), cls.model)

    @classmethod
    async def __imagegenerate__(cls, 
        prompt: str, 
        context: ConversationContext | None = None,
        resolution: types.Resolution = "256x256", 
        image_engine: types.ImageEngine = "dall-e-2",
        save_message: bool = True) -> AIImageResponse:
        
        if not cls.enabled:
            raise DGException(f"{cls.display_name} {_error_text}")
        
        if not isinstance(context, ConversationContext) and save_message == True:
            raise DGException("context cannot be type {} if save_message is True.".format(type(context)))
        
        return await _gpt_image_base(context, prompt, resolution, image_engine, confighandler.get_api_key(cls._api_key), save_message)


class PaLM2(AIModel):

    model: types.AIModels = "chat-bison@002"
    display_name: str = "PaLM 2"
    description: str = f"Very fast, but is costly. Good at general tasks and coding, can appear a bit dumb when treating it like a human. I would recommend using GPT 3 Turbo instead as it can also do the stuff {display_name} can do. Use GPT 4 if enabled."
    
    _api_key: str = "vertex_project_id"
    enabled = confighandler.has_api_key(_api_key)
    
    if enabled:
        vertexai.init(project=confighandler.get_api_key("vertex_project_id"))

    parameters = {
        "temperature": 0.2,
        "max_output_tokens": 256,
        "top_p": 0.8,
        "top_k": 40
    }
    
    errors = {
        "CONSUMER_INVALID": "Given Project ID for Vertex AI is invalid. Check Google Cloud Console for correct ID."
    }
    
    translate_table = {
            "role": "author",
            "content": "content"
    }
    
    @staticmethod
    def _load_translate_context_from_gpt(
        context: ConversationContext) -> list[ChatMessage]:
        """Translates a context from the GPT format to the format used by PaLM 2.

        Args:
            context (ConversationContext): The context to translate.

        Raises:
            TypeError: If the context is not of type ConversationContext.

        Returns:
            list[ChatMessage]: A list of messages so far. Used by PaLM 2.
        """
        if isinstance(context, ConversationContext):
            return [ChatMessage(reply_entry["content"], "user" if reply_entry["role"] == "user" else "bot") for reply_entry in context._context]
        raise TypeError("context should be of type ConversationContext, not {}".format(type(context)))

    @classmethod
    async def __askmodel__(cls, 
        query: str, 
        context: ConversationContext | None, 
        save_message: bool = True) -> AIQueryResponse:
        
        if not cls.enabled:
            raise DGException(f"{cls.display_name} {_error_text}")
        try:
            chat_model = ChatModel.from_pretrained(cls.model)
            ctx: list[ChatMessage] = context.get_context_translated(cls._load_translate_context_from_gpt) if context else []
            
            chat = chat_model.start_chat(
                message_history=ctx, **cls.parameters)
            response = await chat.send_message_async(query, **cls.parameters)

            if save_message and context:
                context.add_conversation_entry(query, response.text, "user")

            emulated_gpt_response = {"id": "PaLM2", "choices": [{"finish_reason": None, "message": {
                "content": response.text}}]}  # Sadly we have to emulate the json response from GPT
            return AIQueryResponse(emulated_gpt_response)

        # PermissionDenied is a class of google.api_core.exceptions
        except PermissionDenied as google_response_error:
            if google_response_error.reason:
                raise DGException(cls.errors.get(
                    google_response_error.reason, google_response_error.message))
            raise DGException(f"Google Cloud Error: {google_response_error}")

        # DefaultCredentialsError is a class of google.auth.exceptions
        except DefaultCredentialsError as google_response_error:
            raise DGException(
                "Host machine not logged into gcloud. The host machine can login by executing `gcloud auth application-default set-quota-project <Project ID>` in the terminal.")

    @classmethod
    async def __askmodelstream__(cls, 
        query: str, 
        context: ConversationContext) -> AsyncGenerator[tuple[str, int], None]:
        
        raise DGException("This model does not support streaming text generation yet.")
    
        if not cls.enabled:
            raise DGException(f"{cls.display_name} {_error_text}")
        
        try:
            chat_model = ChatModel.from_pretrained(cls.model)
            temporary_context = context.get_context_translated(cls._load_translate_context_from_gpt) if context else []

            chat = chat_model.start_chat(
                message_history=temporary_context, **cls.parameters)
            response = chat.send_message_streaming_async(query, **cls.parameters)
            
            async for r in response:
                print(r, dir(r))
                yield r

        # PermissionDenied is a class of google.api_core.exceptions
        except PermissionDenied as google_response_error:
            if google_response_error.reason:
                raise DGException(cls.errors.get(
                    google_response_error.reason, google_response_error.message))
            raise DGException(f"Google Cloud Error: {google_response_error}")

        # DefaultCredentialsError is a class of google.auth.exceptions
        except DefaultCredentialsError as google_response_error:
            raise DGException(
                "Host machine not logged into gcloud. The host machine can login by executing `gcloud auth application-default set-quota-project <Project ID>` in the terminal.")
 
AIModelType = Type[AIModel]
registered_models: dict[str, AIModelType] = {
    "gpt-4": GPT4,
    "gpt-3.5-turbo-16k": GPT3Turbo,
    "gpt-3.5-turbo": GPT3Turbo,
    "chat-bison@002": PaLM2
}
enabled_models = [m for m in registered_models.values() if m.enabled]
disabled_models = [m for m in registered_models.values() if not m.enabled]

