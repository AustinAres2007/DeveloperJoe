"""Handles conversations between the end-user and the GPT Engine."""

from __future__ import annotations

import datetime as _datetime, discord, openai as _openai, random as _random, asyncio as _asyncio
import logging
import aiohttp

from typing import (
    Type,
    Union as _Union, 
    Any as _Any, 
    AsyncGenerator as _AsyncGenerator,
    TYPE_CHECKING
)

from sources import models
from . import (
    exceptions, 
    confighandler, 
    history, 
    ttsmodels,
    models,
    exceptions,
    errors,
    responses
)
from .common import (
    decorators,
    commands_utils,
    developerconfig,
    common,
    types
)

if TYPE_CHECKING:
    from joe import DeveloperJoe


_openai.api_key = confighandler.get_api_key("openai_api_key")
__all__ = [
    "DGTextChat",
    "DGVoiceChat"
]
    

"""
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
                raise GPTContentFilter(query)

    if add_history == True and isinstance(context, GPTConversationContext):
        context.add_conversation_entry(query, replied_content, "user")
""" # TODO: Implement into ask_stream
    
class DGChat:
        
    def __init__(self,
                member:  discord.Member, 
                bot_instance: DeveloperJoe,
                name: str,
                stream: bool,
                display_name: str, 
                model: Type[models.AIModel] | str=confighandler.get_config('default_ai_model'),
                associated_thread: _Union[discord.Thread, None]=None,
                is_private: bool=True,
                voice: _Union[discord.VoiceChannel, discord.StageChannel, None]=None
        ):
        """Represents a base DGChat. Do not use, inherit from this.

        Args:
            bot_instance (_DeveloperJoe): _description_
            _openai_token (str): _description_
            user (_Union[discord.User, discord.Member]): _description_
            name (str): _description_
            stream (bool): _description_
            display_name (str): _description_
            model (models.AIModel, optional): _description_. Defaults to default_ai_model. If the config changes while the bot is active, this default will not change as it is defined at runtime.
            associated_thread (_Union[discord.Thread, None], optional): _description_. Defaults to None.
            is_private (bool, optional): _description_. Defaults to True.
            voice (_Union[discord.VoiceChannel, discord.StageChannel, None], optional): _description_. Defaults to None.
        """
        
        self.bot: DeveloperJoe = bot_instance
        self.member: discord.Member = member
        self.time: _datetime.datetime = _datetime.datetime.now()
        self.hid = hex(int(_datetime.datetime.timestamp(_datetime.datetime.now()) + member.id) * _random.randint(150, 1500))
        self.chat_thread = associated_thread

        self.name = name
        self.display_name = display_name
        self.stream = stream

        if isinstance(model, type(models.AIModel)):
            self.model: models.AIModel = model(member) # type: ignore shutup I did the check
        else:
            self.model: models.AIModel = commands_utils.get_modeltype_from_name(str(model))(member)

        self._private, self._is_active, self.is_processing = is_private, True, False
        self.header = f'{self.display_name} | {self.model.display_name}'
        
        # Voice attributes
        
        self._voice = voice
        self._client_voice_instance: discord.VoiceClient | None = discord.utils.get(self.bot.voice_clients, guild=member.guild) # type: ignore because all single instances are `discord.VoiceClient`
        self.proc_packet, self._is_speaking = False, False
        
        self.voice_tss_queue: list[str] = []
    
    async def get_personal_channel_or_current(self, channel: discord.abc.Messageable) -> discord.abc.Messageable:
        
        if not self.private:
            return channel
        elif self.private and self.member.dm_channel == None:
            return await self.member.create_dm()
        elif isinstance(self.member.dm_channel, discord.DMChannel):
            return self.member.dm_channel
        
        return channel
            
    @property
    def is_active(self) -> bool:
        return self._is_active
    
    @is_active.setter
    def is_active(self, value: bool):
        self._is_active = value
    
    @property
    def private(self) -> bool:
        return self._private

    @property
    def context(self) -> models.ReadableContext:
        return self.model.context
    
    @private.setter
    def private(self, is_p: bool):
        self._private = is_p
    
    async def ask(self, query: str, image_urls: list[str] | None=None):
        raise NotImplementedError
        
    async def ask_stream(self, query: str, channel: developerconfig.InteractableChannel) -> _AsyncGenerator:
        raise NotImplementedError
    
    async def generate_image(self, prompt: str, resolution: str="512x512") -> models.AIImageResponse:
        raise NotImplementedError

    async def read_image(self, query: str) -> models.AIQueryResponse:
        raise NotImplementedError
    
    async def add_images(self, image_urls: list[str], check_if_valid: bool=True) -> None:
        raise NotImplementedError

    async def start(self) -> None:
        self.bot.add_conversation(self.member, self.display_name, self)
        self.bot.set_default_conversation(self.member, self.display_name)
        await self.model.start_chat()

    async def clear(self) -> None:
        raise NotImplementedError
    
    async def stop(self, interaction: discord.Interaction, save_history: bool) -> str:
        raise NotImplementedError
    
    @property
    def type(self):
        return types.DGChatTypesEnum.VOICE
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"
    
    def __str__(self) -> str:
        return self.display_name

class DGTextChat(DGChat):
    """Represents a text-only DG Chat."""
    def __init__(self, 
                member: discord.Member,
                bot_instance: DeveloperJoe,
                name: str,
                stream: bool,
                display_name: str, 
                model: Type[models.AIModel] | str=confighandler.get_config('default_ai_model'), 
                associated_thread: _Union[discord.Thread, None]=None,
                is_private: bool=True 
        ):
        """Represents a text DG Chat.

        Args:
            bot_instance (DeveloperJoe): The DeveloperJoe client instance. This is not type checked so please be wary.
            _openai_token (str): Your OpenAI API Token
            user (_Union[discord.User, discord.Member]): The member this text chat will belong too.
            name (str): Name of the chat.
            stream (bool): Weather the chat will be streamed. (Like ChatGPT)
            display_name (str): What the display name of the chat will be.
            model (AIModel, optional): Which GPT Model to use. Defaults to DEFAULT_GPT_MODEL.
            associated_thread (_Union[discord.Thread, None], optional): What the dedicated discord thread is. Defaults to None.
            is_private (bool): Weather the chat will be private (Only showable to the user) Defaults to True.
        """
        
        super().__init__(
            bot_instance=bot_instance,
            member=member,
            name=name,
            stream=stream,
            display_name=display_name,
            model=model,
            associated_thread=associated_thread,
            is_private=is_private
        )
    
    @property
    def type(self):
        return types.DGChatTypesEnum.TEXT
    
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
        
        if self.model.can_stream == False:
            raise exceptions.DGException(f"{self.model} does not support streaming text.")
        
        private_channel = await self.get_personal_channel_or_current(channel)
        og_message = await private_channel.send(developerconfig.STREAM_PLACEHOLDER)
        self.is_processing = True
        
        async def _stream_reply():
            try:
                ai_reply: _AsyncGenerator[models.AIQueryResponseChunk | models.AIErrorResponse, None] = await self.model.ask_model_stream(query)
                async for chunk in ai_reply:
                    if isinstance(chunk, models.AIQueryResponseChunk):
                        yield chunk.response
                    
                    elif isinstance(chunk, models.AIErrorResponse):
                        models._handle_error(chunk)
                    
                    # TODO: Must sort out stop_reason (If is ResponseChunk)
                    
            except discord.Forbidden as e: # XXX: old exception was GPTReachedLimit. Must conform to new model systems. New exception (Forbidden) is temp
                self.is_active = False
                raise e
            except AttributeError:
                self.is_active = False
                raise exceptions.DGException(f"{self.model} does not support streaming.")
            finally:
                self.is_processing = False
                
        msg: list[discord.Message] = [og_message]
        reply = _stream_reply()
        full_message = f"## {self.header}\n\n"
        i, start_message_at = 0, 0
        sendable_portion = "<>"
        message = ""
        
        try:                
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
            
        except (discord.NotFound, aiohttp.ClientOSError):
            self.is_processing = False
            raise exceptions.DGException("Stopped streaming query as the streamed message was deleted.")
        else:            
            self.context.add_conversation_entry(query, full_message)
            return message
    
    @decorators.check_enabled
    async def generate_image(self, prompt: str, resolution: str = "512x512") -> models.AIImageResponse:
        try:
            image = await self.model.generate_image(prompt)
            self.context.add_image_entry(prompt, str(image.image_url))
            return image
        except _openai.BadRequestError:
            raise exceptions.DGException(errors.AIErrors.AI_REQUEST_ERROR)
        
    @decorators.check_enabled
    async def ask(self, query: str):
        
        if self.model.can_talk == False:
            raise exceptions.ModelError(f"{self.model} cannot talk.")

        # TODO: Remove _send_query as it is pretty useless.
        async def _send_query():
            self.is_processing = True
            
            try:

                response: models.AIQueryResponse = await self.model.ask_model(query)    
                self.is_processing = False

                return response
            except KeyError:
                common.send_fatal_error_warning(f"The Provided OpenAI API key was invalid.")
                return await self.bot.close()
            except TimeoutError:
                raise exceptions.DGException(errors.AIErrors.AI_TIMEOUT_ERROR)
            finally:
                self.is_processing = False
            
        
        reply = await _send_query()
        final_user_reply = f"## {self.header}\n\n{reply.response}"
        self.context.add_conversation_entry(query, reply.response)        
            
        return final_user_reply
    
    async def read_image(self, query: str) -> models.AIQueryResponse:
        if self.model.can_read_images == False or self.model._image_reader_context == None:
            raise exceptions.ModelError(f"{self.model} does not support image reading.")
        
        image_query_reply: models.AIQueryResponse = await self.model.ask_image(query)
        self.context.add_reader_entry(query, self.model._image_reader_context.image_urls, image_query_reply.response)
        return image_query_reply
    
    async def add_images(self, image_urls: list[str], check_if_valid: bool=True) -> None:
        await self.model.add_images(image_urls, check_if_valid)
    
    async def start(self) -> None:
        """Sends a start query to GPT.

        Returns:
            str: The welcome message.
        """
        await super().start()

    async def clear(self) -> None:
        """Clears all internal chat history."""
        # FIXME: Waiting to be transfered to new model system

        await self.model.clear_context()
        self.context.clear()
    
    async def stop(self, interaction: discord.Interaction, save_history: bool) -> str:
        """Stops the chat instance.

        Args:
            interaction (discord.Interaction): The discord interaction instance.
            history (DGHistorySession): A chat history session to upload chat data.
            save_history (str): Weather the chat should be saved. (Will be boolean soon)

        Raises:
            CannotDeleteThread: Raised if the associated thread cannot be deleted.
            DGException: Raised if DG cannot delete your chat thread because of insuffient permissions.

        Returns:
            str: A farewell message.
        """
        with history.DGHistorySession() as dg_history:
            member: discord.Member = commands_utils.assure_class_is_value(interaction.user, discord.Member)
            if isinstance(self.chat_thread, discord.Thread) and self.chat_thread.id == interaction.channel_id:
                raise exceptions.ConversationError(errors.ConversationErrors.CANNOT_STOP_IN_CHANNEL)
            try:
                farewell = f"Ended chat: {self.display_name} with {confighandler.get_config('bot_name')}!"
                await self.bot.delete_conversation(member, self.display_name)
                self.bot.reset_default_conversation(member)
                
                if save_history == True:
                    dg_history.upload_chat_history(self)
                    farewell += f"\n\n\n*Saved chat history with ID: {self.hid}*"
                else:
                    farewell += "\n\n\n*Not saved chat history*"

                if isinstance(self.chat_thread, discord.Thread):
                    await self.chat_thread.delete()
                return farewell
            
            # TODO: Return History ID instead of a message
            
            except discord.Forbidden as e:
                raise exceptions.DGException(f"I have not been granted suffient permissions to delete your thread in this server. Please contact the servers administrator(s).", e)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} type={self.type}, user={self.member} is_active={self.is_active}>"
    
    def __str__(self) -> str:
        return self.display_name

class StdinFFmpegPCMAudioFix(discord.FFmpegPCMAudio):
    def _kill_process(self) -> None:
        MISSING = discord.utils.MISSING
        _log = logging.getLogger(__name__)
        
        proc = self._process
        if proc is MISSING:
            return

        _log.debug('Preparing to terminate ffmpeg process %s.', proc.pid)

        try:
            proc.kill()
        except Exception:
            _log.exception('Ignoring error attempting to kill ffmpeg process %s', proc.pid)

        try:
            if proc.poll() is None:
                _log.info('ffmpeg process %s has not terminated. Waiting to terminate...', proc.pid)            
                proc.communicate()
                _log.info('ffmpeg process %s should have terminated with a return code of %s.', proc.pid, proc.returncode)
            else:
                _log.info('ffmpeg process %s successfully terminated with return code of %s.', proc.pid, proc.returncode)
        except ValueError:
            pass
        
class DGVoiceChat(DGTextChat):
    
    """Represents a voice and text DG Chat."""
    
    def __init__(
            self,
            member: discord.Member, 
            bot_instance: DeveloperJoe,
            name: str,
            stream: bool,
            display_name: str, 
            model: Type[models.AIModel] | str=confighandler.get_config('default_ai_model'), 
            associated_thread: _Union[discord.Thread, None]=None, 
            is_private: bool=True,
            voice: _Union[discord.VoiceChannel, discord.StageChannel, None]=None
        ):
        """Represents a voice and text DG Chat.

        Args:
            bot_instance (_commands.Bot): Your bots main instance.
            _openai_token (str): Your OpenAI API Token
            user (_Union[discord.User, discord.Member]): The member this text chat will belong too.
            name (str): Name of the chat.
            stream (bool): Weather the chat will be streamed. (Like ChatGPT)
            display_name (str): What the display name of the chat will be.
            model (models.AIModel, optional): Which GPT Model to use. Defaults to DEFAULT_GPT_MODEL.
            associated_thread (_Union[discord.Thread, None], optional): What the dedicated discord thread is. Defaults to None.
            voice (_Union[discord.VoiceChannel, discord.StageChannel, None], optional): (DGVoiceChat only) What voice channel the user is in. This is set dynamically by listeners. Defaults to None.
        """
        super().__init__(member, bot_instance, name, stream, display_name, model, associated_thread, is_private)
        self._voice = voice
        self._client_voice_instance: discord.VoiceClient | None = discord.utils.get(self.bot.voice_clients, guild=member.guild) # type: ignore because all single instances are `discord.VoiceClient`
        self._is_speaking = False
        self.voice_tss_queue: list[str] = []
    
    @property
    def voice(self):
        return self._voice
    
    @voice.setter
    def voice(self, _voice: _Union[discord.VoiceChannel, discord.StageChannel, None]):
        self._voice = _voice
    
    @property
    def type(self):
        return types.DGChatTypesEnum.VOICE

    @property
    def is_speaking(self) -> bool:
        return self.client_voice.is_playing() if self.client_voice else False
    
    @property
    def has_voice(self) -> bool:
        return True if self.voice else False

    
    def cleanup_voice(self):
        self.voice_tss_queue.clear()
        
    async def manage_voice(self) -> discord.VoiceClient:
        
        voice: discord.VoiceClient = discord.utils.get(self.bot.voice_clients, guild=self.voice.guild if self.voice else None) # type: ignore because all single instances are `discord.VoiceClient`
        
        # I know elif exists. I am doing this for effiency.
        if voice and voice.is_connected() and (self.voice == voice.channel):
            pass
        else:
            if voice and voice.is_connected() and (self.voice != voice.channel):
                await voice.move_to(self.voice)
            elif self.voice:
                self.client_voice = await self.voice.connect() # type: ignore shutup it'll work. it conforms
                voice: discord.VoiceClient = self.client_voice
            await _asyncio.sleep(5.0)
        
        return voice
    
    @decorators.has_voice
    async def speak(self, text: str): 
        try:
            self.voice_tss_queue.append(text)
            new_voice = await self.manage_voice()
            
            def _play_voice(index: int, error: _Any=None):
                if not error:
                    if not (index >= len(self.voice_tss_queue)):
                        speed: int = confighandler.get_guild_config_attribute(new_voice.guild, "voice-speed")
                        volume: int = confighandler.get_guild_config_attribute(new_voice.guild, "voice-volume")
                        
                        ffmpeg_pcm = StdinFFmpegPCMAudioFix(source=ttsmodels.GTTSModel(self.member, self.voice_tss_queue[index]).process_text(speed), executable=developerconfig.FFMPEG, pipe=True)
                        volume_source = discord.PCMVolumeTransformer(ffmpeg_pcm)
                        volume_source.volume = volume
                        
                        return new_voice.play(volume_source, after=lambda error: _play_voice(index + 1, error))
                        
                    self.voice_tss_queue.clear()
                else:
                    raise exceptions.DGException(f"VoiceError: {str(error)}", log_error=True, send_exceptions=True)

            
            if new_voice.is_paused():
                new_voice.stop()
            _play_voice(0)
            
        except discord.ClientException:
            pass
        except IndexError:
            self.voice_tss_queue.clear()
    
    @decorators.has_config
    async def speak_and_say(self, text: str, channel: developerconfig.InteractableChannel):
        await self.speak(text)
        if isinstance(channel, developerconfig.InteractableChannel):
            return await channel.send()
        raise TypeError(f"`channel` must be InteractableChannel, not {channel.__class__.__name__}")
    
    @decorators.check_enabled
    @decorators.has_voice_with_error
    @decorators.dg_in_voice_channel
    @decorators.dg_is_speaking
    async def stop_speaking(self):
        """Stops the bots voice reply for a user. (Cannot be resumed)"""
        self.client_voice.cleanup()
        self.client_voice.stop() # type: ignore checks in decorators
    
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
        
    async def ask(self, query: str):
        
        text = str(await super().ask(query))
        await self.speak(text)
        
        return text

    async def ask_stream(self, query: str, channel: developerconfig.InteractableChannel) -> str:

        
        if isinstance(channel, developerconfig.InteractableChannel):
            text = await super().ask_stream(query, channel)
            await self.speak(text)
        else:
            raise TypeError("channel cannot be {}. types.InteractableChannels only.".format(channel.__class__))

        return text

    async def read_image(self, query: str) -> models.AIQueryResponse:
        image_query = await super().read_image(query)
        await self.speak(image_query.response)
        return image_query
    
            
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} type={self.type}, user={self.member}, voice={self.voice}, is_active={self.is_active}>"
    
    def __str__(self) -> str:
        return self.display_name

DGChatType = DGTextChat | DGVoiceChat | DGChat