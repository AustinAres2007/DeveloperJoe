from __future__ import annotations
import logging

from discord import TextChannel, Thread, TextChannel

from . import (
    voice_checks,
)
TIMEZONE = "UTC" # Global timezone of the bot. Can be overridden per guild config settings.

"""ADVANCED. SOURCE CODE EDITORS ONLY"""
    
GPT_REQUEST_TIMEOUT = 180 # Any less than 30 and the bot is very lightly to crash
QUERY_TIMEOUT = 10 # Timeout for destructive actions.
QUERY_CONFIRMATION = "yes" # What keyword to use for confirmation of destructive actions

STREAM_UPDATE_MESSAGE_FREQUENCY = 10 # When streaming a reply, this dictates every set amount of chunks to update the message. Any less that 10 and it will lag.
CHATS_LIMIT = 14 # How many chats a user can have at one time. This cannot be more than 14.
CHARACTER_LIMIT = 2000 # Do NOT put this anywhere over 2000. If you do, the bot will crash if a long message is sent.

FINAL = False # This does nothing. Just indicates if the current version of the bot is the final revision. You may delete this.
VERSION = "1.4.8-RC" 
# Current bot version. ("A" at the end means near final release, as you go further down the alphabet, the further away from final release. Example; "Z" means it is very far from final release version. No letter means it is the final release)
# If it is "ARC" that means it is a release-candidate. The "A" refering to the logic above and "RC" meaning release-candidate.
# It's really cool to have your own custom version scheme isn't it? But to others it is probably very confusing and unnessersary.

LOGGER_LEVEL = logging.ERROR # Logger level. By default it is `logging.ERROR` during betas it might be `logging.DEBUG`
DATABASE_VERSION = "1.0.3" # Database version. If bigger than current, the database file will be updated.
DATABASE_EXTENSION = "db" # File extension of the local database file. Can also be sqlite3
DATABASE_FILENAME = "dg_database" # Name of the database file.
DATABASE_FILE = f"dependencies/{DATABASE_FILENAME}.{DATABASE_EXTENSION}" # Where the SQLite3 Database file is located. (Reletive)
DEVELOPERJOE_THUMBNAIL_URL = "https://i.imgur.com/SgdL99Y.png"

TOKEN_FILE = "dependencies/api-keys.yaml" # Where the API keys for Discord and OpenAI are located. (Reletive)
WELCOME_FILE = "dependencies/tutorial.md" # Where the introduction / welcome text is located. (Reletive)
ADMIN_FILE = "dependencies/admin-tutorial.md" # Where the admin introduction / welcome text is located. (Reletive)
CONFIG_FILE = "bot-config.yaml" # Where the client-configuration file is located (Reletive)
LOG_FILE = "misc/bot_log.log" # Where the bots log is located (Reletive)

FFMPEG = voice_checks._get_voice_paths("ffmpeg", False) # FFMPEG executable. Can be an absolute or relative file path. Required for voice services.
FFPROBE = voice_checks._get_voice_paths("ffprobe", False) # FFPROBE executable. Can be an absolute or relative file path. Required for voice services.
LIBOPUS = voice_checks._get_voice_paths("opus", True) # Libopus shared library. Can be an absolute or relative file path. Required for voice services.

STREAM_PLACEHOLDER = "Loading.." # The message that will be sent when streaming. This is needed as a placeholder text so that the initial streaming message is not empty. This can be anything as long as it is not empty, and not more than 2000 characters. It usually doesn't appear for more than half a second.

"""VERY ADVANCED. IGNORE IF NOT CONCERNED."""

ALLOW_TRACEBACK = False # If a minor error occurs, this determines weather it will be in the traceback or not. This can be overriden in the Exceptions definition in `exceptions.py` (log_error param, bool only)

"""Generic Types (Do not edit, no matter what. Unless you foundationally change how this bot work. Which, I think you wouldn't do!)"""

InteractableChannel = TextChannel | Thread

"""Default config, do not change"""

default_config_keys = {
    "bot_name": "DeveloperJoe",
    "bug_report_channel": 0,
    "status_type": 2,
    "status_text": "/help and answering lifes biggest questions.",
    "status_scrolling_change_interval": 10,
    "enable_status_scrolling": False,
    "status_scrolling_options": {"/help and different peoples!": 2, "/help and documentries.": 3, "/help and math tournaments!": 5, "/help and monoply :(": 0},
    "default_ai_model": "gpt-3.5-turbo-16k",
    "voice_speedup_multiplier": 1.3,
    "voice_volume": 1.0,
    "allow_voice": True,
    "backup_upon_start": False
}

default_api_keys = {
    "discord_api_key": "Put Discord Token Here!",
    "openai_api_key": "Put OpenAI API Key (Token) here!",
    "google_api_key": "Put Google API Key here! (Optional)"
}

default_permission_keys = {}
