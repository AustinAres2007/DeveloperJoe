from sqlite3 import DatabaseError
from click import command
import discord as _discord
from discord.ext.commands import Cog as _Cog

from joe import DeveloperJoe
from sources import (
    modelhandler,
    exceptions,
    database,
    confighandler
)
from sources.common import (
    commands_utils,
    developerconfig
)

class Administration(_Cog):
    def __init__(self, _client: DeveloperJoe):
        self.client = _client
        print(f"{self.__cog_name__} Loaded")

    permissions_group = _discord.app_commands.Group(name="permissions", description="Commands for managing what bot functionality different roles can use. (Use /permissions list)")
    owner_group = _discord.app_commands.Group(name="owner", description="Commands for managing the bot. Only usable by the bot owner.")
    admin_group = _discord.app_commands.Group(name="admin", description="Commands for managing the bot. Only usable by server administrators.")
        
    @owner_group.command(name="exit", description="Shuts down bot client.")
    @_discord.app_commands.checks.has_permissions(administrator=True)
    async def halt(self, interaction: _discord.Interaction):
        if await self.client.is_owner(interaction.user):
            await interaction.response.send_message("Shutting Down")
            await self.client.close()

            return exit(0)
        raise exceptions.MissingPermissions(interaction.user)
        
    @owner_group.command(name="backup", description="Backs up the database file.")
    @_discord.app_commands.checks.has_permissions(administrator=True)
    async def backup_database(self, interaction: _discord.Interaction):
        if await self.client.is_owner(interaction.user):
            with database.DGDatabaseSession() as new_database:
                location = new_database.backup_database()
                return await interaction.response.send_message(f'Backed up database to "{location}"')
        raise exceptions.MissingPermissions(interaction.user)
    
    @owner_group.command(name="load", description="Loads backup made with /backup")
    @_discord.app_commands.checks.has_permissions(administrator=True)
    async def load_database(self, interaction: _discord.Interaction):
        if await self.client.is_owner(interaction.user):
            with database.DGDatabaseSession(reset_if_failed_check=False) as old_database:
                try:
                    location = old_database.load_database_backup()
                    return await interaction.response.send_message(f'Loaded backup from "{location}"')
                except DatabaseError:
                    return await interaction.response.send_message(f'You cannot load this backup as it is too old. The backup has been kept.')
                
        raise exceptions.MissingPermissions(interaction.user)

    @admin_group.command(name="lock", description="Locks a select GPT Model behind a role or permission.")
    @_discord.app_commands.checks.has_permissions(manage_channels=True)
    @_discord.app_commands.choices(gpt_model=developerconfig.MODEL_CHOICES)
    @_discord.app_commands.describe(gpt_model="The GPT model you want to lock.", role="The role that will be added to the specified model's list of allowed roles.")
    @_discord.app_commands.check(commands_utils.in_correct_channel)
    async def lock_role(self, interaction: _discord.Interaction, gpt_model: str, role: _discord.Role):
        with modelhandler.DGGuildDatabaseModelHandler(role.guild) as rules:
            _gpt_model = commands_utils.get_modeltype_from_name(gpt_model)
            rules.upload_guild_model(_gpt_model, role)
            await interaction.response.send_message(f"Added {gpt_model} behind role {role.mention}.")

    @admin_group.command(name="unlock", description="Unlocks a previously locked GPT Model.")
    @_discord.app_commands.checks.has_permissions(manage_channels=True)
    @_discord.app_commands.choices(gpt_model=developerconfig.MODEL_CHOICES)
    @_discord.app_commands.describe(gpt_model="The GPT model you want to unlock.", role="The role that will be removed from the specified model's list of allowed roles.")
    @_discord.app_commands.check(commands_utils.in_correct_channel)
    async def unlock_role(self, interaction: _discord.Interaction, gpt_model: str, role: _discord.Role):
        with modelhandler.DGGuildDatabaseModelHandler(role.guild) as rules:
            model = commands_utils.get_modeltype_from_name(gpt_model)
            new_rules = rules.remove_guild_model(model, role)
            await interaction.response.send_message(f"Removed requirement role {role.mention} from {gpt_model}." if new_rules != None else f"{role.mention} has not been added to unlock database.")

    @admin_group.command(name="locks", description="View all models and which roles may utilise them.")
    @_discord.app_commands.checks.has_permissions(manage_channels=True)
    @_discord.app_commands.check(commands_utils.in_correct_channel)
    async def view_locks(self, interaction: _discord.Interaction):    
        
        if guild := commands_utils.assure_class_is_value(interaction.guild, _discord.Guild):
            def _get_valid_role_mention(role_id: int) -> str:
                role = guild.get_role(role_id)
                return role.mention if role else "Deleted role."
            
            with modelhandler.DGGuildDatabaseModelHandler(guild) as rules:
                models = rules.get_guild_models()
                no_roles = "No added roles. \n\n"

                model_texts = []
                
                for model_code_name, model_roles in models.items():
                    model = commands_utils.get_modeltype_from_name(model_code_name)
                    
                    roles_joint = '\n'.join([_get_valid_role_mention(r_id) for r_id in model_roles])
                    model_text = f"\n{model.display_name}\n{no_roles if not roles_joint else roles_joint}"
                    model_texts.append(model_text)
                    
                text = '\n'.join(model_texts) if models else no_roles

                await interaction.response.send_message(text)
    
    @admin_group.command(name="default-model", description="Changes the default model that will be used in certain circumstances.")
    @_discord.app_commands.checks.has_permissions(administrator=True)
    @_discord.app_commands.check(commands_utils.in_correct_channel)
    @_discord.app_commands.choices(ai_model=developerconfig.MODEL_CHOICES)
    async def change_default_model_for_server(self, interaction: _discord.Interaction, ai_model: str | None=None):
        if guild := commands_utils.assure_class_is_value(interaction.guild, _discord.Guild):
            if ai_model == None:
                current_model_object = commands_utils.get_modeltype_from_name(confighandler.get_guild_config_attribute(guild, 'default-ai-model'))
                return await interaction.response.send_message(f"Current default AI Model is {current_model_object.display_name}. {current_model_object.description}")
            model_object = commands_utils.get_modeltype_from_name(ai_model)
            confighandler.edit_guild_config(guild, "default-ai-model", ai_model)
            await interaction.response.send_message(f"Changed default AI Model to {model_object.display_name}.")
            
async def setup(client):
    await client.add_cog(Administration(client))
