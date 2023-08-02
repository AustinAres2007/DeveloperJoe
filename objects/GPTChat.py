import datetime, discord, openai, random, openai_async, json, tiktoken

from typing import Union, Any, AsyncGenerator, Callable
from objects import GPTHistory, GPTErrors, GPTConfig, GPTExceptions

class GPTTypes:
    text = 1
    voice = 2

class GPTChat:
    def __init__(self, 
                openai_token: str, 
                user: Union[discord.User, discord.Member], 
                name: str,
                stream: bool,
                display_name: str, 
                model: str=GPTConfig.DEFAULT_GPT_MODEL, 
                associated_thread: Union[discord.Thread, None]=None, 
        ):

        
        self.user: Union[discord.User, discord.Member] = user
        self.time: datetime.datetime = datetime.datetime.now()
        self.hid = hex(int(datetime.datetime.timestamp(datetime.datetime.now()) + user.id) * random.randint(150, 1500))
        self.chat_thread = associated_thread

        self.oapi = openai_token
        self.chat_thread = associated_thread

        self.name = name
        self.display_name = display_name
        self.stream = stream

        self.model = str(model)
        self.encoding = tiktoken.encoding_for_model(self.model)
        self.tokens = 0

        self.is_processing = False
        self._is_active = True

        self.readable_history = []
        self.chat_history = []

        self._type = GPTTypes.text
        openai.api_key = self.oapi
    
    @property
    def type(self):
        return self._type
    
    @property
    def is_active(self) -> bool:
        return self._is_active
    
    @is_active.setter
    def is_active(self, value: bool):
        self._is_active = value

    def __manage_history__(self, is_gpt_reply: Any, query_type: str, save_message: bool, tokens: int):
        self.is_processing = False

        if not save_message and query_type == "query":
            self.chat_history = self.chat_history[:len(self.chat_history)-2]
            self.readable_history.pop()

        elif not save_message and query_type == "image":
            self.readable_history.pop()

        if is_gpt_reply and save_message and query_type == "query":
            self.tokens += tokens

        return 
    
    async def __get_stream_parsed_data__(self, messages: list[dict], **kwargs) -> AsyncGenerator:
        payload = {"model": self.model, "messages": messages, "stream": True} | kwargs
        reply = await openai_async.chat_complete(api_key=self.oapi, timeout=GPTConfig.GPT_REQUEST_TIMEOUT, payload=payload)

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

    async def __send_query__(self, query_type: str, save_message: bool=True, **kwargs):
            
        replied_content = GPTErrors.GENERIC_ERROR
        error = None
        r_history = []
        replied_content = ""

        reply: Union[None, dict] = None
        usage: Union[None, dict] = None
        self.is_processing = True

        if query_type == "query":
            
            # Put necessary variables here (Doesn't matter weather streaming or not)
            self.chat_history.append(kwargs)

            # TODO: Test async module
            # Reply format: ({"content": "Reply content", "role": "assistent"})
            _reply = await openai_async.chat_complete(api_key=self.oapi, timeout=GPTConfig.GPT_REQUEST_TIMEOUT,
                                                        payload={
                                                            "model": self.model,
                                                            "messages": self.chat_history    
                                                        })
            
            reply = _reply.json()["choices"][0]
            usage = _reply.json()["usage"]

            if isinstance(reply, dict):
                actual_reply = reply["message"]  
                replied_content = actual_reply["content"]

                self.chat_history.append(dict(actual_reply))

                r_history.append(kwargs)
                r_history.append(dict(actual_reply))
                self.readable_history.append(r_history)
            else:
                raise GPTExceptions.GPTReplyError(reply, type(reply))
            
        elif query_type == "image":
            # Required Arguments: Prompt (String < 1000 chars), Size (String, 256x256, 512x512, 1024x1024)

            image_request: dict = dict(openai.Image.create(**kwargs))
            if isinstance(image_request, dict) == True:
                image_url = image_request['data'][0]['url']
                replied_content = f"Created Image at {datetime.datetime.fromtimestamp(image_request['created'])}\nImage Link: {image_url}"
                r_history.extend([{'image': f'User asked GPT to compose the following image: "{kwargs["prompt"]}"'}, {'image_return': image_url}])

                self.readable_history.append(r_history)
            
            raise GPTExceptions.GPTReplyError(image_request, type(image_request), dir(image_request))
        
        else:
            error = f"Generic ({query_type})"

        self.__manage_history__(reply, query_type, save_message, usage["total_tokens"] if reply and usage else 0)
        return replied_content if not error or not str(error).strip() else f"Error: {str(error)}"

    async def __stream_send_query__(self, save_message: bool=True, **kwargs):
        total_tokens = len(self.encoding.encode(kwargs["content"]))
        r_history = []
        replied_content = ""

        add_history, self.is_processing = True, True
        self.chat_history.append(kwargs)
        generator_reply = self.__get_stream_parsed_data__(self.chat_history)

        async for chunk in generator_reply:
            stop_reason = chunk["choices"][0]["finish_reason"]
            if stop_reason == None:
                c_token = chunk["choices"][0]["delta"]["content"].encode("latin-1").decode()
                replied_content += c_token
                total_tokens += len(self.encoding.encode(c_token))

                yield c_token
            elif stop_reason == "length":
                add_history = self.is_active = False
                raise GPTExceptions.GPTReachedLimit()

            elif stop_reason == "content_filter":
                add_history = False
                raise GPTExceptions.GPTContentFilter(kwargs["content"])

        if add_history == True:
            replicate_reply = {"role": "assistant", "content": replied_content}
            self.chat_history.append(replicate_reply)

            r_history.append(kwargs)
            r_history.append(replicate_reply)

            self.readable_history.append(r_history)

            self.__manage_history__(generator_reply, "query", save_message, total_tokens)

    async def ask(self, query: str) -> str:
        if self.is_active:
            return str(await self.__send_query__(query_type="query", role="user", content=query))
        raise GPTExceptions.ChatIsDisabledError(self)
    
    def ask_stream(self, query: str) -> AsyncGenerator:
        if self.is_active:
            return self.__stream_send_query__(role="user", content=query)
        raise GPTExceptions.ChatIsDisabledError(self)
    
    async def start(self) -> str:
        return str(await self.__send_query__(save_message=False, query_type="query", role="system", content="Please give a short and formal introduction to yourself, what you can do, and limitations."))

    def clear(self) -> None:
        self.readable_history.clear()
        self.chat_history.clear()
    
    async def stop(self, interaction: discord.Interaction, history: GPTHistory.GPTHistory, save_history: str) -> str:
        if isinstance(self.chat_thread, discord.Thread) and self.chat_thread.id == interaction.channel_id:
            raise GPTExceptions.CannotDeleteThread(self.chat_thread)
        try:
            farewell = f"Ended chat: {self.display_name} with {GPTConfig.BOT_NAME}!"
            if save_history == "y":
                history.upload_chat_history(self)
                farewell += f"\n\n\n*Saved chat history with ID: {self.hid}*"
            else:
                farewell += "\n\n\n*Not saved chat history*"

            if isinstance(self.chat_thread, discord.Thread):
                await self.chat_thread.delete()
            return farewell
        except discord.Forbidden as e:
            raise GPTExceptions.DGException(f"I have not been granted suffient permissions to delete your thread in this server. Please contact the servers administrator(s).", e)

    def __str__(self) -> str:
        return f"<GPTChat type={self.type}, user={self.user} is_active={self.is_active}>"
    
class GPTVoiceChat(GPTChat):
    def __init__(
            self,
            openai_token: str, 
            user: Union[discord.User, discord.Member], 
            name: str,
            stream: bool,
            display_name: str, 
            model: str=GPTConfig.DEFAULT_GPT_MODEL, 
            associated_thread: Union[discord.Thread, None]=None, 
            voice: Union[discord.VoiceChannel, discord.StageChannel, None]=None
        ):
        super().__init__(openai_token, user, name, stream, display_name, model, associated_thread)
        self._voice = voice
        self._type = GPTTypes.voice
    
    @property
    def voice(self):
        return self._voice
    
    @voice.setter
    def voice(self, _voice: Union[discord.VoiceChannel, discord.StageChannel, None]):
        self._voice = _voice
    
    @property
    def type(self):
        return self._type

    def __str__(self) -> str:
        return f"<GPTVoiceChat type={self.type}, user={self.user}, voice={self.voice}, is_active={self.is_active}>"
        