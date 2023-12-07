

from typing import Callable, Generic, Protocol, TypeVar

import discord

from .. import (
    permissionshandler
)
from . import (
    common
)

T = TypeVar('T')
get_permission_function_key = lambda class_name, function_name: f"{common.get_filename(__file__)}.{class_name}.{function_name}"
class ProtectedClassType(Protocol):
    user: discord.Member
    name: str
    description: str
    
class ProtectedClass(Generic[T]):
    
    name = "Voice Chat"
    description = "test"
    
    def __init__(self, instance: ProtectedClassType) -> None:
        self._permission_key = "permission_key"
        self.user = instance.user
        roles = permissionshandler.get_guild_object_permissions(self.user.guild, self._permission_key)
        member_senior_role = self.user.roles[-1]  
            
        if not hasattr(instance, "user"):
            raise TypeError("__class must conform to ProtectedClassType.")
        
        if not ((roles and member_senior_role >= self.user.guild.get_role(roles[0])) or not roles):
            raise ValueError("User does not have authority to create class instance.")
    
def protected_method(func: Callable):
    
    def _protected_wrapper(self: ProtectedClass, *args, **kwargs):
        if hasattr(self, "__class__") and issubclass(self.__class__, ProtectedClass):
            print(get_permission_function_key(self.__class__.__name__, func.__name__))
            if guild_roles := permissionshandler.get_guild_object_permissions(self.user.guild, get_permission_function_key(self.__class__.__name__, func.__name__)):
                if self.user.roles[-1] >= guild_roles[0]:
                    return func(self, *args, **kwargs)
                else:
                    raise PermissionError("{} does not have suffient permissions.".format(self.user))
            else:
                return func(self, *args, **kwargs)    
        else:
            raise TypeError("Given function must be bound to a class instance.")    
    
    return _protected_wrapper
