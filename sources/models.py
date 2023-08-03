import tiktoken as _tiktoken
from typing import Union as _Union, Type as _Type

class GPTModel:

    _model: str = ""
    _display_name: str = ""
    _description: str = ""
    _tokeniser: _tiktoken.Encoding = _tiktoken.encoding_for_model(_model)

    @property
    @classmethod
    def model(cls) -> str:
        """Returns the actual model name that is used to send communication requests."""
        return cls._model
    
    @property
    @classmethod
    def tokeniser(cls) -> _tiktoken.Encoding:
        """The encoding used to calculate the amount of tokens used."""
        return cls._tokeniser
    
    @property
    @classmethod
    def description(cls) -> str:
        """The description for the model."""
        return cls._description
    
    @property
    @classmethod
    def display_name(cls) -> str:
        """User-readable display name for the model."""
        return cls._display_name
    
    @classmethod
    def __str__(cls) -> str:
        return f"<{cls.__name__} display_name={cls.display_name}, model={cls.model}>"
    
class GPT3Turbo(GPTModel):
    """Generative Pre-Trained Transformer 3 Turbo (gpt-3.5-turbo)"""

    _model: str = "gpt-3.5-turbo"
    _display_name: str = "GPT 3.5 Turbo"
    _description: str = "Good for generating text and general usage. Cost-effective."
    _tokeniser: _tiktoken.Encoding = _tiktoken.encoding_for_model(_model)

    @classmethod
    def __eq__(cls, __value: GPTModel) -> bool:
        return cls.model == __value.model
    
class GPT4(GPTModel):
    """Generative Pre-Trained Transformer 4 (gpt-4)"""

    _model: str = "gpt-4"
    _display_name: str = "GPT 4"
    _description: str = "Better than GPT 3 Turbo at everything. Would stay with GPT 3 for most purposes-- Can get expensive."
    _tokeniser: _tiktoken.Encoding = _tiktoken.encoding_for_model(_model)
    
    @classmethod
    def __eq__(cls, __value: GPTModel) -> bool:
        return cls.model == __value.model

GPTModelType = _Type[_Union[GPT3Turbo, GPT4]]