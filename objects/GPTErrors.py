from . import GPTConfig

NONE = None
GENERIC_ERROR = "Unknown error, contact administrator."

class ConversationErrors:
    NO_CONVO = f"You either do not have a conversation with {GPTConfig.BOT_NAME}, or the provided name does not match any chats you currently have."
    HAS_CONVO = "There is already a conversation with the specified name."
    CANNOT_CONVO = f"""You cannot interact with {GPTConfig.BOT_NAME} inside this channel. You may only interact with {GPTConfig.BOT_NAME} in 
    a server text channel, A private server thread (Only two users, you and {GPTConfig.BOT_NAME}) or in Direct Messages."""
    NO_CONVO_WITH_NAME = "No conversation with the specified name."
    CONVO_LIMIT = f"You cannot start anymore than {GPTConfig.CHATS_LIMIT} chats."
    CONVO_NEEDED_NAME = "If you have any more than 1 chat, you must chose a name."
    ALREADY_PROCESSING_CONVO = f"{GPTConfig.BOT_NAME} is already processing a request for you."

class HistoryErrors:
    INVALID_HISTORY_ID = "Input a valid ID."
    HISTORY_DOESNT_EXIST = "No history with the specified name."
    HISTORY_EMPTY = "No chat history."
