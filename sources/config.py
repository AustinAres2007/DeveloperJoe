import datetime as _datetime
from discord import ChannelType as _ChannelType
from discord import ActivityType as _ActivityType
from discord.app_commands import Choice as _Choice
from discord import TextChannel as _TextChannel

from . import models

# User Configuration

BOT_NAME = "DeveloperJoe" # Name of the bot when describing commands or help.
STATUS_TYPE = _ActivityType.listening # The "Playing" or "Listening to" part of the bot's status
STATUS_TEXT = "/help AND answering lifes biggest questions." # Bot's status when activated
DEFAULT_GPT_MODEL: models.GPTModelType = models.GPT4 # gpt-4, or gpt-3.5-turbo

VOICE_SPEEDUP_MULTIPLIER = 1.167 # How fast you want the default text-to-speach model to talk. (1 = default, quite slow. 2 = Quite fast)
ALLOW_VOICE = True # Weather voice support is enabled. It is by default, and will require additional setup if you do not have FFMPEG installed. It is easy to do so.

TIMEZONE = _datetime.timezone.utc # What timezone to use (UTC by default)

# ADVANCED

GPT_REQUEST_TIMEOUT = 180 # Any less than 30 and the bot is very lightly to crash
QUERY_TIMEOUT = 10 # Timeout for destructive actions.
QUERY_CONFIRMATION = ">y" # What keyword to use for confirmation of destructive actions

STREAM_UPDATE_MESSAGE_FREQUENCY = 10 # When streaming a GPT reply, this dictates every set amount of tokens to update the message. Any less that 10 and it will lag.
CHATS_LIMIT = 20 # How many chats a user can have at one time.
CHARACTER_LIMIT = 2000 # Do NOT put this anywhere over 2000. If you do, the bot will crash if a long message is sent.

FINAL = False # This does nothing. Just indicates if the current version of the bot is the final revision. You may delete this.
DEBUG = True # Debug is ALWAYS True, if set to false, errors will not be logged to misc/bot_log.log
VERSION = "1.3.0-L" # Current bot version. ("A" at the end means near final release, as you go further down the alphabet, the further away from final release. Example; "Z" means it is far from final release version)

DATABASE_FILE = "dependencies/dg_database.db" # Where the SQLite3 Database file is located. (Reletive)
TOKEN_FILE = "dependencies/api-keys.key" # Where the API keys for Discord and OpenAI are located. (Reletive)
WELCOME_FILE = "dependencies/tutorial.md" # Where the introduction / welcome text is located. (Reletive)
ADMIN_FILE = "dependencies/admin-tutorial.md" # Where the admin introduction / welcome text is located. (Reletive)

MODEL_CHOICES: list[_Choice] = [
    _Choice(name="GPT 3 - Davinci", value="text-davinci-003"),
    _Choice(name="GPT 3.5 - Turbo", value="gpt-3.5-turbo"), 
    _Choice(name="GPT 4", value="gpt-4")
] # What models of GPT are avalible to use, you can chose any that exist, but keep in mind that have to follow the return format of GPT 3 / 4. If not, the bot will crash immediately.
REGISTERED_MODELS = {
    "gpt-4": models.GPT4,
    "gpt-3.5-turbo": models.GPT3Turbo,
    "text-davinci-003": models.GPT3Davinci
} # These keys should corrolate with the value parameter of MODEL_CHOICES, and the value should inherit from models.GPTModel
ALLOWED_INTERACTIONS = [_ChannelType.private_thread, _ChannelType.text, _TextChannel] # What text channels the bot is allowed to talk in. Even if modifying source code, I do NOT recommend changing this.
ALLOW_TRACEBACK = True # If a minor error occurs, this determines weather it will be in the traceback or not. This can be overriden in the Exceptions definition in `exceptions.py` (log_error param, bool only)