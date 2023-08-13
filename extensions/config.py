import discord as discord

from discord.ext.commands import Cog as _Cog
from joe import DeveloperJoe
from sources import (
    utils, 
    guildconfig,
    config
)

class Configuration(_Cog):
    def __init__(self, client):
        self.client: DeveloperJoe = client
        print(f"{self.__cog_name__} Loaded")

    @discord.app_commands.command(name="config", description="View this discord servers configuration.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def guild_config(self, interaction: discord.Interaction):
        if guild := utils.assure_class_is_value(interaction.guild, discord.Guild):
            
            config = guildconfig.get_guild_config(guild)
            embed = self.client.get_embed(f"{guild} Configuration Settings")
            
            for config in config.config_data.items():
                embed.add_field(name=f'Config Option: "{config[0]}"', value=config[1], inline=False)
            
            await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="timezone", description="Changes the bots timezone in this server.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    @discord.app_commands.check(utils.in_correct_channel)
    async def change_tz(self, interaction: discord.Interaction, timezone: str):
        if guild := utils.assure_class_is_value(interaction.guild, discord.Guild):
            if timezone in self.client.__tzs__:
                guildconfig.edit_guild_config(guild, "timezone", timezone)
                return await interaction.response.send_message(f"Changed bots timezone to {timezone}.")
            await interaction.response.send_message(f"Unknown timezone: {timezone}")
    
    @discord.app_commands.command(name="voice", description=f"Configure if users can have spoken {config.BOT_NAME} chats.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    @discord.app_commands.check(utils.in_correct_channel)
    async def config_voice(self, interaction: discord.Interaction, allow_voice: bool):
        if guild := utils.assure_class_is_value(interaction.guild, discord.Guild):
            guildconfig.edit_guild_config(guild, "timezone", allow_voice)
            return await interaction.response.send_message(f"Users {'cannot' if allow_voice == False else 'can'} use voice.")
            
    
async def setup(client):
    await client.add_cog(Configuration(client))
