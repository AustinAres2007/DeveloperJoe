import discord
from discord.ext.commands import Cog

from joe import DeveloperJoe
from sources import (
    guildconfig, 
    chat, 
    config, 
    exceptions
)
from sources.common import (
    commands_utils
)

class Voice(Cog):
    def __init__(self, client):
        self.client: DeveloperJoe = client
        print(f"{self.__cog_name__} Loaded")
    
    @discord.app_commands.command(name="speed", description="Set your bots voice speed multiplier for the server.")
    @discord.app_commands.check(commands_utils.in_correct_channel)
    async def set_speed(self, interaction: discord.Interaction, speed: float):
        if guild := commands_utils.assure_class_is_value(interaction.guild, discord.Guild):
            if not speed < 1.0:
                guildconfig.edit_guild_config(guild, "speed", speed)
                await interaction.response.send_message(f"Changed voice speed to {speed}")
            else:
                await interaction.response.send_message("You cannot set the bots speaking speed below 1.0.")
    
    @discord.app_commands.command(name="shutup", description=f"If you have a {config.BOT_NAME} voice chat and you want it to stop talking a reply, execute this command.")
    async def shutup_reply(self, interaction: discord.Interaction):
        member: discord.Member = commands_utils.assure_class_is_value(interaction.user, discord.Member)
        default_chat = self.client.get_default_conversation(member)
        if default_chat and isinstance(default_chat, chat.DGVoiceChat):
            default_chat.stop_speaking()
            return await interaction.response.send_message(f"I have shut up.")
        elif default_chat:
            raise exceptions.ChatIsTextOnly(default_chat)
        else:
            raise exceptions.UserDoesNotHaveChat(str(default_chat))

    @discord.app_commands.command(name="pause", description="Paused the bots voice reply.")
    async def pause_reply(self, interaction: discord.Interaction):
        member: discord.Member = commands_utils.assure_class_is_value(interaction.user, discord.Member)
        default_chat = self.client.get_default_conversation(member)
        
        if default_chat and isinstance(default_chat, chat.DGVoiceChat):
            default_chat.pause_speaking()
            return await interaction.response.send_message(f"I have paused my reply.")
        elif default_chat:
            raise exceptions.ChatIsTextOnly(default_chat)
        else:
            raise exceptions.UserDoesNotHaveChat(str(default_chat))
    
    @discord.app_commands.command(name="resume", description="Resues the bots voice reply.")
    async def resume_reply(self, interaction: discord.Interaction):
        member: discord.Member = commands_utils.assure_class_is_value(interaction.user, discord.Member)
        default_chat = self.client.get_default_conversation(member)
        
        if default_chat and isinstance(default_chat, chat.DGVoiceChat):
            default_chat.resume_speaking()
            return await interaction.response.send_message("Speaking...")
        elif default_chat:
            raise exceptions.ChatIsTextOnly(default_chat)
        else:
            raise exceptions.UserDoesNotHaveChat(str(default_chat))
        
async def setup(client):
    await client.add_cog(Voice(client))