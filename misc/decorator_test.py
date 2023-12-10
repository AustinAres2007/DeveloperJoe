
# Make a type annotation that represents an input of any generic class
from typing import Any, Protocol, Type, TypeVar

T = TypeVar('T')

# Make a generic type annotion that species that any class must have a member called "member"
class MemberDemo:
    def __init__(self, member: int, role: int):
        self.member = member
        self.role = role

class HasMember(Protocol):
    member: MemberDemo

def emulated_database_connection() -> int:
    # This is a function that emulates a database connection
    return 10 # Emulate a role ID

def class_decorator(cls: Type[HasMember]) -> Any:
    # This is a decorator that takes a class as an argument and returns a class
    
    class CLSDecorator(cls):
        def __init__(self, member: MemberDemo, *args, **kwargs):
            self.member = member
            
            if self.member.role < emulated_database_connection():
                print("You do not have the right role to use this command")
            else:
                print("You have the right role to use this command")
                
            super().__init__(member, *args, **kwargs) # TODO: Fix __init__ positional argument error with type annotation

    return CLSDecorator

# This is a class that is decorated by the decorator above
@class_decorator
class ExampleClass:
    def __init__(self, member: MemberDemo, value: int):
        self.member = member
        self.x = value

# This class contains function for testing purposes. (Static methods)

class TestCommands:
    
    @classmethod
    def mkin(cls, member: MemberDemo) -> None:
        test_decorator_class = ExampleClass(member, 10)
    
    @classmethod
    def chusrr(cls, member: MemberDemo) -> None:
        member.role = int(input("New user ID -> "))
        
user_id = int(input("Identify yourself (ID, Int) -> "))
role_id = int(input("Identify your role (ID, Int) -> "))

member_instance = MemberDemo(user_id, role_id)

while True:
    command = input("Enter a command -> ")
    cmd = getattr(TestCommands, command, lambda *any: print("Command not found"))(member_instance)