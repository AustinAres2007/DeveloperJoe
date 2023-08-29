import discord

from discord.ext.commands import Cog as _Cog

from sources import (
    models
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
        embed = self.client.get_embed(f"{developerconfig.BOT_NAME} Commands")
        get_name = lambda cmd: cmd.name

        for name, cog in self.client.cogs.items():
            if not cog.get_app_commands():
                continue
            embed.add_field(name=f" 💻 {name} 💻 ", value="commands", inline=False)

            for command in cog.walk_app_commands():
                if isinstance(command, discord.app_commands.Command):
                    params = ", ".join(list(map(get_name, command.parameters)))
                    embed.add_field(name=f"/{command.name}", value=f'{command.description} | /{command.name} {params}', inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=False)


        
    @discord.app_commands.command(name="times", description="Provides a file which contains timezones you can use.")
    async def give_zones(self, interaction: discord.Interaction):
        await interaction.response.send_message(file=commands_utils.to_file_fp("misc/timezones.txt"))
    
    @discord.app_commands.command(name="models", description="Gives a list of models. Not all of them may be usable depending on your permissions.")
    async def get_models(self, interaction: discord.Interaction):
        embed = self.client.get_embed("GPT Models")
        [embed.add_field(name=model.display_name, value=model.description, inline=False) for model in models.registered_models.values()]
        await interaction.response.send_message(embed=embed)
        
async def setup(client):
    await client.add_cog(General(client))
