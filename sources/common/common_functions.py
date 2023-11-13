"""General functions that assist the bot general function."""

from colorama import Fore

__all__ = [
    "send_fatal_error_warning",
    "warn_for_error",
    "send_affirmative_text"
]

def send_fatal_error_warning(text: str) -> None:
    """Prints a red formatted text, indicating distress to the end client. 

    Args:
        text (str): _description_
    """
    print(Fore.LIGHTRED_EX + "\nLETHAL WARNING: " + Fore.RED + f"{text}\n" + Fore.WHITE)
    
def warn_for_error(text: str) -> None:
    """Prints a yellow formatted text warning to the end client.

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

def send_info_text(text: str) -> None:
    """Prints light cyan text to the end client.

    Args:
        text (str): The text to print.
    """
    print(Fore.LIGHTCYAN_EX + "Info:  " + Fore.CYAN + f"{text}\n" + Fore.WHITE)


