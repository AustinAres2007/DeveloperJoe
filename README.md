# Information

![DeveloperJoe Icon](https://i.imgur.com/SgdL99Y.png)

DeveloperJoe is an AI discord bot that comes with GPT 3 / 4 by default and that is fully customisable if you have sufficient Python knowledge.

- Multiple chats
- Long-term chat storage
- Image Generation
- Streaming chat replies
- Image Analysing
- Markdown support

I would recommend reading all the files inside the instructions folder if you plan to take advantage of the full capabilities of this bot. Though, the "welcome.md" file would suffice, or even just this file would do.

This bot is directed towards people who want customisation. Though, this is because I am lazy and too broke to afford the API prices. The customisation does come at a cost, which is that you have to have some very minor knowledge or python programming.

## Setup

1. ### Run the installation / run script

    - To start, run the installation / run script, labeled "bot" located in the root of DeveloperJoe. It will give you a warning that your API key file (dependencies/api-keys.key) does not exist, this is normal. This error will not appear if the key file already exists.

2. ### Obtain a Discord API Key from Discord's Developer Website

    - Go to [Discord's Developer Website.](https://discord.com/developers/applications)
    - Go to the "Bot" tab, and click "Reveal Token" Once you have revealed it, you may not reveal it again unless you regenerate it. I would recommend saving it somewhere secure. Do **NOT** give it to **ANYONE**. It will be detected as leaked if transmitted via Discord. You can give the Bot any name you like, the bot has been programmed to dynamically reference itself.
    - After you have obtained an API Key, load the file `dependencies/api-keys.yaml` and paste it on the line where it says: "discord_api_key: (key)"

3. ### Obtain an OpenAI API Key from OpenAI's Website

    - Go to [OpenAI's Website](https://platform.openai.com/account)
    - Navigate to the "API keys" tab and register one. And warning for beginnners, using this API costs money, and you will **NEED** to add a payment method if you do not have free credits, and depending on the model and how much you use it, it can get expensive.
    - After you have obtained an API Key, load the file `dependencies/api-keys.yaml` and paste it on the line where it says: "openai_api_key: (key)"

## Running DeveloperJoe

After loading both API keys, all you have to do is double click the file `bot` for most operating systems.

## Configuration (Optional)

In the file `bot-config.yaml` you can change any variables to suit your needs. *Note; it is recommended to set `bot_name` to the same name as is set in the [Discord's Developer Portal](https://discord.com/developers/applications), though, it will not cause any problems if not.*

## Errors

If there are any errors, check the file `misc/bot_log.log`, contact me, and give me the contents of the file. I will then resolve your issue. You may try and resolve the problem yourself if you have sufficient Python programming knowledge.

## Release Notes 1.4.7 & 1.4.8

- New command: /histories - List all histories (saved chats) the user has.
- New command: /model customise - Customise a specified model
- New command: /model destroy - Destroy a custom model made with /model customise
- New command: /model list - List all customised models

## New Features

- Autocompletion for AI Models (Including customised ones), histories, and chat names.
- Export raw json of current chat history

## Bug Fixes

- Fixed fatal bug regarding images and threads.

## Changes

- Internal changes
