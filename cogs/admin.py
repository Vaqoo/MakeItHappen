import re
import time
from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands

from database import get_config, set_config


URL_RE = re.compile(r"https?://\S+", re.I)
INVITE_RE = re.compile(r"(?:discord\.gg|discord(?:app)?\.com/invite)/[A-Za-z0-9-]+", re.I)


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

    @app_commands.command(name="setup_automod", description="Aktiviert grundlegenden Anti-Spam-, Link- und Invite-Schutz.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setup_automod(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        for field, value in (("automod_enabled", 1), ("automod_invites", 1), ("automod_links", 0), ("automod_caps", 0), ("automod_mentions", 0)):
            set_config(interaction.guild.id, field, value)
        await interaction.response.send_message("🛡️ **AutoMod aktiviert.** Invite-Spam und Message-Flooding werden erkannt. Weitere Filter kannst du mit `/automod_filter` setzen.", ephemeral=True)

    @app_commands.command(name="automod_filter", description="Schaltet einzelne AutoMod-Filter an oder aus.")
    @app_commands.describe(filter_name="invites, links, caps oder mentions", enabled="An/Aus")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def automod_filter(self, interaction: discord.Interaction, filter_name: str, enabled: bool) -> None:
        mapping = {"invites": "automod_invites", "links": "automod_links", "caps": "automod_caps", "mentions": "automod_mentions"}
        field = mapping.get(filter_name.lower().strip())
        if field is None:
            return await interaction.response.send_message("❌ Nutze `invites`, `links`, `caps` oder `mentions`.", ephemeral=True)
        set_config(interaction.guild.id, field, 1 if enabled else 0)
        await interaction.response.send_message(f"🛡️ Filter **{filter_name}**: **{'an' if enabled else 'aus'}**.", ephemeral=True)

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
        invite = bool(config["automod_invites"]) and bool(INVITE_RE.search(message.content))
        links = bool(config["automod_links"]) and bool(URL_RE.search(message.content))
        caps = bool(config["automod_caps"]) and len(message.content) >= 12 and sum(c.isupper() for c in message.content if c.isalpha()) / max(1, sum(c.isalpha() for c in message.content)) >= 0.8
        mentions = bool(config["automod_mentions"]) and len(message.mentions) >= 5
        flood = len(history) >= 6
        if not any((invite, links, caps, mentions, flood)):
            return
        try:
            await message.delete(reason="MakeItHappen AutoMod")
        except discord.HTTPException:
            pass
        try:
            await message.author.timeout(timedelta(seconds=30), reason="MakeItHappen AutoMod")
        except discord.HTTPException:
            pass
        reasons = []
        if invite: reasons.append("Invite-Link")
        if links: reasons.append("Link")
        if caps: reasons.append("Caps")
        if mentions: reasons.append("Mention-Spam")
        if flood: reasons.append("Flood")
        warning = "🚨 AutoMod: " + ", ".join(reasons) + " erkannt."
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
