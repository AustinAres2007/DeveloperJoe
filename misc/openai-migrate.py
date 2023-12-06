import asyncio
from cgi import print_environ_usage
import openai

async def main():
    async with openai.AsyncOpenAI(api_key="nunya") as oaia:
        a = await oaia.chat.completions.create(messages=[{"role": "user", "content": "Hello!"}], model="gpt-3.5-turbo", stream=True)        
        async for _res in a.response.aiter_text():
            print(_res)
            
        

asyncio.run(main())