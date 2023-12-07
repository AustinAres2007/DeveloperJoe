import discord

from discord.ext.commands import Cog as _Cog

from sources import (
    models,
    confighandler
)
from sources.common import (
    commands_utils,
    decorators,
    protected,
    developerconfig
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
        [embed.add_field(name=model.display_name, value=model.description, inline=False) for model in models.registered_models.values()]
        await interaction.response.send_message(embed=embed)
    
    """
    @discord.app_commands.command(name="permtest", description="Tests permission decorator.")
    @discord.app_commands.choices(model=developerconfig.MODEL_CHOICES)
    async def perm_test(self, interaction: discord.Interaction, model: str):
        member = commands_utils.assure_class_is_value(interaction.user, discord.Member)
        
        @decorators.check_protected
        def prot_class(member: discord.Member, prot_arg: protected.ProtectedClass[models.GPTModelType]):
            print(prot_arg)
        
        # Everything working. Do more tests on check_protected then test functionality on making a DGVoiceChat (Use check_protected)
        am = commands_utils.get_modeltype_from_name(model)
        prot_class(member=member, prot_arg=protected.ProtectedClass(am))
    """
        
async def setup(client):
    await client.add_cog(General(client))
