import io as _io, gtts as _gtts
from . import exceptions

global has_coqui

try:
    from TTS.api import TTS
    from dgsetup import installcoqui
    import wave, array
except ModuleNotFoundError:
    print("Coqui not installed. Ignoring..")
    has_coqui = False
else:
    print("Coqui installed. (Imported)")
    has_coqui = True
    
"""I want to put more TTS models here, but using one that is not system dependent and has a package for python is difficult."""

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

    def process_text(self) -> _io.BytesIO:
        """This must translate the text to a `io.BytesIO` object.

        Returns:
            _io.BytesIO: The emulated MP3 file.
        """
        ...

class GTTSModel(TTSModel):
    """Google Text-to-Speach model."""
    def process_text(self) -> _io.BytesIO:
        """Processes test into the Google TTS voice.

        Returns:
            _io.BytesIO: The emulated MP3 file.
        """
        _gtts.gTTS(self.text).write_to_fp(self.emulated_file_object)
        self.emulated_file_object.seek(0)
        return self.emulated_file_object

class CoquiTTSModel(TTSModel):
    """Coqui Text-to-Speach model."""
    def process_text(self) -> _io.BytesIO:
        if has_coqui:
            m = TTS(installcoqui.COQUI_TTS_MODELS[0], progress_bar=False)
            r = m.tts(text=self.text, speed=1.5)
        
            if m.synthesizer:
                with wave.Wave_write(self.emulated_file_object) as wv:
                    wv.setparams((1, 2, int(m.synthesizer.output_sample_rate), 0, "NONE", "not compressed"))
                    wv.writeframes(array.array('h', (int(sin * 32767) for sin in r if sin != 0)))
                self.emulated_file_object.seek(0)
            
            return self.emulated_file_object
        
        raise exceptions.CoquiNotInstalled()
        
        
        
