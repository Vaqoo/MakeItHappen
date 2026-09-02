import re
import time
from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands

from database import get_config, set_config


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.recent_messages: dict[tuple[int, int], list[float]] = {}

    @app_commands.command(name="setup_logs", description="Setzt den aktuellen Kanal als MIH Log-Kanal.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setup_logs(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None or not isinstance(interaction.channel, discord.TextChannel):
            return await interaction.response.send_message("❌ Nutze den Befehl in einem Textkanal.", ephemeral=True)
        set_config(interaction.guild.id, "log_channel_id", interaction.channel.id)
        await interaction.response.send_message("📋 **Mod Logs aktiviert.** Dieser Kanal ist jetzt der MIH Log-Kanal.", ephemeral=True)

    @app_commands.command(name="setup_automod", description="Aktiviert grundlegenden Anti-Spam- und Invite-Schutz.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setup_automod(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        set_config(interaction.guild.id, "automod_enabled", 1)
        set_config(interaction.guild.id, "automod_invites", 1)
        await interaction.response.send_message("🛡️ **AutoMod aktiviert.** Invite-Spam und Message-Flooding werden erkannt.", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if not message.guild or message.author.bot or not isinstance(message.author, discord.Member):
            return
        config = get_config(message.guild.id)
        if not config["automod_enabled"]:
            return
        now = time.monotonic()
        key = (message.guild.id, message.author.id)
        history = [t for t in self.recent_messages.get(key, []) if now - t < 8]
        history.append(now)
        self.recent_messages[key] = history
        invite = bool(config["automod_invites"]) and bool(re.search(r"(?:discord\.gg|discord(?:app)?\.com/invite)/[A-Za-z0-9-]+", message.content, re.I))
        flood = len(history) >= 6
        if not invite and not flood:
            return
        try:
            await message.delete(reason="MakeItHappen AutoMod")
        except discord.HTTPException:
            pass
        try:
            await message.author.timeout(timedelta(seconds=30), reason="MakeItHappen AutoMod")
        except discord.HTTPException:
            pass
        warning = "🚨 Invite-Link entfernt." if invite else "🚨 Spam/Flood erkannt und Nachricht entfernt."
        try:
            await message.channel.send(f"{message.author.mention} {warning}", delete_after=5)
        except discord.HTTPException:
            pass

    @app_commands.command(name="automod_off", description="Deaktiviert MIH AutoMod.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def automod_off(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            return
        set_config(interaction.guild.id, "automod_enabled", 0)
        await interaction.response.send_message("🛡️ AutoMod deaktiviert.", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Admin(bot))
