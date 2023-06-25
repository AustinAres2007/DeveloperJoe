NONE = None
GENERIC_ERROR = "Unknown error, contact administrator."

class ConversationErrors:
    NO_CONVO = "You do not have a conversation with DeveloperJoe. Do /start to do such."
    HAS_CONVO = 'You already have an ongoing conversation with DeveloperJoe. To reset, do "/stop."'
    CANNOT_CONVO = """You cannot interact with DeveloperJoe inside this channel. You may only interact with DeveloperJoe in 
    a server text channel, A private server thread (Only two users, you and DeveloperJoe) or in Direct Messages."""
    
class HistoryErrors:
    INVALID_HISTORY_ID = "Input a valid ID."
    HISTORY_DOESNT_EXIST = "No history with the specified name."