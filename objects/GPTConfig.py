import datetime as _datetime
from discord import ChannelType
from discord import ActivityType
from discord.app_commands import Choice
from discord import TextChannel

# User Configuration

BOT_NAME = "DeveloperJoe"
STATUS_TYPE = ActivityType.listening # The "Playing" or "Listening to" part of the bot's status
STATUS_TEXT = "/help AND answering lifes biggest questions." # Bot's status when activated
DEFAULT_GPT_MODEL = "gpt-4" # gpt-4, or gpt-3.5-turbo

TIMEZONE = _datetime.timezone.utc # What timezone to use (UTC by default)

# ADVANCED

GPT_REQUEST_TIMEOUT = 180
QUERY_TIMEOUT = 10
QUERY_CONFIRMATION = ">y"

STREAM_UPDATE_MESSAGE_FREQUENCY = 10
CHATS_LIMIT = 20
CHARACTER_LIMIT = 2000 # DO NOT CHANGE THIS. YOU MAY SUBTRACT FROM IT, DO NOT ADD.

FINAL = False # This does nothing. Just indicates if the current version of the bot is the final revision. You may delete this.
DEBUG = True # Debug is ALWAYS True, if set to false, errors will not be logged to misc/bot_log.log
VERSION = "1.2.6-A"

DATABASE_FILE = "dependencies/dg_database.db"
TOKEN_FILE = "dependencies/api-keys.key"
WELCOME_FILE = "dependencies/tutorial.md"
ADMIN_FILE = "dependencies/admin-tutorial.md"

MODEL_CHOICES: list[Choice] = [
    Choice(name="GPT 3 Turbo", value="gpt-3.5-turbo"), 
    Choice(name="GPT 4", value="gpt-4")
]
ALLOWED_INTERACTIONS = [ChannelType.private_thread, ChannelType.text, TextChannel]