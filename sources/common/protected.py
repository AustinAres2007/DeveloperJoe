
from __future__ import annotations
import ast
import importlib
import os
from typing import TYPE_CHECKING, Any, Callable, Protocol, Type, TypeVar
import inspect

import discord

from .. import (
    permissionshandler
)

if TYPE_CHECKING:
    from joe import DeveloperJoe
    
T = TypeVar('T', covariant=True)

class ProtectedClassType:
    bot: DeveloperJoe
    user: discord.Member
    name: str
    description: str

class ProtectedClass:
    
    name = "ProtectedClass"
    description = "Description"
    
    def __init__(self, instance: ProtectedClass) -> None:
        instance_module = inspect.getmodule(instance)
        
        if instance_module == None:
            raise NameError("Cannot trace ProtectedClass module.")
        
        if not hasattr(instance, "user"):
            raise TypeError("__class must conform to ProtectedClassType.")
        
        self.user: discord.Member = instance.user
        self.bot: DeveloperJoe = instance.bot
        self.instance = instance
        
        roles = self.bot._protected_classes_handler.get_class_authorised_roles(instance)
        member_senior_role = self.user.top_role  
        
        print(roles and member_senior_role >= self.user.guild.get_role(roles[0]))
        if (roles and member_senior_role >= self.user.guild.get_role(roles[0])) == False:
            print("rai")
            raise ValueError("User does not have authority to create class instance.")

class ClassCollector(ast.NodeVisitor):
    def __init__(self):
        super().__init__()
        self.classes = []

    def visit_ClassDef(self, node):
        self.classes.append(node)
        
class ProtectedClassHandler:
    
    def __init__(self, directory_to_search: str="sources"):
        """This class handles all ProtectedClass'es

        Args:
            directory_to_search (_type_): The specified directory where directories and files will be recursivly scanned for ProtectedClass'es
        """
        self.protected_classes: dict[str, ProtectedClass] = {}
        self._protected_classes_map: dict[str, ProtectedClass] = {}
        self.directory = directory_to_search
        
        protected_classes = self._scan_for_protected_class_signature()
        
        for _cls in protected_classes:
            self.add_class(_cls)
        
        print(self.protected_classes)
        
    def _scan_file_for_class_signature(self, filepath: str) -> list[ast.ClassDef]:
        with open(filepath, 'r', encoding='utf-8') as python_file:
            content = python_file.read()
            syntax_tree = ast.parse(content)
            
            collector = ClassCollector()
            collector.visit(syntax_tree)
            
        return collector.classes
    
    def _import_protected_class_from_module(self, module_name: str, _class: str) -> None | Any:
        module = importlib.import_module(module_name, package=".")
        _cls = getattr(module, _class)
        
        if issubclass(_cls, ProtectedClass) and _cls != ProtectedClass:
            return _cls
    
    def _scan_for_protected_class_signature(self) -> list[ProtectedClass]: # Dont know atm
        protected_classes: list[ProtectedClass] = []
        
        for folder, subfolders, filenames in os.walk(self.directory):
            if not set("__pycache__").issuperset(set(subfolders)) == True:
                for _file in filenames: 
                    if _file.endswith(".py"):
                        file_classdef = self._scan_file_for_class_signature(os.path.join(folder, _file))
                        module_path = f"{folder.replace("/", ".")}.{_file[:-3]}"
                        
                        for class_name in file_classdef:
                            _cls = self._import_protected_class_from_module(module_path, class_name.name)
                            if _cls: protected_classes.append(_cls)
        
        return protected_classes
    
    def add_class(self, class_instance: ProtectedClass):
        
        
        _cls_id = self.get_id_for_class(class_instance)
        
        if _cls_id == None:
            raise ValueError("Given class does not inherit from ProtectedClass")
            
        if class_instance.name not in self.protected_classes and _cls_id not in self.protected_classes:
            
            self.protected_classes[_cls_id] = class_instance
            self._protected_classes_map[class_instance.name] = class_instance
            
        else:
            
            instance = self.protected_classes.get(class_instance.name) or self.protected_classes.get(_cls_id)
            
            if self.protected_classes.get(class_instance.name, False):
                raise KeyError(f'''
                    An instance with the specified name: "{class_instance.name}" already exists within the class handler. 
                    {f"And {class_instance} is the same as the instance in the class handler. Which means the instance you are trying to add already exists." if class_instance == instance else ""}''')
            else:
                raise KeyError(f'''
                    An instance with the specified id: "{_cls_id}" already exists within the class handler. 
                    {f"And {class_instance} is the same as the instance in the class handler. Which means the instance you are trying to add already exists." if class_instance == instance else ""}''')
                
    def get_class(self, name_or_id: str):
        return self.protected_classes.get(name_or_id)
    
    def get_id_for_class(self, class_instance: ProtectedClass) -> str | None:
        class_parent_module = inspect.getmodule(class_instance)
        if class_parent_module:            
            class_name = str(class_instance.__name__ if hasattr(class_instance, "__name__") else class_instance.__class__.__name__).lower() # type: ignore accounted for
            return f"{class_parent_module.__name__}.{class_name}"
        
    def get_class_authorised_roles(self, class_instance: ProtectedClass) -> list[int] | None:
        # ID format (relative to joe.py) Example for this class: sources.common.protected.protectedclasshandler
        class_id = self.get_id_for_class(class_instance)
        
        if class_id:
            return permissionshandler.get_guild_object_permissions(class_instance.user.guild, class_id)

# TODO: make decorator that can work bound variable (For normal local functions)
def protected_method(func: Callable):
    
    def _protected_wrapper(self: ProtectedClass, *args, **kwargs):
        if hasattr(self, "__class__") and issubclass(self.__class__, ProtectedClass):
            _cls_id = self.bot._protected_classes_handler.get_id_for_class(self)            
            if _cls_id:
                guild_roles = permissionshandler.get_guild_object_permissions(self.user.guild, _cls_id)
                if self.user.roles[-1] >= guild_roles[0]:
                    return func(self, *args, **kwargs)
                else:
                    raise PermissionError("{} does not have suffient permissions.".format(self.user))
            else:
                return func(self, *args, **kwargs)    
        else:
            raise TypeError("Given function must be bound to a class instance.")    
    
    return _protected_wrapper
