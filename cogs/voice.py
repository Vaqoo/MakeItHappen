import discord
from discord import app_commands
from discord.ext import commands

from database import get_config, get_temp_voice_owner, remove_temp_voice_room, set_config, set_temp_voice_owner


class TemporaryVoice(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def _room(self, interaction: discord.Interaction) -> discord.VoiceChannel | None:
        if not isinstance(interaction.user, discord.Member) or not interaction.user.voice:
            return None
        channel = interaction.user.voice.channel
        if not isinstance(channel, discord.VoiceChannel):
            return None
        return channel if get_temp_voice_owner(channel.id) == interaction.user.id else None

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
        category = guild.get_channel(config["temp_voice_category_id"] or 0)
        if not isinstance(category, discord.CategoryChannel):
            category = await guild.create_category("MakeItHappen • Voice", reason="MakeItHappen temporary voice setup")
        channel = await guild.create_voice_channel("➕ Create a Room", category=category, reason="MakeItHappen temporary voice setup")
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
            try:
                room = await guild.create_voice_channel(f"🎙️ {member.display_name}'s Room"[:100], category=category if isinstance(category, discord.CategoryChannel) else None, reason="MakeItHappen temporary voice room")
                set_temp_voice_owner(guild.id, room.id, member.id, room.category_id)
                await member.move_to(room, reason="MakeItHappen temporary voice room")
            except discord.HTTPException:
                return
        if before.channel:
            owner = get_temp_voice_owner(before.channel.id)
            if owner is not None and len(before.channel.members) == 0:
                remove_temp_voice_room(before.channel.id)
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
        if not name.strip():
            return await interaction.response.send_message("❌ Der Name darf nicht leer sein.", ephemeral=True)
        await channel.edit(name=name.strip()[:100], reason="MakeItHappen voice owner")
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
        await channel.set_permissions(interaction.guild.default_role, connect=False, reason="MakeItHappen voice owner lock")
        await interaction.response.send_message("🔒 Raum gesperrt.")

    @app_commands.command(name="voice_unlock", description="Entsperrt deinen temporären Voice-Raum.")
    async def voice_unlock(self, interaction: discord.Interaction) -> None:
        channel = self._room(interaction)
        if channel is None:
            return await interaction.response.send_message("❌ Du musst Owner eines Temp-Raums sein.", ephemeral=True)
        await channel.set_permissions(interaction.guild.default_role, connect=None, reason="MakeItHappen voice owner unlock")
        await interaction.response.send_message("🔓 Raum entsperrt.")

    @app_commands.command(name="voice_kick", description="Kickt einen User aus deinem temporären Voice-Raum.")
    async def voice_kick(self, interaction: discord.Interaction, member: discord.Member) -> None:
        channel = self._room(interaction)
        if channel is None:
            return await interaction.response.send_message("❌ Du musst Owner eines Temp-Raums sein.", ephemeral=True)
        if member not in channel.members:
            return await interaction.response.send_message("❌ Dieser User ist nicht in deinem Raum.", ephemeral=True)
        if member == interaction.user:
            return await interaction.response.send_message("❌ Du kannst dich nicht selbst kicken.", ephemeral=True)
        await member.move_to(None, reason="MakeItHappen voice owner kick")
        await interaction.response.send_message(f"👢 {member.mention} wurde aus dem Raum entfernt.")

    @app_commands.command(name="voice_transfer", description="Überträgt den Owner deines Temp-Raums.")
    async def voice_transfer(self, interaction: discord.Interaction, member: discord.Member) -> None:
        channel = self._room(interaction)
        if channel is None:
            return await interaction.response.send_message("❌ Du musst Owner eines Temp-Raums sein.", ephemeral=True)
        if member.bot:
            return await interaction.response.send_message("❌ Ein Bot kann nicht Owner werden.", ephemeral=True)
        if member not in channel.members:
            return await interaction.response.send_message("❌ Der neue Owner muss im Raum sein.", ephemeral=True)
        set_temp_voice_owner(interaction.guild.id, channel.id, member.id, channel.category_id)
        await interaction.response.send_message(f"👑 {member.mention} ist jetzt Owner des Raums.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TemporaryVoice(bot))
