"""General functions that assist the bot general function."""

from colorama import Fore

__all__ = [
    "warn_for_error"
]

def warn_for_error(text: str) -> None:
    """Prints a red formatted text warning to the end client.

    Args:
        text (str): _description_ The text to warn.
    """
    print(Fore.LIGHTYELLOW_EX + "\nNON-LETHAL WARNING: " + Fore.YELLOW + f"{text}\n" + Fore.WHITE)
    
def send_affirmative_text(text: str) -> None:
    """Prints green-formatted text to the end client.

    Args:
        text (str): _description_ The text to print.
    """
    print(Fore.GREEN + f"\n{text}\n" + Fore.WHITE)
