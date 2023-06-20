import datetime, discord, openai, random, asyncio, time

from typing import Union
from objects import GPTHistory, GPTErrors

openai.api_key = "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"

class GPTChat:
    def __init__(self, user: Union[discord.User, discord.Member], name: str, stream: bool, client):
        self.user: Union[discord.User, discord.Member] = user
        self.time: datetime.datetime = datetime.datetime.now()
        self.id = hex(int(datetime.datetime.timestamp(datetime.datetime.now()) + user.id) * random.randint(150, 1500))
        self.client = client

        self.name = name
        self.stream = stream

        self.tokens = 0
        self.model = "gpt-3.5-turbo-16k-0613"
        self.is_processing = False

        self.readable_history = []
        self.chat_history = []
        self._readable_history_map_ = []

    def __send_query__(self, query_type: str, save_message: bool=True, give_err_code: bool=False, message: discord.Message=None, **kwargs): # type: ignore
        
        def _edit_message_stream(txt: str):
            return asyncio.run_coroutine_threadsafe(message.edit(content=txt), self.client.loop)
            
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

                if self.stream == True:
                    reply = openai.ChatCompletion.create(model=self.model, messages=self.chat_history, stream=self.stream)   
                    for i, chunk in enumerate(reply):
                        if chunk["choices"][0]["finish_reason"] != "stop": # type: ignore
                            replied_content += chunk["choices"][0]["delta"]["content"] # type: ignore
                            if i % 8 == 0:
                                time.sleep(0.8)
                                _edit_message_stream(replied_content)

                    actual_reply = {"content": replied_content, "role": "assistent"}
                    replied_content = ">"
                else:
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
            
        except openai.InvalidRequestError as e:
            error = e
            error_code = 1
            replied_content = str(e)
        
        except (openai.APIError, openai.error.ServiceUnavalibleError) as e: # type: ignore
            error = e
            error_code = 1
            replied_content = "Generic GPT 3.5 Error, please try again later."
    
        except openai.error.RateLimitError as e: # type: ignore
            error = e
            error_code = 1
            replied_content = "Hit set rate limit for this month. Please contact administrator."

        except openai.error.APIConnectionError as e: # type: ignore
            error = e
            error_code = 1
            replied_content = "Could not connect to OpenAI API Endpoint, contact administrator."

        except Exception as e:
            error = e
            error_code = 1
            replied_content = f"Uncatched Error: {str(e)}. Please contact administrator"

        finally:
            self.is_processing = False
            if (not save_message or error) and query_type == "query":
                self.chat_history = self.chat_history[:len(self.chat_history)-2]
                self.readable_history.pop()
                self._readable_history_map_.pop()
                if error:
                    self.readable_history.append(f"Error: {str(error)}")

            elif (not save_message or error) and query_type == "image":
                self.readable_history.pop()
        
                if error:
                    self.readable_history.append(f"Error: {str(error)}")

            if (reply and save_message and query_type == "query") and not error:
                self.tokens += int(reply["usage"]["total_tokens"]) # type: ignore

            return replied_content if not give_err_code else (replied_content, error_code)

    def ask(self, query: str, interaction: discord.Interaction=None) -> str: # type: ignore
        return str(self.__send_query__(query_type="query", role="user", content=query, interaction=interaction))
    
    def start(self, message: discord.Message) -> str:
        return str(self.__send_query__(save_message=False, query_type="query", message=message, role="system", content="Please give a short and formal introduction to yourself, what you can do, and limitations."))

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
    
    def clear_specific(self, index: int) -> str:
        return ""