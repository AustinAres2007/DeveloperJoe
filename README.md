![alt text](https://cdn.discordapp.com/attachments/1117948406011269140/1131694810454040646/Untitled_Artwork.jpg)

# **Information**

DeveloperJoe is a GPT 3/4 Discord bot that is fully customisable if you have sufficient Python knowledge.
- Multiple Chats at one time
- Long-term chat storage
- Image Generation
- Streaming chat replies

## Setup

* To start, ==run the `install.sh` file== located in the root of DeveloperJoe. It will give you a warning that your API key file (dependencies/api-keys.key) does not exist, this is normal. This error will not appear if the key file already exists.

    >api-keys.key file format:
    >:discord-api-key:
    >:openai-api-key:

* ==Obtain a Discord API Key== from [Discord's Developer Website.](https://discord.com/developers/applications) Go to the "Bot" tab, and click "Reveal Token" Once you have revealed it, you may not reveal it again unless you regenerate it. I would recommend saving it somewhere secure. Do **NOT** give it to **ANYONE**. It will be detected as leaked if transmitted via Discord. You can give the Bot any name you like, the bot has been programmed to dynamically reference itself.

    After you have obtained an API Key, load the file ==`dependencies/api-keys.key` and paste the key on line 1.==

* ==Obtain an OpenAI API Key== from [OpenAI's Website](https://platform.openai.com/account) and navigate to the "API keys" tab and register one. And warning for beginnners, using this API costs money, and you will **NEED** to add a payment method if you do not have free credits, and depending on the model and how much you use it, it can get expensive.

    ==Paste the OpenAI API Key in `dependencies/api-keys.key` on line 2==, under the Discord API Key.
    Congratulations, the hard part is over. The following steps are not essential, but recommended for customisation purposes.

* Congratulations, you have finished the instillation. Click the footnote at the end of this sentence for instructions to run the bot. [^nm] Click the footnote at the end of this sentence for insturctions of how to run the bot for advanced users. [^op]

## Voice Support

Voice support is provided by default. I have only officially supported Windows 10 / 11 and macOS Sonoma. I will test Linux in the future. (Custom distro)
You may disable voice support if you like, either by removing a library in the `voice` folder in root. Or by changing the `ALLOW_VOICE` variable in `sources/common/developerconfig.py` to `False`

You can add your own voice support pretty easily if you have basic knowledge of what your Operating System is, the architechure (32 Bit, 64 Bit, ARM-64, ect..)
I will add to this later, and try and make a more indepth and easy to understand tutorial.

## Optional

* In the file `sources/common/developerconfig.py` you can change any variables to suit your needs. *Note; it is recommended to set `BOT_NAME` to the same name as is set in the [Discord's Developer Portal](https://discord.com/developers/applications), though, it will not cause any problems if not.*

## Errors

* If there are any errors, check the file `misc/bot_log.log`, contact me, and give me the contents of the file. I will then resolve your issue. You may try and resolve the problem yourself if you have sufficient Python programming knowledge.

## Release Notes 1.3.4

1. Bug fixes
2. New AI Command
3. Easier voice setup (Drag and drop)

## Todo 1.3.4

~~Update README with updated method of installing voice library~~
~~Add compatibility with new library name scheme (<lib>-<platform>.<libExtension> Eg. opus-darwin.dylib) done in developerconfig.py~~
Fix `run.sh` not working outside of VENV. For now, execute `. bin/activate` on CLI and run via `python3 main.py`

[^nm]: For a normal user, running `run.sh` within the root folder will suffice.
[^op]: If you want details, use Python version 3.11, and execute `joe.py` within the root folder of DeveloperJoe.
        If you do not do this, you will most likely run into errors regarding importing modules and other dependencies that require reletive paths.

