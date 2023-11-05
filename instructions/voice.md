# In-depth Voice Setup

This tutorial will go into how to setup voice. This is covered in the `README.md` file, but here I will cover is more extensively and some trouble-shooting guides.

# Warnings

Using voice and broadcasting the TTS messages does take extra resources. Especially if you plan to use voice recogniton. Please make sure you have sufficient server / computer specs. Best way to find out is to just test privately. Play around with some commands, find what you like and see if it has any problems.

# Compatibility

This bot has been programmed on a macOS laptop (M1 Pro) so macOS support is always coming first, but linux is also supported. Windows has limited support, voice libraries are not provided nor have I programmed for them. An install and run script is provided for Windows, but I do not update it and do not want to support it. 

Tested on:

macOS (M1 Pro, macOS Sonoma) *VOICE*
Linux (Virtualisation with M1 Pro ARM, Debian 11) *VOICE*
Windows (Intel i3, Windows 10) and (Virtualisation with M1 Pro ARM, Windows 11) *NO VOICE*

# Installation

Go to this [GitHub repository](https://github.com/AustinAres2007/developerjoe-downloads/releases) for the voice libraries and download the 3 files for your respective machines. Simply drag and drop them into the "voice" folder. 
If you are on Linux, you are done. Congratulations.

## macOS Extra Steps

Due to Apple's cautious nature, the files are not trusted by your system. To make them "trusted" Do the following steps:

1. Run the bot with the voice libraries inside the "voice" folder. You will get a warning saying they made by an unidentified developer. Discard this warning.
2. Shut down the bot after running and recieving the warning, go to the "voice" folder.
3. Open each library with the terminal. Right Click > Open With > Terminal. You will get a message saying "Are you sure?" in some words. Click "Open". Do this with each of the 3 voice library files.

All 3 libraries are safe to use.

After that. Simply run the bot and you are done. Congratulations.

## What if I skip the macOS Extra Steps?

The bot will still work, and the prompt when you start it will say that voice is enabled. This is true, the files do exist, but the bot will NOT be able to access them due to Apple blocking the library files. If you try this and use voice features without doing the extra steps, when you go to use voice you will get an error saying the files are not trusted.

This is fine, it doesn't break anything but it is annoying.

# Windows Support?

This bot is fully open-source-- voice libraries and all. If you have a little knowledge of Python, how windows DLLs and Executables (exe) files work with different version of windows, please feel free to add support yourself. This is ONLY done in the `sources/common/voice_checks.py` file. It is pretty simple. Yet I do not feel like supporting windows because I hate it and I cannot be bothered.