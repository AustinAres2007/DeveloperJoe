import discord as discord

from discord.ext.commands import Cog as _Cog
from joe import DeveloperJoe

from sources import (
    guildconfig,
    config
)
from sources.common import (
    commands_utils,
    
)

class Configuration(_Cog):
    def __init__(self, _client: DeveloperJoe):
        self.client = _client
        print(f"{self.__cog_name__} Loaded")

    @discord.app_commands.command(name="config", description="View this discord servers configuration.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def guild_config(self, interaction: discord.Interaction):
        if guild := commands_utils.assure_class_is_value(interaction.guild, discord.Guild):
            
            _config = guildconfig.get_guild_config(guild)
            embed = self.client.get_embed(f"{guild} Configuration Settings")
            
            for c_entry in _config.config_data.items():
                embed.add_field(name=f'Config Option: "{c_entry[0]}"', value=c_entry[1], inline=False)
            
            await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="timezone", description="Changes the bots timezone in this server.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    @discord.app_commands.check(commands_utils.in_correct_channel)
    async def change_tz(self, interaction: discord.Interaction, timezone: str):
        if guild := commands_utils.assure_class_is_value(interaction.guild, discord.Guild):
            if timezone in self.client.__tzs__:
                guildconfig.edit_guild_config(guild, "timezone", timezone)
                return await interaction.response.send_message(f"Changed bots timezone to {timezone}.")
            await interaction.response.send_message(f"Unknown timezone: {timezone}")
    
    @discord.app_commands.command(name="voice", description=f"Configure if users can have spoken {config.BOT_NAME} chats.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    @discord.app_commands.check(commands_utils.in_correct_channel)
    async def config_voice(self, interaction: discord.Interaction, allow_voice: bool):
        if guild := commands_utils.assure_class_is_value(interaction.guild, discord.Guild):
            guildconfig.edit_guild_config(guild, "voice", allow_voice)
            return await interaction.response.send_message(f"Users {'cannot' if allow_voice == False else 'can'} use voice.")
            
    @discord.app_commands.command(name="reset", description=f"Reset this servers configuration back to default.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    @discord.app_commands.check(commands_utils.in_correct_channel)
    async def reset_config(self, interaction: discord.Interaction):
        if guild := commands_utils.assure_class_is_value(interaction.guild, discord.Guild):
            
            confirm = await self.client.get_input(interaction, "Are you sure you want to reset this servers configuration? This cannot be undone unless you remember the current configuration.")
            if confirm.content != config.QUERY_CONFIRMATION:
                return await interaction.followup.send("Cancelled action.", ephemeral=False)
                
            guildconfig.reset_guild_config(guild)
            return await interaction.followup.send("Reset this server configuration keys. You may view them with /config.")
            
        
async def setup(client):
    await client.add_cog(Configuration(client))
