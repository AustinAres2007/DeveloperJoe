![alt text](https://cdn.discordapp.com/attachments/1117948406011269140/1131694810454040646/Untitled_Artwork.jpg)

# **Information**

DeveloperJoe is a GPT 3/4 Discord bot that is fully customisable if you have sufficient Python knowledge.
- Multiple Chats at one time
- Long-term chat storage
- Image Generation
- Streaming chat replies

## Setup

* To start, ==make a file in the `dependencies` folder in the root of the source files called `api-tokens.keys`==

    >api-tokens.key file format:
    ><discord-api-key>
    ><openai-api-key>

* ==Obtain a Discord API Key== from [Discord's Developer Website.](https://discord.com/developers/applications) Go to the "Bot" tab, and click "Reveal Token" Once you have revealed it, you may not reveal it again unless you regenerate it. I would recommend saving it somewhere secure. Do **NOT** give it to **ANYONE**. It will be detected as leaked if transmitted via Discord. You can give the Bot any name you like, the bot has been programmed to dynamically reference itself.

    After you have obtained an API Key, load the file ==`dependencies/api-tokens.key` and paste the key on line 1.==

* ==Obtain an OpenAI API Key== from [OpenAI's Website](https://platform.openai.com/account) and navigate to the "API keys" tab and register one. And warning for beginnners, using this API costs money, and you will **NEED** to add a payment method if you do not have free credits, and depending on the model and how much you use it, it can get expensive.

    ==Paste the OpenAI API Key in `dependencies/api-tokens.key` on line 2==, under the Discord API Key.
    Congratulations, the hard part is over. The following steps are not essential, but recommended for customisation purposes.

## Optional

* In the file `objects/GPTConfig.py` you can change any variables to suit your needs. *Note; it is recommended to set `BOT_NAME` to the same name as is set in the [Discord's Developer Portal](https://discord.com/developers/applications), though, it will not cause any problems if not.*

## Errors

* If there are any errors, check the file `misc/bot_log.log` and contact me, give me the contents of said file, and I will resolve your issue. You may try and resolve the problem yourself if you have sufficient Python programming knowledge.

## Release Notes 1.2.4

1. More customisable setup for users.