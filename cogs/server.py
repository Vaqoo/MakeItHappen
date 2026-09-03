import time
from collections import defaultdict, deque
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks

from database import clear_lockdown_overrides, get_config, get_lockdown_overrides, get_birthdays, remove_temp_voice_room, save_lockdown_override, set_config, set_birthday


class ServerTools(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.joins: dict[int, deque[float]] = defaultdict(deque)
        self.last_raid_alert: dict[int, float] = {}
        self.announced_birthdays: set[tuple[int, str]] = set()
        self.birthday_loop.start()

    def cog_unload(self) -> None:
        self.birthday_loop.cancel()

    @app_commands.command(name="setup_welcome", description="Aktiviert Welcome-Nachrichten im aktuellen Kanal.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setup_welcome(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None or not isinstance(interaction.channel, discord.TextChannel):
            return await interaction.response.send_message("❌ Nutze den Befehl in einem Textkanal.", ephemeral=True)
        set_config(interaction.guild.id, "welcome_channel_id", interaction.channel.id)
        set_config(interaction.guild.id, "welcome_enabled", 1)
        await interaction.response.send_message("👋 Welcome-System aktiviert.", ephemeral=True)

    @app_commands.command(name="setup_goodbye", description="Aktiviert Goodbye-Nachrichten im aktuellen Kanal.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setup_goodbye(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None or not isinstance(interaction.channel, discord.TextChannel):
            return await interaction.response.send_message("❌ Nutze den Befehl in einem Textkanal.", ephemeral=True)
        set_config(interaction.guild.id, "goodbye_channel_id", interaction.channel.id)
        set_config(interaction.guild.id, "goodbye_enabled", 1)
        await interaction.response.send_message("👋 Goodbye-System aktiviert.", ephemeral=True)

    @app_commands.command(name="setup_suggestions", description="Aktiviert das MIH Suggestion-System im aktuellen Kanal.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setup_suggestions(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None or not isinstance(interaction.channel, discord.TextChannel):
            return await interaction.response.send_message("❌ Nutze den Befehl in einem Textkanal.", ephemeral=True)
        set_config(interaction.guild.id, "suggestion_channel_id", interaction.channel.id)
        set_config(interaction.guild.id, "suggestion_enabled", 1)
        await interaction.response.send_message("💡 Suggestion-System aktiviert.", ephemeral=True)

    @app_commands.command(name="suggest", description="Schickt eine Idee an den Suggestion-Kanal.")
    @app_commands.describe(idea="Deine Idee für den Server")
    async def suggest(self, interaction: discord.Interaction, idea: str) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        config = get_config(interaction.guild.id)
        channel = interaction.guild.get_channel(config["suggestion_channel_id"] or 0)
        if not config["suggestion_enabled"] or not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message("❌ Suggestions sind auf diesem Server nicht eingerichtet.", ephemeral=True)
        embed = discord.Embed(title="💡 Neue Suggestion", description=idea[:2000], color=discord.Color.blurple())
        embed.set_footer(text=f"Von {interaction.user} • {interaction.user.id}")
        try:
            message = await channel.send(embed=embed)
            await message.add_reaction("👍")
            await message.add_reaction("👎")
        except discord.HTTPException:
            return await interaction.response.send_message("❌ MIH konnte die Suggestion nicht posten. Prüfe die Kanalrechte.", ephemeral=True)
        await interaction.response.send_message(f"💡 Deine Suggestion wurde in {channel.mention} gepostet.", ephemeral=True)

    @app_commands.command(name="poll", description="Erstellt eine einfache Ja/Nein-Umfrage.")
    @app_commands.describe(question="Deine Frage")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def poll(self, interaction: discord.Interaction, question: str) -> None:
        if not isinstance(interaction.channel, discord.TextChannel):
            return await interaction.response.send_message("❌ Dieser Befehl funktioniert nur in Textkanälen.", ephemeral=True)
        embed = discord.Embed(title="📊 Poll", description=question[:2000], color=discord.Color.blurple())
        embed.set_footer(text=f"Erstellt von {interaction.user}")
        try:
            message = await interaction.channel.send(embed=embed)
            await message.add_reaction("✅")
            await message.add_reaction("❌")
        except discord.HTTPException:
            return await interaction.response.send_message("❌ MIH konnte die Umfrage nicht erstellen. Prüfe die Kanalrechte.", ephemeral=True)
        await interaction.response.send_message("📊 Umfrage erstellt.", ephemeral=True)

    @app_commands.command(name="lockdown", description="Sperrt oder entsperrt den aktuellen Server für @everyone.")
    @app_commands.describe(enabled="True = sperren, False = entsperren")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def lockdown(self, interaction: discord.Interaction, enabled: bool) -> None:
        guild = interaction.guild
        if guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        config = get_config(guild.id)
        changed = 0
        if enabled:
            clear_lockdown_overrides(guild.id)
            for channel in guild.text_channels:
                try:
                    current = channel.overwrites_for(guild.default_role).send_messages
                    encoded = 1 if current is True else 0 if current is False else -1
                    save_lockdown_override(guild.id, channel.id, encoded)
                    await channel.set_permissions(guild.default_role, send_messages=False, reason="MakeItHappen lockdown")
                    changed += 1
                except discord.HTTPException:
                    continue
        else:
            overrides = {int(row["channel_id"]): int(row["send_messages"]) for row in get_lockdown_overrides(guild.id)}
            for channel in guild.text_channels:
                if channel.id not in overrides:
                    continue
                try:
                    encoded = overrides[channel.id]
                    value = True if encoded == 1 else False if encoded == 0 else None
                    await channel.set_permissions(guild.default_role, send_messages=value, reason="MakeItHappen lockdown removed")
                    changed += 1
                except discord.HTTPException:
                    continue
            clear_lockdown_overrides(guild.id)
        set_config(guild.id, "lockdown_enabled", 1 if enabled else 0)
        state = "🔒 **Lockdown aktiviert.**" if enabled else "🔓 **Lockdown aufgehoben.**"
        await interaction.response.send_message(f"{state}\n{changed} Textkanäle angepasst.", ephemeral=True)

    @app_commands.command(name="anti_raid", description="Aktiviert oder deaktiviert Join-Burst-Erkennung.")
    @app_commands.describe(enabled="True = aktivieren, False = deaktivieren", threshold="Joins innerhalb des Zeitfensters")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def anti_raid(self, interaction: discord.Interaction, enabled: bool, threshold: app_commands.Range[int, 3, 30] = 8) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        set_config(interaction.guild.id, "anti_raid_enabled", 1 if enabled else 0)
        set_config(interaction.guild.id, "raid_threshold", threshold)
        set_config(interaction.guild.id, "raid_window", 20)
        self.joins[interaction.guild.id].clear()
        self.last_raid_alert.pop(interaction.guild.id, None)
        await interaction.response.send_message(f"🛡️ Anti-Raid **{'aktiviert' if enabled else 'deaktiviert'}** · Schwelle: **{threshold} Joins / 20s**.", ephemeral=True)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        config = get_config(member.guild.id)
        if config["welcome_enabled"]:
            channel = member.guild.get_channel(config["welcome_channel_id"] or 0)
            if isinstance(channel, discord.TextChannel):
                try:
                    await channel.send(f"👋 Willkommen {member.mention} auf **{member.guild.name}**!\n\n✨ **Make it happen.**")
                except discord.HTTPException:
                    pass
        if not config["anti_raid_enabled"]:
            return
        now = time.monotonic()
        history = self.joins[member.guild.id]
        history.append(now)
        while history and now - history[0] > int(config["raid_window"]):
            history.popleft()
        if len(history) >= int(config["raid_threshold"]):
            last_alert = self.last_raid_alert.get(member.guild.id, 0.0)
            if now - last_alert >= int(config["raid_window"]):
                self.last_raid_alert[member.guild.id] = now
                self.bot.dispatch("mih_moderation_log", member.guild, "🚨 Possible Raid Detected", f"**{len(history)}** Beitritte in {config['raid_window']} Sekunden. Bitte Serverzugänge prüfen.", discord.Color.red())

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        config = get_config(member.guild.id)
        if config["goodbye_enabled"]:
            channel = member.guild.get_channel(config["goodbye_channel_id"] or 0)
            if isinstance(channel, discord.TextChannel):
                try:
                    await channel.send(f"👋 **{member.display_name}** hat den Server verlassen. Alles Gute!")
                except discord.HTTPException:
                    pass

    @tasks.loop(hours=1)
    async def birthday_loop(self) -> None:
        today = datetime.now(timezone.utc)
        key_date = today.strftime("%m-%d")
        for guild in self.bot.guilds:
            config = get_config(guild.id)
            key = (guild.id, key_date)
            if key in self.announced_birthdays:
                continue
            birthdays = get_birthdays(guild.id, today.month, today.day)
            channel = guild.get_channel(config["welcome_channel_id"] or 0)
            if not isinstance(channel, discord.TextChannel):
                continue
            if not birthdays:
                self.announced_birthdays.add(key)
                continue
            mentions = [member.mention for row in birthdays if (member := guild.get_member(int(row["user_id"]))) is not None]
            if mentions:
                try:
                    await channel.send("🎂 **Happy Birthday!**\n\n" + " ".join(mentions) + "\n\nMake it happen — heute ist euer Tag! 🎉")
                except discord.HTTPException:
                    continue
            self.announced_birthdays.add(key)

    @birthday_loop.before_loop
    async def before_birthday_loop(self) -> None:
        await self.bot.wait_until_ready()

    @app_commands.command(name="birthday", description="Speichert deinen Geburtstag (Tag und Monat).")
    @app_commands.describe(day="Tag", month="Monat")
    async def birthday(self, interaction: discord.Interaction, day: app_commands.Range[int, 1, 31], month: app_commands.Range[int, 1, 12]) -> None:
        from calendar import monthrange
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        if day > monthrange(2024, month)[1]:
            return await interaction.response.send_message("❌ Dieser Tag existiert in dem Monat nicht.", ephemeral=True)
        set_birthday(interaction.guild.id, interaction.user.id, month, day)
        await interaction.response.send_message(f"🎂 Geburtstag gespeichert: **{day:02d}.{month:02d}.**", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ServerTools(bot))
