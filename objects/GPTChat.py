import datetime, discord, openai, random, asyncio, time

from typing import Union, Any
from objects import GPTHistory, GPTErrors

openai.api_key = "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"

errors = {
    openai.InvalidRequestError: lambda err: str(err),
    openai.APIError: lambda err: "Generic GPT 3.5 Error, please try again later.",
    openai.error.ServiceUnavailableError: lambda err: "Generic GPT 3.5 Error, please try again later.",
    openai.error.RateLimitError: lambda err: "Hit set rate limit for this month. Please contact administrator.",
    openai.error.APIConnectionError: lambda err: "Could not connect to OpenAI API Endpoint, contact administrator."
}

class GPTChat:
    def __init__(self, user: Union[discord.User, discord.Member], name: str):
        self.user: Union[discord.User, discord.Member] = user
        self.time: datetime.datetime = datetime.datetime.now()
        self.id = hex(int(datetime.datetime.timestamp(datetime.datetime.now()) + user.id) * random.randint(150, 1500))

        self.name = name

        self.tokens = 0
        self.model = "gpt-3.5-turbo-16k-0613"
        self.is_processing = False

        self.readable_history = []
        self.chat_history = []
        self._readable_history_map_ = []

    def __manage_history__(is_gpt_reply: Any, query_type: str, save_message: bool, any_error: Exception, tokens: int):
        self.is_processing = False
        if (not save_message or any_error) and query_type == "query":
            self.chat_history = self.chat_history[:len(self.chat_history)-2]
            self.readable_history.pop()
            self._readable_history_map_.pop()
            if error:
                self.readable_history.append(f"Error: {str(error)}")

        elif (not save_message or any_error) and query_type == "image":
            self.readable_history.pop()
    
            if any_error:
                self.readable_history.append(f"Error: {str(error)}")

        if (is_gpt_reply and save_message and query_type == "query") and not any_error:
            self.tokens += tokens # type: ignore

    def __send_query__(self, query_type: str, save_message: bool=True, give_err_code: bool=False, **kwargs):
            
        error_code = GPTErrors.NONE
        replied_content = GPTErrors.GENERIC_ERROR
        error = GPTErrors.NONE
        r_history = []
        reply = None
        replied_content = ""

        try:
            if query_type == "query":
                
                # Put necessary variables here (Doesn't matter weather streaming or not)
                self.is_processing = True
                self.chat_history.append(kwargs)

                # TODO: If streaming, place code here
                # Reply format: ({"content": "Reply content", "role": "assistent"})
                reply = openai.ChatCompletion.create(model=self.model, messages=self.chat_history)
                actual_reply = reply.choices[0].message  # type: ignore
                replied_content = actual_reply["content"]

                self.chat_history.append(dict(actual_reply))

                r_history.append(kwargs)
                r_history.append(dict(actual_reply))
                self.readable_history.append(r_history)
                self._readable_history_map_.append(len(self.readable_history) - 1)
            
            
            elif query_type == "image":
                # Required Arguments: Prompt (String < 1000 chars), Size (String, 256x256, 512x512, 1024x1024)

                self.is_processing = True
                image_request = openai.Image.create(**kwargs)
                image_url = image_request['data'][0]['url'] # type: ignore
                replied_content = f"Created Image at {datetime.datetime.fromtimestamp(image_request['created'])}\nImage Link: {image_url}" # type: ignore

                r_history.append({'image': f'User asked GPT to compose the following image: "{kwargs["prompt"]}"'})
                r_history.append({'image_return': image_url})

                self.readable_history.append(r_history)
            else:
                error = f"Generic ({query_type})"
                replied_content = f"Unknown Error, contact administrator. (Error Code: {query_type})"

        except Exception as e:            
            error = e
            error_code = 1
            replied_content = errors[type(e)] if type(e) in errors else str(e)

        finally:
            self.__manage_history__(reply, query_type, save_message, error, reply["usage"]["total_tokens"])
            return replied_content if not give_err_code else (replied_content, error_code)

    def ask(self, query: str) -> str: # type: ignore
        return str(self.__send_query__(query_type="query", role="user", content=query))
    
    def start(self) -> str:
        return str(self.__send_query__(save_message=False, query_type="query", role="system", content="Please give a short and formal introduction to yourself, what you can do, and limitations."))

    def clear(self) -> None:
        self.readable_history.clear()
        self.chat_history.clear()
    
    def stop(self, history: GPTHistory.GPTHistory, save_history: str) -> tuple:
        try:
            farewell, error_code = self.__send_query__(query_type="query", role="system", content="Please give a short and formal farewell from yourself.", give_err_code=True)
            if error_code == 0:
                if save_history == "y":
                    history.upload_chat_history(self)
                    farewell += f"\n\n\n*Saved chat history with ID: {self.id}*"
                else:
                    farewell += "\n\n\n*Not saved chat history*"

                return (farewell, int(error_code))
            return (f"An unknown error occured. I have not saved any chat history or deleted your current conversation. \nERROR: ({farewell}, {error_code})", int(error_code))
        except Exception as e:
            return (str(e), 1)

    def __stream_send_query__(self, save_message: bool, **kwargs):
        error_code = GPTErrors.NONE
        replied_content = GPTErrors.GENERIC_ERROR
        error = GPTErrors.NONE
        r_history = []
        generator_reply = None
        replied_content = ""
        tk = 0

        try:
            self.is_processing = True
            self.chat_history.append(kwargs)

            generator_reply = openai.ChatCompletion.create(model=self.model, messages=self.chat_history)

            for tk, chunk in enumerate(generator_reply):
                if chunk["choices"][0]["finish_reason"] != "stop":
                    c_token = chunk["choices"][0]["delta"]["content"]
                    replied_content += c_token
                    yield c_token

            replicate_reply = {"content": replied_content, "role": "assistent"}
            self.chat_history.append(replicate_reply)

            r_history.append(kwargs)
            r_history.append(replicate_reply)

            self.readable_history.append(r_history)
            self._readable_history_map_.append(len(self.readable_history) - 1)

        except Exception as e:
            error = e
            error_code = 1
            replied_content = errors[type(e)] if type(e) in errors else str(e)

        finally:
            self.__manage_history__(generator_reply, "query", save_message, error, tk)
            return replied_content






