from . import config

"""Error reply texts."""

NONE = None
GENERIC_ERROR = "Unknown error, contact administrator."

class ConversationErrors:
    """Errors pertaining to general conversations."""

    NO_CONVO = f"You either do not have a conversation with {config.BOT_NAME}, or the provided name does not match any chats you currently have."
    NO_CONVOS = "You do not have any conversations."
    HAS_CONVO = "There is already a conversation with the specified name."
    CANNOT_CONVO = f"""You cannot interact with {config.BOT_NAME} inside this channel. You may only interact with {config.BOT_NAME} in 
    a server text channel, A private server thread (Only two users, you and {config.BOT_NAME}) or in Direct Messages."""
    NO_CONVO_WITH_NAME = "No conversation with the specified name."
    CONVO_LIMIT = f"You cannot start anymore than {config.CHATS_LIMIT} chats."
    CONVO_NEEDED_NAME = "If you have any more than 1 chat, you must chose a name."
    ALREADY_PROCESSING_CONVO = f"{config.BOT_NAME} is already processing a request for you."

    CONVO_TOKEN_LIMIT = "You have reached your maximum conversation length. I have disabled your chat. You may still export and save it."
    CONVO_CLOSED = "The chat selected has been closed. This is because you have reached the conversation limit. You can still export and save this chat. Please start another if you wish to keep talking."
    CONVO_CANNOT_TALK = "We cannot interact here. You must be in a discord server channel to make commands. (No stages, private direct messages)"
    CANNOT_STOP_IN_CHANNEL = "You cannot do /stop in the thread created by your conversation ({})"
    CHANNEL_DOESNT_EXIST = 'Channel: "{}" pertaining to "{}" from conversation "{}" belonging to user "{}" no longer exists.'
    TEXT_ONLY_CONVO_TYPE = "You only have a text chat."
    
class VoiceConversationErrors:
    """Errors pertaining to spoken conversation."""
    NOT_SPEAKING = "I am not speaking."
    NOT_IN_CHANNEL = "I am not in your voice channel."
    USER_NOT_IN_CHANNEL = "You are not in a voice channel."
    IS_SPEAKING = "I am currently speaking."
    TEXT_ONLY_CHAT = "This chat is text only."
    NO_FFMPEG = "The bot owner does not currently have voice features enabled."
    NO_COQUI = "The bot owner does not have this voice model installed."
    IS_PROCESSING_VOICE = "I am still processing / playing your last voice request."
    VOICE_IS_LOCKED = "This discord server has disabled voice abilities."
    
class UserErrors:
    """Errors pertaining to user status."""

    INCORRECT_USER_TYPE = "{} is not a member of {}."

class GptErrors:
    """Errors pertaining to the OpenAI / GPT Servers."""

    GPT_CONTENT_FILTER = "You have asked a query that flagged GPT's content filter. Do not ask the same query or anything like it again."
    GPT_PORTAL_ERROR = "Invalid command from OpenAI Gateway server."

class HistoryErrors:
    """Errors pertaining to the history database / incorrect parameters."""
    INVALID_HISTORY_ID = "Input a valid ID."
    HISTORY_DOESNT_EXIST = "No history with the specified name."
    HISTORY_EMPTY = "No chat history."
    HISTORY_NOT_USERS = "This saved chat history is private."

class ModelErrors:
    """Errors pertaining to the model lock list."""
    GUILD_NOT_IN_DATABASE = "{} does not exist within database."
    GUILD_IN_MODEL_DATABASE = "Guild with specified ID has already been registered."
    MODEL_LOCKED = "You do not have the sufficient permissions to use the selected model."
    MODEL_NOT_IN_DATABASE = '"{}" model does not exist within the {} lock list. You can add models to the lock list with /lock.'