import random
import time

import discord
from discord import app_commands
from discord.ext import commands

from database import (
    add_coins,
    add_goal,
    add_xp,
    award,
    complete_goal,
    delete_goal,
    get_achievements,
    get_goals,
    get_leaderboard,
    get_rank,
    get_stats,
)


def level_from_xp(xp: int) -> int:
    return xp // 100 + 1


def progress_bar(xp: int, size: int = 12) -> str:
    progress = xp % 100
    filled = round(progress / 100 * size)
    return "█" * filled + "░" * (size - filled)


class Community(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.xp_cooldowns: dict[tuple[int, int], float] = {}

    async def _reward_xp(self, guild_id: int, user_id: int, amount: int) -> tuple[int, int, list[str]]:
        before = get_stats(guild_id, user_id)
        old_level = level_from_xp(int(before["xp"]))
        xp = add_xp(guild_id, user_id, amount)
        new_level = level_from_xp(xp)
        unlocked: list[str] = []
        if new_level > old_level:
            unlocked.append(f"⬆️ Level {new_level}")
        thresholds = ((5, "Getting Started"), (10, "Locked In"), (25, "Driven"), (50, "Elite"), (100, "Legend"))
        for threshold, achievement in thresholds:
            if new_level >= threshold and award(guild_id, user_id, achievement):
                unlocked.append(f"🏆 {achievement}")
        return xp, new_level, unlocked

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if not message.guild or message.author.bot:
            return
        key = (message.guild.id, message.author.id)
        now = time.monotonic()
        if now - self.xp_cooldowns.get(key, 0) < 60:
            return
        self.xp_cooldowns[key] = now
        xp, level, unlocked = await self._reward_xp(message.guild.id, message.author.id, random.randint(5, 15))
        add_coins(message.guild.id, message.author.id, random.randint(1, 4))
        if unlocked and level > 1:
            try:
                await message.channel.send(
                    f"✨ {message.author.mention} **Level Up!** Du bist jetzt Level **{level}**!\n" + " · ".join(unlocked),
                    delete_after=8,
                )
            except discord.HTTPException:
                pass

    @app_commands.command(name="goal", description="Setzt ein persönliches Ziel.")
    @app_commands.describe(title="Dein Ziel")
    async def goal(self, interaction: discord.Interaction, title: str) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        title = title.strip()
        if not title or len(title) > 100:
            return await interaction.response.send_message("❌ Das Ziel muss 1–100 Zeichen lang sein.", ephemeral=True)
        goal_id = add_goal(interaction.guild.id, interaction.user.id, title)
        xp, _, _ = await self._reward_xp(interaction.guild.id, interaction.user.id, 10)
        coins = add_coins(interaction.guild.id, interaction.user.id, 5)
        await interaction.response.send_message(f"🎯 **Ziel erstellt!**\n`#{goal_id}` — {title}\n\n⭐ +10 XP · 🪙 +5 Coins · XP: **{xp}**")

    @app_commands.command(name="goals", description="Zeigt deine offenen Ziele.")
    async def goals(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        rows = get_goals(interaction.guild.id, interaction.user.id)
        if not rows:
            return await interaction.response.send_message("🎯 Keine offenen Ziele. Setz dir eins mit `/goal`.")
        lines = [f"`#{row['id']}` — {row['title']}" for row in rows[:15]]
        await interaction.response.send_message("🎯 **Deine Ziele**\n\n" + "\n".join(lines))

    @app_commands.command(name="complete", description="Markiert ein Ziel als erledigt und gibt dir eine Belohnung.")
    @app_commands.describe(goal_id="Die ID aus /goals")
    async def complete(self, interaction: discord.Interaction, goal_id: int) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        if not complete_goal(interaction.guild.id, interaction.user.id, goal_id):
            return await interaction.response.send_message("❌ Ziel nicht gefunden oder bereits erledigt.", ephemeral=True)
        xp, level, unlocked = await self._reward_xp(interaction.guild.id, interaction.user.id, 50)
        coins = add_coins(interaction.guild.id, interaction.user.id, 30)
        if award(interaction.guild.id, interaction.user.id, "First Step"):
            unlocked.append("🏆 First Step")
        text = f"🏆 **Ziel erreicht!**\n\n⭐ +50 XP · 🪙 +30 Coins\n⭐ Gesamt: **{xp} XP** · Level **{level}**\n\n**Make it happen.** 🔥"
        if unlocked:
            text += "\n\n" + " · ".join(unlocked)
        await interaction.response.send_message(text)

    @app_commands.command(name="goal_delete", description="Löscht eines deiner Ziele.")
    @app_commands.describe(goal_id="Die ID aus /goals")
    async def goal_delete(self, interaction: discord.Interaction, goal_id: int) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        if not delete_goal(interaction.guild.id, interaction.user.id, goal_id):
            return await interaction.response.send_message("❌ Ziel nicht gefunden.", ephemeral=True)
        await interaction.response.send_message("🗑️ Ziel gelöscht.", ephemeral=True)

    @app_commands.command(name="achievements", description="Zeigt deine freigeschalteten Achievements.")
    async def achievements(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        rows = get_achievements(interaction.guild.id, interaction.user.id)
        if not rows:
            return await interaction.response.send_message("🏆 Noch keine Achievements. Dein erstes wartet auf dich!")
        await interaction.response.send_message("🏆 **Deine Achievements**\n\n" + "\n".join(f"• **{row['achievement']}**" for row in rows[:30]))

    @app_commands.command(name="leaderboard", description="Zeigt das MIH-XP-Ranking des Servers.")
    async def leaderboard(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        rows = get_leaderboard(interaction.guild.id, 10)
        if not rows:
            return await interaction.response.send_message("📊 Noch kein Ranking vorhanden.")
        lines = []
        for index, row in enumerate(rows, start=1):
            member = interaction.guild.get_member(int(row["user_id"]))
            name = member.display_name if member else f"User {row['user_id']}"
            lines.append(f"**{index}.** {name} — Level {level_from_xp(int(row['xp']))} · {row['xp']} XP")
        await interaction.response.send_message("🏆 **MakeItHappen Leaderboard**\n\n" + "\n".join(lines))

    @app_commands.command(name="stats", description="Zeigt deine MIH-Fortschritte.")
    async def stats(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        stats = get_stats(interaction.guild.id, interaction.user.id)
        xp = int(stats["xp"])
        level = level_from_xp(xp)
        rank = get_rank(interaction.guild.id, interaction.user.id)
        await interaction.response.send_message(
            f"📈 **Deine MIH Stats**\n\n⭐ Level **{level}**\n`{progress_bar(xp)}` **{xp % 100}/100 XP**\n🏅 Server-Rang **#{rank}**\n🔥 Streak **{stats['streak']} Tage**"
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Community(bot))
