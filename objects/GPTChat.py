from typing import Union
import datetime, discord, openai

openai.api_key = "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"

class GPTChat:
    def __init__(self, user: Union[discord.User, discord.Member]):
        self.user: Union[discord.User, discord.Member] = user
        self.time: datetime.datetime = datetime.datetime.now()

        self.tokens = 0
        self.model = "gpt-3.5-turbo"
        self.is_processing = False

        self.chat_history = []
        self.readable_history = []

    def __send_query__(self, query_type: str, save_message: bool=True, **kwargs) -> str:
        
        replied_content = "Unknown error, contact administrator."
        error = False
        r_history = []
        reply = None

        try:
            if query_type == "query":
                

                self.chat_history.append(kwargs)
                r_history.append(kwargs)

                reply = openai.ChatCompletion.create(model=self.model, messages=self.chat_history)
                actual_reply = reply.choices[0].message  # type: ignore

                replied_content = actual_reply["content"]

                self.chat_history.append(dict(actual_reply))
                r_history.append(dict(actual_reply))
                self.readable_history.append(r_history)
            
            
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
            replied_content = str(e)
        
        except (openai.APIError, openai.error.ServiceUnavalibleError) as e: # type: ignore
            error = e
            replied_content = "Generic GPT 3.5 Error, please try again later."
    
        except openai.error.RateLimitError as e: # type: ignore
            error = e
            replied_content = "Hit set rate limit for this month. Please contact administrator."

        except openai.error.APIConnectionError as e: # type: ignore
            error = e
            replied_content = "Could not connect to OpenAI API Endpoint, contact administrator."

        except Exception as e:
            error = e
            replied_content = f"Uncatched Error: {str(e)}. Please contact administrator"

        finally:
            self.is_processing = False
            if (not save_message or error) and query_type == "query":
                self.chat_history = self.chat_history[:len(self.chat_history)-2]
                self.readable_history.pop()

                if error:
                    self.readable_history.append(f"Error: {str(error)}")

            elif (not save_message or error) and query_type == "image":
                self.readable_history.pop()

                if error:
                    self.readable_history.append(f"Error: {str(error)}")

            if (reply and save_message and query_type == "query") and not error:
                self.tokens += int(reply["usage"]["total_tokens"]) # type: ignore
            
            print(self.tokens)

            return replied_content

    def ask(self, query: str) -> str:
        return self.__send_query__(query_type="query", role="user", content=query)
    
    def start(self) -> str:
        return self.__send_query__(save_message=False, query_type="query", role="system", content="Please give a short and formal introduction to yourself, what you can do, and limitations.")

    def clear(self) -> None:
        self.readable_history.clear()
        self.chat_history.clear()