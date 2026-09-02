import discord
from discord import app_commands
from discord.ext import commands

from database import get_config, set_config


class TemporaryVoice(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.owners: dict[int, int] = {}

    @app_commands.command(name="setup_tempvoice", description="Richtet einen Join-to-create Voice-Kanal ein.")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def setup_tempvoice(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        if guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        category = await guild.create_category("MakeItHappen • Voice")
        channel = await guild.create_voice_channel("➕ Create a Room", category=category)
        set_config(guild.id, "temp_voice_channel_id", channel.id)
        set_config(guild.id, "temp_voice_category_id", category.id)
        await interaction.response.send_message(f"🔊 Temp-Voice aktiviert: {channel.mention}", ephemeral=True)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        guild = member.guild
        config = get_config(guild.id)
        trigger_id = config["temp_voice_channel_id"]
        category_id = config["temp_voice_category_id"]
        if after.channel and after.channel.id == trigger_id:
            category = guild.get_channel(category_id) if category_id else after.channel.category
            room = await guild.create_voice_channel(
                f"🎙️ {member.display_name}'s Room",
                category=category if isinstance(category, discord.CategoryChannel) else None,
                reason="MakeItHappen temporary voice room",
            )
            self.owners[room.id] = member.id
            await member.move_to(room, reason="MakeItHappen temporary voice room")
        if before.channel and before.channel.id in self.owners and len(before.channel.members) == 0:
            self.owners.pop(before.channel.id, None)
            try:
                await before.channel.delete(reason="Empty MakeItHappen temporary voice room")
            except discord.NotFound:
                pass

    @app_commands.command(name="voice_lock", description="Sperrt deinen temporären Voice-Raum.")
    async def voice_lock(self, interaction: discord.Interaction) -> None:
        channel = interaction.user.voice.channel if isinstance(interaction.user, discord.Member) and interaction.user.voice else None
        if not isinstance(channel, discord.VoiceChannel) or self.owners.get(channel.id) != interaction.user.id:
            return await interaction.response.send_message("❌ Du musst Owner eines Temp-Raums sein.", ephemeral=True)
        await channel.set_permissions(interaction.guild.default_role, connect=False)
        await interaction.response.send_message("🔒 Raum gesperrt.")

    @app_commands.command(name="voice_unlock", description="Entsperrt deinen temporären Voice-Raum.")
    async def voice_unlock(self, interaction: discord.Interaction) -> None:
        channel = interaction.user.voice.channel if isinstance(interaction.user, discord.Member) and interaction.user.voice else None
        if not isinstance(channel, discord.VoiceChannel) or self.owners.get(channel.id) != interaction.user.id:
            return await interaction.response.send_message("❌ Du musst Owner eines Temp-Raums sein.", ephemeral=True)
        await channel.set_permissions(interaction.guild.default_role, connect=None)
        await interaction.response.send_message("🔓 Raum entsperrt.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TemporaryVoice(bot))
