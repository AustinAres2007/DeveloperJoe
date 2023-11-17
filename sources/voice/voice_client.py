# -*- coding: utf-8 -*-

from typing import Any, Callable, Optional
import discord
import threading

from discord import AudioSource, opus
from discord.errors import ClientException
from discord.gateway import DiscordVoiceWebSocket
from .gateway import hook
from .reader import AudioReader, AudioSink

class BodgedAudioPlayer(discord.player.AudioPlayer):
    def run(self) -> None:
        try:
            self._do_run()
        except Exception as exc:
            self._current_error = exc
            print("EXC FROM BAP ", exc)
            self.stop()
        finally:
            self._call_after()

class BodgedVoiceClient(discord.VoiceClient):
    def play(self, source: BodgedAudioPlayer, *, after: Optional[Callable[[Optional[Exception]], Any]] = None) -> None:
        """Plays an :class:`AudioSource`.

        The finalizer, ``after`` is called after the source has been exhausted
        or an error occurred.

        If an error happens while the audio player is running, the exception is
        caught and the audio player is then stopped.  If no after callback is
        passed, any caught exception will be logged using the library logger.

        .. versionchanged:: 2.0
            Instead of writing to ``sys.stderr``, the library's logger is used.

        Parameters
        -----------
        source: :class:`AudioSource`
            The audio source we're reading from.
        after: Callable[[Optional[:class:`Exception`]], Any]
            The finalizer that is called after the stream is exhausted.
            This function must have a single parameter, ``error``, that
            denotes an optional exception that was raised during playing.

        Raises
        -------
        ClientException
            Already playing audio or not connected.
        TypeError
            Source is not a :class:`AudioSource` or after is not a callable.
        OpusNotLoaded
            Source is not opus encoded and opus is not loaded.
        """

        if not self.is_connected():
            raise ClientException('Not connected to voice.')

        if self.is_playing():
            raise ClientException('Already playing audio.')

        if not isinstance(source, AudioSource):
            raise TypeError(f'source must be an AudioSource not {source.__class__.__name__}')

        if not self.encoder and not source.is_opus():
            self.encoder = opus.Encoder()

        self._player = BodgedAudioPlayer(source, self, after=after)
        self._player.start()
        
class VoiceRecvClient(BodgedVoiceClient):
    def __init__(self, client, channel):
        super().__init__(client, channel)

        self._connecting = threading.Condition()
        self._reader = None
        self._ssrc_to_id = {}
        self._id_to_ssrc = {}

    async def connect_websocket(self):
        ws = await DiscordVoiceWebSocket.from_client(self, hook=hook)
        self._connected.clear()
        while ws.secret_key is None:
            await ws.poll_event()
        self._connected.set()
        return ws

    async def on_voice_state_update(self, data):
        await super().on_voice_state_update(data)

        channel_id = data['channel_id']
        guild_id = int(data['guild_id'])
        user_id = int(data['user_id'])

        if channel_id and int(channel_id) != self.channel.id and self._reader:
            # someone moved channels
            if self._connection.user.id == user_id:
                # we moved channels
                # print("Resetting all decoders")
                self._reader._reset_decoders()

            # TODO: figure out how to check if either old/new channel
            #       is ours so we don't go around resetting decoders
            #       for irrelevant channel moving

            else:
                # someone else moved channels
                # print(f"ws: Attempting to reset decoder for {user_id}")
                ssrc, _ = self._get_ssrc_mapping(user_id=data['user_id'])
                self._reader._reset_decoders(ssrc)

    # async def on_voice_server_update(self, data):
    #     await super().on_voice_server_update(data)
    #     ...


    def cleanup(self):
        super().cleanup()
        self.stop()
    
    # TODO: copy over new functions
    # add/remove/get ssrc

    def _add_ssrc(self, user_id, ssrc):
        self._ssrc_to_id[ssrc] = user_id
        self._id_to_ssrc[user_id] = ssrc

    def _remove_ssrc(self, *, user_id):
        ssrc = self._id_to_ssrc.pop(user_id, None)
        if ssrc:
            self._ssrc_to_id.pop(ssrc, None)

    def _get_ssrc_mapping(self, *, ssrc):
        uid = self._ssrc_to_id.get(ssrc)
        return ssrc, uid

    def listen(self, sink):
        """Receives audio into a :class:`AudioSink`. TODO: wording"""

        if not self.is_connected():
            raise ClientException('Not connected to voice.')

        if not isinstance(sink, AudioSink):
            raise TypeError('sink must be an AudioSink not {0.__class__.__name__}'.format(sink))

        if self.is_listening():
            raise ClientException('Already receiving audio.')

        self._reader = AudioReader(sink, self)
        self._reader.start()

    def is_listening(self):
        """Indicates if we're currently receiving audio."""
        return self._reader is not None and self._reader.is_listening()

    def stop_listening(self):
        """Stops receiving audio."""
        if self._reader:
            self._reader.stop()
            self._reader = None

    def stop_playing(self):
        """Stops playing audio."""
        if self._player:
            self._player.stop()
            self._player = None

    @property
    def sink(self):
        return self._reader.sink if self._reader else None

    @sink.setter
    def sink(self, value):
        if not isinstance(value, AudioSink):
            raise TypeError('expected AudioSink not {0.__class__.__name__}.'.format(value))

        if self._reader is None:
            raise ValueError('Not receiving anything.')

        self._reader._set_sink(sink)
