from sqlite3 import DatabaseError
import discord
from discord.ext.commands import Cog as _Cog

from joe import DeveloperJoe
from sources import (
    modelhandler,
    exceptions,
    database,
    confighandler,
    errors,
    models,
    transformers
)
from sources.common import (
    commands_utils,
    developerconfig
)

class Administration(_Cog):
    def __init__(self, _client: DeveloperJoe):
        self.client = _client
        print(f"{self.__cog_name__} Loaded")
    
    owner_group = discord.app_commands.Group(name="owner", description="Commands for managing the bot. Only usable by the bot owner.")
    admin_group = discord.app_commands.Group(name="admin", description="Commands for managing the bot. Only usable by server administrators.")
        
    @owner_group.command(name="exit", description="Shuts down bot client.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def halt(self, interaction: discord.Interaction):
        if await self.client.is_owner(interaction.user):
            await interaction.response.send_message("Shutting Down")
            await self.client.close()

            return exit(0)
        raise exceptions.DGException(errors.GenericErrors.USER_MISSING_PERMISSIONS)
        
    @owner_group.command(name="backup", description="Backs up the database file.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def backup_database(self, interaction: discord.Interaction):
        if await self.client.is_owner(interaction.user):
            with database.DGDatabaseSession() as new_database:
                location = new_database.backup_database()
                return await interaction.response.send_message(f'Backed up database to "{location}"')
        raise exceptions.DGException(errors.GenericErrors.USER_MISSING_PERMISSIONS)
    
    @owner_group.command(name="load", description="Loads backup made with /backup")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def load_database(self, interaction: discord.Interaction):
        if await self.client.is_owner(interaction.user):
            with database.DGDatabaseSession(reset_if_failed_check=False) as old_database:
                try:
                    location = old_database.load_database_backup()
                    return await interaction.response.send_message(f'Loaded backup from "{location}"')
                except DatabaseError:
                    return await interaction.response.send_message(f'You cannot load this backup as it is too old. The backup has been kept.')
                
        raise exceptions.DGException(errors.GenericErrors.USER_MISSING_PERMISSIONS)

    @admin_group.command(name="lock", description="Locks a select AI Model behind a role or permission.")
    @discord.app_commands.checks.has_permissions(manage_channels=True)
    @discord.app_commands.choices(ai_model=models.MODEL_CHOICES)
    @discord.app_commands.describe(ai_model="The AI model you want to lock.", role="The role that will be added to the specified model's list of allowed roles.")
    async def lock_role(self, interaction: discord.Interaction, ai_model: transformers.VanillaModelChoices, role: discord.Role):
        
        if confighandler.GuildConfigAttributes.get_guild_model(role.guild).model == ai_model:
            return await interaction.response.send_message("You cannot lock this model as it currently is the this servers default AI model. You may change the default with `/admin default-model`")
        
        with modelhandler.DGGuildDatabaseModelHandler(role.guild) as rules:
            _gpt_model = commands_utils.get_modeltype_from_name(ai_model)
            rules.upload_guild_model(_gpt_model, role)
            await interaction.response.send_message(f"Added {ai_model} behind role {role.mention}.")

    @admin_group.command(name="unlock", description="Unlocks a previously locked AI Model.")
    @discord.app_commands.checks.has_permissions(manage_channels=True)
    @discord.app_commands.choices(ai_model=models.MODEL_CHOICES)
    @discord.app_commands.describe(ai_model="The AI model you want to unlock.", role="The role that will be removed from the specified model's list of allowed roles.")
    async def unlock_role(self, interaction: discord.Interaction, ai_model: transformers.VanillaModelChoices, role: discord.Role):
        with modelhandler.DGGuildDatabaseModelHandler(role.guild) as rules:
            model = commands_utils.get_modeltype_from_name(ai_model)
            
            rules.remove_guild_model(model, role)
            await interaction.response.send_message(f"Removed requirement role {role.mention} from {ai_model}.")

    @admin_group.command(name="locks", description="View all models and which roles may utilise them.")
    @discord.app_commands.checks.has_permissions(manage_channels=True)
    async def view_locks(self, interaction: discord.Interaction):    

        assert isinstance(guild := interaction.guild, discord.Guild)
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
    @discord.app_commands.checks.has_permissions(administrator=True)
    @discord.app_commands.choices(ai_model=models.MODEL_CHOICES)
    async def change_default_model_for_server(self, interaction: discord.Interaction, ai_model: transformers.VanillaModelChoices | None=None):

        assert isinstance(interaction.user, discord.Member)
        model_object: models.AIModel = commands_utils.get_modeltype_from_name(ai_model if isinstance(ai_model, str) else confighandler.get_guild_config_attribute(interaction.user.guild, 'default-ai-model'))(interaction.user)
        
        if ai_model == None: # Check if user checking what model
            return await interaction.response.send_message(f"Current default AI Model is {model_object.display_name}. {model_object.description}")
        
        if model_object.get_lock_list() != []: # Make sure it is accessible (Not in lock list)
            return await interaction.response.send_message(f"Cannot set {model_object.display_name} to the default model as it roles attached to it in the lock list. Undo with `/admin unlock`.")
        
        confighandler.edit_guild_config(interaction.user.guild, "default-ai-model", ai_model)
        await interaction.response.send_message(f"Changed default AI Model to {model_object.display_name}.")

    @admin_group.command(name="set-timezone", description="Changes the bots timezone in this server.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def change_tz(self, interaction: discord.Interaction, timezone: str | None=None):
        assert isinstance(interaction.guild, discord.Guild)
        
        if timezone == None:
            return await interaction.response.send_message(f"Current timezone is {confighandler.get_guild_config_attribute(interaction.guild, 'timezone')}")
        elif timezone in self.client.__tzs__:
            confighandler.edit_guild_config(interaction.guild, "timezone", timezone)
            return await interaction.response.send_message(f"Changed bots timezone to {timezone}.")
        await interaction.response.send_message(f"Unknown timezone: {timezone}")
    
    @admin_group.command(name="voice-enabled", description=f"Configure if users can have spoken {confighandler.get_config('bot_name')} chats.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def config_voice(self, interaction: discord.Interaction, allow_voice: transformers.BooleanChoices):
        assert isinstance(interaction.guild, discord.Guild)
        
        if allow_voice == None:
            return await interaction.response.send_message(f"Users {'cannot' if confighandler.get_guild_config_attribute(interaction.guild, 'voice-enabled') == False else 'can'} use voice.")
        confighandler.edit_guild_config(interaction.guild, "voice-enabled", allow_voice)
        return await interaction.response.send_message(f"Users {'cannot' if allow_voice == False else 'can'} use voice.")
    
    @admin_group.command(name="reset", description=f"Reset this servers configuration back to default.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def reset_config(self, interaction: discord.Interaction):
        assert isinstance(guild := interaction.guild, discord.Guild)
            
        confirm = await self.client.get_input(interaction, f"Are you sure you want to reset this servers configuration? This cannot be undone unless you remember the current configuration. (Type: {developerconfig.QUERY_CONFIRMATION})")
        if not confirm or confirm.content != developerconfig.QUERY_CONFIRMATION:
            return await interaction.followup.send("Cancelled action.", ephemeral=False)
            
        confighandler.reset_guild_config(guild)
        return await interaction.followup.send("The servers configuration options have been reset. You may view them with /config or /server.")
    
    @admin_group.command(name="config", description="View this discord servers configuration.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def guild_config(self, interaction: discord.Interaction):
        assert isinstance(guild := interaction.guild, discord.Guild)
            
        _config = confighandler.get_guild_config(guild)
        embed = self.client.get_embed(f"{guild} Configuration Settings")
        
        for c_entry in _config.raw_config_data.items():
            embed.add_field(name=f'Configuration Option: "{c_entry[0]}"', value=c_entry[1], inline=False)
        
        await interaction.response.send_message(embed=embed) 
        
async def setup(client):
    await client.add_cog(Administration(client))
