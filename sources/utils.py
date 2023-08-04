"""General Utilities that DG Uses."""

import io as _io
from discord import File as _File
from . import config as _config, models as _models, exceptions as _exceptions

def to_file(content: str, name: str) -> _File:
        """From `str` to `discord.File`"""
        f = _io.BytesIO(content.encode())
        f.name = name
        return _File(f)

def get_modeltype_from_name(name: str) -> _models.GPTModelType:
        """Get GPT Model from actual model name. (Get `models.GPT4` from entering `gpt-4`)"""
        if name in list(_config.REGISTERED_MODELS):
            return _config.REGISTERED_MODELS[name]
        raise _exceptions.ModelNotExist(None, name)

def assure_class_is_value(object, __type: type):
    """For internal use. Exact same as `isinstance` but raises `IncorrectInteractionSetting` if the result is `False`."""
    if type(object) == __type:
        return object
    raise _exceptions.IncorrectInteractionSetting(object, type)