import time
from collections import defaultdict, deque

import discord
from discord import app_commands
from discord.ext import commands, tasks

from database import get_config, set_config


class ServerTools(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.joins: dict[int, deque[float]] = defaultdict(deque)
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
        message = await channel.send(embed=embed)
        await message.add_reaction("👍")
        await message.add_reaction("👎")
        await interaction.response.send_message(f"💡 Deine Suggestion wurde in {channel.mention} gepostet.", ephemeral=True)

    @app_commands.command(name="poll", description="Erstellt eine einfache Ja/Nein-Umfrage.")
    @app_commands.describe(question="Deine Frage")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def poll(self, interaction: discord.Interaction, question: str) -> None:
        embed = discord.Embed(title="📊 Poll", description=question[:2000], color=discord.Color.blurple())
        embed.set_footer(text=f"Erstellt von {interaction.user}")
        message = await interaction.channel.send(embed=embed) if interaction.channel else None
        if message:
            await message.add_reaction("✅")
            await message.add_reaction("❌")
        await interaction.response.send_message("📊 Umfrage erstellt.", ephemeral=True)

    @app_commands.command(name="lockdown", description="Sperrt oder entsperrt den aktuellen Server für @everyone.")
    @app_commands.describe(enabled="True = sperren, False = entsperren")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def lockdown(self, interaction: discord.Interaction, enabled: bool) -> None:
        guild = interaction.guild
        if guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        changed = 0
        for channel in guild.text_channels:
            try:
                await channel.set_permissions(guild.default_role, send_messages=False if enabled else None, reason="MakeItHappen lockdown")
                changed += 1
            except discord.HTTPException:
                continue
        set_config(guild.id, "lockdown_enabled", 1 if enabled else 0) if "lockdown_enabled" in get_config(guild.id).keys() else None
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
        await interaction.response.send_message(f"🛡️ Anti-Raid **{'aktiviert' if enabled else 'deaktiviert'}** · Schwelle: **{threshold} Joins / 20s**.", ephemeral=True)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        config = get_config(member.guild.id)
        if config["welcome_enabled"]:
            channel = member.guild.get_channel(config["welcome_channel_id"] or 0)
            if isinstance(channel, discord.TextChannel):
                await channel.send(f"👋 Willkommen {member.mention} auf **{member.guild.name}**!\n\n✨ **Make it happen.**")
        if not config["anti_raid_enabled"]:
            return
        now = time.monotonic()
        history = self.joins[member.guild.id]
        history.append(now)
        while history and now - history[0] > int(config["raid_window"]):
            history.popleft()
        if len(history) >= int(config["raid_threshold"]):
            self.bot.dispatch(
                "mih_moderation_log",
                member.guild,
                "🚨 Possible Raid Detected",
                f"**{len(history)}** Beitritte in {config['raid_window']} Sekunden. Bitte Serverzugänge prüfen.",
                discord.Color.red(),
            )

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        config = get_config(member.guild.id)
        if config["goodbye_enabled"]:
            channel = member.guild.get_channel(config["goodbye_channel_id"] or 0)
            if isinstance(channel, discord.TextChannel):
                await channel.send(f"👋 **{member.display_name}** hat den Server verlassen. Alles Gute!")

    @tasks.loop(hours=1)
    async def birthday_loop(self) -> None:
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc)
        key_date = today.strftime("%m-%d")
        for guild in self.bot.guilds:
            config = get_config(guild.id)
            if not config["welcome_enabled"]:
                continue
            key = (guild.id, key_date)
            if key in self.announced_birthdays:
                continue
            from database import get_birthdays
            birthdays = get_birthdays(guild.id, today.month, today.day)
            if not birthdays:
                self.announced_birthdays.add(key)
                continue
            channel = guild.get_channel(config["welcome_channel_id"] or 0)
            if not isinstance(channel, discord.TextChannel):
                continue
            mentions = []
            for row in birthdays:
                member = guild.get_member(int(row["user_id"]))
                if member:
                    mentions.append(member.mention)
            if mentions:
                await channel.send("🎂 **Happy Birthday!**\n\n" + " ".join(mentions) + "\n\nMake it happen — heute ist euer Tag! 🎉")
            self.announced_birthdays.add(key)

    @birthday_loop.before_loop
    async def before_birthday_loop(self) -> None:
        await self.bot.wait_until_ready()

    @app_commands.command(name="birthday", description="Speichert deinen Geburtstag (Tag und Monat).")
    @app_commands.describe(day="Tag", month="Monat")
    async def birthday(self, interaction: discord.Interaction, day: app_commands.Range[int, 1, 31], month: app_commands.Range[int, 1, 12]) -> None:
        from calendar import monthrange
        from database import set_birthday
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        if day > monthrange(2024, month)[1]:
            return await interaction.response.send_message("❌ Dieser Tag existiert in dem Monat nicht.", ephemeral=True)
        set_birthday(interaction.guild.id, interaction.user.id, month, day)
        await interaction.response.send_message(f"🎂 Geburtstag gespeichert: **{day:02d}.{month:02d}.**", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ServerTools(bot))
