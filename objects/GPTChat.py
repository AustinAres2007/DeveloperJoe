import datetime, discord, openai, random, openai_async

from typing import Union, Any, Generator
from objects import GPTHistory, GPTErrors

open_ai_api_key = "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"
openai.api_key = open_ai_api_key

errors = {
    openai.InvalidRequestError: lambda err: str(err),
    openai.APIError: lambda err: "Generic GPT 3.5 Error, please try again later.",
    openai.error.ServiceUnavailableError: lambda err: "Generic GPT 3.5 Error, please try again later.", # type: ignore
    openai.error.RateLimitError: lambda err: "Hit set rate limit for this month. Please contact administrator.", # type: ignore
    openai.error.APIConnectionError: lambda err: "Could not connect to OpenAI API Endpoint, contact administrator." # type: ignore
}

class GPTChat:
    def __init__(self, user: Union[discord.User, discord.Member], name: str):
        self.user: Union[discord.User, discord.Member] = user
        self.time: datetime.datetime = datetime.datetime.now()
        self.id = hex(int(datetime.datetime.timestamp(datetime.datetime.now()) + user.id) * random.randint(150, 1500))

        self.name = name
        self.stream = False

        self.tokens = 0
        self.model = "gpt-3.5-turbo-16k-0613"
        self.is_processing = False

        self.readable_history = []
        self.chat_history = []
        self._readable_history_map_ = []

    def __manage_history__(self, is_gpt_reply: Any, query_type: str, save_message: bool, any_error: Union[Exception, None, str], tokens: int):
        self.is_processing = False

        if (not save_message or any_error) and query_type == "query":
            
            try:
                self.chat_history = self.chat_history[:len(self.chat_history)-2]
                self.readable_history.pop()
                self._readable_history_map_.pop()
            except IndexError:
                pass
            if any_error:
                return str(any_error)

        elif (not save_message or any_error) and query_type == "image":
            self.readable_history.pop()
    
            if any_error:
                return str(any_error)

        if (is_gpt_reply and save_message and query_type == "query") and not any_error:
            self.tokens += tokens # type: ignore

        return 
    
    async def __send_query__(self, query_type: str, save_message: bool=True, give_err_code: bool=False, **kwargs):
            
        replied_content = GPTErrors.GENERIC_ERROR
        error = GPTErrors.NONE
        r_history = []
        replied_content = ""

        reply = None
        usage = None

        try:
            if query_type == "query":
                
                # Put necessary variables here (Doesn't matter weather streaming or not)
                self.is_processing = True
                self.chat_history.append(kwargs)

                # TODO: Test async module
                # Reply format: ({"content": "Reply content", "role": "assistent"})
                _reply = await openai_async.chat_complete(api_key=open_ai_api_key, timeout=20,
                                                         payload={
                                                             "model": self.model,
                                                             "messages": self.chat_history    
                                                         })
                reply: dict = _reply.json()["choices"][0]
                usage: dict = _reply.json()["usage"]
                actual_reply = reply["message"]  # type: ignore
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

        except Exception as e:            
            error = e
            replied_content = errors[type(e)] if type(e) in errors else str(e)

        finally:    
            
            print(reply, query_type, save_message, error, usage)

            final_error = self.__manage_history__(reply, query_type, save_message, error, usage["total_tokens"] if reply else 0)
            return replied_content if not final_error else f"Critical Error: {final_error}\nContact Administrator."

    def __stream_send_query__(self, save_message: bool=True, **kwargs):
        replied_content = GPTErrors.GENERIC_ERROR
        error = GPTErrors.NONE
        r_history = []
        generator_reply = None
        replied_content = ""
        tk = 0

        try:
            self.is_processing = True
            self.chat_history.append(kwargs)
            generator_reply = openai.ChatCompletion.create(model=self.model, messages=self.chat_history, stream=True)

            for tk, chunk in enumerate(generator_reply):
                if chunk["choices"][0]["finish_reason"] != "stop":
                    c_token = chunk["choices"][0]["delta"]["content"]
                    replied_content += c_token
                    yield c_token

            replicate_reply = {"role": "assistant", "content": replied_content}
            self.chat_history.append(replicate_reply)

            r_history.append(kwargs)
            r_history.append(replicate_reply)

            self.readable_history.append(r_history)
            self._readable_history_map_.append(len(self.readable_history) - 1)

        except Exception as e:
            error = e
            replied_content = errors[type(e)] if type(e) in errors else str(e)

        finally:
            err = self.__manage_history__(generator_reply, "query", save_message, error, tk)
            if err:
                yield f"Critical Error: {err}\nContact Administrator."

    async def ask(self, query: str) -> str: # type: ignore
        return str(await self.__send_query__(query_type="query", role="user", content=query))
    
    def ask_stream(self, query: str) -> Generator:
        return self.__stream_send_query__(role="user", content=query)

    async def start(self) -> str:
        return str(await self.__send_query__(save_message=False, query_type="query", role="system", content="Please give a short and formal introduction to yourself, what you can do, and limitations."))

    def clear(self) -> None:
        self.readable_history.clear()
        self.chat_history.clear()
    
    def stop(self, history: GPTHistory.GPTHistory, save_history: str) -> str:
        try:
            farewell = "Ended chat with DeveloperJoe!"
            if save_history == "y":
                history.upload_chat_history(self)
                farewell += f"\n\n\n*Saved chat history with ID: {self.id}*"
            else:
                farewell += "\n\n\n*Not saved chat history*"

            return farewell
        except Exception as e:
            return f"Critical Error: {e}"