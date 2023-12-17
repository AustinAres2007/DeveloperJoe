"""

# How to make custom models


Every model must have a class that derives from `AIModel`.
The class must also have at least have the following awaitable `classmethod`:

```
@classmethod
async def __askmodel__(query: str, context: ConversationContext | None, save_message: bool = True) -> AIQueryResponse:
    # AI API calling code here
    ...
```

Even if you have no awaitable code to run, the method must be defined as coroutine. (async def)

### A quick summary

- `query` is the message the user sent to the AI.
- `context` is the conversation history. It is an instance of `ConversationContext` which is a class that handles the conversation history.
- `save_message` is a boolean that determines whether or not the message should be saved to the context. (This is optional)
- The method must return an `AIQueryResponse` object.

### Saving messages to a given context.

The second argument of __askmodel__ is called `context`. This is an instance of `ConversationContext` which is a class that handles the conversation history.
This argument is optional. Which means it can be `None`.

It is the responsibility of the model to save the message to the context and should be handled in `__askmodel__`.

When retieving the data from `context`, you may have to translate it into a readable format for the AI you are chosing. 
By default, the format is what OpenAI's GPT uses. Which means it does not need to be translated a model based off of OpenAI's GPT.

The format is as follows:

```
[
    {
        "role": "user",
        "content": "Hello, how are you?"
    },
    {
        "role": "assistant",
        "content": "I am fine, thanks for asking."
    }
]
```
So, to sum it up in a nutshell, the `context` argument is a list of dictionaries. Each dictionary has two keys: `role` and `content` and both are strings.
The `role` key can be either `user` or `assistant` depending on who is talking. The `content` key is the message content. 

This dictionary should be translated into the format your AI uses. If it uses the same format, you can just pass it through. If not, you must translate it.
For example, PaLM 2 uses the following format:

```
[
    {
        "author": "user",
        "content": "Hello, how are you?"
    },
    {
        "author": "bot",
        "content": "I am fine, thanks for asking."
    }
]
```

The difference being that "role" is replaced with with a key called "author" and their value is either "user" or "bot" depending on who is talking. 

### Returning a valid `AIQueryResponse` object

The method must return an `AIQueryResponse` object. You can use the `_gpt_ask_base` function to do this. (If you want it to be based upon OpenAI's GPT engine.
Read the adequate documentation if so) 

If you want to create a custom engine based off of custom training data or such (This is not documentation on that. I am expecting the model is finished. This is mostly
a tutorial on how to implement it into the bot) You can instantiate the `AIQueryResponse` class and return it. To do this you must comply with the following dictionary format:

```
a = {
    "id": "model_name", # This can be anything, but it is recommended to be the name of the model.
    "finish_reason": "length", # This can by anything, but it is recommended to follow the protocol OpenAI set in this page: https://platform.openai.com/docs/guides/text-generation/chat-completions-api. A list of reasons are posted there
    "reply": "AI response here", # This can be just plain-text english.
    "timestamp": 1234567890 # This is the POSIX timestamp of the response. You can use the one sent with the AI's JSON response. If your AI does not have that, use time.time() or something of the sort. It is not optional.
    "completion_tokens": 10, # The number of tokens generated across all completions emissions. This is optional as not all AI models return tokens, but recommended if at all obtainable. Even with a tokeniser. (If not set, the wrapper object will return 0)
    "prompt_tokens": 10, # The number of tokens in the provided prompts for the completions request. This is optional as not all AI models return tokens, but recommended if at all obtainable. Even with a tokeniser. (If not set, the wrapper object will return 0)
}
```

To create an `AIQueryResponse` with the dictionary I defined in `a`, do:

```
r = AIQueryResponse(a)
```

- If missing, non-optional data is passed, a ValueError will be raised.

- If extrenous data is passed, you can access it via the `r.raw` property or using `r.<attr>` (This will not show up in any type checkers or autocomplete).

### Other

~~If you want to add image generation or streaming replies. Please use your own common sense and read the code. I am too lazy to write the documentation at this time. 
I am watching a really good movie.~~

"""