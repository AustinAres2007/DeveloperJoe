from signal import default_int_handler
import discord
from discord.ext.commands import Cog

from joe import DeveloperJoe
from sources import (
    confighandler, 
    chat, 
    exceptions,
    errors
)
from sources.common import (
    commands_utils
)

class Voice(Cog):
    def __init__(self, _client: DeveloperJoe):
        self.client = _client
        print(f"{self.__cog_name__} Loaded")
    
    voice_group = discord.app_commands.Group(name="voice", description="Command group for voice commands.")
    media_group = discord.app_commands.Group(name="media", description="Command group for managing media.")
    
    @voice_group.command(name="speed", description="Set your bots voice speed multiplier for the server.")
    @discord.app_commands.check(commands_utils.in_correct_channel)
    async def set_speed(self, interaction: discord.Interaction, speed: float | None=None):
        if guild := commands_utils.assure_class_is_value(interaction.guild, discord.Guild):
            if speed == None:
                await interaction.response.send_message(f"Voice speed is {confighandler.get_guild_config_attribute(guild, 'voice-speed')}")
            elif not speed < 1.0 and speed < 4.0: # Arbituary limit on 4.0, if anything less than 1 it becomes glitchy if I remember correctly
                confighandler.edit_guild_config(guild, "voice-speed", speed)
                await interaction.response.send_message(f"Changed voice speed to {speed}.")
            else:
                await interaction.response.send_message("You cannot set the bots speaking speed below 1.0 or more than 4.0.")
    
    @voice_group.command(name="volume", description="Sets bots voice volume. Use values between 0.0 - 1.0")
    @discord.app_commands.check(commands_utils.in_correct_channel)
    async def set_volume(self, interaction: discord.Interaction, volume: float | None=None):
        if guild := commands_utils.assure_class_is_value(interaction.guild, discord.Guild):
            if volume != None:
                confighandler.edit_guild_config(guild, "voice-volume", volume)
                return await interaction.response.send_message(f"Changed voice volume to {volume}.")
            await interaction.response.send_message(f"Voice volume is {confighandler.get_guild_config_attribute(guild, 'voice-volume')}.")
            
    @media_group.command(name="skip", description="If talking, this will stop me from talking. Unlike /media pause, this is not reversible.")
    async def shutup_reply(self, interaction: discord.Interaction):
        member: discord.Member = commands_utils.assure_class_is_value(interaction.user, discord.Member)
        default_chat = self.client.get_default_conversation(member)
        
        if default_chat and isinstance(default_chat, chat.DGVoiceChat):
            try:
                await default_chat.stop_speaking()
                return await interaction.response.send_message(f"I have shut up.")
            except:
                pass
        elif default_chat:
            raise exceptions.VoiceError(errors.VoiceConversationErrors.TEXT_ONLY_CHAT)
        else:
            raise exceptions.ConversationError(errors.ConversationErrors.NO_CONVO)

    @media_group.command(name="pause", description="Paused the bots voice reply.")
    async def pause_reply(self, interaction: discord.Interaction):
        member: discord.Member = commands_utils.assure_class_is_value(interaction.user, discord.Member)
        default_chat = self.client.get_default_conversation(member)
        
        if default_chat and isinstance(default_chat, chat.DGVoiceChat):
            await default_chat.pause_speaking()
            return await interaction.response.send_message(f"I have paused my reply.")
        elif default_chat:
            raise exceptions.VoiceError(errors.VoiceConversationErrors.TEXT_ONLY_CHAT)
        else:
            raise exceptions.ConversationError(errors.ConversationErrors.NO_CONVO)
    
    @media_group.command(name="resume", description="Resues the bots voice reply.")
    async def resume_reply(self, interaction: discord.Interaction):
        member: discord.Member = commands_utils.assure_class_is_value(interaction.user, discord.Member)
        default_chat = self.client.get_default_conversation(member)
        
        if default_chat and isinstance(default_chat, chat.DGVoiceChat):
            await default_chat.resume_speaking()
            return await interaction.response.send_message("Speaking...")
        elif default_chat:
            raise exceptions.VoiceError(errors.VoiceConversationErrors.TEXT_ONLY_CHAT)
        else:
            raise exceptions.ConversationError(errors.ConversationErrors.NO_CONVO)
    
    @voice_group.command(name="leave", description="Leaves the voice channel the bot is currently in.")
    async def leave_vc(self, interaction: discord.Interaction):
        member: discord.Member = commands_utils.assure_class_is_value(interaction.user, discord.Member)
        bot_voice: discord.VoiceClient | None = discord.utils.get(self.client.voice_clients, guild=member.guild) # type: ignore because all single instances are `discord.VoiceClient`
        
        member_convos = self.client.get_all_user_voice_conversations(member).values()
        
        if isinstance(bot_voice, discord.VoiceClient):
            
            for convo in member_convos:
                try:
                    convo.cleanup_voice()
                except exceptions.VoiceError:
                    continue
                
            await bot_voice.disconnect()
            bot_voice.cleanup() # XXX: We gonna get the stupid ass stdin error AGAIN?
            
            return await interaction.response.send_message(f"{getattr(self.client.user, "display_name", "Bot")} has left your voice channel.")
        return await interaction.response.send_message("I am not in a voice channel.")

async def setup(client):
    await client.add_cog(Voice(client))
