import discord
from typing import Union
from discord.ext import commands
from joe import DevJoe
from objects import GPTConfig, GPTModelRules

class admin(commands.Cog):
    def __init__(self, client):
        self.client: DevJoe = client
        print(f"{self.__cog_name__} Loaded")

    @discord.app_commands.command(name="shutdown", description="Shuts down bot client")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def halt(self, interaction: discord.Interaction):
        await interaction.response.send_message("Shutting Down")
        await self.client.close()

        exit(0)

    @discord.app_commands.command(name="lock", description="Locks a select GPT Model behind a role or permission.")
    @discord.app_commands.checks.has_permissions(manage_channels=True)
    @discord.app_commands.choices(gpt_model=GPTConfig.MODEL_CHOICES)
    async def lock_role(self, interaction: discord.Interaction, gpt_model: str, role: discord.Role):
        with GPTModelRules.GPTModelRules() as rules:
            if rules.retrieve_guild_models(role.guild.id) == None:
                rules.add_guild(role.guild.id)
                print("Added guild")
            rules.upload_guild_model(gpt_model, role.id, role.guild.id)
            await interaction.response.send_message(f"Added {gpt_model} behind role {role.mention}.")

async def setup(client):
    await client.add_cog(admin(client))
