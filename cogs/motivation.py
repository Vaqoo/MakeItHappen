import random

import discord
from discord import app_commands
from discord.ext import commands


QUOTES = {
    "motivation": (
        "Make it happen.", "Keep going. 🔥", "You got this. 💜", "Progress > perfection.",
        "Your future self is counting on you.", "Start before you're ready.",
    ),
    "focus": (
        "Focus on what you can control.", "One task. One step. One win.",
        "Protect your focus.", "Distraction is expensive.",
    ),
    "discipline": (
        "Discipline beats motivation.", "Do it even when you don't feel like it.",
        "Consistency creates results.", "Keep promises you make to yourself.",
    ),
    "mindset": (
        "Be better than yesterday.", "A setback is not the end of the story.",
        "Learn. Adapt. Continue.", "You are allowed to start again.",
    ),
    "tough": (
        "You don't have to solve everything today.", "Bad days don't erase good progress.",
        "Take a breath. Then take the next step.", "You made it through hard days before.",
    ),
}

CHALLENGES = (
    "Do one thing today that your future self will thank you for.",
    "Put your phone away for 30 minutes and focus on one important task.",
    "Finish the small task you've been avoiding.",
    "Write down one goal and take the first step toward it today.",
    "Help someone without expecting anything back.",
    "Spend 20 minutes learning something useful.",
    "Do something today that scares you a little.",
)


class Motivation(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="motivate", description="Gibt dir einen kurzen Motivationsboost.")
    async def motivate(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f"🔥 **{random.choice(QUOTES['motivation'])}**")

    @app_commands.command(name="quote", description="Gibt dir ein Zitat passend zu deinem Mindset.")
    @app_commands.describe(category="Kategorie: motivation, focus, discipline, mindset oder tough")
    async def quote(self, interaction: discord.Interaction, category: str = "motivation") -> None:
        category = category.lower().strip()
        if category not in QUOTES:
            await interaction.response.send_message("❌ Kategorie: `motivation`, `focus`, `discipline`, `mindset`, `tough`", ephemeral=True)
            return
        await interaction.response.send_message(f"💭 **{random.choice(QUOTES[category])}**")

    @app_commands.command(name="challenge", description="Bekomme eine kleine Make-It-Happen-Challenge.")
    async def challenge(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f"🎯 **Today's Challenge**\n\n{random.choice(CHALLENGES)}")

    @app_commands.command(name="daily", description="Deine tägliche Motivation und dein Streak.")
    async def daily(self, interaction: discord.Interaction) -> None:
        from datetime import date, timedelta
        from database import add_xp, get_stats, set_daily, award

        if interaction.guild is None:
            await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
            return
        stats = get_stats(interaction.guild.id, interaction.user.id)
        today = date.today()
        last = stats["last_daily"]
        if last == today.isoformat():
            await interaction.response.send_message(f"💜 Du hast dein Daily heute schon abgeholt. Streak: **{stats['streak']}** Tage.", ephemeral=True)
            return
        streak = int(stats["streak"] or 0)
        if last == (today - timedelta(days=1)).isoformat():
            streak += 1
        else:
            streak = 1
        set_daily(interaction.guild.id, interaction.user.id, today.isoformat(), streak)
        xp = add_xp(interaction.guild.id, interaction.user.id, 25)
        unlocked = []
        if streak >= 7 and award(interaction.guild.id, interaction.user.id, "On Fire"):
            unlocked.append("🔥 On Fire")
        if streak >= 30 and award(interaction.guild.id, interaction.user.id, "Unstoppable"):
            unlocked.append("💎 Unstoppable")
        text = f"🌅 **Daily Motivation**\n\n> {random.choice(QUOTES['motivation'])}\n\n🔥 Streak: **{streak}** Tage\n⭐ XP: **{xp}**"
        if unlocked:
            text += "\n\n🏆 **Achievement unlocked:** " + ", ".join(unlocked)
        await interaction.response.send_message(text)

    @app_commands.command(name="helpme", description="Wenn du gerade nicht weiterweißt, hörst du bei MIH zu.")
    @app_commands.describe(situation="Was beschäftigt dich gerade?")
    async def helpme(self, interaction: discord.Interaction, situation: str | None = None) -> None:
        if situation:
            response = random.choice((
                "Du musst nicht alles auf einmal lösen. Was ist der kleinste Schritt, den du jetzt machen kannst?",
                "Dass es gerade schwer ist, heißt nicht, dass du schwach bist. Nimm dir einen Moment und geh Schritt für Schritt.",
                "Bevor du aufgibst: Was wäre eine kleine Sache, die du heute noch schaffen könntest?",
                "Du bist nicht dein schlechtester Tag. Atme kurz durch und fang mit dem nächsten machbaren Schritt an.",
            ))
            await interaction.response.send_message(f"🫂 **MIH ist da.**\n\n{response}\n\n> *Du musst nicht alles heute schaffen.*")
            return
        await interaction.response.send_message("🫂 **MIH ist da.**\n\nWenn du gerade nicht weiterweißt, erzähl mir kurz, was los ist. Wir zerlegen das Problem in einen nächsten kleinen Schritt.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Motivation(bot))
