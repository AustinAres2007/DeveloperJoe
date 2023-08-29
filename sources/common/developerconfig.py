from __future__ import annotations

import pytz as _pytz

from discord import ChannelType, ActivityType, TextChannel, Thread, TextChannel
from discord.app_commands import Choice as _Choice

"""END-USER CONFIGURATION"""

# General

BOT_NAME = "DeveloperJoe" # Name of the bot when describing commands or help.
STATUS_TYPE = ActivityType.listening # The "Playing" or "Listening to" part of the bot's status
STATUS_TEXT = "/help AND answering lifes biggest questions." # Bot's status when activated
DEFAULT_GPT_MODEL = "gpt-3.5-turbo" # gpt-4, or gpt-3.5-turbo (GPT4 or GPT3Turbo)

# Voice

LISTENING_KEYWORD = "assistant" # The name that will invoke the bots reply (Like with "Hey Siri" or "Alexa", example: "Hey developer, what is factorial of 1?")
LISTENING_TIMEOUT = 2.5 # How many seconds of silence there must be until the bot will process a users voice request.
VOICE_SPEEDUP_MULTIPLIER = 1.17 # How fast you want the default text-to-speach model to talk. (1 = default, quite slow. 2 = Quite fast)
ALLOW_VOICE = True # Weather voice support is enabled. It is by default, and will require additional setup if you do not have FFMPEG installed. It is easy to do so.

# Region

TIMEZONE = "UTC" # What timezone to use (UTC by default, check misc/timezones.txt for a list of all.)

"""ADVANCED. SOURCE CODE EDITORS ONLY"""

GPT_REQUEST_TIMEOUT = 180 # Any less than 30 and the bot is very lightly to crash
QUERY_TIMEOUT = 10 # Timeout for destructive actions.
QUERY_CONFIRMATION = ">y" # What keyword to use for confirmation of destructive actions

STREAM_UPDATE_MESSAGE_FREQUENCY = 10 # When streaming a GPT reply, this dictates every set amount of tokens to update the message. Any less that 10 and it will lag.
CHATS_LIMIT = 14 # How many chats a user can have at one time. This cannot be more than 14.
CHARACTER_LIMIT = 2000 # Do NOT put this anywhere over 2000. If you do, the bot will crash if a long message is sent.

FINAL = True # This does nothing. Just indicates if the current version of the bot is the final revision. You may delete this.
DEBUG = True # Debug is ALWAYS True, if set to false, errors will not be logged to misc/bot_log.log
VERSION = "1.3.3-L" # Current bot version. ("A" at the end means near final release, as you go further down the alphabet, the further away from final release. Example; "Z" means it is very far from final release version. No letter means it is the final release)

DATABASE_FILE = "dependencies/dg_database.db" # Where the SQLite3 Database file is located. (Reletive)
TOKEN_FILE = "dependencies/api-keys.key" # Where the API keys for Discord and OpenAI are located. (Reletive)
WELCOME_FILE = "dependencies/tutorial.md" # Where the introduction / welcome text is located. (Reletive)
ADMIN_FILE = "dependencies/admin-tutorial.md" # Where the admin introduction / welcome text is located. (Reletive)

MODEL_CHOICES: list[_Choice] = [
    _Choice(name="GPT 3.5 - Turbo", value="gpt-3.5-turbo"),
    _Choice(name="GPT 4", value="gpt-4")
] # What models of GPT are avalible to use, you can chose any that exist, but keep in mind that have to follow the return format of GPT 3 / 4. If not, the bot will crash immediately after a query is sent.

# BUG:TODO: Need to change configuration

FFMPEG = "ffmpeg" # FFMPEG executable. Defaults to what is found in $PATH. Can be an absolute or relative file path.
STREAM_PLACEHOLDER = ":)" # The message that will be sent when streaming. This is needed as a placeholder text so that the initial streaming message is not empty. This can be anything as long as it is not empty, and not more than 2000 characters. It usually doesn't appear for more than half a second.

"""VERY ADVANCED. IGNORE IF NOT CONCERNED."""

ALLOWED_INTERACTIONS = [ChannelType.private_thread, ChannelType.text, TextChannel, ChannelType.private_thread] # What text channels the bot is allowed to talk in. Even if modifying source code, I do NOT recommend changing this.
ALLOW_TRACEBACK = False # If a minor error occurs, this determines weather it will be in the traceback or not. This can be overriden in the Exceptions definition in `exceptions.py` (log_error param, bool only)
GUILD_CONFIG_KEYS = {
    "speed": VOICE_SPEEDUP_MULTIPLIER,
    "timezone": TIMEZONE,
    "voice": True,
    "voice-keyword": LISTENING_KEYWORD,
    "allow-voice": True
} # Default values for guild configurations
DATETIME_TZ = _pytz.timezone(TIMEZONE) # This cannot change AT ALL if you want time systems to work.

"""Generic Types (Do not edit, no matter what. Unless you foundationally change how this bot work. Which, I think you wouldn't do!)"""

InteractableChannel = TextChannel | Thread

