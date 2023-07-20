import datetime as _datetime
from discord import ActivityType

# User Configuration

BOT_NAME = "DeveloperJoe"
STATUS_TYPE = ActivityType.listening # The "Playing" or "Listening to" part of the bot's status
STATUS_TEXT = "/help AND answering lifes biggest questions." # Bot's status when activated
DEFAULT_GPT_MODEL = "gpt-4" # gpt-4, or gpt-3.5-turbo

TIMEZONE = _datetime.timezone.utc # What timezone to use (UTC by default)

# ADVANCED

FINAL = True # This does nothing. Just indicates if the current version of the bot is the final revision. You may delete this.
DEBUG = True # Debug is ALWAYS True, if set to false, errors will not be logged to misc/bot_log.log
QUERY_TIMEOUT = 10
QUERY_CONFIRMATION = ">y"

GPT_REQUEST_TIMEOUT = 180

STREAM_UPDATE_MESSAGE_FREQUENCY = 10
CHATS_LIMIT = 20
CHARACTER_LIMIT = 2000 # DO NOT CHANGE THIS. YOU MAY SUBTRACT FROM IT, DO NOT ADD.
VERSION = "1.2.4"
TOKEN_FILE = "dependencies/api-keys.key"