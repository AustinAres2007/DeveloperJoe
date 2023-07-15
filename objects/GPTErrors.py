import GPTConfig

NONE = None
GENERIC_ERROR = "Unknown error, contact administrator."

class ConversationErrors:
    NO_CONVO = "You do not have any conversation with DeveloperJoe. Do /start to do such."
    HAS_CONVO = "You already have a chat with the specified name."
    CANNOT_CONVO = """You cannot interact with DeveloperJoe inside this channel. You may only interact with DeveloperJoe in 
    a server text channel, A private server thread (Only two users, you and DeveloperJoe) or in Direct Messages."""
    NO_CONVO_WITH_NAME = "No conversation with the specified name."
    INVALID_NAME = "If you have any more than 1 chat, you must chose a name."
    TOO_MANY_CONVOS = f"You may only have {GPTConfig.CHATS_LIMIT} chats."
    
class HistoryErrors:
    INVALID_HISTORY_ID = "Input a valid ID."
    HISTORY_DOESNT_EXIST = "No history with the specified name."