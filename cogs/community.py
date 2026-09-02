import discord
from discord import app_commands
from discord.ext import commands

from database import add_goal, add_xp, award, complete_goal, get_goals


class Community(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="goal", description="Setzt ein persönliches Ziel.")
    @app_commands.describe(title="Dein Ziel")
    async def goal(self, interaction: discord.Interaction, title: str) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        if len(title) > 100:
            return await interaction.response.send_message("❌ Das Ziel darf maximal 100 Zeichen haben.", ephemeral=True)
        goal_id = add_goal(interaction.guild.id, interaction.user.id, title)
        xp = add_xp(interaction.guild.id, interaction.user.id, 10)
        await interaction.response.send_message(f"🎯 **Ziel erstellt!**\n`#{goal_id}` — {title}\n\n⭐ +10 XP · Gesamt: **{xp} XP**")

    @app_commands.command(name="goals", description="Zeigt deine offenen Ziele.")
    async def goals(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        rows = get_goals(interaction.guild.id, interaction.user.id)
        if not rows:
            return await interaction.response.send_message("🎯 Keine offenen Ziele. Setz dir eins mit `/goal`.")
        lines = [f"`#{row['id']}` — {row['title']}" for row in rows[:15]]
        await interaction.response.send_message("🎯 **Deine Ziele**\n\n" + "\n".join(lines))

    @app_commands.command(name="complete", description="Markiert ein Ziel als erledigt.")
    @app_commands.describe(goal_id="Die ID aus /goals")
    async def complete(self, interaction: discord.Interaction, goal_id: int) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        if not complete_goal(interaction.guild.id, interaction.user.id, goal_id):
            return await interaction.response.send_message("❌ Ziel nicht gefunden oder bereits erledigt.", ephemeral=True)
        xp = add_xp(interaction.guild.id, interaction.user.id, 50)
        unlocked = ""
        if award(interaction.guild.id, interaction.user.id, "First Step"):
            unlocked = "\n🏆 **Achievement unlocked:** First Step"
        await interaction.response.send_message(f"🏆 **Ziel erreicht!**\n\n+50 XP · Gesamt: **{xp} XP**\n\n**Make it happen.** 🔥{unlocked}")

    @app_commands.command(name="achievements", description="Zeigt deine freigeschalteten Achievements.")
    async def achievements(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        rows = get_achievements(interaction.guild.id, interaction.user.id)
        if not rows:
            return await interaction.response.send_message("🏆 Noch keine Achievements. Dein erstes wartet auf dich!")
        await interaction.response.send_message("🏆 **Deine Achievements**\n\n" + "\n".join(f"• **{row['achievement']}**" for row in rows))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Community(bot))
