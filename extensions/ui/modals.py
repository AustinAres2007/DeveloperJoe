import discord
from discord import ui

class TestModal(ui.Modal, title="Test"):
    name = ui.TextInput(label="Chat name: ")