import discord
from discord import app_commands
from discord.ext import commands

from database import get_config, set_config


class TemporaryVoice(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.owners: dict[int, int] = {}

    def _room(self, interaction: discord.Interaction) -> discord.VoiceChannel | None:
        if not isinstance(interaction.user, discord.Member) or not interaction.user.voice:
            return None
        channel = interaction.user.voice.channel
        return channel if isinstance(channel, discord.VoiceChannel) and self.owners.get(channel.id) == interaction.user.id else None

    @app_commands.command(name="setup_tempvoice", description="Richtet einen Join-to-create Voice-Kanal ein.")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def setup_tempvoice(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        if guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        config = get_config(guild.id)
        existing = guild.get_channel(config["temp_voice_channel_id"] or 0)
        if isinstance(existing, discord.VoiceChannel):
            return await interaction.response.send_message(f"🔊 Temp-Voice ist bereits aktiv: {existing.mention}", ephemeral=True)
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
            room = await guild.create_voice_channel(f"🎙️ {member.display_name}'s Room", category=category if isinstance(category, discord.CategoryChannel) else None, reason="MakeItHappen temporary voice room")
            self.owners[room.id] = member.id
            await member.move_to(room, reason="MakeItHappen temporary voice room")
        if before.channel and before.channel.id in self.owners and len(before.channel.members) == 0:
            self.owners.pop(before.channel.id, None)
            try:
                await before.channel.delete(reason="Empty MakeItHappen temporary voice room")
            except discord.NotFound:
                pass

    @app_commands.command(name="voice_rename", description="Benennt deinen temporären Voice-Raum um.")
    @app_commands.describe(name="Neuer Name")
    async def voice_rename(self, interaction: discord.Interaction, name: str) -> None:
        channel = self._room(interaction)
        if channel is None:
            return await interaction.response.send_message("❌ Du musst Owner eines Temp-Raums sein.", ephemeral=True)
        await channel.edit(name=name[:100], reason="MakeItHappen voice owner")
        await interaction.response.send_message(f"✏️ Raum umbenannt zu **{channel.name}**.")

    @app_commands.command(name="voice_limit", description="Setzt das User-Limit deines temporären Voice-Raums.")
    @app_commands.describe(limit="0 = unbegrenzt")
    async def voice_limit(self, interaction: discord.Interaction, limit: app_commands.Range[int, 0, 99]) -> None:
        channel = self._room(interaction)
        if channel is None:
            return await interaction.response.send_message("❌ Du musst Owner eines Temp-Raums sein.", ephemeral=True)
        await channel.edit(user_limit=limit, reason="MakeItHappen voice owner")
        await interaction.response.send_message(f"👥 User-Limit: **{limit or 'unbegrenzt'}**.")

    @app_commands.command(name="voice_lock", description="Sperrt deinen temporären Voice-Raum.")
    async def voice_lock(self, interaction: discord.Interaction) -> None:
        channel = self._room(interaction)
        if channel is None:
            return await interaction.response.send_message("❌ Du musst Owner eines Temp-Raums sein.", ephemeral=True)
        await channel.set_permissions(interaction.guild.default_role, connect=False)
        await interaction.response.send_message("🔒 Raum gesperrt.")

    @app_commands.command(name="voice_unlock", description="Entsperrt deinen temporären Voice-Raum.")
    async def voice_unlock(self, interaction: discord.Interaction) -> None:
        channel = self._room(interaction)
        if channel is None:
            return await interaction.response.send_message("❌ Du musst Owner eines Temp-Raums sein.", ephemeral=True)
        await channel.set_permissions(interaction.guild.default_role, connect=None)
        await interaction.response.send_message("🔓 Raum entsperrt.")

    @app_commands.command(name="voice_kick", description="Kickt einen User aus deinem temporären Voice-Raum.")
    async def voice_kick(self, interaction: discord.Interaction, member: discord.Member) -> None:
        channel = self._room(interaction)
        if channel is None:
            return await interaction.response.send_message("❌ Du musst Owner eines Temp-Raums sein.", ephemeral=True)
        if member not in channel.members:
            return await interaction.response.send_message("❌ Dieser User ist nicht in deinem Raum.", ephemeral=True)
        await member.move_to(None, reason="MakeItHappen voice owner kick")
        await interaction.response.send_message(f"👢 {member.mention} wurde aus dem Raum entfernt.")

    @app_commands.command(name="voice_transfer", description="Überträgt den Owner deines Temp-Raums.")
    async def voice_transfer(self, interaction: discord.Interaction, member: discord.Member) -> None:
        channel = self._room(interaction)
        if channel is None:
            return await interaction.response.send_message("❌ Du musst Owner eines Temp-Raums sein.", ephemeral=True)
        if member not in channel.members:
            return await interaction.response.send_message("❌ Der neue Owner muss im Raum sein.", ephemeral=True)
        self.owners[channel.id] = member.id
        await interaction.response.send_message(f"👑 {member.mention} ist jetzt Owner des Raums.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TemporaryVoice(bot))
