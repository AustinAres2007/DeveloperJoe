

from typing import Generic, Protocol, TypeVar

import discord

from .. import (
    permissionshandler
)

T = TypeVar('T')

class ProtectedClassType(Protocol):
    user: discord.Member
    
class ProtectedClass(Generic[T]):
    
    def __init__(self, instance: ProtectedClassType, permission_key: str) -> None:
        self.permission_key = permission_key
        
        user = instance.user
        roles = permissionshandler.get_guild_object_permissions(user.guild, self.permission_key)
        member_senior_role = user.roles[-1]  
            
        if not hasattr(instance, "user"):
            raise TypeError("__class must conform to ProtectedClassType.")
        
        if not ((roles and member_senior_role >= user.guild.get_role(roles[0])) or not roles):
            raise ValueError("User does not have authority to create class instance.")
