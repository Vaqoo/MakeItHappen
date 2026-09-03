import random
from datetime import date, timedelta

import discord
from discord import app_commands
from discord.ext import commands

from database import (
    add_coins,
    add_journal,
    add_mood,
    add_win,
    add_xp,
    award,
    claim_daily,
    get_journal,
    get_moods,
    get_stats,
    get_wins,
)


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

MOODS = ("happy", "good", "okay", "tired", "stressed", "sad", "angry", "motivated")


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
            return await interaction.response.send_message("❌ Kategorie: `motivation`, `focus`, `discipline`, `mindset`, `tough`", ephemeral=True)
        await interaction.response.send_message(f"💭 **{random.choice(QUOTES[category])}**")

    @app_commands.command(name="challenge", description="Bekomme eine kleine Make-It-Happen-Challenge.")
    async def challenge(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f"🎯 **Today's Challenge**\n\n{random.choice(CHALLENGES)}")

    @app_commands.command(name="daily", description="Deine tägliche Motivation und dein Streak.")
    async def daily(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        today = date.today()
        streak = claim_daily(interaction.guild.id, interaction.user.id, today.isoformat(), (today - timedelta(days=1)).isoformat())
        if streak is None:
            stats = get_stats(interaction.guild.id, interaction.user.id)
            return await interaction.response.send_message(f"💜 Du hast dein Daily heute schon abgeholt. Streak: **{stats['streak']}** Tage.", ephemeral=True)
        xp = add_xp(interaction.guild.id, interaction.user.id, 25)
        coins = add_coins(interaction.guild.id, interaction.user.id, 20)
        unlocked = []
        if streak >= 7 and award(interaction.guild.id, interaction.user.id, "On Fire"):
            unlocked.append("🔥 On Fire")
        if streak >= 30 and award(interaction.guild.id, interaction.user.id, "Unstoppable"):
            unlocked.append("💎 Unstoppable")
        text = f"🌅 **Daily Motivation**\n\n> {random.choice(QUOTES['motivation'])}\n\n🔥 Streak: **{streak}** Tage\n⭐ XP: **{xp}**\n🪙 Coins: **{coins}**"
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
            return await interaction.response.send_message(f"🫂 **MIH ist da.**\n\n{response}\n\n> *Du musst nicht alles heute schaffen.*")
        await interaction.response.send_message("🫂 **MIH ist da.**\n\nWenn du gerade nicht weiterweißt, erzähl mir kurz, was los ist. Wir zerlegen das Problem in einen nächsten kleinen Schritt.")

    @app_commands.command(name="mood", description="Speichert, wie du dich gerade fühlst.")
    @app_commands.describe(mood="Dein aktueller Mood", note="Optionaler kurzer Zusatz")
    @app_commands.choices(mood=[app_commands.Choice(name=m.title(), value=m) for m in MOODS])
    async def mood(self, interaction: discord.Interaction, mood: app_commands.Choice[str], note: str | None = None) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        add_mood(interaction.guild.id, interaction.user.id, mood.value, note or "")
        await interaction.response.send_message(f"💜 Mood gespeichert: **{mood.name}**.", ephemeral=True)

    @app_commands.command(name="mood_history", description="Zeigt deine letzten Mood-Einträge.")
    async def mood_history(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        rows = get_moods(interaction.guild.id, interaction.user.id)
        if not rows:
            return await interaction.response.send_message("💭 Noch keine Mood-Einträge.", ephemeral=True)
        lines = [f"• **{row['mood'].title()}** — {row['note']}".rstrip(" —") for row in rows]
        await interaction.response.send_message("💭 **Deine letzten Moods**\n\n" + "\n".join(lines), ephemeral=True)

    @app_commands.command(name="journal", description="Speichert einen privaten Journal-Eintrag.")
    @app_commands.describe(entry="Dein Gedanke oder dein Eintrag")
    async def journal(self, interaction: discord.Interaction, entry: str) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        if len(entry) > 2000:
            return await interaction.response.send_message("❌ Maximal 2000 Zeichen.", ephemeral=True)
        entry_id = add_journal(interaction.guild.id, interaction.user.id, entry)
        await interaction.response.send_message(f"📓 Eintrag **#{entry_id}** privat gespeichert.", ephemeral=True)

    @app_commands.command(name="journal_history", description="Zeigt deine letzten privaten Journal-Einträge.")
    async def journal_history(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        rows = get_journal(interaction.guild.id, interaction.user.id)
        if not rows:
            return await interaction.response.send_message("📓 Noch keine Einträge.", ephemeral=True)
        lines = [f"**#{row['id']}** — {row['entry'][:300]}" for row in rows]
        await interaction.response.send_message("📓 **Dein Journal**\n\n" + "\n\n".join(lines), ephemeral=True)

    @app_commands.command(name="wins", description="Zeigt deine kleinen Erfolge.")
    async def wins(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        rows = get_wins(interaction.guild.id, interaction.user.id)
        if not rows:
            return await interaction.response.send_message("🏅 Noch keine Wins. Was hast du heute geschafft?")
        await interaction.response.send_message("🏅 **Deine Wins**\n\n" + "\n".join(f"• {row['win']}" for row in rows))

    @app_commands.command(name="win", description="Speichert einen kleinen Erfolg und belohnt dich.")
    @app_commands.describe(win="Was hast du geschafft?")
    async def win(self, interaction: discord.Interaction, win: str) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Nur auf einem Server verfügbar.", ephemeral=True)
        if len(win.strip()) > 500 or not win.strip():
            return await interaction.response.send_message("❌ Der Win muss 1–500 Zeichen lang sein.", ephemeral=True)
        add_win(interaction.guild.id, interaction.user.id, win.strip())
        xp = add_xp(interaction.guild.id, interaction.user.id, 20)
        coins = add_coins(interaction.guild.id, interaction.user.id, 10)
        await interaction.response.send_message(f"🏅 **Win gespeichert!**\n⭐ +20 XP · 🪙 +10 Coins\n\nDu hast **{xp} XP** und **{coins} Coins**.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Motivation(bot))
