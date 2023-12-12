import discord

from discord.ext.commands import Cog as _Cog

from sources import (
    models,
    confighandler
)
from sources.common import (
    commands_utils
)

class General(_Cog):
    def __init__(self, _client):
        self.client = _client
        print(f"{self.__cog_name__} Loaded")

    @discord.app_commands.command(name="help", description="Lists avalible commands")
    async def help_command(self, interaction: discord.Interaction):    
        embed = self.client.get_embed(f"{confighandler.get_config('bot_name')} Commands Page 1")
        get_name = lambda cmd: cmd.name
        cmd_len = 1
        
        async def send_embed(_embed: discord.Embed):
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=_embed, ephemeral=False)
            else:
                await interaction.channel.send(embed=_embed) # type: ignore
            
        for name, cog in self.client.cogs.items():
            if not cog.get_app_commands():
                continue
            embed.add_field(name=f" 💻 {name} 💻 ", value="commands", inline=False)

            for i, command in enumerate(cog.walk_app_commands()):
                if isinstance(command, discord.app_commands.Command):
                    cmd_len += 1
                    if cmd_len and cmd_len % 15 == 0:
                        await send_embed(embed)
                        embed = self.client.get_embed(f"{confighandler.get_config('bot_name')} Commands Page {(cmd_len // 15) + 1}")
                        
                    params = ", ".join(list(map(get_name, command.parameters)))
                    embed.add_field(name=f"/{command.name}", value=f'{command.description} | /{command.name} {params}', inline=False)
        else:
            await send_embed(embed)
        
    @discord.app_commands.command(name="times", description="Provides a file which contains timezones you can use.")
    async def give_zones(self, interaction: discord.Interaction):
        await interaction.response.send_message(file=commands_utils.to_file_fp("misc/timezones.txt"))
    
    @discord.app_commands.command(name="models", description="Gives a list of models. Not all of them may be usable depending on your permissions.")
    async def get_models(self, interaction: discord.Interaction):
        embed = self.client.get_embed("GPT Models")
        [embed.add_field(name=model.display_name, value=f"{model.description} | Enabled = {model.enabled}", inline=False) for model in models.registered_models.values()]
        await interaction.response.send_message(embed=embed)
    
    @discord.app_commands.command(name="permtest", description="Tests permission decorator.")
    async def perm_test(self, interaction: discord.Interaction, model: str):
        ...
        
async def setup(client):
    await client.add_cog(General(client))
