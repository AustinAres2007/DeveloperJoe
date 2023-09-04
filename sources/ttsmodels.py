import io as _io, gtts as _gtts, json as _json
from .common.developerconfig import FFMPEG, FFPROBE
from .voice import pydub as _pydub # type: ignore Again, Python is being dumb. The dependency does exist.

"""I want to put more TTS models here, but using one that is not system dependent and has a package for python is difficult."""

__all__ = [
    "TTSModel",
    "GTTSModel"
]

class TTSModel:
    """Base class for generating text-to-speach for discord.py"""
    
    def __init__(self, text: str) -> None:
        """Base class for generating text-to-speach for discord.py

        Args:
            text (str): The text to be translated to voice.
        """
        self._text = text
        self._emulated_file_object: _io.BytesIO = _io.BytesIO()
        
    @property
    def text(self) -> str:
        """The text to be translated to voice.

        Returns:
            str: The text to be translated to voice.
        """
        return self._text
    
    @property
    def emulated_file_object(self) -> _io.BytesIO:
        """The emulated file object. (Path-like)

        Returns:
            _io.BytesIO: The emulated file object. (Path-like)
        """
        return self._emulated_file_object

    def process_text(self, speed: float) -> _io.BytesIO:
        """This must translate the text to a `io.BytesIO` object.

        Args:
            speed (float): The speed at which the bot will talk.

        Returns:
            _io.BytesIO: The spoken response.
        """
        raise NotImplementedError

class GTTSModel(TTSModel):
    """Google Text-to-Speach model."""
    def process_text(self, speed: float) -> _io.BytesIO:
        """Processes text into the Google TTS voice.

        Args:
            speed (float): The speed at which the bot will talk

        Returns:
            _io.BytesIO: The spoken response.
        """
        
        _temp_file = _io.BytesIO()
        _gtts.gTTS(self.text).write_to_fp(_temp_file)
        _temp_file.seek(0)
        
        try:
            speed_up = _pydub.AudioSegment.from_file(_temp_file)
        except _json.decoder.JSONDecodeError: # pydub may not work sometimes depending on ffmpeg / ffprobe version, return non-speedup file instead
            return self.emulated_file_object
        else:
            return speed_up.speedup(playback_speed=speed).export(self.emulated_file_object)
        
        