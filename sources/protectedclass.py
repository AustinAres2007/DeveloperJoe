import inspect
import typing, discord

from . import (
    exceptions
)
from .common import (
    types
)

class ProtectedClassHandler:
    def __init__(self) -> None:
        self.__protected_dict__ = {}
    
    def get_class_id(self, instance: typing.Type[types.HasMember]) -> str:
        class_parent_module = inspect.getmodule(instance)
        if class_parent_module:
            class_name = str(getattr(instance, "__name__") if hasattr(instance, "__name__") else instance.__class__.__name__)
            return f"{class_parent_module.__name__}.{class_name}".lower()
        else:
            raise Exception("Class parent module is not defined")
        
    def add_class(self, instance: typing.Type[types.HasMember]) -> str:
        try:
            instance_id = self.get_class_id(instance)
            
            if instance in self.__protected_dict__.values():
                raise AttributeError("instance already exists.")
    
            self.__protected_dict__[instance_id] = instance
            return instance_id
           
        except IndexError:
            raise TypeError("instance must be a class that derives from types.HasMember")
    
    def has_class(self, id: str) -> bool:
        return id in self.__protected_dict__.keys()
    
    def get_class(self, id: str) -> typing.Type[types.HasMember]:
        ...

protected_class_handler: ProtectedClassHandler | None = None

def protect_class(cls):
    class ProtectedClassWrapper(cls):

        def __init__(self, member: discord.Member, *args, **kwargs):
            if not isinstance(member, discord.Member):
                raise TypeError(f"member should be discord.Member, not {member.__class__.__name__}")
            
            if not isinstance(protected_class_handler, ProtectedClassHandler):
                raise Exception("Protected class handler is not set.")
            
            self.protected_class_handler = protected_class_handler
            self.member = member
            
            role_id = 0 # Not set as I need to finish the backend for this.
            role = member.guild.get_role(role_id)
            
            if role:
                if not self.member.top_role >= role:
                    raise Exception("Missing permissions")
            else:
                raise exceptions.DGException("""
                    The specified role that the command requires to work no longer exists. Please contact the server owner to fix this issue.
                    (For resolution, admin only: do the command /removepermission {})
                """.format(role_id))
                
            super().__init__(member, *args, **kwargs)

    if protected_class_handler:
        protected_class_handler.add_class(cls)
    else:
        raise RuntimeError("Protected class handler is not set.")
    
    print(protected_class_handler.__protected_dict__)
    return ProtectedClassWrapper