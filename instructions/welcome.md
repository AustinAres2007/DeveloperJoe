# Welcome

This is an indepth document on the DeveloperJoe Engine-- on what it does mainly. This is a bot that is fully configurable and modify-able since this project is FULLY open source including the voice libraries which are not mine. They are developed and belong to their very talanted respective developers, I say this with admiration.

- [The FFMPEG project, all contributors and dependencies](https://ffmpeg.org/about.html)
- [libopus and xiph.org](https://opus-codec.org)

# Objective

This documents and all that reside alongside it serve to educate the end-user. (The person who hosts this bot)
I will walk through each command; talk about what it does, the parameters and other aspects of it. 

Feel free to use this as a manual for discord users as it holds no commands or data that is sensitive to the operating of this bot.

# Warnings

This bot is not meant to be used on a large scale. it is to be used by small communities. There are costs associated with running this bot due to services that will have to be used (Like OpenAIs GPT AI Engine) which can get costly if used on a large scale. Smaller database systems are used to keep CPU usage down.

# Extra Warning

Using this bots voice capabilities will use a lot of data and a lot of resources. Please make sure your host computer can handle the demands.

# Commands

I shall state most importants first

1. ## /help
   * This command has no arguments.
   * This command lists ALL commands registered to the bot

2. ## /config
   * This command has no arguments.
   * This command lists the discord server's configuration setup (If voice is enabled, the speaking multiplier, etc...) You do NOT change the configuration here. You do it with other commands.

3. ## /reset
   * This command has no arguments.
   * This command can only be used by the servers administrators.
   * This command resets the discord server's configuration setup. I only recommend this if the default changes or you mess something up. You will need to provide confirmation of the reset after the command is sent.

# Configuration Commands

These commands are used to change the configuration values viewed with `/config`

1. ## /voice `enable_voice`
   * This command has 1 argument. (enable_voice: True or False value)
   * This command can only be used by the servers administrators.
   * This command disabled voice usage within the server the command was sent in. 

2. ## /speed `speed`
   * This command has 1 argument. (speed: decimal or round value. Anything between 1.0 and 4.0)
   * This command changes how fast the bot can speak if enabled. I would personally not recommend anything higher 1.4

3. ## /timezone `timezone`
   * This command has 1 argument. (timezone: This value has to be a valid timezone. You can view them with `/times`)
   * This command can only be used by the servers administrators.
   * This command changes the timezone that is used at the footer of some commands (Bottom of the command)

4. ## /keyword `keyword`
   * This command has 1 argument. (keyword: Anything you like)
   * This command can only be used by the servers administrators.
   * This command changes the listening-keyword that invokes the bots listening. (E.G. You can change it to "Siri" or "Alexa" if you want something that you recognise)

# GPT Commands 

Commands that relate to starting a chat, or anything relating to it

1. ## /start `chat_name` `stream_conversation` `gpt_model` `in_thread` `speak_reply` `in_private`
   * This command has 6 arguments. All are optional and defaults will be used.
        - `chat_name`: The name of the chat being created.
        - `stream_conversation`: Weather the chat will be streamed. (Text will appear gradually, like ChatGPT)
        - `gpt_model`: What model of GPT you want to use.
        - `in_thread`: If a special thread will be made for this chat.
        - `speak_reply`: If the chat will be spoken in a voice channel. The bot will join if this is option is enabled, and the chat owner is in a voice channel.
        - `in_private`: If the chat is private. Meaning that the chat history cannot be exported by other people with the History ID.
    
    * This command starts a chat with the specifed GPT model-- The same models that power ChatGPT.

2. ## /ask `query` `name` `stream`
   * This command has 3 arguments. `name` and `stream` are optional.
      - `query`: What you want to ask DeveloperJoe.
      - `name`: Name of the chat you want to ask a question to. Like having multiple conversations in ChatGPT.
      - `stream` Weather the question posed will be streamed. This overrides the option specified when the chat was started.

3. ## /image `prompt` `resolution` `save_to`
   * This command has 3 arguments. `save_to` is optional.
      - `prompt`: Described version of the image you want made.
      - `resolution`: The resolution of the image. You have to chose from the three options. (256x256, 512x512, 1024x1024)
      - `save_to`: The chat where the image will be saved. This is optional, and the default chat you have saved will be used instead.

3. ## /stop `name` `save_chat`
   * This command has 2 arguments. `save_chat` is optional.
      - `name`: Name of the chat you want to end.
      - `save_chat`: If you want the chat to be stored for long term storage. This is active by default.
   * This command stops a chat that was started with `/start`.

4. ## /inquire `query` `gpt_model`
   * This command has 2 arguments. `gpt_model` is optional.
      - `query`: What you want to ask DeveloperJoe.
      - `gpt_model`: What model of GPT you want to use. This is optional and a default will be used if not provided.

# Chat Settings & Management

Commands that relate to chats.

1. ## /info `name`
   * This command has 1 argument. All are optional.
      - `name`: Name of the chat you want to retrieve info from. This is optional and the users default chat will be used if not provided.
   * This command retrieves in-depth information on a chat you have started. Once the chat has ended, you may no longer view the info on it.

2. ## /switch `chat`
   * This command has 1 argument.
      - `chat`: The chat you want to switch to.
   * This command switches the default chat for the user who sends the command.

3. ## /chats
   * This chat has no arguments.
   * This command lists all chats that a user holds.

# Voice

Commands that relate to voice capabilities. All these commands require you have a conversation with `speak_reply` active (Set to `True`)

1. ## /listen `listen`
   * This command has 1 argument.
      - `listen`: Weather the bot will listen to your voice requests. Like any other smart assistant.
   * This will enable / disable listening. You may ask DeveloperJoe a query with the listening keyword. By default, it is "assistant" but you can change it with `/keyword`

2. ## /shutup
   * This command has no arguments.
   * This command will stop DeveloperJoe from talking if what it is saying takes to long, or you recieve a response that is not favourable.
  
3. ## /pause
   * This command has no arguments.
   * This command will pause DeveloperJoe from speaking. You can undo this with `/resume`

4. ## /resume
   * This command has no arguments.
   * This command will resume DeveloperJoe from a paused state invoked with `/pause`

# History Exporting & Archiving

Commands that relate to chat history management (Like saving the transcript for later)

1. ## /export `name`
   * This command has 1 argument. `name` is optional.
      - `name`: The name of the chat that will be exported. If this argument is not provided, it will use the users current default chat.
   * This command will export the transcript ONLY of a chat that is still currently active.

2. ## /history `history_id`
   * This command has 1 argument.
      - `history_id`: The history ID of the chat that has been completed with `/stop` and saved for long-term storage with the `save_chat` argument active
   * This command will retrieve data from a chat that ended in the past and saved with `/stop`

3. ## /delete `history_id`
   * This command has 1 argument.
      - `history_id`: The history ID of the chat that will be deleted.
   * This command will delete an archived chat that was saved with `/stop`'s `save_chat` parameter.

# Model Restriction

This group of commands limit what GPT Models can be used by certain rank of user.
For example, if you want to lock GPT-4 behind a VIP role, you do it with:
> /lock gpt_model: GPT 4 role: @VIP

1. ## /locks
   * This command has no arguments.
   * This command will view all locks placed upon models.

2. ## /lock `gpt_model` `role`
   * This command has 2 arguments.
      - `gpt_model`: The GPT Model you want to lock.
      - `role` The role you want it to be locked behind.
   * This command will lock a GPT Model behind a role. Higher ranked users than the specified role will still be able to use specified model since they outrank the role that was used for the lock.

3. ## /unlock `gpt_model` `role`
   * This command has 2 arguments.
      - `gpt_model` The GPT Model you want to unlock.
      - `role` Role to remove the usage restriction from.
   * This command removes the role restriction that was placed upon by `/lock`

# General

General commands that have little to no relation to a specific group.

1. ## /models
   * This command has no parameters.
   * This command lists all models avalible to use.

# Administrative

These commands may only be executed by the bots owner. Designated by the discord API keys account that was used.

1. ## /shutdown
   * This command has no arguments.
   * This command can only be used by the bots owner.
   * This command shuts down the bot in a clean and effective way.
