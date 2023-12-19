![alt text](https://cdn.discordapp.com/attachments/1116489126204690523/1185031135261118546/Untitled_Artwork.jpg)

# **Information**

DeveloperJoe is a GPT 3/4 Discord bot that is fully customisable if you have sufficient Python knowledge.
- Multiple Chats at one time
- Long-term chat storage
- Image Generation
- Streaming chat replies

I would recommend reading all the files inside the instructions folder if you plan to take advantage of the full capabilities of this bot. Though, the "welcome.md" file would suffice, or even just this file would do.

This bot is directed towards people who want customisation. Though, this is because I am lazy and too broke to afford the API prices. The customisation does come at a cost, which is that you have to have some very minor knowledge or python programming.

## Setup

1. ### Run the installation / run script 
    * To start, run the installation / run script, labeled "bot" located in the root of DeveloperJoe. It will give you a warning that your API key file (dependencies/api-keys.key) does not exist, this is normal. This error will not appear if the key file already exists.

2. ### Obtain a Discord API Key from [Discord's Developer Website.](https://discord.com/developers/applications) 
    * Go to the "Bot" tab, and click "Reveal Token" Once you have revealed it, you may not reveal it again unless you regenerate it. I would recommend saving it somewhere secure. Do **NOT** give it to **ANYONE**. It will be detected as leaked if transmitted via Discord. You can give the Bot any name you like, the bot has been programmed to dynamically reference itself.

    * After you have obtained an API Key, load the file `dependencies/api-keys.yaml` and paste it on the line where it says: "discord_api_key: (key)"

3. ### Obtain an OpenAI API Key from [OpenAI's Website](https://platform.openai.com/account) 
    * Navigate to the "API keys" tab and register one. And warning for beginnners, using this API costs money, and you will **NEED** to add a payment method if you do not have free credits, and depending on the model and how much you use it, it can get expensive.

    * After you have obtained an API Key, load the file `dependencies/api-keys.yaml` and paste it on the line where it says: "openai_api_key: (key)"

4. ### Congratulations, you have finished the instillation.
    * Read further if you want to setup voice capabilities or instructions on how to run the bot.

## Running DeveloperJoe

All you have to do is double click the file `bot` for all operating systems

## Voice Support

Voice support added by default if you downloaded a release from my GitHub, you do not need to do any setup at all. Just run the bot. If not, you will need to acquire the required libraries. You can download the respective files for your computer at [this repository.](https://github.com/AustinAres2007/developerjoe-downloads/releases) Simply drag and drop all 3 inside your respective ZIP folder files into the `voice` directory.

**Other**

You can add your own voice support pretty easily if you have basic knowledge of what your Operating System is, the architechure (32 Bit, 64 Bit, ARM-64, ect..)
I will add to this later, and try and make a more indepth and easy to understand tutorial.

## Optional

* In the file `bot-config.yaml` you can change any variables to suit your needs. *Note; it is recommended to set `bot_name` to the same name as is set in the [Discord's Developer Portal](https://discord.com/developers/applications), though, it will not cause any problems if not.*

## Errors

* If there are any errors, check the file `misc/bot_log.log`, contact me, and give me the contents of the file. I will then resolve your issue. You may try and resolve the problem yourself if you have sufficient Python programming knowledge.

## Release Notes 1.4.2

Changes

Quick summary

- More customisable permissions
- Command groups
- Overhauled Internal systems

Changelog

- New commands
    - /permissions (With subcommands)
        - /permissions add -> Adds an allowed role to a bot function.
        - /permissions remove -> Removes a role from a bot function.
        - /permissions list -> Lists all bot functions that a role can be applied to.
        - /permissions view -> Lists all roles applied to bot functions.
    
- Renamed Commands
    - /stopbot -> /owner exit
    - /backup -> /owner backup
    - /load -> /owner load
    - /lock -> /admin lock
    - /unlock -> /admin unlock
    - /locks -> /admin locks
    - /models -> /admin change-model

- Bug Fixes
    - Fixed bug when trying to get server configuration value (attr import, incorrect variable name)

- Other
    - Internal AI requests API overhaul

## Todo 1.4.3

- Add Gemini support
- Add more customisable role permission settings (Role can only be X role, or role can only be X and Y)
- Dockerfile

## Technical Todo 1.4.3 (PaLM 2 / Gemini)

- ~~Check if Project ID is valid~~ (Not on runtime but error handling is done for it)
- ~~Check if user logged in with `gcloud login` of whatever the shitty fucking command was~~ Same as above
- ~~Add error handling for PaLM 2. No error handling is set at all. (https://cloud.google.com/vertex-ai/docs/generative-ai/learn/responsible-ai maybe? idk)~~
- ~~Need to redesign /help for command groups~~
- ~~Need to add Gemini and add streaming capabilities to PaLM and or Gemini~~ In another update
- ~~Test Protected Classes~~
- ~~Add protected class functionality to functions (Will become much more useful hopefully)~~

## Other (1.4.x)

- Bot listening bugs. Could be because I removed the silence thingy that was in ttsmodels.py
- Might remove voice. This will fix the stdin error
- The same stupid fucking error with self.stdin.flush(); flush of closed file error again (Happens when using /shutup)

## Notes

- Adding Gemini may be quite difficult due to how chat history is stored and how chats work. It may require big internal changes.
