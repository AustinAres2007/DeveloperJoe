import inspect
import typing, discord

from . import (
    exceptions,
    permissionshandler
)
from .common import (
    types
)

class ProtectedClassWrapper:
    def __init__(self, member: discord.Member, *args, **kwargs):
        ...
    
    @classmethod
    def get_protected_name(cls) -> str:
        """This is where the user-readable name of the class is stored. By default it is the class name, but please override this to something more readable.

        Returns:
            str: _description_
        """
        raise NotImplementedError
    
    @classmethod
    def get_protected_description(cls) -> str:
        """Here is where the end user will see the description of the class. By default it is the docstring (if it exists), but please override this to something more readable.

        Returns:
            str: _description_
        """
        raise NotImplementedError
    
    @classmethod
    def get_error_message(cls) -> str:
        """This is the string that will be send to the user if the user does not have the required permissions to use the command / an aspect of the command.
        
        Returns:
            str: _description_
        """
        raise NotImplementedError
    
class ProtectedClassHandler:
    def __init__(self) -> None:
        self.__protected_dict__: dict[str, typing.Type[ProtectedClassWrapper]] = {}
    
    @staticmethod
    def get_class_id(instance: typing.Type[ProtectedClassWrapper]) -> str:
        class_parent_module = inspect.getmodule(instance)
        if class_parent_module:
            if hasattr(instance, "__name__"):
                class_name = instance.__name__
                return f"{class_parent_module.__name__}.{class_name}".lower()
            raise AttributeError("Class name is not defined. This usually happens because an class instance was passed, not a class definition.")
        else:
            raise Exception("Class parent module is not defined")
        
    def add_class(self, instance: typing.Type[ProtectedClassWrapper]) -> str:
        try:
            parent_instance = instance.__base__
            instance_id = self.get_class_id(parent_instance)
            
            if instance in self.classes.values():
                raise AttributeError("instance already exists.")

            self.__protected_dict__[instance_id] = instance
            return instance_id
           
        except IndexError:
            raise TypeError("instance must be a class that derives from types.HasMember")
    
    def has_class(self, id: str) -> bool:
        return id in self.classes.keys()
    
    def get_class(self, id: str) -> typing.Type[types.HasMember]:
        ...

    @property
    def classes(self) -> dict[str, typing.Type[ProtectedClassWrapper]]:
        return self.__protected_dict__
    
protected_class_handler: ProtectedClassHandler | None = None

def protect_class(passed_cls):
    class ProtectedClassDecoratorWrapper(passed_cls):

        def __init__(self, member: discord.Member, *args, **kwargs):
            if not isinstance(member, discord.Member):
                raise TypeError(f"member should be discord.Member, not {member.__class__.__name__}")
            
            if not isinstance(protected_class_handler, ProtectedClassHandler):
                raise TypeError("Protected class handler is not set.")
            
            self.protected_class_handler = protected_class_handler
            self.member = member
            
            roles = permissionshandler.get_guild_object_permissions(member.guild, ProtectedClassHandler.get_class_id(passed_cls))
            if roles:
                role_id = roles[0]
                role = member.guild.get_role(role_id)
                
                if role:
                    if not self.member.top_role >= role:
                        raise exceptions.DGException(self.get_error_message(role))
                else:
                    raise exceptions.DGException("""
                        The specified role that the command requires to work no longer exists. Please contact the server owner to fix this issue.
                        (For resolution, admin only: do the command /permissions remove {})
                    """.format(role_id))
                
            super().__init__(member, *args, **kwargs)

        @classmethod
        def get_protected_name(cls) -> str:
            """This is where the user-readable name of the class is stored. By default it is the class name, but please override this to something more readable.

            Returns:
                str: _description_
            """
            try:
                return passed_cls.get_protected_name() if hasattr(passed_cls, "get_protected_name") else passed_cls.__name__
            except TypeError:
                raise exceptions.DGException("Error with `{0}` permission: `{0}.get_protected_name()` must be a classmethod. Or, the function must be deleted.".format(passed_cls.__name__))
            
        @classmethod
        def get_protected_description(cls) -> str:
            """Here is where the end user will see the description of the class. By default it is the docstring (if it exists), but please override this to something more readable.

            Returns:
                str: _description_
            """
            try:
                return passed_cls.get_protected_description() if hasattr(passed_cls, "get_protected_description") else "No description provided."
            except TypeError:
                raise exceptions.DGException("Error with `{0}` permission: `{0}.get_protected_description()` must be a classmethod. Or, the function must be deleted.".format(passed_cls.__name__))

        @classmethod
        def get_error_message(cls, role: discord.Role) -> str:
            try:
                return passed_cls.get_error_message(role) if hasattr(passed_cls, "get_error_message") else f"You do not have the required role to use this command or an aspect of this command. You need the role **{role.name}** or higher."
            except TypeError:
                raise exceptions.DGException("Error with `{0}` permission: `{0}.get_error_message()` must be a classmethod. Or, the function must be deleted.".format(passed_cls.__name__))
            
    if protected_class_handler:
        protected_class_handler.add_class(ProtectedClassDecoratorWrapper)
    else:
        raise RuntimeError("Protected class handler is not set.")
    
    return ProtectedClassDecoratorWrapper