import discord
from discord.ext import commands
from joe import DevJoe
from objects import GPTConfig

class general(commands.Cog):
    def __init__(self, client):
        self.client: DevJoe = client
        print(f"{self.__cog_name__} Loaded")

    @discord.app_commands.command(name="help", description="Lists avalible commands")
    async def help_command(self, interaction: discord.Interaction):
        
        embed = discord.Embed(title=f"DeveloperJoe Commands")
        embed.color = discord.Colour.purple()
        embed.set_footer(text="For arguments, type the command and they will appear.")
        get_name = lambda cmd: cmd.name
        uptime = self.client.get_uptime()
        default = self.client.get_default_conversation(interaction.user)

        for name, cog in self.client.cogs.items():
            if not cog.get_app_commands():
                continue
            embed.add_field(name=f" ~ {name} ~", value="commands", inline=False)

            for command in cog.walk_app_commands():
                params = ", ".join(list(map(get_name, command.parameters))) # type: ignore
                embed.add_field(name=f"/{command.name}", value=f'{command.description} | /{command.name} {params}', inline=False)

        embed.set_footer(text=f"Uptime — {uptime.days} Days ({uptime}) | Version — {GPTConfig.VERSION} | Debug = {GPTConfig.DEBUG} | Default = {default.display_name if default else 'Has None.'}")
        await interaction.response.send_message(embed=embed, ephemeral=False)

async def setup(client):
    await client.add_cog(general(client))
