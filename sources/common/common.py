"""General functions that assist the bot general function."""
import datetime, pytz, colorama
import typing
from typing import Any
import os

import yaml
from . import developerconfig

__all__ = [
    "send_fatal_error_warning",
    "warn_for_error",
    "send_affirmative_text",
    "send_info_text",
    "get_posix"
]

colorama.init()
def send_fatal_error_warning(text: str) -> None:
    """Prints a red formatted text, indicating distress to the end client. 

    Args:
        text (str): _description_
    """
    print(colorama.Fore.LIGHTRED_EX + "\nLETHAL WARNING: " + colorama.Fore.RED + f"{text}\n" + colorama.Fore.WHITE)
    
def warn_for_error(text: str) -> None:
    """Prints a yellow formatted text warning to the end client.

    Args:
        text (str): _description_ The text to warn.
    """
    print(colorama.Fore.LIGHTYELLOW_EX + "\nNON-LETHAL WARNING: " + colorama.Fore.YELLOW + f"{text}\n" + colorama.Fore.WHITE)
    
def send_affirmative_text(text: str) -> None:
    """Prints green-formatted text to the end client.

    Args:
        text (str): _description_ The text to print.
    """
    print(colorama.Fore.GREEN + f"\n{text}\n" + colorama.Fore.WHITE)

def send_info_text(text: str) -> None:
    """Prints light cyan text to the end client.

    Args:
        text (str): The text to print.
    """
    print(colorama.Fore.LIGHTCYAN_EX + "Info:  " + colorama.Fore.CYAN + f"{text}\n" + colorama.Fore.WHITE)

def get_posix():
    """Returns the posix timestamp according to the timezone specified in the config."""
    return int(datetime.datetime.now(tz=pytz.timezone(developerconfig.TIMEZONE)).timestamp())
    


