from ast import ParamSpec
import inspect
from os import error
import typing, discord

from . import (
    exceptions,
    permissionshandler
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

class ProtectedFunctionWrapper:
        
    @classmethod
    def function(cls) -> typing.Type[typing.Self]:
        raise NotImplementedError
    
    @classmethod
    def get_protected_name(cls) -> str:
        raise NotImplementedError
    
    @classmethod
    def get_protected_description(cls) -> str:
        raise NotImplementedError
    
    @classmethod
    def get_error_message(cls, _role: discord.Role) -> str:
        raise NotImplementedError
    
ProtectedObject = typing.Type[ProtectedClassWrapper] | typing.Type[ProtectedFunctionWrapper]
ProtectedFunctionCompatible = typing.Callable[typing.Concatenate[..., discord.Member, ...], typing.Any] | typing.Callable[typing.Concatenate[discord.Member, ...], typing.Any]

class ProtectedClassHandler:
    def __init__(self) -> None:
        self.__protected_dict__: dict[str, ProtectedObject] = {}
    
    @staticmethod
    def get_class_id(instance: typing.Any) -> str:
        """Gets the protected ID of any given object definition.

        Args:
            instance (typing.Any): Either a class definition or a function definition.

        Raises:
            AttributeError: An instance was passed, not a definition.
            Exception: The class parent module is not defined.

        Returns:
            str: The protected ID of the object.
        """
        
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
    
    def add_function(self, function_wrapper: typing.Type[ProtectedFunctionWrapper]) -> str:
        try:
            instance_id = self.get_class_id(function_wrapper.function)
            
            if function_wrapper in self.classes.values():
                raise AttributeError("function already exists.")

            self.__protected_dict__[instance_id] = function_wrapper
            return instance_id
        except IndexError:
            raise TypeError("function must be a function that takes a discord.Member as its first argument.")
        
    def has_class(self, id: str) -> bool:
        return id in self.classes.keys()

    @property
    def classes(self) -> dict[str, ProtectedObject]:
        return self.__protected_dict__
    
protected_class_handler: ProtectedClassHandler | None = None

def protect_function(protected_name: str, protected_description: str, error_message: str):
    """Protects a function from being used by a user without the required permissions.

    Args:
        protected_name (str): The name of the permission.
        protected_description (str): The description of the permission.
        error_message (str): The error message to send to the user if they do not have the required permissions.
    """
    
    def _is_bound(func: ProtectedFunctionCompatible) -> bool:
        
        # Get first parameter and check if it is named `self` if so, return True.
        func_params = inspect.signature(func).parameters
        if len(func_params) > 0:
            first_param = list(func_params.values())[0]
            if first_param.name == "self":
                return True
            
        return False 
    
    def _protect_wrapper(function, member: discord.Member, *args, **kwargs):
        
        if not isinstance(member, discord.Member):
            raise TypeError(f"member should be discord.Member, not {member.__class__.__name__}")
        
        if not isinstance(protected_class_handler, ProtectedClassHandler):
            raise TypeError("Protected class handler is not set.")
        
        cls_id = ProtectedClassHandler.get_class_id(function)
        roles = permissionshandler.get_guild_object_permissions(member.guild, cls_id)
        
        if roles:
            role_id = roles[0]
            role = member.guild.get_role(role_id)
            
            if role:
                if not member.top_role >= role:
                    raise exceptions.DGException(error_message)
            else:
                raise exceptions.DGException("""
                    The specified role that the command requires to work no longer exists. Please contact the server owner to fix this issue.
                    (For resolution, admin only: do the command `/permissions remove {}`)
                """.format(cls_id))
        
        return function(member, *args, **kwargs)
    
    def _initial(func: ProtectedFunctionCompatible):
        
        def _inner_Wrapper(*args, **kwargs):
            return _protect_wrapper(func, *args, **kwargs)
        
        class ProtectedFunctionDecoratorWrapper(ProtectedFunctionWrapper):
            
            function: ProtectedFunctionCompatible = func 
            
            @classmethod
            def get_protected_name(cls) -> str:
                return protected_name
            
            @classmethod
            def get_protected_description(cls) -> str:
                return protected_description
            
            @classmethod
            def get_error_message(cls, _role: discord.Role) -> str:
                return error_message
        
        if protected_class_handler:
            
            member_arg_at = 0 if not _is_bound(func) else 1
            first_positional_argument = list(inspect.signature(func).parameters.values())[member_arg_at]
        
            if first_positional_argument.name != "member":
                raise TypeError(f'{func.__name__} first positional argument must be called member and be of type discord.Member. Not called {first_positional_argument.name}')
            
            protected_class_handler.add_function(ProtectedFunctionDecoratorWrapper)
            
        return _inner_Wrapper

    return _initial
        
def protect_class(passed_cls):
    class ProtectedClassDecoratorWrapper(passed_cls):

        def __init__(self, member: discord.Member, *args, **kwargs):
            if not isinstance(member, discord.Member):
                raise TypeError(f"member should be discord.Member, not {member.__class__.__name__}")
            
            if not isinstance(protected_class_handler, ProtectedClassHandler):
                raise TypeError("Protected class handler is not set.")
            
            self.protected_class_handler = protected_class_handler
            self.member = member
            
            cls_id = ProtectedClassHandler.get_class_id(passed_cls)
            roles = permissionshandler.get_guild_object_permissions(member.guild, cls_id)
            
            if roles:
                role_id = roles[0]
                role = member.guild.get_role(role_id)
                
                if role:
                    if not self.member.top_role >= role:
                        raise exceptions.DGException(self.get_error_message(role))
                else:
                    raise exceptions.DGException("""
                        The specified role that the command requires to work no longer exists. Please contact the server owner to fix this issue.
                        (For resolution, admin only: do the command `/permissions remove {}`)
                    """.format(cls_id))
                
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
        # Get first argument of __init__ and check if it is a discord.Member and named member. If not, raise TypeError.
        
        first_positional_argument = list(inspect.signature(passed_cls.__init__).parameters.values())[1]
        if first_positional_argument.name != "member":
            raise TypeError(f'{passed_cls.__name__} first positional argument (Excluding self) must be called member and be of type discord.Member')
        
        protected_class_handler.add_class(ProtectedClassDecoratorWrapper)
    else:
        raise RuntimeError("Protected class handler is not set.")
    
    return ProtectedClassDecoratorWrapper