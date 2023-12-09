
# Make a type annotation that represents an input of any generic class
from typing import Protocol, Type, TypeVar

T = TypeVar('T')

def class_decorator(cls: Type[T]) -> Type[T]:
    # This is a decorator that takes a class as an argument and returns a class
    
    class CLSDecorator(cls):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

    return CLSDecorator

# This is a class that is decorated by the decorator above
@class_decorator
class ExampleClass:
    def __init__(self, value: int):
        self.x = value

# This is a test to see if the decorator works
test = ExampleClass(5)
print(test.x)
