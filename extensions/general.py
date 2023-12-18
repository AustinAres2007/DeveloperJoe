import discord

from discord.ext.commands import Cog as _Cog

from sources import (
    models,
    modelhandler
)
from sources.common import (
    commands_utils
)
from joe import DeveloperJoe

class General(_Cog):
    def __init__(self, _client: DeveloperJoe):
        self.client: DeveloperJoe  = _client
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
        member = commands_utils.assure_class_is_value(interaction.user, discord.Member)
        embed = self.client.get_embed("Registered AI Models")
        
        for model in models.registered_models.values():
            embed.add_field(name=model.display_name, value=f"{model.description} | Enabled = {model.enabled} | Can you use this model = {modelhandler.member_has_model_permissions(member, type(model))}", inline=False)
        await interaction.response.send_message(embed=embed)
        
async def setup(client: DeveloperJoe):
    await client.add_cog(General(client))
