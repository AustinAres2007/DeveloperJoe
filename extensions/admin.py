import discord
from discord.ext import commands
from joe import DevJoe

class admin(commands.Cog):
    def __init__(self, client):
        self.client: DevJoe = client
        print(f"{self.__cog_name__} Loaded")

    @discord.app_commands.command(name="shutdown", description="Shuts down bot client")
    async def halt(self, interaction: discord.Interaction):
        if interaction.user.id == 400089431933059072:
            await interaction.response.send_message("Shutting Down")
            await self.client.close()

            exit(0)
        await interaction.response.send_message("You are not the owner.")
        
async def setup(client):
    await client.add_cog(admin(client))
