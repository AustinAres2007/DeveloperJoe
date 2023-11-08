from __future__ import annotations

from discord import ChannelType, TextChannel, Thread, TextChannel
from discord.app_commands import Choice as _Choice

from .voice_checks import _get_voice_paths

"""ADVANCED. SOURCE CODE EDITORS ONLY"""
    
GPT_REQUEST_TIMEOUT = 180 # Any less than 30 and the bot is very lightly to crash
QUERY_TIMEOUT = 10 # Timeout for destructive actions.
QUERY_CONFIRMATION = ">y" # What keyword to use for confirmation of destructive actions

STREAM_UPDATE_MESSAGE_FREQUENCY = 10 # When streaming a GPT reply, this dictates every set amount of tokens to update the message. Any less that 10 and it will lag.
CHATS_LIMIT = 14 # How many chats a user can have at one time. This cannot be more than 14.
CHARACTER_LIMIT = 2000 # Do NOT put this anywhere over 2000. If you do, the bot will crash if a long message is sent.

FINAL = True # This does nothing. Just indicates if the current version of the bot is the final revision. You may delete this.
VERSION = "1.3.7" # Current bot version. ("A" at the end means near final release, as you go further down the alphabet, the further away from final release. Example; "Z" means it is very far from final release version. No letter means it is the final release)

DATABASE_FILE = "dependencies/dg_database.db" # Where the SQLite3 Database file is located. (Reletive)
TOKEN_FILE = "dependencies/api-keys.key" # Where the API keys for Discord and OpenAI are located. (Reletive)
WELCOME_FILE = "dependencies/tutorial.md" # Where the introduction / welcome text is located. (Reletive)
ADMIN_FILE = "dependencies/admin-tutorial.md" # Where the admin introduction / welcome text is located. (Reletive)
CONFIG_FILE = "bot-config.yaml" # Where the client-configuration file is located (Reletive)

MODEL_CHOICES: list[_Choice] = [
    _Choice(name="GPT 3.5 - Turbo", value="gpt-3.5-turbo"),
    _Choice(name="GPT 4", value="gpt-4")
] # What models of GPT are avalible to use, you can chose any that exist, but keep in mind that have to follow the return format of GPT 3 / 4. If not, the bot will crash immediately after a query is sent.

# TODO: Need to change configuration

FFMPEG = _get_voice_paths("ffmpeg", False) # FFMPEG executable. Can be an absolute or relative file path. Required for voice services.
FFPROBE = _get_voice_paths("ffprobe", False) # FFPROBE executable. Can be an absolute or relative file path. Required for voice services.
LIBOPUS = _get_voice_paths("opus", True)

STREAM_PLACEHOLDER = ":)" # The message that will be sent when streaming. This is needed as a placeholder text so that the initial streaming message is not empty. This can be anything as long as it is not empty, and not more than 2000 characters. It usually doesn't appear for more than half a second.

"""VERY ADVANCED. IGNORE IF NOT CONCERNED."""

ALLOWED_INTERACTIONS = [ChannelType.private_thread, ChannelType.text, TextChannel, ChannelType.private_thread] # What text channels the bot is allowed to talk in. Even if modifying source code, I do NOT recommend changing this.
ALLOW_TRACEBACK = False # If a minor error occurs, this determines weather it will be in the traceback or not. This can be overriden in the Exceptions definition in `exceptions.py` (log_error param, bool only)

"""Generic Types (Do not edit, no matter what. Unless you foundationally change how this bot work. Which, I think you wouldn't do!)"""

InteractableChannel = TextChannel | Thread

"""Default config, do not change"""

default_config_keys = {
    "bot_name": "DeveloperJoe",
    "bug_report_channel": 0,
    "status_type": 2,
    "status_text": "/help and answering lifes biggest questions.",
    "default_gpt_model": "gpt-3.5-turbo",
    "listening_keyword": "assistant",
    "listening_timeout": 2.5,
    "voice_speedup_multiplier": 1.17,
    "allow_voice": True,
    "timezone": "UTC",
    "starting_query": "Please give a short and formal introduction (MUST be under 1500 characters) of yourself (ChatGPT) what you can do and limitations."
}

