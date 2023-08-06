import tiktoken as _tiktoken
from typing import Union as _Union, Type as _Type

class GPTModel:

    _model: str = ""
    _display_name: str = ""
    _description: str = ""
    
    @classmethod
    @property
    def model(cls) -> str:
        """Returns the actual model name that is used to send communication requests."""
        return cls._model
    
    @classmethod
    @property
    def tokeniser(cls) -> _tiktoken.Encoding:
        """The encoding used to calculate the amount of tokens used."""
        return _tiktoken.encoding_for_model(cls.model)
    
    @classmethod
    @property
    def description(cls) -> str:
        """The description for the model."""
        return cls._description
    
    @classmethod
    @property
    def display_name(cls) -> str:
        """User-readable display name for the model."""
        return cls._display_name
    
    @classmethod
    def __repr__(cls):
        # repr and str don't work because of @classmethod.
        return f"<{cls.__name__} display_name={cls.display_name}, model={cls.model}>"
    
    @classmethod
    def __str__(cls) -> str:
        return cls._model
    
class GPT3Davinci(GPTModel):
    """OpenAI Davinci (Based on GPT 3)"""
    
    _model: str = "text-davinci-003"
    _display_name: str = "Davinci"
    _description: str = "Good at language tasks with good enough quality. GPT 3 Turbo is recommended instead."
    
    @classmethod
    def __eq__(cls, __value: GPTModel) -> bool:
        return cls.model == __value.model
    
class GPT3Turbo(GPTModel):
    """Generative Pre-Trained Transformer 3.5 Turbo (gpt-3.5-turbo)"""

    _model: str = "gpt-3.5-turbo"
    _display_name: str = "GPT 3.5 Turbo"
    _description: str = "Good for generating text and general usage. Cost-effective."

    @classmethod
    def __eq__(cls, __value: GPTModel) -> bool:
        return cls.model == __value.model
    
class GPT4(GPTModel):
    """Generative Pre-Trained Transformer 4 (gpt-4)"""

    _model: str = "gpt-4"
    _display_name: str = "GPT 4"
    _description: str = "Better than GPT 3 Turbo at everything. Would stay with GPT 3 for most purposes-- Can get expensive."
    
    @classmethod
    def __eq__(cls, __value: GPTModel) -> bool:
        return cls.model == __value.model

GPTModelType = _Type[_Union[GPT3Davinci, GPT3Turbo, GPT4]]