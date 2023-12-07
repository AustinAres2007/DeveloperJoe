import inspect
    
# Emulate server side response

server = {
    1: {
        "gpt-3": [2]
    }
}
# This is what checks protected values agaisnt their class
def ProtectCheck(func):
    def _wrapper(user: Member, *args, **kwargs):
        
        # Arguments passed MUST be keywords.
        func_args = dict(inspect.signature(func).parameters)
        
        for arg_name, arg_type in func_args.items():
            if issubclass(arg_type.annotation, ProtectedFeature):
                if issubclass(kwargs.get(arg_name, None).__class__, ProtectedFeature):
                    if user.role_id >= server[user.server_id][kwargs.get(arg_name, None).feature_name][-1]:
                        return func(user, *args, **kwargs)
                    raise TypeError("You do not have the permissions for this.")
                raise TypeError("You must use a protected version of this type")
            else:
                if issubclass(kwargs.get(arg_name, None).__class__, ProtectedFeature):
                    kwargs[arg_name] = kwargs.get(arg_name, "").original
                    
        return func(user, *args, **kwargs)
            
    return _wrapper

# Normal Classes

class Member:
    def __init__(self) -> None:
        self.role_id = 2
        self.server_id = 1

class Model:
    def __init__(self) -> None:
        self.speed = 1

class GPT35(Model):
    ...
    
# Protected Classes

class ProtectedFeature:
    def __init__(self, name: str, __class) -> None:
        self.original = __class
        self.feature_name = name

class ProtectedModel(ProtectedFeature):
    def __init__(self, name: str, __class) -> None:
        super().__init__(name, __class)
        if not isinstance(__class, Model):
            raise ValueError("A type of Model was expected, {} was provided.".format(type(__class)))
    
@ProtectCheck
def elite_func(user: Member, model: ProtectedModel):
    print(user)
    print(model)

m = ProtectedModel("gpt-3", GPT35())
u = Member()

elite_func(user=u, model=m)