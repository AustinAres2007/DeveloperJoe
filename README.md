![alt text](https://cdn.discordapp.com/attachments/1117948406011269140/1131694810454040646/Untitled_Artwork.jpg)

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

## Release Notes 1.4.0

New Features

- Can now change bot volume with /volume
- New Scrolling status-- enable it with the configuration option `enable_status_scrolling` and add more via `status_scrolling_options`!

Changes 

- When using /start, the `silent` parameter (set to True by default) will start the chat instantly instead of thinking of a response.
- @ing the bot now makes it talk to you. Like /inquire-- context is not saved.
- Added version checking when a backup is loaded.
- Better voice recognition-- You can now ask the bots listening keyword anywhere within a sentence and it will recognise any words you say after the keyword!
- When using a command that changes the config, you can now leave the value default to view the current config value.

Fixed Bugs

- When using /shutup, there was a good chance an error will appear regarding a closed IO object. This now no longer happens.
- /image gave an error thinking it is in direct messages even in a server. This is fixed.
- If a users voicestate was updated while the bot is coming online, loads of errors would be added to the log. Hopefully fixed as far as my minimal tests go.
- There was another IO error when moving voice channels while the bot was speaking. This is now fixed.

## Todo 1.4.1

- Transplant old version data to new database when the version is different and create defaults of what is missing. (Going to be difficult)
- Add script that installs voice libraries for respective systems. (Keep in mind of OS, and system arch)
- When asking a question, append the query onto `DeveloperJoe.statuses` while the query is being answered so it can appear on DJ's status if chosen. 

## Todo 1.4.x

Experimental

- Experiment with discord UI API
- Experiment with saving the state of the database to a variable every certain amount of time, then use data from said variable. Would be more effient on resources.