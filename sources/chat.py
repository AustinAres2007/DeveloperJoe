"""Handles conversations between the end-user and the GPT Engine."""

from __future__ import annotations
from collections.abc import Iterator
import datetime as _datetime, discord as _discord, openai as _openai, random as _random, openai_async as _openai_async, json as _json, asyncio as _asyncio, io as _io, speech_recognition as _speech_recognition

from enum import Enum as _Enum
from typing import (
    Union as _Union, 
    Any as _Any, 
    AsyncGenerator as _AsyncGenerator,
    TYPE_CHECKING
)
from . import (
    exceptions, 
    guildconfig, 
    history, 
    ttsmodels,
    models
)
from .common import (
    decorators,
    commands_utils,
    developerconfig
)
if TYPE_CHECKING:
    from joe import DeveloperJoe

from .voice import voice_client, reader

__all__ = [
    "GPTConversationContext",
    "DGTextChat",
    "DGVoiceChat"
]

class GPTConversationContext:
    """Class that should contain a users conversation history / context with a GPT Model."""
    def __init__(self) -> None:
        """Class that should contain a users conversation history / context with a GPT Model."""
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
        self._display_context.extend(interaction_data)
        return self._display_context
    
    def get_temporary_context(self, query, user_type: str="user") -> list:

        data = {"role": user_type, "content": query}
        _temp_context = self._context.copy()
        _temp_context.append(data)
        
        return _temp_context
        
class DGChats:
    def __init__(self, 
                bot_instance: DeveloperJoe,
                _openai_token: str, 
                user: _Union[_discord.User, _discord.Member], 
                name: str,
                stream: bool,
                display_name: str, 
                model: models.GPTModelType | str=developerconfig.DEFAULT_GPT_MODEL, 
                associated_thread: _Union[_discord.Thread, None]=None,
                is_private: bool=True,
                voice: _Union[_discord.VoiceChannel, _discord.StageChannel, None]=None
        ):
        """Represents a base DGChat. Do not use, inherit from this.

        Args:
            bot_instance (_DeveloperJoe): _description_
            _openai_token (str): _description_
            user (_Union[_discord.User, _discord.Member]): _description_
            name (str): _description_
            stream (bool): _description_
            display_name (str): _description_
            model (models.GPTModelType, optional): _description_. Defaults to developerconfig.DEFAULT_GPT_MODEL.
            associated_thread (_Union[_discord.Thread, None], optional): _description_. Defaults to None.
            is_private (bool, optional): _description_. Defaults to True.
            voice (_Union[_discord.VoiceChannel, _discord.StageChannel, None], optional): _description_. Defaults to None.
        """
        
        self.bot: DeveloperJoe = bot_instance
        self.user: _Union[_discord.User, _discord.Member] = user
        self.time: _datetime.datetime = _datetime.datetime.now()
        self.hid = hex(int(_datetime.datetime.timestamp(_datetime.datetime.now()) + user.id) * _random.randint(150, 1500))
        self.chat_thread = associated_thread
        self.last_channel: developerconfig.InteractableChannel | None = None
        self.oapi = _openai_token

        self.name = name
        self.display_name = display_name
        self.stream = stream

        print(model)
        self.model = model if isinstance(model, models.GPTModelType) else commands_utils.get_modeltype_from_name(model)
        self.tokens = 0

        self._private, self._is_active, self.is_processing = is_private, True, False
        self.header = f'{self.display_name} | {self.model.display_name}'
        self.context = GPTConversationContext()
        # Voice attributes
        
        self._voice = voice
        self._client_voice_instance: _Union[voice_client.VoiceRecvClient, None] = _discord.utils.get(self.bot.voice_clients, guild=user.guild) # type: ignore because all single instances are `discord.VoiceClient`
        self.proc_packet, self._is_speaking = False, False
        
        self.voice_tss_queue: list[str] = []
        _openai.api_key = self.oapi
    
    @property
    def is_active(self) -> bool:
        return self._is_active
    
    @is_active.setter
    def is_active(self, value: bool):
        self._is_active = value
    
    @property
    def private(self) -> bool:
        return self._private

    @private.setter
    def private(self, is_p: bool):
        self._private = is_p
    
    def __manage_tokens__(self, query_type: str, save_message: bool, tokens: int):
        if save_message and query_type == "query":
            self.tokens += tokens
            
    async def __send_query__(self, query_type: str, save_message: bool=True, **kwargs):
            
        replied_content = ""
        self.is_processing = True
        ai_reply = models.AIReply("No reply.", 0, 0, "Unknown")
        
        if query_type == "query":
            
            # Put necessary variables here (Doesn't matter weather streaming or not)
            # Reply format: ({"content": "Reply content", "role": "assistent"})
            # XXX: Need to transfer this code to GPT-3 / GPT-4 model classes (__askmodel__)
            try:
                ai_reply: models.AIReply = await self.model.__askmodel__(kwargs["content"], self.context, self.oapi, "user", save_message)
                replied_content = ai_reply._reply
            except KeyError:
                print(f"The provided OpenAI API key was invalid. ({self.bot._OPENAI_TOKEN})")
                await self.bot.close()
            
        elif query_type == "image":
            # Required Arguments: Prompt (String < 1000 chars), Size (String, 256x256, 512x512, 1024x1024)
            try:
                image_request: dict = dict(_openai.Image.create(**kwargs))
                if isinstance(image_request, dict) == True:
                    image_url = image_request['data'][0]['url']
                    replied_content = f"Created Image at {_datetime.datetime.fromtimestamp(image_request['created'])}\nImage Link: {image_url}"

                    self.context.add_image_entry(kwargs["prompt"], image_url)
                else:
                    raise exceptions.GPTReplyError(image_request, type(image_request), dir(image_request))
            except _openai.InvalidRequestError:
                raise exceptions.GPTContentFilter(kwargs["prompt"])

        self.__manage_tokens__(query_type, save_message, ai_reply._tokens)
        self.is_processing = False
        return replied_content

    async def __stream_send_query__(self, query: str, save_message: bool=True, **kwargs) -> _AsyncGenerator:
        self.is_processing = True
        try:
            tokens = 0
            ai_reply = self.model.__askmodelstream__(query, self.context, self.oapi, "user")
            async for chunk, token in ai_reply:
                tokens += token
                yield chunk
                
        except exceptions.GPTReachedLimit as e:
            self.is_active = False
            raise e
        finally:
            self.is_processing = False
            
        self.__manage_tokens__("query", save_message, tokens)
    
    async def ask(self, query: str, *_args, **_kwargs) -> str:
        raise NotImplementedError
        
    def ask_stream(self, query: str) -> _AsyncGenerator:
        raise NotImplementedError
    
    async def start(self) -> str:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError
    
    async def stop(self, interaction: _discord.Interaction, history: history.DGHistorySession, save_history: str) -> str:
        raise NotImplementedError

    @property
    def voice(self):
        return self._voice
    
    @voice.setter
    def voice(self, _voice: _Union[_discord.VoiceChannel, _discord.StageChannel, None]):
        self._voice = _voice
    
    @property
    def type(self):
        return DGChatTypesEnum.VOICE

    @property
    def is_speaking(self) -> bool:
        return self.client_voice.is_playing() if self.client_voice else False
    
    @property
    def client_voice(self) -> voice_client.VoiceRecvClient | None:
        return self._client_voice_instance
    
    @property
    def has_voice(self):
        return True if self.voice else False
    
    @client_voice.setter
    def client_voice(self, _bot_vc: voice_client.VoiceRecvClient | None) -> None:
        self._client_voice_instance = _bot_vc 
    
    async def manage_voice_packet_callback(self, member: _discord.Member, voice: _io.BytesIO):
        raise NotImplementedError
        
    async def manage_voice(self) -> _discord.VoiceClient:
       raise NotImplementedError
   
    async def speak(self, text: str, channel: developerconfig.InteractableChannel): 
       raise NotImplementedError
            
    def stop_speaking(self):
        raise NotImplementedError
    
    def pause_speaking(self):
        raise NotImplementedError
    
    def resume_speaking(self):
        raise NotImplementedError
    
    def listen(self):
        raise NotImplementedError
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"
    
    def __str__(self) -> str:
        return self.display_name
    
class DGTextChat(DGChats):
    """Represents a text-only DG Chat."""
    def __init__(self, 
                bot_instance: DeveloperJoe,
                _openai_token: str, 
                user: _Union[_discord.User, _discord.Member], 
                name: str,
                stream: bool,
                display_name: str, 
                model: models.GPTModelType | str=developerconfig.DEFAULT_GPT_MODEL, 
                associated_thread: _Union[_discord.Thread, None]=None,
                is_private: bool=True 
        ):
        """Represents a text DG Chat.

        Args:
            bot_instance (DeveloperJoe): The DeveloperJoe client instance. This is not type checked so please be wary.
            _openai_token (str): Your OpenAI API Token
            user (_Union[_discord.User, _discord.Member]): The member this text chat will belong too.
            name (str): Name of the chat.
            stream (bool): Weather the chat will be streamed. (Like ChatGPT)
            display_name (str): What the display name of the chat will be.
            model (GPTModelType, optional): Which GPT Model to use. Defaults to DEFAULT_GPT_MODEL.
            associated_thread (_Union[_discord.Thread, None], optional): What the dedicated discord thread is. Defaults to None.
            is_private (bool): Weather the chat will be private (Only showable to the user) Defaults to True.
        """
        
        super().__init__(
            bot_instance=bot_instance,
            _openai_token=_openai_token,
            user=user,
            name=name,
            stream=stream,
            display_name=display_name,
            model=model,
            associated_thread=associated_thread,
            is_private=is_private
        )
    
    @property
    def type(self):
        return DGChatTypesEnum.TEXT
    
    @property
    def is_active(self) -> bool:
        return self._is_active
    
    @is_active.setter
    def is_active(self, value: bool):
        self._is_active = value
    
    @property
    def private(self) -> bool:
        return self._private

    @private.setter
    def private(self, is_p: bool):
        self._private = is_p        
    
    @decorators.check_enabled
    async def ask_stream(self, query: str, channel: developerconfig.InteractableChannel) -> str:
        og_message = await channel.send(developerconfig.STREAM_PLACEHOLDER)
                            
        msg: list[_discord.Message] = [og_message]
        reply = self.__stream_send_query__(query, True)
        full_message = f"## {self.header}\n\n"
        i, start_message_at = 0, 0
        sendable_portion = "<>"
        message = ""
        
        try:
            async with channel.typing():
                
                async for t in reply:
                    
                    i += 1
                    full_message += t
                    message += t
                    sendable_portion = full_message[start_message_at * developerconfig.CHARACTER_LIMIT:((start_message_at + 1) * developerconfig.CHARACTER_LIMIT)]
            
                    if len(full_message) and len(full_message) >= (start_message_at + 1) * developerconfig.CHARACTER_LIMIT:
                        await msg[-1].edit(content=sendable_portion)
                        msg.append(await msg[-1].channel.send(developerconfig.STREAM_PLACEHOLDER))

                    start_message_at = len(full_message) // developerconfig.CHARACTER_LIMIT
                    if i and i % developerconfig.STREAM_UPDATE_MESSAGE_FREQUENCY == 0:
                        await msg[-1].edit(content=sendable_portion)

                else:
                    if not msg:
                        await og_message.edit(content=sendable_portion)
                    else:
                        await msg[-1].edit(content=sendable_portion)
                        
        except _discord.NotFound:
            self.is_processing = False
            raise exceptions.DGException("Stopped query since someone deleted the streaming message.")
        else:            
            return message
    
    @decorators.check_enabled
    async def ask(self, query: str, channel: developerconfig.InteractableChannel):
        async with channel.typing():
            reply = await self.__send_query__(query_type="query", role="user", content=query)
            final_user_reply = f"## {self.header}\n\n{reply}"
            
            if len(final_user_reply) > developerconfig.CHARACTER_LIMIT:
                file_reply: _discord.File = commands_utils.to_file(final_user_reply, "reply.txt")
                await channel.send(file=file_reply)
            else:
                await channel.send(final_user_reply)
                
        return reply
            
    async def start(self) -> str:
        """Sends a start query to GPT.

        Returns:
            str: The welcome message.
        """
        return str(await self.__send_query__(save_message=False, query_type="query", role="system", content="Please give a short and formal introduction (Under 1800 characters) of yourself (ChatGPT) what you can do and limitations."))

    def clear(self) -> None:
        """Clears the internal chat history."""
        self.context._context.clear()
        self.context._display_context.clear()
    
    async def stop(self, interaction: _discord.Interaction, history: history.DGHistorySession, save_history: str) -> str:
        """Stops the chat instance.

        Args:
            interaction (_discord.Interaction): The discord interaction instance.
            history (DGHistorySession): A chat history session to upload chat data.
            save_history (str): Weather the chat should be saved. (Will be boolean soon)

        Raises:
            CannotDeleteThread: Raised if the associated thread cannot be deleted.
            DGException: Raised if DG cannot delete your chat thread because of insuffient permissions.

        Returns:
            str: A farewell message.
        """
        if isinstance(self.chat_thread, _discord.Thread) and self.chat_thread.id == interaction.channel_id:
            raise exceptions.CannotDeleteThread(self.chat_thread)
        try:
            farewell = f"Ended chat: {self.display_name} with {developerconfig.BOT_NAME}!"
            if save_history == "y":
                history.upload_chat_history(self)
                farewell += f"\n\n\n*Saved chat history with ID: {self.hid}*"
            else:
                farewell += "\n\n\n*Not saved chat history*"

            if isinstance(self.chat_thread, _discord.Thread):
                await self.chat_thread.delete()
            return farewell
        except _discord.Forbidden as e:
            raise exceptions.DGException(f"I have not been granted suffient permissions to delete your thread in this server. Please contact the servers administrator(s).", e)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} type={self.type}, user={self.user} is_active={self.is_active}>"
    
    def __str__(self) -> str:
        return self.display_name
    
class DGVoiceChat(DGTextChat):
    """Represents a voice and text DG Chat."""
    def __init__(
            self,
            bot_instance: _Any,
            _openai_token: str, 
            user: _discord.Member, 
            name: str,
            stream: bool,
            display_name: str, 
            model: models.GPTModelType | str=developerconfig.DEFAULT_GPT_MODEL, 
            associated_thread: _Union[_discord.Thread, None]=None, 
            is_private: bool=True,
            voice: _Union[_discord.VoiceChannel, _discord.StageChannel, None]=None
        ):
        """Represents a voice and text DG Chat.

        Args:
            bot_instance (_commands.Bot): Your bots main instance.
            _openai_token (str): Your OpenAI API Token
            user (_Union[_discord.User, _discord.Member]): The member this text chat will belong too.
            name (str): Name of the chat.
            stream (bool): Weather the chat will be streamed. (Like ChatGPT)
            display_name (str): What the display name of the chat will be.
            model (GPTModelType, optional): Which GPT Model to use. Defaults to DEFAULT_GPT_MODEL.
            associated_thread (_Union[_discord.Thread, None], optional): What the dedicated discord thread is. Defaults to None.
            voice (_Union[_discord.VoiceChannel, _discord.StageChannel, None], optional): (DGVoiceChat only) What voice channel the user is in. This is set dynamically by listeners. Defaults to None.
        """
        super().__init__(bot_instance, _openai_token, user, name, stream, display_name, model, associated_thread, is_private)
        self._voice = voice
        self._client_voice_instance: _Union[voice_client.VoiceRecvClient, None] = _discord.utils.get(self.bot.voice_clients, guild=user.guild) # type: ignore because all single instances are `discord.VoiceClient`
        self._is_speaking = False
        self.voice_tss_queue: list[str] = []
    
    @property
    def voice(self):
        return self._voice
    
    @voice.setter
    def voice(self, _voice: _Union[_discord.VoiceChannel, _discord.StageChannel, None]):
        self._voice = _voice
    
    @property
    def type(self):
        return DGChatTypesEnum.VOICE

    @property
    def is_speaking(self) -> bool:
        return self.client_voice.is_playing() if self.client_voice else False
    
    @property
    def client_voice(self) -> voice_client.VoiceRecvClient | None:
        return self._client_voice_instance
    
    @property
    def has_voice(self):
        return True if self.voice else False
    
    @client_voice.setter
    def client_voice(self, _bot_vc: voice_client.VoiceRecvClient | None) -> None:
        self._client_voice_instance = _bot_vc 
    
    async def manage_voice_packet_callback(self, member: _discord.Member, voice: _io.BytesIO):
        try:
            
            if self.proc_packet == False:
                self.proc_packet = True
                recogniser = _speech_recognition.Recognizer()
                try:
                    with _speech_recognition.AudioFile(voice) as wav_file:
                        data = recogniser.record(wav_file)
                        text = recogniser.recognize_google(data, pfilter=0)
                except _speech_recognition.UnknownValueError:
                    pass
                else:
                    prefix = guildconfig.get_guild_config_attribute(member.guild, "voice-keyword")
                    if prefix and isinstance(text, str) and text.lower().startswith(prefix) and self.last_channel: # Recognise keyword
                        text = text.split(developerconfig.LISTENING_KEYWORD)[1].lstrip()
                        usr_voice_convo = self.bot.get_default_voice_conversation(member)
                        
                        if isinstance(usr_voice_convo, DGVoiceChat): # Make sure user has vc chat
                            await getattr(usr_voice_convo, "ask" if usr_voice_convo.stream == False else "ask_stream")(text, self.last_channel)
        finally:
            self.proc_packet = False
        
    async def manage_voice(self) -> _discord.VoiceClient:
        
        voice: voice_client.VoiceRecvClient = _discord.utils.get(self.bot.voice_clients, guild=self.voice.guild if self.voice else None) # type: ignore because all single instances are `discord.VoiceClient`
        
        # I know elif exists. I am doing this for effiency.
        if voice and voice.is_connected() and (self.voice == voice.channel):
            pass
        else:
            if voice and voice.is_connected() and (self.voice != voice.channel):
                await voice.move_to(self.voice)
            elif self.voice:
                self.client_voice = await self.voice.connect(cls=voice_client.VoiceRecvClient)
                voice: voice_client.VoiceRecvClient = self.client_voice
            await _asyncio.sleep(5.0)
        
        return voice
    
    @decorators.has_voice
    async def speak(self, text: str, channel: developerconfig.InteractableChannel): 
        try:
            self.last_channel = channel
            self.voice_tss_queue.append(text)
            new_voice = await self.manage_voice()
            
            def _play_voice(index: int, error: _Any=None):
                if not error:
                    if not (index >= len(self.voice_tss_queue)):
                        speed: int = guildconfig.get_guild_config_attribute(new_voice.guild, "speed")
                        return new_voice.play(_discord.FFmpegPCMAudio(source=ttsmodels.GTTSModel(self.voice_tss_queue[index]).process_text(speed), executable=developerconfig.FFMPEG, pipe=True), after=lambda error: _play_voice(index + 1, error))
                        
                    self.voice_tss_queue.clear()
                else:
                    raise exceptions.DGException(f"VoiceError: {str(error)}", log_error=True, send_exceptions=True)
                
            _play_voice(0)
            
        except _discord.ClientException:
            pass
        except IndexError:
            self.voice_tss_queue.clear()
            
        
    @decorators.check_enabled
    @decorators.has_voice_with_error
    @decorators.dg_in_voice_channel
    @decorators.dg_is_speaking
    async def stop_speaking(self):
        """Stops the bots voice reply for a user. (Cannot be resumed)"""
        self.client_voice.stop() # type: ignore Checks done with decorators.
    
    @decorators.check_enabled
    @decorators.has_voice_with_error
    @decorators.dg_in_voice_channel
    @decorators.dg_is_speaking
    async def pause_speaking(self):
        """Pauses the bots voice reply for a user."""
        self.client_voice.pause() # type: ignore Checks done with decorators.
    
    @decorators.check_enabled
    @decorators.has_voice_with_error
    @decorators.dg_in_voice_channel
    @decorators.dg_isnt_speaking
    async def resume_speaking(self):
        """Resumes the bots voice reply for a user."""
        self.client_voice.resume() # type: ignore Checks done with decorators.
    
    @decorators.check_enabled
    @decorators.has_voice_with_error
    @decorators.dg_in_voice_channel
    @decorators.dg_isnt_speaking
    @decorators.dg_isnt_listening
    async def listen(self):
        """Starts the listening events for a users voice conversation."""
        self.client_voice.listen(reader.SentenceSink(self.bot, self.manage_voice_packet_callback, 2.5)) # type: ignore Checks done with decorators.
    
    @decorators.check_enabled
    @decorators.has_voice_with_error
    @decorators.dg_in_voice_channel
    @decorators.dg_isnt_speaking
    @decorators.dg_is_listening
    async def stop_listening(self):
        """Stops the listening events for a users voice conversation"""
        self.client_voice._reader.sink.cleanup() # type: ignore Checks done with decorators.
        self.client_voice.stop_listening() # type: ignore Checks done with decorators.
        
        
    async def ask(self, query: str, channel: developerconfig.InteractableChannel) -> str:
        
        text = await super().ask(query, channel)
        if isinstance(channel, developerconfig.InteractableChannel):
            await self.speak(text, channel)
        else:
            raise TypeError("channel cannot be {}. utils.InteractableChannels only.".format(channel.__class__))
        
        return text

    async def ask_stream(self, query: str, channel: developerconfig.InteractableChannel) -> str:

        text = await super().ask_stream(query, channel)
        if isinstance(channel, developerconfig.InteractableChannel):
            await self.speak(text, channel)
        else:
            raise TypeError("channel cannot be {}. utils.InteractableChannels only.".format(channel.__class__))

        return text
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} type={self.type}, user={self.user}, voice={self.voice}, is_active={self.is_active}>"
    
    def __str__(self) -> str:
        return self.display_name
    
class DGChatTypesEnum(_Enum):
    """Enums for chat types (text or voice)"""
    TEXT = 1
    VOICE = 2

DGChatType = DGTextChat | DGVoiceChat