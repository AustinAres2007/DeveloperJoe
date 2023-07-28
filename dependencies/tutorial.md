# Hello!

I am {0}, a [GPT](https://aws.amazon.com/what-is/gpt/) powered AI bot.

GPT is different than ChatGPT. GPT is what powers ChatGPT, and ChatGPT focuses mainly on text generation. GPT is made by [OpenAI](https://openai.com/).


## Starting a chat

To start a chat with {0}, do `/start`. This is the most basic form of communication, and will pick a model that the owner has set to default.

You can pick a number of parameters to change the conversation name to represent what your chat is about, change GPT model*, or stream your conversation like ChatGPT. All parameters are optional, and defaults will be used if not specified.

\* = *You may only change to set GPT models. The models may have set restrictions set by the operator of the server you are in. For example, GPT 4 may only be used by users with a special role. By default, all models are accessable.*

##### Other to start chat

You can also make a private thread in a discord server with **ONLY** {0} inside. This eliminates the need for  `/ask` as you can talk to it like a normal user.  For this to work, only you and {0} can be in the private thread. You will still need to use `/start`.


## Continuing a chat  

You can use `/ask` to reply to a conversation started with `/start`. The is 1 required parameters, which is only the message you want to send. You can also override other aspects, like the chat you want to use (If you have multiple) or weather you want to stream {0}'s reply.

#### More ways to continue a chat

If you have started a chat in a private thread, just post your query in the private thread like you would chatting to a normal user.

*Note: conversations started in a normal text channel can be carried over to a private thread, they both share the context of the conversation.*

#### Generating Images

You can use `/generate` to generate an image with the [DALL-E](https://openai.com/dall-e-2) Image generation engine also created by [OpenAI]([https://openai.com](https://openai.com/)).

## Stopping a chat
  
You can use `/stop` to stop a chat. There are 2 required parameters, the option to save the chat for retrieval later, and the chat you want to end. Once you end a chat, it cannot be restarted again. You will be asked for confirmation to stop the chat.

## Accessing saved chats

When using `/stop` if you specified to save your chat, you will get a unique ID specific to the chat you ended, you cannot retrieve the ID if the message is lost or deleted. If you want access to it for long-term, please save it somewhere safe.

Use the `/history` command with the single required parameter set to your unique chat ID, and your past {0} chat will be send to you.

#### Deleting chat history

Use the `/delete` command with the single required parameter set to your unique chat ID. This action cannot be undone. You will be asked for confirmation to delete the chat.

#### Exporting chat history whilst chat is active

Use the `/export` command to grant you access to your current ongoing chat. You can specify another chat, but this is optional and your default chat will be used if not specified.

## Other

You can view all commands and their arguments with `/help`.