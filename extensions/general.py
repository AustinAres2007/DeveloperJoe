from click import command
import discord

from discord.ext.commands import Cog as _Cog

from sources import (
    models,
    confighandler
)
from sources.common import (
    commands_utils,
    developerconfig
)

class General(_Cog):
    def __init__(self, _client):
        self.client = _client
        print(f"{self.__cog_name__} Loaded")

    @discord.app_commands.command(name="help", description="Lists avalible commands")
    async def help_command(self, interaction: discord.Interaction):    
        text = ""
        
        for name, cog in self.client.cogs.items():
            if not cog.get_app_commands():
                continue
            
            text +=f"\n 💻 {name} 💻 \n\n"
            
            for i, command in enumerate(cog.walk_app_commands()):
                
                if isinstance(command, discord.app_commands.Command):
                    if command.parent == None:
                        text += f"/{command.name} - {command.description}\n"
                    
                elif isinstance(command, discord.app_commands.Group):
                    text += f"{"\n" if i != 0 else ""}/{command.name} :: {command.description}\n"
                    
                    for subcommand in command.commands:
                        if isinstance(subcommand, discord.app_commands.Command):
                            text += f"/{command.name} {subcommand.name} > {subcommand.description}\n"
        
        await commands_utils.send_regardless(interaction, text)
        
    @discord.app_commands.command(name="times", description="Provides a file which contains timezones you can use.")
    async def give_zones(self, interaction: discord.Interaction):
        await interaction.response.send_message(file=commands_utils.to_file_fp("misc/timezones.txt"))
    
    @discord.app_commands.command(name="models", description="Gives a list of models. Not all of them may be usable depending on your permissions.")
    async def get_models(self, interaction: discord.Interaction):
        embed = self.client.get_embed("AI Models")
        model_values = models.registered_models.values()

        [embed.add_field(name=model.display_name, value=commands_utils.true_to_yes(f"{model.description} Stream Text? {model.can_stream} | Art Generation? {model.can_generate_images}"), inline=False) for model in model_values]
        await interaction.response.send_message(embed=embed)
    
    @discord.app_commands.command(name="server", description="Lists general information about the server and the servers settings.")
    async def list_server(self, interaction: discord.Interaction):
        guild = commands_utils.assure_class_is_value(interaction.guild, discord.Guild)
        embed = discord.Embed(title=interaction.guild, color=discord.Color.from_rgb(20, 31, 17))
        default_embed_fields = {"inline": False}
        
        embed_fields = [
            {"name": f"{guild.name} Member Count :1234:", "value": str(guild.member_count), **default_embed_fields},
            {"name": f"{guild.name} Server ID :wrench:", "value": str(guild.id), **default_embed_fields},
            {"name": f"{guild.name} Owner :gun:", "value": str(guild.owner), **default_embed_fields},
            {"name": f"{guild.name} Prefered Language :om_symbol:", "value": str(guild.preferred_locale), **default_embed_fields},
            {"name": f"{guild.name} Default AI Model :robot:", "value": confighandler.GuildConfigAttributes.get_guild_model(guild).display_name, **default_embed_fields},
            {"name": f"{guild.name} Voice Enabled :question:", "value": confighandler.GuildConfigAttributes.get_voice_status(guild), **default_embed_fields},
            {"name": f"{guild.name} Voice Volume :speaker:", "value": str(confighandler.GuildConfigAttributes.get_voice_volume(guild)), **default_embed_fields},
            {"name": f"{guild.name} Voice Speed :speaking_head:", "value": str(confighandler.GuildConfigAttributes.get_voice_speed(guild)), **default_embed_fields}
        ]
        embed.set_thumbnail(url=getattr(guild.icon, "url", developerconfig.DEVELOPERJOE_THUMBNAIL_URL))
        embed._fields = embed_fields
        
        await interaction.response.send_message(embed=embed)
        
async def setup(client):
    await client.add_cog(General(client))
