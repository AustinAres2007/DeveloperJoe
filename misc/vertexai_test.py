"""# A python file to test the capabilities of Googles Vertex AI (bison2)


import vertexai, asyncio
from vertexai.preview.language_models import ChatModel, ChatSession, ChatMessage, TextGenerationModel

async def main() -> None:
    params = {
        "temperature": 0.2,
        "max_output_tokens": 256,
        "top_p": 0.8,
        "top_k": 40
    }
    vertexai.init(project="developerjoe")
    context = []
    model = ChatModel("text-bison@001")
    chat = model.start_chat(message_history=context, **params)
    
    while True:
        text = input(">> ")
        #chat = model.start_chat(message_history=context, **params)
        
        context.append(ChatMessage(text, "user"))
        response = chat.send_message(text)
        
        print(response.text)
        
        
if __name__ == "__main__":
    asyncio.run(main())"""
    
import vertexai
from vertexai.language_models import ChatModel, InputOutputTextPair, ChatMessage

vertexai.init(project="developerjoe")
def science_tutoring(temperature: float = 0.2) -> None:
    chat_model = ChatModel.from_pretrained("chat-bison@001")

    # TODO developer - override these parameters as needed:
    parameters = {
        "temperature": temperature,  # Temperature controls the degree of randomness in token selection.
        "max_output_tokens": 256,  # Token limit determines the maximum amount of text output.
        "top_p": 0.95,  # Tokens are selected from most probable to least until the sum of their probabilities equals the top_p value.
        "top_k": 40,  # A top_k of 1 means the selected token is the most probable among all tokens.
    }
    msg_history: list[ChatMessage] = []

    while True:
        text = input(">> ")
        chat = chat_model.start_chat(message_history=msg_history)
        
        response = chat.send_message(text, **parameters)
        msg_history.extend([ChatMessage(text, "user"), ChatMessage(response.text, "bot")])
        
        print(f"Response from Model: {response.text}")
    """    
    response = chat.send_message(
        "How many planets are there in the solar system?", **parameters
    )
    print(f"Response from Model: {response.text}")
    """
    
    return response


if __name__ == "__main__":
    science_tutoring()