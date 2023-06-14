import discord
from discord.ext import commands
from joe import DevJoe

class general(commands.Cog):
    def __init__(self, client):
        self.client: DevJoe = client
        print(f"{self.__cog_name__} Loaded")

    @discord.app_commands.command(name="help", description="Lists avalible commands")
    async def help_command(self, interaction: discord.Interaction):
        
        embed = discord.Embed(title=f"DeveloperJoe Commands")
        embed.color = discord.Colour.purple()
        embed.footer = "For arguments, type the command and they will appear."

        for command in self.client.tree.walk_commands():
            embed.add_field(name=f"/{command.name}", value=command.description, inline=False)

        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="shutdown", description="Shuts down bot client")
    async def halt(self, interaction: discord.Interaction):
        if interaction.user.id == 400089431933059072:
            await interaction.response.send_message("Shutting Down")
            return await self.client.close()
        await interaction.response.send_message("You are not the owner.")


async def setup(client):
    await client.add_cog(general(client))
